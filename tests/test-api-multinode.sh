#!/bin/bash

set -e

# Setup separate workspace directories
mkdir -p /tmp/protoplaster/node1/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/node2/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/main/{tests,reports,artifacts}

# Create a local output directory for this script's results
OUTPUT_DIR="test_output"
mkdir -p "$OUTPUT_DIR"

# Create devices.yaml for the main node
cat <<EOF > /tmp/protoplaster/devices.yaml
node1: localhost:2138
node2: localhost:2139
EOF

# Create the multinode test config
cat <<EOF > /tmp/protoplaster/api-test-multinode-simple.yml
tests:
  local_tests:
    - simple:
        device: "local_dev"
  node1_tests:
    - simple:
        device: "node1_dev"
        machines: [node1]
  node2_tests:
    - simple:
        device: "node2_dev"
        machines: [node2]
EOF

echo "Starting Protoplaster nodes..."

# Start Worker Node 1
protoplaster --test-dir /tmp/protoplaster/node1/tests \
             --reports-dir /tmp/protoplaster/node1/reports \
             --artifacts-dir /tmp/protoplaster/node1/artifacts \
             --port 2138 --server &
PID1=$!

# Start Worker Node 2
protoplaster --test-dir /tmp/protoplaster/node2/tests \
             --reports-dir /tmp/protoplaster/node2/reports \
             --artifacts-dir /tmp/protoplaster/node2/artifacts \
             --port 2139 --server &
PID2=$!

# Start Main Node
protoplaster --test-dir /tmp/protoplaster/main/tests \
             --reports-dir /tmp/protoplaster/main/reports \
             --artifacts-dir /tmp/protoplaster/main/artifacts \
             --external-devices /tmp/protoplaster/devices.yaml \
             --port 5000 --server &
PID_MAIN=$!

# Cleanup function
function finish {
  echo "Stopping servers..."
  kill $PID1 $PID2 $PID_MAIN 2>/dev/null || true
}
trap finish EXIT

# Wait for servers
echo "Waiting for servers to start..."
for port in 2138 2139 5000; do
  while ! curl -s http://localhost:$port/api/v1/configs > /dev/null; do
    sleep 1
  done
done

# Upload config to ALL nodes
CONFIG_FILE="api-test-multinode-simple.yml"
for port in 2138 2139 5000; do
  echo "Uploading config to port $port..."
  NAME=$(curl -s -X POST http://localhost:$port/api/v1/configs -F "file=@/tmp/protoplaster/$CONFIG_FILE" | jq -r '.name')
  if [ "$NAME" != "$CONFIG_FILE" ] ; then
    echo "Config upload failed on port $port!"
    exit 1
  fi
done

# Trigger test run on Main Node
echo "Triggering run on Main Node..."
MAIN_RUN_ID=$(curl -s -X POST http://localhost:5000/api/v1/test-runs \
         -H "Content-Type: application/json" \
         -d "{\"config_name\": \"$CONFIG_FILE\"}" | jq -r '.id')

echo "Main Run ID: $MAIN_RUN_ID"

verify_node_execution() {
    local port=$1
    local node_name=$2

    # Define file paths inside output directory
    local report_file="$OUTPUT_DIR/${node_name}_report.csv"
    local artifact_file="$OUTPUT_DIR/${node_name}_file.txt"

    # Get the latest run ID for this node
    local run_id=$(curl -s http://localhost:$port/api/v1/test-runs | jq -r '.[-1].id')

    echo "Verifying $node_name (Port $port, Run ID: $run_id)..."

    # Wait for finish
    local status=""
    while [ "$status" != "finished" ] && [ "$status" != "failed" ]; do
      status=$(curl -s http://localhost:$port/api/v1/test-runs/$run_id | jq -r '.status')
      sleep 1
    done

    # Get report and save to output dir
    curl -s http://localhost:$port/api/v1/test-runs/$run_id/report > "$report_file"

    # Verify specific device test ran
    if ! grep -q "simple" "$report_file"; then
        echo "FAILURE: $node_name report does not contain expected string"
        exit 1
    fi

    # Verify TestSimple::test_success PASSED
    local success_status=$(grep 'TestSimple::test_success' "$report_file" | cut -d ',' -f6)
    if [ "$success_status" != "passed" ]; then
        echo "FAILURE: $node_name test_success did not pass! Status: $success_status"
        exit 1
    fi

    # Verify TestSimple::test_failure FAILED
    local fail_status=$(grep 'TestSimple::test_failure' "$report_file" | cut -d ',' -f6)
    if [ "$fail_status" != "failed" ]; then
        echo "FAILURE: $node_name test_failure did not fail! Status: $fail_status"
        exit 1
    fi

    # Verify artifact recorded
    local artifacts_entry=$(grep 'TestSimple::test_record_artifact' "$report_file" | cut -d ',' -f7-)
    if ! echo "$artifacts_entry" | grep -q "file.txt"; then
        echo "FAILURE: $node_name did not record 'file.txt' artifact in report!"
        exit 1
    fi

    # Download and verify artifact content
    curl -s "http://localhost:$port/api/v1/test-runs/$run_id/artifacts/file.txt" > "$artifact_file"
    if [ "$(cat "$artifact_file")" != "test" ]; then
        echo "FAILURE: $node_name artifact content mismatch!"
        exit 1
    fi

    echo "SUCCESS: $node_name verified."
}

# Verify all nodes
verify_node_execution 5000 "MainNode"
verify_node_execution 2138 "Node1"
verify_node_execution 2139 "Node2"

echo "---------------------------------------------------"
echo "Multinode Simple Test: ALL CHECKS PASSED"
echo "Results saved in: $OUTPUT_DIR"
echo "---------------------------------------------------"
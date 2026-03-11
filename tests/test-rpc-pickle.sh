#!/bin/bash

set -e
mkdir -p /tmp/protoplaster/pickle_node/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/pickle_main/{tests,reports,artifacts}
OUTPUT_DIR="test_pickle_output"
TEST_DIR="$( dirname "${BASH_SOURCE[0]}" )"
mkdir -p "$OUTPUT_DIR"

cat <<EOF > /tmp/protoplaster/pickle_devices.yaml
node1: localhost:2140
EOF

cat <<EOF > /tmp/protoplaster/rpc-pickle-test.yml
tests:
  pickle_test:
    - rpc_pickle:
        dev: "node1"

test-suites:
  local:
    tests:
    - pickle_test
EOF

echo "Starting Protoplaster nodes for Pickle RPC test..."

# Start Worker Node on port 2140
protoplaster --test-dir /tmp/protoplaster/pickle_node/tests \
             --reports-dir /tmp/protoplaster/pickle_node/reports \
             --artifacts-dir /tmp/protoplaster/pickle_node/artifacts \
             --custom-tests $TEST_DIR/custom_modules \
             --port 2140 --dut &
PID_WORKER=$!

# Start Main Node on port 5001
protoplaster --test-dir /tmp/protoplaster/pickle_main/tests \
             --reports-dir /tmp/protoplaster/pickle_main/reports \
             --artifacts-dir /tmp/protoplaster/pickle_main/artifacts \
             --external-devices /tmp/protoplaster/pickle_devices.yaml \
             --custom-tests $TEST_DIR/custom_modules \
             --port 5001 --server &
PID_MAIN=$!

# Cleanup function
function finish {
  echo "Stopping servers..."
  kill $PID_WORKER $PID_MAIN 2>/dev/null || true
}
trap finish EXIT

# Wait for servers
echo "Waiting for servers to start..."
for port in 2140 5001; do
  while ! curl -s http://localhost:$port/api/v1/configs > /dev/null; do
    sleep 1
  done
done

# Upload config
CONFIG_FILE="rpc-pickle-test.yml"
for port in 2140 5001; do
  echo "Uploading config to port $port..."
  NAME=$(curl -s -X POST http://localhost:$port/api/v1/configs -F "file=@/tmp/protoplaster/$CONFIG_FILE" | jq -r '.name')
  if [ "$NAME" != "$CONFIG_FILE" ] ; then
    echo "Config upload failed on port $port!"
    exit 1
  fi
done

# Trigger test run
echo "Triggering Pickle RPC run..."
curl -s -X POST http://localhost:5001/api/v1/test-runs \
         -H "Content-Type: application/json" \
         -d "{\"config_name\": \"$CONFIG_FILE\"}" > /dev/null

sleep 2

REPORT_FILE="$OUTPUT_DIR/pickle_test_report.csv"
RUN_ID=$(curl -s http://localhost:5001/api/v1/test-runs | jq -r '.[-1].id')

# Wait for finish
STATUS=""
while [ "$STATUS" != "finished" ] && [ "$STATUS" != "failed" ]; do
    STATUS=$(curl -s http://localhost:5001/api/v1/test-runs/$RUN_ID | jq -r '.status')
    sleep 1
done

# Get report
curl -s http://localhost:5001/api/v1/test-runs/$RUN_ID/report > "$REPORT_FILE"

if ! grep "test_custom_objects_rpc" "$REPORT_FILE" | grep -q "passed"; then
    echo "FAILURE: Pickle RPC test did not pass!"
    cat "$REPORT_FILE"
    exit 1
fi

echo "SUCCESS: Pickle RPC test passed."
echo "---------------------------------------------------"
echo "Results saved in: $OUTPUT_DIR"
echo "---------------------------------------------------"
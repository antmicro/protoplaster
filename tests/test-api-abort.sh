#!/bin/bash

set -e
mkdir -p /tmp/protoplaster/api_abort_node/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/api_abort_main/{tests,reports,artifacts}
OUTPUT_DIR="test_api_abort_output"
TEST_DIR="$( dirname "${BASH_SOURCE[0]}" )"
PORTS=(5001 2140)
mkdir -p "$OUTPUT_DIR"

cat <<EOF > /tmp/protoplaster/external_devices.yaml
node1: localhost:2140
EOF

cat <<EOF > /tmp/protoplaster/api-abort-test.yml
tests:
  abort_test:
    - sleep:
    - sleep:
    - sleep:
        machines: [node1]
    - sleep:
        machines: [node1]

test-suites:
  local:
    tests:
    - abort_test
EOF

echo "Starting Protoplaster nodes for API Abort test..."

# Start Worker Node on port 2140
protoplaster --test-dir /tmp/protoplaster/api_abort_node/tests \
             --reports-dir /tmp/protoplaster/api_abort_node/reports \
             --artifacts-dir /tmp/protoplaster/api_abort_node/artifacts \
             --custom-tests $TEST_DIR/custom_modules \
             --port ${PORTS[1]} --dut &
PID_WORKER=$!

# Start Main Node on port 5001
protoplaster --test-dir /tmp/protoplaster/api_abort_main/tests \
             --reports-dir /tmp/protoplaster/api_abort_main/reports \
             --artifacts-dir /tmp/protoplaster/api_abort_main/artifacts \
             --external-devices /tmp/protoplaster/external_devices.yaml \
             --custom-tests $TEST_DIR/custom_modules \
             --port ${PORTS[0]} --server &
PID_MAIN=$!

# Cleanup function
function finish {
  echo "Stopping servers..."
  kill $PID_WORKER $PID_MAIN 2>/dev/null || true
}
trap finish EXIT

# Wait for servers
echo "Waiting for servers to start..."
for port in ${PORTS[@]}; do
  while ! curl -s http://localhost:$port/api/v1/configs > /dev/null; do
    sleep 1
  done
done

# Upload config
CONFIG_FILE="api-abort-test.yml"
for port in ${PORTS[@]}; do
  echo "Uploading config to port $port..."
  NAME=$(curl -s -X POST http://localhost:$port/api/v1/configs -F "file=@/tmp/protoplaster/$CONFIG_FILE" | jq -r '.name')
  if [ "$NAME" != "$CONFIG_FILE" ] ; then
    echo "Config upload failed on port $port!"
    exit 1
  fi
done

# Trigger test run
echo "Triggering API Abort run..."
curl -s -X POST http://localhost:5001/api/v1/test-runs \
         -H "Content-Type: application/json" \
         -d "{\"config_name\": \"$CONFIG_FILE\"}" > /dev/null

sleep 2

REPORT_FILE="$OUTPUT_DIR/api_abort_test_report.csv"
RUN_IDS=()

echo "Triggering run abort..."
for i in 0 1; do
    RUN_ID=$(curl -s http://localhost:${PORTS[$i]}/api/v1/test-runs | jq -r '.[-1].id')
    RUN_IDS+=($RUN_ID)
done

curl -s -X DELETE http://localhost:${PORTS[0]}/api/v1/test-runs/${RUN_IDS[0]}
kill -SIGINT $PID_WORKER

# Wait for finish
for i in 0 1; do
    STATUS="running"
    while [ "$STATUS" == "running" ] || [ "$STATUS" == "pending" ]; do
        STATUS=$(curl -s http://localhost:${PORTS[$i]}/api/v1/test-runs/${RUN_IDS[$i]} | jq -r '.status')
        sleep 1
    done

    if [ "$STATUS" != "aborted" ]; then
        echo "Abort failed for RUN:" ${RUN_IDS[$i]} "on port" ${PORTS[$i]} "returned status: " $STATUS
        exit 1
    fi
done


echo "SUCCESS: API Abort test passed."
echo "---------------------------------------------------"
echo "Results saved in: $OUTPUT_DIR"
echo "---------------------------------------------------"
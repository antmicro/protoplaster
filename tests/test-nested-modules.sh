#!/bin/bash

set -e
mkdir -p /tmp/protoplaster/nested_modules/{tests,reports,artifacts}
OUTPUT_DIR="test_nested_modules_output"
TEST_DIR="$( dirname "${BASH_SOURCE[0]}" )"
PORTS=(5001)
mkdir -p "$OUTPUT_DIR"

cat <<EOF > /tmp/protoplaster/nested_modules.yml
tests:
  nested_modules_test:
    tests:
      - nested_tests/impl1/hello:
          message: "Hello"
      - nested_tests/impl2/hello:
          message: "World"

test-suites:
  local:
    tests:
    - nested_modules_test
EOF

echo "Starting Protoplaster nodes for nested modules test..."

# Start Main Node on port 5001
protoplaster --test-dir /tmp/protoplaster/nested_modules/tests \
             --reports-dir /tmp/protoplaster/nested_modules/reports \
             --artifacts-dir /tmp/protoplaster/nested_modules/artifacts \
             --custom-tests $TEST_DIR/custom_modules \
             --port ${PORTS[0]} --server &
PID_MAIN=$!

# Cleanup function
function finish {
  echo "Stopping servers..."
  kill $PID_MAIN 2>/dev/null || true
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
CONFIG_FILE="nested_modules.yml"
for port in ${PORTS[@]}; do
  echo "Uploading config to port $port..."
  NAME=$(curl -s -X POST http://localhost:$port/api/v1/configs -F "file=@/tmp/protoplaster/$CONFIG_FILE" | jq -r '.name')
  if [ "$NAME" != "$CONFIG_FILE" ] ; then
    echo "Config upload failed on port $port!"
    exit 1
  fi
done

# Trigger test run
echo "Triggering nested modules run..."
curl -s -X POST http://localhost:5001/api/v1/test-runs \
         -H "Content-Type: application/json" \
         -d "{\"config_name\": \"$CONFIG_FILE\"}" > /dev/null

sleep 2

REPORT_FILE="$OUTPUT_DIR/nested_modules_test_report.csv"

for RUN_ID in $(curl -s http://localhost:5001/api/v1/test-runs | jq -r '.[].id'); do
  STATUS=""
  while [ "$STATUS" != "finished" ] && [ "$STATUS" != "failed" ]; do
    STATUS=$(curl -s http://localhost:5001/api/v1/test-runs/$RUN_ID | jq -r '.status')
    sleep 1
  done
  HIDDEN=$(curl -s http://localhost:5001/api/v1/test-runs/$RUN_ID | jq -r '.hidden')
  if [ "$HIDDEN" == "true" ]; then
    continue
  fi
  curl -s http://localhost:5001/api/v1/test-runs/$RUN_ID/report >> $REPORT_FILE
done

TEST_STATUS=$(grep 'test.py::TestHello::test_hello' $REPORT_FILE | cut -d ',' -f7)
if [ "$TEST_STATUS" != "passed" ] ; then
  echo "Success test did not pass!"
  exit 1
fi
TEST_STATUS=$(grep 'test.py::TestHello2::test_hello2' $REPORT_FILE | cut -d ',' -f7)
if [ "$TEST_STATUS" != "passed" ] ; then
  echo "Success test did not pass!"
  exit 1
fi


echo "SUCCESS: Nested modules test passed."
echo "---------------------------------------------------"
echo "Results saved in: $OUTPUT_DIR"
echo "---------------------------------------------------"

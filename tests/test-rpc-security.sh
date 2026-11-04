#!/bin/bash

set -e
mkdir -p /tmp/protoplaster/pickle_node/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/pickle_main1/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/pickle_main2/{tests,reports,artifacts}
OUTPUT_DIR="test_secure_output"
TEST_DIR="$(dirname "${BASH_SOURCE[0]}")"
SECURE_TOKEN="test1234"
MISMATCHED_SECURE_TOKEN="${SECURE_TOKEN}add"
mkdir -p "$OUTPUT_DIR"

cat <<EOF >/tmp/protoplaster/rpc_secure_devices.yaml
node1: localhost:2140
EOF

cat <<EOF >/tmp/protoplaster/rpc-secure-test.yml
tests:
  pickle_test:
    - rpc_pickle:
        dev: "node1"

test-suites:
  local:
    tests:
    - pickle_test
EOF

echo ${SECURE_TOKEN} >/tmp/protoplaster/rpc-secure-token.txt

echo "Trying to run Protoplaster without secure token set"

if timeout 10 \
  protoplaster --test-dir /tmp/protoplaster/pickle_node/tests \
  --reports-dir /tmp/protoplaster/pickle_node/reports \
  --artifacts-dir /tmp/protoplaster/pickle_node/artifacts \
  --custom-tests $TEST_DIR/custom_modules \
  --port 2140 --dut >/tmp/actual-output-dut; then
  echo "FAILURE: unexpected exit"
  echo "protoplaster output:"
  cat /tmp/actual-output-dut
  exit 1
else
  EXIT_CODE=$?
  if [ ${EXIT_CODE} -eq 124 ]; then
    echo "FAILURE: DUT started when it should not have"
    echo "protoplaster output:"
    cat /tmp/actual-output-dut
    exit 1
  fi

  if grep "Missing secure" /tmp/actual-output-dut >/dev/null; then
    echo "PASS: DUT refused to start"
  else
    echo "FAILURE: missing exit message"
    echo "protoplaster output:"
    cat /tmp/actual-output-dut
    exit 1
  fi
fi

if timeout 10 \
  protoplaster --test-dir /tmp/protoplaster/pickle_main1/tests \
  --reports-dir /tmp/protoplaster/pickle_main1/reports \
  --artifacts-dir /tmp/protoplaster/pickle_main1/artifacts \
  --custom-tests $TEST_DIR/custom_modules \
  --port 5001 --server >/tmp/actual-output-server; then
  echo "FAILURE: unexpected exit"
  echo "protoplaster output:"
  cat /tmp/actual-output-server
  exit 1
else
  EXIT_CODE=$?
  if [ ${EXIT_CODE} -eq 124 ]; then
    echo "FAILURE: server started when it should not have"
    echo "protoplaster output:"
    cat /tmp/actual-output-server
    exit 1
  fi

  if grep "Missing secure" /tmp/actual-output-server >/dev/null; then
    echo "PASS: server refused to start"
  else
    echo "FAILURE: missing exit message"
    echo "protoplaster output:"
    cat /tmp/actual-output-server
    exit 1
  fi
fi

echo "Starting Protoplaster nodes for RPC security test..."

# Start Worker Node on port 2140 with env secure token
PROTOPLASTER_SECURE_TOKEN="${SECURE_TOKEN}" \
  protoplaster --test-dir /tmp/protoplaster/pickle_node/tests \
  --reports-dir /tmp/protoplaster/pickle_node/reports \
  --artifacts-dir /tmp/protoplaster/pickle_node/artifacts \
  --custom-tests $TEST_DIR/custom_modules \
  --port 2140 --dut &
PID_WORKER=$!

# Start Main Node on port 5001 with file secure token
protoplaster --test-dir /tmp/protoplaster/pickle_main1/tests \
  --reports-dir /tmp/protoplaster/pickle_main1/reports \
  --artifacts-dir /tmp/protoplaster/pickle_main1/artifacts \
  --external-devices /tmp/protoplaster/rpc_secure_devices.yaml \
  --custom-tests $TEST_DIR/custom_modules \
  --token-file /tmp/protoplaster/rpc-secure-token.txt \
  --port 5001 --server &
PID_MAIN1=$!

# Start Main Node on port 5001 with non-matching secure token
PROTOPLASTER_SECURE_TOKEN="${MISMATCHED_SECURE_TOKEN}" \
  protoplaster --test-dir /tmp/protoplaster/pickle_main2/tests \
  --reports-dir /tmp/protoplaster/pickle_main2/reports \
  --artifacts-dir /tmp/protoplaster/pickle_main2/artifacts \
  --external-devices /tmp/protoplaster/rpc_secure_devices.yaml \
  --custom-tests $TEST_DIR/custom_modules \
  --port 5002 --server &
PID_MAIN2=$!

# Cleanup function
function finish {
  echo "Stopping servers..."
  kill $PID_WORKER $PID_MAIN1 $PID_MAIN2 2>/dev/null || true
}
trap finish EXIT

# Wait for servers
echo "Waiting for servers to start..."
for port in 2140 5001 5002; do
  while ! curl -s http://localhost:$port/api/v1/configs >/dev/null; do
    sleep 1
  done
done

# Upload config
CONFIG_FILE="rpc-secure-test.yml"
for port in 2140 5001 5002; do
  echo "Uploading config to port $port..."
  NAME=$(curl -s -X POST http://localhost:$port/api/v1/configs -F "file=@/tmp/protoplaster/$CONFIG_FILE" | jq -r '.name')
  if [ "$NAME" != "$CONFIG_FILE" ]; then
    echo "Config upload failed on port $port!"
    exit 1
  fi
done

# Trigger test runs
echo "Triggering RPC run with matching token..."
curl -s -X POST http://localhost:5001/api/v1/test-runs \
  -H "Content-Type: application/json" \
  -d "{\"config_name\": \"$CONFIG_FILE\"}" >/dev/null

sleep 2

REPORT_FILE="$OUTPUT_DIR/secure_test_report.csv"
RUN_ID=$(curl -s http://localhost:5001/api/v1/test-runs | jq -r '.[-1].id')

# Wait for finish
STATUS=""
while [ "$STATUS" != "finished" ] && [ "$STATUS" != "failed" ]; do
  STATUS=$(curl -s http://localhost:5001/api/v1/test-runs/$RUN_ID | jq -r '.status')
  sleep 1
done

# Get report
curl -s http://localhost:5001/api/v1/test-runs/$RUN_ID/report >"$REPORT_FILE"

if ! grep "test_custom_objects_rpc" "$REPORT_FILE" | grep -q "passed"; then
  echo "FAILURE: RPC security test did not pass!"
  cat "$REPORT_FILE"
  exit 1
fi

echo "Triggering RPC run with non matching token..."
curl -s -X POST http://localhost:5002/api/v1/test-runs \
  -H "Content-Type: application/json" \
  -d "{\"config_name\": \"$CONFIG_FILE\"}" >/dev/null

sleep 2

REPORT_FILE="$OUTPUT_DIR/unmatched_test_report.csv"
RUN_ID=$(curl -s http://localhost:5002/api/v1/test-runs | jq -r '.[-1].id')

# Wait for finish
STATUS=""
while [ "$STATUS" != "finished" ] && [ "$STATUS" != "failed" ]; do
  STATUS=$(curl -s http://localhost:5002/api/v1/test-runs/$RUN_ID | jq -r '.status')
  sleep 1
done

# Get report
curl -s http://localhost:5002/api/v1/test-runs/$RUN_ID/report >"$REPORT_FILE"

if ! grep "test_custom_objects_rpc" "$REPORT_FILE" | grep -q "failed"; then
  echo "FAILURE: RPC security passed with mismatched token!"
  cat "$REPORT_FILE"
  exit 1
fi

echo "SUCCESS: RPC security test passed."
echo "---------------------------------------------------"
echo "Results saved in: $OUTPUT_DIR"
echo "---------------------------------------------------"

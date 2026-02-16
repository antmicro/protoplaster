#!/bin/bash

set -e

mkdir -p srv/protoplaster/{tests,reports,artifacts}
protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts --server &
PROTOPLASTER_PID=$!

# Wait for protoplaster server to start
while ! curl http://localhost:5000/api/v1/configs ; do
  sleep 1
done

# Test config upload
TEST_UPLOAD_NAME=$(curl -X POST http://127.0.0.1:5000/api/v1/configs -F "file=@tests/api-test.yml" | jq -r '.name')
if [ "$TEST_UPLOAD_NAME" != "api-test.yml" ] ; then
  echo "Test config upload failed!"
  exit 1
fi

# Trigger test run
RUN_ID=$(curl -s -X POST http://localhost:5000/api/v1/test-runs -H "Content-Type: application/json" -d '{"config_name": "api-test.yml"}' | jq -r '.id')

# Wait for test run to finish
STATUS=""
while [ "$STATUS" != "finished" ] && [ "$STATUS" != "failed" ]; do
  STATUS=$(curl -s http://localhost:5000/api/v1/test-runs/$RUN_ID | jq -r '.status')
  sleep 1
done

# Collect test report
curl -s http://localhost:5000/api/v1/test-runs/$RUN_ID/report > report.csv

TEST_STATUS=$(grep 'test.py::TestSimple::test_success' report.csv | cut -d ',' -f6)
if [ "$TEST_STATUS" != "passed" ] ; then
  echo "Success test did not pass!"
  exit 1
fi

TEST_STATUS=$(grep 'test.py::TestSimple::test_failure' report.csv | cut -d ',' -f6)
if [ "$TEST_STATUS" != "failed" ] ; then
  echo "Failure test did not fail!"
  exit 1
fi

TEST_STATUS=$(grep 'test.py::TestSimple::test_record_artifact' report.csv | cut -d ',' -f6)
if [ "$TEST_STATUS" != "passed" ] ; then
  echo "Artifacts record test did not pass!"
  exit 1
fi

TEST_ARTIFACTS=$(grep 'test.py::TestSimple::test_record_artifact' report.csv | cut -d ',' -f7-)
if ! echo "$TEST_ARTIFACTS" | grep -q "file.txt"; then
  echo "file.txt artifacts was not recorded!"
  exit 1
fi

curl -s http://localhost:5000/api/v1/test-runs/$RUN_ID/artifacts/file.txt > file.txt
if [ $(cat file.txt) != "test" ] ; then
  echo "file.txt contents does not match!"
  exit 1
fi

function finish {
  kill $PROTOPLASTER_PID
}
trap finish EXIT



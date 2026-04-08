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

TEST_SUITES=$(curl -s http://localhost:5000/api/v1/configs/api-test.yml/test-suites | jq -r '.[]')
if [ "$TEST_SUITES" != "compl" ] ; then
  echo "Fetching list of test suites failed!"
  exit 1
fi

OVERRIDE_HINTS=$(curl -s http://localhost:5000/api/v1/configs/api-test.yml/override-hints | jq -r '.[]')
if [ "$OVERRIDE_HINTS" != $'tests.base.0.simple.device\ntests.ext.0.simple.device' ] ; then
  echo "Fetching list of override hints failed!"
  exit 1
fi

# Trigger test run
curl -s -X POST http://localhost:5000/api/v1/test-runs -H "Content-Type: application/json" -d '{"config_name": "api-test.yml"}' > /dev/null
sleep 2

# Wait for test runs to finish and collect reports
rm -f report.csv
for RUN_ID in $(curl -s http://localhost:5000/api/v1/test-runs | jq -r '.[].id'); do
  STATUS=""
  while [ "$STATUS" != "finished" ] && [ "$STATUS" != "failed" ]; do
    STATUS=$(curl -s http://localhost:5000/api/v1/test-runs/$RUN_ID | jq -r '.status')
    sleep 1
  done
  HIDDEN=$(curl -s http://localhost:5000/api/v1/test-runs/$RUN_ID | jq -r '.hidden')
  if [ "$HIDDEN" == "true" ]; then
    continue
  fi
  curl -s http://localhost:5000/api/v1/test-runs/$RUN_ID/report >> report.csv
  RUN_UNDER_TEST=$RUN_ID
done

TEST_STATUS=$(grep 'test.py::TestSimple::test_success' report.csv | cut -d ',' -f7)
if [ "$TEST_STATUS" != "passed" ] ; then
  echo "Success test did not pass!"
  exit 1
fi

TEST_STATUS=$(grep 'test.py::TestSimple::test_failure' report.csv | cut -d ',' -f7)
if [ "$TEST_STATUS" != "failed" ] ; then
  echo "Failure test did not fail!"
  exit 1
fi

TEST_STATUS=$(grep 'test.py::TestSimple::test_record_artifact' report.csv | cut -d ',' -f7)
if [ "$TEST_STATUS" != "passed" ] ; then
  echo "Artifacts record test did not pass!"
  exit 1
fi

TEST_ARTIFACTS=$(grep 'test.py::TestSimple::test_record_artifact' report.csv | cut -d ',' -f8-)
if ! echo "$TEST_ARTIFACTS" | grep -q "file.txt"; then
  echo "file.txt artifacts was not recorded!"
  exit 1
fi

for RUN_ID in $(curl -s http://localhost:5000/api/v1/test-runs | jq -r '.[].id'); do
  curl -s -f http://localhost:5000/api/v1/test-runs/$RUN_ID/artifacts/file.txt > file.txt || true
done

if [ "$(cat file.txt 2>/dev/null)" != "test" ] ; then
  echo "file.txt contents does not match!"
  exit 1
fi

NEW_ID=$(curl -s http://localhost:5000/api/v1/test-runs/$RUN_UNDER_TEST/repeat -H "Content-Type: application/json" -d '"success or conditional_skip"' | jq -r '.id')
STATUS=""
while [ "$STATUS" != "finished" ] && [ "$STATUS" != "failed" ]; do
  STATUS=$(curl -s http://localhost:5000/api/v1/test-runs/$NEW_ID | jq -r '.status')
  sleep 1
done
curl -s http://localhost:5000/api/v1/test-runs/$NEW_ID/report > report.csv
awk -F',' 'FNR>1 && $3 != "" {print $3}' $(ls -tr report.csv) | sort > /tmp/actual-names
cat << EOF > /tmp/expected-names
conditional_skip[test_config0]
success[test_config0]
EOF
if ! diff -q /tmp/expected-names /tmp/actual-names > /dev/null; then
  echo "Unexpected list of executed tests!"
  exit 1
fi

function finish {
  kill $PROTOPLASTER_PID
}
trap finish EXIT



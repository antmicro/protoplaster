#!/bin/bash

set -e

# Create a local output directory for this script's results
OUTPUT_DIR="test_output"
mkdir -p "$OUTPUT_DIR"

# Setup separate workspace directories
rm -rf /tmp/protoplaster/*
mkdir -p /tmp/protoplaster/node1/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/node2/{tests,reports,artifacts}
mkdir -p /tmp/protoplaster/main/tests

# Create devices.yaml
cat <<EOF > /tmp/protoplaster/devices.yaml
node1: localhost:2138
node2: localhost:2139
EOF

# Create the multinode test config
cat <<EOF > /tmp/protoplaster/main/tests/test-multinode-simple.yml
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

# Create the python test using protoplaster module
cat <<EOF > /tmp/protoplaster/test_module.py
from pathlib import Path
from protoplaster import Protoplaster

p = Protoplaster(
    config_dir="/tmp/protoplaster/main/tests",
    test_file="test-multinode-simple.yml",
    external_devices="/tmp/protoplaster/devices.yaml"
)

p.upload_config_all()

run = p.run_tests()

run.wait()

results = run.results()

print("Collected results:")
print()

for result in results.results:
    print(f"Machine: {result.machine}")
    print(f"Status: {result.status}")
    print(f"Report: {result.report_path}")
    print(f"Artifacts: {result.artifacts_path}")


    assert result.status == "failed"

    expected_results = {
        "success[test_config0]": "passed",
        "failure[test_config0]": "failed",
        "conditional_skip[test_config0]": "passed",
        "record_artifact[test_config0]": "passed",
        "configure_runs_once[test_config0]": "passed",
    }

    for test in result.tests:
      print(f"Test: {test.name}, status: {test.status}")
      assert test.status == expected_results[test.name], (
          f"Unexpected status for {test.name}: "
          f"{test.status} != {expected[test.name]}"
      )

    assert result.report_path.exists(), (
        f"Missing report for {result.machine}"
    )

    assert result.artifacts_path.exists(), (
        f"Missing artifacts for {result.machine}"
    )

    artifact_files = list(result.artifacts_path.rglob("*"))

    assert artifact_files, (
        f"No artifacts downloaded for {result.machine}"
    )

    print()

print("All artifact checks passed")

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

# Cleanup function
function finish {
  echo "Stopping servers..."
  kill $PID1 $PID2 2>/dev/null || true
}
trap finish EXIT

# Wait for servers
echo "Waiting for servers to start..."
for port in 2138 2139; do
  while ! curl -s http://localhost:$port/api/v1/configs > /dev/null; do
    sleep 1
  done
done

# Trigger test run on Main Node
echo "Running test_module.py..."
python /tmp/protoplaster/test_module.py

echo "---------------------------------------------------"
echo "Python Module Test: ALL CHECKS PASSED"
echo "Results saved in: $OUTPUT_DIR"
echo "---------------------------------------------------"

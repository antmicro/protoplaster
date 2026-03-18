#!/bin/bash

rm -f srv/protoplaster/reports/*.csv
mkdir -p srv/protoplaster/{tests,reports,artifacts}

cat <<EOF > srv/protoplaster/tests/anchors.yml
includes:
  - anchors1.yml
  - anchors2.yml
EOF

cat <<EOF > srv/protoplaster/tests/anchors1.yml
tests:
  anchors1:
  - simple: &simple
      device: "abcdef"
test-suites:
  local:
    tests:
    - anchors1
EOF

cat <<EOF > srv/protoplaster/tests/anchors2.yml
tests:
  anchors2:
    - simple:
        <<: *simple
test-suites:
  local:
    tests:
    - anchors2
EOF

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts \
    -t anchors.yml --csv report.csv > /dev/null

if ! [[ $? -eq 0 ]]; then
    echo "-> Protoplaster error; included anchors test FAILED"
    exit 1
fi

awk -F',' 'FNR>1 && $2 != "" {print $2}' $(ls -tr srv/protoplaster/reports/*.csv) > /tmp/actual-names

: > /tmp/expected-names
for i in $(seq 1 10); do # class Simple has 5 tests
    echo "simple(abcdef)" >> /tmp/expected-names
done

echo "Names expected:"
while read -r r; do
    echo "   - $r"
done < /tmp/expected-names

if diff -q /tmp/expected-names /tmp/actual-names > /dev/null; then
    echo "-> Included anchors test passed"
    exit
else
    echo "-> Included anchors test FAILED"
    echo "Actual names used in tests:"
    cat /tmp/actual-names
    exit 1
fi

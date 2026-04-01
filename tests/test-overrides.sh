#!/bin/bash

rm -f srv/protoplaster/reports/*.csv
mkdir -p srv/protoplaster/{tests,reports,artifacts}

cat <<EOF > srv/protoplaster/tests/test-no-overrides.yml
tests:
  000:
  - simple:
      device: "foo"
  - simple:
      device: "bar"
  - simple:
      device: "this_name_stays"

  001:
    tests:
      - simple:
          device: "foo"
EOF

cat <<EOF > srv/protoplaster/tests/test-with-overrides.yml
tests:
  000:
  - simple:
      device: "foo"
  - simple:
      device: "bar"
  - simple:
      device: "this_name_stays"

  001:
    tests:
      - simple:
          device: "old_name"

  000.1.simple.device: new_name
  000.0.simple.device: another_new_name
  001.tests.0.simple.device: "overridden"
EOF

cat <<EOF > srv/protoplaster/tests/test-overrides-includes.yml
includes: [test-no-overrides.yml]
tests:
  000.1.simple.device: new_name
  000.0.simple.device: another_new_name
tests.001.tests.0.simple.device: "overridden"
EOF

cat <<EOF > srv/protoplaster/tests/test-overrides-anchors-a.yml
conf_simple: &predefined
  device: "this_should_not_appear"
EOF

cat <<EOF > srv/protoplaster/tests/test-overrides-anchors-b.yml
tests:
  000:
  - simple:
      <<: *predefined
  - simple:
      <<: *predefined
  - simple: *predefined
  - simple:
      <<: *predefined
EOF

cat <<EOF > srv/protoplaster/tests/test-overrides-anchors.yml
includes:
- test-overrides-anchors-a.yml
- test-overrides-anchors-b.yml

conf_simple.device: "this_name_stays"
tests.000.1.simple.device: "new_name"
tests.000.0.simple.device: "another_new_name"
tests.000.3.simple.device: "overridden"
EOF

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts \
    -t test-no-overrides.yml --csv report.csv \
    --override={"tests.000.1.simple.device: new_name","tests.000.0.simple.device: another_new_name","tests.001.tests.0.simple.device: overridden"} > /dev/null
awk -F',' 'FNR>1 && $2 != "" {print $2}' $(ls -tr srv/protoplaster/reports/*.csv) | uniq > /tmp/actual-names-0

rm -f srv/protoplaster/reports/*.csv

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts \
    -t test-with-overrides.yml --csv report.csv > /dev/null
awk -F',' 'FNR>1 && $2 != "" {print $2}' $(ls -tr srv/protoplaster/reports/*.csv) | uniq > /tmp/actual-names-1

rm -f srv/protoplaster/reports/*.csv

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts \
    -t test-overrides-includes.yml --csv report.csv > /dev/null
awk -F',' 'FNR>1 && $2 != "" {print $2}' $(ls -tr srv/protoplaster/reports/*.csv) | uniq > /tmp/actual-names-2

rm -f srv/protoplaster/reports/*.csv

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts \
    -t test-overrides-anchors.yml --csv report.csv > /dev/null
awk -F',' 'FNR>1 && $2 != "" {print $2}' $(ls -tr srv/protoplaster/reports/*.csv) | uniq > /tmp/actual-names-3

exit_code=0

cat << EOF > /tmp/expected-names
simple(another_new_name)
simple(new_name)
simple(this_name_stays)
simple(overridden)
EOF

echo "Names expected:"
while read -r r; do
    echo "   - $r"
done < /tmp/expected-names

for i in $(seq 0 3); do
    if diff -q /tmp/expected-names /tmp/actual-names-$i > /dev/null; then
        echo "-> $i: Overrides applied successfully"
    else
        echo "-> $i: FAILED to apply overrides"
        echo "Actual names used in tests:"
        cat /tmp/actual-names-$i
        exit_code=1
    fi
done

exit $exit_code

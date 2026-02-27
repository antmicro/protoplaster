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
  000.1.simple.device: new_name
  000.0.simple.device: another_new_name
EOF

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts \
    -t test-no-overrides.yml --csv report.csv --override={"tests.000.1.simple.device: new_name","tests.000.0.simple.device: another_new_name"} > /dev/null
awk -F',' 'FNR>1 && $1 != "" {print $1}' $(ls -tr srv/protoplaster/reports/*.csv) | uniq > /tmp/actual-names-0

rm -f srv/protoplaster/reports/*.csv

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts \
    -t test-with-overrides.yml --csv report.csv > /dev/null
awk -F',' 'FNR>1 && $1 != "" {print $1}' $(ls -tr srv/protoplaster/reports/*.csv) | uniq > /tmp/actual-names-1

exit_code=0

cat << EOF > /tmp/expected-names
simple(another_new_name)
simple(new_name)
simple(this_name_stays)
EOF

echo "Names expected:"
while read -r r; do
    echo "   - $r"
done < /tmp/expected-names

for i in $(seq 0 1); do
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

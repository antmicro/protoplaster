#!/bin/bash

rm -f srv/protoplaster/reports/*.csv
mkdir -p srv/protoplaster/{tests,reports,artifacts}

cat <<EOF > srv/protoplaster/tests/test-execution-order.yml
tests:
  bbb:
  - simple:
      device: "foo"
  - network:
      interface: "eth0"
  - simple:
      device: "bar"
  - network:
      interface: "eth1"
  aaa:
  - network:
      interface: "eth222"
  - simple:
      device: "buz"
  - network:
      interface: "eth333"
test-suites:
  local:
    tests:
    - foo
    - baz
EOF

protoplaster --test-dir srv/protoplaster/tests --reports-dir srv/protoplaster/reports --artifacts-dir srv/protoplaster/artifacts -t test-execution-order.yml --csv report.csv > /dev/null

awk -F',' 'FNR>1 && $1 != "" {print $1}' $(ls -tr srv/protoplaster/reports/*.csv) | uniq > /tmp/actual-order

cat << EOF > /tmp/expected-order
simple(foo)
eth0
simple(bar)
eth1
eth222
simple(buz)
eth333
EOF

exit_code=0
echo "execution order check:"

if diff -q /tmp/expected-order /tmp/actual-order > /dev/null; then
    echo "-> Execution order is correct"
    while read -r r; do
        echo "   - $r"
    done < /tmp/actual-order
else
    echo "-> Execution order is INCORRECT!"
    echo "Expected order:"
    cat /tmp/expected-order
    echo "Actual order found in CSV:"
    cat /tmp/actual-order
    exit_code=1
fi
echo

exit $exit_code
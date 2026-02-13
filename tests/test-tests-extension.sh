#!/bin/bash

mkdir -p /srv/protoplaster/{tests,reports,artifacts}

cat <<EOF > /srv/protoplaster/tests/test-extended.yml
tests:
  test:
  # check if ordinary test still works as it should
  - simple:
      device: "simple"
  # check if attributes are correctly set in base class
  # 'test_conditional_skip' should be skipped
  - extended_simple:
      device: "skip"
  # check if additional logic is correctly extended
  # 'test_conditional_skip' should be skipped
  - extended_simple:
      device: "extended"
      skipped_devices:
        - extended
test-suites:
  local:
    tests:
    - test
EOF


protoplaster --test-dir /srv/protoplaster/tests --reports-dir /srv/protoplaster/reports --artifacts-dir /srv/protoplaster/artifacts -t test-extended.yml --csv report.csv > /dev/null

cat << EOF > /tmp/check-report-regex
^simple\(simple\),success,[^,]+,[^,]+,,passed,
^simple\(simple\),failure,[^,]+,[^,]+,[^,]+,failed,
^simple\(simple\),conditional_skip,[^,]+,[^,]+,,passed,
^simple\(simple\),record_artifact,[^,]+,[^,]+,,passed,
^extended_simple\(skip\),conditional_skip,[^,]+,[^,]+,Skipped,skipped,
^extended_simple\(extended\),conditional_skip,[^,]+,[^,]+,Skipped: [^,]+,skipped,
EOF

exit_code=0
echo "report check:"
while read -r r;do
    echo "- '$r\':"
    echo -n "-> "
    if grep -Eq "$r" /srv/protoplaster/reports/report.csv;
    then
        echo found
    else
        echo not found
        exit_code=1
    fi
    echo
done < /tmp/check-report-regex

exit $exit_code

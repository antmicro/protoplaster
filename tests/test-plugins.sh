#!/bin/bash

# Cleanup
rm -f srv/protoplaster/reports/*.csv
rm -f /tmp/plugin_hooks.log
mkdir -p srv/protoplaster/{tests,reports,artifacts,plugins}

cat <<EOF > srv/protoplaster/tests/test-plugin-config.yml
tests:
  plugin_verification:
  - simple:
      device: "pluggy_device"
  - simple:
      device: "pluggy_device2"
test-suites:
  local:
    tests:
    - plugin_verification
EOF

cat <<EOF > srv/protoplaster/plugins/test_plugin.py
from protoplaster.conf.plugin_manager import hookimpl

class ProtoplasterPlugin:
    @hookimpl
    def before_test_setup(self, test_class):
        # If this runs before configure(), test_class.counter will still be 0
        counter_val = getattr(test_class, 'counter', 'MISSING')
        with open("/tmp/plugin_hooks.log", "a") as f:
            f.write(f"SETUP:{test_class.__name__}:counter={counter_val}\n")

    @hookimpl
    def before_test_function(self, test_instance, test_function):
        with open("/tmp/plugin_hooks.log", "a") as f:
            f.write(f"BEFORE:{test_instance.name()}:{test_function.__name__}\n")

    @hookimpl
    def after_test_function(self, test_instance, test_function):
        with open("/tmp/plugin_hooks.log", "a") as f:
            f.write(f"AFTER:{test_instance.name()}:{test_function.__name__}\n")
EOF

protoplaster --test-dir srv/protoplaster/tests \
             --reports-dir srv/protoplaster/reports \
             --artifacts-dir srv/protoplaster/artifacts \
             -t test-plugin-config.yml \
             --plugins srv/protoplaster/plugins \
             --csv report.csv > /tmp/protoplaster-plugin-out.txt 2>&1

exit_code=0
echo "Plugin functionality test:"

# TEST: Plugin Registration
if grep -q "Registered plugin:" /tmp/protoplaster-plugin-out.txt; then
    echo "-> [PASS] Plugin registration logged successfully."
else
    echo "-> [FAIL] Plugin registration not found in console output."
    exit_code=1
fi

if [ ! -f /tmp/plugin_hooks.log ]; then
    echo "-> [FAIL] Plugin hooks log file not found. Plugins didn't run!"
    exit 1
fi

# TEST: Pre-configure hook runs once per test group module entry, and before configure()
# Since we have 2 devices in the YAML, this should appear exactly 2 times.
SETUP_COUNT=$(grep -c "SETUP:TestSimple:counter=0" /tmp/plugin_hooks.log || true)

if [ "$SETUP_COUNT" -eq 2 ]; then
    echo "-> [PASS] before_test_setup ran exactly once per device configuration AND before configure() (counter was 0)."
else
    echo "-> [FAIL] before_test_setup did not run exactly twice before configure! Found $SETUP_COUNT times."
    exit_code=1
fi

# TEST: Normal execution verification
if grep -q "BEFORE:simple(pluggy_device):test_success" /tmp/plugin_hooks.log; then
    echo "-> [PASS] before_test_function hook fired correctly for test_success."
else
    echo "-> [FAIL] before_test_function hook did not fire for test_success."
    exit_code=1
fi

if grep -q "AFTER:simple(pluggy_device):test_success" /tmp/plugin_hooks.log; then
    echo "-> [PASS] after_test_function hook fired correctly for test_success."
else
    echo "-> [FAIL] after_test_function hook did not fire for test_success."
    exit_code=1
fi

# TEST: Plugins still run after test failure
if grep -q "AFTER:simple(pluggy_device):test_failure" /tmp/plugin_hooks.log; then
    echo "-> [PASS] after_test_function ran successfully even after 'test_failure' failed."
else
    echo "-> [FAIL] after_test_function did not run for 'test_failure'."
    exit_code=1
fi

if [ $exit_code -ne 0 ]; then
    echo ""
    echo " Console Output "
    cat /tmp/protoplaster-plugin-out.txt
    echo " Hook File Content "
    cat /tmp/plugin_hooks.log
fi

exit $exit_code
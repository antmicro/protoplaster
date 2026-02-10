import pytest
from protoplaster.conf.module import ModuleName
from protoplaster.tests.pmic.DA9062.DA9062 import DA9062, ldo_selection


@ModuleName("DA9062")
class TestDA9062:
    """
    {% macro TestDA9062(prefix) -%}
    DA9062 device test
    ----------------
    This module provides tests for DA9062:
    {%- endmacro %}
    """

    def setup_class(self):
        self.current_selections = getattr(self, "current_selections", [])
        self.current_voltages = getattr(self, "current_voltages", [])
        self.smbus_force = getattr(self, "smbus_force", False)
        self.pmic = DA9062(self.bus, self.address, self.smbus_force)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if DA9062 responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.pmic.is_alive(
        ), f"DA9062 does not respond correctly. Reason: {self.pmic.fail_reason}"

    def test_variant_id(self):
        """
        {% macro test_variant_id(device) -%}
          verify that the DA9062 PMIC returns the expected variant ID: `{{ device['variant_id'] }}`
        {%- endmacro %}
        """
        val = self.pmic.get_variant_id()
        assert val == self.variant_id, f"The Variant ID does not match. Expected: {self.variant_id}, Actual: {val}"

    def test_customer_id(self):
        """
        {% macro test_customer_id(device) -%}
          verify that the DA9062 PMIC returns the expected customer ID: `{{ device['customer_id'] }}`
        {%- endmacro %}
        """
        val = self.pmic.get_customer_id()
        assert val == self.customer_id, f"The Customer ID does not match. Expected: {self.customer_id}, Actual: {val}"

    def test_config_id(self):
        """
        {% macro test_config_id(device) -%}
          verify that the DA9062 PMIC returns the expected config ID: `{{ device['config_id'] }}`
        {%- endmacro %}
        """
        val = self.pmic.get_config_id()
        assert val == self.config_id, f"The Config ID does not match. Expected: {self.config_id}, Actual: {val}"

    def test_current_selections(self):
        """
        {% macro test_current_selections(device) -%}
        verify selection of: {% for ldo in device.current_selections -%}
            LDO{{ ldo['ldo_id'] }}, {% endfor -%}
        {%- endmacro %}
        """
        if not self.current_selections:
            pytest.skip("current_selections parameter not set")

        for ldo in self.current_selections:
            val = self.pmic.get_ldo_curr_selection(ldo['ldo_id'])
            exp = ldo_selection[ldo['ldo_selection']]
            assert val == exp, f"The selection of ldo({ldo['ldo_id']}) does not match. Expected: {exp}, Actual: {val}"

    def test_current_ldos(self):
        """
        {% macro test_current_ldos(device) -%}
        verify voltage of: {% for ldo in device['current_voltages'] -%}LDO{{ ldo['ldo_id'] }}({{ ldo['min_voltage'] or '-inf'}}, {{ ldo['max_voltage'] or '+inf'}}), {% endfor -%}
        {%- endmacro %}
        """
        if not self.current_voltages:
            pytest.skip("current_voltages parameter not set")

        for ldo in self.current_voltages:
            curr_voltage = self.pmic.get_ldo_curr_voltage(ldo['ldo_id'])
            if 'max_voltage' in ldo:
                assert curr_voltage <= ldo['max_voltage'], \
                    f"The voltage of ldo({ldo['ldo_id']}) is {curr_voltage}, above max {ldo['max_voltage']}."
            if 'min_volatge' in ldo:
                assert ldo['min_volatge'] <= curr_voltage, \
                    f"The voltage of ldo({ldo['ldo_id']}) is {curr_voltage}, below min {ldo['min_volatge']}."

    def name(self):
        return f"DA9062({self.bus}, {hex(self.address)})"

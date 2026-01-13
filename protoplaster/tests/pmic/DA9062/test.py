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
        assert self.pmic.is_alive(), "DA9062 does not respond correctly"

    def test_variant_id(self):
        """
        {% macro test_variant_id(device) -%}
          verify that the DA9062 PMIC returns the expected variant ID: `{{ device['variant_id'] }}`
        {%- endmacro %}
        """
        assert self.pmic.get_variant_id(
        ) == self.variant_id, "The Variant ID does not match the provided value"

    def test_customer_id(self):
        """
        {% macro test_customer_id(device) -%}
          verify that the DA9062 PMIC returns the expected customer ID: `{{ device['customer_id'] }}`
        {%- endmacro %}
        """
        assert self.pmic.get_customer_id(
        ) == self.customer_id, "The Customer ID does not match the provided value"

    def test_config_id(self):
        """
        {% macro test_config_id(device) -%}
          verify that the DA9062 PMIC returns the expected config ID: `{{ device['config_id'] }}`
        {%- endmacro %}
        """
        assert self.pmic.get_config_id(
        ) == self.config_id, "The Config ID does not match the provided value"

    def test_current_selections(self):
        """
        {% macro test_current_selections(device) -%}
        verify selection of: {% for ldo in device.current_selections -%}
            LDO{{ ldo['ldo_id'] }}, {% endfor -%}
        {%- endmacro %}
        """
        for ldo in self.current_selections:
            assert self.pmic.get_ldo_curr_selection(
                ldo['ldo_id']
            ) == ldo_selection[ldo[
                'ldo_selection']], f"The selction of ldo({ldo['ldo_id']}) does not match the provided value"

    def test_current_ldos(self):
        """
        {% macro test_current_ldos(device) -%}
        verify voltage of: {% for ldo in device['current_voltages'] -%}LDO{{ ldo['ldo_id'] }}({{ ldo['min_voltage'] or '-inf'}}, {{ ldo['max_voltage'] or '+inf'}}), {% endfor -%}
        {%- endmacro %}
        """

        for ldo in self.current_voltages:
            curr_voltage = self.pmic.get_ldo_curr_voltage(ldo['ldo_id'])
            if 'max_voltage' in ldo:
                assert curr_voltage <= ldo[
                    'max_voltage'], f"The voltage of ldo({ldo['ldo_id']}) is above the maximum allowed value."
            if 'min_volatge' in ldo:
                assert ldo[
                    'min_volatge'] <= curr_voltage, f"The voltage of ldo({ldo['ldo_id']}) is below the minimum allowed value."

    def name(self):
        return f"DA9062({self.bus}, {self.address})"

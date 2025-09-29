from protoplaster.adc.adc.adc import ADC
from protoplaster.conf.module import ModuleName


@ModuleName("adc")
class TestADC:
    """
    {% macro TestADC(prefix) -%}
    ADC device test
    ---------------
    This module provides tests for ADC devices:
    {%- endmacro %}
    """

    def setup_class(self):
        self.adc = ADC(self.sysfs_path)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if `{{ device['path'] }}` exists
        {%- endmacro %}
        """
        assert self.adc.is_alive(), "ADC does not respond correctly"

    def test_device_name(self):
        """
        {% macro test_device_name(device) -%}
          check if the device name is `{{ device['device_name'] }}`
        {%- endmacro %}
        """
        assert self.adc.get_device_name(
        ) == self.device_name, "The device name is not correct"

    def test_read_adc(self):
        """
        {% macro test_read_adc(device) -%}
          verify that the ADC output stays between the defined minimum({{ device['min_voltage'] or '-inf'}}) and maximum({{device['max_voltage'] or '+inf'}})
        {%- endmacro %}
        """
        curr_voltage = self.adc.read_adc(self.channel)
        if hasattr(self, 'max_voltage'):
            assert curr_voltage <= self.max_voltage, f"The voltage is above the maximum allowed value."
        if hasattr(self, 'min_voltage'):
            assert self.min_voltage <= curr_voltage, f"The voltage is below the minimum allowed value."

    def name(self):
        return f"ADC({self.sysfs_path})"
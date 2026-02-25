from collections import defaultdict

import pytest

from protoplaster.conf.module import ModuleName
from protoplaster.tests.pmic.UCD90320U.UCD90320U import UCD90320U, UCD90320URegs


@ModuleName("UCD90320U")
class TestUCD90320U:
    """
    {% macro TestUCD90320U(prefix) -%}
    UCD90320U device test
    ----------------
    {% do prefix.append('') %}
    This module provides tests for UCD90320U:
    {%- endmacro %}
    """

    def configure(self):
        self.smbus_force = getattr(self, "smbus_force", False)
        self.pmic = UCD90320U(self.bus, self.address, self.smbus_force)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if UCD90320U responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.pmic.is_alive(), "UCD90320U does not respond correctly"

    def test_clear_faults(self):
        """
        {% macro test_clear_faults(device) -%}
          clear the faults latched by the UCD90320U in preparation for
          a new test run
        {%- endmacro %}
        """
        if getattr(self, "check_faults", False):
            pytest.skip("Check run - not clearing faults")
        self.pmic.clear_faults()

    def test_read_faults(self):
        """
        {% macro test_read_faults(device) -%}
          read the faults latched by the UCD90320U after the test run
        {%- endmacro %}
        """
        if not getattr(self, "check_faults", False):
            pytest.skip("Clear run - not reading faults")

        status = self.pmic.read_status_faults()
        cml = self.pmic.read_cml_faults()
        rail_faults = defaultdict(dict)
        for rail in range(getattr(self, "rails", UCD90320U.NUM_RAILS)):
            rail_faults[rail]["vout"] = self.pmic.read_rail_faults(
                rail, UCD90320URegs.STATUS_VOUT)
            rail_faults[rail]["iout"] = self.pmic.read_rail_faults(
                rail, UCD90320URegs.STATUS_IOUT)
            rail_faults[rail]["temperature"] = self.pmic.read_rail_faults(
                rail, UCD90320URegs.STATUS_TEMPERATURE)

        failure_reasons = []
        if status:
            failure_reasons.append(f"Status faults: {status}")
        if cml:
            failure_reasons.append(f"CML faults: {cml}")
        failure_reasons.extend(f"Rail {i} {typ} faults: {faults}"
                               for i, rail in rail_faults.items()
                               for typ, faults in rail.items() if faults)

        assert not failure_reasons, failure_reasons

    def name(self):
        return f"UCD90320U({self.bus}, {hex(self.address)})"

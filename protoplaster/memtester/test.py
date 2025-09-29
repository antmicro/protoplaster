from protoplaster.conf.module import ModuleName
from protoplaster.memtester.memtester import run_memtester


@ModuleName("memtester")
class TestDMA:
    """
    {% macro TestDMA(prefix) -%}
    DMA test
    --------
    This module provides tests for DMA:
    {%- endmacro %}
    """

    def setup_class(self):
        if not hasattr(self, "device"):
            self.device = None
        if not hasattr(self, "physaddr"):
            self.physaddr = None

    def test_memory(self):
        """
        {% macro test_memory(device) -%}
         verify the integrity of memory of size {{ device['memory']}}{{ " on device `" ~ device['device'] ~ "`" if device['device'] is defined else "" }} with {{ device['iterations'] }} iterations.
        {%- endmacro %}
        """
        res = run_memtester(self.memory, self.iterations, self.device,
                            self.physaddr)
        assert res == 0, f"Memory error was detected by memtester - return code: {res}"

    def name(self):
        return '/dev/mem' if self.device is None else self.device

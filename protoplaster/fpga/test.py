from protoplaster.conf.module import ModuleName
import os


@ModuleName("fpga")
class TestFPGA:

    def test_sysfs_interface(self):
        assert os.path.exists(self.sysfs_interface)

    def test_flashing_bitstream(self):
        assert os.path.exists(f"/lib/firmware/{self.bitstream_path}"), "Bitstream file does not exist"
        with open(self.sysfs_interface, 'w') as file:
            file.write(self.bitstream_path)
        anwser = input("Did the bitstream work? [y/n] ")
        assert anwser.lower() == 'y', "The bitstream failed"

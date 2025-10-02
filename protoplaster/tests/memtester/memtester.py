#!/usr/bin/env python3

import subprocess


def run_memtester(memory, iterations=1, device=None, physaddr=None):
    cmd = ["memtester"]
    # dropping device if physaddress is not provided
    if physaddr:
        cmd += ["-p", physaddr]
        if device:
            cmd += ["-d", device]
    cmd += [memory]
    if iterations:
        cmd += [str(iterations)]

    p = subprocess.run(cmd,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    exit_code = p.returncode
    return exit_code

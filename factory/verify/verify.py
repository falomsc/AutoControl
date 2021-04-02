import re
import time
from typing import List, Dict

from factory.verify.get_verify_config import get_verify_tx_config
from tools.ssh import SSHConnection


def check_connection(s: SSHConnection, t: int = 10) -> None:
    for i in range(t):
        sync = s.rfsw_cmd("cpri init_ant 0 10")
        if re.search("CPRI synced", sync):
            break
        time.sleep(2)
        if i == t - 1:
            raise Exception("SYNC FAILED")
    s.rfsw_cmd("cpri read_ant_eid 0")
    s.rfsw_cmd("cpri ant_t14_calibration 0")
    s.rfsw_cmd("ant write 0 0x90048 0xffffffff")


def tx_verify(s: SSHConnection, tx_pipe_list: List[List[List[Dict[str, str]]]]) -> None:
    for tx_freq_list in tx_pipe_list:
        pipe = int(tx_freq_list[0][0].get("pipe"))
        s.rfsw_cmd("ant rf reset 0")
        if pipe == 0:
            s.rfsw_cmd("ant squatch3 setTddMode 0 2")
            s.rfsw_cmd("madura create_from_draco 0.{pipe}".format(pipe=pipe))
            s.rfsw_cmd("ant rf init 0 {pipe} 100000".format(pipe=pipe))
            s.rfsw_cmd("ant wave_mem_write 0 0 fpga_out_100MHz_14dBFS_245p76MSps_cfr7p5.bin")
            s.rfsw_cmd("ant write 0 0x270060 0xf")
            s.rfsw_cmd("ant write 0 0x270048 0x7fff0002")
        elif pipe in (1, 2):
            s.rfsw_cmd("madura create_from_draco 0.{pipe}".format(pipe=pipe))
            s.rfsw_cmd("ant rf init 0 {pipe} 20000".format(pipe=pipe))
            s.rfsw_cmd("ant wave_mem_write 0 0 fpga_out_20MHz_14dBFS_245p76MSps_cfr7p5.bin")
            s.rfsw_cmd("ant write 0 0x270060 0xf0")
            s.rfsw_cmd("ant write 0 0x270048 0x7fff0002")
        for tx_branch_list in tx_freq_list:
            freq = int(float(tx_branch_list[0].get("freq")) * 1e3)
            s.rfsw_cmd("ant tx config 0 {pipe} {freq}".format(pipe=pipe, freq=freq))
            for tx_branch in tx_branch_list:
                branch = int(tx_branch.get("branch"))
                power = float(tx_branch.get("power"))
                channel = branch % 4
                s.rfsw_cmd("ant tx set_power 0 {branch} {power}".format(branch=branch, power=power))
                s.rfsw_cmd("ant tx enable 0 {branch} 1 1".format(branch=branch))
                s.pprint("\n")
                s.pprint("#####################")
                s.pprint(" frequency: %d, branch: %d " % (freq, branch))
                s.pprint("#####################")
                s.pprint("\n")
                while True:
                    time.sleep(3)
                    s1 = s.rfsw_cmd("madura ClgcStatusGet 0.{pipe} {channel}".format(pipe=pipe, channel=channel))
                    try:
                        loop_gain = float(re.search("loop_gain_dB = (-?\d+\.?\d*)", s1).group(1))
                    except AttributeError:
                        continue
                    s2 = s.rfsw_cmd("madura ClgcConfigGet 0.{pipe} {channel}".format(pipe=pipe, channel=channel))
                    expected_loop_gain = float(re.search('"clgcExpectedLoopGain_dB": (-?\d+\.?\d*)', s2).group(1))
                    res = abs(abs(loop_gain) - abs(expected_loop_gain))
                    if res < 0.1:
                        s.pprint("\nabs(abs(%.4f) - abs(%.4f)) = %.4f < 0.1 PASS\n" % (loop_gain, expected_loop_gain, res))
                        break
                    else:
                        s.pprint("\nabs(abs(%.4f) - abs(%.4f)) = %.4f >= 0.1 RETRY\n" % (loop_gain, expected_loop_gain, res))
                while True:
                    time.sleep(3)
                    s3 = s.rfsw_cmd("madura DpdStatusGet 0.{pipe} {channel}".format(pipe=pipe, channel=channel))
                    update_count = int(re.search("update_count: (\d+\.?\d*)", s3).group(1))
                    if update_count >= 5:
                        break
                s.rfsw_cmd("ant tx get_atten 0 {branch}".format(branch=branch))
                s.rfsw_cmd("ant tx enable 0 {branch} 0".format(branch=branch))


def rx_verify():
    pass


if __name__ == '__main__':
    s = SSHConnection(host="192.168.255.129", port=22, username="toor4nsn", password="oZPS0POrRieRtu")
    tx_pipe_list = get_verify_tx_config("./tx_verify_all.xml")
    check_connection(s)
    tx_verify(s, tx_pipe_list)

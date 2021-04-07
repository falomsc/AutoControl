import re
import time
from typing import List, Dict

from factory.cali.get_cali_config import get_cali_tx_config
from tools.ssh import SSHConnection
from tools.visa import VisaConnection
from tools.visa_cmd_ks import channel_power


class Calibration:
    def __init__(self, s: SSHConnection, v: VisaConnection):
        self._s = s
        self._v = v

    def check_connection(self, t: int = 10) -> None:
        for i in range(t):
            sync = self._s.rfsw_cmd("cpri init_ant 0 10")
            if re.search("CPRI synced", sync):
                break
            time.sleep(2)
            if i == t - 1:
                raise Exception("SYNC FAILED")
        self._s.rfsw_cmd("cpri read_ant_eid 0")
        self._s.rfsw_cmd("cpri ant_t14_calibration 0")
        self._s.rfsw_cmd("ant write 0 0x90048 0xffffffff")

    def tx_cali(self, tx_pipe_list: List[List[List[Dict[str, str]]]]) -> None:
        # bb = False
        for tx_freq_list in tx_pipe_list:
            pipe = int(tx_freq_list[0][0].get("pipe"))
            self._s.rfsw_cmd("ant rf reset 0")
            self._s.rfsw_cmd("ant flash unlock_factory_flash 0")
            self._s.rfsw_cmd("ant cal format_nvm 0 {pipe}".format(pipe=pipe))
            self._s.rfsw_cmd("ant rf reset 0")
            if pipe == 0:
                self._s.rfsw_cmd("ant squatch3 setTddMode 0 2")
                self._s.rfsw_cmd("madura create_from_draco 0.{pipe}".format(pipe=pipe))
                self._s.rfsw_cmd("ant rf init 0 {pipe} 100000".format(pipe=pipe))
            elif pipe in (1, 2):
                self._s.rfsw_cmd("madura create_from_draco 0.{pipe}".format(pipe=pipe))
                self._s.rfsw_cmd("ant rf init 0 {pipe} 20000".format(pipe=pipe))
            self._s.rfsw_cmd("ant cal tx clear 0 {pipe}".format(pipe=pipe))
            self._s.rfsw_cmd("ant cal tx start 0 fwd_freq {pipe}".format(pipe=pipe))
            self._s.rfsw_cmd("ant wave_mem_write 0 0 fpga_out_20MHz_14dBFS_245p76MSps_cfr7p5.bin")
            if pipe == 0:
                self._s.rfsw_cmd("ant write 0 0x270060 0xf")
            elif pipe in (1, 2):
                self._s.rfsw_cmd("ant write 0 0x270060 0xf0")
            self._s.rfsw_cmd("ant write 0 0x270048 0x7fff0002")
            for tx_branch_list in tx_freq_list:
                freq = int(float(tx_branch_list[0].get("freq")) * 1e3)
                # TODO set powermeter frequency
                self._s.rfsw_cmd("ant cal tx set_freq 0 {pip} {freq}".format(pip=-pipe**2+5*pipe, freq=freq))
                for tx_branch in tx_branch_list:
                    branch = int(tx_branch.get("branch"))
                    gain_list = list(map(int, tx_branch.get("gain_list").split(",")))
                    channel = branch % 4
                    self._s.pprint("\n")
                    self._s.pprint("#####################")
                    self._s.pprint(" frequency: %d, branch: %d " % (freq, branch))
                    self._s.pprint("#####################")
                    self._s.pprint("\n")
                    for gain in gain_list:
                        self._s.rfsw_cmd("ant cal tx set_gain 0 {branch} {gain}".format(branch=branch, gain=gain))
                        self._s.rfsw_cmd("ant tx enable 0 {branch} 1 1".format(branch=branch))
                        for i in range(10):
                            time.sleep(3)
                            s1 = self._s.rfsw_cmd("madura ClgcStatusGet 0.{pipe} {channel}".format(pipe=pipe, channel=channel))
                            try:
                                loop_gain = float(re.search("loop_gain_dB = (-?\d+\.?\d*)", s1).group(1))
                            except AttributeError:
                                continue
                            res = abs(abs(loop_gain) - abs(gain))
                            if res < 0.1:
                                self._s.pprint("\nabs(abs(%.4f) - abs(%d)) = %.4f < 0.1 PASS\n" % (loop_gain, gain, res))
                                break
                            else:
                                self._s.pprint("\nabs(abs(%.4f) - abs(%d)) = %.4f >= 0.1 RETRY\n" % (loop_gain, gain, res))
                            if i == 19:
                                raise Exception("CLGC CANNOT CONVERGE!")
                        # TODO get power
                        rf_params = dict(freq=str(freq/1e3), bandwidth="20", loss="-28")
                        power = channel_power(self._v, rf_params)
                        self._s.pprint("\npower is %f\n" % power)

                        # if not bb and freq == 3460000 and branch == 1:
                        #     self._s.rfsw_cmd("madura ArmMemDump 0.{pipe} /tmp/armdump.bin".format(pipe=pipe))
                        #     bb = True
                        #     input("CCLLGGCC")

                        if power < 10:
                            self._s.pprint("\n************* ")
                            self._s.pprint("LOW POWER!")
                            self._s.pprint(" *************\n")
                            # self._s.rfsw_cmd("madura ArmMemDump 0.{pipe} /tmp/armdump.bin".format(pipe=pipe))
                            while True:
                                self._s.pprint("\n")
                                cmd = input("Please enter command:")
                                self._s.rfsw_cmd(cmd)
                        self._s.rfsw_cmd("ant cal tx set_meas 0 {branch} {power}".format(branch=branch, power=power))
                    self._s.rfsw_cmd("ant tx enable 0 {branch} 0".format(branch=branch))
            self._s.rfsw_cmd("ant cal tx stop 0 {pipe}".format(pipe=pipe))
            self._s.rfsw_cmd("ant cal tx show 0 {pipe}".format(pipe=pipe))
            self._s.rfsw_cmd("ant flash lock_flash 0")


if __name__ == '__main__':
    for i in range(50):
        s = SSHConnection(hostname="192.168.255.129", port=22, username="toor4nsn", password="oZPS0POrRieRtu")
        v = VisaConnection("TCPIP0::192.168.255.125::inst0::INSTR", timeout=10000)
        tx_pipe_list = get_cali_tx_config("./tx_cali_5g.xml")
        ca = Calibration(s, v)
        ca.check_connection()
        ca.tx_cali(tx_pipe_list)
        print("******** 第 %d 校准完毕 ********" % (i+1))

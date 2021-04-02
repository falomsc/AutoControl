import re
import time
from typing import Dict, List

from tools.ssh import SSHConnection
from tools.visa import VisaConnection


class Calibration:
    def __init__(self, s: SSHConnection, sw: VisaConnection, pm: VisaConnection, sg: VisaConnection) -> None:
        """

        :param s:
        :param sw: switch: VisaConnection("GPIB::9")
        :param p: power meter: VisaConnection("GPIB::13")
        :param sg: signal generator
        """
        self._s = s
        self._sw = sw
        self._pm = pm
        self._sg = sg

    # TODO offset
    def set_powermeter_freq(self, freq: float, offset: float) -> None:
        self._pm.send_cmd(":SENS1:CORR:GAIN2:STAT ON;")
        self._pm.send_cmd(":SENS1:CORR:GAIN2:INP:MAGN %.2f" % offset)
        self._pm.send_cmd(":SENS1:FREQ %.2f" % (freq * 1e6))
        self._pm.send_cmd(":SENS2:FREQ %.2f" % (freq * 1e6))

    def get_tx_power(self) -> float:
        self._pm.send_cmd("UNIT:POW dBm")
        p = self._pm.rec_cmd("FETC1?")
        return float(p)

    def switch(self, channel: int) -> None:
        pass

    def generate_rx_signal(self, freq: float, amp: float) -> None:
        pass

    def generator_on(self):
        pass

    def generator_off(self):
        pass

    def tx_calibrate_freq_point(self, tx_params_freq: Dict[str, str]) -> None:
        """

        :param tx_params_freq: {"pipe":str, "branch":str, "freq":str, "gainlist":list}
        :return:
        """
        settings_dict = {"pipe": int(tx_params_freq.get("pipe")),
                         "branch": int(tx_params_freq.get("branch")),
                         "freq": float(tx_params_freq.get("freq")) * 1000,
                         "gainlist": list(map(int, tx_params_freq.get("gainlist").split(","))),
                         "channel": int(tx_params_freq.get("branch")) % 4}

        self._s.rfsw_cmd("ant cal tx set_freq 0 {branch} {freq}".format(**settings_dict))
        for gain_value in settings_dict["gainlist"]:
            self._s.rfsw_cmd("ant cal tx set_gain 0 {branch} {gain}".format(**settings_dict))
            self._s.rfsw_cmd("ant tx enable 0 {branch} 1 1".format(**settings_dict))
            for i in range(20):
                clgc_log = self._s.rfsw_cmd("madura ClgcStatusGet 0.{pipe} {channel}".format(**settings_dict))
                loop_gain = float(re.search("loop_gain_dB = (\d+\.?\d*)", clgc_log).group(1))
                if abs(abs(loop_gain) - abs(gain_value)) < 0.1:
                    break
                if i == 19:
                    raise Exception("CLGC CANNOT CONVERGE!")
                time.sleep(2)
            p = self.get_tx_power()
            self._s.rfsw_cmd("ant cal tx set_meas 0 {branch} {power}".format(**settings_dict, power=p))
            self._s.rfsw_cmd("ant tx enable 0 {branch} 0".format(**settings_dict))

    def tx_process(self, tx_params_pipe_list: List[List[List[Dict[str, str]]]]) -> None:
        """

        :param tx_params_pipe_list:
        :return:
        """
        central_freq = {"0": 3575, "1": 2655, "2": 2155}
        for tx_params_branch_list in tx_params_pipe_list:
            pip = tx_params_branch_list[0][0].get("pipe")
            self.set_powermeter_freq(central_freq[pip])
            self._s.rfsw_cmd("ant rf reset 0")
            self._s.rfsw_cmd("ant flash unlock_factory_flash 0")
            self._s.rfsw_cmd("ant cal format_nvm 0 {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant rf reset 0")
            if pip == 0:
                self._s.rfsw_cmd("ant squatch3 setTddMode 0 2")
            self._s.rfsw_cmd("madura create_from_draco 0.{pipe}".format(pipe=pip))
            if pip == 0:
                self._s.rfsw_cmd("ant rf init 0 {pipe} 100000".format(pipe=pip))
            elif pip in (1, 2):
                self._s.rfsw_cmd("ant rf init 0 {pipe} 20000".format(pipe=pip))
            self._s.rfsw_cmd("ant cal tx clear 0 {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant cal tx start 0 fwd_freq {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant wave_mem_write 0 0 fpga_out_20MHz_14dBFS_245p76MSps_cfr7p5.bin")
            if pip == 0:
                self._s.rfsw_cmd("ant write 0 0x270060 0xf")
            if pip in (1, 2):
                self._s.rfsw_cmd("ant write 0 0x270060 0xf0")
            self._s.rfsw_cmd("ant write 0 0x270048 0x7fff0002")
            for tx_params_freq_list in tx_params_branch_list:
                bran = tx_params_freq_list[0].get("branch")
                self.switch(int(bran) % 4)
                for tx_params_freq in tx_params_freq_list:
                    self.tx_calibrate_freq_point(tx_params_freq)
            self._s.rfsw_cmd("ant cal tx stop 0 {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant cal tx show 0 {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant flash lock_flash 0")

    def rx_calibrate_gain_range(self, rx_params_gain_range: [str, str]) -> None:
        """

        :param rx_params_gain_range: {"pipe":str, "branch":str, "freq":str, "start":str, "stop":str, "step":str, "power":str}
        :return:
        """
        settings_dict = {"branch": int(rx_params_gain_range.get("branch")),
                         "freq": float(rx_params_gain_range.get("freq")),
                         "start": int(rx_params_gain_range.get("start")),
                         "stop": int(rx_params_gain_range.get("stop")),
                         "step": int(rx_params_gain_range.get("step")),
                         "power": float(rx_params_gain_range.get("power"))
                         }
        for index in range(settings_dict["start"], settings_dict["stop"] + 1, settings_dict["step"]):
            self.generate_rx_signal(settings_dict["freq"], settings_dict["power"])
            self._s.rfsw_cmd("ant cal rx gain_cal  0 {branch} {index} {power}".format(**settings_dict, index=index))

    def rx_calibrate_freq_point(self, rx_params_freq: List[Dict[str, str]]) -> None:
        """

        :param rx_params_freq:
        :return:
        """
        settings_dict = {"branch": int(rx_params_freq[0].get("branch")),
                         "channel": int(rx_params_freq[0].get("branch")) % 4,
                         "freq": float(rx_params_freq[0].get("freq")) * 1000,
                         "pipe": int(rx_params_freq[0].get("pipe"))}
        if settings_dict["pipe"] == 2:
            self._s.rfsw_cmd(
                "ant cal rx set_freq 0 {branch} {rfreq}".format(**settings_dict, refreq=3800 - settings_dict["freq"]))
        self._s.rfsw_cmd("ant cal rx set_freq 0 {branch} {freq}".format(**settings_dict))
        self._s.rfsw_cmd("ant rx enable 0 {branch} 1 0".format(**settings_dict))
        for rx_params_gain_range in rx_params_freq:
            self.rx_calibrate_gain_range(rx_params_gain_range)

    def rx_process(self, rx_params_pipe_list: List[List[List[List[Dict[str, str]]]]]) -> None:
        for rx_params_branch_list in rx_params_pipe_list:
            self.generator_on()
            pip = rx_params_branch_list[0][0][0].get("pipe")
            self._s.rfsw_cmd("ant rf reset 0")
            self._s.rfsw_cmd("ant flash unlock_factory_flash 0")
            self._s.rfsw_cmd("ant cal format_nvm 0 {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant rf reset 0")
            self._s.rfsw_cmd("ant squatch3 setTddMode 0 2")
            self._s.rfsw_cmd("madura create_from_draco 0.{pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant rf init 0 {pipe} 100000".format(pipe=pip))
            self._s.rfsw_cmd("ant cal rx clear_cache 0 {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant cal rx start 0 {pipe}".format(pipe=pip))
            for rx_params_freq_list in rx_params_branch_list:
                bran = rx_params_freq_list[0][0].get("branch")
                self.switch(int(bran) % 4)
                for rx_params_freq in rx_params_freq_list:
                    self.rx_calibrate_freq_point(rx_params_freq)
                self._s.rfsw_cmd("ant rx enable 0 {branch} 0 0".format(branch=bran))
            self.generator_off()
            self._s.rfsw_cmd("ant cal rx stop 0 {pipe}".format(pipe=pip))
            self._s.rfsw_cmd("ant flash lock_flash 0")
            self._s.rfsw_cmd("ant cal rx show 0 {pipe}".format(pipe=pip))

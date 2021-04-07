import re
from typing import Dict
from tools.function import *
from tools.ssh import SSHConnection


def get_clgc(ssh: SSHConnection, rf_params: Dict[str, str]) -> list:
    """

    :param ssh:
    :param rf_params:
    :return: [loop_gain, atten]
    """
    branch = rf_params.get('branch')
    pid_str = ssh.common_cmd("ps -ef | grep hwrel")
    pid = re.search("toor4nsn\s+(\d+).+/usr/bin/", pid_str).group(1)
    clgc_str = ssh.aashell_cmd("madura_ClgcStatusGet %d %d @%s" % (int(branch) // 4, int(branch) % 4, pid))
    loop_gain, atten = re.search("loop_gain_dB = (-?\d+\.?\d*).+tx_atten_dB = (\d+\.?\d*)", clgc_str, re.S).groups()
    return (strlist_to_floatlist([loop_gain, atten]))


def get_pa_temperature(ssh: SSHConnection, rf_params: Dict[str, str]) -> int:
    """

    :param ssh:
    :param rf_params:
    :return:
    """
    branch = rf_params.get('branch')
    pid_str = ssh.common_cmd("ps -ef | grep hwrel")
    pid = re.search("toor4nsn\s+(\d+).+/usr/bin/", pid_str).group(1)
    temp_str = ssh.aashell_cmd("tx_temperature %s @%s" % (branch, pid))
    temp = re.search("(\d+)C", temp_str).group(1)
    return int(temp)

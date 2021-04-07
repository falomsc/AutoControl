import re
from typing import Dict
from tools.function import *
from tools.ssh import SSHConnection


def get_atten(ssh: SSHConnection, rf_params: Dict[str, str]) -> float:
    """

    :param ssh:
    :param rf_params:
    :return:
    """
    branch = rf_params.get('branch')
    pid_str = ssh.common_cmd("ps -ef | grep hwrel")
    pid = re.search("toor4nsn\s+(\d+).+/usr/bin/", pid_str).group(1)
    atten_str = ssh.aashell_cmd("madura_ClgcStatusGet %d %d @%s" % (int(branch) // 4, int(branch) % 4, pid))
    atten = re.search("tx_atten_dB = (\d+\.?\d*)", atten_str).group(1)
    return float(atten)


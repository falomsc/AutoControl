from tools.ssh import SSHConnection
from tools.visa import VisaConnection
from xstep_new.get_xstep_config import *

if __name__ == '__main__':
    s = SSHConnection(hostname=hostname, port=port, username=username, password=password)
    v = VisaConnection(address=address)
    mode = 'TM3_1'
    tx_bandwidth_list = get_xstep_tx_config("./config/5G_config.xml")
    for tx_pipe_list in tx_bandwidth_list:
        for tx_branch_list in tx_pipe_list:
            for tx_freq_list in tx_branch_list:
                for tx_freq in tx_freq_list:
                    bandwidth = tx_freq.get('bandwidth')
                    pipe = tx_freq.get('pipe')
                    branch = tx_freq.get('branch')
                    loss = tx_freq.get('loss')
                    power = tx_freq.get('power')
                    freq = tx_freq.get('freq')
                    if bandwidth.find('+') > -1:
                        typ = 2
                    elif bandwidth.find('+') > -1 and bandwidth.find('gap') > -1:
                        typ = 3
                    else:
                        typ = 1


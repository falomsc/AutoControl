from tools.ssh import SSHConnection
from tools.ssh_cmd import get_clgc, get_pa_temperature
from tools.visa import VisaConnection
from tools.visa_cmd_rs import *
from xstep_new.get_xstep_config import *

def lte_test(s: SSHConnection, v: VisaConnection, rf_params: Dict[str, str]):
    res_basic = [rf_params.get('mode'), rf_params.get('bandwidth'), int(rf_params.get('pipe')),
                 int(rf_params.get('branch')), float(rf_params.get('freq')), float(rf_params.get('power'))]
    res_madura = get_clgc(s, rf_params).append(get_pa_temperature(s, rf_params))


def lte_multi_test(s: SSHConnection, v: VisaConnection, rf_params: Dict[str, str]):
    pass

def lte_multi_gap_test(s: SSHConnection, v: VisaConnection, rf_params: Dict[str, str]):
    pass

def nr5g_test(s: SSHConnection, v: VisaConnection, rf_params: Dict[str, str]):
    pass

def nr5g_multi_test(s: SSHConnection, v: VisaConnection, rf_params: Dict[str, str]):
    pass

def nr5g_multi_gap_test(s: SSHConnection, v: VisaConnection, rf_params: Dict[str, str]):
    pass





if __name__ == '__main__':
    s = SSHConnection(hostname=hostname, port=port, username=username, password=password)
    v = VisaConnection(address=address)
    mode = 'TM3_1'
    abw_dict = {"5": 20, "20": 80, "50": 120, "60": 120, "100": 240, "200": 320}
    tx_bandwidth_list = get_xstep_tx_config("./config/5G_config.xml")
    for tx_pipe_list in tx_bandwidth_list:
        for tx_branch_list in tx_pipe_list:
            for tx_freq_list in tx_branch_list:
                for tx_freq in tx_freq_list:
                    pipe = tx_freq.get('pipe')
                    bandwidth = tx_freq.get('bandwidth')
                    rf_params = {"mode": mode}
                    rf_params.update(tx_freq)
                    res_basic = [rf_params.get('mode'), rf_params.get('bandwidth'), int(rf_params.get('pipe')),
                                 int(rf_params.get('branch')), float(rf_params.get('freq')),
                                 float(rf_params.get('power'))]
                    res_madura = get_clgc(s, rf_params).append(get_pa_temperature(s, rf_params))
                    if bandwidth.find('+') > -1 and bandwidth.find('gap') > -1:
                        if pipe == "0":
                            pass
                        elif pipe in ("1", "2"):
                            pass
                    elif bandwidth.find('+') > -1:
                        if pipe == "0":
                            pass
                        elif pipe in ("1", "2"):
                            pass
                    else:
                        span = int(int(bandwidth) * 1.5)
                        abw = abw_dict.get(bandwidth)
                        if pipe == "0":
                            # ACP
                            v.send_cmd("*RST")
                            v.send_cmd("INST:CRE:NEW NR5G, 'ACP'")
                            res_acp = nr5g_acp(v, rf_params, current="ACP")
                            # OBW
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW'")
                            res_obw = obw(v, rf_params, span=span, current="OBW")
                            # CCDF
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'CCDF'")
                            res_ccdf = ccdf(v, rf_params, abw, current="CCDF")
                            # SEM
                            v.send_cmd("INST:CRE:NEW NR5G, 'SEM'")
                            res_sem = nr5g_sem(v, rf_params, current="SEM")
                            # SE
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'SE'")
                            res_se = se(v, rf_params, current="SE")
                        elif pipe in ("1", "2"):
                            # ACP
                            v.send_cmd("*RST")
                            v.send_cmd("INST:CRE:NEW LTE, 'ACP'")
                            res_acp = lte_acp(v, rf_params, current="ACP")
                            # OBW
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW'")
                            res_obw = obw(v, rf_params, span=span, current="OBW")
                            # CCDF
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'CCDF'")
                            res_ccdf = ccdf(v, rf_params, abw, current="CCDF")
                            # EVM
                            v.send_cmd("INST:CRE:NEW LTE, 'EVM'")
                            res_evm = lte_evm(v, rf_params, current="SEM")
                            # SEM
                            v.send_cmd("INST:CRE:NEW LTE, 'SEM'")
                            res_sem = lte_sem(v, rf_params, current="SEM")
                            # SE
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'SE'")
                            res_se = se(v, rf_params, current="SE")


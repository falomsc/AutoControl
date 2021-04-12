from tools.ssh import SSHConnection
from tools.ssh_cmd import get_clgc_and_pa_temperature
from tools.visa_cmd_rs import *
from xstep_new.fill_report import FillReport
from xstep_new.get_xstep_config import *


if __name__ == '__main__':
    s = SSHConnection(hostname=hostname, port=port, username=username, password=password)
    v = VisaConnection(address=address)
    fr = FillReport("./report/model.xlsx")
    mode = 'TM3_1'
    abw_dict = {"5": 20, "20": 80, "40": 120, "50": 120, "60": 120, "70": 160, "100": 240, "200": 320}
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
                    res_madura = get_clgc_and_pa_temperature(s, rf_params)
                    ############## notion ##############
                    input("Please conform the information: branch: {branch}, freq: {freq}, mode: {mode}, bw: {bandwidth}".format(**rf_params))

                    ############## 2 Carriers ##############
                    if bandwidth.find('+') > -1:
                        bw1 = re.match("(.\d+)", bandwidth).group(1)
                        if bandwidth.find("gap") > -1:
                            gap = re.search("gap(.\d+)", bandwidth).group(1)
                            bw2 = re.search("\+(.\d+)", bandwidth).group(1)
                        else:
                            gap = "0"
                            bw2 = re.search("\+(.\d+)", bandwidth).group(1)
                        abw = abw_dict.get(str(int(bw1)+int(gap)+int(bw2)))

                        ############## 2 Carriers NR5G ##############
                        if pipe == "0":
                            # ACP
                            v.send_cmd("*RST")
                            v.send_cmd("INST:CRE:NEW NR5G, 'ACP'")
                            res_acp = nr5g_multi_acp(v, rf_params, current="ACP", exs=True,
                                                     snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_1.JPG".format(**rf_params))
                            # OBW
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW1'")
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW2'")
                            res_obw = multi_obw(v, rf_params, current1="OBW1", current2="OBW2", exs=True,
                                                snappath1="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_2_1.JPG".format(**rf_params),
                                                snappath2="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_2_2.JPG".format(**rf_params))
                            # CCDF
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'CCDF'")
                            res_ccdf = ccdf(v, rf_params, abw, current="CCDF", samp_num=1000000, exs=True,
                                            snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_3.JPG".format(**rf_params))
                            # EVM
                            v.send_cmd("INST:CRE:NEW NR5G, 'EVM'")
                            res_evm = nr5g_multi_evm(v, rf_params, current="EVM", exs=True,
                                                     snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_4.JPG".format(**rf_params))
                            # SEM
                            v.send_cmd("INST:CRE:NEW NR5G, 'SEM'")
                            res_sem = nr5g_multi_sem(v, rf_params, current="SEM", exs=True,
                                                     snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_5.JPG".format(**rf_params))
                            # SE
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'SE'")
                            res_se = se(v, rf_params, current="SE",
                                        snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_6.JPG".format(**rf_params))

                            fr.next_line()
                            fr.fill_xl_value(FillReport.BASIC, res_basic, mode_extra=mode)
                            fr.fill_xl_value(FillReport.MADURA, res_madura, mode_extra=mode)
                            fr.fill_xl_value(FillReport.NR5G_MULTI_ACP, res_acp, mode_extra=mode)
                            fr.fill_xl_value(FillReport.MULTI_OBW, res_obw, mode_extra=mode)
                            fr.fill_xl_value(FillReport.CCDF, res_ccdf, mode_extra=mode)
                            fr.fill_xl_value(FillReport.NR5G_MULTI_EVM, res_evm, mode_extra=mode)
                            fr.fill_xl_value(FillReport.NR5G_MULTI_SEM, res_sem, mode_extra=mode)
                            fr.fill_xl_value(FillReport.SE, res_se, mode_extra=mode)

                        ############## 2 Carriers LTE ##############
                        elif pipe in ("1", "2"):
                            # ACP
                            v.send_cmd("*RST")
                            v.send_cmd("NST:CRE:NEW LTE, 'ACP'")
                            res_acp = lte_multi_acp(v, rf_params, current="ACP",
                                                    snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_1.JPG".format(**rf_params))
                            # OBW
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW1'")
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW2'")
                            res_obw = multi_obw(v, rf_params, current1="OBW1", current2="OBW2",
                                                snappath1="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_2_1.JPG".format(**rf_params),
                                                snappath2="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_2_2.JPG".format(**rf_params))
                            # CCDF
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'CCDF'")
                            res_ccdf = ccdf(v, rf_params, abw, current="CCDF",
                                            snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_3.JPG".format(**rf_params))
                            # EVM
                            v.send_cmd("NST:CRE:NEW LTE, 'EVM'")
                            res_evm = lte_multi_evm(v, rf_params, current="EVM",
                                                    snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_4.JPG".format(**rf_params))
                            # SEM
                            v.send_cmd("NST:CRE:NEW LTE, 'SEM'")
                            res_sem = lte_multi_sem(v, rf_params, current="SEM",
                                                    snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_5.JPG".format(**rf_params))
                            # SE
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'SE'")
                            res_se = se(v, rf_params, current="SE",
                                        snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_6.JPG".format(**rf_params))

                            fr.next_line()
                            fr.fill_xl_value(FillReport.BASIC, res_basic, mode_extra=mode)
                            fr.fill_xl_value(FillReport.MADURA, res_madura, mode_extra=mode)
                            fr.fill_xl_value(FillReport.LTE_MULTI_ACP, res_acp, mode_extra=mode)
                            fr.fill_xl_value(FillReport.MULTI_OBW, res_obw, mode_extra=mode)
                            fr.fill_xl_value(FillReport.CCDF, res_ccdf, mode_extra=mode)
                            fr.fill_xl_value(FillReport.LTE_MULTI_EVM, res_evm, mode_extra=mode)
                            fr.fill_xl_value(FillReport.LTE_MULTI_SEM, res_sem, mode_extra=mode)
                            fr.fill_xl_value(FillReport.SE, res_se, mode_extra=mode)

                    ############## 1 Carrier ##############
                    else:
                        abw = abw_dict.get(bandwidth)

                        ############## 1 Carrier NR5G ##############
                        if pipe == "0":
                            # ACP
                            v.send_cmd("*RST")
                            v.send_cmd("INST:CRE:NEW NR5G, 'ACP'")
                            res_acp = nr5g_acp(v, rf_params, current="ACP", exs=True,
                                               snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_1.JPG".format(**rf_params))
                            # OBW
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW'")
                            res_obw = obw(v, rf_params, current="OBW", exs=True,
                                          snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_2.JPG".format(**rf_params))
                            # CCDF
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'CCDF'")
                            res_ccdf = ccdf(v, rf_params, abw, current="CCDF", samp_num=1000000, exs=True,
                                            snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_3.JPG".format(**rf_params))
                            # EVM
                            v.send_cmd("INST:CRE:NEW NR5G, 'EVM'")
                            res_evm = nr5g_evm(v, rf_params, current="EVM", exs=True,
                                               snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_4.JPG".format(**rf_params))
                            # SEM
                            v.send_cmd("INST:CRE:NEW NR5G, 'SEM'")
                            res_sem = nr5g_sem(v, rf_params, current="SEM", exs=True,
                                               snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_5.JPG".format(**rf_params))
                            # SE
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'SE'")
                            res_se = se(v, rf_params, current="SE",
                                        snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_6.JPG".format(**rf_params))

                            fr.next_line()
                            fr.fill_xl_value(FillReport.BASIC, res_basic, mode_extra=mode)
                            fr.fill_xl_value(FillReport.MADURA, res_madura, mode_extra=mode)
                            fr.fill_xl_value(FillReport.NR5G_ACP, res_acp, mode_extra=mode)
                            fr.fill_xl_value(FillReport.OBW, res_obw, mode_extra=mode)
                            fr.fill_xl_value(FillReport.CCDF, res_ccdf, mode_extra=mode)
                            fr.fill_xl_value(FillReport.NR5G_EVM, res_evm, mode_extra=mode)
                            fr.fill_xl_value(FillReport.NR5G_SEM, res_sem, mode_extra=mode)
                            fr.fill_xl_value(FillReport.SE, res_se, mode_extra=mode)

                        ############## 1 Carrier LTE ##############
                        elif pipe in ("1", "2"):
                            # ACP
                            v.send_cmd("*RST")
                            v.send_cmd("INST:CRE:NEW LTE, 'ACP'")
                            res_acp = lte_acp(v, rf_params, current="ACP",
                                              snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_1.JPG".format(**rf_params))
                            # OBW
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'OBW'")
                            res_obw = obw(v, rf_params, current="OBW",
                                          snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_2.JPG".format(**rf_params))
                            # CCDF
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'CCDF'")
                            res_ccdf = ccdf(v, rf_params, abw, current="CCDF",
                                            snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_3.JPG".format(**rf_params))
                            # EVM
                            v.send_cmd("INST:CRE:NEW LTE, 'EVM'")
                            res_evm = lte_evm(v, rf_params, current="EVM",
                                              snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_4.JPG".format(**rf_params))
                            # SEM
                            v.send_cmd("INST:CRE:NEW LTE, 'SEM'")
                            res_sem = lte_sem(v, rf_params, current="SEM",
                                              snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_5.JPG".format(**rf_params))
                            # SE
                            v.send_cmd("INST:CRE:NEW SANALYZER, 'SE'")
                            res_se = se(v, rf_params, current="SE",
                                        snappath="C:\\Xstep\\{bandwidth}\\pipe{pipe}\\{branch}_{mode}_{freq}_{power}_6.JPG".format(**rf_params))

                            fr.next_line()
                            fr.fill_xl_value(FillReport.BASIC, res_basic, mode_extra=mode)
                            fr.fill_xl_value(FillReport.MADURA, res_madura, mode_extra=mode)
                            fr.fill_xl_value(FillReport.LTE_ACP, res_acp, mode_extra=mode)
                            fr.fill_xl_value(FillReport.OBW, res_obw, mode_extra=mode)
                            fr.fill_xl_value(FillReport.CCDF, res_ccdf, mode_extra=mode)
                            fr.fill_xl_value(FillReport.LTE_EVM, res_evm, mode_extra=mode)
                            fr.fill_xl_value(FillReport.LTE_SEM, res_sem, mode_extra=mode)
                            fr.fill_xl_value(FillReport.SE, res_se, mode_extra=mode)

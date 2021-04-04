from tools.visa import VisaConnection
from tools.visa_cmd_rs import *

v = VisaConnection("TCPIP0::192.168.0.130::inst0::INSTR", timeout=100000)
# rf_params = {"pipe": "1", "freq": "2640", "loss": "28.6", "bandwidth": "20+20", "mode": "TM3_1A"}
# v.send_cmd("*RST")
# v.send_cmd("INST:CRE:NEW LTE, 'LTE'")
# res = lte_multi_sem(v, rf_params)
# print(res)
# for i in res:
#     print(i)

# v.send_cmd("*RST")
# v.send_cmd("INST:CRE:NEW SANALYZER, 'Spectrum'")
# res = v.rec_cmd("CALC:MARK:FUNC:POW:RES? ACP").split(",")
# for i in res:
#     print(float(i))

rf_params = {"pipe": "0", "freq": "3550", "loss": "28.9", "bandwidth": "100+100", "mode": "TM3_1A"}
v.send_cmd("*RST")
v.send_cmd("INST:CRE:NEW NR5G, '5G NR'")
res = nr5g_multi_sem(v, rf_params, exs=True)
print(res)

from tools.visa import VisaConnection
from tools.visa_cmd_rs import *

v = VisaConnection("TCPIP0::192.168.0.130::inst0::INSTR", timeout=100000)
# rf_params = {"pipe": "1", "freq": "2655", "loss": "28.6", "bandwidth": "20+gap30+20", "mode": "TM3_1"}
# v.send_cmd("*RST")
# v.send_cmd("INST:CRE:NEW LTE, 'LTE'")
# res = lte_multi_sem(v, rf_params)
# for i in res:
#     print(res)

# v.send_cmd("*RST")
# v.send_cmd("INST:CRE:NEW SANALYZER, 'Spectrum'")
# res = v.rec_cmd("CALC:MARK:FUNC:POW:RES? ACP").split(",")
# for i in res:
#     print(float(i))

rf_params = {"pipe": "0", "freq": "3550", "loss": "28.9", "bandwidth": "50+gap90+60", "mode": "TM3_1"}
v.send_cmd("*RST")
v.send_cmd("INST:CRE:NEW NR5G, '5G NR'")
res = nr5g_multi_sem(v, rf_params, exs=True)
for i in res:
    print(i)


# res1 = v.rec_cmd("CALC:MARK:FUNC:POW1:RES? CPOW")
# res2 = v.rec_cmd("CALC:MARK:FUNC:POW2:RES? CPOW")
# res3 = v.rec_cmd("TRAC:DATA? LIST").split(",")
# num = 8
# for i in range(num):
#     res3[1 + 11 * i: 5 + 11 * i] = hzlist_to_mhzlist(res3[1 + 11 * i: 5 + 11 * i])
# res3.insert(0, res2)
# res3.insert(0, res1)
# res = strlist_to_floatlist(res3)
# while 0.0 in res:
#     res.remove(0.0)
# for i in res:
#     print(i)
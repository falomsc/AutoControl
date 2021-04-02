from tools.visa import VisaConnection
from tools.visa_cmd_rs import lte_multi_aclr

v = VisaConnection("TCPIP0::192.168.0.130::inst0::INSTR", timeout=10000)
rf_params = {"freq": "2640", "loss": "28.6", "bandwidth": "20+20", "mode": "TM3_1A"}
v.send_cmd("*RST")
v.send_cmd("INST:CRE:NEW LTE, 'LTE'")
res = lte_multi_aclr(v, rf_params)
print(res)
import time
from typing import Dict

from tools.function import str_to_float
from tools.visa import VisaConnection


def channel_power(v: VisaConnection, rf_params: Dict[str, str]) -> float:
    freq = rf_params.get('freq')
    bandwidth = rf_params.get('bandwidth')
    loss = rf_params.get('loss')
    v.send_cmd("*RST")
    v.send_cmd("SYST:PRES")
    v.send_cmd("CONF:CHP")
    v.send_cmd("CORR:SA:GAIN %s" % loss)
    v.send_cmd("FREQ:CENT %s MHz" % freq)
    v.send_cmd("CHP:BAND:INT %s MHz" % bandwidth)
    v.send_cmd("POW:RANG:OPT IMM")
    time.sleep(3)
    res = v.rec_cmd("FETCh:CHP:CHP?")
    return str_to_float(res)

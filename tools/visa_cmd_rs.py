import re
import time
from typing import List, Dict

from tools.function import *
from tools.visa import VisaConnection


def obw(v: VisaConnection, rf_params: Dict[str, str], span: int,
        rel: float = 25, atten: int = 20, rbw: int = 30, count: int = 10001, point: int = 10001,
        current: str = None, rename: str = None,
        exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> float:
    """
    Create a channel first
    INST:CRE:NEW SANALYZER, 'Spectrum'
    :param v: VisaConnection
    :param rf_params: should add temp and mode
    rf_params =
    :param span: Span (MHz)
    :param rel: Ref Level (dBm)
    :param atten: RF Atten Manual (dB)
    :param rbw: Res Bw Manual (KHz)
    :param count: Sweep/Average Count
    :param point: Sweep Points
    :param current: Current Name
    :param rename: Rename
    :param exs: Is External Trigger
    :param snap: Enable SnapShot
    :param snappath: Path of SnapShot
    :param delay: Time Delay
    :return:
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CALC:MARK:FUNC:POW:SEL OBW")

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
        v.send_cmd("SENS:SWE:OPT SPE")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("DISP:TRAC1:MODE AVER")
    v.send_cmd("DET RMS")
    v.send_cmd("POW:ACH:BAND %sMHz" % bandwidth)
    v.send_cmd("FREQ:SPAN %fMHz" % span)
    v.send_cmd("BAND %d kHz" % rbw)
    v.send_cmd("SWE:COUN %d" % count)
    v.send_cmd("SWE:POIN %d" % point)

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res = v.rec_cmd("CALC:MARK:FUNC:POW:RES? OBW")
    return hz_to_mhz(res)


def ccdf(v: VisaConnection, rf_params: Dict[str, str], abw: float,
         rel: float = 25, atten: int = 20,
         current: str = None, rename: str = None,
         exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """
    INST:CRE:NEW SANALYZER, 'Spectrum'
    :param v:
    :param rf_params:
    :param abw: Analysis BW (MHz)
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [Mean, Peak, Crest, 10%, 1%, 0.1%, 0.01%]
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CALC:STAT:CCDF ON")

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("BAND %f MHz" % abw)

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res = v.rec_cmd("CALC:STAT:RES1? ALL").split(";")
    res.append(v.rec_cmd("CALC:STAT:CCDF:X1? P10"))
    res.append(v.rec_cmd("CALC:STAT:CCDF:X1? P1"))
    res.append(v.rec_cmd("CALC:STAT:CCDF:X1? P0_1"))
    res.append(v.rec_cmd("CALC:STAT:CCDF:X1? P0_01"))
    return strlist_to_floatlist(res)


def se(v: VisaConnection, rf_params: Dict[str, str],
       rel: float = 25, atten: int = 10,
       current: str = None, rename: str = None,
       exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """
    return [Range No, Range Low(MHz), Range Up(MHz), RBW(MHz), Frequency(MHz), Power Abs(dBm), Delta Limit(dB)]
    """
    pipe = rf_params.get('pipe')
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')

    if pipe == 0:
        start = "3440"
        stop = "3710"
    elif pipe == 1:
        start = "2610"
        stop = "2700"
    elif pipe == 2:
        start = "2100"
        stop = "2210"
    range_list = [
        ["9KHz", "150KHz", "1KHz", "-36", "-36", "701"],
        ["150KHz", "30MHz", "10KHz", "-36", "-36", "4001"],
        ["30MHz", "1GHz", "100KHz", "-36", "-36", "32001"],
        ["1GHz", "%sMHz" % start, "1MHz", "-30", "-30", "16001"],
        ["%sMHz" % stop, "12.75GHz", "1MHz", "-30", "-30", "16001"]
    ]

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("SWE:MODE LIST")

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
        v.send_cmd("SENS:SWE:EGAT:CONT:STAT ON")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INIT:CONT OFF")
    for i, r in enumerate(range_list):
        v.send_cmd("LIST:RANG%d:FREQ:STAR %s" % (i + 1, r[0]))
        v.send_cmd("LIST:RANG%d:FREQ:STOP %s" % (i + 1, r[1]))
        v.send_cmd("LIST:RANG%d:BAND:RES %s" % (i + 1, r[2]))
        v.send_cmd("LIST:RANG%d:LIM:STAR %s" % (i + 1, r[3]))
        v.send_cmd("LIST:RANG%d:LIM:STOP %s" % (i + 1, r[4]))
        v.send_cmd("LIST:RANG%d:POIN %s" % (i + 1, r[5]))
        v.send_cmd("LIST:RANG%d:INP:ATT:AUTO OFF" % (i + 1))
        v.send_cmd("LIST:RANG%d:INP:ATT %d" % ((i + 1), atten))
    v.send_cmd("SENS:LIST:XADJ;*WAI")
    v.send_cmd("INIT:SPUR; *WAI")

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res1 = v.rec_cmd("TRAC:DATA? LIST").split(",")
    res2 = []
    for i in range(5):
        res2.append(i + 1)
        res2.append(hz_to_mhz(res1[i * 11 * 25 + 1]))
        res2.append(hz_to_mhz(res1[i * 11 * 25 + 2]))
        res2.append(hz_to_mhz(res1[i * 11 * 25 + 3]))
        res2.append(hz_to_mhz(res1[i * 11 * 25 + 4]))
        res2.append(str_to_float(res1[i * 11 * 25 + 5]))
        res2.append(str_to_float(res1[i * 11 * 25 + 7]))
    return res2


def lte_aclr(v: VisaConnection, rf_params: Dict[str, str],
             rel: float = 25, atten: int = 5,
             current: str = None, rename: str = None,
             exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """
    INST:CRE:NEW LTE, 'LTE'
    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [power, offset(-bw), offset(+bw), offset(-2*bw), offset(+2*bw)]
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    t_mode = "E-" + mode + "__" + bandwidth + "MHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:LTE:MEAS ACLR")
    v.send_cmd("MMEM:LOAD:CC:TMOD:DL '%s'" % t_mode)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res = v.rec_cmd("CALC:MARK:FUNC:POW:RES? ACP").split(",")
    return strlist_to_floatlist(res)


def lte_multi_aclr(v: VisaConnection, rf_params: Dict[str, str],
                   rel: float = 25, atten: int = 5,
                   current: str = None, rename: str = None,
                   exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:

    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    bw1 = re.match("(.\d+)", bandwidth).group(1)
    if bandwidth.find("gap") > -1:
        gap = re.search("gap(.\d+)", bandwidth).group(1)
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    else:
        gap = "0"
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    t_mode = "E-" + mode + "__" + bw1 + "MHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:LTE:MEAS MCAClr")
    v.send_cmd("MMEM:LOAD:CC:TMOD:DL '%s'" % t_mode)
    v.send_cmd("CONF:LTE:NOCC 2")
    v.send_cmd("CONF:LTE:DL:CC:BW BW%s_00" % bw1)
    v.send_cmd("CONF:LTE:DL:CC2:BW BW%s_00" % bw2)
    offset1 = int((float(freq) - float(bw2) / 2 - float(gap) / 2) * 1e6)
    offset2 = int((float(freq) + float(bw1) / 2 + float(gap) / 2) * 1e6)
    v.send_cmd("SENS:FREQ:CENT:CC %d" % offset1)
    v.send_cmd("SENS:FREQ:CENT:CC2 %d" % offset2)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res = v.rec_cmd("CALC:MARK:FUNC:POW:RES? MCAC").split(",")
    # s2 = v.rec_cmd("CALC:MARK:FUNC:POW:RES? GACL")
    # s3 = v.rec_cmd("CALC:MARK:FUNC:POW:RES? MACM")
    return strlist_to_floatlist(res)


def lte_evm(v: VisaConnection, rf_params: Dict[str, str],
            rel: float = 25, atten: int = 20,
            current: str = None, rename: str = None,
            exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[List[float]]:
    """
    INST:CRE:NEW LTE, 'LTE'
    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [EVM PDSCH QPSK(%), EVM PDSCH 16QAM(%), EVM PDSCH 64QAM(%), EVM PDSCH 256QAM(%),
                0                   1                   2                   3
            EVM ALL(%), EVM Phys Channel(%), EVM Phys Signal(%),
                4           5                   6
            Frequency Error(Hz), Sampling Error(ppm),
                7                   8
            I/Q Offset(dB), I/Q Gain Imbalance(dB), I/Q Quadrature Error(°),
                9               10                      11
            RSTP(dBm), OSTP(dBm), RSSI(dBm),
                12      13          14
            Power(dBm), Crest Factor(dB)]
                15      16
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    t_mode = "E-" + mode + "__" + bandwidth + "MHz"
    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:LTE:MEAS EVM")
    v.send_cmd("MMEM:LOAD:CC:TMOD:DL '%s'" % t_mode)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("LAY:REM:WIND '3'")
    v.send_cmd("LAY:ADD:WIND? '5',LEFT,EVSY")

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    evm_qpsk = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSQP:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSQP:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSQP:MAX?"))]
    evm_16qam = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSST:AVER?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSST:MIN?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSST:MAX?"))]
    evm_64qam = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSSF:AVER?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSSF:MIN?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSSF:MAX?"))]
    evm_256qam = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSTS:AVER?")),
                  str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSTS:MIN?")),
                  str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSTS:MAX?"))]
    evm_all = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:AVER?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:MIN?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:MAX?"))]
    evm_pch = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PCH:AVER?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PCH:MIN?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PCH:MAX?"))]
    evm_psig = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PSIG:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PSIG:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PSIG:MAX?"))]
    evm_ferr = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:FERR:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:FERR:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:FERR:MAX?"))]
    evm_serr = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:SERR:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:SERR:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:SERR:MAX?"))]
    evm_iqof = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:IQOF:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:IQOF:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:IQOF:MAX?"))]
    evm_gimb = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:GIMB:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:GIMB:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:GIMB:MAX?"))]
    evm_quad = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:QUAD:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:QUAD:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:QUAD:MAX?"))]
    evm_rstp = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:RSTP:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:RSTP:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:RSTP:MAX?"))]
    evm_ostp = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:OSTP:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:OSTP:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:OSTP:MAX?"))]
    evm_rssi = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:RSSI:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:RSSI:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:RSSI:MAX?"))]
    evm_pow = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:POW:AVER?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:POW:MIN?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:POW:MAX?"))]
    evm_cres = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:CRES:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:CRES:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:CRES:MAX?"))]
    res = [evm_qpsk, evm_16qam, evm_64qam, evm_256qam, evm_all, evm_pch, evm_psig, evm_ferr, evm_serr, evm_iqof,
           evm_gimb, evm_quad, evm_rstp, evm_ostp, evm_rssi, evm_pow, evm_cres]
    return res


def lte_multi_evm(v: VisaConnection, rf_params: Dict[str, str],
                  rel: float = 25, atten: int = 20,
                  current: str = None, rename: str = None,
                  exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[List[float]]:

    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    bw1 = re.match("(.\d+)", bandwidth).group(1)
    if bandwidth.find("gap") > -1:
        gap = re.search("gap(.\d+)", bandwidth).group(1)
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    else:
        gap = "0"
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    t_mode = "E-" + mode + "__" + bw1 + "MHz"
    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:LTE:MEAS EVM")
    v.send_cmd("MMEM:LOAD:CC:TMOD:DL '%s'" % t_mode)
    v.send_cmd("CONF:LTE:NOCC 2")
    v.send_cmd("CONF:LTE:DL:CC:BW BW%s_00" % bw1)
    v.send_cmd("CONF:LTE:DL:CC2:BW BW%s_00" % bw2)
    offset1 = int((float(freq) - float(bw2) / 2 - float(gap) / 2) * 1e6)
    offset2 = int((float(freq) + float(bw1) / 2 + float(gap) / 2) * 1e6)
    v.send_cmd("SENS:FREQ:CENT:CC %d" % offset1)
    v.send_cmd("SENS:FREQ:CENT:CC2 %d" % offset2)


    if exs:
        v.send_cmd("TRIG:SOUR EXT")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("LAY:REM:WIND '3'")
    v.send_cmd("LAY:ADD:WIND? '5',LEFT,EVSY")

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res_list = []
    for i in range(2):
        evm_qpsk = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSQP:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSQP:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSQP:MAX?" % (i+1)))]
        evm_16qam = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSST:AVER?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSST:MIN?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSST:MAX?" % (i+1)))]
        evm_64qam = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSSF:AVER?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSSF:MIN?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSSF:MAX?" % (i+1)))]
        evm_256qam = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSTS:AVER?" % (i+1))),
                      str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSTS:MIN?" % (i+1))),
                      str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSTS:MAX?" % (i+1)))]
        evm_all = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:AVER?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:MIN?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:MAX?" % (i+1)))]
        evm_pch = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PCH:AVER?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PCH:MIN?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PCH:MAX?" % (i+1)))]
        evm_psig = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PSIG:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PSIG:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PSIG:MAX?" % (i+1)))]
        evm_ferr = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:FERR:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:FERR:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:FERR:MAX?" % (i+1)))]
        evm_serr = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:SERR:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:SERR:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:SERR:MAX?" % (i+1)))]
        evm_iqof = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:IQOF:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:IQOF:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:IQOF:MAX?" % (i+1)))]
        evm_gimb = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:GIMB:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:GIMB:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:GIMB:MAX?" % (i+1)))]
        evm_quad = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:QUAD:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:QUAD:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:QUAD:MAX?" % (i+1)))]
        evm_rstp = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:RSTP:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:RSTP:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:RSTP:MAX?" % (i+1)))]
        evm_ostp = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:OSTP:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:OSTP:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:OSTP:MAX?" % (i+1)))]
        evm_rssi = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:RSSI:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:RSSI:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:RSSI:MAX?" % (i+1)))]
        evm_pow = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:POW:AVER?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:POW:MIN?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:POW:MAX?" % (i+1)))]
        evm_cres = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:CRES:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:CRES:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:CRES:MAX?" % (i+1)))]
        res = [evm_qpsk, evm_16qam, evm_64qam, evm_256qam, evm_all, evm_pch, evm_psig, evm_ferr, evm_serr, evm_iqof, 
               evm_gimb, evm_quad, evm_rstp, evm_ostp, evm_rssi, evm_pow, evm_cres]
        res_list.append(res)
    return res_list


def lte_sem(v: VisaConnection, rf_params: Dict[str, str],
            rel: float = 25, atten: int = 12,
            current: str = None, rename: str = None,
            exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """

    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [TxPower(dBm), Range No, Start Freq Rel(MHz), Stop Freq Rel(MHz), RBW(MHz),
    Frequency at Delta to Limit(MHz), Power Abs(dBm), Power Rel(dB), Delta to Limit(dB), ...]
    4 Ranges Totally
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    t_mode = "E-" + mode + "__" + bandwidth + "MHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:LTE:MEAS ESP")
    v.send_cmd("MMEM:LOAD:CC:TMOD:DL '%s'" % t_mode)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")

    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    # v.send_cmd("INIT:CONT OFF")

    v.send_cmd("SENS:ESP1:PRES:STAN 'C:\R_S\Instr\sem_std\EUTRA-LTE\SEM_DL_BW%s_00_LocalArea_FSW.xml'" % bandwidth)
    v.send_cmd("SENS:ESP1:RANG2:DEL")
    v.send_cmd("SENS:ESP1:RANG7:DEL")
    v.send_cmd("SENS:ESP1:RANG1:FREQ:STOP -15050000")
    v.send_cmd("SENS:ESP1:RANG7:FREQ:STAR 15050000")
    v.send_cmd("SENS:ESP1:RANG7:FREQ:STAR 15050000")

    for i in range(7):
        v.send_cmd("SENS:ESP1:RANG%d:INP:ATT %d" % ((i + 1), atten))
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STAR -37")
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STOP -30")
    v.send_cmd("SENS:ESP1:RANG6:LIM1:ABS:STAR -30")
    v.send_cmd("SENS:ESP1:RANG6:LIM1:ABS:STOP -37")

    # v.send_cmd("INIT:CONT OFF")
    v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res1 = v.rec_cmd("CALC:MARK:FUNC:POW:RES? CPOW")
    res2 = v.rec_cmd("TRAC:DATA? LIST").split(",")
    for i in range(4):
        res2[1 + 11 * i: 5 + 11 * i] = hzlist_to_mhzlist(res2[1 + 11 * i: 5 + 11 * i])
    res2.insert(0, res1)
    res = strlist_to_floatlist(res2)
    while 0.0 in res:
        res.remove(0.0)
    return res


def lte_multi_sem(v: VisaConnection, rf_params: Dict[str, str],
                  rel: float = 25, atten: int = 12,
                  current: str = None, rename: str = None,
                  exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """

    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [TxPower(dBm), Range No, Start Freq Rel(MHz), Stop Freq Rel(MHz), RBW(MHz),
    Frequency at Delta to Limit(MHz), Power Abs(dBm), Power Rel(dB), Delta to Limit(dB), ...]
    4 Ranges Totally
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    bw1 = re.match("(.\d+)", bandwidth).group(1)
    if bandwidth.find("gap") > -1:
        gap = re.search("gap(.\d+)", bandwidth).group(1)
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    else:
        gap = "0"
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    t_mode = "E-" + mode + "__" + bw1 + "MHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:LTE:MEAS MCESpectrum")
    v.send_cmd("MMEM:LOAD:CC:TMOD:DL '%s'" % t_mode)
    v.send_cmd("CONF:LTE:NOCC 2")
    v.send_cmd("CONF:LTE:DL:CC:BW BW%s_00" % bw1)
    v.send_cmd("CONF:LTE:DL:CC2:BW BW%s_00" % bw2)
    offset1 = int((float(freq) - float(bw2) / 2 - float(gap) / 2) * 1e6)
    offset2 = int((float(freq) + float(bw1) / 2 + float(gap) / 2) * 1e6)
    v.send_cmd("SENS:FREQ:CENT:CC %d" % offset1)
    v.send_cmd("SENS:FREQ:CENT:CC2 %d" % offset2)


    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")

    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    # v.send_cmd("INIT:CONT OFF")

    v.send_cmd("SENS:ESP1:PRES:STAN 'C:\R_S\Instr\sem_std\EUTRA-LTE\SEM_DL_BW20_00_LocalArea_FSW.xml'")
    v.send_cmd("SENS:ESP1:RANG2:DEL")
    v.send_cmd("SENS:ESP1:RANG7:DEL")
    v.send_cmd("SENS:ESP1:RANG1:FREQ:STOP -15050000")
    v.send_cmd("SENS:ESP1:RANG7:FREQ:STAR 15050000")
    v.send_cmd("SENS:ESP1:RANG7:FREQ:STAR 15050000")

    for i in range(7):
        v.send_cmd("SENS:ESP1:RANG%d:INP:ATT %d" % ((i + 1), atten))
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STAR -37")
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STOP -30")
    v.send_cmd("SENS:ESP1:RANG6:LIM1:ABS:STAR -30")
    v.send_cmd("SENS:ESP1:RANG6:LIM1:ABS:STOP -37")

    # v.send_cmd("INIT:CONT OFF")
    v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res1 = v.rec_cmd("CALC:MARK:FUNC:POW:RES? CPOW")
    res2 = v.rec_cmd("TRAC:DATA? LIST").split(",")
    for i in range(4):
        res2[1 + 11 * i: 5 + 11 * i] = hzlist_to_mhzlist(res2[1 + 11 * i: 5 + 11 * i])
    res2.insert(0, res1)
    res = strlist_to_floatlist(res2)
    while 0.0 in res:
        res.remove(0.0)
    return res


def nr5g_aclr(v: VisaConnection, rf_params: Dict[str, str],
              rel: float = 25, atten: int = 5,
              current: str = None, rename: str = None,
              exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """
    INST:CRE:NEW NR5G, '5G NR'
    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return:
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    t_mode = "NR-FR1-" + mode + "__TDD_" + bandwidth + "_30kHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:NR5G:MEAS ACLR")
    v.send_cmd("MMEM:LOAD:TMOD:CC1 '%s'" % t_mode)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("SENS:SWE:OPT SPE")
    v.send_cmd("SENS:SWE:TIME 0.005")

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res = v.rec_cmd("CALC:MARK:FUNC:POW:RES? ACP").split(",")
    return strlist_to_floatlist(res)


def nr5g_multi_aclr(v: VisaConnection, rf_params: Dict[str, str],
                    rel: float = 25, atten: int = 5,
                    current: str = None, rename: str = None,
                    exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:

    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    bw1 = re.match("(.\d+)", bandwidth).group(1)
    if bandwidth.find("gap") > -1:
        gap = re.search("gap(.\d+)", bandwidth).group(1)
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    else:
        gap = "0"
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    t_mode = "NR-FR1-" + mode + "__TDD_" + bw1 + "_30kHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:NR5G:MEAS MCAClr")
    v.send_cmd("MMEM:LOAD:TMOD:CC1 '%s'" % t_mode)
    v.send_cmd("CONF:NR5G:NOCC 2")
    v.send_cmd("CONF:NR5G:DL:CC1:BW BW%s" % bw1)
    v.send_cmd("CONF:NR5G:DL:CC2:BW BW%s" % bw2)
    offset1 = int((float(freq) - float(bw2) / 2 - float(gap) / 2) * 1e6)
    offset2 = int((float(freq) + float(bw1) / 2 + float(gap) / 2) * 1e6)
    v.send_cmd("SENS:FREQ:CENT:CC1 %d" % offset1)
    v.send_cmd("SENS:FREQ:CENT:CC2 %d" % offset2)


    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("SENS:SWE:OPT SPE")
    v.send_cmd("SENS:SWE:TIME 0.005")

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res = v.rec_cmd("CALC:MARK:FUNC:POW:RES? MCAC").split(",")
    return strlist_to_floatlist(res)


def nr5g_evm(v: VisaConnection, rf_params: Dict[str, str],
             rel: float = 25, atten: int = 20,
             current: str = None, rename: str = None,
             exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[List[float]]:
    """
    INST:CRE:NEW NR5G, '5G NR'
    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [EVM PDSCH QPSK(%), EVM PDSCH 16QAM(%), EVM PDSCH 64QAM(%), EVM PDSCH 256QAM(%),
                0                   1                   2                   3
            EVM ALL(%), EVM Phys Channel(%), EVM Phys Signal(%),
                4           5                   6
            Frequency Error(Hz), Sampling Error(ppm),
                7                   8
            I/Q Offset(dB), I/Q Gain Imbalance(dB), I/Q Quadrature Error(°),
                9               10                      11
            OSTP(dBm),
                12
            Power(dBm), Crest Factor(dB)]
                13      14
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    t_mode = "NR-FR1-" + mode + "__TDD_" + bandwidth + "_30kHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:NR5G:MEAS EVM")
    v.send_cmd("MMEM:LOAD:TMOD:CC1 '%s'" % t_mode)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("CONF:NR5G:DL:CC1:RFUC:STAT OFF")
    v.send_cmd("LAY:REM:WIND '3'")
    v.send_cmd("INIT:IMM;*WAI")
    v.send_cmd("LAY:ADD:WIND? '4',LEFT,EVSY")

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    evm_qpsk = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSQP:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSQP:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSQP:MAX?"))]
    evm_16qam = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSST:AVER?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSST:MIN?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSST:MAX?"))]
    evm_64qam = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSSF:AVER?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSSF:MIN?")),
                 str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSSF:MAX?"))]
    evm_256qam = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSTS:AVER?")),
                  str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSTS:MIN?")),
                  str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:DSTS:MAX?"))]
    evm_all = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:AVER?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:MIN?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:MAX?"))]
    evm_pch = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PCH:AVER?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PCH:MIN?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PCH:MAX?"))]
    evm_psig = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PSIG:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PSIG:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:EVM:PSIG:MAX?"))]
    evm_ferr = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:FERR:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:FERR:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:FERR:MAX?"))]
    evm_serr = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:SERR:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:SERR:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:SERR:MAX?"))]
    evm_iqof = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:IQOF:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:IQOF:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:IQOF:MAX?"))]
    evm_gimb = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:GIMB:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:GIMB:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:GIMB:MAX?"))]
    evm_quad = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:QUAD:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:QUAD:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:QUAD:MAX?"))]
    evm_ostp = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:OSTP:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:OSTP:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:OSTP:MAX?"))]
    evm_pow = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:POW:AVER?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:POW:MIN?")),
               str_to_float(v.rec_cmd("FETC:CC1:SUMM:POW:MAX?"))]
    evm_cres = [str_to_float(v.rec_cmd("FETC:CC1:SUMM:CRES:AVER?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:CRES:MIN?")),
                str_to_float(v.rec_cmd("FETC:CC1:SUMM:CRES:MAX?"))]
    res = [evm_qpsk, evm_16qam, evm_64qam, evm_256qam, evm_all, evm_pch, evm_psig, evm_ferr, evm_serr, evm_iqof,
           evm_gimb, evm_quad, evm_ostp, evm_pow, evm_cres]
    return res


def nr5g_multi_evm(v: VisaConnection, rf_params: Dict[str, str],
                   rel: float = 25, atten: int = 20,
                   current: str = None, rename: str = None,
                   exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[List[float]]:
    """
    INST:CRE:NEW NR5G, '5G NR'
    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [EVM PDSCH QPSK(%), EVM PDSCH 16QAM(%), EVM PDSCH 64QAM(%), EVM PDSCH 256QAM(%),
                0                   1                   2                   3
            EVM ALL(%), EVM Phys Channel(%), EVM Phys Signal(%),
                4           5                   6
            Frequency Error(Hz), Sampling Error(ppm),
                7                   8
            I/Q Offset(dB), I/Q Gain Imbalance(dB), I/Q Quadrature Error(¡ã),
                9               10                      11
            OSTP(dBm),
                12
            Power(dBm), Crest Factor(dB)]
                13      14
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    bw1 = re.match("(.\d+)", bandwidth).group(1)
    if bandwidth.find("gap") > -1:
        gap = re.search("gap(.\d+)", bandwidth).group(1)
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    else:
        gap = "0"
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    t_mode = "NR-FR1-" + mode + "__TDD_" + bw1 + "_30kHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:NR5G:MEAS EVM")
    v.send_cmd("MMEM:LOAD:TMOD:CC1 '%s'" % t_mode)
    v.send_cmd("CONF:NR5G:NOCC 2")
    v.send_cmd("CONF:NR5G:DL:CC1:BW BW%s" % bw1)
    v.send_cmd("CONF:NR5G:DL:CC2:BW BW%s" % bw2)
    offset1 = int((float(freq) - float(bw2) / 2 - float(gap) / 2) * 1e6)
    offset2 = int((float(freq) + float(bw1) / 2 + float(gap) / 2) * 1e6)
    v.send_cmd("SENS:FREQ:CENT:CC1 %d" % offset1)
    v.send_cmd("SENS:FREQ:CENT:CC2 %d" % offset2)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    v.send_cmd("INP:ATT %ddB" % atten)

    v.send_cmd("CONF:NR5G:DL:CC1:RFUC:STAT OFF")
    v.send_cmd("LAY:REM:WIND '3'")
    v.send_cmd("INIT:IMM;*WAI")
    v.send_cmd("LAY:ADD:WIND? '4',LEFT,EVSY")

    # v.send_cmd("INIT:CONT OFF")
    # v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res_list = []
    for i in range(2):
        evm_qpsk = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSQP:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSQP:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSQP:MAX?" % (i+1)))]
        evm_16qam = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSST:AVER?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSST:MIN?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSST:MAX?" % (i+1)))]
        evm_64qam = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSSF:AVER?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSSF:MIN?" % (i+1))),
                     str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSSF:MAX?" % (i+1)))]
        evm_256qam = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSTS:AVER?" % (i+1))),
                      str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSTS:MIN?" % (i+1))),
                      str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:DSTS:MAX?" % (i+1)))]
        evm_all = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:AVER?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:MIN?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:MAX?" % (i+1)))]
        evm_pch = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PCH:AVER?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PCH:MIN?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PCH:MAX?" % (i+1)))]
        evm_psig = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PSIG:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PSIG:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:EVM:PSIG:MAX?" % (i+1)))]
        evm_ferr = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:FERR:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:FERR:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:FERR:MAX?" % (i+1)))]
        evm_serr = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:SERR:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:SERR:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:SERR:MAX?" % (i+1)))]
        evm_iqof = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:IQOF:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:IQOF:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:IQOF:MAX?" % (i+1)))]
        evm_gimb = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:GIMB:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:GIMB:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:GIMB:MAX?" % (i+1)))]
        evm_quad = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:QUAD:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:QUAD:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:QUAD:MAX?" % (i+1)))]
        evm_ostp = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:OSTP:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:OSTP:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:OSTP:MAX?" % (i+1)))]
        evm_pow = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:POW:AVER?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:POW:MIN?" % (i+1))),
                   str_to_float(v.rec_cmd("FETC:CC%d:SUMM:POW:MAX?" % (i+1)))]
        evm_cres = [str_to_float(v.rec_cmd("FETC:CC%d:SUMM:CRES:AVER?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:CRES:MIN?" % (i+1))),
                    str_to_float(v.rec_cmd("FETC:CC%d:SUMM:CRES:MAX?" % (i+1)))]
        res = [evm_qpsk, evm_16qam, evm_64qam, evm_256qam, evm_all, evm_pch, evm_psig, evm_ferr, evm_serr, evm_iqof,
               evm_gimb, evm_quad, evm_ostp, evm_pow, evm_cres]
        res_list.append(res)
    return res_list


def nr5g_sem(v: VisaConnection, rf_params: Dict[str, str],
            rel: float = 25, atten: int = 12,
            current: str = None, rename: str = None,
            exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """

    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [TxPower(dBm), Range No, Start Freq Rel(MHz), Stop Freq Rel(MHz), RBW(MHz),
    Frequency at Delta to Limit(MHz), Power Abs(dBm), Power Rel(dB), Delta to Limit(dB), ...]
    4 Ranges Totally
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    t_mode = "NR-FR1-" + mode + "__TDD_" + bandwidth + "_30kHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:NR5G:MEAS ESP")
    v.send_cmd("MMEM:LOAD:TMOD:CC1 '%s'" % t_mode)



    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
        v.send_cmd("SENS:SWE:EGAT:CONT:STAT ON")

    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    # v.send_cmd("INIT:CONT OFF")

    v.send_cmd(r"SENS:ESP1:PRES:STAN 'C:\R_S\Instr\sem_std\NR5G\NR5G_SEM_DL_LocalArea_BW%s_BASESTATIONTYPE_1_C_FSW.xml'" % rf_params.get('bandwidth'))

    v.send_cmd("SENS:ESP1:RANG2:DEL")
    v.send_cmd("SENS:ESP1:RANG5:DEL")
    if bandwidth == "20":
        v.send_cmd("SENS:ESP1:RANG1:FREQ:STOP -15050000")
        v.send_cmd("SENS:ESP1:RANG5:FREQ:STAR 15050000")
    elif bandwidth == "100":
        v.send_cmd("SENS:ESP1:RANG1:FREQ:STOP -55050000")
        v.send_cmd("SENS:ESP1:RANG5:FREQ:STAR 55050000")

    for i in range(5):
        v.send_cmd("SENS:ESP1:RANG%d:INP:ATT %d" % ((i + 1), atten))
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STAR -37")
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STOP -30")
    v.send_cmd("SENS:ESP1:RANG4:LIM1:ABS:STAR -30")
    v.send_cmd("SENS:ESP1:RANG4:LIM1:ABS:STOP -37")


    # v.send_cmd("INIT:CONT OFF")
    v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res1 = v.rec_cmd("CALC:MARK:FUNC:POW:RES? CPOW")
    res2 = v.rec_cmd("TRAC:DATA? LIST").split(",")
    for i in range(4):
        res2[1 + 11 * i: 5 + 11 * i] = hzlist_to_mhzlist(res2[1 + 11 * i: 5 + 11 * i])
    res2.insert(0, res1)
    res = strlist_to_floatlist(res2)
    while 0.0 in res:
        res.remove(0.0)
    return res


def nr5g_multi_sem(v: VisaConnection, rf_params: Dict[str, str],
                   rel: float = 25, atten: int = 12,
                   current: str = None, rename: str = None,
                   exs: bool = False, snap: bool = False, snappath: str = None, delay: int = 5) -> List[float]:
    """

    :param v:
    :param rf_params:
    :param rel:
    :param atten:
    :param current:
    :param rename:
    :param exs:
    :param snap:
    :param snappath:
    :param delay:
    :return: [TxPower(dBm), Range No, Start Freq Rel(MHz), Stop Freq Rel(MHz), RBW(MHz),
    Frequency at Delta to Limit(MHz), Power Abs(dBm), Power Rel(dB), Delta to Limit(dB), ...]
    4 Ranges Totally
    """
    freq = rf_params.get('freq')
    loss = rf_params.get('loss')
    bandwidth = rf_params.get('bandwidth')
    mode = rf_params.get('mode')
    bw1 = re.match("(.\d+)", bandwidth).group(1)
    if bandwidth.find("gap") > -1:
        gap = re.search("gap(.\d+)", bandwidth).group(1)
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    else:
        gap = "0"
        bw2 = re.search("\+(.\d+)", bandwidth).group(1)
    t_mode = "NR-FR1-" + mode + "__TDD_" + bw1 + "_30kHz"

    if current is not None:
        v.send_cmd("INST '%s'" % current)
        if rename is not None:
            v.send_cmd("INST:REN '%s','%s'" % (current, rename))

    v.send_cmd("CONF:NR5G:MEAS MCESpectrum")
    v.send_cmd("MMEM:LOAD:TMOD:CC1 '%s'" % t_mode)
    v.send_cmd("CONF:NR5G:DL:CC1:BW BW%s" % bw1)
    v.send_cmd("CONF:NR5G:DL:CC2:BW BW%s" % bw2)
    offset1 = int((float(freq) - float(bw2) / 2 - float(gap) / 2) * 1e6)
    offset2 = int((float(freq) + float(bw1) / 2 + float(gap) / 2) * 1e6)
    v.send_cmd("SENS:FREQ:CENT:CC1 %d" % offset1)
    v.send_cmd("SENS:FREQ:CENT:CC2 %d" % offset2)

    if exs:
        v.send_cmd("TRIG:SOUR EXT")
        v.send_cmd("SENS:SWE:EGAT ON")
        v.send_cmd("SENS:SWE:EGAT:CONT:STAT ON")

    v.send_cmd("FREQ:CENT %sMHz" % freq)
    v.send_cmd("DISP:TRAC:Y:RLEV:OFFS %sdB" % loss)
    v.send_cmd("DISP:TRAC:Y:RLEV %fdBm" % rel)
    # v.send_cmd("INIT:CONT OFF")

    v.send_cmd(r"SENS:ESP1:PRES:STAN 'C:\R_S\Instr\sem_std\NR5G\NR5G_SEM_DL_LocalArea_BW%s_BASESTATIONTYPE_1_C_FSW.xml'" % rf_params.get('bandwidth'))

    v.send_cmd("SENS:ESP1:RANG2:DEL")
    v.send_cmd("SENS:ESP1:RANG5:DEL")
    if bandwidth == "20":
        v.send_cmd("SENS:ESP1:RANG1:FREQ:STOP -15050000")
        v.send_cmd("SENS:ESP1:RANG5:FREQ:STAR 15050000")
    elif bandwidth == "100":
        v.send_cmd("SENS:ESP1:RANG1:FREQ:STOP -55050000")
        v.send_cmd("SENS:ESP1:RANG5:FREQ:STAR 55050000")

    for i in range(5):
        v.send_cmd("SENS:ESP1:RANG%d:INP:ATT %d" % ((i + 1), atten))
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STAR -37")
    v.send_cmd("SENS:ESP1:RANG2:LIM1:ABS:STOP -30")
    v.send_cmd("SENS:ESP1:RANG4:LIM1:ABS:STAR -30")
    v.send_cmd("SENS:ESP1:RANG4:LIM1:ABS:STOP -37")


    # v.send_cmd("INIT:CONT OFF")
    v.send_cmd("INIT;*WAI")
    time.sleep(delay)

    if snap:
        v.send_cmd("HCOP:DEST 'SYST:COMM:MMEM'")
        v.send_cmd("HCOP:DEV:LANG1 JPG")
        v.send_cmd("HCOP:CMAP:DEF4")
        v.send_cmd("MMEM:NAME '%s'" % snappath)
        v.send_cmd("HCOP:IMM1")

    res1 = v.rec_cmd("CALC:MARK:FUNC:POW:RES? CPOW")
    res2 = v.rec_cmd("TRAC:DATA? LIST").split(",")
    for i in range(4):
        res2[1 + 11 * i: 5 + 11 * i] = hzlist_to_mhzlist(res2[1 + 11 * i: 5 + 11 * i])
    res2.insert(0, res1)
    res = strlist_to_floatlist(res2)
    while 0.0 in res:
        res.remove(0.0)
    return res
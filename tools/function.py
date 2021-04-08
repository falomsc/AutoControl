from typing import List

from openpyxl.worksheet.worksheet import Worksheet


def str_to_float(s) -> float:
    if abs(float(s)) <= 0.1:
        f = "%.4f" % float(s)
    elif abs(float(s)) < 1:
        f = "%.3f" % float(s)
    else:
        f = "%.2f" % float(s)
    return float(f)


def hz_to_mhz(s) -> float:
    if abs(float(s) / 1000000) <= 0.1:
        f = "%.4f" % (float(s) / 1000000)
    elif abs(float(s) / 1000000) < 1:
        f = "%.3f" % (float(s) / 1000000)
    else:
        f = "%.2f" % (float(s) / 1000000)
    return float(f)


def strlist_to_floatlist(l: List) -> List[float]:
    res = []
    for i in l:
        res.append(str_to_float(i))
    return res


def hzlist_to_mhzlist(l: List) -> List[float]:
    res = []
    for i in l:
        res.append(hz_to_mhz(i))
    return res


def new_line(ws: Worksheet, space: int = 1, init_row: int = 1, col: int = 1) -> int:
    row = init_row
    while True:
        if ws.cell(row=row, column=col).value is None:
            break
        row += space
    return row

from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.worksheet import Worksheet


class Fill_Report:
    BASIC = 1
    MADURA = 2
    ACP = 3
    OBW = 4

    def __init__(self, wb: Workbook):





def fill_xl_value(ws: Worksheet, row: int, res_acp: list):
    first_row = tuple(ws.values)[0]
    second_row = tuple(ws.values)[1]
    for i, v in enumerate(second_row):
        if v == "CHP1(dBm)":
            print(i)









if __name__ == '__main__':
    wb = load_workbook("./report/res.xlsx")
    print(type(wb))

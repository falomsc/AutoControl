from typing import List, Dict

from lxml import etree


def get_cali_tx_config(path: str) -> List[List[List[Dict[str, str]]]]:
    """
    tx_pipe_list: [tx_branch_list1, tx_branch_list2, ...]
                    pipe1           pipe2
    tx_freq_list: [tx_freq_list1, tx_freq_list2, ...]
                    frequency1      frequency2
    tx_branch_list: [tx_branch1, tx_branch2, ...]
                    branch1         branch2
    tx_branch: {"pipe":str, "freq":str, "gain_list":str, "branch":str}
    """
    tree = etree.parse(path)
    px_list = tree.xpath("//pipe")
    tx_pipe_list = []
    for px in px_list:
        pipe = px.xpath("./@pip")[0]
        fx_list = px.xpath("./freq")
        tx_freq_list = []
        for fx in fx_list:
            freq = str(fx.xpath("./@fre")[0])
            bx_list = fx.xpath("branch")
            tx_branch_list = []
            for bx in bx_list:
                branch = str(bx.xpath("./text()")[0])
                gain_list = str(bx.xpath("./@gain_list")[0])
                tx_branch = dict(pipe=pipe, freq=freq, gain_list=gain_list, branch=branch)
                tx_branch_list.append(tx_branch)
            tx_freq_list.append(tx_branch_list)
        tx_pipe_list.append(tx_freq_list)
    return tx_pipe_list


if __name__ == '__main__':
    for i in get_cali_tx_config("./tx_cali_all.xml"):
        print(i)

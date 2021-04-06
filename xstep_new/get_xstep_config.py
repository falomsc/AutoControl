import configparser
from typing import List, Dict

from lxml import etree

cf = configparser.ConfigParser()
cf.read("./config/equip_config.ini")

hostname = cf.get("ssh", "hostname")
port = int(cf.get("ssh", "port"))
username = cf.get("ssh", "username")
password = cf.get("ssh", "password")

address = cf.get("visa", "address")
timeout = int(cf.get("visa", "timeout"))


def get_xstep_tx_config(path: str) -> List[List[List[List[Dict[str, str]]]]]:
    """
    tx_bandwidth_list: [tx_pipe_list, tx_pipe_list2, ...]
                        bandwidth1      bandwidth2
    tx_pipe_list: [tx_branch_list1, tx_branch_list2, ...]
                    pipe1           pipe2
    tx_branch_list: [tx_freq_list1, tx_freq_list2, ...]
                    branch1         branch2
    tx_freq_list: [tx_freq1, tx_freq2, ...]
                    frequency1  frequency2
    tx_freq: {"bandwidth":str, "pipe":str, "branch":str, "loss":str, "power":str, "freq":str}
    :param path:
    :return:
    """
    tree = etree.parse(path)
    bx_list = tree.xpath("//bandwidth")
    tx_bandwidth_list = []
    for bx in bx_list:
        px_list = bx.xpath("./pipe")
        bandwidth = str(bx.xpath("./@bw")[0])
        tx_pipe_list = []
        for px in px_list:
            pipe = str(px.xpath("./@pip")[0])
            brx_list = px.xpath("./branch")
            tx_branch_list = []
            for brx in brx_list:
                branch = str(brx.xpath("./@id")[0])
                loss = str(brx.xpath("./loss/text()")[0])
                fx_list = brx.xpath("./freq")
                tx_freq_list = []
                for fx in fx_list:
                    power = str(fx.xpath("./@power")[0])
                    freq = str(fx.xpath("./text()")[0])
                    tx_freq = dict(bandwidth=bandwidth, pipe=pipe, branch=branch, loss=loss,
                                   power=power, freq=freq)
                    tx_freq_list.append(tx_freq)
                tx_branch_list.append(tx_freq_list)
            tx_pipe_list.append(tx_branch_list)
        tx_bandwidth_list.append(tx_pipe_list)
    return tx_bandwidth_list


# if __name__ == '__main__':
#     # get_xstep_tx_config("./config/5G_config.xml")
#     for i in get_xstep_tx_config("./config/4G_config.xml"):
#         for j in i:
#             for k in j:
#                 print(k)

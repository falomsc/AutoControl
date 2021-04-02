from typing import List

from lxml import etree


def get_tx_config(path: str) -> List:
    """
    tx_params_pipe_list: [tx_params_branch_list1, tx_params_branch_list2, ...]
                            pipe1                   pipe1
    tx_params_branch_list: [tx_params_freq_list1, tx_params_freq_list2, ...]
                            branch1                 branch2
    tx_params_freq_list: [tx_params_freq, tx_params_freq, ...]
                            frequency1      frequency2
    tx_params_freq: {"pipe":str, "branch":str, "freq":str, "gainlist":list}
    :param path: "./config/4GTX.xml"
    :return:
    """
    tree = etree.parse(path)
    px_list = tree.xpath("//pipe")
    tx_params_pipe_list = []
    for px in px_list:
        pipe = px.xpath("./@pip")[0]
        bx_list = px.xpath("./branch")
        tx_params_branch_list = []
        for bx in bx_list:
            branch = str(bx.xpath("./@id")[0])
            fx_list = bx.xpath("freq")
            tx_params_freq_list = []
            for fx in fx_list:
                gain_list = str(fx.xpath("./@gainlist")[0])
                freq = str(fx.xpath("./text()")[0])
                tx_params_freq = dict(pipe=pipe, branch=branch, freq=freq, gain_list=gain_list)
                tx_params_freq_list.append(tx_params_freq)
            tx_params_branch_list.append(tx_params_freq_list)
        tx_params_pipe_list.append(tx_params_branch_list)
    return tx_params_pipe_list


def get_rx_config(path: str) -> List:
    """
    rx_params_pipe_list: [rx_params_branch_list1, rx_params_branch_list2, ...]
                            pipe1                   pipe1
    rx_params_branch_list: [rx_params_freq_list1, rx_params_freq_list2, ...]
                            branch1                 branch2
    rx_params_freq_list: [rx_params_freq, rx_params_freq, ...]
                            frequency1      frequency2
    rx_params_freq: [rx_params_gain_range1, rx_params_gain_range2, ...]
                        gain_range1         gain_range2
    rx_params_gain_range: {"pipe":str, "branch":str, "freq":str, "start":str, "stop":str, "step":str, "power":str}
    :param path: "./config/4GRX.xml"
    :return:
    """
    tree = etree.parse(path)
    px_list = tree.xpath("//pipe")
    rx_params_pipe_list = []
    for px in px_list:
        pipe = px.xpath("./@pip")[0]
        bx_list = px.xpath("./branch")
        rx_params_branch_list = []
        for bx in bx_list:
            branch = str(bx.xpath("./@id")[0])
            fx_list = bx.xpath("fre")
            rx_params_freq_list = []
            for fx in fx_list:
                freq = str(fx.xpath("./@freq")[0])
                grx_list = fx.xpath("./power")
                rx_params_freq = []
                for grx in grx_list:
                    start = str(grx.xpath("./@start")[0])
                    stop = str(grx.xpath("./@stop")[0])
                    step = str(grx.xpath("./@step")[0])
                    power = str(grx.xpath("./text()")[0])
                    rx_params_gain_range = dict(pipe=pipe, branch=branch, freq=freq,
                                                start=start, stop=stop, step=step, power=power)
                    rx_params_freq.append(rx_params_gain_range)
                rx_params_freq_list.append(rx_params_freq)
            rx_params_branch_list.append(rx_params_freq_list)
        rx_params_pipe_list.append(rx_params_branch_list)
    return rx_params_pipe_list


if __name__ == '__main__':
    path = "./config/4GRX.xml"
    rx_params_pipe_list = get_rx_config(path)
    pip = rx_params_pipe_list[0][0][0][0].get("pipe")
    print(pip)

import time

import pyvisa as visa


class VisaConnection:
    def __init__(self, address: str, timeout: int = 10000):
        """
        :param address:
        :param timeout: milliseconds
        """
        self._rm = visa.ResourceManager()
        self._tcp_inst = self._rm.open_resource(address)
        self._tcp_inst.timeout = timeout

    def send_cmd(self, command: str, delay: int = 0.1) -> None:
        """

        :param command:
        :param delay:
        :return:
        """
        self._tcp_inst.write(command)
        time.sleep(delay)

    def rec_cmd(self, command: str) -> str:
        """

        :param command:
        :return:
        """
        return self._tcp_inst.query(command)


if __name__ == '__main__':
    pass

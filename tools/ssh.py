import re
import time

import paramiko
from PyQt5.QtCore import pyqtSignal

from tools.log import SSHLogger


class SSHConnection:
    COMMON = 1
    RFSW = 2
    AASHELL = 3

    def __init__(self, hostname: str, port: int, username: str, password: str,
                 print_flag: bool = True, log_flag: bool = False, sg: pyqtSignal = None,
                 delay: float = 0.5):
        """

        :param hostname:
        :param port:
        :param username:
        :param password:
        :param print_flag:
        :param log_flag:
        :param sg:
        """
        self.type = SSHConnection.COMMON
        self.print_flag = print_flag
        self._log_flag = log_flag
        self.sg_flag = False
        self.time_interval = 0.5
        self.sg = sg
        self._delay = delay

        self._transport = paramiko.Transport((hostname, port))
        self._transport.connect(username=username, password=password)
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh._transport = self._transport
        self._channel = self._transport.open_session()
        self._channel.get_pty()
        self._channel.invoke_shell()
        self._read_until("toor4nsn@.+# ")

    def _read_until(self, endre: str) -> str:
        total_out = ""
        while True:
            if self._channel.recv_ready():
                output = self._channel.recv(1024)
                total_out += output.decode("utf-8", "ignore").replace('\r', '')
                self.pprint(output.decode("utf-8", "ignore").replace('\r', ''))
            else:
                time.sleep(self.time_interval)
            if re.search(endre, total_out):
                break
        time.sleep(self._delay)
        return total_out

    def common_cmd(self, command: str) -> str:
        if self.type == SSHConnection.RFSW:
            self._channel.send("exit \n")
            self._read_until("toor4nsn@.+# ")
        elif self.type == SSHConnection.AASHELL:
            self._channel.send("quit \n")
            self._read_until("toor4nsn@.+# ")
        self.type = SSHConnection.COMMON
        self._channel.send(command + " \n")
        return self._read_until("toor4nsn@.+# ")

    def rfsw_cmd(self, command: str) -> str:
        if self.type == SSHConnection.COMMON:
            self._channel.send("rfsw_cli \n")
            self._read_until("rfsw> ")
        elif self.type == SSHConnection.AASHELL:
            self._channel.send("quit \n")
            self._channel.send("rfsw_cli \n")
            self._read_until("rfsw> ")
        self.type = SSHConnection.RFSW
        self._channel.send(command + " \n")
        return self._read_until("rfsw> ")

    def aashell_cmd(self, command: str) -> str:
        if self.type == SSHConnection.COMMON:
            self._channel.send("telnet localhost 15007 \n")
            self._read_until("AaShell> ")
        elif self.type == SSHConnection.RFSW:
            self._channel.send("exit \n")
            self._read_until("toor4nsn@.+# ")
            self._channel.send("telnet localhost 15007 \n")
            self._read_until("AaShell> ")
        self.type = SSHConnection.AASHELL
        self._channel.send(command + " \n")
        return self._read_until("AaShell> ")

    def reboot(self) -> None:
        if self.type == SSHConnection.AASHELL:
            self._channel.send("exit \n")
            self._read_until("toor4nsn@.+# ")
        self._channel.send("reboot \n")
        self.pprint("rebooting!... \n")

    # TODO reconnect function
    def reconnect(self):
        pass

    def pprint(self, message: str, wrap: bool = False) -> None:
        """
        print message in the console
        :param wrap:
        :param message:
        :return:
        """
        if self.print_flag:
            if wrap:
                print(message)
            else:
                print(message, end="")
        if self.log_flag:
            self.log.logger.info(message)
        if self.sg_flag:
            self.sg.emit(message)

    @property
    def log_flag(self) -> bool:
        return self._log_flag

    @log_flag.setter
    def log_flag(self, log_flag: bool) -> None:
        """
        create SSHLogger and delete SSHLogger
        :param log_flag:
        :return:
        """
        if log_flag and not self._log_flag:
            self.log = SSHLogger()
            self._log_flag = True
        elif not log_flag and self._log_flag:
            del self.log
            self._log_flag = False

    def close(self):
        self._ssh.close()
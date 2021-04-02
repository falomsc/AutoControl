from tools.ssh import SSHConnection
from tools.ssh_cmd import *

s = SSHConnection(host="192.168.255.129", port=22, username="toor4nsn", password="oZPS0POrRieRtu")
rf_params = {"freq":"3500", "bandwidth":"100", "mode":"31", "branch":"0", "loss":"28.9", "power":"24", "temp": "25"}
tx_on(s, rf_params)
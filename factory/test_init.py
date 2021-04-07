import re
import time

from tools.ssh import SSHConnection

def count():
    for i in range(120):
        print(120-i)
        time.sleep(1)



p = f1 = f2 = e = 0
while True:
    if p+f1+f2 == 20:
        break
    s = SSHConnection(hostname="192.168.255.129", port=22, username="toor4nsn", password="oZPS0POrRieRtu")
    for i in range(10):
        sync = s.rfsw_cmd("cpri init_ant 0 8")
        if re.search("CPRI synced", sync):
            break
        time.sleep(2)
        if i == 9:
            raise Exception("SYNC FAILED")
    eid = s.rfsw_cmd("cpri read_ant_eid 0")
    if re.search("Error", eid):
        e += 1
        continue
    s.rfsw_cmd("cpri ant_t14_calibration 0")
    s.rfsw_cmd("ant write 0 0x90048 0xffffffff")
    s.rfsw_cmd("ant rf reset 0")
    s.rfsw_cmd("ant squatch3 setTddMode 0 2")
    s.rfsw_cmd("madura create_from_draco 0.0")
    s.rfsw_cmd("madura create_from_draco 0.1")
    init1 = s.rfsw_cmd("ant rf init 0 0 100000")
    if re.search("BW: -3", init1):
        f1 += 1
        s.reboot()
        del s
        print("Total = %d, p = %d, f1 = %d, f2 = %d, eid = %d" % ((p+f1+f2), p, f1, f2, e))
        count()
        continue
        # s.rfsw_cmd("madura ArmMemDump 0.0 /tmp/ArmDump_Madura0_%s.bin"
        #            % time.strftime('%H%M%S', time.localtime()))
        # raise Exception("Madura0 BW-3")

    init2 = s.rfsw_cmd("ant rf init 0 1 20000")
    if re.search("BW: -3", init2):
        f2 += 1
        s.reboot()
        del s
        print("Total = %d, p = %d, f1 = %d, f2 = %d, eid = %d" % ((p+f1+f2), p, f1, f2, e))
        count()
        continue
        # s.rfsw_cmd("madura ArmMemDump 0.1 /tmp/ArmDump_Madura1_%s.bin"
        #            % time.strftime('%H%M%S', time.localtime()))
        # raise Exception("Madura1 BW-3")
    p += 1
    s.reboot()
    del s
    print("Total = %d, p = %d, f1 = %d, f2 = %d, eid = %d" % ((p+f1+f2), p, f1, f2, e))
    count()

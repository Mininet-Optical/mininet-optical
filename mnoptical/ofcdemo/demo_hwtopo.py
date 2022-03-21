#!/usr/bin/env python3

"""
lroadmtest.py: simple netconf control test for lroadm.py
"""

from mnoptical.ofcdemo.Control_Test_Lum import (
    Lumentum_Control_NETCONF, LumentumName_to_IP, Control_Test )

from mnoptical.ofcdemo.Demo_Control import TrafficTest

from sys import argv

NetconfPortBase = 1830

def fixIPMap(nameToIP):
    "Fix name-to-IP map for Mininet"
    for i in range(1, 7):
        port = NetconfPortBase +i
        nameToIP[f'L{i}'] = f'localhost:{port}'

def Control_Test():
    " set up a lightpath from r4 to r1 bidirectionally with channel 5"

    ####### Lumentum Test ########
    path = ['r4', 'r3', 'r2', 'r1']
    Controller = Lumentum_Control_NETCONF()
    print('*** Cleaning ROADMs')
    Controller.cleanAllROADMs()
    Controller.installPath(path=path, channel=5, lightpathID=1)
    Controller.channel_monitor(path=path, lightpathID=1)
    print("Press enter to continue...")
    input()
    Controller.uninstallPath(path=path, lightpathID=1)

if __name__ == '__main__':

    # Fix name-to-ip map for Mininet
    fixIPMap(LumentumName_to_IP)

    print("*** IP Address Map:")
    print(LumentumName_to_IP)

    if 'test' in argv:
        Control_Test()
    else:
        TrafficTest(Mininet_Enable=False)

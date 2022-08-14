#!/usr/bin/env python3

"""
nc_add_connection.py: add an LROADM connection using netconf

currently hard-wired for cosmos tutorial
"""

# For now this is hard-wired for the cosmos tutorial
from mnoptical.examples.cosmostutorial import username, password

from mnoptical.ofcdemo.lumentum_NETCONF_API import (
    Lumentum, Lumentum_NETCONF
)

from sys import argv

def connect(ipport, module, connection_id, operation, blocked,
            inport, outport, startfreq, endfreq, loss, name):
    "Make a netconf connection RPC, printing results and new config"
    roadm = Lumentum(ipport, username=username, password=password)
    connection = Lumentum.WSSConnection(
        module=module, connection_id=connection_id, operation='in-service',
        blocked='false', input_port=inport, output_port=outport,
        start_freq=startfreq, end_freq=endfreq,
        attenuation=loss, name=name)
    reply = roadm.wss_add_connections([connection])
    print('Reply:', reply)
        
if __name__ == '__main__':
    if 'test' in argv: exit(0)  # allow runtests.sh to succeed
    if len(argv) != 12:
        print("Usage: \n"
              f"{argv[0]} "
              "ipport module connection_id operation blocked "
              "inport outport startfreq endfreq loss name ")
        print("Example:\n"
              f"{argv[0]} localhost:1831 1 10 in-service false "
              "4102 4201 192950 193050 5 Exp1-FromTor1")
        exit(1)
    else:
        args = argv[1:]
        connect(*args)

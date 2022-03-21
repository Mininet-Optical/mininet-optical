#!/usr/bin/python

"""
demo.py: Start up Mininet with OFC Demo Topology
"""

from mnoptical.dataplane import Mininet, ROADM, Terminal, disableIPv6
from mnoptical.ofcdemo.demolib_2021 import DemoTopo, CLI
from mnoptical.rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

from sys import argv, stdout
from os.path import dirname
from subprocess import check_call

if __name__ == '__main__':

    setLogLevel( 'info' )
    cleanup()
    info( '*** Creating Demo Topology \n' )
    net = Mininet( topo=DemoTopo( n=4, txCount=90), autoSetMacs=True,
                   controller=RemoteController )
    disableIPv6( net )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    if 'test' in argv:
        check_call("python3 -m mnoptical.ofcdemo.Demo_Control_2".split())
    else:
        CLI( net )
    stdout.flush()
    restServer.stop()
    stdout.flush()    
    net.stop()

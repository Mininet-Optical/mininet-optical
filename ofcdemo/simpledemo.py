#!/usr/bin/python

"""
simpledemo.py: demonstrate physical/dataplane/control plane emulation

This demo uses the simpler 3-node linear ROADM topology
"""

from dataplane import Mininet, ROADM, Terminal, disableIPv6
from ofcdemo.demolib import LinearRoadmTopo, CLI
from rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

if __name__ == '__main__':

    cleanup()
    setLogLevel( 'info' )
    net = Mininet( topo=LinearRoadmTopo(), autoSetMacs=True,
                   controller=RemoteController )
    disableIPv6( net )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    CLI( net )
    restServer.stop()
    net.stop()

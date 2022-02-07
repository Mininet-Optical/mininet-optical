#!/usr/bin/python

"""
simpledemo.py: demonstrate physical/dataplane/control plane emulation

This demo uses the simpler 3-node linear ROADM topology
"""

from mnoptical.dataplane import Mininet, ROADM, Terminal, disableIPv6
from mnoptical.ofcdemo.demolib import LinearRoadmTopo, CLI
from mnoptical.rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

if __name__ == '__main__':

    setLogLevel( 'info' )
    cleanup()
    net = Mininet( topo=LinearRoadmTopo(txCount=6), autoSetMacs=True,
                   controller=RemoteController )
    disableIPv6( net )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    CLI( net )
    restServer.stop()
    net.stop()

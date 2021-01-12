#!/usr/bin/python

"""
demo.py: Start up Mininet with OFC Demo Topology
"""

from dataplane import Mininet, ROADM, Terminal, disableIPv6
from ofcdemo.demolib import DemoTopo, CLI
from rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

if __name__ == '__main__':

    cleanup()
    setLogLevel( 'info' )
    info( '*** Creating Demo Topology \n' )
    net = Mininet( topo=DemoTopo( txCount=15), autoSetMacs=True,
                   controller=RemoteController )
    disableIPv6( net )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    CLI( net )
    restServer.stop()
    net.stop()

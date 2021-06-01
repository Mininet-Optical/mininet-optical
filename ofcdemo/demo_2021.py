#!/usr/bin/python

"""
demo.py: Start up Mininet with OFC Demo Topology
"""

from dataplane import Mininet, ROADM, Terminal, disableIPv6
from ofcdemo.demolib_2021 import DemoTopo, CLI
from rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

if __name__ == '__main__':

    setLogLevel( 'info' )
    cleanup()
    info( '*** Creating Demo Topology \n' )
    net = Mininet( topo=DemoTopo( txCount=90), autoSetMacs=True,
                   controller=RemoteController )
    disableIPv6( net )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    CLI( net )
    restServer.stop()
    net.stop()

#!/usr/bin/python

"""
demopp.py: Start up Mininet with OFC Demo Topology - PP
"""

from mnoptical.dataplane import Mininet, ROADM, Terminal, disableIPv6
from mnoptical.ofcdemo.demolib import DemoTopo, DemoTopobis, CLI
from mnoptical.rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController
from mnoptical.examples.singleroadm import plotNet

if __name__ == '__main__':

    setLogLevel( 'info' )
    cleanup()
    info( '*** Creating Demo Topology \n' )
    net = Mininet( topo=DemoTopobis( txCount=80), autoSetMacs=True,
                   controller=RemoteController )
    disableIPv6( net )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    plotNet(net, outfile='ofc25_bis.png', directed=False,
            linksPerPair=None)
    CLI( net )
    restServer.stop()
    net.stop()

#!/usr/bin/python

"""
demo.py: demonstrate physical/dataplane/control plane emulation

Note: this prototype is not yet complete

- missing OFC demo topology
- missing OFC demo scenarios
- control plane is simplified REST API
- controller is python script and not ONOS (yet)
- no ONOS CLI yet
- no topology visualization in ONOS GUI (yet)
"""

from dataplane import ROADM, Terminal
from demolib import LinearRoadmTopo, CLI
from rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

if __name__ == '__main__':

    cleanup()
    setLogLevel( 'info' )
    net = Mininet( topo=LinearRoadmTopo(), autoSetMacs=True,
                   controller=RemoteController )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    CLI( net )
    restServer.stop()
    net.stop()

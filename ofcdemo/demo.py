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
from demolib import LinearRoadmTopo, configureLinearNet, CLI
from rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

if __name__ == '__main__':

    cleanup()
    setLogLevel( 'info' )
    net = Mininet( topo=LinearRoadmTopo() )
    restServer = RestServer( net )
    net.start()
    # Only configure packet network directly!
    # Optical network will be configured remotely.
    configureLinearNet( net, packetOnly=True )
    restServer.start()
    CLI( net )
    restServer.stop()
    net.stop()

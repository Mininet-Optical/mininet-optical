#!/usr/bin/env python3

"""
simplelink.py: simple link between two terminals

This is very close to the simplest fully emulated packet-optical
network that we can create.

To configure the optical network using the REST API:

curl 'localhost:8080/connect?node=t1&ethPort=1&wdmPort=2&channel=1'
curl 'localhost:8080/turn_on?node=t1'
curl 'localhost:8080/turn_on?node=t2'
"""

from dataplane import (Terminal, OpticalLink, OpticalNet as Mininet,
                       km, dB, dBm)
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.clean import cleanup

class SimpleLinkTopo(Topo):
    """Simple link topology:
       h1 - t1 - (boost->) --25km-- (<-boost) - t1 - h2"""

    def build(self):
        "Build single link topology"
        # Packet network elements
        h1, h2 = self.addHost('h1'), self.addHost('h2')
        # Optical network elements
        params = {'transceivers': [('tx1',0*dBm,'C')],
                  'receiver_threshold': 15.0*dB } # FIXME
        t1 = self.addSwitch('t1', cls=Terminal, **params)
        t2 = self.addSwitch('t2', cls=Terminal, **params)
        # Ethernet links
        self.addLink(h1, t1, port2=1)
        self.addLink(h2, t2, port2=1)
        # WDM links
        self.addLink(t1, t2, cls=OpticalLink, port1=2, port2=2,
                     boost=('boost', {'target_gain':17*dB}),
                     spans=[25*km])

if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')

    topo = SimpleLinkTopo()
    net = Mininet(topo=topo)
    restServer = RestServer(net)

    net.start()
    restServer.start()
    CLI(net)
    restServer.stop()
    net.stop()

#!/usr/bin/env python3

"""
single-link.py: single link between two terminals

This is a slightly more complicated single-link topology.

Some complexity is added by a span consisting of two 25km
fiber segments with boost amplifiers and compensating amplifiers,
as well as monitors for the terminals.

Also the hosts are now connected to an Ethernet switch rather
than directly to the terminals/transceivers.

To configure the optical network using the REST API:

mn=localhost:8080; t1=$mn; t2=$mn
curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1'
curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=1'
curl "$t1/turn_on?node=t1'
curl "$t2/turn_on?node=t2'
"""

from sys import argv

from dataplane import (Terminal, OpticalLink, OpticalNet as Mininet,
                       km, dB, dBm)
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import Host, OVSBridge
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

class SingleLinkTopo(Topo):
    """Single link topology:
    h1 - s1 - t1 -
    (boost->,amp2<-) --25km-- amp1 --25km-- (->amp2,<-boost)
    - t1 - s2 - h2
    """
    def build(self):
        "Build single link topology"
        # Packet network elements
        h1, h2 = self.addHost('h1'), self.addHost('h2')
        s1, s2 = self.addSwitch('s1'), self.addSwitch('s2')
        # Optical network elements
        params = {'transceivers': [('tx1',0*dBm,'C')],
                  'monitor_mode': 'in'}
        t1 = self.addSwitch('t1', cls=Terminal, **params)
        t2 = self.addSwitch('t2', cls=Terminal, **params)
        # Ethernet links
        self.addLink(h1, s1)
        self.addLink(s1, t1, port2=1)
        self.addLink(h2, s2)
        self.addLink(s2, t2, port2=1)
        # WDM link
        boost = ('boost', {'target_gain':3.0*dB})
        amp1 = ('amp1', {'target_gain': 25*.22*dB})
        amp2 = ('amp2', {'target_gain': 25*.22*dB})
        spans = [25*km, amp1, 25*km, amp2]
        self.addLink(t1, t2, cls=OpticalLink, port1=2, port2=2,
                     boost=boost, spans=spans)

if __name__ == '__main__':
    cleanup()  # Just in case!
    setLogLevel('info')

    topo = SingleLinkTopo()
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    restServer = RestServer(net)

    net.start()
    restServer.start()
    info(__doc__)
    CLI(net)
    restServer.stop()
    net.stop()

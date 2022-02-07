#!/usr/bin/env python3

"""
simplelink.py: simple link between two terminals

This is very close to the simplest fully emulated packet-optical
network that we can create.

To configure the optical network using the REST API, *open another
window* and use the following commands at the bash prompt (replacing
localhost with the IP address of this system as needed):

mn=localhost:8080; t1=$mn; t2=$mn

curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1"
curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=1"
curl "$t1/turn_on?node=t1"
curl "$t2/turn_on?node=t2"
"""

from mnoptical.dataplane import (Terminal, OpticalLink, OpticalNet as Mininet,
                       km, dB, dBm)
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.demolib import OpticalCLI as CLI

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

from os.path import dirname, realpath, join
from subprocess import run
from sys import argv

class SimpleLinkTopo(Topo):
    """Simple link topology:
       h1 - t1 - (boost->) --25km-- (<-boost) - t2 - h2"""

    def build(self):
        "Build single link topology"
        # Packet network elements
        h1, h2 = self.addHost('h1'), self.addHost('h2')
        # Optical network elements
        params = {'transceivers': [('tx1',0*dBm,'C')],
                  'monitor_mode': 'in'}
        t1 = self.addSwitch('t1', cls=Terminal, **params)
        t2 = self.addSwitch('t2', cls=Terminal, **params)
        # Ethernet links
        self.addLink(h1, t1, port2=1)
        self.addLink(h2, t2, port2=1)
        # WDM link
        self.addLink(t1, t2, cls=OpticalLink, port1=2, port2=2,
                     boost=('boost', {'target_gain':17*dB}),
                     spans=[25*km])

def test(net):
    "Run config script and simple test"
    testdir = dirname(realpath(argv[0]))
    # Note config-singlelink.sh works for us as well
    script = join(testdir, 'config-singlelink.sh')
    run(script)
    assert net.pingAll() == 0

if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')

    topo = SimpleLinkTopo()
    net = Mininet(topo=topo)
    restServer = RestServer(net)

    net.start()
    restServer.start()
    info(__doc__)
    test(net) if 'test' in argv else CLI(net)
    restServer.stop()
    net.stop()

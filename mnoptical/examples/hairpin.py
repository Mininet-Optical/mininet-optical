#!/usr/bin/env python3

"""
hairpin.py: hairpinning through a terminal
"""

from mnoptical.dataplane import (
    Terminal, OpticalLink, OpticalNet as Mininet,
    km, dB, dBm)
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.demolib import OpticalCLI as CLI

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

from os.path import dirname, realpath, join
from subprocess import run
from sys import argv

class HairpinTopo(Topo):
    """Hairpin topology:
       h1 - t1 - t3 - t2 - h2"""

    def build(self):
        "Build hairpin topology"
        # Packet network elements
        h1, h2 = self.addHost('h1'), self.addHost('h2')
        # Optical network elements
        tx1, tx2 = ('tx1',0 *dBm, 'C'), ('tx2', 0*dBm, 'C')
        params1 = {'transceivers': [tx1], 'monitor_mode':'in'}
        params2 = {'transceivers': [tx1, tx2], 'monitor_mode':'in'}
        t1 = self.addSwitch('t1', cls=Terminal, **params1)
        t2 = self.addSwitch('t2', cls=Terminal, **params1)
        t3 = self.addSwitch('t3', cls=Terminal, **params2)
        # Ethernet links
        self.addLink(h1, t1, port2=1)
        self.addLink(h2, t2, port2=1)
        # WDM links
        boost = ('boost', {'target_gain':3.0*dB})
        amp1 = ('amp1', {'target_gain': 25*.22*dB})
        amp2 = ('amp2', {'target_gain': 25*.22*dB})
        spans = [25*km, amp1, 25*km, amp2]
        self.addLink(t1, t3, cls=OpticalLink, port1=2, port2=1,
                     boost=boost, spans=spans)
        self.addLink(t2, t3, cls=OpticalLink, port1=2, port2=2,
                     boost=boost, spans=spans)

    # For testing, you can call this from the CLI:
    # py net.topo.config.test(net)
    def config(_self, net):
        "Configure hairpin O/E/O routing through t3"
        t1, t2, t3 = net['t1'], net['t2'], net['t3']
        t1.connect(1, wdmPort=2, channel=1)
        t2.connect(1, wdmPort=2, channel=2)
        # Hairpin O/E/O through t3
        t3.connect(wdmInPort=1, wdmPort=2, inChannel=1, channel=2)
        # Turn on transceivers
        for t in t1, t2, t3:
            t.turn_on()

def test(net):
    "Run config script and simple test"
    testdir = dirname(realpath(argv[0]))
    script = join(testdir, 'config-hairpin.sh')
    run(script)
    assert net.pingAll() == 0

import pdb

if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')

    topo = HairpinTopo()
    net = Mininet(topo=topo)
    restServer = RestServer(net)

    net.start()
    restServer.start()
    info(__doc__)
    test(net) if 'test' in argv else CLI(net)
    restServer.stop()
    net.stop()

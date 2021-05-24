#!/usr/bin/env python3

"""
    This script shows how to create Terminals by passing Transceiver
    objects to their constructor method (lines 64-67); it also shows
    how to create ROADMs by passing boost and preamp Amplifier objects
    to their constructor method (lines 72-74)

    Simple linear topology:
    h1 - s1 - t1 -- r1 -- t2 - s2 - h2

    Transmitting 1 channel from t1 to t2
"""

from node import Transceiver, Amplifier
from dataplane import (Terminal, ROADM, OpticalLink,
                       OpticalNet as Mininet, km, m, dB, dBm)
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.log import setLogLevel, warning
from mininet.clean import cleanup

from os.path import dirname, realpath, join
from subprocess import run
from sys import argv


def add_amp(node_name=None, type=None, gain_dB=None):
    """
    Create an Amplifier object to add to a ROADM node
    :param node_name: string
    :param type: string ('boost' or 'preamp'
    :param gain_dB: int or float
    """
    label = '%s-%s' % (node_name, type)
    if type == 'preamp':
        return Amplifier(name=label,
                         target_gain=float(gain_dB),
                         boost=True,
                         monitor_mode='out')
    else:
        return Amplifier(name=label,
                         target_gain=float(gain_dB),
                         preamp=True,
                         monitor_mode='out')


class SingleROADMTopo(Topo):
    """
    h1 - s1 - t1 -- r1 -- t2 - s2 - h2
    """
    def build(self):
        "Build single ROADM topology"
        # Packet network elements
        hosts = [self.addHost(h) for h in ('h1', 'h2')]
        switches = [self.addSwitch(s)
                    for s in ('s1', 's2')]

        line_terminals = []
        for i in range(2):
            transceivers = [Transceiver(1, 'tr1', operation_power=0 * dBm)]
            lt = self.addSwitch(
                't%s' % (i + 1), cls=Terminal, transceivers=transceivers,
                monitor_mode='in')
            line_terminals.append(lt)
        t1 = line_terminals[0]
        t2 = line_terminals[1]

        r1 = self.addSwitch('r1', cls=ROADM,
                            preamp=add_amp(node_name='r1', type='preamp', gain_dB=17.6),
                            boost=add_amp(node_name='r2', type='boost', gain_dB=17.0))

        # Ethernet links
        for h, s, t in zip(hosts, switches, line_terminals):
            self.addLink(h, s)
            self.addLink(s, t, port2=1)

        amp1 = ('amp1', {'target_gain': 25 * .22 * dB})
        amp2 = ('amp2', {'target_gain': 25 * .22 * dB})
        spans = [25 * km, amp1, 25 * km, amp2]
        self.addLink(r1, t1, cls=OpticalLink, port1=1, port2=2, spans=spans)
        self.addLink(r1, t2, cls=OpticalLink, port1=2, port2=2, spans=spans)

def test(net):
    "Run config script and simple test"
    testdir = dirname(realpath(argv[0]))
    script = join(testdir, 'config-roadm_with_amps.sh')
    run(script)
    assert net.pingPair() == 0

if __name__ == '__main__':

    cleanup()
    setLogLevel('info')

    topo = SingleROADMTopo()
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    restServer = RestServer(net)
    net.start()
    restServer.start()
    test(net) if 'test' in argv else CLI(net)
    restServer.stop()
    net.stop()

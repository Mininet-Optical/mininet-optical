#!/usr/bin/env python

"""

demolib.py: PTL Demo Topology and CLI

2 linear topologies for different experiments

"""
from dataplane import (Terminal, ROADM, OpticalLink,
                       dBm, dB, km,
                       disableIPv6, Mininet)
from rest import RestServer

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

from collections import namedtuple
import numpy as np

from ofcdemo.demolib import OpticalCLI

# Routers start listening at 6654
ListenPortBase = 6653

CLI = OpticalCLI


class OpticalTopo(Topo):
    "Topo with convenience methods for optical links"

    def wdmLink(self, *args, **kwargs):
        "Convenience function to add an OpticalLink"
        kwargs.update(cls=OpticalLink)
        self.addLink(*args, **kwargs)

    def ethLink(self, *args, **kwargs):
        "Clarifying alias for addLink"
        self.addLink(*args, **kwargs)


SpanSpec = namedtuple('SpanSpec', 'length amp')
AmpSpec = namedtuple('AmpSpec', 'name params ')


def spanSpec(length, amp, targetGain):
    "Return span specifier [length, (amp, params)]"
    return SpanSpec(length, AmpSpec(amp, dict(target_gain=targetGain)))


class LinearRoadmTopo(OpticalTopo):
    """A linear network with a single ROADM and three POPs

       h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3
                             ||
                             t2 - s2 - h2
       h1-h3: hosts
       s1-s3: routers (downlink: eth0, uplink: eth1, eth2)
       t1-t3: terminals (downlink: eth1, eth2, uplink: wdm3, wdm4)
       r1-r3: ROADMs (add/drop: wdm1, wdm2, line: wdm3, wdm4)"""

    @staticmethod
    def ip(pop, intfnum=0, template='10.%d.0.%d', subnet='/24'):
        "Return a local IP address or subnet for the given POP"
        return template % (pop, intfnum) + subnet

    def buildPop(self, p, txCount=2):
        "Build a POP; returns: ROADM"
        # Network elements
        hostname, hostip, subnet = 'h%d' % p, self.ip(p, 1), self.ip(p, 0)
        host = self.addHost(hostname, ip=hostip,
                            defaultRoute='dev ' + hostname + '-eth0')
        router = self.addSwitch('s%d' % p, subnet=subnet,
                                listenPort=(ListenPortBase + p))
        transceivers = [
            ('t%d' % t, 0 * dBm, 'C') for t in range(1, txCount + 1)]
        terminal = self.addSwitch(
            't%d' % p, cls=Terminal, transceivers=transceivers)
        roadm = self.addSwitch('r%d' % p, cls=ROADM)
        # Local links
        for port in range(1, txCount + 1):
            self.ethLink(router, terminal, port1=port, port2=port)
        self.ethLink(router, host, port1=txCount + 1)
        for port in range(1, txCount + 1):
            self.wdmLink(terminal, roadm, port1=txCount + port, port2=port)
        # Return ROADM so we can link it to other POPs as needed
        return roadm

    @staticmethod
    def spans(spanLength=50 * km, spanCount=4):
        """Return a list of span specifiers (length, (amp, params))
           the compensation amplifiers are named prefix-ampN"""
        entries = [spanSpec(length=spanLength, amp='amp%d' % i,
                            targetGain=spanLength / km * .22 * dB)
                   for i in range(1, spanCount + 1)]
        return sum([list(entry) for entry in entries], [])

    def build(self, n=5, txCount=2):
        "Add POPs and connect them in a line"
        roadms = [self.buildPop(p, txCount) for p in range(1, n + 1)]

        # Inter-POP links
        for i in range(0, n - 1):
            src, dst = roadms[i], roadms[i + 1]
            boost = ('boost', dict(target_gain=17.0 * dB))
            spans = self.spans(spanLength=80 * km, spanCount=3)
            # XXX Unfortunately we currently have to have a priori knowledge of
            # this prefix
            prefix1, prefix2 = '%s-%s-' % (src, dst), '%s-%s-' % (dst, src)
            firstAmpName, lastAmpName = spans[1].name, spans[-1].name
            monitors = [(prefix1 + lastAmpName + '-monitor', prefix1 + lastAmpName),
                        (prefix2 + firstAmpName + '-monitor', prefix2 + firstAmpName)]
            self.wdmLink(src, dst, boost=boost, spans=spans,
                         monitors=monitors)


def configureLinearNet(net, channel_no=10):
    """Configure linear network locally
       Channel usage:
       r1<->r5: 1-10
    """

    info('*** Configuring linear network \n')

    # Configure routers
    # eth1: dest1, eth2: dest2, etc. ... ethN: local
    routers = s1, s5 = net.get('s1', 's5')
    for pop, dests in enumerate([(s1, s5)], start=1):
        router, dest1, dest2 = routers[pop - 1], dests[0], dests[1]
        # XXX Only one host for now
        hostmac = net.get('h%d' % pop).MAC()
        router.dpctl('del-flows')
        for eth, dest in enumerate([dest1, dest2, router], start=1):
            dstmod = ('mod_dl_dst=%s,' % hostmac) if dest == router else ''
            for protocol in 'ip', 'icmp', 'arp':
                flow = (protocol + ',ip_dst=' + dest.params['subnet'] +
                        'actions=' + dstmod +
                        'dec_ttl,output:%d' % eth)
                router.dpctl('add-flow', flow)

    channels = list(np.arange(1, channel_no + 1))
    # Port numbering
    eth_ports = list(np.arange(1, channel_no + 2))
    wdm_ports = list(np.arange(1, channel_no + 2))

    # Configure transceivers
    t1 = net.get('t1')
    for tx_id, ch in enumerate(channels):
        t1.connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[-1], channel=ch)

    # Configure roadms
    r1, r2, r3, r4, r5 = net.get('r1', 'r2', 'r3', 'r4', 'r5')
    line1, line2 = 11, 12

    # r1: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        r1.connect(port1=local_port, port2=line1, channels=[ch])

    # r2: pass through channels r1<->r5
    r2.connect(port1=line1, port2=line2, channels=channels)

    # r3: pass through channels r1<->r5
    r3.connect(port1=line1, port2=line2, channels=channels)

    # r4: pass through channels r1<->r5
    r4.connect(port1=line1, port2=line2, channels=channels)

    # r5: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        r5.connect(port1=line1, port2=local_port, channels=[ch])


if __name__ == '__main__':
    # Test our demo topology
    cleanup()
    setLogLevel('info')
    topo1 = LinearRoadmTopo(n=5, txCount=10)
    # topo2 = LinearRoadmTopo(n=15, txCount=9)
    net = Mininet(topo=topo1, autoSetMacs=True,
                  controller=RemoteController)
    disableIPv6(net)
    restServer = RestServer(net)
    net.start()
    configureLinearNet(net)
    restServer.start()
    CLI(net)
    restServer.stop()
    net.stop()

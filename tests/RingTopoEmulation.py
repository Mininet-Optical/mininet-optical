from dataplane import (Terminal, ROADM, OpticalLink,
                       dBm, dB, km,
                       disableIPv6, Mininet)
from node import Transceiver
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


class RingTopo(OpticalTopo):
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
        roadm = self.addSwitch('r%d' % p, cls=ROADM)

        # create the labels for the transceivers
        tr_labels = ['tr%s' % str(x + 1) for x in range(txCount)]
        # create as many transceivers as labels
        transceivers = [Transceiver(id, tr, operation_power=-2) for id, tr in enumerate(tr_labels, start=1)]
        # create a terminal with the transceivers
        terminal = self.addSwitch('t%d' % p, cls=Terminal, transceivers=transceivers)

        # Terminal <--> Router Link
        # This is NOT a Transceiver connection, the port
        # numbering refers to a physical port identifier,
        # but the link will be an ethLink, thus no need
        # for transceivers.
        eth_ports = [101, 102]
        for eth_port in eth_ports:
            self.ethLink(terminal, router, port1=eth_port, port2=eth_port)

        # Router <--> Host Link
        # AD: Which port should this be? 0?
        self.ethLink(router, host, port1=0)

        # Modelling Lumentum ROADM-20 port numbering
        roadm20_in_ports = [i + 1 for i in range(4100, 4120)]
        roadm20_out_ports = [i + 1 for i in range(5200, 5220)]
        # Terminals <--> ROADMs
        for i, tr in enumerate(transceivers):
            roadm20_in_port = roadm20_in_ports[i]
            self.wdmLink(terminal, roadm, port1=tr.id, port2=roadm20_in_port)

            # AD: We want to be able to do this! Enabling uni-directional links.
            # roadm20_out_port = roadm20_out_ports[i]
            # self.wdmLink(roadm, terminal, port1=roadm20_out_port, port2=tr.id)

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

        for i, roadm in enumerate(roadms):
            if i == len(roadms) - 1:
                src, dst = roadm, roadms[0]
            else:
                src, dst = roadm, roadms[i + 1]
            print("*** RingTopo: creating link for ROADMs", src, dst)

            boost = ('boost', dict(target_gain=17.0 * dB, boost=True))
            spans = self.spans(spanLength=80 * km, spanCount=3)
            # XXX Unfortunately we currently have to have a priori knowledge of
            # this prefix
            prefix1, prefix2 = '%s-%s-' % (src, dst), '%s-%s-' % (dst, src)
            monitors = [(prefix1 + 'boost' + '-monitor', prefix1 + 'boost')]
            for j in np.arange(1, len(spans), 2):
                amp_name = spans[j].name
                monitors.append((prefix1 + amp_name + '-monitor', prefix1 + amp_name))
                amp_name2 = spans[j].name
                monitors.append((prefix2 + amp_name2 + '-monitor', prefix2 + amp_name2))
            monitors.append((prefix2 + 'boost' + '-monitor', prefix2 + 'boost'))
            self.wdmLink(src, dst, boost=boost, spans=spans,
                         monitors=monitors)
            print("*** RingTopo: OK")


if __name__ == '__main__':
    # Test our demo topology
    cleanup()
    setLogLevel('info')
    topo1 = RingTopo(n=3, txCount=2)
    net = Mininet(topo=topo1, autoSetMacs=True,
                  controller=RemoteController)
    disableIPv6(net)
    restServer = RestServer(net)
    net.start()
    restServer.start()
    CLI(net)
    restServer.stop()
    net.stop()
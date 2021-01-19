from dataplane import (Terminal, ROADM, OpticalLink,
                       dBm, dB, km,
                       disableIPv6, Mininet)
from rest import RestServer

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController

from collections import namedtuple

from ofcdemo.demolib import OpticalCLI

# Routers start listening at 6654
ListenPortBase = 6653

CLI = OpticalCLI


class OpticalTopo(Topo):
    """Topo with convenience methods for optical links"""

    def wdmLink(self, *args, **kwargs):
        """Convenience function to add an OpticalLink"""
        kwargs.update(cls=OpticalLink)
        self.addLink(*args, **kwargs)

    def ethLink(self, *args, **kwargs):
        """Clarifying alias for addLink"""
        self.addLink(*args, **kwargs)


SpanSpec = namedtuple('SpanSpec', 'length amp')
AmpSpec = namedtuple('AmpSpec', 'name params ')


def spanSpec(length, amp, **ampParams):
    """Return span specifier [length, (ampName, params)]"""
    ampSpec = AmpSpec(amp, ampParams)
    return SpanSpec(length, ampSpec)


class Cost239Topo(OpticalTopo):
    """Cost239 Network Topology"""

    @staticmethod
    def ip(pop, intfnum=0, template='10.%d.0.%d', subnet='/24'):
        """Return a local IP address or subnet for the given POP"""
        return template % (pop, intfnum) + subnet

    def build_pop(self, city_count, city_name, txCount=2):
        city_names = ['berlin', 'copenhagen', 'london', 'paris', 'prague', 'vienna']

        """Build a POP; returns: ROADM"""
        # Network elements
        hostname, hostip, subnet = 'h%d' % city_count, self.ip(city_count, 1), self.ip(city_count, 0)
        host = self.addHost(hostname, ip=hostip,
                            defaultRoute='dev ' + hostname + '-eth0')
        router = self.addSwitch('s%d' % city_count, subnet=subnet,
                                listenPort=(ListenPortBase + city_count))
        if city_name in city_names:
            transceivers = [
                ('t%d' % t, 0 * dBm, 'C') for t in range(1, txCount + 1)]
        else:
            transceivers = [('t2', 0 * dBm, 'C')]
        terminal = self.addSwitch(
            't%d' % city_count, cls=Terminal, transceivers=transceivers)
        roadm = self.addSwitch('r%d' % city_count, cls=ROADM)
        # Local links
        if city_name in city_names:
            for port in range(1, txCount + 1):
                self.ethLink(router, terminal, port1=port, port2=port)
            self.ethLink(router, host, port1=txCount + 1)
            for port in range(1, txCount + 1):
                self.wdmLink(terminal, roadm, port1=txCount + port, port2=port)
        else:
            for port in range(1, 2):
                self.ethLink(router, terminal, port1=port, port2=port)
            self.ethLink(router, host, port1=1 + 1)
            for port in range(1, 2):
                self.wdmLink(terminal, roadm, port1=1 + port, port2=port)

        # Return ROADM so we can link it to other POPs as needed
        return roadm

    @staticmethod
    def build_spans(total_len):
        """
        Helper function for building spans of
        fixed length of 50km and handling those
        that require different lengths
        """
        # extra span for residual
        extra_span = None
        # store all spans (sequentially) in a list
        spans = []
        # get number of spans (int)
        span_no = int(total_len / 50)
        # get a residual length if not fixed
        res_len = total_len - 50 * span_no

        last_span = 50
        if res_len > 20:
            # if exceeding 20 km, save
            # as an extra span
            extra_span = res_len
        else:
            # otherwise, add to the last span
            last_span += res_len

        c = 0
        for i in range(1, span_no):
            # append all spans except last one
            spanSpec(length=50.0, amp='amp%d' % i,
                     target_gain=50.0 / km * .22 * dB,
                     monitor_mode='out')
            spans.append(spanSpec(length=50.0, amp='amp%d' % i,
                                  target_gain=50.0 / km * .22 * dB,
                                  monitor_mode='out'))
            c = i + 1
        # append last span (length might have changed)
        spans.append(spanSpec(length=last_span, amp='amp%d' % c,
                              target_gain=last_span / km * .22 * dB,
                              monitor_mode='out'))
        c += 1

        if extra_span:
            # add an extra span (if needed)
            spans.append(spanSpec(length=extra_span, amp='amp%d' % c,
                                  target_gain=extra_span / km * .22 * dB,
                                  monitor_mode='out'))

        return sum([list(span) for span in spans], [])

    def build_pop_link(self, r1, r2, total_len):
        boost = ('boost', dict(target_gain=17.0, boost=True, monitor_mode='out'))
        spans = self.build_spans(total_len)
        self.wdmLink(r1, r2, boost=boost, spans=spans)

    def build(self, txCount=2):
        city_names = ['amsterdam', 'berlin', 'brussels', 'copenhagen', 'london',
                      'luxembourg', 'milan', 'paris', 'prague', 'vienna', 'zurich']
        "Add POPs and connect them in a line"
        roadms = [self.build_pop(city_count, city_name, txCount) for
                  city_count, city_name in enumerate(city_names, start=1)]

        city_name_to_roadm = {}
        for city_name, roadm in zip(city_names, roadms):
            city_name_to_roadm[city_name] = roadm
        cntr = city_name_to_roadm

        # Main Amsterdam bi-links
        self.build_pop_link(cntr['amsterdam'], cntr['london'], 390)
        self.build_pop_link(cntr['amsterdam'], cntr['brussels'], 200)
        self.build_pop_link(cntr['amsterdam'], cntr['luxembourg'], 310)
        self.build_pop_link(cntr['amsterdam'], cntr['berlin'], 600)
        self.build_pop_link(cntr['amsterdam'], cntr['copenhagen'], 750)

        # Main Berlin bi-links
        self.build_pop_link(cntr['berlin'], cntr['copenhagen'], 400)
        self.build_pop_link(cntr['berlin'], cntr['paris'], 900)
        self.build_pop_link(cntr['berlin'], cntr['prague'], 320)
        self.build_pop_link(cntr['berlin'], cntr['vienna'], 710)

        # Main Brussels bi-links
        self.build_pop_link(cntr['brussels'], cntr['london'], 340)
        self.build_pop_link(cntr['brussels'], cntr['paris'], 270)
        self.build_pop_link(cntr['brussels'], cntr['milan'], 850)
        self.build_pop_link(cntr['brussels'], cntr['luxembourg'], 100)

        # Main Copenhagen bi-links
        self.build_pop_link(cntr['copenhagen'], cntr['london'], 1000)
        self.build_pop_link(cntr['copenhagen'], cntr['prague'], 760)

        # Main London bi-links
        self.build_pop_link(cntr['london'], cntr['paris'], 410)

        # Main Luxembourg bi-links
        self.build_pop_link(cntr['luxembourg'], cntr['paris'], 370)
        self.build_pop_link(cntr['luxembourg'], cntr['zurich'], 440)
        self.build_pop_link(cntr['luxembourg'], cntr['prague'], 900)

        # Main Milan bi-links
        self.build_pop_link(cntr['milan'], cntr['paris'], 810)
        self.build_pop_link(cntr['milan'], cntr['zurich'], 100)
        self.build_pop_link(cntr['milan'], cntr['vienna'], 720)

        # Main Paris bi-links
        self.build_pop_link(cntr['paris'], cntr['zurich'], 590)

        # Main Prague bi-links
        self.build_pop_link(cntr['prague'], cntr['zurich'], 100)
        self.build_pop_link(cntr['prague'], cntr['vienna'], 350)

        # Main Vienna bi-links
        self.build_pop_link(cntr['vienna'], cntr['zurich'], 710)


if __name__ == '__main__':
    # Test our demo topology
    cleanup()
    setLogLevel('info')
    net = Mininet(topo=Cost239Topo(txCount=2), autoSetMacs=True,
                      controller=RemoteController)
    disableIPv6(net)
    restServer = RestServer(net)
    net.start()
    print("The restServer at emulation_demolib with the network will start now!")
    restServer.start()
    print("The restServer at emulation_demolib with the network started (as I said)!")
    CLI(net)
    restServer.stop()
    net.stop()

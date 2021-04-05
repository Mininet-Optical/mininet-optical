from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy,
                                    OFSwitchProxy, TerminalProxy,
                                    fetchNodes)
import network
from link import Span as Fiber, SpanTuple as Segment
from node import Transceiver


km = dB = dBm = 1.0
m = .001


def Span(km, amp=None):
    """Return a fiber segment of length km with a compensating amp"""
    return Segment(span=Fiber(length=km), amplifier=amp)


def build_spans(net, r1, r2):
    """
    Helper function for building spans of
    fixed length of 50km and handling those
    that require different lengths
    """
    # store all spans (sequentially) in a list
    spans = []
    # get number of spans (int)
    span_no = 1
    span_length = 80

    for i in range(1, span_no + 1):
        # append all spans except last one
        amp = net.add_amplifier(
            '%s-%s-amp%d' % (r1, r2, i), target_gain=span_length * 0.22 * dB, monitor_mode='out')
        span = Span(span_length, amp=amp)
        spans.append(span)

    return net, spans


def build_link(net, r1, r2, gain=17.00022):
    # boost amplifier object
    boost_l = '%s-%s-boost' % (r1, r2)  # label boost amp
    boost_amp = net.add_amplifier(name=boost_l, amplifier_type='EDFA', target_gain=float(gain), boost=True, monitor_mode='out')

    net, spans = build_spans(net, r1, r2)
    for step, span in enumerate(spans, start=1):
        net.spans.append(span)

    # link object
    net.add_link(r1, r2, boost_amp=boost_amp, spans=spans)


def install_paths(nodes, channels, line_terminals):
    for i, node in enumerate(nodes):
        if i == len(nodes) - 1:
            return
        out_port = net.find_link_and_out_port_from_nodes(node, nodes[i + 1])
        if i == 0:
            src_node = line_terminals[i]
            for c in channels:
                node.install_switch_rule(1, c, out_port, [c], src_node=src_node)
        else:
            in_port = net.find_link_and_in_port_from_nodes(nodes[i - 1], node)
            node.install_switch_rule(1, in_port, out_port, channels, src_node=nodes[i - 1])


class OpticalTopo(Topo):
    "Topo with convenience methods for optical links"

    def wdmLink(self, *args, **kwargs):
        "Convenience function to add an OpticalLink"
        kwargs.update(cls=OpticalLink)
        self.addLink(*args, **kwargs)

    def ethLink(self, *args, **kwargs):
        "Clarifying alias for addLink"
        self.addLink(*args, **kwargs)

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

        tx_labels = ['tx%s' % str(x + 1) for x in range(txCount)]
        rx_labels = ['rx%s' % str(x + 1) for x in range(txCount)]
        tx_transceivers = [Transceiver(id, tr, operation_power=p, type='tx')
                           for id, tr in enumerate(tx_labels, start=1)]
        rx_transceivers = [Transceiver(id, tr, operation_power=p, type='rx')
                           for id, tr in enumerate(rx_labels, start=1)]
        transceivers = tx_transceivers + rx_transceivers
        terminal = self.addSwitch(
            't%d' % p, cls=Terminal, transceivers=transceivers)

        roadm = self.addSwitch('r%d' % p, cls=ROADM)
        # Local links
        for port in range(1, txCount + 1):
            self.ethLink(router, terminal, port1=port, port2=port)
        self.ethLink(router, host, port1=txCount + 1)

        for lt, roadm in zip(line_terminals, roadms):
            for tx in tx_transceivers:
                net.add_link(lt, roadm, src_out_port=tx.id, dst_in_port=tx.id, spans=[Span(1 * m)])
            for rx in rx_transceivers:
                net.add_link(roadm, lt, src_out_port=rx.id, dst_in_port=rx.id, spans=[Span(1 * m)])

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
            boost = ('boost', dict(target_gain=17.0 * dB, boost=True))
            spans = self.spans(spanLength=80 * km, spanCount=6)
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


net = network.Network()
# Create line terminals
operational_power = 0  # power in dBm

# Create bi-directional links between LTs and ROADMs
for lt, roadm in zip(line_terminals, roadms):
    for tx in tx_transceivers:
        net.add_link(lt, roadm, src_out_port=tx.id, dst_in_port=tx.id, spans=[Span(1 * m)])
    for rx in rx_transceivers:
        net.add_link(roadm, lt, src_out_port=rx.id, dst_in_port=rx.id, spans=[Span(1 * m)])


# Build links between ROADMs
for i, roadm in enumerate(roadms):
    if i == len(roadms) - 1:
        build_link(net, roadm, roadms[0])
    else:
        build_link(net, roadm, roadms[i + 1])

ch_no = 1
channels = range(1, ch_no + 1)
channels = [1]
for i, (r, lt_tx) in enumerate(zip(roadms, line_terminals)):
    if i == 0:
        lt_rx = line_terminals[-1]
    else:
        lt_rx = line_terminals[i - 1]

    # configure line terminal
    for c in channels:
        tx_transceiver = lt_tx.tx_transceivers[c]
        lt_tx.assoc_tx_to_channel(tx_transceiver, c, c)

        rx_transceiver = lt_rx.rx_transceivers[c]
        lt_rx.assoc_rx_to_channel(rx_transceiver, c)

    # build paths from r_i to r_n
    path = [r] + roadms[i + 1:]
    if len(path) < len(roadms):
        path += roadms[:i]
    path.append(lt_rx)

    # install switch rules into the ROADMs
    install_paths(path, channels, line_terminals)

    print("*** Turning on:", lt_tx)
    lt_tx.turn_on()

    ch = channels[0]
    ch += 1
    channels[0] = ch
    # channels = range(ch_no + 1, ch_no + ch_no + 1)
    # ch_no += ch_no

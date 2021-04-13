import network
from link import Span as Fiber, SpanTuple as Segment
import numpy as np
from node import Transceiver


km = dB = dBm = 1.0
m = .001

counter = 0


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
    span_no = 3
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


class LinearTopology:

    @staticmethod
    def build(op=0, non=3):
        """
        :param op: operational power in dBm
        :param non: number of nodes (integer)
        :return: Network object
        """
        # Create an optical-network object
        net = network.Network()

        operational_power = 0
        tr_no = range(1, 11)
        tr_labels = ['tr%s' % str(x) for x in tr_no]
        line_terminals = []
        for i in range(non):
            # plugging a Transceiver at the first 10 ports of the Terminal
            transceivers = [Transceiver(id, tr, operation_power=operational_power)
                            for id, tr in enumerate(tr_labels, start=1)]
            lt = net.add_lt('lt_%s' % (i + 1), transceivers=transceivers)
            line_terminals.append(lt)

        roadms = [net.add_roadm('r%s' % (i + 1)) for i in range(non)]
        name_to_roadm = {roadm.name: roadm for roadm in roadms}

        # Modelling Lumentum ROADM-20 port numbering
        roadm20_in_ports = [i + 1 for i in range(4100, 4120)]
        roadm20_out_ports = [i + 1 for i in range(5200, 5220)]
        # Create bi-directional links between LTs and ROADMs
        # Need to decide which ports are connected to the ROADM
        # Port-1 from Terminals are connected to Port-4101 from ROADMs.
        for lt, roadm in zip(line_terminals, roadms):
            for i, tr in enumerate(transceivers):
                roadm20_in_port = roadm20_in_ports[i]
                net.add_link(lt, roadm, src_out_port=tr.id, dst_in_port=roadm20_in_port, spans=[Span(0 * m)])

                roadm20_out_port = roadm20_out_ports[i]
                net.add_link(roadm, lt, src_out_port=roadm20_out_port, dst_in_port=tr.id, spans=[Span(0 * m)])

        tmp = 0
        for i in range(non-1):
            # Iterate through the number of nodes linearly connected
            r1 = name_to_roadm['r' + str(i + 1)]  # init node
            r2 = name_to_roadm['r' + str(i + 2)]  # next node
            if tmp == 0:
                build_link(net, r1, r2, gain=17.0)
                tmp += 1
            else:
                build_link(net, r1, r2, gain=17.0)

        return net

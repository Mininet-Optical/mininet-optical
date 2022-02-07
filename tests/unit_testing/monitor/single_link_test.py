#!/usr/bin/python

"""
single_link_test.py: test monitoring on a single link
"""

import mnoptical.network as network
from mnoptical.link import Span as Fiber, SpanTuple as Segment
from mnoptical.node import Transceiver


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
    span_no = 3
    span_length = 80

    for i in range(1, span_no + 1):
        # append all spans except last one
        amp = net.add_amplifier(
            '%s-%s-amp%d' % (r1, r2, i), target_gain=span_length * 0.22 * dB, monitor_mode='out')
        span = Span(span_length, amp=amp)
        spans.append(span)

    return net, spans


def build_link(net, r1, r2, gain=17.0):
    # boost amplifier object
    boost_l = '%s-%s-boost' % (r1, r2)  # label boost amp
    boost_amp = net.add_amplifier(name=boost_l, amplifier_type='EDFA',
                                  target_gain=float(gain), boost=True, monitor_mode='out')

    net, spans = build_spans(net, r1, r2)
    for step, span in enumerate(spans, start=1):
        net.spans.append(span)

    # link object
    net.add_link(r1, r2, boost_amp=boost_amp, spans=spans)

def singleLinkPhyNetwork( lengths=[50*km] ):
    "Link two hosts via a series of fiber spans and amplifiers"
    net = network.Network()

    operational_power = -2  # power in dBm
    # Endpoints
    transceivers = [ Transceiver(1, 'tr1', operation_power=operational_power) ]
    terminals = tx1, tx2 = [ net.add_lt( 'tx%d' % i, transceivers=transceivers )
                             for i in ( 1, 2  ) ]

    roadm_linear_loss = 17
    roadms = [net.add_roadm('r%s' % (i + 1),
                        target_output_power_dB=operational_power - roadm_linear_loss,
                        effective_output_power_dB=operational_power,
                        reference_power=operational_power) for i in range(2)]

    # Modelling Lumentum ROADM-20 port numbering
    roadm20_in_ports = [i + 1 for i in range(4100, 4120)]
    roadm20_out_ports = [i + 1 for i in range(5200, 5220)]

    # Create bi-directional links between LTs and ROADMs
    for lt, roadm in zip(terminals, roadms):
        for i, tr in enumerate(transceivers):
            roadm20_in_port = roadm20_in_ports[i]
            net.add_link(lt, roadm, src_out_port=tr.id, dst_in_port=roadm20_in_port, spans=[Span(0 * m)])

            roadm20_out_port = roadm20_out_ports[i]
            net.add_link(roadm, lt, src_out_port=roadm20_out_port, dst_in_port=tr.id, spans=[Span(0 * m)])

    lt1 = net.name_to_node['tx1']
    lt2 = net.name_to_node['tx2']

    r1 = net.name_to_node['r1']
    r2 = net.name_to_node['r2']

    build_link(net, r1, r2)

    # Print network elements

    print("*** Terminals:", net.line_terminals)
    print("*** Links:", net.links)
    print("*** Amplifiers:", net.amplifiers)
    print("*** Ports:", tx1.ports_out, tx2.ports_in)

    return net


# Support functions

def formatSignals( signalPowers ):
    "Nice format for signal powers"
    return '\n'.join(
        '%s %.2f dBm' % ( channel, signalPowers[ channel ] )
        for channel in sorted( signalPowers ) )


def dumpLinkPower(link):
    "Print out power for all spans in a Link"
    for span, amp in link.spans:
        print( 'span:', span )
        if amp:
            print('amp:', amp, 'input', formatSignals(amp.input_power),
                  'output', formatSignals(amp.output_power) )


# Physical model test


def singleLinkPhyTest():
    "Create a single link and monitor its OSNR and gOSNR"
    net = singleLinkPhyNetwork( lengths=[25*km, 50*km, 25*km] )
    node = net.name_to_node

    r1, r2 = node['r1'], node['r2']
    tx1, tx2 = node['tx1'], node['tx2']
    channels = [1]

    print('*** Configure ROADMs')
    in_port_lt = 4101
    out_port = 5202
    r1.install_switch_rule(in_port_lt, out_port, channels, src_node=tx1)

    in_port = 4102
    out_port = 5201
    r2.install_switch_rule(in_port, out_port, channels, src_node=r2)

    print( '*** Starting test transmission...' )
    tx1.assoc_tx_to_channel(tx1.id_to_transceivers[1], 1, out_port=1)
    tx2.assoc_rx_to_channel(tx2.id_to_transceivers[1], 1)
    tx1.turn_on()

    print( '*** Initial OSNR and gOSNR:' )
    for amp in net.amplifiers:
        print(amp.monitor.name, 'OSNR', amp.monitor.get_list_osnr())
        print(amp.monitor.name, 'gOSNR', amp.monitor.get_list_gosnr())


if __name__ == '__main__':

    singleLinkPhyTest()
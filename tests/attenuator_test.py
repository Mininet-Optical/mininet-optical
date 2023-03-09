from mnoptical.units import *
from mnoptical.link import Span as FiberSpan
import sys
import mnoptical.network as network
from mnoptical.link import Span as Fiber, SpanTuple as Segment
import numpy as np
from mnoptical.node import Transceiver, Attenuator

km = dB = dBm = 1.0
m = .001

def Span(km, amp=None):
    """Return a fiber segment of length km with a compensating amp"""
    return Segment(span=Fiber(length=km), amplifier=amp)

attenuators = attenuator1, attenuator2, attenuator3 = Attenuator('attn1', loss=1, monitor='out'), Attenuator('attn2', loss=2, monitor='out'), Attenuator('attn3', loss=1, monitor='out')

def build_spans(net, r1, r2):

    spans = []
    spans.append(Span(10, amp=net.add_amplifier('amp1', target_gain=18.0, monitor_mode='out')))
    spans.append(Span(0, amp=attenuator1))
    spans.append(Span(20, amp=net.add_amplifier('amp2', target_gain=18.0, monitor_mode='out')))
    spans.append(Span(0, amp=attenuator2))
    spans.append(Span(1.0*m, amp=attenuator3))
    spans.append(Span(10, amp=net.add_amplifier('amp3', target_gain=18.0, monitor_mode='out')))
    
    return net, spans

def build_link(net, r1, r2):
    net, spans = build_spans(net, r1, r2)
    for step, span in enumerate(spans, start=1):
        net.spans.append(span)

    # link object
    net.add_link(r1, r2, spans=spans, srs_model=None)

class LinearTopology:

    @staticmethod
    def build(op=0, bidirectional=False):

        net = network.Network()
        tr_no = range(1, 4)
        tr_labels = ['tr%s' % str(x) for x in tr_no]
        line_terminals = []

        transceivers = [Transceiver(id, tr, operation_power=op)
                        for id, tr in enumerate(tr_labels, start=1)]
        lt1 = net.add_lt('lt_1', transceivers=transceivers, monitor_mode='out')
        line_terminals.append(lt1)

        lt2 = net.add_lt('lt_2', transceivers=transceivers, monitor_mode='in')
        line_terminals.append(lt2)

        roadms = r1, r2 = [net.add_roadm('r1', insertion_loss_dB=17, reference_power_dBm=op, monitor_mode='out'),
        net.add_roadm('r2', insertion_loss_dB=17, reference_power_dBm=op, monitor_mode='in')]
        name_to_roadm = {roadm.name: roadm for roadm in roadms}

        # Modelling Lumentum ROADM-20 port numbering
        roadm20_in_ports = [i + 1 for i in range(4100, 4120)]
        roadm20_out_ports = [i + 1 for i in range(5200, 5220)]

        for lt, roadm in zip(line_terminals, roadms):
            for i, tr in enumerate(transceivers):
                roadm20_in_port = roadm20_in_ports[i]
                net.add_link(lt, roadm, src_out_port=tr.id, 
                    dst_in_port=roadm20_in_port, spans=[Span(0 * m)])

                roadm20_out_port = roadm20_out_ports[i]
                net.add_link(roadm, lt, src_out_port=roadm20_out_port, 
                    dst_in_port=tr.id, spans=[Span(0 * m)])

        build_link(net, r1, r2)
        if bidirectional:
            build_link(net, r2, r1)

        return net


def test():
    "Verify that the Attenuator works as expected"

    num_wavelengths = 3
    channel_indexes = list(range(1, num_wavelengths + 1))

    print("*** Building Linear network topology for operational power: 2dB")

    net = LinearTopology.build(op=2, bidirectional=False)
    lt_1 = net.name_to_node['lt_1']
    lt_2 = net.name_to_node['lt_2']
    roadm1 = net.name_to_node['r1']
    roadm2 = net.name_to_node['r2']

    for c in channel_indexes:

        # configure transmitter terminal
        tx_transceiver = lt_1.id_to_transceivers[c]
        lt_1.assoc_tx_to_channel(tx_transceiver, c, out_port=c)

        # configure receiver terminal
        rx_transceiver = lt_2.id_to_transceivers[c]
        lt_2.assoc_rx_to_channel(rx_transceiver, c, in_port=c)

    out_port = net.find_link_and_out_port_from_nodes(roadm1, roadm2)
    for channel in channel_indexes:
        in_port = 4100 + channel
        roadm1.install_switch_rule(in_port, out_port, [channel])
    in_port = net.find_link_and_in_port_from_nodes(roadm1, roadm2)
    for channel in channel_indexes:
        out_port = 5200 + channel
        roadm2.install_switch_rule(in_port, out_port, [channel])

    lt_1.turn_on()

    # Getting Power levels from amplifiers and attenuators.

    def get_power_levels(monitor):
        power_levels = {}
        power_levels['total_power'] = abs_to_db(np.mean(list(monitor.get_dict_power().values())))
        power_levels['ase_power'] = abs_to_db(np.mean(list(monitor.get_dict_ase_noise().values())))
        power_levels['nli_power'] = abs_to_db(np.mean(list(monitor.get_dict_nli_noise().values())))
        
        return power_levels

    def power_diff(comp1, comp2):

        monitor1 = comp1.monitor
        monitor2 = comp2.monitor

        monitor1.modify_mode("out")
        monitor2.modify_mode("out")

        input_power = get_power_levels(monitor1)
        output_power = get_power_levels(monitor2)

        total_power_diff = round(input_power['total_power'] - output_power['total_power'], 3)
        ase_power_diff = round(input_power['ase_power'] - output_power['ase_power'],3)
        nli_power_diff = round(input_power['nli_power'] - output_power['nli_power'],3)

        print("Total Power Loss(dB): ", total_power_diff)
        print("ASE Noise Power Loss(dB): ", ase_power_diff)
        print("NLI Noise Power Loss(dB): ", nli_power_diff, "\n")

        return [total_power_diff, ase_power_diff, nli_power_diff]

    amp1, amp2, amp3 = [i for i in net.amplifiers[:3]]

    print("Power Loss across Attn1(loss=1dB)")
    power_difference = power_diff(amp1, attenuator1)
    attn1_loss = round(abs_to_db(attenuator1.attenuation_power),3)
    # Checking against attenuation power of Attn1
    for i in range(3):
        assert (power_difference[i] - attn1_loss) == 0

    print("Power Loss in Attn2(loss=2dB)")
    power_difference = power_diff(amp2, attenuator2)
    attn2_loss = round(abs_to_db(attenuator2.attenuation_power),3)
    # Checking against attenuation power of Attn2
    for i in range(3):
        assert (power_difference[i] - attn2_loss) == 0

    print("Power Loss in Attn3(loss=1dB)")
    power_difference = power_diff(attenuator2, attenuator3)
    attn3_loss = round(abs_to_db(attenuator3.attenuation_power),3)
    # Checking against attenuation power of Attn3
    for i in range(3):
        assert (power_difference[i] - attn3_loss) == 0

    print("Power Loss in Attn2(loss=2dB) + Attn3(loss=1dB)")
    power_difference = power_diff(amp2, attenuator3)
    attn2_attn3_loss = attn2_loss + attn3_loss
    # Checking against combined attenuation power of Attn2 and Attn3
    for i in range(3):
        assert (power_difference[i] - attn2_attn3_loss) == 0

if __name__ == '__main__':
    result = test()
    exit(result)


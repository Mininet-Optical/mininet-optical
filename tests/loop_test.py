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


net = network.Network()
# Create line terminals
operational_power = 0  # power in dBm
non = 3  # number of nodes
tr_no = range(1, 11)
tx_labels = ['tx%s' % str(x) for x in tr_no]
rx_labels = ['rx%s' % str(x) for x in tr_no]

line_terminals = []
for i in range(non):
    tx_transceivers = [Transceiver(id, tr, operation_power=operational_power, type='tx')
                       for id, tr in enumerate(tx_labels, start=1)]
    rx_transceivers = [Transceiver(id, tr, operation_power=operational_power, type='rx')
                       for id, tr in enumerate(rx_labels, start=1)]
    transceivers = tx_transceivers + rx_transceivers
    lt = net.add_lt('lt_%s' % (i + 1), transceivers=transceivers)
    line_terminals.append(lt)

roadms = [net.add_roadm('r%s' % (i + 1)) for i in range(non)]

# Create bi-directional links between LTs and ROADMs
for lt, roadm in zip(line_terminals, roadms):
    for tx in tx_transceivers:
        net.add_link(lt, roadm, src_out_port=tx.id, dst_in_port=tx.id, spans=[Span(1 * m)])
    for rx in rx_transceivers:
        net.add_link(roadm, lt, src_out_port=rx.id, dst_in_port=rx.id, spans=[Span(1 * m)])

lt1 = net.name_to_node['lt_1']
lt2 = net.name_to_node['lt_2']
lt3 = net.name_to_node['lt_3']

r1 = net.name_to_node['r1']
r2 = net.name_to_node['r2']
r3 = net.name_to_node['r3']

build_link(net, r1, r2)
build_link(net, r2, r3)
build_link(net, r3, r1)

in_port_lt = 1
out_port = net.find_link_and_out_port_from_nodes(r1, r2)
r1.install_switch_rule(1, in_port_lt, out_port, [1], src_node=lt1)

in_port = net.find_link_and_in_port_from_nodes(r1, r2)
out_port = net.find_link_and_out_port_from_nodes(r2, r3)
r2.install_switch_rule(1, in_port, out_port, [1], src_node=r1)

in_port = net.find_link_and_in_port_from_nodes(r2, r3)
out_port = net.find_link_and_out_port_from_nodes(r3, lt3)
r3.install_switch_rule(1, in_port, out_port, [1], src_node=r2)


in_port_lt = 2
out_port = net.find_link_and_out_port_from_nodes(r2, r3)
r2.install_switch_rule(1, in_port_lt, out_port, [2], src_node=lt2)

in_port = net.find_link_and_in_port_from_nodes(r2, r3)
out_port = net.find_link_and_out_port_from_nodes(r3, r1)
r3.install_switch_rule(1, in_port, out_port, [2], src_node=r2)

in_port = net.find_link_and_in_port_from_nodes(r3, r1)
out_port = net.find_link_and_out_port_from_nodes(r1, lt1)
r1.install_switch_rule(1, in_port, out_port, [2], src_node=r3)



in_port_lt = 3
out_port = net.find_link_and_out_port_from_nodes(r3, r1)
r3.install_switch_rule(1, in_port_lt, out_port, [3], src_node=lt3)

in_port = net.find_link_and_in_port_from_nodes(r3, r1)
out_port = net.find_link_and_out_port_from_nodes(r1, r2)
r1.install_switch_rule(1, in_port, out_port, [3], src_node=r3)

in_port = net.find_link_and_in_port_from_nodes(r1, r2)
out_port = net.find_link_and_out_port_from_nodes(r2, lt2)
r2.install_switch_rule(1, in_port, out_port, [3], src_node=r1)


print("*** TURNING ON LT1")
lt1.assoc_tx_to_channel(lt1.tx_transceivers[1], 1, out_port=1)
lt3.assoc_rx_to_channel(lt3.rx_transceivers[1], 1)
lt1.turn_on()

print("*** TURNING ON LT2")
lt2.assoc_tx_to_channel(lt2.tx_transceivers[2], 2, out_port=2)
lt1.assoc_rx_to_channel(lt1.rx_transceivers[2], 2)
lt2.turn_on()

print("*** TURNING ON LT3")
lt3.assoc_tx_to_channel(lt3.tx_transceivers[3], 3)
lt2.assoc_rx_to_channel(lt2.rx_transceivers[3], 3)
lt3.turn_on()


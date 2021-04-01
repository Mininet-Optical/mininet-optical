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
        tmp = 0


net = network.Network()
# Create line terminals
operational_power = 0  # power in dBm
non = 5  # number of nodes
tr_no = range(1, 91)
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

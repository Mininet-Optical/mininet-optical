"""
    This script will:
    - Model a ring topology (up to 10 nodes due to port availability).
    - Model port numbering of Lumentum ROADM-20 Whiteboxes

    The transmission setup consist in launching one signal from each Terminal
    that terminates at the farthest, adjecent Terminal.
    For example, in a 3 node topology (Terminals 1, 2 and 3):
        Terminal-1 will transmit channel-1 terminating at Terminal-3
        Terminal-2 will transmit channel-2 terminating at Terminal-1
        Terminal-3 will transmit channel-3 terminating at Terminal-2

"""

import mnoptical.network as network
from mnoptical.link import Span as Fiber, SpanTuple as Segment
from mnoptical.node import Transceiver


km = dB = dBm = 1.0
m = .001

# These are the parameters that can be modified
operational_power = 0  # power in dBm
non = 10  # number of nodes (up to 10 because of ports!)
# End of the parameters that can be changed

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
        # amp = net.add_amplifier(
        #     '%s-%s-amp%d' % (r1, r2, i), target_gain=span_length * 0.22 * dB, monitor_mode='out')
        span = Span(span_length, amp=None)
        spans.append(span)

    return net, spans

def build_link(net, r1, r2):
    net, spans = build_spans(net, r1, r2)
    for step, span in enumerate(spans, start=1):
        net.spans.append(span)

    # link object
    net.add_link(r1, r2, spans=spans)

def add_amp(net, node_name=None, type=None, gain_dB=None):
    """
    Create an Amplifier object to add to a ROADM node
    :param node_name: string
    :param type: string ('boost' or 'preamp'
    :param gain_dB: int or float
    """
    label = '%s-%s' % (node_name, type)
    if type == 'preamp':
        return net.add_amplifier(name=label,
                                 target_gain=float(gain_dB),
                                 boost=True,
                                 monitor_mode='out')
    else:
        return net.add_amplifier(name=label,
                                 target_gain=float(gain_dB),
                                 preamp=True,
                                 monitor_mode='out')


def install_paths(nodes, channels, line_terminals):
    for i, node in enumerate(nodes):
        if i == len(nodes) - 1:
            return
        out_port = net.find_link_and_out_port_from_nodes(node, nodes[i + 1])
        if i == 0:
            src_node = line_terminals[i]
            for c in channels:
                in_port = 4100 + c
                node.install_switch_rule(in_port, out_port, [c], src_node=src_node)
        else:
            in_port = net.find_link_and_in_port_from_nodes(nodes[i - 1], node)
            node.install_switch_rule(in_port, out_port, channels, src_node=nodes[i - 1])

# Create a Network object
net = network.Network()
# Create Line Terminals
# Enabling only 10 Transceivers, leaving (theoretically)
# 14 ports to use when modeling Cassini Transponders
tr_no = range(1, 11)
tr_labels = ['tr%s' % str(x) for x in tr_no]
line_terminals = []
for i in range(non):
    # plugging a Transceiver at the first 10 ports of the Terminal
    transceivers = [Transceiver(id, tr, operation_power=operational_power)
                       for id, tr in enumerate(tr_labels, start=1)]
    lt = net.add_lt('lt_%s' % (i + 1), transceivers=transceivers, monitor_mode='in')
    line_terminals.append(lt)

# If you change the launch power of signals, remember to configure
# the ROADM parameters: insertion_loss_dB and reference_power_dBm;
# default reference_power_dBm is 0 dBm
roadms = [net.add_roadm('r%s' % (i + 1),
                        preamp=add_amp(net, node_name='r%s' % (i + 1), type='preamp', gain_dB=17.6),
                        boost=add_amp(net, node_name='r%s' % (i + 1), type='boost', gain_dB=17.0)
                        ) for i in range(non)]

# Modelling Lumentum ROADM-20 port numbering
roadm20_in_ports = [i + 1 for i in range(4100, 4120)]
roadm20_out_ports = [i + 1 for i in range(5200, 5220)]
# Create bi-directional links between LTs and ROADMs
# Need to decide which ports are connected to the ROADM
# Port-1 from Terminals are connected to Port-4101 from ROADMs.
for lt, roadm in zip(line_terminals, roadms):
    for i, tr in enumerate(transceivers):
        roadm20_in_port = roadm20_in_ports[i]
        net.add_link(lt, roadm, src_out_port=tr.id, dst_in_port=roadm20_in_port, spans=[Span(1 * m)])

        roadm20_out_port = roadm20_out_ports[i]
        net.add_link(roadm, lt, src_out_port=roadm20_out_port, dst_in_port=tr.id, spans=[Span(1 * m)])

# Build links between ROADMs
# Port numbering will be sequential based on the
# last configured port. Based on the configuration above:
#   - next input port numbering is: 4111
#   - next output port numbering is: 5211
for i, roadm in enumerate(roadms):
    if i == len(roadms) - 1:
        build_link(net, roadm, roadms[0])
    else:
        build_link(net, roadm, roadms[i + 1])

# Modelling transmission of one channel from each Terminal
ch_no = 1
channels = range(1, ch_no + 1)
channels = [1]
for i, (r, lt_tx) in enumerate(zip(roadms, line_terminals)):
    # Get the receiver terminal
    if i == 0:
        lt_rx = line_terminals[-1]
    else:
        lt_rx = line_terminals[i - 1]

    for c in channels:
        # configure transmitter terminal
        tx_transceiver = lt_tx.id_to_transceivers[c]
        lt_tx.assoc_tx_to_channel(tx_transceiver, c, out_port=c)

        # configure receiver terminal
        rx_transceiver = lt_rx.id_to_transceivers[c]
        lt_rx.assoc_rx_to_channel(rx_transceiver, c, in_port=1)

    # build paths from r_i to r_n
    path = [r] + roadms[i + 1:]
    if len(path) < len(roadms):
        path += roadms[:i]
    path.append(lt_rx)

    # install switch rules into the ROADMs based on the paths
    install_paths(path, channels, line_terminals)

    print("*** Turning on:", lt_tx)
    lt_tx.turn_on()

    # Increment channel index
    ch = channels[0] + 1
    channels[0] = ch

# Verify that all signals are received properly
# Note we may wish to lower our threshold of 20 dB in the future

tcount = len(line_terminals)
for i, lt in enumerate(line_terminals, start=0):
    mon = lt.monitor
    osnrs = mon.get_dict_osnr()
    gosnrs = mon.get_dict_gosnr()
    ch = (i+1)%tcount + 1
    assert list(sig.index for sig in osnrs.keys()) == [ch]
    osnr = list(osnrs.values())[0]
    gosnr = list(gosnrs.values())[0]
    assert 0 < osnr < 21, f"{lt} channel {ch} bad OSNR: <{osnr}>"
    assert 0 < gosnr < 21, f"{lt} channel {ch} bad gOSNR: <{gosnr}>"
    osnr, gosnr = '%.2f'%osnr, '%.2f'%gosnr
    print(f'Channel {ch} received at {lt} gOSNR {gosnr} dB OSNR {osnr} dB')

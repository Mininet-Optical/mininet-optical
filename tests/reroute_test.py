"""
    This script models a linear topology between two line terminals
    with two ROADMs in between and two links between ROADMS:

                       (link1)
                       ------>
           lt1 ---> r1         r2 ----> lt2
                       ------>
                       (link2)

    lt1 will transmit channel 1 at 0 dBm launch power and
    r1 will switch from port 4101 out to port 5203
    r2 will switch from port 4103 out to port 5201

    Then we will update the system so that:
    r1 will switch from port 4101 out to port 5204
    r2 will switch from port 4104 out to port 5202
"""


import mnoptical.network as network
from mnoptical.link import Span as Fiber, SpanTuple as Segment
from mnoptical.node import Transceiver


km = dB = dBm = 1.0
m = .001

def Span(km, amp=None):
    """Return a fiber segment of length km with a compensating amp"""
    return Segment(span=Fiber(length=km), amplifier=amp)

def build_spans(net, r1, r2, _id):
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
            '%s-%s-amp%d-%s' % (r1, r2, i, _id), target_gain=span_length * 0.22 * dB, monitor_mode='out')
        span = Span(span_length, amp=amp)
        spans.append(span)

    return net, spans

def build_link(net, r1, r2, _id):
    net, spans = build_spans(net, r1, r2, _id)
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


# Create the network object
net = network.Network()
# Create line terminals
operational_power = 0  # power in dBm
non = 2  # only 2 nodes in this script!
tr_no = [1, 2] # number of transceivers in a terminal
tr_labels = ['tr%s' % str(x) for x in tr_no]

line_terminals = []
for i in range(non):
    # need to create new Transceivers for the different Terminals
    transceivers = [Transceiver(id, tr, operation_power=operational_power)
                       for id, tr in enumerate(tr_labels, start=1)]
    lt = net.add_lt('lt_%s' % (i + 1), transceivers=transceivers)
    line_terminals.append(lt)

# add roadms to the network
roadms = [net.add_roadm('r%s' % (i + 1),
                        insertion_loss_dB=17,
                        reference_power_dBm=operational_power,
                        preamp=add_amp(net, node_name='r%s' % (i + 1), type='preamp', gain_dB=17.6),
                        boost=add_amp(net, node_name='r%s' % (i + 1), type='boost', gain_dB=17.0)
                        ) for i in range(non)]

# Modelling Lumentum ROADM-20 port numbering
roadm20_in_ports = [i + 1 for i in range(4100, 4120)]
roadm20_out_ports = [i + 1 for i in range(5200, 5220)]

# Create bi-directional links between LTs and ROADMs
for lt, roadm in zip(line_terminals, roadms):
    for i, tr in enumerate(transceivers):
        roadm20_in_port = roadm20_in_ports[i]
        net.add_link(lt, roadm, src_out_port=tr.id, dst_in_port=roadm20_in_port, spans=[Span(0 * m)])

        roadm20_out_port = roadm20_out_ports[i]
        net.add_link(roadm, lt, src_out_port=roadm20_out_port, dst_in_port=tr.id, spans=[Span(0 * m)])

lt_1 = net.name_to_node['lt_1']
lt_2 = net.name_to_node['lt_2']

r1 = net.name_to_node['r1']
r2 = net.name_to_node['r2']

# create two links between r1 and r2
build_link(net, r1, r2, 1)
build_link(net, r1, r2, 2)

# configure transmitter terminal
tx_transceiver = lt_1.id_to_transceivers[1]
channel = 1
lt_1.assoc_tx_to_channel(tx_transceiver, channel, out_port=1)
# configure receiver terminal
rx_transceiver = lt_2.id_to_transceivers[1]
lt_2.assoc_rx_to_channel(rx_transceiver, channel, in_port=1)

# install switch rules
r1.install_switch_rule(4101, 5203, channel, src_node=lt_1)
r2.install_switch_rule(4103, 5201, channel, src_node=r1)

# launch channel 1 from lt1
lt_1.turn_on()

# rerouting process:
# reconfigure receiver terminal
lt_2.disassoc_rx_to_channel(in_port=1, channel_id=1)

# configure new receiver terminal
new_rx_transceiver = lt_2.id_to_transceivers[2]
lt_2.assoc_rx_to_channel(new_rx_transceiver, channel, in_port=2)

# remove previous rule for channel 1 at r2,
# this is not required for rerouting to be successful,
# but the controller needs to clean unused/old switch rules
r2.delete_switch_rule(4103, channel)
# install new switch rule for r2
r2.install_switch_rule(4104, 5202, channel)
# reroute channel 1 at r1
r1.update_switch_rule(4101, channel, 5204, switch=True)

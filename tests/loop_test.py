"""
    This script will create a loop topology with 3 nodes

    The configuration of the network components, mainly Terminals, ROADMs
    is hard-coded to allow for detailed explanation. For an automated
    script refer to loop_test_auto.py

    It also attempts to model the Lumentum ROADM-20 port configuration.

    Transmission configuration:
        LT1 transmits CH1 to be delivered at LT3
        LT2 transmits CH2 to be delivered at LT1
        LT3 transmits CH3 to be delivered at LT2

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


# Create the network object
net = network.Network()
# Create line terminals
operational_power = -2  # power in dBm
non = 3  # only 3 nodes in this script!
tr_no = range(1, 11) # number of transceivers in a terminal
tr_labels = ['tr%s' % str(x) for x in tr_no]

line_terminals = []
for i in range(non):
    # need to create new Transceivers for the different Terminals
    transceivers = [Transceiver(id, tr, operation_power=operational_power)
                       for id, tr in enumerate(tr_labels, start=1)]
    lt = net.add_lt('lt_%s' % (i + 1), transceivers=transceivers, monitor_mode='in')
    line_terminals.append(lt)

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

lt1 = net.name_to_node['lt_1']
lt2 = net.name_to_node['lt_2']
lt3 = net.name_to_node['lt_3']

r1 = net.name_to_node['r1']
r2 = net.name_to_node['r2']
r3 = net.name_to_node['r3']

build_link(net, r1, r2)
build_link(net, r2, r3)
build_link(net, r3, r1)

in_port_lt = 4101
out_port = 5211
r1.install_switch_rule(in_port_lt, out_port, [1], src_node=lt1)

in_port = 4111
out_port = 5211
r2.install_switch_rule(in_port, out_port, [1], src_node=r1)

in_port = 4111
out_port = 5201
r3.install_switch_rule(in_port, out_port, [1], src_node=r2)


in_port_lt = 4102
out_port = 5211
r2.install_switch_rule(in_port_lt, out_port, [2], src_node=lt2)

in_port = 4111
out_port = 5211
r3.install_switch_rule(in_port, out_port, [2], src_node=r2)

in_port = 4111
out_port = 5202
r1.install_switch_rule(in_port, out_port, [2], src_node=r3)



in_port_lt = 4103
out_port = 5211
r3.install_switch_rule(in_port_lt, out_port, [3], src_node=lt3)

in_port = 4111
out_port = 5211
r1.install_switch_rule(in_port, out_port, [3], src_node=r3)

in_port = 4111
out_port = 5203
r2.install_switch_rule(in_port, out_port, [3], src_node=r1)


print("*** TURNING ON LT1")
lt1.assoc_tx_to_channel(lt1.id_to_transceivers[1], 1, out_port=1)
lt3.assoc_rx_to_channel(lt3.id_to_transceivers[1], 1, in_port=1)
lt1.turn_on()

print("*** TURNING ON LT2")
lt2.assoc_tx_to_channel(lt2.id_to_transceivers[2], 2, out_port=2)
lt1.assoc_rx_to_channel(lt1.id_to_transceivers[2], 2, in_port=2)
lt2.turn_on()

print("*** TURNING ON LT3")
lt3.assoc_tx_to_channel(lt3.id_to_transceivers[3], 3, out_port=3)
lt2.assoc_rx_to_channel(lt2.id_to_transceivers[3], 3, in_port=3)
lt3.turn_on()


# Verify that all signals are received properly

for i, lt in enumerate((lt1, lt2, lt3)):
    mon = lt.monitor
    osnrs = mon.get_dict_osnr()
    gosnrs = mon.get_dict_gosnr()
    ch = (i+1)%3 + 1
    assert list(sig.index for sig in osnrs.keys()) == [ch]
    osnr = list(osnrs.values())[0]
    gosnr = list(gosnrs.values())[0]
    assert 15 < osnr < 25, f"{lt} channel {ch} bad OSNR: <{osnr}>"
    assert 15 < gosnr < 25, f"{lt} channel {ch} bad gOSNR: <{gosnr}>"
    osnr, gosnr = '%.2f'%osnr, '%.2f'%gosnr
    print(f'Channel {ch} received at {lt} gOSNR {gosnr} dB OSNR {osnr} dB')

"""
    This is an example used for an internal tutorial on Mininet-Optical.

    It models a linear topology with 5-ROADMs, with 3x80km spans
    between ROADMs, optically amplified with EDFAs. We then use
    2 line terminals (LT) with N number of transceivers for transmitting
    and receiving modelled optical signals.

    The script allows the user to monitor OSNR or gOSNR levels
    of N number of channels transmitted from LT1 --> LT2, at each
    amplifier of the end-to-end link.

"""
from topo.linear import LinearTopology
from units import *


# Define initial and end power levels for the transmission
p_start = 0
p_end = 2
p_step = 2
power_levels = list(np.arange(p_start, p_end, p_step))
# Define number of wavelengths to transmit
num_wavelengths = 3
channel_indexes = list(range(1, num_wavelengths + 1))
# Define channel index to monitor (channel under test - cut)
cut = int(np.floor(len(channel_indexes) / 2))

print("*** Monitoring channel with index: ", cut)

for i, p in enumerate(power_levels):
    print("*** Building Linear network topology for operational power: %s" % p)
    net = LinearTopology.build(op=p, non=5)

    # Retrieve line terminals (transceivers) from network
    lt_1 = net.name_to_node['lt_1']
    lt_5 = net.name_to_node['lt_5']
    # Configure terminals
    for c in channel_indexes:
        # configure transmitter terminal
        tx_transceiver = lt_1.id_to_transceivers[c]
        lt_1.assoc_tx_to_channel(tx_transceiver, c, out_port=c)

        # configure receiver terminal
        rx_transceiver = lt_5.id_to_transceivers[c]
        lt_5.assoc_rx_to_channel(rx_transceiver, c)

    # This allows to iterate through the ROADMs
    roadms = net.roadms
    # Installing rules to the ROADMs (algorithms can vary)
    for i, roadm in enumerate(roadms):
        if i == 0:
            current_roadm = roadm
            next_roadm = roadms[i + 1]
            # We find the output port of r1 towards r2
            out_port = net.find_link_and_out_port_from_nodes(current_roadm, next_roadm)
            # We need to install channels sequentially when signals go
            # from a terminal (transceiver) to a ROADM
            for channel in channel_indexes:
                in_port = 4100 + channel
                # install switch rule gets as input: rule_id, in_port, out_port, channel.
                current_roadm.install_switch_rule(in_port, out_port, [channel])
        else:
            prev_roadm = roadms[i - 1]
            current_roadm = roadm
            in_port = net.find_link_and_in_port_from_nodes(prev_roadm, current_roadm)

            if i < len(roadms) - 1:
                next_roadm = roadms[i + 1]
                out_port = net.find_link_and_out_port_from_nodes(current_roadm, next_roadm)
            elif i == len(roadms) - 1:
                out_port = net.find_link_and_out_port_from_nodes(current_roadm, lt_5)
            # It is possible to get a single rule for multiple channels
            # for the connections between ROADMs.
            current_roadm.install_switch_rule(in_port, out_port, channel_indexes)

    # Now we turn on the "comb source" connected to the main terminal
    lt_1.turn_on()

    print("*** Monitoring interfaces")
    osnrs = []
    gosnrs = []
    # Iterate through monitoring nodes at each EDFA
    for amp in net.amplifiers:
        print(amp.monitor.get_list_osnr())
        osnrs.append((amp.monitor, amp.monitor.get_list_osnr()[cut][1]))
        gosnrs.append((amp.monitor, amp.monitor.get_list_gosnr()[cut][1]))

# print("The gOSNR of channel %s at each location:" %cut)
# for element in gosnrs:
#     print("Channel: %s | Location: %s | gOSNR: %f dB" % (cut, element[0].name, element[1]))

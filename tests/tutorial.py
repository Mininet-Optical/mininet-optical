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
# Structures to monitor the OSNR, gOSNR and OSNR-ASE (analytical model)
plotting_osnr = []
plotting_gosnr = []
plotting_analytical = []
# Define number of wavelengths to transmit
num_wavelengths = 3
wavelength_indexes = list(range(1, num_wavelengths + 1))
# Define channel index to monitor (channel under test - cut)
cut = int(np.floor(len(wavelength_indexes) / 2))

print("*** Monitoring channel with index: ", cut)

for i, p in enumerate(power_levels):
    print("*** Building Linear network topology for operational power: %s" % p)
    net = LinearTopology.build(op=p, non=5)

    # Retrieve line terminals (transceivers) from network
    lt_1 = net.name_to_node['lt_1']
    lt_5 = net.name_to_node['lt_5']

    # Retrieve ROADMs from network
    roadm_1 = net.name_to_node['r1']
    roadm_2 = net.name_to_node['r2']
    roadm_3 = net.name_to_node['r3']
    roadm_4 = net.name_to_node['r4']
    roadm_5 = net.name_to_node['r5']

    # Configure terminals
    transceivers = lt_1.transceivers
    for i, channel in enumerate(wavelength_indexes, start=wavelength_indexes[0]):
        # channels are enumerated starting from 1
        # transceivers and their ports are enumerated starting from 0
        t = transceivers[i - 1]
        lp_descriptor = {'src_roadm': roadm_1, 'dst_roadm': roadm_5}
        # associate transceiver to channel in LineTerminal
        lt_1.configure_terminal(t, channel)

    # Now, we will install switch rules into the ROADM nodes

    # We retrieve the first input port of ROADM connected to the terminal
    in_port_lt = wavelength_indexes[0] - 1

    # This allows to iterate through the ROADMs
    roadms = [roadm_1, roadm_2, roadm_3, roadm_4, roadm_5]
    # Installing rules to the ROADMs (algorithms can vary)
    for i in range(len(roadms)):
        if i == 0:
            r1 = roadms[i]
            r2 = roadms[i + 1]
            # We find the output port of r1 towards r2
            out_port = net.find_link_and_out_port_from_nodes(r1, r2)
            # We need to install channels sequentially when signals go
            # from a terminal (transceiver) to a ROADM
            for i, channel in enumerate(wavelength_indexes, start=1):
                # install switch rule gets as input: rule_id, in_port, out_port, channel.
                r1.install_switch_rule(i, in_port_lt, out_port, [channel])
                # We can configure the variable optical attenuators comprising the ROADM.
                r1.configure_voa(channel_id=channel, output_port=out_port, operational_power_dB=p)
                in_port_lt += 1

        else:
            r1 = roadms[i - 1]
            r2 = roadms[i]
            in_port = net.find_link_and_in_port_from_nodes(r1, r2)

            if i < 4:
                r3 = roadms[i + 1]
                out_port = net.find_link_and_out_port_from_nodes(r2, r3)
            elif i == 4:
                out_port = net.find_link_and_out_port_from_nodes(r2, lt_5)
            # It is possible to get a single rule for multiple channels
            # for the connections between ROADMs.
            r2.install_switch_rule(1, in_port, out_port, wavelength_indexes)
            for chx in wavelength_indexes:
                r2.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=p)

    # Now we turn on the "comb source" connected to the main terminal
    lt_1.turn_on()

    print("*** Monitoring interfaces")
    osnrs = []
    gosnrs = []
    # Iterate through monitoring nodes at each EDFA
    for amp in net.amplifiers:
        osnrs.append((amp.monitor, amp.monitor.get_list_osnr()[cut][1]))
        gosnrs.append((amp.monitor, amp.monitor.get_list_gosnr()[cut][1]))

print("The gOSNR of channel %s at each location:" %cut)
for element in gosnrs:
    print("Channel: %s | Location: %s | gOSNR: %f dB" % (cut, element[0].name, element[1]))
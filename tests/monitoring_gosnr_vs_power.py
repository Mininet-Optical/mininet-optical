from topo.linear import LinearTopology
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager
import pickle


# Uncomment this for manipulating plots
# Plot configuration parameters
# figure(num=None, figsize=(7, 6), dpi=256)
# del matplotlib.font_manager.weight_dict['roman']
# matplotlib.font_manager._rebuild()
# plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams["font.size"] = 20


def process_signals(signals):
    """
    For later processing, this method creates a pickle file
    containing the signal objects of the transmissions
    executed in the main script.
    """
    signals_to_pickle = [s[0] for s in signals]
    signal = signals[0][0]
    loc_out_to_state = signal.loc_out_to_state

    element_to_signals = {}
    element_count = 0
    for element in signal.visited_elements:
        element_to_signals[element_count] = []
        element_count += 1

    for tup in signals:
        signal = tup[0]
        element_count = 0
        for element in signal.loc_out_to_state.keys():
            metrics = signal.loc_out_to_state[element]

            signal_to_metric = (signal.index, metrics)
            element_to_signals[element_count].append(signal_to_metric)
            element_count += 1
    # pickle.dump(element_to_signals, open('propagation_mo.pickle', 'wb'))


def db_to_abs(db_value):
    """
    :param db_value: list or float
    :return: Convert dB to absolute value
    """
    absolute_value = 10**(db_value/float(10))
    return absolute_value


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10*np.log10(absolute_value)
    return db_value


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
        lt_1.configure_terminal(t, channel)#, lp_descriptor=lp_descriptor)

    # Install switch rules into the ROADM nodes
    # input port of roadm when coming from terminal
    in_port_lt = wavelength_indexes[0] - 1

    roadms = [roadm_1, roadm_2, roadm_3, roadm_4, roadm_5]
    # roadms
    for i in range(len(roadms)):
        if i == 0:
            r1 = roadms[i]
            r2 = roadms[i + 1]
            out_port = net.find_link_and_out_port_from_nodes(r1, r2)
            for i, channel in enumerate(wavelength_indexes, start=1):
                r1.install_switch_rule(i, in_port_lt, out_port, [channel])
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

            r2.install_switch_rule(1, in_port, out_port, wavelength_indexes)
            for chx in wavelength_indexes:
                r2.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=p)

    lt_1.turn_on()

    print("*** Monitoring interfaces")
    osnrs = []
    gosnrs = []
    equis_list = []
    # Retrieve number of amplifiers (or monitoring nodes)
    for amp in net.amplifiers:
        osnrs.append(amp.monitor.get_list_osnr()[cut][1])
        gosnrs.append(amp.monitor.get_list_gosnr()[cut][1])
        # This is for later processing of the signals
        tmp = []
        for tup in amp.monitor.get_list_gosnr():
            tmp.append(tup[1])
        equis_list.append(tmp)
    tmp_amp = net.amplifiers[-1]

    optical_signal = tmp_amp.monitor.extract_optical_signal()
    process_signals(optical_signal)

    plotting_osnr.append(osnrs)
    plotting_gosnr.append(gosnrs)

    an_osnr = []
    for s in range(16):
        t_osnr = p + 58 - 0.22 * 80 - 5.5 - 10 * np.log10(s + 1)
        an_osnr.append(t_osnr)
    plotting_analytical.append(an_osnr)

    print("*** Destroying objects")
    del net
    del osnrs
    del gosnrs


colors = ['r', 'g', 'b', 'y', 'k']
op = list(np.arange(p_start, p_end, 2)[::-1])
label_flag = True
for a in plotting_analytical:
    if label_flag:
        plt.plot(a, color='r', markerfacecolor='None', label='Analytical model')
        label_flag = False
    else:
        plt.plot(a, color='r', markerfacecolor='None')
for o, g, a in zip(plotting_osnr, plotting_gosnr, plotting_analytical):
    pp = op.pop()
    label = 'Tx launch power: ' + str(pp) + 'dBm'
    c = colors.pop()
    plt.plot(o, markeredgewidth=3, markersize=9, color=c, label=label)
    plt.plot(g, '--', markeredgewidth=3, markersize=9, markerfacecolor='None', color=c)

plt.ylabel("OSNR, gOSNR(dashed) (dB)")
plt.xlabel("Amplifiers")
ticks = []
s = 0
for i in range(17):
    ticks.append(s)
    if i == 5 or i == 11:
        continue
    else:
        s += 8
plt.xticks(np.arange(16))
plt.legend(loc=1)
plt.grid(True)
# plt.savefig('../../gosnr_vs_power.eps', format='eps')
plt.show()

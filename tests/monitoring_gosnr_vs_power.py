from topo.linear import LinearTopology
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager
import pickle


# Plot configuration parameters
# figure(num=None, figsize=(7, 6), dpi=256)
# del matplotlib.font_manager.weight_dict['roman']
# matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20


def process_signals(signals):
    signals_to_pickle = [s[0] for s in signals]
    signal = signals[0][0]
    loc_out_to_state = signal.loc_out_to_state
    # abandoning creating path_elements with the
    # network elements as keys due to pickle issues.
    # for element in loc_out_to_state.keys():
    #     if type(element) is tuple:
    #         print(type(element[1]))
    #         path_elements.append(element[1])
    #     else:
    #         path_elements.append(element)

    element_to_signals = {}
    element_count = 0
    for element in signal.visited_elements:
        element_to_signals[element_count] = []
        element_count += 1

    for tup in signals:
        signal = tup[0]
        element_count = 0
        for element in signal.loc_out_to_state.keys():
            # print("%s - Adding element %s" % (element_count,element))
            # print(element)
            metrics = signal.loc_out_to_state[element]

            # power = metrics['power']
            # ase = metrics['ase_noise']
            # nli = metrics['nli_noise']

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

# print("*** Monitoring channel with index: ", cut)

const = [0.9208695298291589,
0.6143331039817461,
0.4204186816395481,
0.29917618240415145,
0.22509003725233256,
0.18223342079877014,
0.1607038351903185,
0.15308848572732714,
0.14641861288907165,
0.11029305856456517,
0.024941672404327875,
0.14369069155251424,
0.3931033768664225,
0.8887881899976264]
for i, p in enumerate(power_levels):
    # print("*** Building Linear network topology for operational power: %s" % p)
    # if p < 0:
    #     p -= const[i]
    # else:
    #     p -= const[i]
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
        # associate transceiver to channel in LineTerminal
        lt_1.configure_terminal(t, channel)

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

    # print("*** Monitoring interfaces")
    osnrs = []
    gosnrs = []
    equis_list = []
    # Retrieve number of amplifiers (or monitoring nodes)
    for amp in net.amplifiers:
        osnrs.append(amp.monitor.get_list_osnr()[cut][1])
        gosnrs.append(amp.monitor.get_list_gosnr()[cut][1])
        tmp = []
        for tup in amp.monitor.get_list_gosnr():
            tmp.append(tup[1])
        equis_list.append(tmp)
    tmp_amp = net.amplifiers[-1]

    # for equis in equis_list:
    #     print(equis)

    optical_signal = tmp_amp.monitor.extract_optical_signal()
    process_signals(optical_signal)

    tmp_list = []
    for tup in tmp_amp.monitor.get_list_gosnr():
        tmp_list.append(tup[1])
    # print(tmp_list, ",")
    # print(tmp_list[89], ",")
    plotting_osnr.append(osnrs)
    plotting_gosnr.append(gosnrs)

    an_osnr = []
    for s in range(16):
        t_osnr = p + 58 - 0.22 * 80 - 5.5 - 10 * np.log10(s + 1)
        an_osnr.append(t_osnr)
    plotting_analytical.append(an_osnr)

    #print("*** Destroying objects")
    del net
    del osnrs
    del gosnrs

# for gosnr_value in plotting_gosnr:
#    print(str(gosnr_value[0]) + ',')

# print(plotting_osnr)

# colors = ['r', 'g', 'b', 'y', 'k']
# op = list(np.arange(p_start, p_end, 2)[::-1])
# label_flag = True
# for a in plotting_analytical:
#     if label_flag:
#         plt.plot(a, color='r', markerfacecolor='None', label='Analytical model')
#         label_flag = False
#     else:
#         plt.plot(a, color='r', markerfacecolor='None')
# for o, g, a in zip(plotting_osnr, plotting_gosnr, plotting_analytical):
#     pp = op.pop()
#     label = 'Tx launch power: ' + str(pp) + 'dBm'
#     c = colors.pop()
#     plt.plot(o, markeredgewidth=3, markersize=9, color=c, label=label)
#     plt.plot(g, '--', markeredgewidth=3, markersize=9, markerfacecolor='None', color=c)
# # Retrieved data from emulator
# gosnr_0 = [35.33233577118823, 31.37664820503778, 29.337195864255065, 27.95468662911725,
#        27.260088963719397, 26.35274045416481, 25.60277551116353, 24.9633017937713,
#        24.602184439802617, 24.085431568092144, 23.62504242642067, 23.20871259522844,
#        22.9653910885472, 22.603394605978284, 22.27117344994892, 21.962490381114318]
# gosnr_m2 = [33.409092181516876, 29.952722654611506, 28.049563136381686, 26.728610845562347,
#             25.907648074249426, 25.057124363613173, 24.345159828032177, 23.732559106857867,
#             23.301613338567453, 22.814181577214228, 22.375518798652575, 21.976406329063703,
#             21.68427417512917, 21.342462391048294, 21.025412451391507, 20.729400827053006]
# gosnr_m4 = [31.458229639468573, 28.122927062557398, 26.25730945682382, 24.955259283403542,
#             24.093989132517393, 23.258946820864956, 22.558244501581825, 21.954423438959946,
#             21.50157438359468, 21.022141225609445, 20.590050051132263, 20.19667014116184,
#             19.889396750962813, 19.55303384554338, 19.240617414522458, 18.948863283716474]
# plt.plot(gosnr_0, 'g')
# plt.plot(gosnr_m2, 'g')
# plt.plot(gosnr_m4, 'g')
#
#
# plt.ylabel("OSNR, gOSNR(dashed) (dB)")
# plt.xlabel("Amplifiers")
# ticks = []
# s = 0
# for i in range(17):
#     ticks.append(s)
#     if i == 5 or i == 11:
#         continue
#     else:
#         s += 8
# plt.xticks(np.arange(16))
# plt.legend(loc=1)
# plt.grid(True)
# # plt.savefig('../../gosnr_vs_power.eps', format='eps')
# plt.show()

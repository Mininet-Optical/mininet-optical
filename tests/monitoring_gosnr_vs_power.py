from sklearn.metrics import mean_absolute_error
from topo.linear import LinearTopology
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager
import random

# Plot configuration parameters
# figure(num=None, figsize=(7, 6), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 16


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


p_start = 6
p_end = 12
power_levels = list(np.arange(p_start, p_end, 2))
plotting_osnr = []
plotting_gosnr = []
plotting_osnr_nli = []
plotting_theo = []
rx_gosnr = []
rx_osnr_nli = []
rx_osnr = []
num_channels = 76
wavelength_indexes = list(range(1, num_channels + 1))
index = int(np.floor(len(wavelength_indexes) / 2))
print("Monitoring channel with index: ", index)
# wavelength_indexes.reverse()
# wavelength_indexes = random.sample(range(1, 90), 81)

for p in power_levels:
    # print("*** Building Linear network topology for operational power: %s" % p)
    print("*** Building Linear network topology..." % p)
    net = LinearTopology.build(op=p, non=5)

    lt_1 = net.name_to_node['lt_1']
    lt_2 = net.name_to_node['lt_2']
    lt_3 = net.name_to_node['lt_3']

    roadm_1 = net.name_to_node['roadm_1']
    roadm_2 = net.name_to_node['roadm_2']
    roadm_3 = net.name_to_node['roadm_3']
    roadm_4 = net.name_to_node['roadm_4']
    roadm_5 = net.name_to_node['roadm_5']

    # for port, node in roadm_3.port_to_node_out.items():
    #     print("%s reachable through port %s" % (node.name, port))
    # for port, node in roadm_3.port_to_node_in.items():
    #     print("roadm_3 reachable by %s through port %s" % (node.name, port))

    # Install switch rules into the ROADM nodes
    # wavelength_indexes = range(1, 82)
    # reversed(wavelength_indexes)
    roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
    roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_3.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_5.install_switch_rule(1, 1, 100, wavelength_indexes)

    rw = wavelength_indexes
    # Set resources to use and initiate transmission
    resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
    net.transmit(lt_1, roadm_1, resources=resources)

    print("*** Monitoring interfaces...")
    osnrs = {i: [] for i in range(1, 17)}
    gosnrs = {i: [] for i in range(1, 17)}
    osnrs_nli = {i: [] for i in range(1, 17)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'opm_'
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        osnrs[key] = opm.get_list_osnr()
        gosnrs[key] = opm.get_list_gosnr()
        osnrs_nli[key] = opm.get_list_osnr_nli()

    # Retrieve only the channels of interest
    osnr_cut = []
    for span, _list in osnrs.items():
        osnr_cut.append(_list[index])
        # osnr_cut.append(np.mean(_list))
    plotting_osnr.append(osnr_cut)
    rx_osnr.append(osnr_cut[-1])

    gosnr_cut = []
    for span, _list in gosnrs.items():
        # gosnr_cut.append(np.mean(_list))
        gosnr_cut.append(_list[index])
    plotting_gosnr.append(gosnr_cut)
    rx_gosnr.append(gosnr_cut[-1])

    osnr_nli_cut = []
    for span, _list in osnrs_nli.items():
        # osnr_nli_cut.append(np.mean(_list))
        osnr_nli_cut.append(_list[index])
    plotting_osnr_nli.append(osnr_nli_cut)
    rx_osnr_nli.append(osnr_nli_cut[-1])

    an_osnr = []  # [osnr_c46[0]]
    c = 0
    i = 0
    for s in range(16):
        # if i is 3 or i is 7 or i is 11:
        #     t_osnr = c
        # else:
        t_osnr = p + 58 - 0.22 * 80 - 5.5 - 10 * np.log10(s + 1)
        c = t_osnr
        i += 1
        an_osnr.append(t_osnr)
    plotting_theo.append(an_osnr)

    mae = mean_absolute_error(plotting_theo, plotting_osnr)
    print(mae)

    print("*** Destroying objects")
    del net
    del osnrs
    del gosnrs

colors = ['r', 'g', 'k', 'grey', 'silver', 'r', 'g', 'k', 'grey', 'silver', 'r', 'g', 'k', 'grey', 'silver']
markers = ['o', 's', 'D']
op = list(np.arange(p_start, p_end, 2)[::-1])
label_flag = True
for a in plotting_theo:
    if label_flag:
        plt.plot(a, color='r', markerfacecolor='None', label='Analytical model')
        label_flag = False
    else:
        plt.plot(a, color='r', markerfacecolor='None')
for o, g, a in zip(plotting_osnr, plotting_gosnr, plotting_theo):
    pp = op.pop()
    l = 'Tx launch power: ' + str(pp) + 'dBm'
    c = colors.pop()
    # m = markers.pop()
    # plt.plot(o, markeredgewidth=2, marker=m, markersize=9, color=c, label=l)
    plt.plot(o, markeredgewidth=3, markersize=9, color=c, label=l)
    # plt.plot(g, '--', markeredgewidth=2, marker=m, markersize=9, markerfacecolor='None', color=c)
    plt.plot(g, '--', markeredgewidth=3, markersize=9, markerfacecolor='None', color=c)
    print("=%=%=%=%=%=%=%=%=%")
    print(l)
    print(o)
    print(g)
    print(a)
    # print(gosnr_c46_dict[pp])
    print("=%=%=%=%=%=%=%=%=%")


plt.ylabel("OSNR, gOSNR(dashed) (dB)")
plt.xlabel("Amplifiers")
# plt.yticks(np.arange(18, 40, 2))
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
# for i in range(2):
#     if i is 0:
#         axs[i].set_ylabel("OSNR(dB)")
#         plt.setp(axs[i].get_xticklabels(), visible=False)
#         axs[i].tick_params(axis='x', which='both', length=0)
#     else:
#         axs[i].set_ylabel("gOSNR (dB)")
#         axs[i].set_xlabel("Spans and hops")
#     ticks = []
#     s = 0
#     for j in range(17):
#         ticks.append(s)
#         if j == 5 or j == 11:
#             continue
#         else:
#             s += 8
#     axs[i].set_xticks(np.arange(16))
#     axs[i].set_yticks(np.arange(12, 50, 6))
#     axs[i].legend(loc=1, prop={'size': 14})
#     axs[i].grid(True)
plt.savefig('../../gosnr_vs_power.eps', format='eps')
print("=%=%=%=%=%=%=%")
print(rx_osnr)
print(rx_gosnr)
print(rx_osnr_nli)
# print(plotting_osnr)
plt.show()

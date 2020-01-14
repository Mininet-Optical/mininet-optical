"""
    This script will build the Linear topology and run a single
    81-channel transmission with the default configuration of the simulator,
    and will monitor 1 channel when launched at different distances and
    power levels.
    The latter, will then be plotted.

    For different distances and monitoring points one needs to edit the
    LinearTopology declaration in ../topo/linear.py

"""

from topo.deutsche_telekom import DeutscheTelekom
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager

del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20


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


power_levels = list(np.arange(-4, 6, 2))
plotting_osnr = []
plotting_gosnr = []
plotting_theo = []

for p in power_levels:
    print("*** Building Deutsche Telekom network topology for operational power: %s" % p)
    net = DeutscheTelekom.build(op=p)

    lt_koln = net.name_to_node['lt_koln']
    lt_munchen = net.name_to_node['lt_munchen']

    roadm_koln = net.name_to_node['roadm_koln']
    roadm_frankfurt = net.name_to_node['roadm_frankfurt']
    roadm_nurnberg = net.name_to_node['roadm_nurnberg']
    roadm_munchen = net.name_to_node['roadm_munchen']

    # Install switch rules into the ROADM nodes
    wavelength_indexes = range(1, 82)
    roadm_koln.install_switch_rule(1, 0, 103, wavelength_indexes)
    roadm_frankfurt.install_switch_rule(1, 2, 104, wavelength_indexes)
    roadm_nurnberg.install_switch_rule(1, 1, 103, wavelength_indexes)
    roadm_munchen.install_switch_rule(1, 1, 100, wavelength_indexes)

    # Set resources to use and initiate transmission
    resources = {'transceiver': lt_koln.name_to_transceivers['t1'], 'required_wavelengths': wavelength_indexes}
    print("*** Initializing end-to-end transmission from %s to %s" % (lt_koln.name, lt_munchen.name))
    net.transmit(lt_koln, roadm_koln, resources=resources)
    print("*** Transmission successful!")

    print("*** Monitoring interfaces")
    osnrs = {i: [] for i in range(0, 13)}
    gosnrs = {i: [] for i in range(0, 13)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'verification_opm'
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        osnrs[key] = opm.get_list_osnr()
        if key == 0:
            gosnrs[key] = opm.get_list_osnr()
        else:
            gosnrs[key] = opm.get_list_gosnr()

    # Retrieve only the channels of interest
    osnr_c46 = []
    for span, _list in osnrs.items():
        osnr_c46.append(_list[45])
    plotting_osnr.append(osnr_c46)

    gosnr_c46 = []
    # plt.plot(x, tmp, color='green', marker='o')
    for span, _list in gosnrs.items():
        gosnr_c46.append(_list[45])
    plotting_gosnr.append(gosnr_c46)

    # Create structure and compute OSNR with the analytical model
    theo = []
    init = osnr_c46[0]
    theo.append(init)
    prev_value = 0
    for i in range(1, 13):
        if i == 6 or i == 12:
            theo.append(prev_value)
        elif i > 6:
            prev_value = p + 58 - 0.22 * 80 - 6 - 10 * np.log10(i - 1)
            theo.append(prev_value)
        else:
            prev_value = p + 58 - 0.22 * 80 - 6 - 10 * np.log10(i)
            theo.append(prev_value)
    plotting_theo.append(theo)

    print("*** Destroying objects")
    del net
    del osnrs
    del gosnrs
    del theo

colors = ['r', 'g', 'b', 'y', 'k']
op = list(np.arange(-4, 6, 2)[::-1])
for o, g, t in zip(plotting_osnr, plotting_gosnr, plotting_theo):
    label = 'Launch power: ' + str(op.pop()) + 'dBm'
    color = colors.pop()
    plt.plot(o, marker='o', color=color)
    plt.plot(g, '--', marker='*', color=color, label=label)
    plt.plot(t, '-.', marker='^', color=color)

plt.ylabel("OSNR/gOSNR (dB)")
plt.xlabel("Spans and hops")
<<<<<<< HEAD
<<<<<<< HEAD
plt.yticks(np.arange(0, 52, 2))
plt.xticks(np.arange(0, 13, 1))
plt.legend(loc=1)
plt.grid(True)
plt.show()
=======
=======
>>>>>>> c2a2354... minor changes for PTL paper
plt.yticks(np.arange(12, 50, 2))
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
plt.savefig('../gosnr_vs_power.eps', format='eps')
# plt.show()
<<<<<<< HEAD
>>>>>>> c2a2354... minor changes for PTL paper
=======
>>>>>>> c2a2354... minor changes for PTL paper

from topo.linear import LinearTopology
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
# figure(num=None, figsize=(7, 6), dpi=256)
# del matplotlib.font_manager.weight_dict['roman']
# matplotlib.font_manager._rebuild()

# plt.rcParams["font.family"] = "Times New Roman"
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


power_levels = list(np.arange(-4, 2, 2))
plotting_osnr = []
plotting_gosnr = []
plotting_theo = []

for p in power_levels:
    print("*** Building Linear network topology for operational power: %s" % p)
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
    wavelength_indexes = range(1, 82)
    roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
    roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_3.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_5.install_switch_rule(1, 1, 100, wavelength_indexes)

    rw = wavelength_indexes
    # Set resources to use and initiate transmission
    resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
    net.transmit(lt_1, roadm_1, resources=resources)

    print("*** Monitoring interfaces")
    osnrs = {i: [] for i in range(1, 17)}
    gosnrs = {i: [] for i in range(1, 17)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'opm_'
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        osnrs[key] = opm.get_list_osnr()
        if key == 1:
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

    an_osnr = []
    for s in range(16):
        t_osnr = p + 58 - 0.22 * 80 - 5.5 - 10 * np.log10(s + 1)
        an_osnr.append(t_osnr)
    plotting_theo.append(an_osnr)

    print("*** Destroying objects")
    del net
    del osnrs
    del gosnrs

colors = ['r', 'g', 'b', 'y', 'k']
op = list(np.arange(-4, 6, 2)[::-1])
for o, g, a in zip(plotting_osnr, plotting_gosnr, plotting_theo):
    l = 'Launch power: ' + str(op.pop()) + 'dBm'
    c = colors.pop()
    plt.plot(o, marker='o', color=c)
    plt.plot(g, '--', marker='x', color=c, label=l, linewidth=2)
    plt.plot(o, marker='v', color='r')

plt.ylabel("OSNR/gOSNR (dB)")
plt.xlabel("Spans and hops")
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
# plt.savefig('../gosnr_vs_power.eps', format='eps')
plt.show()

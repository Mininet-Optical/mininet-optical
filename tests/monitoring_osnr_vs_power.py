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


p_start = -2
p_end = 0
power_levels = list(np.arange(p_start, p_end, 2))
plotting_osnr = []
osnr_per_span = []
osnr_per_span_qot = []
plotting_gosnr = []
plotting_osnr_qot = []
plotting_gosnr_qot = []
plotting_theo = []
rx_gosnr = []
rx_gosnr_qot = []
rx_osnr_qot = []
rx_osnr = []

power_plt = []
power_qot_plt = []
ase_plt = []
ase_qot_plt = []
nli_plt = []
nli_qot_plt = []
num_channels = 89
wavelength_indexes = list(range(1, num_channels + 1))
# index = int(np.floor(len(wavelength_indexes) / 2))
index = 15 - 1
print("Monitoring channel with index: ", index)
# wavelength_indexes.reverse()
# wavelength_indexes = random.sample(range(1, 90), 81)

for p in power_levels:
    # print("*** Building Linear network topology for operational power: %s" % p)
    print("*** Building Linear network topology..." % p)
    net = LinearTopology.build(op=p, non=15)

    lt_1 = net.name_to_node['lt_1']

    roadm_1 = net.name_to_node['roadm_1']
    roadm_2 = net.name_to_node['roadm_2']
    roadm_3 = net.name_to_node['roadm_3']
    roadm_4 = net.name_to_node['roadm_4']
    roadm_5 = net.name_to_node['roadm_5']
    roadm_6 = net.name_to_node['roadm_6']
    roadm_7 = net.name_to_node['roadm_7']
    roadm_8 = net.name_to_node['roadm_8']
    roadm_9 = net.name_to_node['roadm_9']
    roadm_10 = net.name_to_node['roadm_10']
    roadm_11 = net.name_to_node['roadm_11']
    roadm_12 = net.name_to_node['roadm_12']
    roadm_13 = net.name_to_node['roadm_13']
    roadm_14 = net.name_to_node['roadm_14']
    roadm_15 = net.name_to_node['roadm_15']

    # Install switch rules into the ROADM nodes
    # wavelength_indexes = range(1, 82)
    # reversed(wavelength_indexes)
    roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
    roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_3.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_5.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_6.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_7.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_8.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_9.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_10.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_11.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_12.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_13.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_14.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_15.install_switch_rule(1, 1, 100, wavelength_indexes)

    rw = wavelength_indexes
    # Set resources to use and initiate transmission
    resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
    net.transmit(lt_1, roadm_1, resources=resources)

    print("*** Monitoring interfaces...")
    num_opm = 98
    osnrs = {i: [] for i in range(1, num_opm)}
    gosnrs = {i: [] for i in range(1, num_opm)}
    osnrs_qot = {i: [] for i in range(1, num_opm)}
    gosnrs_qot = {i: [] for i in range(1, num_opm)}
    power = {i: [] for i in range(1, num_opm)}
    power_qot = {i: [] for i in range(1, num_opm)}
    ase = {i: [] for i in range(1, num_opm)}
    ase_qot = {i: [] for i in range(1, num_opm)}
    nli = {i: [] for i in range(1, num_opm)}
    nli_qot = {i: [] for i in range(1, num_opm)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'opm_'
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        osnrs[key] = opm.get_list_osnr()
        gosnrs[key] = opm.get_list_gosnr()
        osnrs_qot[key] = opm.get_list_osnr_qot()
        gosnrs_qot[key] = opm.get_list_gosnr_qot()
        power[key] = opm.get_list_power()
        power_qot[key] = opm.get_list_power_qot()

        ase[key] = opm.get_list_ase()
        ase_qot[key] = opm.get_list_ase_qot()

        nli[key] = opm.get_list_nli()
        nli_qot[key] = opm.get_list_nli_qot()

    # Retrieve only the channels of interest
    osnr_cut = []
    for span, _list in osnrs.items():
        osnr_cut.append(_list[index])
        osnr_per_span.append(_list)
        # osnr_cut.append(np.mean(_list))
    plotting_osnr.append(osnr_cut)
    rx_osnr.append(osnr_cut[-1])

    osnr_cut_qot = []
    for span, _list in osnrs_qot.items():
        # gosnr_cut.append(np.mean(_list))
        osnr_cut_qot.append(_list[index])
        osnr_per_span_qot.append(_list)
    plotting_osnr_qot.append(osnr_cut_qot)
    rx_osnr_qot.append(osnr_cut_qot[-1])

    for span, _list in gosnrs.items():
        plotting_gosnr.append(_list)
    for span, _list in gosnrs_qot.items():
        plotting_gosnr_qot.append(_list)

    for span, _list in power.items():
        power_plt.append(_list)
    for span, _list in power_qot.items():
        power_qot_plt.append(_list)

    for span, _list in ase.items():
        ase_plt.append(_list)
    for span, _list in ase_qot.items():
        ase_qot_plt.append(_list)

    for span, _list in nli.items():
        nli_plt.append(_list)
    for span, _list in nli_qot.items():
        nli_qot_plt.append(_list)

    print("*** Destroying objects")
    del net
    del osnrs


i = 0
# a = plotting_osnr[-1]
# b = plotting_osnr_qot[-1]
# plt.plot(a, 'r')
# plt.plot(b, 'b')
colors = ['r', 'b', 'y', 'g', 'r', 'b', 'y', 'g', 'r', 'b', 'y', 'g', 'r', 'b', 'y', 'g', 'r', 'b', 'y', 'g']
color = colors.pop()
c = 0
for _list in plotting_gosnr_qot:
    # print(_list[index])
    i += 1
    if i == 8:
        color = colors.pop()
        i = 1
    c += 1
    if c == 28:
        plt.plot(_list, 'k')
    else:
        plt.plot(_list, color)


# plt.ylabel("OSNR, gOSNR(dashed) (dB)")
# plt.xlabel("Amplifiers")
# plt.yticks(np.arange(18, 40, 2))
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
plt.grid(True)

print("=%=%=%=%=%=%=%")
print(rx_osnr)
print(rx_osnr_qot)
plt.show()

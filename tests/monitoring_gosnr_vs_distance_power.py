from topo.linear import LinearTopology
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
figure(num=None, figsize=(7, 6), dpi=256)
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


power_levels = list(np.arange(-7, 3, 1))
plotting_osnr = {3: [], 7: []}
plotting_gosnr = {3: [], 7: []}
plotting_gosnr_4000 = {3: [], 7: []}
plotting_theo = {3: [], 7: []}


w_num = [3, 7]

for wnm in w_num:
    for p in power_levels:
        print("*** Building Linear network topology for operational power: %s" % p)
        net = LinearTopology.build(op=p, non=2)

        lt_1 = net.name_to_node['lt_1']

        roadm_1 = net.name_to_node['roadm_1']
        roadm_2 = net.name_to_node['roadm_2']

        # Install switch rules into the ROADM nodes
        wavelength_indexes = range(1, wnm)
        roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
        roadm_2.install_switch_rule(1, 1, 100, wavelength_indexes)

        rw = wavelength_indexes
        # Set resources to use and initiate transmission
        resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
        net.transmit(lt_1, roadm_1, resources=resources)

        opm = net.name_to_node['opm_25']
        osnrs = opm.get_list_osnr()
        gosnrs = opm.get_list_gosnr()

        opm = net.name_to_node['opm_48']
        osnrs_4000 = opm.get_list_osnr()
        gosnrs_4000 = opm.get_list_gosnr()

        plotting_osnr[wnm].append(osnrs[int(np.floor(wnm/2))])
        plotting_gosnr[wnm].append(gosnrs[int(np.floor(wnm/2))])
        plotting_gosnr_4000[wnm].append(gosnrs_4000[int(np.floor(wnm/2))])

        # Create structure and compute OSNR with the analytical model
        t_osnr = p + 58 - 0.22 * 80 - 5.5 - 10 * np.log10(48)
        plotting_theo[wnm].append(t_osnr)

        print("*** Destroying objects")
        del net
        del osnrs
        del gosnrs

labs = ['2000km 32ch', '2000km 4ch']
labs2 = ['4000km 32ch', '4000km 4ch']
colors = ['b', 'r']
colors2 = ['k', 'y']
markers = ['*', 'v']
for k in w_num:
    c = colors.pop()
    c2 = colors2.pop()
    lab = labs.pop()
    lab2 = labs2.pop()
    m = markers.pop()
    plt.plot(plotting_gosnr[k], color=c, label=lab, linewidth=2, marker='x')
    plt.plot(plotting_gosnr_4000[k], color=c2, label=lab2, linewidth=2, marker='x')
    # plt.plot(plotting_theo[k])

plt.ylabel("gOSNR (dB)")
plt.xlabel("Launch power (dBm)")
# plt.yticks(np.arange(4, 16, 1))
plt.xticks((range(len(power_levels))), power_levels)
# plt.xticks()
plt.legend(loc='lower left')
plt.grid(True)
# plt.savefig('../gosnr_vs_distance_power.eps', format='eps')
plt.show()

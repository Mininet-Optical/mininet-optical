from topo.linear import LinearTopology
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
# figure(num=None, figsize=(7, 6), dpi=256)
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


power_levels = list(np.arange(-10, 5, 1))
plotting_osnr = {8: [], 64: []}
plotting_gosnr = {8: [], 64: []}


w_num = [8, 64]

for wnm in w_num:
    for p in power_levels:
        print("*** Building Linear network topology for operational power: %s" % p)
        net = LinearTopology.build(op=p)

        lt_1 = net.name_to_node['lt_1']

        roadm_1 = net.name_to_node['roadm_1']
        roadm_2 = net.name_to_node['roadm_2']
        roadm_3 = net.name_to_node['roadm_3']
        # roadm_4 = net.name_to_node['roadm_4']
        # roadm_5 = net.name_to_node['roadm_5']
        # roadm_6 = net.name_to_node['roadm_6']
        # roadm_7 = net.name_to_node['roadm_7']
        # roadm_8 = net.name_to_node['roadm_8']
        # roadm_9 = net.name_to_node['roadm_9']

        # Install switch rules into the ROADM nodes
        wavelength_indexes = range(1, wnm)
        roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
        roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_3.install_switch_rule(1, 1, 100, wavelength_indexes)
        # roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
        # roadm_5.install_switch_rule(1, 1, 102, wavelength_indexes)
        # roadm_6.install_switch_rule(1, 1, 102, wavelength_indexes)
        # roadm_7.install_switch_rule(1, 1, 102, wavelength_indexes)
        # roadm_8.install_switch_rule(1, 1, 102, wavelength_indexes)
        # roadm_9.install_switch_rule(1, 1, 100, wavelength_indexes)

        rw = wavelength_indexes
        # Set resources to use and initiate transmission
        resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
        net.transmit(lt_1, roadm_1, resources=resources)

        opm = net.name_to_node['opm_14']
        osnrs = opm.get_list_osnr()
        gosnrs = opm.get_list_gosnr()

        plotting_osnr[wnm].append(osnrs[int(np.floor(wnm/2))])
        plotting_gosnr[wnm].append(gosnrs[int(np.floor(wnm/2))])

    # Create structure and compute OSNR with the analytical model
    # theo = []
    # init = osnrs[3]
    # theo.append(init)
    # prev_value = 0
    # for i in range(1, 27):
    #     if i % 4 == 0:
    #         theo.append(prev_value)
    #     elif i > 4:
    #         prev_value = p + 58 - 0.22 * 65 - 6 - 10 * np.log10(i - 1)
    #         theo.append(prev_value)
    #     else:
    #         prev_value = p + 58 - 0.22 * 65 - 6 - 10 * np.log10(i)
    #         theo.append(prev_value)
    # plotting_theo.append(theo)

        print("*** Destroying objects")
        del net
        del osnrs
        del gosnrs
        # del theo

# print(plotting_gosnr)
gosnr = {8: [16.98580951843988, 17.954818687511654, 18.894143629647772, 19.776177405621077, 20.550708712672545, 21.133907998446347, 21.406479151438248, 21.24223306699355, 20.572201976837626, 19.432398586260927, 17.937843625090014, 16.215438594172486, 14.361716900160243, 12.437040392190015, 10.475361702604374], 64: [16.997173846282344, 17.9463863558872, 18.84729419095001, 19.656693325789156, 20.300402282215273, 20.66724959047201, 20.627653781480134, 20.090924353392104, 19.064877666909904, 17.65013035933563, 15.976322965034077, 14.14968036334188, 12.239348852780164, 10.285065558954628, 8.308204784858251]}
gosnr2 = {8: [14.014253814292521, 14.983338313422696, 15.922559334246408, 16.804086510110487, 17.577316377616434, 18.157856352638248, 18.425905803409705, 18.255398938940402, 17.578502818866365, 16.432725177908512, 14.93387177168264, 13.208752357978415, 11.353442382978526, 9.427871165109481, 7.465695790723643], 64: [14.025446748646171, 14.974560164767643, 15.875028599823398, 16.6833084380158, 17.324701966285666, 17.687495446342716, 17.64202830163216, 17.098503735917365, 16.066234480362684, 14.646837406493749, 12.97002880051091, 11.141614715018903, 9.230285526671999, 7.275451579783992, 5.298288308231765]}


labs = ['480km 64ch', '480km 8ch']
labs2 = ['960km 64ch', '960km 8ch']
colors = ['b', 'r']
colors2 = ['k', 'y']
markers = ['*', 'v']
for k in w_num:
    c = colors.pop()
    c2 = colors2.pop()
    lab = labs.pop()
    lab2 = labs2.pop()
    m = markers.pop()
    plt.plot(plotting_gosnr[k], color=c, label='OSNR', linewidth=4)
    # plt.plot(gosnr[k], color=c, label=lab, marker=m, linewidth=4)
    # plt.plot(gosnr2[k], color=c2, label=lab2, marker=m, linewidth=4)

plt.ylabel("gOSNR (dB)")
plt.xlabel("Launch power (dBm)")
# plt.yticks(np.arange(4, 16, 1))
plt.xticks((range(len(power_levels))), power_levels)
# plt.xticks()
plt.legend(loc=3)
plt.grid(True)
# plt.savefig('../gosnr_vs_distance_power.eps', format='eps')
plt.show()

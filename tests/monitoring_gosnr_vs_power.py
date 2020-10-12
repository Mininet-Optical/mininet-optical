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


# Define initial and end power levels for the transmission
p_start = -4
p_end = 2
p_step = 2
power_levels = list(np.arange(p_start, p_end, p_step))
# Structures to monitor the OSNR, gOSNR and OSNR-ASE (analytical model)
plotting_osnr = []
plotting_gosnr = []
plotting_analytical = []
# Define number of wavelengths to transmit
num_wavelengths = 81
wavelength_indexes = list(range(1, num_wavelengths + 1))
# Define channel index to monitor (channel under test - cut)
# cut = int(np.floor(len(wavelength_indexes) / 2))
cut = 39
print("*** Monitoring channel with index: ", cut)

for p in power_levels:
    print("*** Building Linear network topology for operational power: %s" % p)
    net = LinearTopology.build(op=p, non=5)

    # Retrieve line terminals (transceivers) from network
    lt_1 = net.name_to_node['lt_1']
    lt_2 = net.name_to_node['lt_2']
    lt_3 = net.name_to_node['lt_3']

    # Retrieve ROADMs from network
    roadm_1 = net.name_to_node['roadm_1']
    roadm_2 = net.name_to_node['roadm_2']
    roadm_3 = net.name_to_node['roadm_3']
    roadm_4 = net.name_to_node['roadm_4']
    roadm_5 = net.name_to_node['roadm_5']

    # Install switch rules into the ROADM nodes
    roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
    roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_3.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
    roadm_5.install_switch_rule(1, 1, 100, wavelength_indexes)

    # Set resources to use and initiate transmission
    tr_labels = ['t%s' % str(x) for x in wavelength_indexes]
    for tr, wavelength in zip(tr_labels, wavelength_indexes):
        resources = {'transceiver': lt_1.name_to_transceivers[tr],
                     'required_wavelengths': [wavelength]}
        outport = 100
        lt_1.transmit(lt_1.name_to_transceivers[tr], outport, [wavelength])

    print("*** Monitoring interfaces")
    # Retrieve number of amplifiers (or monitoring nodes)
    num_amplifiers = int((len(net.amplifiers) / 2) + 1)
    osnrs = {i: [] for i in range(1, num_amplifiers)}
    gosnrs = {i: [] for i in range(1, num_amplifiers)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'opm_'
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        osnrs[key] = opm.get_list_osnr()
        gosnrs[key] = opm.get_list_gosnr()

    # Retrieve only the channels of interest
    osnr_cut = []
    for span, _list in osnrs.items():
        osnr_cut.append(_list[cut])
    plotting_osnr.append(osnr_cut)

    gosnr_cut = []
    for span, _list in gosnrs.items():
        gosnr_cut.append(_list[cut])
    plotting_gosnr.append(gosnr_cut)

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
    print(g)
# Retrieved data from emulator
gosnr_0 = [35.33233577118823, 31.37664820503778, 29.337195864255065, 27.95468662911725,
       27.260088963719397, 26.35274045416481, 25.60277551116353, 24.9633017937713,
       24.602184439802617, 24.085431568092144, 23.62504242642067, 23.20871259522844,
       22.9653910885472, 22.603394605978284, 22.27117344994892, 21.962490381114318]
gosnr_m2 = [33.409092181516876, 29.952722654611506, 28.049563136381686, 26.728610845562347,
            25.907648074249426, 25.057124363613173, 24.345159828032177, 23.732559106857867,
            23.301613338567453, 22.814181577214228, 22.375518798652575, 21.976406329063703,
            21.68427417512917, 21.342462391048294, 21.025412451391507, 20.729400827053006]
gosnr_m4 = [31.458229639468573, 28.122927062557398, 26.25730945682382, 24.955259283403542,
            24.093989132517393, 23.258946820864956, 22.558244501581825, 21.954423438959946,
            21.50157438359468, 21.022141225609445, 20.590050051132263, 20.19667014116184,
            19.889396750962813, 19.55303384554338, 19.240617414522458, 18.948863283716474]
plt.plot(gosnr_0, 'g')
plt.plot(gosnr_m2, 'g')
plt.plot(gosnr_m4, 'g')


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

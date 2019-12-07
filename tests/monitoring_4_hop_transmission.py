"""
    This script will build the Deutsche Telekom topology and run a single
    81-channel transmission with the default configuration of the simulator,
    and will monitor six channels. The latter, will then be plotted.

    For different distances and monitoring points one needs to edit the
    Deutsche Telekom declaration in ../topo/deutsche_telekom.py

    Date: November 11th, 2019

"""


from topo.deutsche_telekom import DeutscheTelekom
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
figure(num=None, figsize=(8, 6), dpi=256)
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


print("*** Building Deutsche Telekom network topology")
net = DeutscheTelekom.build()

lt_koln = net.name_to_node['lt_koln']
lt_munchen = net.name_to_node['lt_munchen']

roadm_koln = net.name_to_node['roadm_koln']
roadm_frankfurt = net.name_to_node['roadm_frankfurt']
roadm_nurnberg = net.name_to_node['roadm_nurnberg']
roadm_munchen = net.name_to_node['roadm_munchen']

# for port, node in roadm_koln.port_to_node_out.items():
#     print("%s reachable through port %s" % (node.name, port))
# for port, node in roadm_koln.port_to_node_in.items():
#     print("roadm_munchen reachable by %s through port %s" % (node.name, port))

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
channels = [1, 16, 31, 46, 61, 76]
osnr_c1 = []
osnr_c16 = []
osnr_c31 = []
osnr_c46 = []
osnr_c61 = []
osnr_c76 = []
gosnr_c1 = []
gosnr_c16 = []
gosnr_c31 = []
gosnr_c46 = []
gosnr_c61 = []
gosnr_c76 = []
for span, _list in osnrs.items():
    osnr_c1.append(_list[0])
    osnr_c16.append(_list[15])
    osnr_c31.append(_list[30])
    osnr_c46.append(_list[45])
    osnr_c61.append(_list[60])
    osnr_c76.append(_list[75])

# plt.plot(x, tmp, color='green', marker='o')
for span, _list in gosnrs.items():
    gosnr_c1.append(_list[0])
    gosnr_c16.append(_list[15])
    gosnr_c31.append(_list[30])
    gosnr_c46.append(_list[45])
    gosnr_c61.append(_list[60])
    gosnr_c76.append(_list[75])

# Create structure and compute OSNR with the analytical model
theo = []
init = osnr_c76[0]
theo.append(init)
for i in range(1, 13):
    # include previous value for hop increments
    theo.append(-2 + 58 - 0.22*80 - 6 - 10*np.log10(i))

# Structures for plotting purposes of OSNR
all_channels_sim = [osnr_c1, osnr_c16, osnr_c31, osnr_c46, osnr_c61, osnr_c76]
# Structures for plotting purposes of gOSNR
all_channels_simg = [gosnr_c1, gosnr_c16, gosnr_c31, gosnr_c46, gosnr_c61, gosnr_c76]

# Just include one label for the OSNR channels
tmp = False
for s in all_channels_sim:
    if not tmp:
        plt.plot(s, color='green', marker='*', label='OSNR-Simulation 6-ch')
        tmp = True
    else:
        plt.plot(s, color='green', marker='*')

# Just include one label for the gOSNR channels
tmp2 = False
for s in all_channels_simg:
    if not tmp2:
        plt.plot(s, '--', color='green', marker='*', label='gOSNR-Simulation 6-ch')
        tmp2 = True
    else:
        plt.plot(s, '--', color='green', marker='*')

# Plot the analytical model
plt.plot(theo, '--', color='red', label="OSNR-Analytical model", marker='o')

plt.ylabel("OSNR/gOSNR (dB)")
plt.xlabel("Spans and hops")
ticks = [str(i) for i in range(0, 13)]
plt.xticks((range(13)), ticks)
# plt.yticks(np.arange(13, 47, 2))
plt.grid(True)
plt.legend()
# Uncomment for showing or saving the plot
plt.show()
# plt.savefig('../figures/4_hop_transmission.eps', format='eps')

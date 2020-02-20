import topo.ofc_demo as OFCDemo
from tests.ofc.failure_recovery.switching_tuples import SwitchTuples as st
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
# figure(num=None, figsize=(9, 6), dpi=256)
# plt.rcParams["font.size"] = 18


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


# build topology
net = OFCDemo.build()

n = net.name_to_node
lt1, lt2, lt3 = [n['lt%d' % i] for i in (1, 2, 3)]
roadm1, roadm2, roadm3 = [n['roadm%d' % i] for i in (1, 2, 3)]
r3_mon = n['mon%d' % 12]
r2_mon = n['mon%d' % 20]

# Install switch rules into the ROADM nodes
channels1 = list(np.arange(1, 11, 1))
channels2 = list(np.arange(11, 21, 1))
channels3 = list(np.arange(21, 31, 1))

proc = st()
proc.switch_main()
for pr in proc.roadm1:
    roadm1.install_switch_rule(**pr)
for pr in proc.roadm2:
    roadm2.install_switch_rule(**pr)
for pr in proc.roadm3:
    roadm3.install_switch_rule(**pr)

rw = channels1 + channels2 + channels3

# Set resources to use and initiate transmission
resources = {'transceiver': lt1.name_to_transceivers['t1'],
             'required_wavelengths': rw}
net.transmit(lt1, roadm1, resources=resources)

# osnr = r3_mon.get_list_osnr()
# _osnr = r2_mon.get_list_osnr()
# net.mock_nf_adjust('amp12', (30, 90), 'roadm1', 'roadm3')
# osnr2 = r3_mon.get_list_osnr()
#
# if np.mean(osnr2) < 20:
#     print("*** deleting rule roadm3")
#     roadm3.delete_switch_rule(1)
#     print("*** installing rule in roadm2")
#     roadm2.install_switch_rule(3, 1, 102, channels1)
#     print("*** installing rule in roadm2")
#     roadm3.install_switch_rule(4, 2, 100, channels1)
#     print("*** updating rule in roadm1")
#     roadm1.update_switch_rule(1, 101)
# # osnr3 = r3_mon.get_list_osnr()
# _osnr2 = r2_mon.get_list_osnr()
#
# # plt.plot(osnr, linewidth=4, color='b', marker='D', markersize=8, markerfacecolor='None', label="Before NF adjustment")
# # plt.plot(osnr2, linewidth=4, color='r', marker='D', markersize=8, markerfacecolor='None', label="After NF adjustment")
# x = range(10, 30)
# plt.plot(x, _osnr, linewidth=4, color='g', marker='D', markersize=8, markerfacecolor='None', label="Before re-routing")
# x2 = range(0, 30)
# plt.plot(x2, _osnr2, linewidth=4, color='y', marker='D', markersize=8, markerfacecolor='None', label="After re-routing")
# # plt.plot(osnr3, color='r')
# plt.title("OSNR levels Link 2")
# plt.xlabel("Channel index")
# plt.ylabel("OSNR (dB)")
# # xticklabel = [str(x) for x in np.arange(1, 31, 5)]
# # plt.xticks(range(len(xticklabel)), xticklabel)
# xticks = []
# i = 0
# while i <= 30:
#     if i % 5 is 0 and i is not 0 or i is 1:
#         xticks.append(i)
#     elif i is 0:
#         pass
#     else:
#         xticks.append('')
#     i += 1
# l = len(xticks)
#
# plt.xticks(np.arange(0, 30, 1), xticks)
# plt.legend()
# plt.savefig('../link2.eps', format='eps')
# plt.show()

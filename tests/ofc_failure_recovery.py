import topo.ofc_demo as OFCDemo
import numpy as np

import matplotlib.pyplot as plt
from tests.switching_tuples import SwitchTuples as st


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

# Install switch rules into the ROADM nodes
channels1 = list(np.arange(1, 11, 1))
channels2 = list(np.arange(11, 21, 1))
channels3 = list(np.arange(21, 31, 1))

proc = st()
proc.switch_proc1()
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

gosnr = r3_mon.get_list_gosnr()
net.mock_nf_adjust('amp12', (5.5, 90), 'roadm1', 'roadm3')
gosnr2 = r3_mon.get_list_gosnr()
# net.mock_nf_adjust('amp11', (10.5, 90), 'roadm1', 'roadm3')
# gosnr3 = r3_mon.get_list_gosnr()
# net.mock_nf_adjust('amp10', (10.5, 90), 'roadm1', 'roadm3')
# gosnr4 = r3_mon.get_list_gosnr()
# net.mock_nf_adjust('amp9', (10.5, 90), 'roadm1', 'roadm3')
# gosnr5 = r3_mon.get_list_gosnr()
# net.mock_nf_adjust('boost9', (10.5, 90), 'roadm1', 'roadm3')
# gosnr6 = r3_mon.get_list_gosnr()

# if np.mean(gosnr3) < 30.0:
#     print("DISRPUTION TIME!")

plt.plot(gosnr, color='b', marker='*')
plt.plot(gosnr2, color='y')
# th = [30.0] * 10
# plt.plot(th, '--', color='k')
# plt.plot(gosnr3, color='r')
# plt.plot(gosnr4, '--', color='r')
# plt.plot(gosnr5, '--', color='r')
# plt.plot(gosnr6, '--', color='r')
plt.show()

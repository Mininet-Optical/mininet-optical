import topo.ofc_demo as OFCDemo
from tests.ofc.switching_tuples import SwitchTuples as st
from tests.ofc.failure_recovery.plot_osnr import plot_osnr, plot_list_osnr
import numpy as np


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


# Setting up 2-main transmission setups
# build topology
net = OFCDemo.build()

n = net.name_to_node
lt1, lt6 = [n['lt%d' % i] for i in (1, 6)]
roadm1, roadm2, roadm3, roadm4, roadm5, roadm6 = [n['roadm%d' % i] for i in (1, 2, 3, 4, 5, 6)]
# Channel sub-sets
channels1 = list(np.arange(1, 11, 1))
channels2 = list(np.arange(11, 21, 1))
channels3 = list(np.arange(21, 31, 1))
channels4 = list(np.arange(31, 41, 1))
channels4 += (list(np.arange(61, 80, 1)))
channels5 = list(np.arange(51, 61, 1))

# Install fixed rules into switches
switch_proc = st()
switch_proc.switch_full()
for pr in switch_proc.roadm1:
    roadm1.install_switch_rule(**pr)
for pr in switch_proc.roadm2:
    roadm2.install_switch_rule(**pr)
for pr in switch_proc.roadm3:
    roadm3.install_switch_rule(**pr)
for pr in switch_proc.roadm4:
    roadm4.install_switch_rule(**pr)
for pr in switch_proc.roadm5:
    roadm5.install_switch_rule(**pr)
for pr in switch_proc.roadm6:
    roadm6.install_switch_rule(**pr)

# Set resources to use and initiate transmission
rw = channels1 + channels2
resources = {'transceiver': lt1.name_to_transceivers['t1'],
             'required_wavelengths': rw}
net.transmit(lt1, roadm1, resources=resources)
rw2 = channels3 + channels4 + channels5
resources2 = {'transceiver': lt6.name_to_transceivers['t1'],
              'required_wavelengths': rw2}
net.transmit(lt6, roadm6, resources=resources2)

margin = 0
r3_r1_mon = n['mon%d' % 16]
osnr_r3_r1 = r3_r1_mon.get_list_gosnr()

r2_r4_mon = n['mon%d' % 28]
osnr_r2_r42 = r2_r4_mon.get_list_gosnr()
osnr_r2_r42_qot = r2_r4_mon.get_list_gosnr_qot()

osnr_r3_r1_qot = r3_r1_mon.get_list_gosnr_qot()
m_osnr_r3_r1_qot = [margin + x for x in osnr_r3_r1_qot]

# plot_list_osnr([osnr_r3_r1, m_osnr_r3_r1_qot])
plot_list_osnr([osnr_r2_r42, osnr_r2_r42_qot])

osnr_diff = [abs(x - y) for x, y in zip(osnr_r3_r1, m_osnr_r3_r1_qot)]
print(osnr_diff)
print(np.mean(osnr_diff))

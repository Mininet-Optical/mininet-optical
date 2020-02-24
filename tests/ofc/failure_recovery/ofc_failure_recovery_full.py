import topo.ofc_demo as OFCDemo
from tests.ofc.switching_tuples import SwitchTuples as st
from tests.ofc.failure_recovery.plot_osnr import plot_list_osnr
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


# Monitoring nodes at the receiver-ends
r2_r4_mon = n['mon%d' % 28]
osnr_r2_r42 = r2_r4_mon.get_list_osnr()

r4_r6_mon = n['mon%d' % 52]
osnr_r4_r6 = r4_r6_mon.get_list_osnr()

# Adjust NF of amplifier in link between R1 and R2, so that
# multiple links break.
# net.mock_nf_adjust('amp3', (30, 90), 'roadm1', 'roadm2')
# net.mock_amp_gain_adjust('amp3', -10, 'roadm1', 'roadm2')
#
# r2_r4_mon = n['mon%d' % 28]
# osnr_r2_r43 = r2_r4_mon.get_list_osnr()
#
# r4_r6_mon = n['mon%d' % 52]
# osnr_r4_r62 = r4_r6_mon.get_list_osnr()
#
# plot_list_osnr([osnr_r4_r6, osnr_r4_r62])
#
# # control procedures for recovery
# roadm6.delete_switch_rule(1)
# roadm5.delete_switch_rule(1)
# roadm4.delete_switch_rule(1)
# roadm4.delete_switch_rule(2)
# roadm2.delete_switch_rule(1)
#
# switch_proc = st()
# switch_proc.recovery_link_r1_r2()
# for pr in switch_proc.roadm3:
#     roadm3.install_switch_rule(**pr)
# for pr in switch_proc.roadm5:
#     roadm5.install_switch_rule(**pr)
# for pr in switch_proc.roadm6:
#     roadm6.install_switch_rule(**pr)
#
# roadm1.update_switch_rule(1, 102)
#
# r3_r5_mon = n['mon%d' % 36]
# osnr_r3_r5 = r3_r5_mon.get_list_osnr()
#
# r5_r6_mon = n['mon%d' % 60]
# osnr_r5_r6 = r5_r6_mon.get_list_osnr()
# # visualise the performance before and after
# plot_list_osnr([osnr_r5_r6])

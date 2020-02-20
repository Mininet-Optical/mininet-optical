import topo.ofc_demo as OFCDemo
from tests.ofc.failure_recovery.switching_tuples import SwitchTuples as st
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

osnr = r3_mon.get_list_osnr()
net.mock_nf_adjust('amp12', (10.5, 90), 'roadm1', 'roadm3')
osnr2 = r3_mon.get_list_osnr()

# if else clause
print("*** deleting rule roadm3")
roadm3.delete_switch_rule(1)
print("*** installing rule in roadm2")
roadm2.install_switch_rule(3, 1, 102, channels1)
print("*** installing rule in roadm2")
roadm3.install_switch_rule(4, 2, 100, channels1)
print("*** updating rule in roadm1")
roadm1.update_switch_rule(1, 101)
osnr3 = r3_mon.get_list_osnr()

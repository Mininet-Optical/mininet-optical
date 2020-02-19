import topo.ofc_demo as OFCDemo
from tests.ofc.failure_recovery.switching_tuples import SwitchTuples as st
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import matplotlib.font_manager


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


def transmit(net, lt, roadm):

    # Install switch rules into the ROADM nodes
    channels1 = list(np.arange(1, 11, 1))
    channels2 = list(np.arange(11, 21, 1))
    channels3 = list(np.arange(21, 31, 1))

    rw = channels1 + channels2 + channels3

    # Set resources to use and initiate transmission
    resources = {'transceiver': lt.name_to_transceivers['t1'],
                 'required_wavelengths': rw}
    net.transmit(lt, roadm, resources=resources)


# if __name__ == '__main__':
# build topology
network = OFCDemo.build()

n = network.name_to_node
lt1, lt2, lt3 = [n['lt%d' % i] for i in (1, 2, 3)]
roadm1, roadm2, roadm3 = [n['roadm%d' % i] for i in (1, 2, 3)]
### Run test(s)
transmit(network, lt1, roadm1)

proc = st()
proc.switch_main()
for pr in proc.roadm1:
    roadm1.install_switch_rule(**pr)
for pr in proc.roadm3:
    roadm3.install_switch_rule(**pr)



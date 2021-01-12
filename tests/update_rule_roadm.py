"""
    This script will build the Ring topology and run a single
    2-channel transmission with the default configuration of the simulator,
    and will monitor their OSNR levels. The latter, will then be plotted.

    Then, one of the signal will be re-routed through different ports, and
    the reconfiguration on the other channels should be automatic through
    the Traffic wrapper.

    Date: November 29th, 2019

"""


from topo.ring_topology import RingTopology
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


print("*** Building Ring network topology")
net = RingTopology.build()

lt_1 = net.name_to_node['lt_1']
lt_2 = net.name_to_node['lt_2']
lt_3 = net.name_to_node['lt_3']

roadm_1 = net.name_to_node['roadm_1']
roadm_2 = net.name_to_node['roadm_2']
roadm_3 = net.name_to_node['roadm_3']

# Install switch rules into the ROADM nodes
wavelength_indexes = [1, 2]
wavelength_indexes2 = [3, 4]
wavelength_indexes3 = [5, 6]
roadm_1.install_switch_rule(1, 0, 102, wavelength_indexes)
roadm_1.install_switch_rule(2, 0, 101, wavelength_indexes2)
roadm_1.install_switch_rule(3, 0, 101, wavelength_indexes3)
roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes2)
roadm_2.install_switch_rule(2, 1, 102, wavelength_indexes3)
roadm_3.install_switch_rule(1, 1, 100, wavelength_indexes)
roadm_3.install_switch_rule(2, 2, 100, wavelength_indexes2)
roadm_3.install_switch_rule(3, 2, 100, wavelength_indexes3)

rw = wavelength_indexes + wavelength_indexes2 + wavelength_indexes3
# Set resources to use and initiate transmission
resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
net.transmit(lt_1, roadm_1, resources=resources)

print("*** Updating switch rule in roadm_1...")
roadm_2.delete_switch_rule(1)
roadm_3.delete_switch_rule(2)
roadm_3.install_switch_rule(4, 1, 100, wavelength_indexes2)
roadm_1.update_switch_rule(2, 102)

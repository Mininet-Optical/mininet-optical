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

# for port, node in roadm_3.port_to_node_out.items():
#     print("%s reachable through port %s" % (node.name, port))
# for port, node in roadm_3.port_to_node_in.items():
#     print("roadm_3 reachable by %s through port %s" % (node.name, port))

# Install switch rules into the ROADM nodes
wavelength_indexes = range(1, 11)
roadm_1.install_switch_rule(1, 0, 102, wavelength_indexes)
roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
roadm_3.install_switch_rule(1, 1, 101, wavelength_indexes)

rw = wavelength_indexes
# Set resources to use and initiate transmission
resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
net.transmit(lt_1, roadm_1, resources=resources)

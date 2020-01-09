"""
    This script verifies the computation of the power excursions
    (EDFA-WDG profile reconfigurations) according to what's been reported
    in: Weiyang Mo, Shengxiang Zhu, Yao Li, and Daniel C. Kilper,
    "Dual-wavelength source based optical circuit switching and wavelength
    reconfiguration in multi-hop ROADM systems," Opt. Express 25, 27736-27749 (2017)
"""
from topo.cian_small_linear import CIANSmallLinear
import numpy as np
import json
from pprint import pprint


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


net = CIANSmallLinear.build()

lt_1 = net.name_to_node['lt_1']

roadm_1 = net.name_to_node['roadm_1']
roadm_2 = net.name_to_node['roadm_2']
roadm_3 = net.name_to_node['roadm_3']
roadm_4 = net.name_to_node['roadm_4']
roadm_5 = net.name_to_node['roadm_5']

# Install switch rules into the ROADM nodes
wavelength_indexes = (50,)
roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
roadm_3.install_switch_rule(1, 1, 102, wavelength_indexes)
roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
roadm_5.install_switch_rule(1, 1, 100, wavelength_indexes)

rw = wavelength_indexes
# Set resources to use and initiate transmission
resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
net.transmit(lt_1, roadm_1, resources=resources)

opm_1 = net.name_to_node['opm_1']
# print(opm_1.amplifier.system_gain)

wavelength_indexes = (72,)
roadm_1.install_switch_rule(2, 0, 101, wavelength_indexes)
roadm_2.install_switch_rule(2, 1, 102, wavelength_indexes)
roadm_3.install_switch_rule(2, 1, 102, wavelength_indexes)
roadm_4.install_switch_rule(2, 1, 102, wavelength_indexes)
roadm_5.install_switch_rule(2, 1, 100, wavelength_indexes)

rw = wavelength_indexes
# Set resources to use and initiate transmission
resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
net.transmit(lt_1, roadm_1, resources=resources)

# print(opm_1.amplifier.system_gain)

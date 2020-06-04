from topo.linear import LinearTopology
import numpy as np
import json
import os
from pprint import pprint
import random


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


# This won't run unless modified
test_run = 1
while test_run <= 300:
    print("*** Running for test %d" % test_run)
    test_id = 't' + str(test_run)
    # different wavelength loads corresponding
    # to 30, 60 and 90 % of wavelength capacity
    j = 0
    _load = [27, 54, 81]
    while j < 3:
        load = _load[j]
        load_id = str(load)
        net = LinearTopology.build(op=0, non=27)

        lt_1 = net.name_to_node['lt_1']

        roadm_1 = net.name_to_node['roadm_1']
        roadm_2 = net.name_to_node['roadm_2']
        roadm_3 = net.name_to_node['roadm_3']
        roadm_4 = net.name_to_node['roadm_4']
        roadm_5 = net.name_to_node['roadm_5']
        roadm_6 = net.name_to_node['roadm_6']
        roadm_7 = net.name_to_node['roadm_7']
        roadm_8 = net.name_to_node['roadm_8']
        roadm_9 = net.name_to_node['roadm_9']
        roadm_10 = net.name_to_node['roadm_10']
        roadm_11 = net.name_to_node['roadm_11']
        roadm_12 = net.name_to_node['roadm_12']
        roadm_13 = net.name_to_node['roadm_13']
        roadm_14 = net.name_to_node['roadm_14']
        roadm_27 = net.name_to_node['roadm_27']

        # Install switch rules into the ROADM nodes
        # wavelength_indexes = list(range(1, load + 1))
        wavelength_indexes = random.sample(range(1, 82), load)
        roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
        roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_3.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_5.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_6.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_7.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_8.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_9.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_10.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_11.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_12.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_13.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_14.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_27.install_switch_rule(1, 1, 100, wavelength_indexes)

        rw = wavelength_indexes
        # Set resources to use and initiate transmission
        resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
        net.transmit(lt_1, roadm_1, resources=resources)

        for opm_id in range(1, 99):
            json_struct = {'tests': []}
            json_struct_qot = {'tests_qot': []}
            opm_name = 'opm_' + str(opm_id)
            opm = net.name_to_node[opm_name]
            osnrs = opm.get_list_osnr()
            gosnrs = opm.get_list_gosnr()

            _osnr_id = 'osnr_load_' + load_id
            _gosnr_id = 'gosnr_load_' + load_id
            json_struct['tests'].append({_osnr_id: osnrs})
            json_struct['tests'].append({_gosnr_id: gosnrs})

            osnrs_qot = opm.get_list_osnr_qot()
            gosnrs_qot = opm.get_list_gosnr_qot()

            _osnr_id_qot = 'osnr_load_qot_' + load_id
            _gosnr_id_qot = 'gosnr_load_qot_' + load_id
            json_struct_qot['tests_qot'].append({_osnr_id_qot: osnrs_qot})
            json_struct_qot['tests_qot'].append({_gosnr_id_qot: gosnrs_qot})

            test = '../../metrics-monitor/'
            # dir_ = test + 'opm-sim-m14/' + opm_name
            # dir_2 = test + 'opm-sim-qot-m14/' + opm_name
            dir_ = test + 'opm-sim-no-m/' + opm_name
            dir_2 = test + 'opm-sim-qot-no-m/' + opm_name
            if not os.path.exists(dir_) and not os.path.exists(dir_2):
                os.makedirs(dir_)
                os.makedirs(dir_2)
            json_file_name = dir_ + '/' + test_id + '_' + str(load_id) + '.json'
            with open(json_file_name, 'w+') as outfile:
                json.dump(json_struct, outfile)

            json_file_name_2 = dir_2 + '/' + test_id + '_' + str(load_id) + '.json'
            with open(json_file_name_2, 'w+') as outfile2:
                json.dump(json_struct_qot, outfile2)

        j += 1
    test_run += 1

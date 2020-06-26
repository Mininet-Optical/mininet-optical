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


# optionally: retrieve WDG seed to pass to EDFAs
# this seed is created with the wdg_seed.py script
# currently in my computer at utils/
with open('seeds/wdg_seed.txt', 'r') as f:
    lines = f.readlines()
wdg_seeds = []
for line in lines:
    wdg_seed = line.split(',')
    wdg_seed[-1] = wdg_seed[-1][:-1]
    wdg_seeds.append(wdg_seed)

loadings = {9: [], 27: [], 81: []}
for ch_key in loadings.keys():
    load_str = 'seeds/channel_loading_seed_' + str(ch_key) + '.txt'
    with open(load_str, 'r') as f:
        lines = f.readlines()
    for line in lines:
        ch_load = line.split(',')
        ch_load[-1] = ch_load[-1][:-1]
        loadings[ch_key].append([int(x) for x in ch_load])

# loadings = {9: [32,48,81,89,50,47,59,86,2], 27: [26,64,1,85,60,37,73,74,16,6,19,34,84,54,21,89,88,52,55,10,45,78,12,40,82,3,59], 81: [45,61,18,64,56,69,31,52,80,76,10,8,86,33,67,44,21,34,40,4,70,25,48,87,83,62,88,49,66,57,1,79,59,7,32,5,54,29,17,50,75,19,41,60,65,72,55,3,38,37,68,28,13,42,77,81,84,63,39,43,20,9,85,78,47,35,82,71,73,6,58,11,2,16,27,14,89,26,51,24,23]}

# This won't run unless modified
test_run = 1
while test_run <= 5:
    print("*** Running for test %d" % test_run)
    test_id = 't' + str(test_run)
    # different wavelength loads corresponding
    # to 30, 60 and 90 % of wavelength capacity
    j = 0
    _load = [9, 27, 81]
    while j < 3:
        load = _load[j]
        load_id = str(load)
        # with seed
        net = LinearTopology.build(op=-2, non=15, wdg_seed=wdg_seeds[test_run-1].copy())
        # without seed
        # net = LinearTopology.build(op=-2, non=15, wdg_seed=None)

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
        roadm_15 = net.name_to_node['roadm_15']

        # Install switch rules into the ROADM nodes
        # wavelength_indexes = loadings[load]
        wavelength_indexes = loadings[load][test_run-1]
        # wavelength_indexes = list(range(1, load + 1))
        # wavelength_indexes = random.sample(range(1, 82), load)
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
        roadm_15.install_switch_rule(1, 1, 100, wavelength_indexes)

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
            # dir_ = test + 'opm-sim-m7/' + opm_name
            # dir_2 = test + 'opm-sim-qot-m7/' + opm_name
            # dir_ = test + 'opm-sim-m14/' + opm_name
            # dir_2 = test + 'opm-sim-qot-m14/' + opm_name
            # dir_ = test + 'opm-sim-m28/' + opm_name
            # dir_2 = test + 'opm-sim-qot-m28/' + opm_name
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

from estimation_module import *
import json
import os


def keys_to_int(_dict):
    return {int(k): i for k, i in _dict.items()}


def keys_to_str(_dict):
    return {str(k): i for k, i in _dict.items()}


monitor_keys = [
        'r1-r2-boost', 'r1-r2-amp1-monitor', 'r1-r2-amp2-monitor', 'r1-r2-amp3-monitor', 'r1-r2-amp4-monitor',
        'r1-r2-amp5-monitor', 'r1-r2-amp6-monitor', 'r2-r3-boost', 'r2-r3-amp1-monitor', 'r2-r3-amp2-monitor',
        'r2-r3-amp3-monitor', 'r2-r3-amp4-monitor', 'r2-r3-amp5-monitor', 'r2-r3-amp6-monitor', 'r3-r4-boost',
        'r3-r4-amp1-monitor', 'r3-r4-amp2-monitor', 'r3-r4-amp3-monitor', 'r3-r4-amp4-monitor', 'r3-r4-amp5-monitor',
        'r3-r4-amp6-monitor', 'r4-r5-boost', 'r4-r5-amp1-monitor', 'r4-r5-amp2-monitor', 'r4-r5-amp3-monitor',
        'r4-r5-amp4-monitor', 'r4-r5-amp5-monitor', 'r4-r5-amp6-monitor', 'r5-r6-boost', 'r5-r6-amp1-monitor',
        'r5-r6-amp2-monitor', 'r5-r6-amp3-monitor', 'r5-r6-amp4-monitor', 'r5-r6-amp5-monitor', 'r5-r6-amp6-monitor',
        'r6-r7-boost', 'r6-r7-amp1-monitor', 'r6-r7-amp2-monitor', 'r6-r7-amp3-monitor', 'r6-r7-amp4-monitor',
        'r6-r7-amp5-monitor', 'r6-r7-amp6-monitor', 'r7-r8-boost', 'r7-r8-amp1-monitor', 'r7-r8-amp2-monitor',
        'r7-r8-amp3-monitor', 'r7-r8-amp4-monitor', 'r7-r8-amp5-monitor', 'r7-r8-amp6-monitor', 'r8-r9-boost',
        'r8-r9-amp1-monitor', 'r8-r9-amp2-monitor', 'r8-r9-amp3-monitor', 'r8-r9-amp4-monitor', 'r8-r9-amp5-monitor',
        'r8-r9-amp6-monitor', 'r9-r10-boost', 'r9-r10-amp1-monitor', 'r9-r10-amp2-monitor', 'r9-r10-amp3-monitor',
        'r9-r10-amp4-monitor', 'r9-r10-amp5-monitor', 'r9-r10-amp6-monitor', 'r10-r11-boost', 'r10-r11-amp1-monitor',
        'r10-r11-amp2-monitor', 'r10-r11-amp3-monitor', 'r10-r11-amp4-monitor', 'r10-r11-amp5-monitor',
        'r10-r11-amp6-monitor', 'r11-r12-boost', 'r11-r12-amp1-monitor', 'r11-r12-amp2-monitor',
        'r11-r12-amp3-monitor', 'r11-r12-amp4-monitor', 'r11-r12-amp5-monitor', 'r11-r12-amp6-monitor',
        'r12-r13-boost', 'r12-r13-amp1-monitor', 'r12-r13-amp2-monitor', 'r12-r13-amp3-monitor',
        'r12-r13-amp4-monitor', 'r12-r13-amp5-monitor', 'r12-r13-amp6-monitor', 'r13-r14-boost',
        'r13-r14-amp1-monitor', 'r13-r14-amp2-monitor', 'r13-r14-amp3-monitor', 'r13-r14-amp4-monitor',
        'r13-r14-amp5-monitor', 'r13-r14-amp6-monitor', 'r14-r15-boost', 'r14-r15-amp1-monitor',
        'r14-r15-amp2-monitor', 'r14-r15-amp3-monitor', 'r14-r15-amp4-monitor', 'r14-r15-amp5-monitor',
        'r14-r15-amp6-monitor'
    ]

# locations of the json files
root_dir = '../../data/sequential-loading/'
opm_dir = 'opm-all/'
opm_path = root_dir + opm_dir

# only save the random values per load
gosnr_opm_dict = dict.fromkeys(monitor_keys)
power_opm_dict = dict.fromkeys(monitor_keys)
ase_opm_dict = dict.fromkeys(monitor_keys)
nli_opm_dict = dict.fromkeys(monitor_keys)
# save all records for the random case comparison
for key in monitor_keys:
    gosnr_opm_dict[key] = {9: {}, 27: {}, 81: {}}
    power_opm_dict[key] = {9: {}, 27: {}, 81: {}}
    ase_opm_dict[key] = {9: {}, 27: {}, 81: {}}
    nli_opm_dict[key] = {9: {}, 27: {}, 81: {}}

for opm_key in monitor_keys:
    # enter the folder and locate the files
    opm_mon_path = opm_path + opm_key
    files = os.listdir(opm_mon_path)

    for filename in files:
        if filename.endswith(".json"):
            # there are 150 files per load (450 iterations).
            file_path = opm_mon_path + '/' + filename
            name_split = filename.split('_')
            test_id = int(name_split[0])
            name_split = name_split[1].split('.')
            load = int(name_split[0])

            gosnr_label = 'gosnr_load_' + str(load)

            power_label = 'power_load_' + str(load)
            ase_label = 'ase_load_' + str(load)
            nli_label = 'nli_load_' + str(load)

            with open(file_path) as json_file:
                f = json.load(json_file)
            json_items = list(f.items())
            metric_items = json_items[0][1]
            gosnr_dict = metric_items[1]
            power_dict = metric_items[2]
            ase_dict = metric_items[3]
            nli_dict = metric_items[4]

            gosnr_opm = gosnr_dict[gosnr_label]
            power_opm = power_dict[power_label]
            ase_opm = ase_dict[ase_label]
            nli_opm = nli_dict[nli_label]
            # record gosnr estimation per load
            gosnr_opm_dict[opm_key][load][test_id] = gosnr_opm
            power_opm_dict[opm_key][load][test_id] = power_opm
            ase_opm_dict[opm_key][load][test_id] = ase_opm
            nli_opm_dict[opm_key][load][test_id] = nli_opm


def obsolete(load, signals_id=None):
    # initialize signal structures
    if signals_id:
        signals_id = [int(x) for x in signals_id]
    main_struct = build_struct(load, signal_ids=signals_id)
    # store gosnr values at each OPM
    gosnr_correct = []

    # determines the node intervals
    m = 1
    test_id = 0
    opm_index = 6

    for i in range(14):
        # run estimation for 6 span x m
        _, estimation_gosnr_log = estimation_module_dyn(main_struct, m)

        opm_key = monitor_keys[opm_index]

        gosnr_dict = keys_to_int(gosnr_opm_dict[opm_key][load][test_id])
        #  correction point
        estimation_gosnr_log[-1] = gosnr_dict
        for _list in estimation_gosnr_log:
            gosnr_correct.append(_list)

        power_dict = keys_to_int(power_opm_dict[opm_key][load][test_id])
        ase_dict = keys_to_int(ase_opm_dict[opm_key][load][test_id])
        nli_dict = keys_to_int(nli_opm_dict[opm_key][load][test_id])

        main_struct = power_dict.keys(), power_dict, ase_dict, nli_dict
        opm_index += 7
    return gosnr_correct


def get_corrected_struct(load, signals_id=None):
    gosnr_corr_dict = dict.fromkeys(monitor_keys)

    for key in monitor_keys:
        gosnr_corr_dict[key] = {9: {}, 27: {}, 81: {}}

    for test_id in range(50):
        prev_opm_index = 0
        opm_index = 7

        # initialize signal structures
        if signals_id:
            signals_id = [int(x) for x in signals_id]
        main_struct = build_struct(load, signal_ids=signals_id)
        for i in range(14):
            m = 1
            opm_key = monitor_keys[opm_index - 1]
            # run estimation for 6 span x m
            _, estimation_gosnr_log = estimation_module_dyn(main_struct, m)

            gosnr_dict = keys_to_int(gosnr_opm_dict[opm_key][load][test_id])

            #  correction point
            estimation_gosnr_log[-1] = gosnr_dict
            # store in dict
            tmp_m_keys = monitor_keys[prev_opm_index:opm_index]
            for i, mk in enumerate(tmp_m_keys):
                gosnr_corr_dict[mk][load][test_id] = keys_to_str(estimation_gosnr_log[i])

            power_dict = keys_to_int(power_opm_dict[opm_key][load][test_id])
            ase_dict = keys_to_int(ase_opm_dict[opm_key][load][test_id])
            nli_dict = keys_to_int(nli_opm_dict[opm_key][load][test_id])

            main_struct = power_dict.keys(), power_dict, ase_dict, nli_dict
            prev_opm_index = opm_index
            opm_index += 7
    return gosnr_corr_dict



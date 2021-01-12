from sdn_monitor_qot_e.estimation_module import *
import json
import os
import numpy as np
from sklearn import preprocessing
import matplotlib.pyplot as plt



def keys_to_int(_dict):
    return {int(k): i for k, i in _dict.items()}


def keys_to_str(_dict):
    return {str(k): i for k, i in _dict.items()}


def db_to_abs(db_value):
    """
    :param db_value: list or float
    :return: Convert dB to absolute value
    """
    absolute_value = 10 ** (db_value / float(10))
    return absolute_value


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10 * np.log10(absolute_value)
    return db_value


# dummy boolean
tmp_bool = False
if tmp_bool:

    monitor_keys = [
            'r1-r2-boost-monitor', 'r1-r2-amp1-monitor', 'r1-r2-amp2-monitor', 'r1-r2-amp3-monitor', 'r1-r2-amp4-monitor',
            'r1-r2-amp5-monitor', 'r1-r2-amp6-monitor', 'r2-r3-boost-monitor', 'r2-r3-amp1-monitor', 'r2-r3-amp2-monitor',
            'r2-r3-amp3-monitor', 'r2-r3-amp4-monitor', 'r2-r3-amp5-monitor', 'r2-r3-amp6-monitor', 'r3-r4-boost-monitor',
            'r3-r4-amp1-monitor', 'r3-r4-amp2-monitor', 'r3-r4-amp3-monitor', 'r3-r4-amp4-monitor', 'r3-r4-amp5-monitor',
            'r3-r4-amp6-monitor', 'r4-r5-boost-monitor', 'r4-r5-amp1-monitor', 'r4-r5-amp2-monitor', 'r4-r5-amp3-monitor',
            'r4-r5-amp4-monitor', 'r4-r5-amp5-monitor', 'r4-r5-amp6-monitor', 'r5-r6-boost-monitor', 'r5-r6-amp1-monitor',
            'r5-r6-amp2-monitor', 'r5-r6-amp3-monitor', 'r5-r6-amp4-monitor', 'r5-r6-amp5-monitor', 'r5-r6-amp6-monitor',
            'r6-r7-boost-monitor', 'r6-r7-amp1-monitor', 'r6-r7-amp2-monitor', 'r6-r7-amp3-monitor', 'r6-r7-amp4-monitor',
            'r6-r7-amp5-monitor', 'r6-r7-amp6-monitor', 'r7-r8-boost-monitor', 'r7-r8-amp1-monitor', 'r7-r8-amp2-monitor',
            'r7-r8-amp3-monitor', 'r7-r8-amp4-monitor', 'r7-r8-amp5-monitor', 'r7-r8-amp6-monitor', 'r8-r9-boost-monitor',
            'r8-r9-amp1-monitor', 'r8-r9-amp2-monitor', 'r8-r9-amp3-monitor', 'r8-r9-amp4-monitor', 'r8-r9-amp5-monitor',
            'r8-r9-amp6-monitor', 'r9-r10-boost-monitor', 'r9-r10-amp1-monitor', 'r9-r10-amp2-monitor', 'r9-r10-amp3-monitor',
            'r9-r10-amp4-monitor', 'r9-r10-amp5-monitor', 'r9-r10-amp6-monitor', 'r10-r11-boost-monitor', 'r10-r11-amp1-monitor',
            'r10-r11-amp2-monitor', 'r10-r11-amp3-monitor', 'r10-r11-amp4-monitor', 'r10-r11-amp5-monitor',
            'r10-r11-amp6-monitor', 'r11-r12-boost-monitor', 'r11-r12-amp1-monitor', 'r11-r12-amp2-monitor',
            'r11-r12-amp3-monitor', 'r11-r12-amp4-monitor', 'r11-r12-amp5-monitor', 'r11-r12-amp6-monitor',
            'r12-r13-boost-monitor', 'r12-r13-amp1-monitor', 'r12-r13-amp2-monitor', 'r12-r13-amp3-monitor',
            'r12-r13-amp4-monitor', 'r12-r13-amp5-monitor', 'r12-r13-amp6-monitor', 'r13-r14-boost-monitor',
            'r13-r14-amp1-monitor', 'r13-r14-amp2-monitor', 'r13-r14-amp3-monitor', 'r13-r14-amp4-monitor',
            'r13-r14-amp5-monitor', 'r13-r14-amp6-monitor', 'r14-r15-boost-monitor', 'r14-r15-amp1-monitor',
            'r14-r15-amp2-monitor', 'r14-r15-amp3-monitor', 'r14-r15-amp4-monitor', 'r14-r15-amp5-monitor',
            'r14-r15-amp6-monitor'
        ]

    # locations of the json files
    # root_dir = '../../data/sequential-loading/'
    root_dir = 'metrics-monitor/'
    opm_dir = 'opm-all/'
    opm_path = root_dir + opm_dir

    # only save the random values per load
    osnr_opm_dict = dict.fromkeys(monitor_keys)
    gosnr_opm_dict = dict.fromkeys(monitor_keys)
    power_opm_dict = dict.fromkeys(monitor_keys)
    ase_opm_dict = dict.fromkeys(monitor_keys)
    nli_opm_dict = dict.fromkeys(monitor_keys)
    # save all records for the random case comparison
    for key in monitor_keys:
        osnr_opm_dict[key] = {9: {}, 27: {}, 81: {}}
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

                osnr_label = 'osnr_load_' + str(load)
                gosnr_label = 'gosnr_load_' + str(load)

                power_label = 'power_load_' + str(load)
                ase_label = 'ase_load_' + str(load)
                nli_label = 'nli_load_' + str(load)

                with open(file_path) as json_file:
                    f = json.load(json_file)
                json_items = list(f.items())
                metric_items = json_items[0][1]
                osnr_dict = metric_items[0]
                gosnr_dict = metric_items[1]
                power_dict = metric_items[2]
                ase_dict = metric_items[3]
                nli_dict = metric_items[4]

                osnr_opm = osnr_dict[osnr_label]
                gosnr_opm = gosnr_dict[gosnr_label]
                power_opm = power_dict[power_label]
                ase_opm = ase_dict[ase_label]
                nli_opm = nli_dict[nli_label]
                # record gosnr estimation per load
                osnr_opm_dict[opm_key][load][test_id] = osnr_opm
                gosnr_opm_dict[opm_key][load][test_id] = gosnr_opm
                power_opm_dict[opm_key][load][test_id] = power_opm
                ase_opm_dict[opm_key][load][test_id] = ase_opm
                nli_opm_dict[opm_key][load][test_id] = nli_opm


def get_corrected_struct(load, signals_id=None):
    gosnr_corr_dict = dict.fromkeys(monitor_keys)

    for key in monitor_keys:
        gosnr_corr_dict[key] = {9: {}, 27: {}, 81: {}}

    for test_id in range(150):
        # iterate through the number of files
        prev_opm_index = 0  # initial loc of monitors
        opm_index = 14  # initial step

        # initialize signal structures
        if signals_id:
            signals_id = [int(x) for x in signals_id]
        main_struct = build_struct(load, signal_ids=signals_id)
        for i in range(7):
            m = 2
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
            opm_index += 14
    return gosnr_corr_dict


def get_corrected_struct_ran(load, gosnr_corr_dict, signals_id=None, test_id=None):
    # gosnr_corr_dict = dict.fromkeys(monitor_keys)
    #
    # for key in monitor_keys:
    #     gosnr_corr_dict[key] = {9: {}, 27: {}, 81: {}}

    # iterate through the number of files
    prev_opm_index = 0  # initial loc of monitors
    opm_index = 14  # initial step

    # initialize signal structures
    if signals_id:
        signals_id = [int(x) for x in signals_id]
    main_struct = build_struct(load, signal_ids=signals_id)
    for i in range(7):
        m = 2
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
        opm_index += 14
    return gosnr_corr_dict


def get_corrected_struct_approx(load, signals_id=None):
    gosnr_corr_dict = dict.fromkeys(monitor_keys)

    for key in monitor_keys:
        gosnr_corr_dict[key] = {9: {}, 27: {}, 81: {}}

    for test_id in range(10):
        # iterate through the number of files
        prev_opm_index = 0  # initial loc of monitors
        opm_index = 7  # initial step

        # initialize signal structures
        if signals_id:
            signals_id = [int(x) for x in signals_id]
        main_struct = build_struct(load, signal_ids=signals_id)
        for i in range(14):
            m = 1
            opm_key = monitor_keys[opm_index - 1]
            # run estimation for 6 span x m
            estimation_osnr_log, estimation_gosnr_log, power, ase, nli = estimation_module_approx(main_struct, m)

            #  correction point
            # get the osnr from ground truth (monitoring point)
            osnr_dict = keys_to_int(osnr_opm_dict[opm_key][load][test_id])
            # get the osnr from estimation (at monitoring point)
            osnr_est_log = estimation_osnr_log[-1]
            # compute and apply to NLI noise the correction factor based
            # on the OSNR difference
            nli = nli_correction_algorithm(osnr_dict, osnr_est_log, nli)
            # modify the last entry from the estimated osnr
            estimation_gosnr_log[-1] = correct_gosnr(power, ase, nli)
            # store in dict
            tmp_m_keys = monitor_keys[prev_opm_index:opm_index]
            for i, mk in enumerate(tmp_m_keys):
                gosnr_corr_dict[mk][load][test_id] = keys_to_str(estimation_gosnr_log[i])

            power_dict = keys_to_int(power_opm_dict[opm_key][load][test_id])
            ase_dict = keys_to_int(ase_opm_dict[opm_key][load][test_id])

            main_struct = power_dict.keys(), power_dict, ase_dict, nli
            prev_opm_index = opm_index
            opm_index += 7
    return gosnr_corr_dict


def get_spans_and_channels_from_link_key(link_key):
    dist_dict = {('amsterdam', 'london'): 390, ('london', 'amsterdam'): 390, ('amsterdam', 'brussels'): 200,
                 ('brussels', 'amsterdam'): 200, ('amsterdam', 'luxembourg'): 310, ('luxembourg', 'amsterdam'): 310,
                 ('amsterdam', 'berlin'): 600, ('berlin', 'amsterdam'): 600, ('amsterdam', 'copenhagen'): 750,
                 ('copenhagen', 'amsterdam'): 750, ('berlin', 'copenhagen'): 400, ('copenhagen', 'berlin'): 400,
                 ('berlin', 'paris'): 900, ('paris', 'berlin'): 900, ('berlin', 'prague'): 320,
                 ('prague', 'berlin'): 320,
                 ('berlin', 'vienna'): 710, ('vienna', 'berlin'): 710, ('brussels', 'london'): 340,
                 ('london', 'brussels'): 340,
                 ('brussels', 'paris'): 270, ('paris', 'brussels'): 270, ('brussels', 'milan'): 850,
                 ('milan', 'brussels'): 850,
                 ('brussels', 'luxembourg'): 100, ('luxembourg', 'brussels'): 100, ('copenhagen', 'london'): 1000,
                 ('london', 'copenhagen'): 1000, ('copenhagen', 'prague'): 760, ('prague', 'copenhagen'): 760,
                 ('london', 'paris'): 410, ('paris', 'london'): 410, ('luxembourg', 'paris'): 370,
                 ('paris', 'luxembourg'): 370,
                 ('luxembourg', 'zurich'): 440, ('zurich', 'luxembourg'): 440, ('luxembourg', 'prague'): 900,
                 ('prague', 'luxembourg'): 900, ('milan', 'paris'): 810, ('paris', 'milan'): 810,
                 ('milan', 'zurich'): 100,
                 ('zurich', 'milan'): 100, ('milan', 'vienna'): 720, ('vienna', 'milan'): 720, ('paris', 'zurich'): 590,
                 ('zurich', 'paris'): 590, ('prague', 'zurich'): 100, ('zurich', 'prague'): 100,
                 ('prague', 'vienna'): 350,
                 ('vienna', 'prague'): 350, ('vienna', 'zurich'): 710, ('zurich', 'vienna'): 710,('hop1', 'hop2'): 50, ('hop2', 'hop1'): 50, ('hop2', 'hop3'): 50, ('hop3', 'hop2'): 50, ('hop3', 'hop4'): 50, ('hop4', 'hop3'): 50, ('hop4', 'hop5'): 50, ('hop5', 'hop4'): 50, ('hop5', 'hop6'): 50, ('hop6', 'hop5'): 50, ('hop6', 'hop7'): 50, ('hop7', 'hop6'): 50, ('hop7', 'hop8'): 50, ('hop8', 'hop7'): 50, ('hop8', 'hop9'): 50, ('hop9', 'hop8'): 50}



    """if link_key == 'r_london-r_copenhagen':
        return [50.0] * 20, range(1, 16)
    elif link_key == 'r_copenhagen-r_berlin':
        return [50.0] * 8, range(1, 16)
    elif link_key == 'r_paris-r_berlin':
        return [50.0] * 18, range(16, 31)
    elif link_key == 'r_prague-r_vienna':
        return [50.0] * 7, range(31, 46)
    else:"""
    step = 50
    stripped_name = link_key
    node_list = link_key.split('-')
    node_list = [node_list[i].strip('r_') for i in range(0, len(node_list))]
    no_monitors = round(dist_dict[(node_list[0], node_list[1])] / step)
    return [50.0] * no_monitors, [1,2,3,4,5,6,7,8,73,74,75,85,86]


def get_opm_struct(link_key, monitors):
    # locations of the json files
    _opm_path = 'cost239-monitor/monitor-module-new/' + link_key + '/'

    osnr_opm_dict = dict.fromkeys(monitors)
    gosnr_opm_dict = dict.fromkeys(monitors)
    power_opm_dict = dict.fromkeys(monitors)
    ase_opm_dict = dict.fromkeys(monitors)
    nli_opm_dict = dict.fromkeys(monitors)

    files = os.listdir(_opm_path)

    for filename in files:
        if filename.endswith(".json"):
            file_path = _opm_path + filename
            monitor_name = filename.split('.')[0]

            osnr_label = 'osnr'
            gosnr_label = 'gosnr'

            power_label = 'power'
            ase_label = 'ase'
            nli_label = 'nli'

            with open(file_path) as json_file:
                f = json.load(json_file)
            json_items = list(f.items())
            metric_items = json_items[0][1]
            osnr_dict = metric_items[0]
            gosnr_dict = metric_items[1]
            power_dict = metric_items[2]
            ase_dict = metric_items[3]
            nli_dict = metric_items[4]

            osnr_opm = osnr_dict[osnr_label]
            gosnr_opm = gosnr_dict[gosnr_label]
            power_opm = power_dict[power_label]
            ase_opm = ase_dict[ase_label]
            nli_opm = nli_dict[nli_label]
            # record gosnr estimation per load
            osnr_opm_dict[monitor_name] = osnr_opm
            gosnr_opm_dict[monitor_name] = gosnr_opm
            power_opm_dict[monitor_name] = power_opm
            ase_opm_dict[monitor_name] = ase_opm
            nli_opm_dict[monitor_name] = nli_opm

    return osnr_opm_dict, gosnr_opm_dict, power_opm_dict, ase_opm_dict, nli_opm_dict

total_monitor_list = []
def get_corrected_struct_simpledemo(link_key, monitors, monitors_by_density, main_struct=None,monitored_nli=False):
    osnr_opm_dict, gosnr_opm_dict, power_opm_dict, ase_opm_dict, nli_opm_dict = get_opm_struct(link_key, monitors)


    gosnr_corr_dict = dict.fromkeys(monitors, {})

    spans, channels = get_spans_and_channels_from_link_key(link_key)
    spans.insert(0, 0)  # to comply with monitors length

    monitor_count = 0
    for i, (span, monitor) in enumerate(zip(spans, monitors)):
        if i == 0:
            # the first span does not matter because is booster
            est_osnr, est_gosnr, power, ase, nli = \
                estimation_module_simpledemo_correct(main_struct, span, first=True)
        else:
            est_osnr, est_gosnr, power, ase, nli = \
                estimation_module_simpledemo_correct(main_struct, span)

        if len(monitors_by_density) == 4 and 'r_london-r_copenhagen-amp7' in str(monitor):
            if False:
                fig = plt.figure(55)
                """plt.plot(list(nli.keys()), list(nli.values()), '--', markeredgewidth=3, markersize=9,
                          markerfacecolor='None',
                          color='r', marker='o',label="Corrected-ASE")
                 #plt.ylabel("Corrected NLI Value")
                plt.plot(list(nli.keys()), list(keys_to_int(nli_opm_dict[monitor]).values()), '--', markeredgewidth=3,
                          markersize=9, markerfacecolor='None',
                          color='b', marker='x',label="Monitored-ASE")"""
                plt.plot(list(nli.keys()), list(nli.values()), '--', markeredgewidth=3, markersize=9,
                         markerfacecolor='None',
                         color='r', marker='o', label="Estimated-NLI")
                # plt.ylabel("Corrected NLI Value")
                plt.plot(list(nli.keys()), list(keys_to_int(nli_opm_dict[monitor]).values()), '--', markeredgewidth=3,
                         markersize=9, markerfacecolor='None',
                         color='b', marker='x', label="Monitored-NLI")

                plt.ylabel("NLI Absolute Value")
                plt.xlabel("Channels")
                plt.title(str(monitor))
                plt.grid(True)
                plt.legend()


                fig = plt.figure(56)

                plt.plot(list(power.keys()), list(power.values()), '--', markeredgewidth=3, markersize=9,
                         markerfacecolor='None',
                         color='r', marker='o', label="Estimated-Power")
                # plt.ylabel("Corrected NLI Value")
                plt.plot(list(power.keys()), list(keys_to_int(power_opm_dict[monitor]).values()), '--', markeredgewidth=3,
                         markersize=9, markerfacecolor='None',
                         color='b', marker='x', label="Monitored-Power")

                plt.ylabel("Power Absolute Value")
                plt.xlabel("Channels")
                plt.title(str(monitor))
                plt.grid(True)
                plt.legend()

                fig = plt.figure(57)

                plt.plot(list(ase.keys()), list(ase.values()), '--', markeredgewidth=3, markersize=9,
                         markerfacecolor='None',
                         color='r', marker='o', label="Estimated-ASE")
                # plt.ylabel("Corrected NLI Value")
                plt.plot(list(ase.keys()), list(keys_to_int(ase_opm_dict[monitor]).values()), '--', markeredgewidth=3,
                         markersize=9, markerfacecolor='None',
                         color='b', marker='x', label="Monitored-ASE")

                plt.ylabel("ASE Absolute Value")
                plt.xlabel("Channels")

                plt.title(str(monitor))
                plt.grid(True)
                plt.legend()

        print("Link : " + str(link_key) + " Monitor nodes : " + str(monitors_by_density) + " ," + "Monitor : " + str(
            monitor))
        total_monitor_list.append(str(monitor))

        if monitor in monitors_by_density:
            print("Link : " + str(link_key) + " Monitor nodes : " + str(monitors_by_density)+" ,"+ "Monitor : "+str(monitor))

            opm_osnr = keys_to_int(osnr_opm_dict[monitor])
            # compute and apply to NLI noise the correction factor based
            # on the OSNR difference
            # this is used for the correction algorithm
            #print("monitor : "+str(monitor)+" density : "+str(len(monitors_by_density)))

            power_dict = keys_to_int(power_opm_dict[monitor])
            ase_dict = keys_to_int(ase_opm_dict[monitor])
            nli_dict=keys_to_int(nli_opm_dict[monitor])


            nli = nli_correction_algorithm(power_dict,power, nli)
            est_gosnr = correct_gosnr(power_dict, ase_dict, nli)



            if len(monitors_by_density)==4 and 'r_london-r_copenhagen' in str(monitor):
                if False:
                   fig= plt.figure(monitor_count+10)
                   """plt.plot(list(nli.keys()), list(nli.values()), '--', markeredgewidth=3, markersize=9,
                             markerfacecolor='None',
                             color='r', marker='o',label="Corrected-ASE")
                    #plt.ylabel("Corrected NLI Value")
                   plt.plot(list(nli.keys()), list(keys_to_int(nli_opm_dict[monitor]).values()), '--', markeredgewidth=3,
                             markersize=9, markerfacecolor='None',
                             color='b', marker='x',label="Monitored-ASE")"""
                   plt.plot(list(nli.keys()), list(nli.values()), '--', markeredgewidth=3, markersize=9,
                             markerfacecolor='None',
                             color='r', marker='o',label="Corrected-NLI")
                    #plt.ylabel("Corrected NLI Value")
                   plt.plot(list(nli.keys()),  list(keys_to_int(nli_opm_dict[monitor]).values()), '--', markeredgewidth=3,
                             markersize=9, markerfacecolor='None',
                             color='b', marker='x',label="Monitored-NLI")
                
                   plt.ylabel("NLI Absolute Value")
                   plt.xlabel("Channels")
                   plt.title(str(monitor))
                   plt.grid(True)
                   plt.legend()
                   monitor_count=monitor_count+1





            # this is used for correcting everything
            #print('actual NLI : '+str(keys_to_int(nli_opm_dict[monitor])))
            if(monitored_nli):
                nli = keys_to_int(nli_opm_dict[monitor])

            #est_gosnr = correct_gosnr(power_dict, ase_dict, nli)

            gosnr_corr_dict[monitor] = keys_to_str(est_gosnr)

            main_struct = power_dict.keys(), power_dict, ase_dict, nli

        else:
            gosnr_corr_dict[monitor] = keys_to_str(est_gosnr)
            main_struct = power.keys(), power, ase, nli

    print(total_monitor_list)
    return main_struct, gosnr_corr_dict

def normalize(d, target=1):
   raw = sum(d.values())

   temp_list=[]
   for key in sorted(d.keys()):

       temp_list.append([abs_to_db(d[key])])

   temp_list_arr=np.array(temp_list)

   temp_list_arr.reshape(1, -1)


   temp_list_arr = preprocessing.normalize(temp_list_arr)

   for id, key in enumerate(sorted(d.keys())):
       d[key] = db_to_abs(temp_list_arr[id])

   #factor = target/raw
   return d

def nli_correction_algorithm(osnr_dB, osnr_qot_dB, nli):
    osnr_lin = {k: db_to_abs(x) for k, x in osnr_dB.items()}
    osnr_qot_lin = {k: db_to_abs(x) for k, x in osnr_qot_dB.items()}
    o_err_cub_lin_dict={}
    for k in nli.keys():
        o_err_lin =  osnr_lin[k]/osnr_qot_lin[k]
        o_err_cub_lin_dict[k]=o_err_lin**3

    #o_err_cub_lin_dict=normalize(o_err_cub_lin_dict)
    #print(osnr_dB)
    #print(osnr_qot_dB)

    for k in nli.keys():
        #o_err_lin=o_err_lin_dict[k]

        #o_err_cub_lin = o_err_lin ** 3
        o_err_cub_lin = o_err_cub_lin_dict[k]

        #print(str(k) + ": " + str((o_err_lin))+' cube error : '+str((o_err_cub_lin)))
        if (osnr_lin[k]>osnr_qot_lin[k]):
            nli[k] = nli[k]*o_err_cub_lin
        if (osnr_lin[k]<osnr_qot_lin[k]):
            nli[k] *= o_err_cub_lin

    return nli


def correct_gosnr(power, ase, nli):
    gosnr_corr_lin = {}
    for k in power.keys():
        gosnr_corr_lin[k] = power[k] / (ase[k] + nli[k] * (12.5e9/32.0e9))
    gosnr_corr_dB = {k: abs_to_db(x) for k, x in gosnr_corr_lin.items()}
    return gosnr_corr_dB

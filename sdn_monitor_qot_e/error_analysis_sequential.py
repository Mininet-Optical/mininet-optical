import json
import os
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager
from correction_procedure import *

# Plot configuration parameters
# figure(num=None, figsize=(9, 7), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20


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


def compute_errors(y, z):
    _errors = []
    keys = z.keys()
    for k in keys:
        e = abs(y[k] - z[k])
        _errors.append(e)
    return max(_errors)


# locations of the json files
root_dir = '../../data/sequential-loading/'
est_dir = 'estimation-module/'
opm_dir = 'opm-all/'

est_path = root_dir + est_dir
opm_path = root_dir + opm_dir

# only save the estimated values per load
gosnr_est_dict = dict.fromkeys(monitor_keys)
for key in monitor_keys:
    gosnr_est_dict[key] = {9: None, 27: None, 81: None}

# #for each OPM node there are 150 samples
# #to be compared against 1 estimated value
for opm_key in monitor_keys:
    # enter the folder and locate the files
    est_mon_path = est_path + opm_key
    files = os.listdir(est_mon_path)
    for filename in files:
        if filename.endswith(".json"):
            # identify load from name
            file_path = est_mon_path + '/' + filename
            name_split = filename.split('.')
            load = int(name_split[0])

            # process file
            with open(file_path) as json_file:
                f = json.load(json_file)
            json_items = list(f.items())
            metric_items = json_items[0][1]
            gosnr_dict = metric_items[1]

            # retrieve gosnr as a list
            gosnr_label = 'gosnr_load_' + str(load)
            gosnr = gosnr_dict[gosnr_label]

            # record gosnr estimation per load
            gosnr_est_dict[opm_key][load] = gosnr

# record max error from 150 samples at each OPM
errors_orig = {9: [], 27: [], 81: []}
errors_corr = {9: [], 27: [], 81: []}

gosnr_corr_log_9 = get_corrected_struct(9)
gosnr_corr_log_27 = get_corrected_struct(27)
gosnr_corr_log_81 = get_corrected_struct(81)
gosnr_corr = {9: gosnr_corr_log_9,
              27: gosnr_corr_log_27,
              81: gosnr_corr_log_81}


for mk, opm_key in enumerate(monitor_keys):
    # enter the folder and locate the files
    opm_mon_path = opm_path + opm_key
    files = os.listdir(opm_mon_path)

    # temp record errors OPM vs. QoT-E
    errors_tmp = {9: [], 27: [], 81: []}
    # temp record errors OPM vs. QoT-E corrected
    errors_c_tmp = {9: [], 27: [], 81: []}
    for filename in files:
        if filename.endswith(".json"):
            # there are 150 files per load (450 iterations).
            file_path = opm_mon_path + '/' + filename
            name_split = filename.split('_')
            test_id = int(name_split[0])
            name_split = name_split[1].split('.')
            load = int(name_split[0])

            gosnr_label = 'gosnr_load_' + str(load)

            with open(file_path) as json_file:
                f = json.load(json_file)
            json_items = list(f.items())
            metric_items = json_items[0][1]
            gosnr_dict = metric_items[1]

            # get gosnr from OPM
            gosnr_opm = gosnr_dict[gosnr_label]
            # get gosnr from QoT-E
            gosnr_est = gosnr_est_dict[opm_key][load]
            # Compute errors for the above
            error = compute_errors(gosnr_opm, gosnr_est)
            errors_tmp[load].append(error)

            # get gosnr from QoT-E corrected
            gosnr_corrected = gosnr_corr[load][opm_key][load][test_id]
            # Compute errors for OPM and QoT-E corrected
            error_c = compute_errors(gosnr_opm, gosnr_corrected)
            errors_c_tmp[load].append(error_c)

    for _load, _errors in errors_tmp.items():
        errors_orig[_load].append(max(_errors))
    for _load, _errors in errors_c_tmp.items():
        errors_corr[_load].append(max(_errors))

error_9 = errors_orig[9]
error_27 = errors_orig[27]
error_81 = errors_orig[81]

error_c_9 = errors_corr[9]
error_c_27 = errors_corr[27]
error_c_81 = errors_corr[81]


xt = [1, 14, 28, 42, 56, 70, 84, 98]
plt.xticks([0, 13, 27, 41, 55, 69, 83, 97], xt)
plt.yticks(np.arange(0, 7.5, 0.5))
plt.ylabel("Max Error (dB)")
plt.xlabel("Amplifiers")

ms = 12
ls = 6
plt.plot(error_9, color='b', linewidth=ls, label='NM-10%')
plt.plot(error_27, color='orange', linewidth=ls, label='NM-30%')
plt.plot(error_81, color='g', linewidth=ls, label='NM-90%')

plt.plot(error_c_9, linestyle='None', marker='s', markeredgewidth=2, markersize=ms,
             markerfacecolor='None', color='b', label='M-10%')
plt.plot(error_c_27, linestyle='None', marker='v', markeredgewidth=2, markersize=ms,
             markerfacecolor='None', color='orange', label='M-30%')
plt.plot(error_c_81, linestyle='None', marker='D', markeredgewidth=2, markersize=ms,
             markerfacecolor='None', color='g', label='M-90%')
plt.legend(ncol=2, loc='best', columnspacing=0.1, handletextpad=0.1)  # , bbox_to_anchor=(0.5, 0.9))
plt.grid(True)
#fig_name = '../../images/sequential_analysis_50.eps'
#plt.savefig(fig_name, format='eps', bbox_inches='tight', pad_inches=0)
plt.show()


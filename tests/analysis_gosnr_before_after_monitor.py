"""
    This script will read the files from the test-loads-sim/qot folder
    and compute the RMSE and MAE errors from the simulations considering
    WDG functions at the EDFAs compared against the QoT (analytical
    performance computations). Said files can be generated with the
    monitoring_multiple_hop_transmission script found in the tests
    directory of this project.
"""
import json
import os
from pprint import pprint
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager


def compute_errors(y, z):
    errors = []
    for j, h in zip(y, z):
        e = abs(j - h)
        errors.append(e)
    return errors


def find_max_channel(_list, num):
    c = 0
    for e in _list:
        if e == num:
            return c
        c += 1
    return -1


# Plot configuration parameters
# figure(num=None, figsize=(9, 7), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 16

gosnr_mean_rmse_9 = []
gosnr_mean_rmse_27 = []
gosnr_mean_rmse_81 = []

gosnr_mean_rmse_9_m14 = []
gosnr_mean_rmse_27_m14 = []
gosnr_mean_rmse_81_m14 = []

monitors = ['no-m', 'm7']
for monitor in monitors:
    file_id = 0
    mon = monitor
    while file_id <= 97:
        file_id += 1
        opm = 'opm_' + str(file_id) + '/'

        directory = '../../metrics-monitor/opm-sim-' + mon + '/' + opm
        print("*** Running for file: %s" % directory)

        osnrs = {'osnr_load_9': [], 'osnr_load_27': [], 'osnr_load_81': []}
        gosnrs = {'gosnr_load_9': [], 'gosnr_load_27': [], 'gosnr_load_81': []}

        files = os.listdir(directory)
        sorted_files = sorted(files)
        for filename in sorted_files:
            if filename.endswith(".json"):
                file_path = directory + str(filename)
                with open(file_path) as json_file:
                    f = json.load(json_file)
                for key, items in f.items():
                    i = 0
                    for element in items:
                        k = list(element.keys())[0]
                        if i == 0:
                            osnrs[k].append(element[k])
                            i += 1
                        else:
                            gosnrs[k].append(element[k])

        qot_directory = '../../metrics-monitor/opm-sim-qot-' + mon + '/' + opm
        qot_osnrs = {'osnr_load_qot_9': [], 'osnr_load_qot_27': [], 'osnr_load_qot_81': []}
        qot_gosnrs = {'gosnr_load_qot_9': [], 'gosnr_load_qot_27': [], 'gosnr_load_qot_81': []}

        qot_files = os.listdir(qot_directory)
        qot_sorted_files = sorted(qot_files)
        for filename in qot_sorted_files:
            if filename.endswith(".json"):
                file_path = qot_directory + str(filename)
                with open(file_path) as json_file:
                    f = json.load(json_file)
                for key, items in f.items():
                    i = 0
                    for element in items:
                        k = list(element.keys())[0]
                        if i == 0:
                            qot_osnrs[k].append(element[k])
                            i += 1
                        else:
                            qot_gosnrs[k].append(element[k])

        gosnrs_9 = gosnrs['gosnr_load_9']
        qot_gosnrs_9 = qot_gosnrs['gosnr_load_qot_9']
        gosnr_9_rmse = []
        max_channels_9 = []  # register which channels are being looked at
        max_channels_qot_9 = []  # register which channels are being looked at
        for _list1, _list2 in zip(qot_gosnrs_9, gosnrs_9):
            # gosnr_9_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
            gosnr_9_rmse.append(compute_errors(_list1, _list2))
        if mon == 'no-m':
            # gosnr_mean_rmse_9.append(np.max(gosnr_9_rmse[0][2]))
            max_num = np.max(gosnr_9_rmse)
            gosnr_mean_rmse_9.append(max_num)
            # max_channels_9.append(find_max_channel(gosnr_9_rmse[0], max_num))
        else:
            # gosnr_mean_rmse_9_m14.append(np.max(gosnr_9_rmse[0][2]))
            max_num = np.max(gosnr_9_rmse)
            gosnr_mean_rmse_9_m14.append(max_num)
        #     max_channels_qot_9.append(find_max_channel(gosnr_9_rmse[0], max_num))
        # with open('../../max_channels_9_seeds.txt', 'a') as f:
        #     for el in max_channels_9:
        #         line = str(el) + '\n'
        #         f.write(line)
        # with open('../../max_channels_qot_9_seeds.txt', 'a') as f:
        #     for el in max_channels_qot_9:
        #         line = str(el) + '\n'
        #         f.write(line)

        gosnrs_27 = gosnrs['gosnr_load_27']
        qot_gosnrs_27 = qot_gosnrs['gosnr_load_qot_27']
        gosnr_27_rmse = []
        for _list1, _list2 in zip(gosnrs_27, qot_gosnrs_27):
            # gosnr_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
            gosnr_27_rmse.append(compute_errors(_list1, _list2))
        if mon == 'no-m':
            # gosnr_mean_rmse_27.append(np.max(gosnr_27_rmse[0][2]))
            gosnr_mean_rmse_27.append(np.max(gosnr_27_rmse))
        else:
            # gosnr_mean_rmse_27_m14.append(np.max(gosnr_27_rmse[0][2]))
            gosnr_mean_rmse_27_m14.append(np.max(gosnr_27_rmse))

        gosnrs_81 = gosnrs['gosnr_load_81']
        qot_gosnrs_81 = qot_gosnrs['gosnr_load_qot_81']
        gosnr_81_rmse = []
        for _list1, _list2 in zip(qot_gosnrs_81, gosnrs_81):
            # gosnr_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
            gosnr_81_rmse.append(compute_errors(_list1, _list2))
        if mon == 'no-m':
            # gosnr_mean_rmse_81.append(np.max(gosnr_81_rmse[0][2]))
            gosnr_mean_rmse_81.append(np.max(gosnr_81_rmse))
        else:
            # gosnr_mean_rmse_81_m14.append(np.max(gosnr_81_rmse[0][2]))
            gosnr_mean_rmse_81_m14.append(np.max(gosnr_81_rmse))

        del qot_osnrs
        del qot_gosnrs
        del gosnr_9_rmse
        del gosnr_27_rmse
        del gosnr_81_rmse


x = range(0, 98)
xt = [1, 14, 28, 42, 56, 70, 84, 98]
plt.xticks([0, 13, 27, 41, 55, 69, 83, 97], xt)
# plt.yticks(np.arange(0, 10.5, 0.5))
plt.ylabel("Max Error (dB)")
plt.xlabel("Amplifiers")
ms = 12
ls = 6
plt.plot(x, gosnr_mean_rmse_9, color='silver', linewidth=ls, label='No-Monitoring-10%')
plt.plot(x, gosnr_mean_rmse_27, color='grey', linewidth=ls, label='No-Monitoring-30%')
plt.plot(x, gosnr_mean_rmse_81, color='k', linewidth=ls, label='No-Monitoring-90%')

plt.plot(x, gosnr_mean_rmse_9_m14, linestyle='None', marker='s', markersize=ms,
         markerfacecolor='None', color='silver', label='Monitoring-10%')
plt.plot(x, gosnr_mean_rmse_27_m14, linestyle='None', marker='v', markersize=ms,
         markerfacecolor='None', color='grey', label='Monitoring-30%')
plt.plot(x, gosnr_mean_rmse_81_m14, linestyle='None', marker='D', markersize=ms,
         markerfacecolor='None', color='k', label='Monitoring-90%')
plt.legend(ncol=2, columnspacing=0.2, handletextpad=0.2)
plt.grid(True)
# fig_name = '../../images/monitoring_metrics_before_after_worst_m28.eps'
# fig_name = '../../images/tmp_fig.eps'
# plt.savefig(fig_name, format='eps')
plt.show()


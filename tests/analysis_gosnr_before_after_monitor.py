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

# Plot configuration parameters
figure(num=None, figsize=(8.4, 6.4), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 18

gosnr_mean_rmse_27 = []
gosnr_mean_rmse_54 = []
gosnr_mean_rmse_81 = []

gosnr_mean_rmse_27_m14 = []
gosnr_mean_rmse_54_m14 = []
gosnr_mean_rmse_81_m14 = []

monitors = ['no-m', 'm14']
for monitor in monitors:
    file_id = 0
    mon = monitor
    while file_id <= 97:
        file_id += 1
        opm = 'opm_' + str(file_id) + '/'

        directory = '../metrics-monitor/opm-sim-' + mon + '/' + opm
        print("*** Running for file: %s" % directory)

        osnrs = {'osnr_load_27': [], 'osnr_load_54': [], 'osnr_load_81': []}
        gosnrs = {'gosnr_load_27': [], 'gosnr_load_54': [], 'gosnr_load_81': []}

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

        qot_directory = '../metrics-monitor/opm-sim-qot-' + mon + '/' + opm
        qot_osnrs = {'osnr_load_qot_27': [], 'osnr_load_qot_54': [], 'osnr_load_qot_81': []}
        qot_gosnrs = {'gosnr_load_qot_27': [], 'gosnr_load_qot_54': [], 'gosnr_load_qot_81': []}

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

        gosnrs_27 = gosnrs['gosnr_load_27']
        qot_gosnrs_27 = qot_gosnrs['gosnr_load_qot_27']
        gosnr_27_rmse = []
        for _list1, _list2 in zip(qot_gosnrs_27, gosnrs_27):
            gosnr_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
        if mon == 'no-m':
            gosnr_mean_rmse_27.append(np.mean(gosnr_27_rmse))
        else:
            gosnr_mean_rmse_27_m14.append(np.mean(gosnr_27_rmse))

        gosnrs_54 = gosnrs['gosnr_load_54']
        qot_gosnrs_54 = qot_gosnrs['gosnr_load_qot_54']
        gosnr_54_rmse = []
        for _list1, _list2 in zip(gosnrs_54, qot_gosnrs_54):
            gosnr_54_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
        if mon == 'no-m':
            gosnr_mean_rmse_54.append(np.mean(gosnr_54_rmse))
        else:
            gosnr_mean_rmse_54_m14.append(np.mean(gosnr_54_rmse))

        gosnrs_81 = gosnrs['gosnr_load_81']
        qot_gosnrs_81 = qot_gosnrs['gosnr_load_qot_81']
        gosnr_81_rmse = []
        for _list1, _list2 in zip(qot_gosnrs_81, gosnrs_81):
            gosnr_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
        if mon == 'no-m':
            gosnr_mean_rmse_81.append(np.mean(gosnr_81_rmse))
        else:
            gosnr_mean_rmse_81_m14.append(np.mean(gosnr_81_rmse))

        del qot_osnrs
        del qot_gosnrs
        del gosnr_27_rmse
        del gosnr_54_rmse
        del gosnr_81_rmse


x = range(0, 98)
xt = [1, 14, 28, 42, 56, 70, 84, 98]
plt.xticks([0, 14, 28, 42, 56, 70, 84, 98], xt)
plt.yticks(np.arange(0, 6.5, 0.5))
plt.ylabel("Average RMSE (dB) of \nSDN-controller QoT-E model")
plt.xlabel("Amplifiers")
ms = 12
ls = 6
plt.plot(x, gosnr_mean_rmse_27, color='silver', linewidth=ls, label='No-Monitoring-30%')
plt.plot(x, gosnr_mean_rmse_54, color='grey', linewidth=ls, label='No-Monitoring-60%')
plt.plot(x, gosnr_mean_rmse_81, color='k', linewidth=ls, label='No-Monitoring-90%')

plt.plot(x, gosnr_mean_rmse_27_m14, linestyle='None', marker='s', markersize=ms,
         markerfacecolor='None', color='silver', label='Monitoring-30%')
plt.plot(x, gosnr_mean_rmse_54_m14, linestyle='None', marker='v', markersize=ms,
         markerfacecolor='None', color='grey', label='Monitoring-60%')
plt.plot(x, gosnr_mean_rmse_81_m14, linestyle='None', marker='D', markersize=ms,
         markerfacecolor='None', color='k', label='Monitoring-90%')
plt.legend(ncol=2, columnspacing=0.2, handletextpad=0.2)
plt.grid(True)
fig_name = '../monitoring_metrics_before_after2.eps'
plt.savefig(fig_name, format='eps')
# plt.show()

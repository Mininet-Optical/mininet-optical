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
plt.rcParams["font.size"] = 20

osnr_mean_rmse_27 = []
osnr_mean_rmse_54 = []
osnr_mean_rmse_81 = []

osnr_mean_rmse_27_m14 = []
osnr_mean_rmse_54_m14 = []
osnr_mean_rmse_81_m14 = []

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
        # osnrs = {'osnr_load_27': [], 'osnr_load_54': [], 'osnr_load_81': []}

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
                        gornot = k[0]
                        if gornot == 'o':
                            if i == 0:
                                osnrs[k].append(element[k])
                                i += 1
                            else:
                                osnrs[k].append(element[k])

        qot_directory = '../metrics-monitor/opm-sim-qot-' + mon + '/' + opm
        qot_osnrs = {'osnr_load_qot_27': [], 'osnr_load_qot_54': [], 'osnr_load_qot_81': []}
        # qot_osnrs = {'osnr_load_qot_27': [], 'osnr_load_qot_54': [], 'osnr_load_qot_81': []}

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
                        gornot = k[0]
                        if gornot == 'o':
                            if i == 0:
                                qot_osnrs[k].append(element[k])
                                i += 1
                            else:
                                qot_osnrs[k].append(element[k])

        osnrs_27 = osnrs['osnr_load_27']
        qot_osnrs_27 = qot_osnrs['osnr_load_qot_27']
        osnr_27_rmse = []
        for _list1, _list2 in zip(qot_osnrs_27, osnrs_27):
            osnr_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
        if mon == 'no-m':
            osnr_mean_rmse_27.append(np.mean(osnr_27_rmse))
        else:
            osnr_mean_rmse_27_m14.append(np.mean(osnr_27_rmse))

        osnrs_54 = osnrs['osnr_load_54']
        qot_osnrs_54 = qot_osnrs['osnr_load_qot_54']
        osnr_54_rmse = []
        for _list1, _list2 in zip(osnrs_54, qot_osnrs_54):
            osnr_54_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
        if mon == 'no-m':
            osnr_mean_rmse_54.append(np.mean(osnr_54_rmse))
        else:
            osnr_mean_rmse_54_m14.append(np.mean(osnr_54_rmse))

        osnrs_81 = osnrs['osnr_load_81']
        qot_osnrs_81 = qot_osnrs['osnr_load_qot_81']
        osnr_81_rmse = []
        for _list1, _list2 in zip(qot_osnrs_81, osnrs_81):
            osnr_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
        if mon == 'no-m':
            osnr_mean_rmse_81.append(np.mean(osnr_81_rmse))
        else:
            osnr_mean_rmse_81_m14.append(np.mean(osnr_81_rmse))

        del osnrs
        del qot_osnrs
        del osnr_27_rmse
        del osnr_54_rmse
        del osnr_81_rmse


x = range(0, 98)
xt = [1, 14, 28, 42, 56, 70, 84, 98]
plt.xticks([0, 14, 28, 42, 56, 70, 84, 98], xt)
# plt.yticks(np.arange(0, 6.5, 0.5))
plt.ylabel("Mean RMSE (dB) of \nSDN-controller QoT-E model")
plt.xlabel("OPM node index")
ms = 12
ls = 6
plt.plot(x, osnr_mean_rmse_27, color='b', linewidth=ls, label='W/O-MC*-30%')
plt.plot(x, osnr_mean_rmse_54, color='y', linewidth=ls, label='W/O-MC-60%')
plt.plot(x, osnr_mean_rmse_81, color='r', linewidth=ls, label='W/O-MC-90%')

plt.plot(x, osnr_mean_rmse_27_m14, linestyle='None', marker='s', markersize=ms,
         markerfacecolor='None', color='b', label='MC-14**-30%')
plt.plot(x, osnr_mean_rmse_54_m14, linestyle='None', marker='v', markersize=ms,
         markerfacecolor='None', color='y', label='MC-14-60%')
plt.plot(x, osnr_mean_rmse_81_m14, linestyle='None', marker='D', markersize=ms,
         markerfacecolor='None', color='r', label='MC-14-90%')
plt.legend(ncol=2, columnspacing=0.2, handletextpad=0.2)
plt.grid(True)
fig_name = '../monitoring_osnr_before_after.eps'
plt.savefig(fig_name, format='eps')
# plt.show()

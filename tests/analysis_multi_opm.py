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
    return max(errors)


# Plot configuration parameters
# figure(num=None, figsize=(9, 7), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 18

gosnr_mean_rmse_9 = []
osnr_mean_rmse_9 = []
gosnr_mean_rmse_27 = []
osnr_mean_rmse_27 = []
gosnr_mean_rmse_81 = []
osnr_mean_rmse_81 = []

key_t = 'g'  # key for plotting gOSNR or OSNR (g or o, respectively)
file_id = 0  # needed to iterate through the files
num_opm_t = 97  # indicate number of OPMs in the simulation
while file_id <= num_opm_t:
    file_id += 1
    opm = 'opm_' + str(file_id) + '/'
    mon = 'no-m/'
    directory = '../../metrics-monitor/opm-sim-' + mon + opm
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

    qot_directory = '../../metrics-monitor/opm-sim-qot-' + mon + opm
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
    if key_t is 'g':
        gosnrs_9 = gosnrs['gosnr_load_9']
        qot_gosnrs_9 = qot_gosnrs['gosnr_load_qot_9']
        gosnr_9_rmse = []
        for _list1, _list2 in zip(qot_gosnrs_9, gosnrs_9):
            # gosnr_9_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
            gosnr_9_rmse.append(compute_errors(_list1, _list2))
        gosnr_mean_rmse_9.append(np.max(gosnr_9_rmse))
    else:
        osnrs_9 = osnrs['osnr_load_9']
        qot_osnrs_9 = qot_osnrs['osnr_load_qot_9']
        osnr_9_rmse = []
        for _lista, _listb in zip(qot_osnrs_9, osnrs_9):
            osnr_9_rmse.append(sqrt(mean_squared_error(_lista, _listb)))
        osnr_mean_rmse_9.append(np.max(osnr_9_rmse))

    if key_t is 'g':
        gosnrs_27 = gosnrs['gosnr_load_27']
        qot_gosnrs_27 = qot_gosnrs['gosnr_load_qot_27']
        gosnr_27_rmse = []
        for _list1, _list2 in zip(gosnrs_27, qot_gosnrs_27):
            # gosnr_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
            gosnr_27_rmse.append(compute_errors(_list1, _list2))
        gosnr_mean_rmse_27.append(np.max(gosnr_27_rmse))
    else:
        osnrs_27 = osnrs['osnr_load_27']
        qot_osnrs_27 = qot_osnrs['osnr_load_qot_27']
        osnr_27_rmse = []
        for _list1, _list2 in zip(osnrs_27, qot_osnrs_27):
            osnr_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
        osnr_mean_rmse_27.append(np.max(osnr_27_rmse))

    if key_t is 'g':
        gosnrs_81 = gosnrs['gosnr_load_81']
        qot_gosnrs_81 = qot_gosnrs['gosnr_load_qot_81']
        gosnr_81_rmse = []
        for _list1, _list2 in zip(qot_gosnrs_81, gosnrs_81):
            # gosnr_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
            gosnr_81_rmse.append(compute_errors(_list1, _list2))
        gosnr_mean_rmse_81.append(np.max(gosnr_81_rmse))
    else:
        osnrs_81 = osnrs['osnr_load_81']
        qot_osnrs_81 = qot_osnrs['osnr_load_qot_81']
        osnr_81_rmse = []
        for _lista, _listb in zip(qot_osnrs_81, osnrs_81):
            osnr_81_rmse.append(sqrt(mean_squared_error(_lista, _listb)))
        osnr_mean_rmse_81.append(np.max(osnr_81_rmse))

    del qot_osnrs
    del qot_gosnrs

    if key_t is 'g':
        del gosnr_9_rmse
        del gosnr_27_rmse
        del gosnr_81_rmse
    else:
        del osnr_9_rmse
        del osnr_27_rmse
        del osnr_81_rmse


# plt.plot(osnr_mean_rmse_9, color='b', marker='s', markerfacecolor='None')
# plt.plot(osnr_mean_rmse_81, color='r', marker='D', markerfacecolor='None')
x = range(0, num_opm_t + 1)
# xt = [1, 14, 28, 42, 56, 70, 84, 98]
# plt.xticks([0, 14, 28, 42, 56, 70, 84, 98], xt)
# plt.yticks(np.arange(0, 27.4, 0.1))
plt.ylabel("Max Error (dB)")
plt.xlabel("Amplifiers")
ms = 9
if key_t is 'g':
    plt.plot(x, gosnr_mean_rmse_9, linestyle='None', marker='s', markeredgewidth=3, markersize=ms,
             markerfacecolor='None', color='silver', label='Monitoring-10%')
    plt.plot(x, gosnr_mean_rmse_27, linestyle='None', marker='v', markeredgewidth=3, markersize=ms,
             markerfacecolor='None', color='grey', label='Monitoring-30%')
    plt.plot(x, gosnr_mean_rmse_81, linestyle='None', marker='D', markeredgewidth=3, markersize=ms,
             markerfacecolor='None', color='k', label='Monitoring-90%')
else:
    plt.plot(x, osnr_mean_rmse_9, linestyle='None', marker='s', markeredgewidth=3, markersize=ms,
             markerfacecolor='None', color='silver', label='Monitoring-10%')
    plt.plot(x, osnr_mean_rmse_27, linestyle='None', marker='v', markeredgewidth=3, markersize=ms,
             markerfacecolor='None', color='grey', label='Monitoring-30%')
    plt.plot(x, osnr_mean_rmse_81, linestyle='None', marker='D', markeredgewidth=3, markersize=ms,
             markerfacecolor='None', color='k', label='Monitoring-90%')
plt.legend()
plt.grid(True)
if key_t is 'g':
    plt.title('gOSNR Divergence')
else:
    plt.title('OSNR Divergence')
# plt.savefig('../../monitoring_metrics_worst_m14.eps', format='eps')
plt.show()

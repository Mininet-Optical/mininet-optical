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
import sys

# Plot configuration parameters
figure(num=None, figsize=(8.4, 6.4), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20

power_mean_rmse_27 = []
ase_mean_rmse_27 = []
nli_mean_rmse_27 = []
power_worst_rmse_27 = []
power_best_rmse_27 = []

power_mean_rmse_54 = []
ase_mean_rmse_54 = []
nli_mean_rmse_54 = []
power_worst_rmse_54 = []
power_best_rmse_54 = []

power_mean_rmse_81 = []
ase_mean_rmse_81 = []
nli_mean_rmse_81 = []
power_worst_rmse_81 = []
power_best_rmse_81 = []

file_id = 0
mon = 'm14'
while file_id <= 97:
    file_id += 1
    opm = 'opm_' + str(file_id) + '/'
    directory = '../raw-monitor/opm-sim-' + mon + '/' + opm
    print("*** Running for file: %s" % directory)

    powers = {'power_27': [], 'power_54': [], 'power_81': []}
    ases = {'ase_27': [], 'ase_54': [], 'ase_81': []}
    nlis = {'nli_27': [], 'nli_54': [], 'nli_81': []}

    files = os.listdir(directory)
    sorted_files = sorted(files)
    for filename in sorted_files:
        if filename.endswith(".json"):
            file_path = directory + str(filename)
            with open(file_path) as json_file:
                f = json.load(json_file)
            for key, items in f.items():
                i = 1
                for element in items:
                    k = list(element.keys())[0]
                    if i == 1:
                        powers[k].append(element[k])
                        i += 1
                    elif i == 2:
                        ases[k].append(element[k])
                        i += 1
                    else:
                        nlis[k].append(element[k])

    qot_directory = '../raw-monitor/opm-sim-qot-' + mon + '/' + opm
    qot_powers = {'power_qot_27': [], 'power_qot_54': [], 'power_qot_81': []}
    qot_ases = {'ase_qot_27': [], 'ase_qot_54': [], 'ase_qot_81': []}
    qot_nlis = {'nli_qot_27': [], 'nli_qot_54': [], 'nli_qot_81': []}

    qot_files = os.listdir(qot_directory)
    qot_sorted_files = sorted(qot_files)
    for filename in qot_sorted_files:
        if filename.endswith(".json"):
            file_path = qot_directory + str(filename)
            with open(file_path) as json_file:
                f = json.load(json_file)
            for key, items in f.items():
                i = 1
                for element in items:
                    k = list(element.keys())[0]
                    if i == 1:
                        qot_powers[k].append(element[k])
                        i += 1
                    elif i == 2:
                        qot_ases[k].append(element[k])
                        i += 1
                    else:
                        qot_nlis[k].append(element[k])

    # Monitoring power levels
    powers_27 = powers['power_27']
    qot_powers_27 = qot_powers['power_qot_27']
    powers_27_rmse = []
    for _list1, _list2 in zip(qot_powers_27, powers_27):
        powers_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    power_mean_rmse_27.append(np.median(powers_27_rmse))

    powers_54 = powers['power_54']
    qot_powers_54 = qot_powers['power_qot_54']
    powers_54_rmse = []
    for _list1, _list2 in zip(qot_powers_54, powers_54):
        powers_54_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    power_mean_rmse_54.append(np.median(powers_54_rmse))

    powers_81 = powers['power_81']
    qot_powers_81 = qot_powers['power_qot_81']
    powers_81_rmse = []
    for _list1, _list2 in zip(qot_powers_81, powers_81):
        powers_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    power_mean_rmse_81.append(np.median(powers_81_rmse))

    # Monitoring ASE noise levels
    ases_27 = ases['ase_27']
    qot_ases_27 = qot_ases['ase_qot_27']
    ases_27_rmse = []
    for _list1, _list2 in zip(qot_ases_27, ases_27):
        ases_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    ase_mean_rmse_27.append(np.median(ases_27_rmse))

    ases_54 = ases['ase_54']
    qot_ases_54 = qot_ases['ase_qot_54']
    ases_54_rmse = []
    for _list1, _list2 in zip(qot_ases_54, ases_54):
        ases_54_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    ase_mean_rmse_54.append(np.median(ases_54_rmse))

    ases_81 = ases['ase_81']
    qot_ases_81 = qot_ases['ase_qot_81']
    ases_81_rmse = []
    for _list1, _list2 in zip(qot_ases_81, ases_81):
        ases_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    ase_mean_rmse_81.append(np.median(ases_81_rmse))

    # Monitoring NLI noise levels
    nlis_27 = nlis['nli_27']
    qot_nlis_27 = qot_nlis['nli_qot_27']
    nlis_27_rmse = []
    for _list1, _list2 in zip(qot_nlis_27, nlis_27):
        nlis_27_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    nli_mean_rmse_27.append(np.median(nlis_27_rmse))

    nlis_54 = nlis['nli_54']
    qot_nlis_54 = qot_nlis['nli_qot_54']
    nlis_54_rmse = []
    for _list1, _list2 in zip(qot_nlis_54, nlis_54):
        nlis_54_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    nli_mean_rmse_54.append(np.median(nlis_54_rmse))

    nlis_81 = nlis['nli_81']
    qot_nlis_81 = qot_nlis['nli_qot_81']
    nlis_81_rmse = []
    for _list1, _list2 in zip(qot_nlis_81, nlis_81):
        nlis_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    nli_mean_rmse_81.append(np.median(nlis_81_rmse))

    del powers
    del ases
    del nlis
    del qot_powers
    del qot_ases
    del qot_nlis
    del powers_27_rmse
    del powers_54_rmse
    del powers_81_rmse

# print power
plt.ylabel("Mean RMSE (dB) of \nSDN-controller QoT-E model")
plt.xlabel("Index and location of OPM nodes")
x = range(0, 98)
ms = 12
plt.plot(x, power_mean_rmse_27, linestyle='None', marker='s', markersize=ms,
         markerfacecolor='None', color='b', label='30% ch-load')
plt.plot(x, power_mean_rmse_54, linestyle='None', marker='v', markersize=ms,
         markerfacecolor='None', color='y', label='60% ch-load')
plt.plot(x, power_mean_rmse_81, linestyle='None', marker='D', markersize=ms,
         markerfacecolor='None', color='r', label='90% ch-load')
plt.legend()
plt.grid(True)
fig_name = '../monitoring_power_' + mon + '.eps'
plt.savefig(fig_name, format='eps')
plt.clf()

# print ase noise
plt.ylabel("Mean RMSE (dB) of \nSDN-controller QoT-E model")
plt.xlabel("Index and location of OPM nodes")
x = range(0, 98)
ms = 12
plt.plot(x, ase_mean_rmse_27, linestyle='None', marker='s', markersize=ms,
         markerfacecolor='None', color='b', label='30% ch-load')
plt.plot(x, ase_mean_rmse_54, linestyle='None', marker='v', markersize=ms,
         markerfacecolor='None', color='y', label='60% ch-load')
plt.plot(x, ase_mean_rmse_81, linestyle='None', marker='D', markersize=ms,
         markerfacecolor='None', color='r', label='90% ch-load')
plt.legend()
plt.grid(True)
fig_name = '../monitoring_ase_' + mon + '.eps'
plt.savefig(fig_name, format='eps')
plt.clf()

# print nli noise
plt.ylabel("Mean RMSE (dB) of \nSDN-controller QoT-E model")
plt.xlabel("Index and location of OPM nodes")
x = range(0, 98)
ms = 12
plt.plot(x, nli_mean_rmse_27, linestyle='None', marker='s', markersize=ms,
         markerfacecolor='None', color='b', label='30% ch-load')
plt.plot(x, nli_mean_rmse_54, linestyle='None', marker='v', markersize=ms,
         markerfacecolor='None', color='y', label='60% ch-load')
plt.plot(x, nli_mean_rmse_81, linestyle='None', marker='D', markersize=ms,
         markerfacecolor='None', color='r', label='90% ch-load')
plt.legend()
plt.grid(True)
fig_name = '../monitoring_nli_' + mon + '.eps'
plt.savefig(fig_name, format='eps')
plt.clf()

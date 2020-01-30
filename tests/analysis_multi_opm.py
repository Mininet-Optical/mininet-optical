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
# figure(num=None, figsize=(7, 6), dpi=256)
# del matplotlib.font_manager.weight_dict['roman']
# matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20

gosnr_mean_rmse_27 = []
osnr_mean_rmse_27 = []
gosnr_mean_rmse_54 = []
gosnr_mean_rmse_81 = []
osnr_mean_rmse_81 = []

file_id = 0
while file_id <= 95:
    file_id += 1
    opm = 'opm_' + str(file_id) + '/'
    directory = '../opm-sim/' + opm
    print("*** Running for file: %s" % directory)

    osnrs = {'osnr_load_27': [], 'osnr_load_54': [], 'osnr_load_81': []}
    gosnrs = {'gosnr_load_27': [], 'gosnr_load_54': [], 'gosnr_load_81': []}

    for filename in os.listdir(directory):
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

    qot_directory = '../opm-sim-qot/' + opm
    qot_osnrs = {'osnr_load_qot_27': [], 'osnr_load_qot_54': [], 'osnr_load_qot_81': []}
    qot_gosnrs = {'gosnr_load_qot_27': [], 'gosnr_load_qot_54': [], 'gosnr_load_qot_81': []}

    for filename in os.listdir(qot_directory):
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
    gosnr_mean_rmse_27.append(np.median(gosnr_27_rmse))

    osnrs_27 = osnrs['osnr_load_27']
    qot_osnrs_27 = qot_osnrs['osnr_load_qot_27']

    osnr_27_rmse = []
    for _lista, _listb in zip(qot_osnrs_27, osnrs_27):
        osnr_27_rmse.append(sqrt(mean_squared_error(_lista, _listb)))
    osnr_mean_rmse_27.append(np.median(osnr_27_rmse))

    # gosnrs_54 = gosnrs['gosnr_load_54']
    # qot_gosnrs_54 = qot_gosnrs['gosnr_load_qot_54']
    #
    # gosnr_54_rmse = []
    # for _list1, _list2 in zip(gosnrs_54, qot_gosnrs_54):
    #     gosnr_54_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    # gosnr_mean_rmse_54.append(np.mean(gosnr_54_rmse))

    gosnrs_81 = gosnrs['gosnr_load_81']
    qot_gosnrs_81 = qot_gosnrs['gosnr_load_qot_81']

    gosnr_81_rmse = []
    for _list1, _list2 in zip(qot_gosnrs_81, gosnrs_81):
        gosnr_81_rmse.append(sqrt(mean_squared_error(_list1, _list2)))
    gosnr_mean_rmse_81.append(np.median(gosnr_81_rmse))

    osnrs_81 = osnrs['osnr_load_81']
    qot_osnrs_81 = qot_osnrs['osnr_load_qot_81']

    osnr_81_rmse = []
    for _lista, _listb in zip(qot_osnrs_81, osnrs_81):
        osnr_81_rmse.append(sqrt(mean_squared_error(_lista, _listb)))
    osnr_mean_rmse_81.append(np.median(osnr_81_rmse))

    del qot_osnrs
    del qot_gosnrs
    del gosnr_27_rmse
    del osnr_27_rmse
    # del gosnr_54_rmse
    del gosnr_81_rmse
    del osnr_81_rmse


# plt.plot(osnr_mean_rmse_27, color='b', marker='s', markerfacecolor='None')
# plt.plot(osnr_mean_rmse_81, color='r', marker='D', markerfacecolor='None')
# plt.xticks(range(0, 8), range(1, 9))
plt.title("OSNR QoT-E without corrections")
plt.ylabel("Mean RMSE (dB) of QoT-E of all channels")
plt.xlabel("Index and location of OPM nodes")
plt.plot(gosnr_mean_rmse_27, linestyle='None', marker='s', markerfacecolor='None', color='b', label='30% ch-load')
# plt.plot(gosnr_mean_rmse_54, linestyle='None', marker='v', markerfacecolor='None', color='y')
plt.plot(gosnr_mean_rmse_81, linestyle='None', marker='D', markerfacecolor='None', color='r', label='90% ch-load')
plt.legend()
# plt.savefig('../generic_plot.eps', format='eps')
plt.grid(True)
plt.show()

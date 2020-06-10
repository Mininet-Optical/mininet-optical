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
gosnr_mean_rmse_54 = []
gosnr_mean_rmse_81 = []

file_id = 1
while file_id <= 50:
    file_id += 1
    opm = 'opm_' + str(file_id) + '/'
    directory = '../opm-sim-no-m/' + opm
    print("*** Running for file: %s" % directory)

    osnr_load_keys = ['osnr_load_27', 'osnr_load_54', 'osnr_load_81']
    gosnr_load_keys = ['gosnr_load_27', 'gosnr_load_54', 'gosnr_load_81']

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

    qot_directory = '../opm-sim-qot-no-m/' + opm
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
                        for e in element[k]:
                            qot_osnrs[k].append(e)
                        i += 1
                    else:
                        for e in element[k]:
                            qot_gosnrs[k].append(e)

    gosnrs_27 = gosnrs['gosnr_load_27']
    qot_gosnrs_27 = qot_gosnrs['gosnr_load_qot_27']

    gosnr_27_rmse = []
    for _list in gosnrs_27:
        gosnr_27_rmse.append(sqrt(mean_squared_error(_list, qot_gosnrs_27)))
    gosnr_mean_rmse_27.append(np.mean(gosnr_27_rmse))

    gosnrs_54 = gosnrs['gosnr_load_54']
    qot_gosnrs_54 = qot_gosnrs['gosnr_load_qot_54']

    gosnr_54_rmse = []
    for _list in gosnrs_54:
        gosnr_54_rmse.append(sqrt(mean_squared_error(_list, qot_gosnrs_54)))
    gosnr_mean_rmse_54.append(np.mean(gosnr_54_rmse))

    gosnrs_81 = gosnrs['gosnr_load_81']
    qot_gosnrs_81 = qot_gosnrs['gosnr_load_qot_81']

    gosnr_81_rmse = []
    for _list in gosnrs_81:
        gosnr_81_rmse.append(sqrt(mean_squared_error(_list, qot_gosnrs_81)))
    gosnr_mean_rmse_81.append(np.mean(gosnr_81_rmse))

    del qot_osnrs
    del qot_gosnrs
    del gosnr_27_rmse
    del gosnr_54_rmse
    del gosnr_81_rmse


plt.plot(gosnr_mean_rmse_27, color='b')
plt.plot(gosnr_mean_rmse_81, color='r')
# plt.xticks(range(1, 4), ('RMSE-30%', 'RMSE-60%', 'RMSE-90%',))
# plt.yticks(np.arange(4, 13, 1))
# plt.savefig('../gOSNR_RMSE_15_hop.eps', format='eps')
plt.show()

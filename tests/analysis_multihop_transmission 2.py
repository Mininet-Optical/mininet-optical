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
figure(num=None, figsize=(7, 6), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20

hop = '15_hop/'
directory = '../test-loads-sim/' + hop

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

qot_directory = '../test-loads-qot/' + hop
qot_osnrs = {'osnr_load_27': [], 'osnr_load_54': [], 'osnr_load_81': []}
qot_gosnrs = {'gosnr_load_27': [], 'gosnr_load_54': [], 'gosnr_load_81': []}

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
qot_gosnrs_27 = qot_gosnrs['gosnr_load_27']

gosnr_27_rmse = []
gosnr_27_mae = []
for _list in gosnrs_27:
    gosnr_27_rmse.append(sqrt(mean_squared_error(_list, qot_gosnrs_27)))
    gosnr_27_mae.append(mean_absolute_error(_list, qot_gosnrs_27))
# print("osnr load-30%% mean RMSE over 27,000 comparisons: %f" % np.mean(osnr_27_rmse))
# print("osnr load-30%% max RMSE over 27,000 comparisons: %f" % max(osnr_27_rmse))
# print("osnr load-30%% min RMSE over 27,000 comparisons: %f" % min(osnr_27_rmse))
# print(osnr_27_mae)
# print(np.mean(osnr_27_mae))

# round_diff = 0
# checked_comp = 0
#
# for _list in osnrs_27:
#     for osnr, qot_osnr in zip(_list, qot_osnrs_27):
#         if abs(round(osnr) - round(qot_osnr)) >= 1:
#             round_diff += 1
#         checked_comp += 1
#
# print("osnrs load-30%% Found %d >= than 1 dB in %d checks" % (round_diff, checked_comp))


gosnrs_54 = gosnrs['gosnr_load_54']
qot_gosnrs_54 = qot_gosnrs['gosnr_load_54']

gosnr_54_rmse = []
gosnr_54_mae = []
for _list in gosnrs_54:
    gosnr_54_rmse.append(sqrt(mean_squared_error(_list, qot_gosnrs_54)))
    gosnr_54_mae.append(mean_absolute_error(_list, qot_gosnrs_54))
# print("osnr load-60%% mean RMSE over 54,000 comparisons: %f" % np.mean(osnr_54_rmse))
# print("osnr load-60%% max RMSE over 54,000 comparisons: %f" % max(osnr_54_rmse))
# print("osnr load-60%% min RMSE over 54,000 comparisons: %f" % min(osnr_54_rmse))

# round_diff = 0
# checked_comp = 0
#
# for _list in osnrs_54:
#     for osnr, qot_osnr in zip(_list, qot_osnrs_54):
#         if abs(round(osnr) - round(qot_osnr)) >= 1:
#             round_diff += 1
#         checked_comp += 1
#
# print("osnrs load-60%% Found %d >= than 1 dB in %d checks" % (round_diff, checked_comp))

gosnrs_81 = gosnrs['gosnr_load_81']
qot_gosnrs_81 = qot_gosnrs['gosnr_load_81']

gosnr_81_rmse = []
gosnr_81_mae = []
for _list in gosnrs_81:
    gosnr_81_rmse.append(sqrt(mean_squared_error(_list, qot_gosnrs_81)))
    gosnr_81_mae.append(mean_absolute_error(_list, qot_gosnrs_81))
print("osnr load-90%% mean RMSE over 81,000 comparisons: %f" % np.mean(gosnr_81_rmse))
print("osnr load-90%% max RMSE over 81,000 comparisons: %f" % max(gosnr_81_rmse))
print("osnr load-90%% min RMSE over 81,000 comparisons: %f" % min(gosnr_81_rmse))

# round_diff = 0
# checked_comp = 0
#
# for _list in osnrs_81:
#     for osnr, qot_osnr in zip(_list, qot_osnrs_81):
#         if abs(round(osnr) - round(qot_osnr)) >= 1:
#             round_diff += 1
#         checked_comp += 1
#
# print("osnrs load-90%% Found %d >= than 1 dB in %d checks" % (round_diff, checked_comp))


# plt.rcParams["font.size"] = 22
box = [gosnr_27_rmse, gosnr_27_mae, gosnr_54_rmse, gosnr_54_mae, gosnr_81_rmse, gosnr_81_mae]
# box = [gosnr_27_rmse, gosnr_54_rmse, gosnr_81_rmse]
bx = plt.boxplot(box, notch=True, patch_artist=True)
colors = ['hotpink', 'pink', 'cyan', 'darkturquoise', 'springgreen', 'mediumseagreen']
# colors = ['pink', 'darkturquoise', 'mediumseagreen']
for patch, color in zip(bx['boxes'], colors):
    patch.set_facecolor(color)
plt.ylabel("gOSNR Error (dB)")
# plt.legend([bx['boxes'][0], bx['boxes'][1]], ['RMSE', 'MAE'], loc='upper center', edgecolor='k')
plt.xticks(range(1, 7), ('RMSE\n30%', 'MAE\n30%', 'RMSE\n60%', 'MAE\n60%', 'RMSE\n90%', 'MAE\n90%',))
# plt.xticks(range(1, 4), ('RMSE-30%', 'RMSE-60%', 'RMSE-90%',))
# plt.yticks(np.arange(4, 13, 1))
# plt.savefig('../gOSNR_RMSE_15_hop.eps', format='eps')
plt.show()
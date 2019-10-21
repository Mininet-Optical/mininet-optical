import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt
import os


directory = '../test-files-sim/'

span1_osnr = []
span1_gosnr = []
span2_osnr = []
span2_gosnr = []
span3_osnr = []
span3_gosnr = []

i = 0

for filename in os.listdir(directory):
    if i == 1000:
        break
    if filename.endswith(".json"):
        file_path = directory + str(filename)
        with open(file_path) as json_file:
            f = json.load(json_file)
            for key, items in f.items():
                _list = items[0]
                span1_osnr.append(_list['osnr'][0])
                span2_osnr.append(_list['osnr'][1])
                span3_osnr.append(_list['osnr'][2])
                span1_gosnr.append(_list['gosnr'][0])
                span2_gosnr.append(_list['gosnr'][1])
                span3_gosnr.append(_list['gosnr'][2])
            i += 1
        continue
    else:
        continue

with open('../test-files-qot/spans_qot_0.json') as json_file:
    f = json.load(json_file)
    for key, items in f.items():
        _list = items[0]
        qot_span1_osnr = _list['osnr'][0]
        qot_span2_osnr = _list['osnr'][1]
        qot_span3_osnr = _list['osnr'][2]
        qot_span1_gosnr = _list['gosnr'][0]
        qot_span2_gosnr = _list['gosnr'][1]
        qot_span3_gosnr = _list['gosnr'][2]
# x = range(len(span1_osnr))
# plt.plot(x, span1_gosnr, '--', color='cyan', label='gOSNR-Span-1')
# plt.plot(x, span2_gosnr, '--', color='magenta', label='gOSNR-Span-2')
# plt.plot(x, span3_gosnr, '--', color='green', label='gOSNR-Span-3')
# plt.scatter(x, span1_osnr, color='black', marker='+', label='OSNR-Span-1')
# plt.scatter(x, span2_osnr, color='red', marker='^', label='OSNR-Span-2')
# plt.scatter(x, span3_osnr, color='blue', marker='v', label='OSNR-Span-3')
# plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
#            ncol=3, mode="expand", borderaxespad=0.)
# plt.xlabel("Simulation run number")
# plt.ylabel("OSNR/gOSNR (dB)")
# plt.show()

"""
Plotting whisker
"""
# fig, ax = plt.subplots(nrows=3, ncols=2)
#
# x_ticks_configs = {'axis': 'x',
#                    'which': 'both',
#                    'bottom': False,
#                    'top': False,
#                    'labelbottom': False}
#
# ax[0, 0].boxplot(span1_osnr)
# ax[0, 0].scatter(1.2, qot_span1_osnr, color='k', marker='+')
# ax[0, 0].annotate('QoT-E', (1.2, qot_span1_osnr+.1))
# ax[0, 0].tick_params(**x_ticks_configs)
# ax[0, 0].set_yticks(np.arange(min(span1_osnr), max(span1_osnr) + 0.4, 0.4))
# ax[0, 0].legend(('Span 1',), loc='lower left', handletextpad=0, handlelength=0)
#
# ax[1, 0].boxplot(span2_osnr)
# ax[1, 0].scatter(1.2, qot_span2_osnr, color='k', marker='+')
# ax[1, 0].annotate('QoT-E', (1.2, qot_span2_osnr+.1))
# ax[1, 0].tick_params(**x_ticks_configs)
# ax[1, 0].set_yticks(np.arange(min(span2_osnr), max(span2_osnr) + 0.4, 0.4))
# ax[1, 0].legend(('Span 2',), loc='lower left', handletextpad=0, handlelength=0)
#
# ax[2, 0].boxplot(span3_osnr)
# ax[2, 0].scatter(1.2, qot_span3_osnr, color='k', marker='+')
# ax[2, 0].annotate('QoT-E', (1.2, qot_span3_osnr+.1))
# ax[2, 0].tick_params(**x_ticks_configs)
# ax[2, 0].set_yticks(np.arange(min(span3_osnr), max(span3_osnr) + 0.4, 0.4))
# ax[2, 0].legend(('Span 3',), loc='lower left', handletextpad=0, handlelength=0)
#
# ax[0, 1].boxplot(span1_gosnr)
# ax[0, 1].scatter(1.2, qot_span1_gosnr, color='k', marker='+')
# ax[0, 1].annotate('QoT-E', (1.2, qot_span1_gosnr+.02))
# ax[0, 1].tick_params(**x_ticks_configs)
# ax[0, 1].set_yticks(np.arange(min(span1_gosnr), max(span1_gosnr) + 0.2, 0.2))
# ax[0, 1].legend(('Span 1',), loc='lower left', handletextpad=0, handlelength=0)
#
# ax[1, 1].boxplot(span2_gosnr)
# ax[1, 1].scatter(1.2, qot_span2_gosnr, color='k', marker='+')
# ax[1, 1].annotate('QoT-E', (1.2, qot_span2_gosnr+.02))
# ax[1, 1].tick_params(**x_ticks_configs)
# ax[1, 1].set_yticks(np.arange(qot_span2_gosnr, max(span2_gosnr) + 0.2, 0.2))
# ax[1, 1].legend(('Span 2',), loc='lower left', handletextpad=0, handlelength=0)
#
# ax[2, 1].boxplot(span3_gosnr)
# ax[2, 1].scatter(1.2, qot_span3_gosnr, color='k', marker='+')
# ax[2, 1].annotate('QoT-E', (1.2, qot_span3_gosnr+.02))
# ax[2, 1].tick_params(**x_ticks_configs)
# ax[2, 1].set_yticks(np.arange(qot_span3_gosnr, max(span3_gosnr) + 0.2, 0.2))
# ax[2, 1].legend(('Span 3',), loc='lower left', handletextpad=0, handlelength=0)
#
# fig.tight_layout()
# plt.show()

"""
Statistics
"""
# span1_osnr = []
# span1_gosnr = []
# span2_osnr = []
# span2_gosnr = []
# span3_osnr = []
# span3_gosnr = []
# qot_span1_osnr = _list['osnr'][0]
# qot_span2_osnr = _list['osnr'][1]
# qot_span3_osnr = _list['osnr'][2]
# qot_span1_gosnr = _list['gosnr'][0]
# qot_span2_gosnr = _list['gosnr'][1]
# qot_span3_gosnr = _list['gosnr'][2]

list_qot_span1_osnr = [qot_span1_osnr] * len(span1_osnr)
list_qot_span2_osnr = [qot_span2_osnr] * len(span2_osnr)
list_qot_span3_osnr = [qot_span3_osnr] * len(span3_osnr)

osnr_mse_span_1 = sqrt(mean_squared_error(span1_osnr, list_qot_span1_osnr))
osnr_mse_span_2 = sqrt(mean_squared_error(span2_osnr, list_qot_span2_osnr))
osnr_mse_span_3 = sqrt(mean_squared_error(span3_osnr, list_qot_span3_osnr))

osnr_mae_span_1 = sqrt(mean_absolute_error(span1_osnr, list_qot_span1_osnr))
osnr_mae_span_2 = sqrt(mean_absolute_error(span2_osnr, list_qot_span2_osnr))
osnr_mae_span_3 = sqrt(mean_absolute_error(span3_osnr, list_qot_span3_osnr))
print(osnr_mse_span_1)
print(osnr_mse_span_2)
print(osnr_mse_span_3)
print(osnr_mae_span_1)
print(osnr_mae_span_2)
print(osnr_mae_span_3)
print("+++")
list_qot_span1_gosnr = [qot_span1_gosnr] * len(span1_gosnr)
list_qot_span2_gosnr = [qot_span2_gosnr] * len(span2_gosnr)
list_qot_span3_gosnr = [qot_span3_gosnr] * len(span3_gosnr)

gosnr_mse_span_1 = sqrt(mean_squared_error(span1_gosnr, list_qot_span1_gosnr))
gosnr_mse_span_2 = sqrt(mean_squared_error(span2_gosnr, list_qot_span2_gosnr))
gosnr_mse_span_3 = sqrt(mean_squared_error(span3_gosnr, list_qot_span3_gosnr))

gosnr_mae_span_1 = sqrt(mean_absolute_error(span1_gosnr, list_qot_span1_gosnr))
gosnr_mae_span_2 = sqrt(mean_absolute_error(span2_gosnr, list_qot_span2_gosnr))
gosnr_mae_span_3 = sqrt(mean_absolute_error(span3_gosnr, list_qot_span3_gosnr))
print(gosnr_mse_span_1)
print(gosnr_mse_span_2)
print(gosnr_mse_span_3)
print(gosnr_mae_span_1)
print(gosnr_mae_span_2)
print(gosnr_mae_span_3)

import matplotlib.pyplot as plt
import numpy as np
import json

test = 'equalisation-tests/no-equalisation/'
dir_sim = '/home/alan/Trinity-College/Research/Agile-Cloud/one-env-PTL/' + test + 'opm-sim/'
dir_qot = '/home/alan/Trinity-College/Research/Agile-Cloud/one-env-PTL/' + test + 'opm-sim-qot/'

for i in range(13, 16):
    _id = str(i)
    opm = 'opm_' + _id + '/'
    file = 't1_81.json'

    osnr_sim = []
    osnr_qot = []
    gosnr_sim = []
    gosnr_qot = []

    f_path_sim = dir_sim + opm + file
    with open(f_path_sim) as json_file:
        f = json.load(json_file)
        for key, items in f.items():
            i = 0
            for element in items:
                k = list(element.keys())[0]
                if i == 0:
                    osnr_sim = element[k]
                    i += 1
                else:
                    gosnr_sim = element[k]

    f_path_qot = dir_qot + opm + file
    with open(f_path_qot) as json_file:
        f = json.load(json_file)
        for key, items in f.items():
            i = 0
            for element in items:
                k = list(element.keys())[0]
                if i == 0:
                    osnr_qot = element[k]
                    i += 1
                else:
                    gosnr_qot = element[k]

    plt.plot(osnr_sim, color='b', label='simulation', linestyle='None', marker='s', markerfacecolor='None')
    plt.plot(osnr_qot, color='r', label='estimation', linestyle='None', marker='D', markerfacecolor='None')
    plt.legend()
    plt.grid(True)
    n = '/home/alan/Trinity-College/Research/Agile-Cloud/one-env-PTL/equalisation-tests/no-equalisation/eq' + _id + '.eps'
    plt.savefig(n, format='eps')
    plt.clf()
    # plt.show()

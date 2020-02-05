import matplotlib.pyplot as plt
import numpy as np
import json

test = 'opm-monitoring-points/equalisation-tests/no-equalisation/'
dir_sim = '/Users/adiaz/Documents/Trinity-College/Research/Agile-Cloud/PTL2019/' + test + 'opm-sim/'
dir_qot = '/Users/adiaz/Documents/Trinity-College/Research/Agile-Cloud/PTL2019/' + test + 'opm-sim-qot/'

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

    plt.plot(gosnr_sim, color='b', label='simulation', linestyle='None', marker='s', markerfacecolor='None')
    plt.plot(gosnr_qot, color='r', label='estimation', linestyle='None', marker='D', markerfacecolor='None')
    # plt.yticks(np.arange(20.0, 22.4, 0.1))
    plt.legend()
    plt.grid(True)
    n = '/Users/adiaz/Documents/Trinity-College/Research/Agile-Cloud/PTL2019/' + test + 'eq' + _id + '_eq.eps'
    plt.savefig(n, format='eps')
    plt.clf()
    # plt.show()

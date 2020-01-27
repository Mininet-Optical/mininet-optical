import matplotlib.pyplot as plt
import numpy as np
import json


dir_sim = '/home/alan/Trinity-College/Research/Agile-Cloud/one-env-PTL/opm-sim/'
dir_qot = '/home/alan/Trinity-College/Research/Agile-Cloud/one-env-PTL/opm-sim-qot/'
opm = 'opm_7/'
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

plt.plot(gosnr_sim, color='b', label='simulation')
plt.plot(gosnr_qot, color='r', label='estimation')
plt.legend()
plt.show()

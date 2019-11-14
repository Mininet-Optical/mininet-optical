import numpy as np
import json
import matplotlib.pyplot as plt


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10*np.log10(absolute_value)
    return db_value


dir = '../monitoring-power-noise/'
dir_file = dir + 'roadm_frankfurt.json'

_keys = ['ase_noise_in', 'power_in', 'power_out', 'ase_noise_out']

noise = []
power = []

with open(dir_file) as json_file:
    data = json.load(json_file)
    for _dict in data['tests']:
        if list(_dict.keys())[0] == 'ase_noise_in' or list(_dict.keys())[0] == 'ase_noise_out':
            noise.append(list(_dict.values())[0])
        else:
            power.append(list(_dict.values())[0])

    db_noise = []
    db_power = []
    for _ln, _lp in zip(noise, power):
        db_noise.append([abs_to_db(x) for x in _ln])
        db_power.append([abs_to_db(x) for x in _lp])
    colors = ['blue', 'red']
    for _ln, _lp in zip(db_noise, db_power):
        c = colors.pop()
        ax1 = plt.subplot(221)
        ax1.set_ylabel('ASE noise (dB)')
        plt.plot(_ln, c)
        ax2 = plt.subplot(222)
        ax2.set_ylabel('Power (dBm)')
        plt.plot(_lp, c)

    # Compute OSNR and plot
    db_osnr = []
    for _ln, _lp in zip(noise, power):
        db_osnr.append([abs_to_db(x/y) for x, y in zip(_lp, _ln)])
    for osnr in db_osnr:
        ax3 = plt.subplot(212)
        ax3.set_ylabel('OSNR (dB)')
        plt.plot(osnr)
    plt.xlabel('Channel index')
    plt.show()

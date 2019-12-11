"""
Development testing file.
"""
import numpy as np
import json
import matplotlib.pyplot as plt
import os


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10*np.log10(absolute_value)
    return db_value


dir = '../monitoring-nli-noise/'

nli = []
for file in os.listdir(dir):
    if file.endswith('.json'):
        with open(dir + file) as json_file:
            data = json.load(json_file)
            for _dict in data['tests']:
                nli.append(list(_dict.values())[0])

db_nli = []
for n in nli:
    tmp = [abs_to_db(i * 1.0e0) for i in n]
    db_nli.append(tmp)

for v in db_nli:
    plt.plot(v)
plt.show()

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

# a = nli[0]
# b = nli[1]
# # d = nli[2]
# c = [x + y for x, y in zip(a, b)]
# plt.plot(c)
for v in nli:
    plt.plot(v)
plt.show()

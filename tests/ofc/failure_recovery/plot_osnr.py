import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
# figure(num=None, figsize=(7, 6), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20


def plot_osnr(_list):
    x = np.arange(11, 21)
    plt.plot(x, _list, linestyle='None', linewidth=4, color='g', marker='D', markersize=8, markerfacecolor='None',)
    plt.xlabel("Channel index")
    plt.ylabel("OSNR (dB)")
    plt.show()


def plot_list_osnr(_list):
    fig_count = 1
    for element in _list:
        plt.figure(fig_count)
        plt.xlabel("Channel index")
        plt.ylabel("OSNR (dB)")
        plt.plot(element, linestyle='None', linewidth=4, color='g', marker='D', markersize=8, markerfacecolor='None', )
        fig_count += 1
    plt.show()

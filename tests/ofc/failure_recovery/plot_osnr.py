import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
figure(num=None, figsize=(9, 7), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 24


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


def plot_1(_list):
    wv = ['1541.2', '1537.2', '1533.2', '1529.6']
    x = []
    for j in range(3):
        x.append(wv.pop())
        for i in range(9):
            if j == 2 and i == 8:
                x.append(wv.pop())
            else:
                x.append('')

    plt.plot(_list, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.xticks(range(30), x)
    plt.yticks(np.arange(14.5, 23, 0.9))
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    plt.grid(True)
    plt.savefig('fig1.png', format='png')
    # plt.show()


def plot_2(_list):
    wv = ['1541.2', '1537.2', '1533.2', '1529.6']
    x = []
    for j in range(3):
        x.append(wv.pop())
        for i in range(9):
            if j == 2 and i == 8:
                x.append(wv.pop())
            else:
                x.append('')

    plt.plot(_list, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.xticks(range(30), x)
    plt.yticks(np.arange(9.5, 15.6, 1.2))
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    plt.grid(True)
    plt.savefig('fig2.png', format='png')
    # plt.show()


def plot_3(_list):
    wv = ['1541.2', '1537.2', '1533.2', '1529.6']
    x = []
    for j in range(2):
        x.append(wv.pop())
        for i in range(9):
            if j == 1 and i == 8:
                x.append(wv.pop())
            else:
                x.append('')

    plt.plot(_list, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.xticks(range(20), x)
    plt.yticks(np.arange(23.1, 23.6, 0.1))
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    plt.grid(True)
    plt.savefig('fig3.png', format='png')
    # plt.show()

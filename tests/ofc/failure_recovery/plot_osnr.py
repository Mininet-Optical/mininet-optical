import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager

# Plot configuration parameters
# figure(num=None, figsize=(9, 7), dpi=256)
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


def plot_1_10(_list, _list2):
    wv = ['1545.2', '1541.2', '1537.2', '1533.2', '1529.6']
    wv.reverse()
    plt.xticks([0, 10, 20, 30, 40], wv)
    x1 = np.arange(0, 10)
    x2 = np.arange(10, 20)
    x3 = np.arange(20, 30)
    x4 = np.arange(30, 40)

    ch1 = _list[:10]
    ch2 = _list[10:20]
    ch3 = _list[20:30]
    ch4 = _list[30:40]

    ch1_g = _list2[:10]
    ch2_g = _list2[10:20]
    ch3_g = _list2[20:30]
    ch4_g = _list2[30:40]

    plt.plot(x1, ch1, linestyle='None', linewidth=4, color='b', marker='D', markersize=10)
    plt.plot(x2, ch2, linestyle='None', linewidth=4, color='g', marker='D', markersize=10)
    plt.plot(x3, ch3, linestyle='None', linewidth=4, color='k', marker='D', markersize=10)
    plt.plot(x4, ch4, linestyle='None', linewidth=4, color='y', marker='D', markersize=10)

    plt.plot(x1, ch1_g, linestyle='None', linewidth=4, color='b', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x2, ch2_g, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x3, ch3_g, linestyle='None', linewidth=4, color='k', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x4, ch4_g, linestyle='None', linewidth=4, color='y', marker='D', markersize=10, markerfacecolor='None', )
    # plt.xticks(range(30), x)
    plt.yticks(np.arange(20, 35.3, 1.5))
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("OSNR (solid) / gOSNR (open) [dB]")
    plt.grid(True)
    plt.savefig('fig1.png', format='png')
    # plt.show()


def plot_1(_list, _list2):
    x1 = np.arange(0, 5)
    x2 = np.arange(5, 10)
    x3 = np.arange(10, 15)
    x4 = np.arange(15, 20)

    ch1 = _list[:5]
    ch2 = _list[5:10]
    ch3 = _list[10:15]
    ch4 = _list[15:20]

    ch1_g = _list2[:5]
    ch2_g = _list2[5:10]
    ch3_g = _list2[10:15]
    ch4_g = _list2[15:20]

    plt.plot(x1, ch1, linestyle='None', linewidth=4, color='b', marker='D', markersize=10)
    plt.plot(x2, ch2, linestyle='None', linewidth=4, color='g', marker='D', markersize=10)
    plt.plot(x3, ch3, linestyle='None', linewidth=4, color='k', marker='D', markersize=10)
    plt.plot(x4, ch4, linestyle='None', linewidth=4, color='y', marker='D', markersize=10)

    plt.plot(x1, ch1_g, linestyle='None', linewidth=4, color='b', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x2, ch2_g, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x3, ch3_g, linestyle='None', linewidth=4, color='k', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x4, ch4_g, linestyle='None', linewidth=4, color='y', marker='D', markersize=10, markerfacecolor='None', )
    # plt.yticks(np.arange(20, 35.3, 1.5))
    wv = ['1537.2', '1535.2', '1533.2', '1531.2', '1529.6']
    wv.reverse()
    plt.xticks([0, 5.0, 10.0, 15.0, 20.0], wv)
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("OSNR (solid) / gOSNR (open) [dB]")
    plt.grid(True)
    # plt.savefig('../fig1.png', format='png')
    plt.show()


def plot_2_10(_list):
    wv = ['1545.2', '1541.2', '1537.2', '1533.2', '1529.6']
    wv.reverse()
    plt.xticks([0, 10, 20, 30, 40], wv)
    ch1 = _list[:10]
    x1 = np.arange(0, 10)
    ch2 = _list[10:20]
    x2 = np.arange(10, 20)
    ch3 = _list[20:30]
    x3 = np.arange(20, 30)
    ch4 = _list[30:40]
    x4 = np.arange(30, 40)

    plt.plot(x1, ch1, linestyle='None', linewidth=4, color='b', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x2, ch2, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x3, ch3, linestyle='None', linewidth=4, color='k', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x4, ch4, linestyle='None', linewidth=4, color='y', marker='D', markersize=10, markerfacecolor='None', )
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    # plt.yticks(np.arange(9.5, 23.5, 1.5))
    plt.grid(True)
    plt.savefig('../fig2.png', format='png')
    # plt.show()


def plot_2(_list):
    wv = ['1537.2', '1535.2', '1533.2', '1531.2', '1529.6']
    wv.reverse()
    plt.xticks([0, 5, 10, 15, 20], wv)
    ch1 = _list[:5]
    x1 = np.arange(0, 5)
    ch2 = _list[5:10]
    x2 = np.arange(5, 10)
    ch3 = _list[10:15]
    x3 = np.arange(10, 15)
    ch4 = _list[15:20]
    x4 = np.arange(15, 20)

    plt.plot(x1, ch1, linestyle='None', linewidth=4, color='b', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x2, ch2, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x3, ch3, linestyle='None', linewidth=4, color='k', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x4, ch4, linestyle='None', linewidth=4, color='y', marker='D', markersize=10, markerfacecolor='None', )
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    wv = ['1537.2', '1535.2', '1533.2', '1531.2', '1529.6']
    wv.reverse()
    plt.xticks([0, 5, 10, 15, 20], wv)
    plt.yticks(np.arange(18.5, 28, 1.5))
    plt.grid(True)
    plt.savefig('../fig2.png', format='png')
    # plt.show()


def plot_3_10(_list):
    wv = ['1553.2', '1549.2', '1545.2', '1541.2', '1537.2', '1533.2', '1529.6']
    wv.reverse()
    plt.xticks([0, 10, 20, 30, 40, 50, 60], wv)
    ch5 = _list[:10]
    x5 = np.arange(50, 60)
    ch1 = _list[10:20]
    x1 = np.arange(0, 10)
    ch2 = _list[20:30]
    x2 = np.arange(10, 20)

    plt.plot(x1, ch1, linestyle='None', linewidth=4, color='b', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x2, ch2, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x5, ch5, linestyle='None', linewidth=4, color='purple', marker='D', markersize=10, markerfacecolor='None', )

    plt.yticks(np.arange(20.5, 21.6, 0.2))
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    plt.grid(True)
    plt.savefig('fig3.png', format='png')
    # plt.show()


def plot_3(_list):
    ch5 = _list[:5]
    x5 = np.arange(20, 25)
    ch1 = _list[5:10]
    x1 = np.arange(0, 5)
    ch2 = _list[10:15]
    x2 = np.arange(5, 10)

    plt.plot(x1, ch1, linestyle='None', linewidth=4, color='b', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x2, ch2, linestyle='None', linewidth=4, color='g', marker='D', markersize=10, markerfacecolor='None', )
    plt.plot(x5, ch5, linestyle='None', linewidth=4, color='purple', marker='D', markersize=10, markerfacecolor='None', )

    plt.yticks(np.arange(23.2, 24.2, 0.2))
    wv = ['1539.2', '1537.2', '1535.2', '1533.2', '1531.2', '1529.6']
    wv.reverse()
    plt.xticks([0, 5, 10, 15, 20, 25], wv)
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    plt.grid(True)
    plt.savefig('../fig3.png', format='png')
    # plt.show()


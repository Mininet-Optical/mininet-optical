import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import matplotlib.font_manager


# figure(num=None, figsize=(7, 6), dpi=256)
del matplotlib.font_manager.weight_dict['roman']
matplotlib.font_manager._rebuild()
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 20


def plot_osnr(_list):
    plt.plot(_list, linestyle='None', linewidth=4, color='g', marker='D', markersize=8, markerfacecolor='None',)
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
    wv = ['1529.6', '1533.2', '1537.2', '1541.2']
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
    plt.xlabel("Wavelength index [nm]")
    plt.ylabel("gOSNR (dB)")
    # plt.savefig('fig2.png', format='png')
    plt.show()

    


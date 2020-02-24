import matplotlib.pyplot as plt


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


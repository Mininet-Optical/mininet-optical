import numpy as np
from topo.linear import LinearTopology
import matplotlib.pyplot as plt


def db_to_abs(db_value):
    """
    :param db_value: list or float
    :return: Convert dB to absolute value
    """
    absolute_value = 10**(db_value/float(10))
    return absolute_value


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10*np.log10(absolute_value)
    return db_value


def run(net):
    load = 9
    lt_1 = net.name_to_node['lt_1']

    configure_terminal(lt_1, load)

    configure_roadms(net, load)

    transmit(lt_1)

    monitor(net)


def configure_terminal(term, channel_no, signal_ids=None):
    """
    Configure the transceivers from the terminals.
    """
    if signal_ids:
        channels = signal_ids
    else:
        channels = list(np.arange(1, channel_no + 1))

    transceivers = term.transceivers
    out_port = 100
    # transceiver, out_port, channels
    for i, ch in enumerate(channels):
        t = transceivers[i]
        term.configure_terminal(t, out_port, [ch])


def configure_roadms(net, channel_no, signal_ids=None):
    roadm_1 = net.name_to_node['roadm_1']
    roadm_2 = net.name_to_node['roadm_2']
    roadm_3 = net.name_to_node['roadm_3']
    roadm_4 = net.name_to_node['roadm_4']
    roadm_5 = net.name_to_node['roadm_5']
    roadm_6 = net.name_to_node['roadm_6']
    roadm_7 = net.name_to_node['roadm_7']
    roadm_8 = net.name_to_node['roadm_8']
    roadm_9 = net.name_to_node['roadm_9']
    roadm_10 = net.name_to_node['roadm_10']
    roadm_11 = net.name_to_node['roadm_11']
    roadm_12 = net.name_to_node['roadm_12']
    roadm_13 = net.name_to_node['roadm_13']
    roadm_14 = net.name_to_node['roadm_14']
    roadm_15 = net.name_to_node['roadm_15']

    if signal_ids:
        channels = signal_ids
    else:
        channels = list(np.arange(1, channel_no + 1))

    roadm_1.install_switch_rule(1, 0, 101, channels)
    roadm_2.install_switch_rule(1, 1, 102, channels)
    roadm_3.install_switch_rule(1, 1, 102, channels)
    roadm_4.install_switch_rule(1, 1, 102, channels)
    roadm_5.install_switch_rule(1, 1, 102, channels)
    roadm_6.install_switch_rule(1, 1, 102, channels)
    roadm_7.install_switch_rule(1, 1, 102, channels)
    roadm_8.install_switch_rule(1, 1, 102, channels)
    roadm_9.install_switch_rule(1, 1, 102, channels)
    roadm_10.install_switch_rule(1, 1, 102, channels)
    roadm_11.install_switch_rule(1, 1, 102, channels)
    roadm_12.install_switch_rule(1, 1, 102, channels)
    roadm_13.install_switch_rule(1, 1, 102, channels)
    roadm_14.install_switch_rule(1, 1, 102, channels)
    roadm_15.install_switch_rule(1, 1, 100, channels)


def transmit(term):
    out_port = [100]
    term.turn_on(out_port)


def monitor(net):
    print("*** Monitoring interfaces")
    # Retrieve number of amplifiers (or monitoring nodes)
    num_amplifiers = int((len(net.amplifiers) / 2) + 1)
    osnrs = {i: [] for i in range(1, num_amplifiers)}
    gosnrs = {i: [] for i in range(1, num_amplifiers)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'opm_'
    cut = 0
    plotting_osnr = []
    plotting_gosnr = []
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        osnrs[key] = opm.get_list_osnr()
        gosnrs[key] = opm.get_list_gosnr()

    # Retrieve only the channels of interest
    osnr_cut = []
    for span, _list in osnrs.items():
        osnr_cut.append(_list[cut])
    plotting_osnr.append(osnr_cut)

    gosnr_cut = []
    for span, _list in gosnrs.items():
        gosnr_cut.append(_list[cut])
    plotting_gosnr.append(gosnr_cut)

    for o, g in zip(plotting_osnr, plotting_gosnr):
        plt.plot(o, color='g', label='OSNR')
        plt.plot(g, 'b', label='gOSNR')
    plt.legend()
    plt.xlabel('amplifier number')
    plt.ylabel('OSNR and gOSNR [dB]')
    plt.show()


if __name__ == '__main__':
    net = LinearTopology.build(op=-2, non=15)
    run(net)

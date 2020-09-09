"""
This is a helper script to check fast and easy
performance of the physical models.

"""


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
    load = 81
    lt_1 = net.name_to_node['lt_1']

    configure_terminal(lt_1, load)

    for i in range(1, load + 1):
        pass
        #configure_transceiver(lt_1, i)

    configure_roadms(net, load)

    transmit(lt_1)

    # monitor(net)


def configure_transceiver(term, tid):
    tr_name = 't' + str(tid)
    term.configure_symbol_rate(tr_name, 64e9)


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


def plot_monitor(net):
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
    for opm, _list in osnrs.items():
        osnr_cut.append(_list[cut])
    plotting_osnr.append(osnr_cut)

    gosnr_cut = []
    for opm, _list in gosnrs.items():
        gosnr_cut.append(_list[cut])
    plotting_gosnr.append(gosnr_cut)

    for o, g in zip(plotting_osnr, plotting_gosnr):
        plt.plot(o, color='g', label='OSNR')
        plt.plot(g, 'b', label='gOSNR')
    plt.legend()
    plt.yticks(np.arange(12.5, 35, 0.5))
    plt.xlabel('amplifier number')
    plt.ylabel('OSNR and gOSNR [dB]')
    plt.grid(True)
    #plt.show()
    print(plotting_gosnr)


def monitor(net):
    # Retrieve number of amplifiers (or monitoring nodes)
    num_amplifiers = int((len(net.amplifiers) / 2) + 1)
    osnrs = {i: [] for i in range(1, num_amplifiers)}
    gosnrs = {i: [] for i in range(1, num_amplifiers)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'opm_'
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        gosnrs[key] = opm.get_dict_gosnr()

    for opm, _dict in gosnrs.items():
        _gosnrs = _dict.values()
        max_val = max(_gosnrs)
        min_val = min(_gosnrs)
        mean = np.mean(list(_gosnrs))
        print(list(_gosnrs))
        for ch, _gosnr in _dict.items():
            if _gosnr == max_val:
                print("max val ", ch, max_val)
            if _gosnr == min_val:
                print("min val ", ch, min_val)
            if ch.index == 9:
                print(_gosnr)
        print("mean val ", mean)


def simple_analysis():
    prev = [10.91133808116804, 10.59341742427818, 10.367168188505353, 10.1565395852077, 9.998458013805658,
            9.879226327315331, 9.803409729494852, 9.765737181844992, 9.755465803803798, 9.756810639526234,
            9.765396843553688, 9.78168392584163, 9.807929401600399, 9.848526965621229, 9.917174362583747,
            10.010434884244484, 10.129728168686942, 10.267557037662606, 10.42558326679633, 10.581650569290051,
            10.72709210865555, 10.854194621240786, 10.956673905236062, 11.031066445816666, 11.083748586481102,
            11.117653940258009, 11.139813933811602, 11.15854078395282, 11.188468656534347, 11.26361729035635]
    conf = [11.592270784099142, 11.22118475602138, 10.943603779033868, 10.67655900640524, 10.468696040881998,
            10.303991846685804, 10.187619008480503, 10.112765490270096, 10.069569359559825, 10.041219184717605,
            10.02044852066506, 10.011304699519943, 10.018919228494793, 10.04693679986018, 10.111335264209554,
            10.207159097557897, 10.338916905493472, 10.494966526390282, 10.678958782401725, 10.86575590299666,
            11.04573711718996, 11.20598881663537, 11.338581354423592, 11.436847948110657, 11.503713717837456,
            11.541097084274348, 11.55351706535826, 11.553573715177528, 11.545261126989192, 11.552912844085352]
    th = [10] * 30

    plt.xlabel('channel index')
    plt.ylabel('gOSNR [dB]')
    plt.plot(prev, 'b', label='R = 25 GBaud')
    plt.plot(conf, 'g', label='R = 64 GBaud')
    plt.plot(th, 'r', label='QoT threshold')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    # simple_analysis()
    net = LinearTopology.build(op=0, non=15)
    run(net)

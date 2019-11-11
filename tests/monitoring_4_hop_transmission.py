import sys
sys.path.append('../optical-network-emulator/')
from topo.deutsche_telekom import DeutscheTelekom
import matplotlib.pyplot as plt
import numpy as np
import json


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


j = 0
while j < 1:
    print("*** Running for test %d" % j)
    json_struct = {'tests': []}
    json_id = 'test_' + str(j)
    net = DeutscheTelekom.build()
    """
    print("Number of line terminals: %s" % len(net.line_terminals))
    print("Number of ROAMDs: %s" % len(net.roadms))
    print("Number of links: %s" % len(net.links))
    """
    lt_koln = net.name_to_node['lt_koln']
    lt_munchen = net.name_to_node['lt_munchen']

    roadm_koln = net.name_to_node['roadm_koln']
    roadm_frankfurt = net.name_to_node['roadm_frankfurt']
    roadm_nurnberg = net.name_to_node['roadm_nurnberg']
    roadm_munchen = net.name_to_node['roadm_munchen']

    # for port, node in roadm_koln.port_to_node_out.items():
    #     print("%s reachable through port %s" % (node.name, port))
    # for port, node in roadm_koln.port_to_node_in.items():
    #     print("roadm_munchen reachable by %s through port %s" % (node.name, port))

    wavelength_indexes = range(1, 82)
    roadm_koln.install_switch_rule(1, 0, 103, wavelength_indexes)
    roadm_frankfurt.install_switch_rule(1, 2, 104, wavelength_indexes)
    roadm_nurnberg.install_switch_rule(1, 1, 103, wavelength_indexes)
    roadm_munchen.install_switch_rule(1, 1, 100, wavelength_indexes)

    resources = {'transceiver': lt_koln.name_to_transceivers['t1'], 'required_wavelengths': wavelength_indexes}
    traffic_req1 = net.transmit(lt_koln, lt_munchen, resources=resources)

    osnrs = {}
    gosnrs = {}
    for i in range(0, 19):
        osnrs[i] = []
        gosnrs[i] = []

    opm_name_base = 'verification_opm'
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        for i in wavelength_indexes:
            signal = traffic_req1.get_signal(i)
            opm = net.name_to_node[opm_name]
            osnrs[key].append(opm.get_osnr(signal))
            if key == 0:
                gosnrs[key].append(opm.get_osnr(signal))
            else:
                gosnrs[key].append(opm.get_gosnr(signal))

    channels = [1, 16, 31, 46, 61, 76]
    osnr_c1 = []
    osnr_c16 = []
    osnr_c31 = []
    osnr_c46 = []
    osnr_c61 = []
    osnr_c76 = []
    gosnr_c1 = []
    gosnr_c16 = []
    gosnr_c31 = []
    gosnr_c46 = []
    gosnr_c61 = []
    gosnr_c76 = []
    for span, _list in osnrs.items():
        osnr_c1.append(_list[0])
        osnr_c16.append(_list[15])
        osnr_c31.append(_list[30])
        osnr_c46.append(_list[45])
        osnr_c61.append(_list[60])
        osnr_c76.append(_list[75])

    # plt.plot(x, tmp, color='green', marker='o')
    for span, _list in gosnrs.items():
        gosnr_c1.append(_list[0])
        gosnr_c16.append(_list[15])
        gosnr_c31.append(_list[30])
        gosnr_c46.append(_list[45])
        gosnr_c61.append(_list[60])
        gosnr_c76.append(_list[75])

    sim = osnr_c76
    all_channels_sim = [osnr_c1, osnr_c16, osnr_c31, osnr_c46, osnr_c61, osnr_c76]
    simg = gosnr_c76
    all_channels_simg = [gosnr_c1, gosnr_c16, gosnr_c31, gosnr_c46, gosnr_c61, gosnr_c76]
    theo = []
    init = osnr_c76[0]
    theo.append(init)
    for i in range(1, 19):
        theo.append(-2 + 58 - 0.22*60 - 6 - 10*np.log10(i))

    boost_keys = [11, 15]
    colors = ['blue', 'red', 'green', 'black', 'cyan', 'purple']
    tmp = False
    for s in all_channels_sim:
        if not tmp:
            plt.plot(s, color='green', marker='*', label='OSNR-Simulation 6-ch')
            tmp = True
        else:
            plt.plot(s, color='green', marker='*')

    colors = ['blue', 'gray', 'green', 'black', 'yellow', 'purple']
    tmp = False
    for s in all_channels_simg:
        if not tmp:
            plt.plot(s, '--', color='green', marker='*', label='gOSNR-Simulation 6-ch')
            tmp = True
        else:
            plt.plot(s, '--', color='green', marker='*')

    plt.plot(theo, '--', color='red', label="OSNR-Analytical model", marker='o')

    plt.ylabel("OSNR/gOSNR (dB)")
    plt.xlabel("Spans and hops")
    ticks = [str(i) for i in range(0, 19)]
    plt.xticks((range(19)), ticks)
    plt.yticks(np.arange(13, 47, 2))
    plt.grid(True)
    plt.legend()
    plt.show()
    j += 1

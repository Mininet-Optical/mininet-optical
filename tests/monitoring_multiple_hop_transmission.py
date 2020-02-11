# from topo.deutsche_telekom import DeutscheTelekom
from topo.linear import LinearTopology
import numpy as np
import json
from pprint import pprint


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


# This won't run unless modified
test_run = 1
while test_run <= 1000:
    print("*** Running for test %d" % test_run)
    test_id = 't' + str(test_run)
    # different wavelength loads corresponding
    # to 30, 60 and 90 % of wavelength capacity
    j = 0
    _load = [27, 54, 81]
    while j < 3:
        json_struct = {'tests': []}
        load = _load[j]
        load_id = str(load)
        net = LinearTopology.build(non=15)

        # pprint(net.name_to_node)
        # print()

        # # 2-hop analysis: Berlin to Leipzig
        # lt_berlin = net.name_to_node['lt_berlin']
        # lt_leipzig = net.name_to_node['lt_leipzig']
        #
        # roadm_berlin = net.name_to_node['roadm_berlin']
        # roadm_leipzig = net.name_to_node['roadm_leipzig']
        #
        # # for port, node in roadm_leipzig.port_to_node_out.items():
        # #     print("%s reachable through port %s" % (node.name, port))
        # # for port, node in roadm_leipzig.port_to_node_in.items():
        # #     print("ROADM-Leipzig reachable by %s through port %s" % (node.name, port))
        #
        # wavelength_indexes = range(1, load + 1)
        # roadm_berlin.install_switch_rule(1, 0, 103, wavelength_indexes)
        # roadm_leipzig.install_switch_rule(1, 1, 100, wavelength_indexes)
        #
        # resources = {'transceiver': lt_berlin.name_to_transceivers['t1'], 'required_wavelengths': wavelength_indexes}
        # net.transmit(lt_berlin, roadm_berlin, resources=resources)
        #
        # 3-hop analysis: Frankfurt to Stuttgart to Ulm
        # lt_frankfurt = net.name_to_node['lt_frankfurt']
        # lt_ulm = net.name_to_node['lt_ulm']
        #
        # roadm_frankfurt = net.name_to_node['roadm_frankfurt']
        # roadm_stuttgart = net.name_to_node['roadm_stuttgart']
        # roadm_ulm = net.name_to_node['roadm_ulm']
        #
        # # for port, node in roadm_ulm.port_to_node_out.items():
        # #     print("%s reachable through port %s" % (node.name, port))
        # # for port, node in roadm_ulm.port_to_node_in.items():
        # #     print("ROADM-Ulm reachable by %s through port %s" % (node.name, port))
        #
        # wavelength_indexes = range(1, load + 1)
        # roadm_frankfurt.install_switch_rule(1, 0, 105, wavelength_indexes)
        # roadm_stuttgart.install_switch_rule(1, 1, 103, wavelength_indexes)
        # roadm_ulm.install_switch_rule(1, 2, 100, wavelength_indexes)
        #
        # resources = {'transceiver': lt_frankfurt.name_to_transceivers['t1'],
        #              'required_wavelengths': wavelength_indexes}
        # net.transmit(lt_frankfurt, roadm_frankfurt, resources=resources)

        # 4-hop analysis: Koln to Frankfurt to Nurnberg to Munchen
        # lt_koln = net.name_to_node['lt_koln']
        # lt_munchen = net.name_to_node['lt_munchen']
        #
        # roadm_koln = net.name_to_node['roadm_koln']
        # roadm_frankfurt = net.name_to_node['roadm_frankfurt']
        # roadm_nurnberg = net.name_to_node['roadm_nurnberg']
        # roadm_munchen = net.name_to_node['roadm_munchen']
        #
        # # for port, node in roadm_munchen.port_to_node_out.items():
        # #     print("%s reachable through port %s" % (node.name, port))
        # # for port, node in roadm_munchen.port_to_node_in.items():
        # #     print("roadm_munchen reachable by %s through port %s" % (node.name, port))
        #
        # wavelength_indexes = range(1, load + 1)
        # roadm_koln.install_switch_rule(1, 0, 103, wavelength_indexes)
        # roadm_frankfurt.install_switch_rule(1, 2, 104, wavelength_indexes)
        # roadm_nurnberg.install_switch_rule(1, 1, 103, wavelength_indexes)
        # roadm_munchen.install_switch_rule(1, 1, 100, wavelength_indexes)
        #
        # resources = {'transceiver': lt_koln.name_to_transceivers['t1'], 'required_wavelengths': wavelength_indexes}
        # net.transmit(lt_koln, roadm_koln, resources=resources)

        # # 5-hop analysis: Hamburg to Munchen
        # lt_hamburg = net.name_to_node['lt_hamburg']
        # lt_munchen = net.name_to_node['lt_munchen']
        #
        # roadm_hamburg = net.name_to_node['roadm_hamburg']
        # roadm_hannover = net.name_to_node['roadm_hannover']
        # roadm_leipzig = net.name_to_node['roadm_leipzig']
        # roadm_nurnberg = net.name_to_node['roadm_nurnberg']
        # roadm_munchen = net.name_to_node['roadm_munchen']

        # for port, node in roadm_hamburg.port_to_node_out.items():
        #     print("%s reachable through port %s" % (node.name, port))
        # for port, node in roadm_hamburg.port_to_node_in.items():
        #     print("roadm_hamburg reachable by %s through port %s" % (node.name, port))

        # wavelength_indexes = range(1, load + 1)
        # roadm_hamburg.install_switch_rule(1, 0, 103, wavelength_indexes)
        # roadm_hannover.install_switch_rule(1, 5, 106, wavelength_indexes)
        # roadm_leipzig.install_switch_rule(1, 3, 104, wavelength_indexes)
        # roadm_nurnberg.install_switch_rule(1, 2, 103, wavelength_indexes)
        # roadm_munchen.install_switch_rule(1, 1, 100, wavelength_indexes)
        #
        # resources = {'transceiver': lt_hamburg.name_to_transceivers['t1'], 'required_wavelengths': wavelength_indexes}
        # net.transmit(lt_hamburg, roadm_hamburg, resources=resources)

        lt_1 = net.name_to_node['lt_1']

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

        # Install switch rules into the ROADM nodes
        wavelength_indexes = range(1, load + 1)
        roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
        roadm_2.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_3.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_4.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_5.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_6.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_7.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_8.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_9.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_10.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_11.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_12.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_13.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_14.install_switch_rule(1, 1, 102, wavelength_indexes)
        roadm_15.install_switch_rule(1, 1, 100, wavelength_indexes)

        rw = wavelength_indexes
        # Set resources to use and initiate transmission
        resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
        net.transmit(lt_1, roadm_1, resources=resources)

        # THIS CAN BE IMPROVED IF ALSO CHECKING THE LAT OPM
        # AND THEN SAVE TO A FILE.
        # SAVING HALF THE TIME.
        opm_63 = net.name_to_node['opm_63']
        osnrs = opm_63.get_list_osnr()
        gosnrs = opm_63.get_list_gosnr()

        _osnr_id = 'osnr_load_' + load_id
        _gosnr_id = 'gosnr_load_' + load_id
        json_struct['tests'].append({_osnr_id: osnrs})
        json_struct['tests'].append({_gosnr_id: gosnrs})
        json_file_name = '../test-loads-sim/10_hop/' + test_id + '_10_hop_load_' + str(load_id) + '.json'
        with open(json_file_name, 'w+') as outfile:
            json.dump(json_struct, outfile)
        j += 1
    test_run += 1
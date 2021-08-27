"""
This script is to help in the validation of the simulation system in Mininet-Optical
against that from the GNPy project.

This project creates 14400 simulation tests with Mininet-Optical
Each test models a linear optical transmission scenario with varying features:

    Power levels to test:
        -12, -10, -8, -6, -4, -2, 0, 2, 4 and 6 dBm - Vector size: 10
    Fibre lengths:
        50, 60, 70, 80, 90, 100 and 120 km - Vector size: 7
    Number of spans between hops:
        1, 2, 3 - Vector size: 3
    ROADM hops:
        1, 2, 3, 4, 5 and 6 - Vector size: 6
    Number of sequentially transmitted signals:
        5, 10, 20, 30, 40, 50, 60, 70, 80 and 90 - Vector size: 10

GNPy simulation test outputs are logged to file: gnpy_tests.csv

gnpy_tests.csv has the dimensions 14400 x 12
    test no, frequency, launch power, fibre length, spans, hops, signal no, power, ASE noise, NLI noise, OSNR, GSNR
"""

import time
import itertools
from helper_structs import transceiver, fibre_span, roadm, edfa
import gnpy
from gnpy.tools.json_io import network_from_json, load_equipment
from gnpy.core.utils import db2lin, lin2db, automatic_nch
from gnpy.core.network import build_network
from gnpy.core.info import create_input_spectral_information
from gnpy.core.elements import Transceiver
from networkx import dijkstra_path

# Equipment configuration file with added EDFAs
eqpt_library_name = '../tests/data/eqpt_config.json'


def add_transceivers(json_struct, hop_no):
    """
    Add tx-1 and rx-$hop_no to the json_struct
    :param json_struct:
    :param hop_no: int, number of hops
    :return:
    """
    tx = transceiver.copy()
    tx["uid"] = "tx1"
    rx = transceiver.copy()
    rx["uid"] = "rx" + str(hop_no)
    json_struct["elements"].append(dict(tx.items()))
    json_struct["elements"].append(dict(rx.items()))
    return json_struct


def add_roadms(json_struct, power_dBm, hop_no):
    """
    Add Roadms to json_struct
    :param json_struct: dict, network elements and their connections
    :param power_dBm: int, power levels in dBm
    :param hop_no: int, hop number
    :return:
    """
    for roadm_no in range(1, hop_no + 1):
        roadm_x = roadm.copy()
        roadm_x["uid"] = "roadm" + str(roadm_no)
        roadm_x["params"]["target_pch_out_db"] = -17 + power_dBm
        json_struct["elements"].append(roadm_x)
    return json_struct


def add_spans(json_struct, fibre_length_km, span_no, hop_no):
    """
    Add spans to json_struct
    :param json_struct: dict, network elements and their connections
    :param fibre_length_km: int, fibre length in km
    :param span_no: int, span number
    :param hop_no: int, hop number
    :return:
    """
    for i in range(1, hop_no + 1):
        for j in range(1, span_no + 1):
            span_ij = fibre_span.copy()
            span_ij["uid"] = "span" + str(i) + "_" + str(j)
            span_ij["params"]["length"] = fibre_length_km
            json_struct["elements"].append(span_ij)
    return json_struct


def add_edfas(json_struct, fibre_length_km, span_no, hop_no):
    """
    Add EDFAs to json_struct
    :param json_struct: dict, network elements and their connections
    :param fibre_length_km: int, fibre length in km
    :param span_no: int, span number
    :param hop_no: int, hop number
    :return:
    """
    fibre_length_to_edfa_type =\
        {50: 'mo_gain_11',
         60: 'mo_gain_13', 70: 'mo_gain_15', 80: 'mo_gain_17', 90: 'mo_gain_19', 100: 'mo_gain_22', 110: 'mo_gain_24',
         120: 'mo_gain_26'}
    for i in range(1, hop_no + 1):
        boost_amp = edfa.copy()
        boost_amp["uid"] = "boost" + str(i)
        boost_amp["type_variety"] = "mo_gain_boost"
        json_struct["elements"].append(boost_amp)
        for j in range(1, span_no + 1):
            edfa_ij = edfa.copy()
            edfa_ij["uid"] = "edfa" + str(i) + "_" + str(j)
            edfa_ij["type_variety"] = fibre_length_to_edfa_type[fibre_length_km]
            json_struct["elements"].append(edfa_ij)
    return json_struct


def add_connections(json_struct, span_no, hop_no):
    """
    Add connections to json_struct
    :param json_struct: dict, network elements and their connections
    :param span_no: int, number of spans
    :param hop_no: int, number of hops
    :return:
    """
    conn = {"from_node": "", "to_node": ""}
    # Connect tx1 --> roadm1
    conn_tx_roadm = conn.copy()
    conn_tx_roadm["from_node"] = "tx1"
    conn_tx_roadm["to_node"] = "roadm1"
    json_struct["connections"].append(conn_tx_roadm)

    # Iterate through hops
    for i in range(1, hop_no + 1):
        conn_roadm_boost = conn.copy()
        conn_roadm_boost["from_node"] = "roadm" + str(i)
        conn_roadm_boost["to_node"] = "boost" + str(i)
        json_struct["connections"].append(conn_roadm_boost)

        conn_boost_span = conn.copy()
        conn_boost_span["from_node"] = "boost" + str(i)
        conn_boost_span["to_node"] = "span" + str(i) + "_" + str(1)
        json_struct["connections"].append(conn_boost_span)

        # iterate through spans after hops
        conn_span_edfa = {}
        for j in range(1, span_no + 1):
            if j > 1:
                conn_edfa_span = conn.copy()
                conn_edfa_span["from_node"] = "edfa" + str(i) + "_" + str(j - 1)
                conn_edfa_span["to_node"] = "span" + str(i) + "_" + str(j)
                json_struct["connections"].append(conn_edfa_span)
            conn_span_edfa = conn.copy()
            conn_span_edfa["from_node"] = "span" + str(i) + "_" + str(j)
            conn_span_edfa["to_node"] = "edfa" + str(i) + "_" + str(j)
            json_struct["connections"].append(conn_span_edfa)

        conn_end_link = conn.copy()
        conn_end_link["from_node"] = conn_span_edfa["to_node"]
        if 1 < hop_no != i:
            # connect to subsequent hop
            conn_end_link["to_node"] = "roadm" + str(i + 1)
        else:
            # connect to receiver end
            conn_end_link["to_node"] = "rx" + str(hop_no)
        json_struct["connections"].append(conn_end_link)

    return json_struct


def create_net_json_struct(power_dBm, fibre_length_km, span_no, hop_no, _signal_no):
    """
    Create the json structure that will define the network elements and the topology
    :param power_dBm: int, power levels in dBm
    :param fibre_length_km: int, fibre length in km
    :param span_no: int, number of spans in each interlink connection
    :param hop_no: int, number of hops in linear topology
    :param _signal_no, int, number of signals (unused param)
    :return:
    """
    json_struct = {
        "elements": [],
        "connections": []
    }
    json_struct = add_transceivers(json_struct, hop_no)
    json_struct = add_roadms(json_struct, power_dBm, hop_no)
    json_struct = add_spans(json_struct, fibre_length_km, span_no, hop_no)
    json_struct = add_edfas(json_struct, fibre_length_km, span_no, hop_no)
    json_struct = add_connections(json_struct, span_no, hop_no)
    return json_struct


def gnpy_tests(test_no, c, logdata=False):
    """
    Model a network topology given the parameters in c
    :param test_no: int, test number
    :param c: tuple, test combination with parameters
    :param logdata: boolean, indicate whether to log results in file
    :return:
    """
    # retrieve parameters from c and create spectral information
    power_dBm = c[0]
    power_mW = db2lin(power_dBm) * 1e-3
    signal_no = c[4]
    hop_no = c[3]
    spacing = 50e9  # THz
    si = create_input_spectral_information(191.3e12, 191.3e12 + signal_no * spacing,
                                           0.0, 32e9, power_mW, spacing)
    f_min = 191.3e12
    f_max = si.carriers[-1].frequency
    total_power_dBm = power_dBm + lin2db(automatic_nch(f_min, f_max, spacing))
    # build network model (topology)
    build_network(network, equipment, power_dBm, total_power_dBm)

    transceivers = {n.uid: n for n in network.nodes() if isinstance(n, Transceiver)}
    source = next(transceivers[uid] for uid in transceivers if uid == 'tx1')
    dest = 'rx' + str(hop_no)
    sink = next(transceivers[uid] for uid in transceivers if uid == dest)
    # compute the end-to-end path in the linear topology
    path = dijkstra_path(network, source, sink)

    # Iterate through each element in the path.
    # Automated processes upon object __call__
    for el_no, el in enumerate(path):
        if el_no == len(path) - 1:
            si = el(si, logdata=logdata, test_no=test_no, c=c)
        else:
            if isinstance(el, gnpy.core.elements.Roadm):
                si = el(si, 1000)
            else:
                si = el(si)


if __name__ == '__main__':
    # Feature sets
    power_levels_dBm = range(-12, 8, 2)
    fibre_lengths_km = list(range(50, 130, 10))
    span_no = range(1, 4)  # span no between hops
    hop_no = range(1, 7)
    signal_no = [5] + list(range(10, 100, 10))

    start_time = time.time()
    # create all possible combinations with the sets
    combinations = itertools.product(power_levels_dBm,
                                     fibre_lengths_km,
                                     span_no, hop_no, signal_no)
    equipment = load_equipment(eqpt_library_name)
    for test_number, combination in enumerate(combinations, start=1):
        if test_number > 2:
            break
        # create json-like object from the combination
        net_json = create_net_json_struct(*combination)
        # create network object from the json-like object
        network = network_from_json(net_json, equipment)
        # pass combination and execute test
        gnpy_tests(test_number, combination, logdata=True)

    print("--- It took %s seconds to run GNPy tests ---" % (time.time() - start_time))

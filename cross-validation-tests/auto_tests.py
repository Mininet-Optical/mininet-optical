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

    Mininet-Optical simulation test outputs are logged to file: mo_tests.csv

    mo_tests.csv has the dimensions 14400 x 12

        test no, frequency, launch power, fibre length, spans, hops, signal no, power, ASE noise, NLI noise, OSNR, GSNR

    NOTE: For the cross-validation tests, this script executes two tests only.
    If you want to run the 14400 tests comment or remove the indicate lines of code in main()

"""
from mnoptical.topo.linear_params import LinearTopology
import itertools
import time


def configure_terminals(net, power_level_dBm, signal_no):
    tx = net.name_to_node['tx']
    rx = net.name_to_node['rx']

    for p, c in enumerate(range(1, signal_no + 1), start=1):
        # configure transmitter terminal
        tx_transceiver = tx.id_to_transceivers[c]
        tx.assoc_tx_to_channel(tx_transceiver, c, out_port=p)
        # configure receiver terminal
        rx_transceiver = rx.id_to_transceivers[1]
        rx.assoc_rx_to_channel(rx_transceiver, c, in_port=1)

def configure_roadms(net, hop_no, signal_no):
    if hop_no == 1:
        # case when there's only one ROADM
        r = net.roadms[0]
        for port, c in enumerate(range(1, signal_no + 1), start=1):
            r.install_switch_rule(port, 1, c)
    else:
        in_port = out_port = 0
        for i, r in enumerate(net.roadms):
            if i == 0:
                # case for first ROADM
                for in_port, c in enumerate(range(1, signal_no + 1), start=1):
                    r.install_switch_rule(in_port, out_port, c)
            elif i == len(net.roadms) - 1:
                in_port = 0
                # case for last ROADM
                for out_port, c in enumerate(range(1, signal_no + 1), start=1):
                    r.install_switch_rule(in_port, 1, c)
            else:
                # case for intermediate ROADM
                in_port = out_port = 0
                for c in range(1, signal_no + 1):
                    r.install_switch_rule(in_port, out_port, c)

def launch_transmission(net):
    tx = net.name_to_node['tx']
    tx.turn_on()

def monitor(net, test_no, c, logdata):
    power_level_dBm = c[0]
    fibre_length_km = c[1]
    span_no = c[2]
    hop_no = c[3]
    signal_no = c[4]

    rx = net.name_to_node['rx']
    optical_signals = rx.monitor.get_optical_signals()
    power_dict = rx.monitor.get_dict_power()
    ase_noise_dict = rx.monitor.get_dict_ase_noise()
    nli_noise_dict = rx.monitor.get_dict_nli_noise()
    osnr_noise_dict = rx.monitor.get_dict_osnr()
    gosnr_noise_dict = rx.monitor.get_dict_gosnr()

    if logdata:
        log_data(test_no, power_level_dBm, fibre_length_km,
                 span_no, hop_no, signal_no, optical_signals,
                 power_dict, ase_noise_dict, nli_noise_dict,
                 osnr_noise_dict, gosnr_noise_dict)

def log_data(test_no, power_level_dBm, fibre_length_km,
             span_no, hop_no, signal_no, optical_signals,
             power_dict, ase_noise_dict, nli_noise_dict,
             osnr_noise_dict, gosnr_noise_dict):
    """
    Write data to mo_test.csv
    """
    if test_no == 1:
        rows = [
            "test no,frequency,launch power,fibre length,spans,hops,signal no,power,ASE noise,NLI noise,OSNR,GSNR\n"
        ]
    else:
        rows = []
    for optical_signal in optical_signals:
        row = str(test_no) + ',' +\
              str(optical_signal.frequency) + ',' +\
              str(power_level_dBm) + ',' +\
              str(fibre_length_km) + ',' +\
              str(span_no) + ',' +\
              str(hop_no) + ',' +\
              str(signal_no) + ',' +\
              str(power_dict[optical_signal]) + ',' + \
              str(ase_noise_dict[optical_signal]) + ',' + \
              str(nli_noise_dict[optical_signal]) + ',' + \
              str(osnr_noise_dict[optical_signal]) + ',' + \
              str(gosnr_noise_dict[optical_signal]) + '\n'
        rows.append(row)
    with open('mo_tests.csv', 'a') as mo_tests:
        mo_tests.writelines(rows)



def mnoptical_test(test_no, c, logdata=False):
    """
    create Mininet-Optical model
    execute Mininet-Optical test
    clean and record Mininet-Optical model
    :param test_no: int, test number
    :param c: tuple, (power_level_dBm, fibre_length_km,
                        span_no, hop_no, signal_no)
    :return:
    """
    # create Network object
    net = LinearTopology.build(*c, debugger=False)

    # configure LineTerminals
    configure_terminals(net, c[0], c[4])

    # configure ROADMs
    configure_roadms(net, c[3], c[4])

    # launch transmission
    launch_transmission(net)

    # monitor and log
    monitor(net, test_no, c, logdata)

    del net


if __name__ == '__main__':
    # Feature sets
    power_levels_dBm = range(-12, 8, 2)
    fibre_lengths_km = list(range(50, 130, 10))
    span_no = range(1, 4)  # span no between hops
    hop_no = range(1, 7)
    signal_no = [5] + list(range(10, 100, 10))

    # create all possible combinations with the sets
    combinations = itertools.product(power_levels_dBm,
                                     fibre_lengths_km,
                                     span_no, hop_no, signal_no)
    start_time = time.time()
    for test_no, combination in enumerate(combinations, start=1):
        # remove or comment this if-clause to run the 14400 tests.
        if test_no > 2:
            break
        # execute Mininet-Optical tests
        mnoptical_test(test_no, combination, logdata=True)
    print("It took %s seconds to run Mininet-Optical tests" % str(time.time() - start_time))

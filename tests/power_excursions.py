"""
    This script can be used to check the effect of the power excursions effect
    in the EDFA class.

    It will model a linear topology with the params specified below and launch
    a transmission with as many signals as indicated in signal_no (see below).

    wdg1 will increase the average gain of the EDFAs, thus the AGC reconfiguration
    will decrease the system gain of all EDFAs.
    wdg2 will decrease the average gain of the EDFAs, thus the AGC reconfiguration
    will increase the system gain of all EDFAs.

    One can then inspect/monitor the changes by looking at the power_excursions()
    function in the EDFA class.
"""

from mnoptical.topo.linear_params import LinearTopology


power_dBm = 0
span_length_km = 25
span_no = 10
hop_no = 1
signal_no = 3
wdg_id = 'wdg1'  # change wdg_id to wdg2 for opposite effect


net = LinearTopology.build(power_dBm=power_dBm, span_length_km=span_length_km,
                           span_no=span_no, hop_no=hop_no, signal_no=signal_no, wdg_id='wdg1')

def configure_terminals():
    tx = net.name_to_node['tx']
    rx = net.name_to_node['rx']

    for p, c in enumerate(range(1, signal_no + 1), start=1):
        # configure transmitter terminal
        tx_transceiver = tx.id_to_transceivers[c]
        tx.assoc_tx_to_channel(tx_transceiver, c, out_port=p)
        # configure receiver terminal
        rx_transceiver = rx.id_to_transceivers[1]
        rx.assoc_rx_to_channel(rx_transceiver, c, in_port=1)


def configure_roadms():
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


def launch_transmission():
    tx = net.name_to_node['tx']
    tx.turn_on()


configure_terminals()
configure_roadms()
launch_transmission()
"""

    This script models a linear topology between two line terminals
    with two ROADMs in between:
        lt1 ---> r1 ---> r2 ----> lt2

    lt1 will transmit 10 channels at 0 dBm launch power

    Three function tests are enabled:
    reset_lt1: turn on lt1, reset lt1, turn on lt1
        outcome: lt1 does not transmit anything second time
    reset_r1: turn on lt1, reset r1, turn on lt1
        outcome: r1 does not find rules for the signals
    reset_r2: turn on lt1, reset r2, turn on lt1
        outcome: r2 does not find rules for the signals
"""


from mnoptical.topo.linear import LinearTopology


def reset_lt1():
    lt_1.turn_on()
    lt_1.reset()
    # safe_switch=True will indicate that the
    # repetition in the same transmission
    # is not a loop!
    lt_1.turn_on(safe_switch=True)

def reset_r1():
    lt_1.turn_on()
    r1.reset()
    lt_1.turn_on(safe_switch=True)

def reset_r2():
    lt_1.turn_on()
    r1.reset()
    lt_1.turn_on(safe_switch=True)


operational_power_dBm = 0
net = LinearTopology.build(op=operational_power_dBm, non=2)

# Retrieve line terminals (transceivers) from network
lt_1 = net.name_to_node['lt_1']
lt_2 = net.name_to_node['lt_2']

num_wavelengths = 10
ports = channel_indexes = list(range(1, num_wavelengths + 1))


for c, p in zip(channel_indexes, ports):
    # configure transmitter terminal
    tx_transceiver = lt_1.id_to_transceivers[c]
    lt_1.assoc_tx_to_channel(tx_transceiver, c, out_port=p)

    # configure receiver terminal
    rx_transceiver = lt_2.id_to_transceivers[c]
    lt_2.assoc_rx_to_channel(rx_transceiver, c, in_port=p)

# Configure ROADM 1
r1 = net.roadms[0]
for c, p in zip(channel_indexes, ports):
    in_port = 4100 + p
    out_port = 5211
    r1.install_switch_rule(in_port, out_port, [c])

# Configure ROADM 2
r2 = net.roadms[1]
for c, p in zip(channel_indexes, ports):
    in_port = 4111
    out_port = 5200 + p
    r2.install_switch_rule(in_port, out_port, [c])

# Uncomment lines below to run the tests
# Test: reset_lt1()
#reset_lt1()
# Test: reset_r1()
reset_r1()
# Test: reset_r2()
#reset_r2()
"""

    This script models a linear topology between two line terminals
    with two ROADMs in between:
        lt1 ---> r1 ---> r2 ----> lt2

    lt1 will transmit 10 channels at 0 dBm launch power
"""


from mnoptical.topo.linear import LinearTopology


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

lt_1.turn_on()

tx1 = lt_1.id_to_transceivers[1]
rx1 = lt_2.id_to_transceivers[1]
print("*** Modulation format of %s in lt_1 before reconfiguration: %s" % (tx1.name, tx1.modulation_format))
print("*** Modulation format of %s in lt_2 before reconfiguration: %s" % (rx1.name, rx1.modulation_format))
# Important: modulation format of the receiver
# needs to be updated before transmitter!
lt_2.set_modulation_format(rx1, '64QAM')
# Note: since tx1 is used as a transmitter,
# tx is set to True,
# tx default is False
lt_1.set_modulation_format(tx1, '64QAM', tx=True)
print("*** Modulation format of %s in lt_1 after reconfiguration: %s" % (tx1.name, tx1.modulation_format))
print("*** Modulation format of %s in lt_2 after reconfiguration: %s" % (rx1.name, rx1.modulation_format))
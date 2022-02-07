from mnoptical.topo.linear import LinearTopology


operational_power_dBm = 0
net = LinearTopology.build(op=operational_power_dBm, non=2, bidirectional=True)

# Retrieve line terminals (transceivers) from network
lt_1 = net.name_to_node['lt_1']
lt_2 = net.name_to_node['lt_2']

num_wavelengths = 3
ports = channel_indexes = list(range(1, num_wavelengths + 1))


for c, p in zip(channel_indexes, ports):
    # configure transmitter terminals
    lt_1_tx_transceiver = lt_1.id_to_transceivers[c]
    lt_1.assoc_tx_to_channel(lt_1_tx_transceiver, c, out_port=p)

    lt_2_tx_transceiver = lt_2.id_to_transceivers[c]
    lt_2.assoc_tx_to_channel(lt_2_tx_transceiver, c, out_port=p)

    # configure receiver terminals
    lt_2_rx_transceiver = lt_2.id_to_transceivers[c]
    lt_2.assoc_rx_to_channel(lt_2_rx_transceiver, c, in_port=p)

    lt_1_rx_transceiver = lt_1.id_to_transceivers[c]
    lt_1.assoc_rx_to_channel(lt_1_rx_transceiver, c, in_port=p)

r1 = net.roadms[0]
r2 = net.roadms[1]

# Configure ROADM 1
for c, p in zip(channel_indexes, ports):
    in_port = 4100 + p
    out_port = 5211
    r1.install_switch_rule(in_port, out_port, [c], src_node=lt_1)
    # bidirectional rule
    in_port = 4111
    out_port = 5200 + p
    r1.install_switch_rule(in_port, out_port, [c], src_node=r2)

# Configure ROADM 2
for c, p in zip(channel_indexes, ports):
    in_port = 4111
    out_port = 5200 + p
    r2.install_switch_rule(in_port, out_port, [c], src_node=r1)
    # bidirectional rule
    in_port = 4100 + p
    out_port = 5211
    r2.install_switch_rule(in_port, out_port, [c], src_node=lt_2)

lt_1.turn_on()
lt_2.turn_on()

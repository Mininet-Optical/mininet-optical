from mnoptical.topo.linear_multiloc import LinearTopology


net = LinearTopology.build()

# Retrieve line terminals (transceivers) from network
lt1 = net.name_to_node['lt1']
lt3 = net.name_to_node['lt3']
lt4 = net.name_to_node['lt4']

channel1 = 1
channel2 = 2

# configure channel1 traversing lt1 - r1 - r2 - r3 - r4 - lt4
# configure transmitter terminal
tx_transceiver = lt1.id_to_transceivers[1]
lt1.assoc_tx_to_channel(tx_transceiver, channel1, out_port=1)

# configure receiver terminal
rx_transceiver = lt4.id_to_transceivers[1]
lt4.assoc_rx_to_channel(rx_transceiver, channel1, in_port=1)

# Retrieve ROADMs from network
r1 = net.name_to_node['r1']
r2 = net.name_to_node['r2']
r3 = net.name_to_node['r3']
r4 = net.name_to_node['r4']

# in_port, out_port, signal_indices, src_node=None
r1.install_switch_rule(1, 4, channel1, src_node=lt1)
r2.install_switch_rule(4, 5, channel1, src_node=r1)
r3.install_switch_rule(4, 5, channel1, src_node=r2)
r4.install_switch_rule(4, 1, channel1, src_node=r3)

lt1.turn_on()


# configure channel1 traversing lt1 - r1 - r2 - r3 - lt3
# configure transmitter terminal
tx_transceiver = lt1.id_to_transceivers[2]
lt1.assoc_tx_to_channel(tx_transceiver, channel2, out_port=2)
# configure receiver terminal
rx_transceiver = lt3.id_to_transceivers[2]
lt3.assoc_rx_to_channel(rx_transceiver, channel2, in_port=2)

r1.install_switch_rule(2, 4, channel2, src_node=lt1)
r2.install_switch_rule(4, 5, channel2, src_node=r1)
r3.install_switch_rule(4, 2, channel2, src_node=r2)

lt1.turn_on()
print()

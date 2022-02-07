

from mnoptical.topo.linear import LinearTopology


operational_power_dBm = 0
net = LinearTopology.build(op=operational_power_dBm, non=2)

# Retrieve line terminals (transceivers) from network
lt_1 = net.name_to_node['lt_1']
lt_2 = net.name_to_node['lt_2']

num_wavelengths = 2
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
    r1.install_switch_rule(in_port, out_port, [c], src_node=lt_1)

# Configure ROADM 2
r2 = net.roadms[1]
for c, p in zip(channel_indexes, ports):
    in_port = 4111
    out_port = 5200 + p
    r2.install_switch_rule(in_port, out_port, [c], src_node=r1)

lt_1.turn_on()

print("*** Updating gain of r1_r2_amp1 to 10 dB")
r1_r2_amp1 = net.name_to_node['r1-r2-amp1']
gain = r1_r2_amp1.target_gain
r1_r2_amp1.set_gain(10)
print("*** Recover:")
r1_r2_amp1.set_gain(gain)

print("*** Updating gain of r1 boost to 10 dB")
gain = r1.boost.target_gain
r1.set_boost_gain(10)
print("*** Recover:")
r1.set_boost_gain(gain)
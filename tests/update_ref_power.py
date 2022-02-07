


from mnoptical.topo.linear import LinearTopology


operational_power_dBm = 0
net = LinearTopology.build(op=operational_power_dBm, non=2)

# Retrieve line terminals (transceivers) from network
lt_1 = net.name_to_node['lt_1']
lt_2 = net.name_to_node['lt_2']

num_wavelengths = 3
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

print("*** Turning off port 1 of lt_1")
out_ports = [1]
lt_1.turn_off(out_ports)

new_ref_power_dBm = 4
print("*** Setting reference power of r1 to %f dBm for ch-1", new_ref_power_dBm)
r1.set_reference_power(new_ref_power_dBm, ch_index=1)

print("*** Reconfigure tx1 of lt_1 to use launch power %f dBm", new_ref_power_dBm)
tx1 = lt_1.id_to_transceivers[1]
lt_1.tx_config(tx1, new_ref_power_dBm)
print("*** Reconfigure lt_1 to transmit ch-1 with tx1")
lt_1.assoc_tx_to_channel(tx_transceiver, 1, out_port=1)
print("*** Turning on lt_1")
lt_1.turn_on()


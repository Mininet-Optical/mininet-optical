import network


net = network.Network()

olt1 = net.add_olt('olt1')
tr1 = olt1.add_transceiver('t1', 'C')

roadm1 = net.add_roadm('roadm1')
roadm2 = net.add_roadm('roadm2')

olt2 = net.add_olt('olt2')
tr2 = olt2.add_transceiver('t1', 'C')

link1 = net.add_link(olt1, roadm1)
span1 = net.add_span('SMF', 100)
edfa1 = net.add_amplifier('edfa1', 'EDFA')
net.add_span_to_link(link1, span1, edfa1)

net.add_link(roadm1, olt2)


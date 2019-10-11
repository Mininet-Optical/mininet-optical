import test_topology as tp
from node import Roadm

topo = tp.TestTopology()
ols1 = topo.name_to_node['ols1']
tx_ols1 = ols1.name_to_transceivers['t1']

ols2 = topo.name_to_node['ols2']

route = topo.net.routing(ols1, ols2)
wavelength_indexes = [1, 2, 3, 4]
print(route)


# Switching rule1, for traffic from ols-1 to ols-2
# traversing roadm-A and roadm-B.

roadmA = topo.name_to_node['roadmA']
roadmA.install_switch_rule(1, 0, 100, wavelength_indexes)
roadmB = topo.name_to_node['roadmB']
roadmB.install_switch_rule(1, 0, 100, wavelength_indexes)

traffic1 = topo.net.transmit(ols1, ols2, route=route,
                             resources={'transceiver': tx_ols1, 'required_wavelengths': wavelength_indexes})

roadmA.update_switch_rule(1, 2, 0, 101, wavelength_indexes, traffic1)
topo.net.traffic.remove(traffic1)
# TO BE DEVELOPED
# New route to communicate with ols-2 (from ols-1)
# Check transmission effects.
roadmC = topo.name_to_node['roadmC']
roadmC.install_switch_rule(1, 0, 100, wavelength_indexes)
route = []
for link in topo.links:
    if link.node1 is ols1 and link.node2 is roadmA:
        route.append((ols1, link))
    if link.node1 is roadmA and link.node2 is roadmC:
        route.append((roadmA, link))
    if link.node1 is roadmC and link.node2 is ols2:
        route.append((roadmC, link))
route.append((ols2, None))

traffic2 = topo.net.transmit(ols1, ols2, route=route,
                             resources={'transceiver': tx_ols1, 'required_wavelengths': wavelength_indexes})

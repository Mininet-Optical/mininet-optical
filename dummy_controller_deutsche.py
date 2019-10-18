from deutsche_telekom import DeutscheTelekom
from pprint import pprint

net = DeutscheTelekom.build()
"""
print("Number of line terminals: %s" % len(net.line_terminals))
print("Number of ROAMDs: %s" % len(net.roadms))
print("Number of links: %s" % len(net.links))
"""
lt_berlin = net.name_to_node['lt_berlin']
lt_leipzig = net.name_to_node['lt_leipzig']

roadm_berlin = net.name_to_node['roadm_berlin']
roadm_leipzig = net.name_to_node['roadm_leipzig']

for port, node in roadm_leipzig.port_to_node_out.items():
    print("%s reachable through port %s" % (node.name, port))
for port, node in roadm_leipzig.port_to_node_in.items():
    print("ROADM-Leipzig reachable by %s through port %s" % (node.name, port))

wavelength_indexes = [1, 2, 3, 4]
roadm_berlin.install_switch_rule(1, 0, 103, wavelength_indexes)
roadm_leipzig.install_switch_rule(1, 1, 100, wavelength_indexes)
net.transmit(lt_berlin, lt_leipzig)

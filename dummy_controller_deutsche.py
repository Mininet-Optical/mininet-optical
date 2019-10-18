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

wavelength_indexes = range(1, 42)
roadm_berlin.install_switch_rule(1, 0, 103, wavelength_indexes)
roadm_leipzig.install_switch_rule(1, 1, 100, wavelength_indexes)

resources = {'transceiver': lt_berlin.name_to_transceivers['t1'], 'required_wavelengths': wavelength_indexes}
traffic_req1 = net.transmit(lt_berlin, lt_leipzig, resources=resources)
signal = traffic_req1.get_signal(41)
opm1 = net.name_to_node['opm1']
opm2 = net.name_to_node['opm2']
print("OSNR and GOSNR AT SIGNAL 1")
print(opm1.get_osnr(signal))
print(opm1.get_gosnr(signal))
print("+++++")
print("OSNR and GOSNR AT SIGNAL 1")
print(opm2.get_osnr(signal))
print(opm2.get_gosnr(signal))
print("+++++")

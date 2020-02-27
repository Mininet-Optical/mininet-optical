from topo.linear import LinearTopology
from tests.ofc.failure_recovery.plot_osnr import plot_list_osnr

net = LinearTopology.build(op=0, non=2)

lt_1 = net.name_to_node['lt_1']

roadm_1 = net.name_to_node['roadm_1']
roadm_2 = net.name_to_node['roadm_2']

wavelength_indexes = list(range(1, 12))
roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
roadm_2.install_switch_rule(1, 1, 100, wavelength_indexes)

rw = wavelength_indexes
# Set resources to use and initiate transmission
resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': rw}
net.transmit(lt_1, roadm_1, resources=resources)

opm = net.name_to_node['opm_19']
gosnr = opm.get_list_gosnr()
nli = opm.get_nonlinear_interference()

plot_list_osnr([gosnr])

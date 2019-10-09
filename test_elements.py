import network
import time
from pprint import pprint

"""
    TOPOLOGY CREATION
"""
# Create an optical-network object
net = network.Network()

# Create an optical line system object
ols1 = net.add_ols('ols1')
# Add a transceiver object to the OLS object
ols1_tr1 = ols1.add_transceiver('t1', 'C')
ols1_tr2 = ols1.add_transceiver('t2', 'C')
# ols1.update_transceiver('t2', {'modulation_format': '16QAM',
#                                'bits_per_symbol': 4.0,
#                                'symbol_rate': 0.032 * 1e12})

# Create a ROADM object
roadm1 = net.add_roadm('roadm1')

preamp_link_ols1_roadm1 = net.add_amplifier('preamp-edfa1', 'EDFA', target_gain=6)
link_ols1_roadm1 = net.add_link(ols1, roadm1, preamp=preamp_link_ols1_roadm1)
# Create a fiber span
span1 = net.add_span('SMF', 100)
# Create an amplifier (compensating for fiber span)
edfa1 = net.add_amplifier('edfa1', 'EDFA', target_gain=22)
# Add the fiber span and compensation EDFA to link_ols1_roadm1
net.add_span_to_link(link_ols1_roadm1, span1, edfa1)


roadm2 = net.add_roadm('roadm2')
preamp_link_roadm1_roadm2 = net.add_amplifier('preamp-edfa4', 'EDFA')
link_roadm1_roadm2 = net.add_link(roadm1, roadm2, preamp=preamp_link_roadm1_roadm2)
span4 = net.add_span('SMF', 100)
edfa4 = net.add_amplifier('edfa4', 'EDFA', target_gain=22)
net.add_span_to_link(link_roadm1_roadm2, span4, edfa4)


# Create an optical line system object
ols2 = net.add_ols('ols2')
# Add a transceiver object to the OLS object
ols2_tr1 = ols2.add_transceiver('t1', 'C')

preamp_link_roadm2_ols2 = net.add_amplifier('preamp-edfa2', 'EDFA')
# Add a link between ROADM1 and OLS2
link_roadm2_ols2 = net.add_link(roadm2, ols2, preamp=preamp_link_roadm2_ols2)
# Create a fiber span
span2 = net.add_span('SMF', 100)
# Create an amplifier (compensating for fiber span)
edfa2 = net.add_amplifier('edfa2', 'EDFA')
# Add the fiber span and compensation EDFA to link_roadm1_ols2
net.add_span_to_link(link_roadm2_ols2, span2, edfa2)


# Create an optical line system object
ols3 = net.add_ols('ols3')
# Add a transceiver object to the OLS object
ols3_tr1 = ols3.add_transceiver('t1', 'C')

preamp_link_roadm1_ols3 = net.add_amplifier('preamp-edfa3', 'EDFA')
# Add a link between ROADM1 and OLS2
link_roadm1_ols3 = net.add_link(roadm1, ols3, preamp=preamp_link_roadm1_ols3)
# Create a fiber span
span3 = net.add_span('SMF', 100)
# Create an amplifier (compensating for fiber span)
edfa3 = net.add_amplifier('edfa3', 'EDFA')
# Add the fiber span and compensation EDFA to link_roadm1_ols2
net.add_span_to_link(link_roadm1_ols3, span3, edfa3)

pprint(net.topology)

"""
    END TOPOLOGY CREATION
"""
tmp = False
if tmp:
    for i in range(3):
        if i == 0:
            net.transmit(ols1, ols2)
            time.sleep(1)
        elif i == 1:
            net.transmit(ols1, ols3)
            time.sleep(1)
        else:
            net.transmit(ols1, ols2)

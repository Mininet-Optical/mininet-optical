import network
import time
from pprint import pprint

"""
    TOPOLOGY CREATION
    
    OBSOLETE
"""
# Create an optical-network object
net = network.Network()

# Create an optical line system object
transceivers = [('t1', 'C'), ('t2', 'C')]
lt1 = net.add_lt('lt1')
# Add a transceiver object to the lt object
lt1_tr1 = lt1.add_transceiver('t1', 'C')
lt1_tr2 = lt1.add_transceiver
# lt1.update_transceiver('t2', {'modulation_format': '16QAM',
#                                'bits_per_symbol': 4.0,
#                                'symbol_rate': 0.032 * 1e12})

# Create a ROADM object
roadm1 = net.add_roadm('roadm1')

preamp_link_lt1_roadm1 = net.add_amplifier('preamp-edfa1', 'EDFA', target_gain=6)
link_lt1_roadm1 = net.add_link(lt1, roadm1, boost_amp=preamp_link_lt1_roadm1)
# Create a fiber span
span1 = net.add_span('SMF', 100)
# Create an amplifier (compensating for fiber span)
edfa1 = net.add_amplifier('edfa1', 'EDFA', target_gain=22)
# Add the fiber span and compensation EDFA to link_lt1_roadm1
net.add_span_to_link(link_lt1_roadm1, span1, edfa1)


roadm2 = net.add_roadm('roadm2')
preamp_link_roadm1_roadm2 = net.add_amplifier('preamp-edfa4', 'EDFA')
link_roadm1_roadm2 = net.add_link(roadm1, roadm2, boost_amp=preamp_link_roadm1_roadm2)
span4 = net.add_span('SMF', 100)
edfa4 = net.add_amplifier('edfa4', 'EDFA', target_gain=22)
net.add_span_to_link(link_roadm1_roadm2, span4, edfa4)


# Create an optical line system object
lt2 = net.add_lt('lt2')
# Add a transceiver object to the lt object
lt2_tr1 = lt2.add_transceiver('t1', 'C')

preamp_link_roadm2_lt2 = net.add_amplifier('preamp-edfa2', 'EDFA')
# Add a link between ROADM1 and lt2
link_roadm2_lt2 = net.add_link(roadm2, lt2, boost_amp=preamp_link_roadm2_lt2)
# Create a fiber span
span2 = net.add_span('SMF', 100)
# Create an amplifier (compensating for fiber span)
edfa2 = net.add_amplifier('edfa2', 'EDFA')
# Add the fiber span and compensation EDFA to link_roadm1_lt2
net.add_span_to_link(link_roadm2_lt2, span2, edfa2)


# Create an optical line system object
lt3 = net.add_lt('lt3')
# Add a transceiver object to the lt object
lt3_tr1 = lt3.add_transceiver('t1', 'C')

preamp_link_roadm1_lt3 = net.add_amplifier('preamp-edfa3', 'EDFA')
# Add a link between ROADM1 and lt2
link_roadm1_lt3 = net.add_link(roadm1, lt3, boost_amp=preamp_link_roadm1_lt3)
# Create a fiber span
span3 = net.add_span('SMF', 100)
# Create an amplifier (compensating for fiber span)
edfa3 = net.add_amplifier('edfa3', 'EDFA')
# Add the fiber span and compensation EDFA to link_roadm1_lt2
net.add_span_to_link(link_roadm1_lt3, span3, edfa3)

pprint(net.topology)

"""
    END TOPOLOGY CREATION
"""
tmp = False
if tmp:
    for i in range(3):
        if i == 0:
            net.transmit(lt1, lt2)
            time.sleep(1)
        elif i == 1:
            net.transmit(lt1, lt3)
            time.sleep(1)
        else:
            net.transmit(lt1, lt2)

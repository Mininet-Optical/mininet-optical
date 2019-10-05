import network

# Create an optical-network object
net = network.Network()

# Create an optical line system object
ols1 = net.add_ols('ols1')
# Add a transceiver object to the OLS object
tr1 = ols1.add_transceiver('t1', 'C')

# Create a ROADM object
roadm1 = net.add_roadm('roadm1')
# Create a ROADM object
roadm2 = net.add_roadm('roadm2')

# Create an optical line system object
ols2 = net.add_ols('ols2')
# Add a transceiver object to the OLS object
tr2 = ols2.add_transceiver('t1', 'C')

# Create a link between OLS1 and ROADM1
link1 = net.add_link(ols1, roadm1)
# Create a fiber span
span1 = net.add_span('SMF', 100)
# Create an amplifier (compensating for fiber span)
edfa1 = net.add_amplifier('edfa1', 'EDFA')
# Add the fiber span and compensation EDFA to link1
net.add_span_to_link(link1, span1, edfa1)

# Add a link between ROADM1 and OLS2
net.add_link(roadm1, ols2)


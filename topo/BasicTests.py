import network
from link import SpanTuple, Span

#Baby's first topologies
#Optical line cards we call transeivers
#Chassis or backplane
#Todo: Draw a Diagram of system

def Topology1():
    """This is an immensely basic linear topology, designed to be a basic simple first
    topology. This system is unidirectional, transmits from Line Terminal 1 to Line Terminal
    2 and is connected by 1 m span.

    This module is how to connect 2 transceivers by a 1 m span, and only works in 1 direction.
    We have also created two transceivers. We could have used 1 transceiver for both line
    terminals however we chose not to as to avoid bad user habits"""

    # **************************** Network Topology *********************************
    # lt_1 ---> transceiver1 ---> unidirectional_span ----> transceiver2 ----> lt_2 **
    # *******************************************************************************

    net = network.Network()
    # Trasnceiver parameters: [(name, power, band)]
    transceiver1 = ('t1', 10, 'C')
    transceiver2 = ('t2', 10, 'C')
    # Elements of our topology, transceiver - span - transceiver
    lt_1 = net.add_lt('lt_1', transceivers=[transceiver1])
    lt_2 = net.add_lt('lt_2', transceivers=[transceiver2])
    boost_amp = net.add_amplifier("boost_amp", 'EDFA', target_gain=13)

    unidirectional_span = SpanTuple(span=Span('SMF', length=15), amplifier=boost_amp)

    # Connects components together
    net.add_link(lt_1, lt_2, spans=[unidirectional_span])

    # *********************************************************************
    # ****** THIS IS THE END OF THE TOPOLOGY. BELOW IS A SIMPLE TEST ******
    # *********************************************************************

    net.transmit(lt_1, lt_2)

def Topology2():
    """Here is an extended 2 node bi-directional topology with roadm switches and amplifiers and a span
    accross The system. This reflects a much more real system designed to show a lot of the major
    systems and switching rules one can expect when running a topology.

    We will also expect an understanding of for loops, as many of our features will have for loops
    to show how they can be used in coding a topology"""
    # Initialise network
    net = network.Network()

    span_length = 80 #km length
    Target_gain = 0.22 * span_length # (db) Will be used to compensate fiber loss

    # Calling parts we will use in network
    transceiver1 = ('t1', 0, 'C')
    transceiver2 = ('t2', 0, 'C')
    lt_1 = net.add_lt('lt_1', transceivers=[transceiver1])
    lt_2 = net.add_lt('lt_2', transceivers=[transceiver2])
    roadm_1 = net.add_roadm("roadm_1")
    roadm_2 = net.add_roadm("roadm_2")
    boost_amp = net.add_amplifier("boost_amp", 'EDFA', target_gain=20.0, boost=True)
    in_line_amp = net.add_amplifier("in_line_amp", 'EDFA', target_gain=Target_gain, boost=True)
    fiber_span = SpanTuple(span=Span('SMF', length=span_length), amplifier=in_line_amp)
        # in_line amplifier attached at end of fiber span

    # Create bi-directional link between roadm_1 and LT_1
    link1 = net.add_link(lt_1, roadm_1)
    link1.add_span(Span('SMF', 0.001), amplifier=None)
    bi_link1 = net.add_link(roadm_1, lt_1)
    bi_link1.add_span(Span('SMF', 0.001), amplifier=None)

    # Create link2 between roadm_1 and LT_1
    link2 = net.add_link(lt_2, roadm_2)
    link2.add_span(Span('SMF', 0.001), amplifier=None)
    bi_link2 = net.add_link(roadm_2, lt_2)
    bi_link2.add_span(Span('SMF', 0.001), amplifier=None)

    # Link roadm's together
    net.add_link(roadm_1, roadm_2, boost_amp =boost_amp, spans=[fiber_span])
    net.add_link(roadm_2, roadm_1, boost_amp=boost_amp, spans=[fiber_span])

    # Attach monitor to inline amplifier
    opm = net.add_monitor('opm', amplifier = in_line_amp)

    # ***************************************************************************
    # ****** THIS IS THE END OF THE TOPOLOGY. BELOW IS A TEST WHICH RETURNS *****
    # ****** THE OSNR AND GOSNR. AND ALLOWS FOR A BASIC INTRO TO SWITCHING ******
    # ******* RULES. THE OUTPUT HERE IS FOR 7 WAVELENGTHS PASSED THROUGH. *******
    # ***************************************************************************

    # Allows user to see where roadm input and output ports connect.
    print("Roadm_1 input node ", roadm_1.port_to_node_in, " output node ", roadm_1.port_to_node_out)
    print("Roadm_2 input node ", roadm_2.port_to_node_in, " output node ", roadm_2.port_to_node_out)

    # Wavelgths: [191.3e9, 191.35e9, 191.4e9, 191.45e9, 191.5e9 191.55e9] (Hz)
    wavelength_indexes = range(1, 2)

    # Switching rule #1:
    #   roadm_1: (input_port = LT_1, output port = roadm_2)
    #   roadm_2: (input port = roadm_2, output port = LT_1)
    # This tells the system the signal travels the following path
    # LT_1 -> roadm_1 -> roadm_2 -> LT_2
    roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
    roadm_2.install_switch_rule(1, 1, 100, wavelength_indexes)

    resources = {'transceiver': lt_1.name_to_transceivers['t1'], 'required_wavelengths': wavelength_indexes}
    net.transmit(lt_1, roadm_1, resources=resources)
    opm = net.name_to_node['opm']
    # Returns the OSNR and gOSNR for the 6 Wavelength signals we propegate through the system
    osnr = opm.get_list_osnr()
    gosnr = opm.get_list_gosnr()

    print("Osnr = ", osnr, "     Gosnr = ", gosnr)



def Topology3():
    net = network.Network()
    span_length = 1


    in_line_amp = net.add_amplifier("in_line_amp", 'EDFA', target_gain = 1)
    fiber_span = SpanTuple(span=Span('SMF', length=span_length), amplifier=in_line_amp)

    operational_power = 0  # power in dBm
    boost_amp = net.add_amplifier("boost_amp", 'edfa', target_gain = 15)

    transceivers = [('t%s' %(i), operational_power, 'C') for i in range (0,6)]
    line_terminals = [net.add_lt('lt_%s' % (i), transceivers=[transceivers[i]], Modulation_Format='bpsk') for i in range (0,6)]

    roadm = net.add_roadm('roadm')

    net.add_link(line_terminals[0], roadm,  spans=[fiber_span], boost_amp=boost_amp)

    for i in range(1,6):
        net.add_link(roadm, line_terminals[i],  spans=[fiber_span], boost_amp=boost_amp)
    print("Roadm input node ", roadm.port_to_node_in, " output node ", roadm.port_to_node_out)

    wavelength_indexes = range(1,7)
    roadm.install_switch_rule(1, 0, 101, [1, 2, 3])
    roadm.install_switch_rule(1, 0, 102, [4, 5, 6])
    resources = {'transceiver': line_terminals[0].name_to_transceivers['t0'], 'required_wavelengths': wavelength_indexes}

    net.transmit(line_terminals[0], roadm, resources=resources)

Topology3()


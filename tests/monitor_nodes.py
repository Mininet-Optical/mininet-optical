import network
from link import SpanTuple, Span
from node import Node_Monitor

def monitor_nodes():
    """This builds a linear topology for 2 ROADM's and 2 LT"""
    net = network.Network()

    span_length = 80
    Target_gain = 0.22 * span_length


    transceiver1 = ('t1', 0, 'C')
    transceiver2 = ('t2', 0, 'C')
    lt_1 = net.add_lt('lt_1', transceivers=[transceiver1])
    lt_2 = net.add_lt('lt_2', transceivers=[transceiver2])
    roadm_1 = net.add_roadm("roadm_1",monitor={'mode':'out'}) # initialization of monitor in the output mode for ROADM
    roadm_2 = net.add_roadm("roadm_2",monitor={'mode':'in'}) # initialization of monitor in the input mode for ROADM

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


    boost_amp_1 = net.add_amplifier("boost_amp", 'EDFA', target_gain=20.0, boost=True, monitor={'mode':'out'}) # initialization of monitor with boost=True in the output mode
    link_r1_r2 = net.add_link(roadm_1, roadm_2, boost_amp=boost_amp_1)
    in_line_amp_1 = net.add_amplifier("in_line_amp", 'EDFA', target_gain=Target_gain,
                                      monitor={'mode': 'out', 'link': link_r1_r2})  # initialization of monitor with boost= False in the output mode
    fiber_span = SpanTuple(span=Span('SMF', length=span_length), amplifier=in_line_amp_1)
    link_r1_r2.spans.append(fiber_span)

    boost_amp_2 = net.add_amplifier("boost_amp_2", 'EDFA', target_gain=20.0, boost=True)
    link_r2_r1=net.add_link(roadm_2, roadm_1, boost_amp=boost_amp_2, spans=[fiber_span])

    wavelength_indexes = range(1, 6)

    roadm_1.install_switch_rule(1, 0, 101, wavelength_indexes)
    roadm_2.install_switch_rule(1, 1, 100, wavelength_indexes)

    lt_1.configure_terminal(lt_1.name_to_transceivers['t1'], 100, wavelength_indexes)
    lt_1.turn_on([100])
    opm_1 = in_line_amp_1.monitor # Accessing the monitors
    print("GOSNR in '"+opm_1.mode+"' mode at "+opm_1.component.name+" : "+str(opm_1.get_list_gosnr()))
    opm_2 = roadm_1.monitor
    print("GOSNR in '" + opm_2.mode + "' mode at " + opm_2.component.name + " : " + str(opm_2.get_list_gosnr()))
    opm_3 = roadm_2.monitor
    print("GOSNR in '" + opm_3.mode + "' mode at " + opm_3.component.name + " : " + str(opm_3.get_list_gosnr()))
    opm_3.modify_mode(mode='out') # change modes
    print("GOSNR in '" + opm_3.mode + "' mode at " + opm_3.component.name + " : " + str(opm_3.get_list_gosnr()))



    opm = Node_Monitor("boost_amp_2_opm", component=boost_amp_1) # initializing monitors separately for any component (ROADM, Amplifiers)
    print("GOSNR in '" + opm.mode + "' mode at " + opm.component.name + " : " + str(opm.get_list_gosnr()))


    roadm_1.print_signals()
    roadm_2.print_signals()




if __name__ == '__main__':
    monitor_nodes()
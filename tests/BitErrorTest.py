import network
from link import SpanTuple, Span



def Topology1():


    net = network.Network()
    transceiver1 = ('t1', 0, 'C')
    transceiver2 = ('t2', 0, 'C')
    lt_1 = net.add_lt('lt_1', transceivers=[transceiver1], monitor_mode='out')
    compensating_amp = net.add_amplifier("boost_amp", 'EDFA', target_gain=.22*15)
    lt_2 = net.add_lt('lt_2', transceivers=[transceiver2], monitor_mode='in')

    net.add_link(lt_1, lt_2, spans=[(Span('SMF', length=15), compensating_amp)])

    mon2 = lt_2.monitor
    lt_1.configure_terminal(lt_1.transceivers[0], 1, 0)
    lt_1.turn_on()
    print( 'monitor:', mon2)
    print( 'OSNR', mon2.get_list_osnr(), 'gOSNR', mon2.get_list_gosnr() )
    print(mon2.get_ber('qpsk'))
Topology1()

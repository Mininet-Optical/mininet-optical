#!/usr/bin/python
"""
single_link_test.py: test monitoring on a single link

Note this version uses and depends on explicit port assignment!
"""

from network import Network
from link import Span as Fiber, SpanTuple as Segment
from node import Transceiver
from units import *

# Units


km = dB = dBm = 1.0
m = .001

# Parameters

NUM_WAV = 20
# ROADM port numbers (input and output)
LINE_PORT = NUM_WAV
LINE_PORT2 = NUM_WAV+1


# Physical model API helpers

def Span( km, amp=None ):
    "Return a fiber segment of length km with a compensating amp"
    return Segment( span=Fiber( length=km ), amplifier=amp )


# Physical Network simulation, created out of base PHY model objects

def twoRoadmPhyNetwork( lengths=[50*km] ):

    """Two ROADMs connected bidirectionally over a single link consisting
       of a boost amplifier and one or more fiber spans with compensating
       amplifiers. Source terminal tx1 is connected to source ROADM r1,
       and destination ROADM r2 is connected to destination terminal tx2,
       as follows:

       Eastbound:
       tx1 -> r1 -> boost1e -> fiber span -> amp1e (...) -> r2 -> tx2

       Westbound:
       tx1 <- r1 <- (...) amp1w <- fiber span <- boost1w <- r2 <- tx2

       We assign the port numbers explicitly and symmetrically:

       tx1:0 -> 1:r1:0 -> 0:r2:1 -> 0:tx2
       tx1:0 <- 1:r1:0 <- 0:r2:1 <- 0:tx2

       Which is to say ROADM ports in:0 and out:0 are LINE ports
       and ROADM ports in:1 and out:1 are ADD/DROP ports.

       Getting the port assignment right and the rules right
       is an essential, but tricky, part of getting any SDN
       network to work properly.
    """
    net = Network()

    # Network nodes
    transceivers = [ ( 't%d' % i, 0*dBm, 'C' )  for i in range(1, NUM_WAV+1) ]
    # two terminals, each includes t1 and t2
    terminals = tx1, tx2 = [
        net.add_lt( name, transceivers=transceivers, monitor_mode=mode )
        for name,mode in [('tx1','in'),('tx2','in')] ]
    roadms = r1, r2 = [ net.add_roadm( 'r%d' % i ) for i in (1, 2) ]

    # Convenience alias
    link = net.add_link

    # Eastbound WAN link consisting of a boost amplifier going into
    # one or more segments of fiber with compensating amplifiers
    boost = net.add_amplifier( 'boost1e', target_gain=17*dB, boost=True )
    spans = []
    for i, length in enumerate( lengths, start=1 ):
        amp = net.add_amplifier(
            'amp%de' % i, target_gain=11*dB, monitor_mode='out')
        span = Span( length, amp=amp )
        spans.append( span )

    link( r1, r2, src_out_port=LINE_PORT, dst_in_port=LINE_PORT, boost_amp=boost,
          spans=spans )

    # Westbound WAN link consisting of a boost amplifier going into
    # one or more segments of fiber with compensating amplifiers
    boost = net.add_amplifier( 'boost1w', target_gain=17*dB, boost=True )
    spans = []
    for i, length in enumerate( lengths, start=1 ):
        amp = net.add_amplifier(
            'amp%dw' % i, target_gain=11*dB, monitor_mode='out')
        span = Span( length, amp=amp )
        spans.append( span )

    link( r2, r1, src_out_port=LINE_PORT, dst_in_port=LINE_PORT, boost_amp=boost,
          spans=spans )

    # Local add/drop links between terminals/transceivers and ROADMs
    for add_drop_port in range(NUM_WAV):
        link( tx1, r1, src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
        link( r1, tx1, src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
        link( tx2, r2, src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
        link( r2, tx2, src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )

    """# tx1:t1->r1
    link( tx1, r1, src_out_port=TX_0, dst_in_port=ADD_DROP_0, spans=[Span(1*m)] )
    # tx1:t2->r1
    link( tx1, r1, src_out_port=TX_1, dst_in_port=ADD_DROP_1, spans=[Span(1*m)] )
    # tx1:t1<-r1
    link( r1, tx1, src_out_port=ADD_DROP_0, dst_in_port=TX_0, spans=[Span(1*m)] )
    # tx1:t2<-r1
    link( r1, tx1, src_out_port=ADD_DROP_1, dst_in_port=TX_1, spans=[Span(1*m)] )

    # tx2:t2->r2
    link( tx2, r2, src_out_port=TX_0, dst_in_port=ADD_DROP_0, spans=[Span(1*m)] )
    # tx2:t2->r2
    link( tx2, r2, src_out_port=TX_1, dst_in_port=ADD_DROP_1, spans=[Span(1*m)] )
    # tx2:t1<-r2
    link( r2, tx2, src_out_port=ADD_DROP_0, dst_in_port=TX_0, spans=[Span(1*m)] )
    # tx2:t2<-r2
    link( r2, tx2, src_out_port=ADD_DROP_1, dst_in_port=TX_1, spans=[Span(1*m)] )
    #"""

    return net


# Physical model test

def twoRoadmPhyTest():
    # ROADM port numbers (input and output)
    LINE_PORT = NUM_WAV
    LINE_PORT2 = NUM_WAV+1

    #ADD_DROP_0 = 0
    #ADD_DROP_1 = 1

    # Line terminal port numbers (input and output)
    #TX_0 = 0
    #TX_1 = 1

    "Create a single link and monitor its OSNR and gOSNR"
    net = twoRoadmPhyNetwork( lengths=[50*km, 50*km, 50*km] )
    nodes = net.name_to_node
    tx1, tx2 = nodes[ 'tx1' ], nodes[ 'tx2' ]
    roadms = r1, r2 = nodes[ 'r1' ], nodes[ 'r2' ]
    t11, t12 = tx1.name_to_transceivers['t1'],tx1.name_to_transceivers['t2']
    t21, t22 = tx2.name_to_transceivers['t1'],tx2.name_to_transceivers['t2']

    # Configure ROADMS to add/drop channel 1 to local terminal
    chs = ch1, ch2 = 1, 2
    route = [('tx1', 'r1', 'r2', 'tx2'), chs]
    path = route[0]
    rule_id_dict = {'r1':1, 'r2':1}

    for i in range(1, len(path) - 1 ):
        node1, roadm, node2 = path[i-1], path[i], path[i+1]
        if i == 1:
            for ch in chs:
                nodes[roadm].install_switch_rule(rule_id = rule_id_dict[roadm], in_port=ch-1, out_port=LINE_PORT, signal_indices=[ch] )
                rule_id_dict[roadm] += 1
        elif i == len(path) - 2:
            for ch in chs:
                nodes[roadm].install_switch_rule(rule_id = rule_id_dict[roadm], in_port=LINE_PORT, out_port=ch-1, signal_indices=[ch] )
                rule_id_dict[roadm] += 1
        else:
            nodes[roadm].install_switch_rule(rule_id = rule_id_dict[roadm], in_port=LINE_PORT, out_port=LINE_PORT2, signal_indices=[ch] )
            rule_id_dict[roadm] += 1

    """r1.install_switch_rule(
        rule_id = 1, in_port=ch1-1, out_port=LINE_PORT, signal_indices=[ch1] )
    r1.install_switch_rule(
        rule_id = 2, in_port=ch2-1, out_port=LINE_PORT, signal_indices=[ch2])
    r2.install_switch_rule(
        rule_id = 1, in_port=LINE_PORT, out_port=ch1-1, signal_indices=[ch1])
    r2.install_switch_rule(
        rule_id = 2, in_port=LINE_PORT, out_port=ch2-1, signal_indices=[ch2])
    #"""

    print( '*** ROADM connections and flow table' )
    for node in r1, r2:
        print( node, 'inputs', node.port_to_node_in )
        print( node, 'outputs', node.port_to_node_in )
        print( node, 'flow table', node.port_to_optical_signal_out )

    print( '*** Checking correct ROADM flow tables' )
    print(r1, r1.switch_table)
    print(r2, r2.switch_table)

    # start test
    # launch power 0dbm
    t11.operation_power = db_to_abs(2)
    t12.operation_power = db_to_abs(2)
    t21.operation_power = db_to_abs(2)
    t22.operation_power = db_to_abs(2)
    r1.configure_voa(channel_id = ch1, output_port = LINE_PORT,operational_power_dB = 2)
    r1.configure_voa(channel_id =ch2, output_port = LINE_PORT, operational_power_dB = 2)
    r2.configure_voa(channel_id =ch1, output_port = ch1-1, operational_power_dB = 2)
    r2.configure_voa(channel_id =ch2, output_port = ch2-1, operational_power_dB = 2)
    print( '*** Starting test transmission...' )
    tx1.configure_terminal(tx1.transceivers[0], 1)
    tx1.configure_terminal(tx1.transceivers[1], 2)
    tx1.turn_on()

    print( '*** Initial OSNR and gOSNR:' )
    monitors = [ node.monitor for node in [tx2] ]
    for mon in monitors:
        print( 'monitor:', mon )
        optical_signals = mon.extract_optical_signal()
        for sig in optical_signals:
            power = mon.get_power(sig)
            print( 'sig_power', sig[0], power )
        print( 'OSNR', mon.get_list_osnr(), 'gOSNR', mon.get_list_gosnr() )

    # launch power -10dbm
    print('=======================================================')
    t11.operation_power = db_to_abs(-5)
    t12.operation_power = db_to_abs(-5)
    t21.operation_power = db_to_abs(-5)
    t22.operation_power = db_to_abs(-5)
    r1.configure_voa(channel_id = ch1, output_port = LINE_PORT,operational_power_dB = -5)
    r1.configure_voa(channel_id =ch2, output_port = LINE_PORT, operational_power_dB = -5)
    r2.configure_voa(channel_id =ch1, output_port = ch1-1, operational_power_dB = -5)
    r2.configure_voa(channel_id =ch2, output_port = ch2-1, operational_power_dB = -5)
    print( '*** Starting test transmission...' )
    tx1.configure_terminal(tx1.transceivers[0], 1)
    tx1.configure_terminal(tx1.transceivers[1], 2)
    tx1.turn_on()

    print( '*** Initial OSNR and gOSNR:' )
    monitors = [ node.monitor for node in [tx2] ]
    for mon in monitors:
        print( 'monitor:', mon )
        optical_signals = mon.extract_optical_signal()
        for sig in optical_signals:
            power = mon.get_power(sig)
            print( 'sig_power', sig[0], power )
        print( 'OSNR', mon.get_list_osnr(), 'gOSNR', mon.get_list_gosnr() )
    #'''

if __name__ == '__main__':
    twoRoadmPhyTest()

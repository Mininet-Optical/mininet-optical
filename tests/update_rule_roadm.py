#!/usr/bin/env python3

"""
single_link_test.py: test monitoring on a single link

Note this version uses and depends on explicit port assignment!
"""

from network import Network
from link import Span as Fiber, SpanTuple as Segment
from node import Transceiver

# Units

km = dB = dBm = 1.0
m = .001


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
    transceivers = [ ( 't1', 0*dBm, 'C' ) ]
    terminals = tx1, tx2, tx3 = [
        net.add_lt( name, transceivers=transceivers, monitor_mode=mode )
        for name,mode in [('tx1','in'),('tx2','in'),('tx3','in')] ]
    roadms = r1, r2, r3 = [ net.add_roadm( 'r%d' % i ) for i in (1, 2, 3) ]

    # ROADM port numbers (input and output)
    LINE_PORT_1 = 1
    LINE_PORT_2 = 2

    # ROADM communicating to LT
    ADD_DROP_0 = 0

    # Line terminal port numbers (input and output)
    TX_0 = 0

    # Convenience alias
    link = net.add_link

    # R1 - R2
    boost = net.add_amplifier( 'boost1_r1_r2', target_gain=17*dB, boost=True )
    spans = []
    for i, length in enumerate( lengths, start=1 ):
        amp = net.add_amplifier(
            'ampr1_r2%de' % i, target_gain=11*dB, monitor_mode='out')
        span = Span( length, amp=amp )
        spans.append( span )

    link( r1, r2, src_out_port=LINE_PORT_1, dst_in_port=LINE_PORT_1, boost_amp=boost,
          spans=spans )

    # R2 - R1
    boost = net.add_amplifier( 'boost1_r2_r1', target_gain=17*dB, boost=True )
    spans = []
    for i, length in enumerate( lengths, start=1 ):
        amp = net.add_amplifier(
            'ampr2_r1%dw' % i, target_gain=11*dB, monitor_mode='out')
        span = Span( length, amp=amp )
        spans.append( span )

    link( r2, r1, src_out_port=LINE_PORT_1, dst_in_port=LINE_PORT_1, boost_amp=boost,
          spans=spans )

    # R1 - R3
    boost = net.add_amplifier('boost1_r1_r3', target_gain=17 * dB, boost=True)
    spans = []
    for i, length in enumerate(lengths, start=1):
        amp = net.add_amplifier(
            'ampr1_r3%de' % i, target_gain=11 * dB, monitor_mode='out')
        span = Span(length, amp=amp)
        spans.append(span)

    link(r1, r3, src_out_port=LINE_PORT_2, dst_in_port=LINE_PORT_1, boost_amp=boost,
         spans=spans)

    # R3 - R1
    boost = net.add_amplifier('boost1_r3_r1', target_gain=17 * dB, boost=True)
    spans = []
    for i, length in enumerate(lengths, start=1):
        amp = net.add_amplifier(
            'ampr3_r1%de' % i, target_gain=11 * dB, monitor_mode='out')
        span = Span(length, amp=amp)
        spans.append(span)

    link(r3, r1, src_out_port=LINE_PORT_1, dst_in_port=LINE_PORT_2, boost_amp=boost,
         spans=spans)

    # R2 - R3
    boost = net.add_amplifier('boost1_r2_r3', target_gain=17 * dB, boost=True)
    spans = []
    for i, length in enumerate(lengths, start=1):
        amp = net.add_amplifier(
            'ampr2_r3%de' % i, target_gain=11 * dB, monitor_mode='out')
        span = Span(length, amp=amp)
        spans.append(span)

    link(r2, r3, src_out_port=LINE_PORT_2, dst_in_port=LINE_PORT_2, boost_amp=boost,
         spans=spans)

    # R3 - R2
    boost = net.add_amplifier('boost1_r3_r2', target_gain=17 * dB, boost=True)
    spans = []
    for i, length in enumerate(lengths, start=1):
        amp = net.add_amplifier(
            'ampr3_r2%de' % i, target_gain=11 * dB, monitor_mode='out')
        span = Span(length, amp=amp)
        spans.append(span)

    link(r3, r2, src_out_port=LINE_PORT_2, dst_in_port=LINE_PORT_2, boost_amp=boost,
         spans=spans)

    # Local add/drop links between terminals/transceivers and ROADMs
    link( tx1, r1, src_out_port=TX_0, dst_in_port=ADD_DROP_0, spans=[Span(1*m)] )
    link( r1, tx1, src_out_port=ADD_DROP_0, dst_in_port=TX_0, spans=[Span(1*m)] )

    link( tx2, r2, src_out_port=TX_0, dst_in_port=ADD_DROP_0, spans=[Span(1*m)] )
    link( r2, tx2, src_out_port=ADD_DROP_0, dst_in_port=TX_0, spans=[Span(1*m)] )

    link(tx3, r3, src_out_port=TX_0, dst_in_port=ADD_DROP_0, spans=[Span(1 * m)])
    link(r3, tx3, src_out_port=ADD_DROP_0, dst_in_port=TX_0, spans=[Span(1 * m)])

    # Configure ROADMS to add/drop channels 1 and 2 to local terminal
    r1.install_switch_rule(
        1, in_port=ADD_DROP_0, out_port=LINE_PORT_1, signal_indices=[1], src_node=tx1 )
    r2.install_switch_rule(
        1, in_port=LINE_PORT_1, out_port=TX_0, signal_indices=[1], src_node=r1 )

    # Rules for the opposite direction

    print( '*** ROADM connections and flow table' )
    for node in r1, r2:
        print( node, 'inputs', node.port_to_node_in )
        print( node, 'outputs', node.port_to_node_in )
        print( node, 'flow table', node.port_to_optical_signal_out )

    print( '*** Checking correct ROADM flow tables' )
    print(r1, r1.switch_table)
    print(r2, r2.switch_table)
    return net


# Physical model test

def twoRoadmPhyTest():
    "Create a single link and monitor its OSNR and gOSNR"
    net = twoRoadmPhyNetwork( lengths=[50*km, 50*km, 50*km] )
    nodes = net.name_to_node
    tx1, tx2 = nodes[ 'tx1' ], nodes[ 'tx2' ]
    r1, r2, r3 = nodes[ 'r1' ], nodes[ 'r2' ], nodes[ 'r3' ]
    print( '*** Starting test transmission...' )

    print('*** TURNING ON TERMINAL', tx1)
    tx1.configure_terminal(tx1.transceivers[0], 1)
    tx1.turn_on()

    # ROADM port numbers (input and output)
    LINE_PORT_1 = 1
    LINE_PORT_2 = 2
    ADD_DROP_0 = 0

    r3.install_switch_rule(
        1, in_port=LINE_PORT_1, out_port=LINE_PORT_2, signal_indices=[1], src_node=tx1)
    r2.install_switch_rule(
        2, in_port=LINE_PORT_2, out_port=ADD_DROP_0, signal_indices=[1], src_node=r3)

    print("*** Deleting switch rule 1 from r2")
    r2.delete_switch_rule(1)

    print("r1 is updating rule 1 towards LINE_PORT_2")
    r1.update_switch_rule(1, LINE_PORT_2)


if __name__ == '__main__':
    twoRoadmPhyTest()
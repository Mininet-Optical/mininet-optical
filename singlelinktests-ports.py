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
    transceivers = [ ( 't1', 0*dBm, 'C' ), ]
    terminals = tx1, tx2 = [
        net.add_lt( name, transceivers=transceivers, monitor_mode=mode )
        for name,mode in [('tx1','in'),('tx2','in')] ]
    roadms = r1, r2 = [ net.add_roadm( 'r%d' % i ) for i in (1, 2) ]

    # ROADM port numbers (input and output)
    LINE_0 = 0
    ADD_DROP_1 = 1

    # Line terminal port numbers (input and output)
    TX_0 = 0

    # Convenience alias
    link = net.add_link

    # Eastbound WAN link consisting of a boost amplifier going into
    # one or more segments of fiber with compensating amplifiers
    boost = net.add_amplifier( 'boost1e', target_gain=3*dB, boost=True )
    spans = []
    for i, length in enumerate( lengths, start=1 ):
        amp = net.add_amplifier(
            'amp%de' % i, target_gain=11*dB, monitor_mode='out')
        span = Span( length, amp=amp )
        spans.append( span )

    link( r1, r2, src_out_port=LINE_0, dst_in_port=LINE_0, boost_amp=boost,
          spans=spans )

    # Westbound WAN link consisting of a boost amplifier going into
    # one or more segments of fiber with compensating amplifiers
    boost = net.add_amplifier( 'boost1w', target_gain=3*dB, boost=True )
    spans = []
    for i, length in enumerate( lengths, start=1 ):
        amp = net.add_amplifier(
            'amp%dw' % i, target_gain=11*dB, monitor_mode='out')
        span = Span( length, amp=amp )
        spans.append( span )

    link( r2, r1, src_out_port=LINE_0, dst_in_port=LINE_0, boost_amp=boost,
          spans=spans )

    # Local add/drop links between terminals/transceivers and ROADMs
    link( tx1, r1, src_out_port=TX_0, dst_in_port=ADD_DROP_1, spans=[Span(1*m)] )
    link( r1, tx1, src_out_port=ADD_DROP_1, dst_in_port=TX_0, spans=[Span(1*m)] )
    link( tx2, r2, src_out_port=TX_0, dst_in_port=ADD_DROP_1, spans=[Span(1*m)] )
    link( r2, tx2, src_out_port=ADD_DROP_1, dst_in_port=TX_0, spans=[Span(1*m)] )

    # Configure ROADMS to add/drop channel 1 to local terminal
    r1.install_switch_rule(
        1, in_port=LINE_0, out_port=ADD_DROP_1, signal_indices=[1] )
    r1.install_switch_rule(
        2, in_port=ADD_DROP_1, out_port=LINE_0, signal_indices=[1] )
    r2.install_switch_rule(
        1, in_port=LINE_0, out_port=ADD_DROP_1, signal_indices=[1] )
    r2.install_switch_rule(
        2, in_port=ADD_DROP_1, out_port=LINE_0, signal_indices=[1] )

    print( '*** ROADM connections and flow table' )
    for node in r1, r2:
        print( node, 'inputs', node.port_to_node_in )
        print( node, 'outputs', node.port_to_node_in )
        print( node, 'flow table', node.port_to_optical_signal_out )

    print( '*** Verifying correct ROADM flow tables' )
    print(r1, r1.switch_table)
    print(r2, r2.switch_table)
    return net


# Physical model test

def twoRoadmPhyTest():
    "Create a single link and monitor its OSNR and gOSNR"
    net = twoRoadmPhyNetwork( lengths=[50*km, 50*km, 50*km] )
    nodes = net.name_to_node
    tx1, tx2 = nodes[ 'tx1' ], nodes[ 'tx2' ]
    r1, r2 = nodes[ 'r1' ], nodes[ 'r2' ]
    print( '*** Starting test transmission...' )
    for tx in tx1, tx2:
        print(tx, "outports", tx.ports_out)
        tx.configure_terminal(tx.transceivers[0], [1])
        print('*** TURNING ON TERMINAL', tx)
        tx.turn_on()

    print( '*** Initial OSNR and gOSNR:' )
    monitors = [ node.monitor for node in (tx1, tx2) ]
    for mon in monitors:
        print( 'monitor:', mon )
        print( 'OSNR', mon.get_list_osnr(), 'gOSNR', mon.get_list_gosnr() )

    print( '*** Changing gain for amp1e' )
    # AD: this is not enabled to recompute anything,
    # it used to be for the network to execute.
    # Needs to be implemented.
    amp1 = nodes[ 'amp1e' ]
    amp1.mock_amp_gain_adjust( 1.0 )

    print( '*** Updated OSNR and gOSNR:' )
    for mon in monitors:
        print( 'monitor:', mon )
        print(' OSNR', mon.get_list_osnr(), 'gOSNR', mon.get_list_gosnr() )


if __name__ == '__main__':
    twoRoadmPhyTest()
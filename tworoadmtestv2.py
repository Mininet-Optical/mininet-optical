#!/usr/bin/env python3

from network import Network
from link import Span as Fiber, SpanTuple as Segment
from node import LineTerminal

from functools import partial


km = dB = dBm = 1.0; m = 1e-3


def Span( net, length, amp=None ):
    "Return fiber span of given length (km) with optional amp"
    return Segment( span=Fiber( length=length*km ), amplifier=amp )


def twoRoadmPhyNetwork( lengths=(25*km, 50*km, 25*km) ):
    "Return network consisting of two ROADMS and Terminals"
    net = Network()

    # Nodes
    transceivers = [ ( 't1', 0*dBm, 'C' ), ]
    tx1, tx2 = [
        net.add_lt( name, transceivers=transceivers, monitor_mode=mode )
        for name,mode in [('tx1','out'),('tx2','in')] ]

    r1, r2 = [ net.add_roadm(n) for n in ('r1','r2') ]

    # Spans, amplifiers, and links
    boost1 = net.add_amplifier(
        'boost1', target_gain=3*dB, boost=True, monitor_mode='out' )
    boost2 = net.add_amplifier(
        'boost2', target_gain=3*dB, boost=True, monitor_mode='out' )
    amp1 = net.add_amplifier(
        'amp1', target_gain=.22*dB*25, monitor_mode='out' )
    amp2 = net.add_amplifier(
        'amp2', target_gain=.22*dB*50, monitor_mode='out' )
    span = partial( Span, net )
    spans1 = [ span( 25*km, amp1 ) ]
    spans2 = [ span( 25*km, amp2 ) ]

    # ROADM port numbers (input and output)
    LINE_0 = 0
    ADD_DROP_1 = 1

    # Line terminal port numbers (input and output)
    TX_0 = 0

    net.add_link( tx1, r1, src_out_port=TX_0, dst_in_port=ADD_DROP_1, spans=[ span(1*m) ] )
    net.add_link(r1, r2, src_out_port=LINE_0, dst_in_port=LINE_0, boost_amp=boost1, spans=spans1)
    net.add_link( r2, tx2, src_out_port=ADD_DROP_1, dst_in_port=TX_0, spans=[ span(1*m) ] )

    net.add_link(r1, tx1, src_out_port=ADD_DROP_1, dst_in_port=TX_0, spans=[span(1 * m)])
    net.add_link(r2, r1, src_out_port=LINE_0, dst_in_port=LINE_0, boost_amp=boost2, spans=spans2)
    net.add_link( tx2, r2, src_out_port=TX_0, dst_in_port=ADD_DROP_1, spans=[ span(1*m) ] )

    # Switching rules - add/drop to/from line port 0
    r1.install_switch_rule(
        1, in_port=1, out_port=0, signal_indices=[1] )
    r1.install_switch_rule(
        2, in_port=0, out_port=1, signal_indices=[1] )
    r2.install_switch_rule(
        1, in_port=0, out_port=1, signal_indices=[1] )
    r2.install_switch_rule(
        2, in_port=1, out_port=0, signal_indices=[1] )

    return net


def gosnr( state ):
    "return gOSNR computed from signal state"
    power = state[ 'power' ]
    ase_noise = state[ 'ase_noise' ]
    nli_noise = state[ 'nli_noise' ]
    return LineTerminal.gosnr( power, ase_noise, nli_noise )


def dumpSignal( signal ):
    "Trace signal data"
    print( '***', signal, 'inputs' )
    instates = signal.loc_in_to_state
    outstates = signal.loc_out_to_state
    for loc in outstates:
        instate = instates.get( loc, None )
        outstate = outstates.get( loc, None )
        if instate:
            print(' %30s in:  gOSNR %.2f dB'
                  % ( str(loc), gosnr( instate ) ) )
        if outstate:
            print(' %30s out: gOSNR %.2f dB'
                  % ( str(loc), gosnr( outstate ) ) )


def dumpNodes( net ):
    for name, node in net.name_to_node.items():
        print( name,
               'in', node.port_to_node_in,
               'out', node.port_to_node_out )


def twoRoadmPhyTest():
    "Create a two-ROADM network and display OSNR and gOSNR"
    net = twoRoadmPhyNetwork()
    dumpNodes( net )
    nodes = net.name_to_node
    tx1, tx2 = nodes[ 'tx1' ] , nodes[ 'tx2' ]
    r1, r2 = nodes['r1'], nodes['r2']
    for tx in tx1, tx2:
        tx.configure_terminal(tx.transceivers[0], [1])
        tx.turn_on()
    for node in r1, r2:
        print( "****", node, "signals" )
        print( "in", node.port_to_optical_signal_in )
        print( "out", node.port_to_optical_signal_out )
    link = net.links[ 0 ]
    # Get OSNR and gOSNR from monitors
    monitors = [ amp.monitor for amp in net.amplifiers
                 if hasattr( amp, 'monitor' ) ]
    for mon in monitors:
        print(mon,
              'gOSNR1', mon.get_list_osnr(),
              'gOSNR', mon.get_dict_gosnr())
    dumpSignal( list(tx1.port_to_optical_signal_out.values())[0][0] )

if __name__ == '__main__':

    twoRoadmPhyTest()

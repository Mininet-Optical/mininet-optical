#!/usr/bin/python

"""
single_link_test.py: test monitoring on a single link
"""

from network import Network
from link import Span as FiberSpan, SpanTuple

# Units

km = dB = dBm = 1.0
m = .001


# Physical model API helpers

def Span( km, amp=None ):
    "Return a usable span of length km with amplifer amp"
    return SpanTuple( span=FiberSpan( length=km ), amplifier=amp )


# Physical Network simulation, created out of base PHY model objects

def singleLinkPhyNetwork( lengths=[50*km] ):
    "Link two hosts via a series of fiber spans and amplifiers"
    net = Network()

    # Endpoints
    transceivers = [ ( 't1', 0*dBm, 'C' ) ]
    terminals = tx1, tx2 = [ net.add_lt( 'tx%d' % i, transceivers=transceivers )
                             for i in ( 1, 2  ) ]
    roadms = r1, r2 = [ net.add_roadm( 'r%d' % i ) for i in ( 1, 2 ) ]

    # Single link consisting of multiple fiber spans and amplifiers
    boost = net.add_amplifier( 'boost1', target_gain=3*dB, boost=True )
    amplifiers, spans = [], []
    for i, length in enumerate( lengths, start=1 ):
        amp = net.add_amplifier( 'amp%d' % i, target_gain=11*dB )
        span = Span( length, amp=amp )
        amplifiers.append ( amp )
        spans.append( span )

    net.add_link( tx1, r1, ports=dict(node1_output_port=100, node2_input_port=0),
                  spans=[Span(1*m)])
    link = net.add_link( r1, r2, ports=dict(node1_output_port=101, node2_input_port=1), spans=spans )
    monitors = [
        net.add_monitor( 'mon%d' % i, link=link, span=span, amplifier=amplifiers[i-1] )
        for i, spantuple in enumerate( spans, start=1 )
        for span, amplifier in [spantuple] ]
    net.add_link( r2, tx2, ports=dict(node1_output_port=100, node2_input_port=0),
                  spans=[Span(1*m)])

    # Configure ROADM
    r1.install_switch_rule( 1, in_port=0, out_port=101, signal_indices=[1] )
    r2.install_switch_rule( 1, in_port=1, out_port=100, signal_indices=[1] )

    # Print network elements

    print("*** Terminals:", terminals)
    print("*** Spans:", spans)
    print("*** Amplifiers:", amplifiers)
    print("*** Monitors", monitors)
    print("*** Ports:", tx1.ports_out, tx2.ports_in)

    return net

# Support functions

def formatSignals( signalPowers ):
    "Nice format for signal powers"
    return '\n'.join(
        '%s %.2f dBm' % ( channel, signalPowers[ channel ] )
        for channel in sorted( signalPowers ) )


def dumpLinkPower(link):
    "Print out power for all spans in a Link"
    for span, amp in link.spans:
        print( 'span:', span )
        if amp:
            print('amp:', amp, 'input', formatSignals(amp.input_power),
                  'output', formatSignals(amp.output_power) )


# Physical model test


def singleLinkPhyTest():
    "Create a single link and monitor its OSNR and gOSNR"
    net = singleLinkPhyNetwork( lengths=[25*km, 50*km, 25*km] )
    node = net.name_to_node
    print( '*** Nodes', node )
    print( '*** Links', net.links )
    r1, r2 = node[ 'r1' ], node[ 'r2' ]
    print( '*** r1 switch table', r1.switch_table )
    print( '*** r2 switch table', r2.switch_table )
    print( '*** Starting test transmission...' )
    tx1, tx2 = node[ 'tx1' ], node[ 'tx2' ]
    transceiver = tx1.name_to_transceivers[ 't1' ]
    outport = tx1.ports_out[0]
    tx1.transmit( transceiver, outport, channels=[ 1 ] )
    print( '*** Signals:' )
    tx1.print_signals()
    r1.print_signals()
    r2.print_signals()
    r2.print_signals()
    print( '*** Link power:' )
    link = net.links[1]
    dumpLinkPower(link)

    print( '*** Initial OSNR and gOSNR:' )
    monitors = [ node[ 'mon%d' % i] for i in range(1, 4) ]
    for mon in monitors:
        print( 'monitor:', mon )
        print('OSNR', mon.get_list_osnr(), 'gOSNR', mon.get_list_gosnr())


    print( '*** Changing gain for amp3' )
    net.mock_amp_gain_adjust( 'amp3', 1.0, 'r1', 'r2' )


    print( '*** Updated Link power:' )
    dumpLinkPower(link)

    print( '*** Updated OSNR and gOSNR:' )
    for mon in monitors:
        print( 'monitor:', mon )
        print('OSNR', mon.get_list_osnr(), 'gOSNR', mon.get_list_gosnr())

if __name__ == '__main__':

    singleLinkPhyTest()

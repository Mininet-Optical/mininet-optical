#!/usr/bin/python

"""
single_link_test.py: test monitoring on a single link
"""


from network import Network
from link import Span as FiberSpan, SpanTuple

# Units

km = db = dbM = 1.0
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
    transceivers = [ ( 't1', 0*dbM, 'C' ) ]
    terminals = tx1, tx2 = [ net.add_lt( 'tx%d' % i, transceivers=transceivers )
                  for i in ( 1, 2  ) ]


    # Link consisting of multiple fiber spans and amplifiers
    boost = net.add_amplifier( 'boost1', target_gain=6*db, boost=True )
    net.add_monitor( 'mon0', amplifier=boost )
    amplifiers = [ net.add_amplifier( 'amp%d' % i, target_gain=11*db,  )
                   for i, _ in enumerate( lengths, start=1 ) ]
    monitors = [ net.add_monitor( 'mon%d' % i, amplifier=amp )
                   for i, amp in enumerate( amplifiers, start=1 ) ]
    spans = [ Span( length, amp=amplifiers[ i ] )
              for i, length in enumerate( lengths ) ]

    # debugging

    src, dst = terminals
    net.add_link( src, dst, spans=spans )

    print("TERMINALS", terminals)
    print("AMPLIFIERS", amplifiers)
    print("MONITORS", monitors)
    print("SPANS", spans)
    print("PORTS", tx1.ports_out, tx2.ports_in)

    return net


# Physical model test

def formatSignals( signalPowers ):
    return '\n'.join(
        '%s %.2f dbM' % ( channel, signalPowers[ channel ] )
        for channel in sorted( signalPowers ) )


def dumpLinkPower(link):
    "Print out power for all spans in a Link"
    for span, amp in link.spans:
        print(span, end='')
        if amp:
            print(amp, 'input', formatSignals(amp.input_power),
                  'output', formatSignals(amp.output_power) )


def singleLinkPhyTest():
    lengths = [25*km, 50*km, 25*km]
    net = singleLinkPhyNetwork( lengths=lengths)
    node = net.name_to_node
    tx1, tx2 = node[ 'tx1' ], node[ 'tx2' ]
    channels = [ 1 ]
    transceiver = tx1.name_to_transceivers[ 't1' ]
    link = net.links[0]
    outport = tx1.ports_out[0]
    monitors = [net.name_to_node['mon%d' %i] for i in (1,2,3)]
    tx1.transmit( transceiver, outport, channels )
    tx1.print_signals()
    tx2.print_signals()
    for mon in monitors:
        print('OSNR', mon.get_list_osnr())
        print('gOSNR', mon.get_list_gosnr())
    dumpLinkPower(link)


if __name__ == '__main__':

    singleLinkPhyTest()

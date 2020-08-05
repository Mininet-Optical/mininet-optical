#!/usr/bin/python3

"""

simpletopo.py: Simple Topology Example for Mininet-Optical

This is intended to be a simple but hopefully useful and
comprehensible demonstration of the topology API for
Mininet-Optical.

This example uses full emulation API including the dataplane
and external SDN control plane; note that it is also possible
to use the PHY simulation API on its own, if you don't need
or care about the dataplane or sending packets or using
external SDN control (vs. the internal control API.)

The simple topology consists of two hosts, each connected
to an optical terminal (with some number of transceiver
line cars), connected by a bidirectional, point-to-point
optical link consisting of a boost amplifier and two
50km fiber spans with compensating amplifiers.

Each amplifier has a monitor attached to it. Note that
in the reverse direction you encounter the amplifiers in
reverse order.

Note that in this simple design we will be sending
packets on a single ethernet link, which will be connected
to a single transceiver/line card in the Terminal.

Using the REST API, it should be possible to connect the
ethernet port to the transceiver and to set the channel
and power using shell commands like:

curl 'localhost:8080/connect?node=t1&ethPort=1&wdmPort=2&channel=1&power=0'
curl 'localhost:8080/connect?node=t2&ethPort=1&wdmPort=2&channel=1&power=0'

"""

# Base Mininet imports
from mininet.clean import cleanup
from mininet.net import Mininet
from mininet.log import setLogLevel

# Mininet-Optical imports
from dataplane import Terminal, disableIPv6
from rest import RestServer
from ofcdemo.demolib import ( OpticalTopo, OpticalCLI as CLI, tx, edfa )
# Note that OpticalTopo is simply a Topo() that defines
# ethLink(), wdmLink(), addTerminal() and addROADM()


class SimpleLinearTopo( OpticalTopo ):
    """Simple linear topology with two hosts/terminals
       connected by two 50 km spans:

       h1 - t1 - boost - 50km - amp1 - 50km - amp2 - t2 - h2"""

    def build( self, txCount=4 ):
        "Build our optical network topology specification"

        # Two hosts
        h1, h2 = [ self.addHost( name ) for name in ( 'h1', 'h2' ) ]

        # Two terminals with txCount transceivers each
        txparams = [ tx( 't%d' % t ) for t in range( 1, txCount+1 ) ]
        t1, t2 = [ self.addTerminal( name, transceivers=txparams )
                   for name in ( 't1', 't2' ) ]

        # Ethernet links from hosts to terminals
        self.ethLink( h1, t1 )
        self.ethLink( h2, t2 )

        # Boost amplifiers (in both directions) before optical spans
        boost = edfa( 'boost', target_gain=1.0, monitor=True )

        # Spans: two 50 km spans with compensating EDFAs and monitors
        spans = [ 50.0, edfa( 'amp1', target_gain=50*.22, monitor=True ),
                  50.0, edfa( 'amp1', target_gain=50*.22, monitor=True ) ]

        # Inter-terminal WDM link with boost amplifiers and multiple spans
        self.wdmLink( t1, t2, boost=boost, spans=spans )


### Run our simple network

if __name__ == '__main__':

    # Clean up any leftover junk (equivalent to sudo mn -c)
    cleanup()

    # Print informative messages
    setLogLevel( 'info' )

    # Create network, passing in an instance of our simple
    # topology template; do not create an OpenFlow controller
    net = Mininet( topo=SimpleLinearTopo(), controller=None )

    # Disable IPv6 since we aren't using it and don't want
    # its neighbor discovery packets
    disableIPv6( net )

    # Create REST server for SDN control of optical network elements
    restServer = RestServer( net )

    # Start up network and REST server
    net.start()
    restServer.start()

    # Run optical CLI
    CLI( net )

    # Stop network and REST server
    restServer.stop()
    net.stop()

#!/usr/bin/env python

"""

demolib.py: OFC Demo Topology and CLI

Our demo topology is a cross-connected mesh of 6 POPs.

"""

from mininet_optical.dataplane import ( Terminal, ROADM, OpticalLink,
                        SwitchBase as OpticalSwitchBase,
                        dBm, dB, km,
                        cleanOptLinks, disableIPv6, Mininet )

from mininet_optical.ofcdemo.demolib import OpticalCLI

from mininet_optical.rest import RestServer

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.node import RemoteController
from mininet.util import natural

from collections import namedtuple


# Routers start listening at 6654
ListenPortBase = 6653

CLI = OpticalCLI


### Sanity tests

class OpticalTopo( Topo ):
    "Topo with convenience methods for optical links"

    def wdmLink( self, *args, **kwargs ):
        "Convenience function to add an OpticalLink"
        kwargs.update(cls=OpticalLink)
        self.addLink( *args, **kwargs )

    def ethLink( self, *args, **kwargs ):
        "Clarifying alias for addLink"
        self.addLink( *args, **kwargs )

SpanSpec = namedtuple( 'SpanSpec', 'length amp' )
AmpSpec = namedtuple( 'AmpSpec', 'name params ')

def spanSpec( length, amp, **ampParams):
    "Return span specifier [length, (ampName, params)]"
    ampSpec = AmpSpec(amp, ampParams)
    return SpanSpec( length, ampSpec )


class LinearRoadmTopo( OpticalTopo ):
    """A linear network with a single ROADM and three POPs

       h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3
                             ||
                             t2 - s2 - h2
       h1-h3: hosts
       s1-s3: routers (downlink: eth0, uplink: eth1, eth2)
       t1-t3: terminals (downlink: eth1, eth2, uplink: wdm3, wdm4)
       r1-r3: ROADMs (add/drop: wdm1, wdm2, line: wdm3, wdm4)"""

    @staticmethod
    def ip( pop, intfnum=0, template='10.%d.0.%d', subnet='/24' ):
        "Return a local IP address or subnet for the given POP"
        return template % ( pop, intfnum ) + subnet

    def buildPop( self, p, txCount=2 ):
        "Build a POP; returns: ROADM"
        # Network elements
        hostname, hostip, subnet = 'h%d' % p, self.ip(p, 1), self.ip(p, 0)
        host = self.addHost(hostname, ip=hostip,
                            defaultRoute='dev ' + hostname + '-eth0' )
        router = self.addSwitch('s%d' % p, subnet=subnet,
                                listenPort=(ListenPortBase + p))
        transceivers = [
            ('t%d' %t, 0*dBm, 'C') for t in range(1, txCount+1) ]
        terminal = self.addSwitch(
            't%d' % p, cls=Terminal, transceivers=transceivers )
        roadm = self.addSwitch( 'r%d' % p,  cls=ROADM, monitor_mode='out')
        # Local links
        for port in range( 1, txCount+1 ):
            self.ethLink( router, terminal, port1=port, port2=port )
        self.ethLink( router, host, port1=txCount + 1 )
        for port in range( 1, txCount+1 ):
            self.wdmLink( terminal, roadm, port1=txCount+port, port2=port )
        # Return ROADM so we can link it to other POPs as needed
        return roadm

    def spans( self, spanLength=50*km, spanCount=4 ):
        """Return a list of span specifiers (length, (amp, params))
           the compensation amplifiers are named prefix-ampN"""
        entries = [ spanSpec( length=spanLength, amp='amp%d' % i,
                              target_gain=spanLength/km * .22 * dB,
                              monitor_mode='out' )
                    for i in range(1, spanCount+1) ]
        return sum( [ list(entry) for entry in entries ], [] )

    def build( self, n=3, txCount=2 ):
        "Add POPs and connect them in a line"
        roadms = [ self.buildPop( p, txCount ) for p in range( 1, n+1 ) ]

        # Inter-POP links
        for i in range( 0, n - 1 ):
            src, dst = roadms[i], roadms[i+1]
            boost = ( 'boost', dict(target_gain=17.0*dB) )
            spans = self.spans( spanCount=2 )
            self.wdmLink( src, dst, boost=boost, spans=spans )


def configureLinearNet( net, packetOnly=False ):
    """Configure linear network locally
       Channel usage:
       r1<->r2: 1
       r1<->r3: 2
       r2<->r3: 1"""

    info( '*** Configuring linear network \n' )

    # Port numbering
    eth1, eth2, eth3 = 1, 2, 3
    wdm1, wdm2, wdm3, wdm4 = 1, 2, 3, 4

    # Configure routers
    # eth0: local, eth1: dest1, eth2: dest2
    routers = s1, s2, s3 = net.get( 's1', 's2', 's3' )
    for pop, dests in enumerate([(s2,s3), (s1, s3), (s1,s2)], start=1):
        router, dest1, dest2 = routers[ pop - 1], dests[0], dests[1]
        # XXX Only one host for now
        hostmac = net.get( 'h%d' % pop).MAC()
        router.dpctl( 'del-flows' )
        for eth, dest in enumerate( [ dest1, dest2, router ], start=1 ) :
            dstmod = ( 'mod_dl_dst=%s,' % hostmac ) if dest == router else ''
            for protocol in 'ip', 'icmp', 'arp':
                flow = ( protocol + ',ip_dst=' + dest.params['subnet'] +
                         'actions=' +  dstmod +
                         'dec_ttl,output:%d' % eth )
                router.dpctl( 'add-flow', flow )

    # Configure transceivers
    t1, t2, t3 = net.get( 't1', 't2', 't3' )
    t1.connect( tx=0, ethPort=eth1, wdmPort=wdm3, channel=1)
    t1.connect( tx=1, ethPort=eth2, wdmPort=wdm4, channel=2)
    t2.connect( tx=0, ethPort=eth1, wdmPort=wdm3, channel=1)
    t2.connect( tx=1, ethPort=eth2, wdmPort=wdm4, channel=1)
    t3.connect( tx=0, ethPort=eth1, wdmPort=wdm3, channel=2)
    t3.connect( tx=1, ethPort=eth2, wdmPort=wdm4, channel=1)

    # Configure roadms
    r1, r2, r3 = net.get( 'r1', 'r2', 'r3' )
    local1, local2, line1, line2 = wdm1, wdm2, wdm3, wdm4

    # r1: add/drop ch1<->r2, ch2<->r3
    r1.connect( port1=local1, port2=line1, channels=[1] )
    r1.connect( port1=local2, port2=line1, channels=[2] )

    # r2: add/drop ch1<->r1, ch1<->r3
    r2.connect( port1=local1, port2=line1, channels=[1] )
    r2.connect( port1=local2, port2=line2, channels=[1] )
    # r2: pass through ch2 r1<->r3
    r2.connect( port1=line1, port2=line2, channels=[2] )

    r3.connect( port1=local1, port2=line1, channels=[2] )
    r3.connect( port1=local2, port2=line1, channels=[1] )

    #for roadm in r1, r2, r3:
    # roadm.propagate()


def linearRoadmTest():
    "Test Linear ROADM topology"

    topo = LinearRoadmTopo( n=3 )
    net = Mininet( topo=topo )
    net.start()
    configureLinearNet( net )
    CLI( net )
    net.stop()



### OFC Demo Topology


class DemoTopo( LinearRoadmTopo ):
    """OFC Demo Topology

        -------------Linear Topo----------------
        POP1 -- POP2 -- POP3 -- POP4

       All of the links are bidirectional.

      Each POP consists of a host, router, optical terminal, and ROADM:

       h1 - s1 - t1 - r1
       h2 - s2 - t2 - r2
       etc.
    """

    # Link helper function
    def addPopLink( self, src, dst ):
        "Construct a link of four 50km fiber spans"
        boost = ( 'boost', dict(target_gain=17.0*dB) )
        spans = self.spans( spanLength=50*km, spanCount=2 )
        self.wdmLink( src, dst, boost=boost, spans=spans )

    def build( self, n=4, txCount=10 ):
        "Add POPs and connect them in a ring with some cross-connects"

        # Build POPs
        roadms = {p: self.buildPop( p, txCount=txCount ) for p in range( 1, n+1 ) }
        print(roadms)


        # print(ring)
        # Linear links
        for i in range( 1, n ):
            src, dst = roadms[i], roadms[i+1]
            self.addPopLink( src, dst )


if __name__ == '__main__':

    # Test our demo topology
    cleanup()
    setLogLevel( 'info' )
    net = Mininet( topo=DemoTopo( txCount=15 ), autoSetMacs=True,
                   controller=RemoteController )
    disableIPv6( net )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    CLI( net )
    restServer.stop()
    net.stop()

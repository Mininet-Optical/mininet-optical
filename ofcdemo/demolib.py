#!/usr/bin/env python

"""

ofcdemolib.py: OFC Demo Topology and CLI

(Work in progress - currently we just have a test topology )

Our demo topology is a cross-connected mesh of 6 POPs.

"""

from dataplane import ( Terminal, ROADM, OpticalLink,
                        dbM, km,
                        cleanOptLinks )

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.examples.linuxrouter import LinuxRouter
from mininet.clean import cleanup
from mininet.cli import CLI


class OpticalCLI( CLI ):
    "Extend CLI with ring network routing commands"

    prompt = 'mininet-optical> '

    def do_signals( self, _line ):
        "Print signals "
        for node in self.mn.switches:
            if hasattr( node, 'model' ):
                node.model.print_signals()

    def do_propagate( self, _line ):
        for node in self.mn.switches:
            if isinstance( node, Terminal ):
                node.propagate()
        for node in self.mn.switches:
            if isinstance( node, ROADM ):
                node.propagate()


CLI = OpticalCLI


### Sanity tests


class LinearRoadmTopo( Topo ):
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

    def buildPop( self, p ):
        "Build a POP; returns: ROADM"
        # Network elements
        hostip, routerip, subnet = self.ip(p, 2), self.ip(p, 1), self.ip(p, 0)
        gateway = self.ip(p, 1, subnet='')
        host = self.addHost(
            'h%d' % p, ip=hostip, defaultRoute='via ' + gateway )
        router = self.addNode(
            's%d' % p, cls=LinuxRouter, ip=routerip, subnet=subnet )
        transceivers = [ (t, -2*dbM, 'C') for t in ('tx1', 'tx2') ]
        terminal = self.addSwitch(
            't%d' % p, cls=Terminal, transceivers=transceivers )
        roadm = self.addSwitch( 'r%d' % p,  cls=ROADM )
        # Local links
        params1 = dict(ip=routerip, subnet=subnet)
        eth0, eth1, eth2 = 0, 1, 2
        wdm1, wdm2, wdm3, wdm4 = 1, 2, 3, 4
        self.addLink( host, router, port1=eth0, port2=eth0, params=params1 )
        self.addLink( router, terminal, port1=eth1, port2=eth1 )
        self.addLink( router, terminal, port1=eth2, port2=eth2 )
        self.addLink( terminal, roadm, port1=wdm3, port2=wdm1, cls=OpticalLink )
        self.addLink( terminal, roadm, port1=wdm4, port2=wdm2, cls=OpticalLink )
        # Return ROADM so we can link it to other POPs as needed
        return roadm

    def build( self, n=3 ):
        "Add POPs and connect them in a line"
        roadms = [ self.buildPop( p ) for p in range( 1, n+1 ) ]
        # Inter-POP links
        for i in range( 0, n - 1 ):
            self.addLink( roadms[i], roadms[i+1], cls=OpticalLink,
                          spans=[50*km + i*25*km])


def configureLinearNet( net, packetOnly=False ):
    """Configure linear network
       Channel usage:
       r1<->r2: 1
       r1<->r3: 2
       r2<->r3: 1"""

    info( '*** Configuring linear network \n' )

    # Port numbering
    eth0, eth1, eth2 = 0, 1, 2
    wdm1, wdm2, wdm3, wdm4 = 1, 2, 3, 4

    # Configure routers - IP routing is painful
    routers = s1, s2, s3 = net.get( 's1', 's2', 's3' )
    for pop, dests in enumerate([(s2,s3), (s1, s3), (s1,s2)], start=1):
        # Start from scratch for clarity
        router = routers[ pop - 1]
        router.cmd( 'ip route flush table main' )
        # Local subnet: eth0
        ip, subnet = router.IP(), router.params[ 'subnet' ]
        router.cmd( 'ip route add', subnet, 'dev', router.intfs[eth0] )
        # Remote subnets: eth1, eth2
        dest1, dest2 = dests
        subnet1, subnet2 = dest1.params[ 'subnet' ], dest2.params[ 'subnet' ]
        router.cmd('ip route add', dest1.IP(), 'dev', router.intfs[eth1] )
        router.cmd('ip route add', subnet1, 'via', dest1.IP() )
        router.cmd('ip route add', dest2.IP(), 'dev', router.intfs[eth2] )
        router.cmd('ip route add', subnet2, 'via', dest2.IP() )

    # Don't configure optical elements; they will be configured remotely
    assert packetOnly
    if packetOnly:
        return

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

    for roadm in r1, r2, r3:
        roadm.propagate()


def linearRoadmTest():
    "Test Linear ROADM topology"

    topo = LinearRoadmTopo( n=3 )
    net = Mininet( topo=topo )
    net.start()
    configureLinearNet( net )
    CLI( net )
    net.stop()


### TODO: OFC Demo Topology

class DemoTopo( Topo ):
    "Demo Topology"
    pass

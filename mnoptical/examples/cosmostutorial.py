#!/usr/bin/env python3

"""
cosmostutorial.py: hardware-like topology for COSM-IC mini-tutorial.

This is for the tutorial at:
https://wiki.cosmos-lab.org/wiki/Tutorials/Optical/MininetOpticalTutorial1
"""

from mnoptical.dataplane import (
    OpticalLink, UnidirectionalOpticalLink as ULink,
    ROADM, Terminal, OpticalNet as Mininet, km, m, dB, dBm )
from mnoptical.node import Amplifier

from mnoptical.ofcdemo.demolib import OpticalCLI as CLI, cleanup
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.netconfserver import NetconfServer
from mnoptical.ofcdemo.lroadm import LROADM, NetconfPortBase
from mnoptical.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.log import setLogLevel, info

from subprocess import run
from sys import argv
from time import sleep

### Netconf fake credentials for Mininet-Optical
username = 'cosmos'
password = 'cosmos'
sslkeyfile = 'testcerts/fakeserver.key'

# Lumentum Roadm20 Port numbering
LINEIN, LINEOUT = 5101, 4201
ADD, DROP = 4100, 5200

# Channel
ch = 34   # 193 THz
ch2 = 60  # only used in test()

### Tutorial Topology

class TutorialTopo( Topo ):

    """
    COSM-IC mini-tutorial topology:

    roadm4 <-> roadm1 <-> roadm2 <-22km-> roadm3
     |          |                          |
    tor1       tor2                       tor3
     |          |                          |
    server1    server2                    server3

    This is for the COSMOS mini-tutorial at:
    https://wiki.cosmos-lab.org/wiki/Tutorials/Optical/MininetOpticalTutorial1
    """

    # Helper function for making WDM links

    def wdmLink( self, src, dst, port1, port2, **params ):
        "Add a (default unidirectional) WDM link"
        params.setdefault( 'cls', ULink )
        params.setdefault( 'spans', [1.0*m] )
        self.addLink( src, dst, port1, port2, **params )

    # Build the topology template

    def build( self ):
        "Build COSMOS tutorial topology"

        # ROADMs
        NC = NetconfPortBase
        roadm4 = self.addSwitch('roadm4', cls=LROADM, netconfPort=NC+4)
        roadm1 = self.addSwitch('roadm1', cls=LROADM, netconfPort=NC+1)
        # ROADM2 and ROADM3 compensate for signal loss on long link
        roadm2 = self.addSwitch('roadm2', cls=LROADM, netconfPort=NC+2,
                                preamp=Amplifier('roadm2-preamp', target_gain=3*dB))
        roadm3 = self.addSwitch('roadm3', cls=LROADM, netconfPort=NC+3,
                                boost=Amplifier('roadm3-boost', target_gain=3*dB))

        # ToR switches
        tparams = dict(cls=Terminal, monitor_mode='in')
        tor1 = self.addSwitch('tor1', transceivers=[('32', 0*dBm)], **tparams)
        tor2 = self.addSwitch('tor2', transceivers=[('29', 0*dBm)], **tparams)
        tor3 = self.addSwitch('tor3', transceivers=[('31', 0*dBm)], **tparams)

        # Servers
        server1 = self.addHost('server1')
        server2 = self.addHost('server2')
        server3 = self.addHost('server3')

        # Inter-ROADM links
        # We put 22km of fiber between roadm2 and roadm3
        # Default fiber length is 1m if not specified
        self.wdmLink(roadm4, roadm1, LINEOUT, LINEIN)
        self.wdmLink(roadm1, roadm4, LINEOUT, LINEIN)
        self.wdmLink(roadm1, roadm2, DROP+1, ADD+1)  # passthrough
        self.wdmLink(roadm2, roadm1, DROP+1, ADD+1)  # passthrough
        # Sub-millisecond delays won't be accurate (due to scheduler timing
        # granularity and running in a VM) but this will add observable
        # propagation delay for the longer links.
        self.wdmLink(roadm2, roadm3, LINEOUT, LINEIN, spans=[22*km], delay='73us')
        self.wdmLink(roadm3, roadm2, LINEOUT, LINEIN, spans=[22*km], delay='73us')

        # ROADM add/drop 2 <-> ToR transceiver links
        self.wdmLink(tor1, roadm4, 320, ADD+2)
        self.wdmLink(roadm4, tor1, DROP+2, 321)
        self.wdmLink(tor2, roadm1, 290, ADD+2)
        self.wdmLink(roadm1, tor2, DROP+2, 291)
        self.wdmLink(tor3, roadm3, 310, ADD+2)
        self.wdmLink(roadm3, tor3, DROP+2, 311)

        # Server<->ToR Ethernet links
        self.addLink(server1, tor1, port1=0, port2=1)
        self.addLink(server2, tor2, port1=0, port2=2)
        self.addLink(server3, tor3, port1=0, port2=3)


### Configuration test using internal Python API

def config0(net):
    "Simple sanity-check configuration using internal API"

    # ROADM configuration
    roadm1, roadm2, roadm3, roadm4 = [
        net.get(f'roadm{i}') for i in range(1,5)]

    def connect1():
        "ROADM configuration 1: tor1<->tor2 connection"
        info('*** Installing ROADM configuration 1 for tor1<->tor2')
        roadm4.connect(ADD+2, LINEOUT, [ch])
        roadm4.connect(LINEIN, DROP+2, [ch])
        roadm1.connect(ADD+2, LINEOUT, [ch])
        roadm1.connect(LINEIN, DROP+2, [ch])

    def connect2():
        "ROADM configuration 2: tor1<->tor3 connection"
        info('*** Installing ROADM configuration 1 for tor1<->tor3')
        # roadm4: same as connection 1
        roadm4.connect(ADD+2, LINEOUT, [ch])
        roadm4.connect(LINEIN, DROP+2, [ch])
        # roadm1: through connection (for snake)
        roadm1.connect(ADD+1, LINEOUT, [ch, ch2])
        roadm1.connect(LINEIN, DROP+1, [ch, ch2])
        # roadm2: through connection (for snake)
        roadm2.connect(ADD+1, LINEOUT, [ch, ch2])
        roadm2.connect(LINEIN, DROP+1, [ch, ch2])
        # roadm3: same as roadm1/4 in connection 1
        roadm3.connect(ADD+2, LINEOUT, [ch])
        roadm3.connect(LINEIN, DROP+2, [ch])

    # ToR switch and transceiver configuration (bidirectional)
    tor1, tor2, tor3 = [net.get(f'tor{i}') for i in (1, 2, 3)]
    tor1.connect(ethPort=1, wdmPort=320, wdmInPort=321, channel=ch)
    tor2.connect(ethPort=2, wdmPort=290, wdmInPort=291, channel=ch)
    tor3.connect(ethPort=3, wdmPort=310, wdmInPort=311, channel=ch)
    tor1.turn_on()
    tor2.turn_on()
    tor3.turn_on()

    # Configure server interfaces
    server1, server2, server3 = [
        net.get(f'server{i}') for i in (1, 2, 3)]
    server1.cmd('ifconfig server1-eth0 192.168.1.1/24')
    server2.cmd('ifconfig server2-eth0 192.168.1.2/24')
    server3.cmd('ifconfig server3-eth0 192.168.1.3/24')

    return connect1, connect2


def arp(net):
    "Update host IP address info and send gratuitous ARPs"
    for h in net.hosts:
        h.defaultIntf().updateIP()
        h.sendCmd('arping -c 1 -U -I', h.defaultIntf(), h.IP())
    for h in net.hosts:
        h.waitOutput()


def test(net):
    "Test network configurations"
    connect1, connect2 = config0(net)
    arp(net); net.pingAll(timeout=1)
    connect1()
    arp(net); net.pingAll(timeout=1)
    net['server1'].cmdPrint('ping -c3 192.168.1.2')
    connect2()
    arp(net); net.pingAll(timeout=1)
    net['server1'].cmdPrint('ping -c3 192.168.1.3')


if __name__ == '__main__':
    cleanup()  # Just in case!
    setLogLevel('info')
    if 'clean' in argv: exit( 0 )
    topo = TutorialTopo()
    net = Mininet( topo=topo, controller=None )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    netconfServer = NetconfServer(
        net, username=username, password=password, sslkeyfile=sslkeyfile )
    netconfServer.start()
    plotNet(net, outfile='tutorial.png', directed=True,
            layout='circo', colorMap={LROADM: 'red'})
    if 'test' in argv:
        test(net)
    else:
        info(TutorialTopo.__doc__+'\n')
        CLI(net)
    netconfServer.stop()
    restServer.stop()
    net.stop()
    info( 'Done.\n')

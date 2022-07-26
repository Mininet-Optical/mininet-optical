#!/usr/bin/env python3

"""
sigcommtutorial.py: hardware-like topology for SIGCOMM22

This is for the tutorial at:
[tbd]
"""

from mnoptical.dataplane import (
    UniLink, Terminal, OpticalNet as Mininet, CombSource,
    km, m, dB, dBm )

from mnoptical.node import Amplifier, Node, Transceiver

from mnoptical.ofcdemo.demolib import OpticalCLI as CLI, cleanup
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.netconfserver import NetconfServer
from mnoptical.ofcdemo.lroadm import LROADM, NetconfPortBase
from mnoptical.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.log import setLogLevel, info

from sys import argv
from subprocess import run

NetconfPortBase = 1830

### Netconf fake credentials for Mininet-Optical
username = 'cosmos'
password = 'cosmos'
sslkeyfile = 'testcerts/fakeserver.key'

# Channel/transceiver count for comb soures
txcount = 95

# Lumentum rdm2lg10 Port numbering
LINEIN, LINEOUT = 5101, 4201
ADD, DROP = 4100, 5200

# Channel
ch = 61 # 194.35 THz

comb_src_range = list(range(10,20)) + list(range(40,50)) + list(range(80,90))
comb1_power = {10: -16.2, 11: -16, 12: -15.9, 13: -15.9, 14: -15.8, 15: -16, 16: -16, 17: -16.1, 18: -15.9, 19: -16.1, 40: -15.6, 41: -16.1, 42: -16.2, 43: -16.4, 44: -16.9, 45: -16.4, 46: -16.1, 47: -16.8, 48: -15.6, 49: -16, 80: -15.9, 81: -15.8, 82: -15.5, 83: -16.1, 84: -16.1, 85: -16.1, 86: -15.8, 87: -15.5, 88: -15.5, 89: -15.6}

comb2_power = {10:-16, 11:-15.8, 12:-15.7, 13:-15.6, 14:-15.6, 15:-15.8, 16:-15.8, 17:-15.8, 18:-15.6, 19:-15.9, 40:-15.3, 41:-15.8, 42:-15.9, 43:-16.1, 44:-16.5, 45:-16, 46:-15.8, 47:-16.5, 48:-15.3, 49:-15.6, 80:-15.3, 81:-15.3, 82:-15, 83:-15.5, 84:-15.6, 85:-15.6, 86:-15.2, 87:-15, 88:-14.9, 89:-15}

# No debugging messages by default
Node.debugger = False

### Tutorial Topology

class TutorialTopo( Topo ):

    """
    SIGCOMM22 mini-tutorial topology:

    comb1 -> rdm1co1 <--10km--> rdm1lg1 || rdm2lg1 <--32km--> rdm2co1 <- comb2
               |                  |                              |
            swda_co1           swda_lg1--------------------------|
               |                  |                              |
            srv1_co1           srv1_lg1                       srv2_lg1

    This is for the SIGCOMM22 mini-tutorial at:
    https://wiki.cosmos-lab.org/wiki/Workshops/SigComm2022/MininetOptical
    """

    # Helper function for making WDM links

    def wdmLink( self, src, dst, port1, port2, **params ):
        "Add a (default unidirectional) WDM link"
        params.setdefault( 'cls', UniLink )
        params.setdefault( 'spans', [1.0*m] )
        self.addLink( src, dst, port1, port2, **params )

    # Build the topology template

    def build( self ):
        "Build COSMOS tutorial topology"

        # ROADMs
        NC = NetconfPortBase
        ropts = dict(cls=LROADM, monitor_mode='in')
        # We set different WDG functions for the boost amps
        rdm1co1 = self.addSwitch('rdm1co1', netconfPort=NC+4, insertion_loss_dB=10, **ropts)
        rdm1lg1 = self.addSwitch('rdm1lg1', netconfPort=NC+1, insertion_loss_dB=10, **ropts)
        # rdm2lg1 and rdm2co1 compensate for signal loss on long link
        rdm2lg1 = self.addSwitch('rdm2lg1', netconfPort=NC+2, insertion_loss_dB=10, **ropts)
        rdm2co1 = self.addSwitch('rdm2co1', netconfPort=NC+3, insertion_loss_dB=10, **ropts)

        # ToR switches
        topts = dict(cls=Terminal, monitor_mode='in')
        swda_co1 = self.addSwitch('swda-co1', transceivers=[('32', -1.5*dB)], **topts)
        swda_lg1 = self.addSwitch('swda-lg1', transceivers=[('29', -1.5*dB), ('31', -1.5*dB)], **topts)

        # Comb Sources

        comb1 = self.addSwitch('comb1', cls=CombSource, power=comb1_power, monitor_mode='out')
        comb2 = self.addSwitch('comb2', cls=CombSource, power=comb2_power, monitor_mode='out')

        # Servers
        server1 = self.addHost('srv1_co1')
        server2 = self.addHost('srv1_lg1')
        server3 = self.addHost('srv2_lg1')

        # Inter-ROADM links
        # We put 22km of fiber between rdm2lg1 and rdm2co1
        # Default fiber length is 1m if not specified
        self.wdmLink(rdm1co1, rdm1lg1, LINEOUT, LINEIN,
            spans=[0.0*m,
                ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                10.0*km,
                ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
            delay='33us')

        self.wdmLink(rdm1lg1, rdm1co1, LINEOUT, LINEIN,
            spans=[0.0*m,
                ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'linear', 'monitor_mode': 'out'}),
                10.0*km,
                ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'linear', 'monitor_mode': 'out'})],
            delay='33us')

        self.wdmLink(rdm1lg1, rdm2lg1, DROP+11, ADD+11)  # passthrough
        self.wdmLink(rdm2lg1, rdm1lg1, DROP+11, ADD+11)  # passthrough
        # Sub-millisecond delays won't be accurate (due to scheduler timing
        # granularity and running in a VM) but this will add observable
        # propagation delay for the longer links.

        self.wdmLink(rdm2lg1, rdm2co1, LINEOUT, LINEIN,
            spans=[0.0*m,
                ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                32.0*km,
                ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
            delay='106us')
        self.wdmLink(rdm2co1, rdm2lg1, LINEOUT, LINEIN,
            spans=[0.0*m,
                ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg2', 'monitor_mode': 'out'}),
                32.0*km,
                ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg2', 'monitor_mode': 'out'})],
            delay='106us')

        # ROADM add/drop 2 <-> ToR transceiver links
        self.wdmLink(swda_co1, rdm1co1, 320, ADD+2)
        self.wdmLink(rdm1co1, swda_co1, DROP+2, 321)
        self.wdmLink(swda_lg1, rdm1lg1, 290, ADD+2)
        self.wdmLink(rdm1lg1, swda_lg1, DROP+2, 291)
        self.wdmLink(swda_lg1, rdm2co1, 310, ADD+2)
        self.wdmLink(rdm2co1, swda_lg1, DROP+2, 311)

        # Comb Source links to rdm1co1 and rdm2co1
        self.wdmLink(comb1, rdm1co1, CombSource.LINEOUT, ADD+1)
        self.wdmLink(comb2, rdm2co1, CombSource.LINEOUT, ADD+1)

        # Server<->ToR Ethernet links
        self.addLink(server1, swda_co1, port1=0, port2=1)
        self.addLink(server2, swda_lg1, port1=0, port2=2)
        self.addLink(server3, swda_lg1, port1=0, port2=3)


if __name__ == '__main__':
    cleanup()  # Just in case!
    setLogLevel('info')
    if 'clean' in argv: exit( 0 )
    if 'test' not in argv: argv.append('cli')
    topo = TutorialTopo()
    net = Mininet(topo=topo, controller=None)
    restServer = RestServer(net)
    net.start()
    restServer.start()
    netconfServer = NetconfServer(
        net, username=username, password=password, sslkeyfile=sslkeyfile)
    netconfServer.start()
    plotNet(net, outfile='tutorial.png', directed=True,
            layout='dot', colorMap={LROADM: 'red'},
            linksPerPair=1)
    if 'test' in argv:
        pass
    if 'cli' in argv:
        info(TutorialTopo.__doc__+'\n')
        CLI(net)
    netconfServer.stop()
    restServer.stop()
    net.stop()
    info( 'Done.\n')

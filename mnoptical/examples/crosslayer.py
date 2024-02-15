#!/usr/bin/env python3

"""
crosslayer.py: hardware-like topology for OFC PDP 2024

This is for the tutorial at:
[tbd]
"""

from mnoptical.dataplane import (
    UniLink, Terminal, ROADM, OpticalNet as Mininet, CombSource,
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

        # IRELAND - OpenIreland Testbed
        # ROADM 1. Lumentum 2 is connected to Transponder
        r1l1ie = self.addSwitch('r1l1ie', netconfPort=NC+1, insertion_loss_dB=10, **ropts)
        r1l2ie = self.addSwitch('r1l2ie', netconfPort=NC+2, insertion_loss_dB=10, **ropts)
        r1l3ie = self.addSwitch('r1l3ie', netconfPort=NC+3, insertion_loss_dB=10, **ropts)

        # ROADM 2
        r2l4ie = self.addSwitch('r2l4ie', netconfPort=NC+4, insertion_loss_dB=10, **ropts)
        r2l5ie = self.addSwitch('r2l5ie', netconfPort=NC+5, insertion_loss_dB=10, **ropts)

        # ROADM 3
        r3l6ie = self.addSwitch('r3l6ie', netconfPort=NC+6, insertion_loss_dB=10, **ropts)
        r3l7ie = self.addSwitch('r3l7ie', netconfPort=NC+7, insertion_loss_dB=10, **ropts)

        # US - COSMOS Testbed
        # ROADM 1. Lumentum 2 is connected to Transponder
        r1l1us = self.addSwitch('r1l1us', netconfPort=NC+11, insertion_loss_dB=10, **ropts)
        r1l2us = self.addSwitch('r1l2us', netconfPort=NC+12, insertion_loss_dB=10, **ropts)
        r1l3us = self.addSwitch('r1l3us', netconfPort=NC+13, insertion_loss_dB=10, **ropts)

        # ROADM 2
        r2l4us = self.addSwitch('r2l4us', netconfPort=NC+14, insertion_loss_dB=10, **ropts)
        r2l5us = self.addSwitch('r2l5us', netconfPort=NC+15, insertion_loss_dB=10, **ropts)

        # ROADM 3
        r3l6us = self.addSwitch('r3l6us', netconfPort=NC+16, insertion_loss_dB=10, **ropts)
        r3l7us = self.addSwitch('r3l7us', netconfPort=NC+17, insertion_loss_dB=10, **ropts)


        # Transponder
        topts = dict(cls=Terminal, monitor_mode='in')
        # IRELAND
        teraie = self.addSwitch('teraie', transceivers=[('tx1', -1.5*dB), ('tx2', -1.5*dB)], **topts)
        # US
        teraus = self.addSwitch('teraus', transceivers=[('tx1', -1.5*dB), ('tx2', -1.5*dB)], **topts)

        # Comb Sources (if needed)
        #comb1 = self.addSwitch('comb1', cls=CombSource, power=comb1_power, monitor_mode='out')
        #comb2 = self.addSwitch('comb2', cls=CombSource, power=comb2_power, monitor_mode='out')

        # Servers
        serverie = self.addHost('serverie')
        serverus = self.addHost('serverus')
        crossatl1 = self.addHost('crossatl1')
        crossatl2 = self.addHost('crossatl2')
        servermmw = self.addHost('servermmw')

        # Polatis switch - ROADM node try
        polatisie = self.addSwitch('polatisie', cls=ROADM, insertion_loss_dB=0.5, monitor_mode='in')
        polatisus = self.addSwitch('polatisus', cls=ROADM, insertion_loss_dB=0.5, monitor_mode='in')
        #polatisie = self.addSwitch('polatisie', transceivers=[('tx1', -1.5*dB), ('tx2', -1.5*dB), ('tx3', -1.5*dB),
        #                                                  ('tx4', -1.5*dB), ('tx5', -1.5*dB), ('tx6', -1.5*dB),
        #                                                  ('tx7', -1.5*dB), ('tx11', -1.5*dB), ('tx12', -1.5*dB),
        #                                                  ('tx13', -1.5*dB), ('tx14', -1.5*dB), ('tx15', -1.5*dB),
        #                                                  ('tx16', -1.5*dB), ('tx17', -1.5*dB)], **topts)
        #polatisus = self.addSwitch('polatisus', transceivers=[('tx1', -1.5*dB), ('tx2', -1.5*dB), ('tx3', -1.5*dB),
        #                                                  ('tx4', -1.5*dB), ('tx5', -1.5*dB), ('tx6', -1.5*dB),
        #                                                  ('tx7', -1.5*dB), ('tx11', -1.5*dB), ('tx12', -1.5*dB),
        #                                                  ('tx13', -1.5*dB), ('tx14', -1.5*dB), ('tx15', -1.5*dB),
        #                                                  ('tx16', -1.5*dB), ('tx17', -1.5*dB)], **topts)
        # Inter-ROADM links
        # 50km between rdm1-rdm2, 25kn between rdm2-rdm3 and rdm1-rdm3.
        # Default fiber length is 1m if not specified

        # IRELAND
        self.wdmLink(r1l1ie, r2l4ie, LINEOUT, LINEIN,
            spans=[0.0*m,
                ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                50.0*km,
                ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
            delay='33us')

        self.wdmLink(r2l5ie, r1l3ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r2l4ie, r3l6ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l6ie, r2l5ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l7ie, r1l1ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r1l3ie, r3l7ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        # US
        self.wdmLink(r1l1us, r2l4us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r2l5us, r1l3us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r2l4us, r3l6us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l6us, r2l5us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l7us, r1l1us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r1l3us, r3l7us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        # Polatis - Roadms links

        # Passthrough rdm links - connected to the Polatis switch
        # IRELAND
        self.wdmLink(r1l1ie, polatisie, DROP+1, 1)
        self.wdmLink(r1l2ie, polatisie, DROP+1, 2)
        self.wdmLink(r1l3ie, polatisie, DROP+1, 3)
        self.wdmLink(polatisie, r1l1ie, 11, ADD+1)
        self.wdmLink(polatisie, r1l2ie, 12, ADD+1)
        self.wdmLink(polatisie, r1l3ie, 13, ADD+1)
        self.wdmLink(r2l4ie, polatisie, DROP+1, 5)
        self.wdmLink(r2l5ie, polatisie, DROP+1, 4)
        self.wdmLink(polatisie, r2l4ie, 14, ADD+1)
        self.wdmLink(polatisie, r2l5ie, 15, ADD+1)
        self.wdmLink(r3l6ie, polatisie, DROP+1, 6)
        self.wdmLink(r3l7ie, polatisie, DROP+1, 7)
        self.wdmLink(polatisie, r3l6ie, 16, ADD+1)
        self.wdmLink(polatisie, r3l7ie, 17, ADD+1)
        #self.wdmLink(r2l4ie, r2l4ie, DROP+1, ADD+1) # Same source and destination doesn't work
        #self.wdmLink(r3l6ie, r3l7ie, DROP+1, ADD+1)
        #self.wdmLink(r1l1ie, r1l2ie, DROP+1, ADD+1)

        # US
        self.wdmLink(r1l1us, polatisus, DROP+1, 1)
        self.wdmLink(r1l2us, polatisus, DROP+1, 2)
        self.wdmLink(r1l3us, polatisus, DROP+1, 3)
        self.wdmLink(polatisus, r1l1us, 11, ADD+1)
        self.wdmLink(polatisus, r1l2us, 12, ADD+1)
        self.wdmLink(polatisus, r1l3us, 13, ADD+1)
        self.wdmLink(r2l4us, polatisus, DROP+1, 5)
        self.wdmLink(r2l5us, polatisus, DROP+1, 4)
        self.wdmLink(polatisus, r2l4us, 14, ADD+1)
        self.wdmLink(polatisus, r2l5us, 15, ADD+1)
        self.wdmLink(r3l6us, polatisus, DROP+1, 6)
        self.wdmLink(r3l7us, polatisus, DROP+1, 7)
        self.wdmLink(polatisus, r3l6us, 16, ADD+1)
        self.wdmLink(polatisus, r3l7us, 17, ADD+1)
        #self.wdmLink(r1l2us, r1l1us, DROP+1, ADD+1)
        #self.wdmLink(r2l4us, r2l4us, DROP+1, ADD+1) # Same source and destination doesn't work
        #self.wdmLink(r3l6us, r3l7us, DROP+1, ADD+1)
        #self.wdmLink(r1l1us, r1l2us, DROP+1, ADD+1)

        # Sub-millisecond delays won't be accurate (due to scheduler timing
        # granularity and running in a VM) but this will add observable
        # propagation delay for the longer links.

        # ROADM add/drop 2 <-> Txp transceiver links
        # IRELAND
        self.wdmLink(teraie, r1l2ie, 1, LINEIN)
        self.wdmLink(r1l2ie, teraie, LINEOUT, 2)
        # US
        self.wdmLink(teraus, r1l2us, 1, LINEIN)
        self.wdmLink(r1l2us, teraus, LINEOUT, 2)

        # Comb Source links to rdm1co1 and rdm2co1
        #self.wdmLink(comb1, rdm1co1, CombSource.LINEOUT, ADD+1)
        #self.wdmLink(comb2, rdm2co1, CombSource.LINEOUT, ADD+1)

        # Server<->ToR Ethernet links
        self.addLink(serverie, teraie, port1=0, port2=3)
        self.addLink(serverie, crossatl1, port1=1, port2=0)
        self.addLink(crossatl1, crossatl2, port1=1, port2=3)
        self.addLink(crossatl2, servermmw, port1=2, port2=1)
        self.addLink(crossatl2, serverus, port1=1, port2=1)
        self.addLink(serverus, teraus, port1=0, port2=3)



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
    plotNet(net, outfile='ofc24_topo.png', directed=True,
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

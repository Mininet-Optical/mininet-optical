#!/usr/bin/env python3

"""
crosslayer.py: hardware-like topology for cross-layer experiment

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
from mnoptical.click import ClickUserSwitch

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.node import OVSSwitch
from mininet.link import TCLink

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
    Cross-layer topology:

     h1 -> s1 -> teraie1    teraie2 -> satl1 -> satl2 -> teraus1    teraus2 -> s2 -> h2
                    \        |                              \         |
                    r1 ---- r2                               r1 ---- r2
                     \     |                                   \     |
                       r3                                         r3


    """

    # Helper function for making WDM links

    def wdmLink( self, src, dst, port1, port2, **params ):
        "Add a (default unidirectional) WDM link"
        params.setdefault( 'cls', UniLink )
        params.setdefault( 'spans', [1.0*m] )
        self.addLink( src, dst, port1, port2, **params )

    # Build the topology template

    def build( self ):
        "Build OFC topology"

        # ROADMs
        NC = NetconfPortBase
        ropts = dict(cls=LROADM, monitor_mode='in')

        # IRELAND - OpenIreland Testbed
        # ROADM 1. Lumentum 2 is connected to Transponder
        r1l1ie = self.addSwitch('r1l1ie', netconfPort=NC+1, insertion_loss_dB=10, **ropts)
        r1l2ie = self.addSwitch('r1l2ie', netconfPort=NC+2, insertion_loss_dB=10, **ropts)

        # ROADM 2
        r2l3ie = self.addSwitch('r2l3ie', netconfPort=NC+3, insertion_loss_dB=10, **ropts)
        r2l4ie = self.addSwitch('r2l4ie', netconfPort=NC+4, insertion_loss_dB=10, **ropts)

        # ROADM 3
        r3l5ie = self.addSwitch('r3l5ie', netconfPort=NC+5, insertion_loss_dB=10, **ropts)
        r3l6ie = self.addSwitch('r3l6ie', netconfPort=NC+6, insertion_loss_dB=10, **ropts)

        # US - COSMOS Testbed
        # ROADM 1. Lumentum 2 is connected to Transponder
        r1l1us = self.addSwitch('r1l1us', netconfPort=NC+11, insertion_loss_dB=10, **ropts)
        r1l2us = self.addSwitch('r1l2us', netconfPort=NC+12, insertion_loss_dB=10, **ropts)

        # ROADM 2
        r2l3us = self.addSwitch('r2l3us', netconfPort=NC+13, insertion_loss_dB=10, **ropts)
        r2l4us = self.addSwitch('r2l4us', netconfPort=NC+14, insertion_loss_dB=10, **ropts)

        # ROADM 3
        r3l5us = self.addSwitch('r3l5us', netconfPort=NC+15, insertion_loss_dB=10, **ropts)
        r3l6us = self.addSwitch('r3l6us', netconfPort=NC+16, insertion_loss_dB=10, **ropts)


        # Transponder
        topts = dict(cls=Terminal, monitor_mode='in')
        # IRELAND
        teraie1 = self.addSwitch('teraie1', transceivers=[('tx1', 0*dBm, 'C'), ('tx2', 0*dBm, 'C')], **topts)
        teraie2 = self.addSwitch('teraie2', transceivers=[('tx1', 0*dBm, 'C'), ('tx2', 0*dBm, 'C')], **topts)
        # US
        teraus1 = self.addSwitch('teraus1', transceivers=[('tx1', 0*dBm, 'C'), ('tx2', 0*dBm, 'C')], **topts)
        teraus2 = self.addSwitch('teraus2', transceivers=[('tx1', 0*dBm, 'C'), ('tx2', 0*dBm, 'C')], **topts)

        # Comb Sources (if needed for background traffic)
        #comb1 = self.addSwitch('comb1', cls=CombSource, power=comb1_power, monitor_mode='out')
        #comb2 = self.addSwitch('comb2', cls=CombSource, power=comb2_power, monitor_mode='out')

        # Servers
        #s1 = self.addSwitch('s1', cls=ClickUserSwitch,
        #                    config_file='/home/julieraulin/Documents/mininet-optical/mnoptical/switch.click',
        #                    link=TCLink, log_file='s1.log', parameters=dict(HOST='s1-eth0', NETWORK='s1-eth1'))
        #s2 = self.addSwitch('s2', cls=ClickUserSwitch,
        #                    config_file='/home/julieraulin/Documents/mininet-optical/mnoptical/switch.click',
        #                    link=TCLink, log_file='s2.log', parameters=dict(HOST='s2-eth0', NETWORK='s2-eth1'))
        s1 = self.addSwitch('s1', cls=OVSSwitch) #cls=OVSSwitch
        s2 = self.addSwitch('s2', cls=OVSSwitch)
        satl1 = self.addSwitch('satl1', cls=OVSSwitch)
        satl2 = self.addSwitch('satl2', cls=OVSSwitch)

        # controller for switches
        #c0 = self.addController( 'c0' )
        # Hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Polatis switch - ROADM node try
        polatisie = self.addSwitch('polatisie', cls=ROADM, insertion_loss_dB=1.5, monitor_mode='in')
        polatisus = self.addSwitch('polatisus', cls=ROADM, insertion_loss_dB=1.5, monitor_mode='in')

        # Inter-ROADM links
        # 25km between rdm1-rdm2, 25km between rdm1-rdm3 and 25km+EDFA+25km+EDFA+25km for rdm2-rdm3.
        # Default fiber length is 1m if not specified

        # IRELAND
        self.wdmLink(r1l1ie, r2l3ie, LINEOUT, LINEIN,
                    spans=[0.0*m,
                        ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                        25.0*km,
                        ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                    delay='33us')

        self.wdmLink(r2l3ie, r1l1ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r1l2ie, r3l5ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l5ie, r1l2ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r2l4ie, r3l6ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('amp2', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('amp3', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l6ie, r2l4ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('amp3', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('amp2', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        # US
        self.wdmLink(r1l1us, r2l3us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r2l3us, r1l1us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r1l2us, r3l5us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l5us, r1l2us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r2l4us, r3l6us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('amp2', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('amp3', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(r3l6us, r2l4us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('amp3', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('amp2', {'target_gain': 25*.22*dB}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')


        # Polatis - Roadms links

        # Passthrough rdm links - connected to the Polatis switch
        # IRELAND
        self.wdmLink(polatisie, r1l1ie,3, ADD+1)
        self.wdmLink(r1l1ie, polatisie, DROP+1, 4)
        self.wdmLink(r1l2ie, polatisie, DROP+1, 5)
        self.wdmLink(polatisie, r1l2ie, 6, ADD+1)
        self.wdmLink(polatisie, r2l3ie, 7, ADD+1)
        self.wdmLink(r2l3ie, polatisie, DROP+1, 8)
        self.wdmLink(r2l4ie, polatisie, DROP+1, 9)
        self.wdmLink(polatisie, r2l4ie, 10, ADD+1)
        self.wdmLink(polatisie, r3l5ie, 11, ADD+1)
        self.wdmLink(r3l5ie, polatisie, DROP+1, 12)
        self.wdmLink(r3l6ie, polatisie, DROP+1, 13)
        self.wdmLink(polatisie, r3l6ie, 14, ADD+1)


        # US
        self.wdmLink(polatisus, r1l1us,3, ADD+1)
        self.wdmLink(r1l1us, polatisus, DROP+1, 4)
        self.wdmLink(r1l2us, polatisus, DROP+1, 5)
        self.wdmLink(polatisus, r1l2us, 6, ADD+1)
        self.wdmLink(polatisus, r2l3us, 7, ADD+1)
        self.wdmLink(r2l3us, polatisus, DROP+1, 8)
        self.wdmLink(r2l4us, polatisus, DROP+1, 9)
        self.wdmLink(polatisus, r2l4us, 10, ADD+1)
        self.wdmLink(polatisus, r3l5us, 11, ADD+1)
        self.wdmLink(r3l5us, polatisus, DROP+1, 12)
        self.wdmLink(r3l6us, polatisus, DROP+1, 13)
        self.wdmLink(polatisus, r3l6us, 14, ADD+1)


        # Sub-millisecond delays won't be accurate (due to scheduler timing
        # granularity and running in a VM) but this will add observable
        # propagation delay for the longer links.

        # ROADM add/drop 2 <-> Txp transceiver links
        # IRELAND
        # Tera1
        self.wdmLink(teraie1, polatisie, 2, 1)
        self.wdmLink(polatisie, teraie1, 2, 3)
        # Tera2
        self.wdmLink(teraie2, polatisie, 2, 15)
        self.wdmLink(polatisie, teraie2, 16, 3)

        # US
        # Tera1
        self.wdmLink(teraus1, polatisus, 2, 1)
        self.wdmLink(polatisus, teraus1, 2, 3)
        # Tera2
        self.wdmLink(teraus2, polatisus, 2, 15)
        self.wdmLink(polatisus, teraus2, 16, 3)

        # Comb Source links to rdm1co1 and rdm2co1
        #self.wdmLink(comb1, rdm1co1, CombSource.LINEOUT, ADD+1)
        #self.wdmLink(comb2, rdm2co1, CombSource.LINEOUT, ADD+1)

        # Ethernet links
        self.addLink(h1, s1, port1=0, port2=2)
        self.addLink(s1, teraie1, port1=1, port2=1)
        self.addLink(teraie2, satl1, port1=1, port2=1)
        self.addLink(satl1, satl2, port1=2, port2=2, bw=10000, delay='5ms', loss=0)
        self.addLink(satl2, teraus1, port1=1, port2=1)
        self.addLink(teraus2, s2, port1=1, port2=1)
        self.addLink(s2, h2, port1=2, port2=0)



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
    plotNet(net, outfile='ofc24_topo-bis-v2.png', directed=True,
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

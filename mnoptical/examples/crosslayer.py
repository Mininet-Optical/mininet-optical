#!/usr/bin/env python3

"""
crosslayer.py: hardware-like topology for OFC PDP 2024

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

        # IRELAND - OpenIreland Testbed
        # ROADM 1. Lumentum 2 is connected to Transponder
        rdm1lum1ie = self.addSwitch('rdm1lum1ie', netconfPort=NC+1, insertion_loss_dB=10, **ropts)
        rdm1lum2ie = self.addSwitch('rdm1lum2ie', netconfPort=NC+2, insertion_loss_dB=10, **ropts)
        rdm1lum3ie = self.addSwitch('rdm1lum3ie', netconfPort=NC+3, insertion_loss_dB=10, **ropts)

        # ROADM 2
        rdm2lum4ie = self.addSwitch('rdm2lum4ie', netconfPort=NC+4, insertion_loss_dB=10, **ropts)
        rdm2lum5ie = self.addSwitch('rdm2lum5ie', netconfPort=NC+5, insertion_loss_dB=10, **ropts)

        # ROADM 3
        rdm3lum6ie = self.addSwitch('rdm3lum6ie', netconfPort=NC+6, insertion_loss_dB=10, **ropts)
        rdm3lum7ie = self.addSwitch('rdm3lum7ie', netconfPort=NC+7, insertion_loss_dB=10, **ropts)

        # US - COSMOS Testbed
        # ROADM 1. Lumentum 2 is connected to Transponder
        rdm1lum1us = self.addSwitch('rdm1lum1us', netconfPort=NC+1, insertion_loss_dB=10, **ropts)
        rdm1lum2us = self.addSwitch('rdm1lum2us', netconfPort=NC+2, insertion_loss_dB=10, **ropts)
        rdm1lum3us = self.addSwitch('rdm1lum3us', netconfPort=NC+3, insertion_loss_dB=10, **ropts)

        # ROADM 2
        rdm2lum4us = self.addSwitch('rdm2lum4us', netconfPort=NC+4, insertion_loss_dB=10, **ropts)
        rdm2lum5us = self.addSwitch('rdm2lum5us', netconfPort=NC+5, insertion_loss_dB=10, **ropts)

        # ROADM 3
        rdm3lum6us = self.addSwitch('rdm3lum6us', netconfPort=NC+6, insertion_loss_dB=10, **ropts)
        rdm3lum7us = self.addSwitch('rdm3lum7us', netconfPort=NC+7, insertion_loss_dB=10, **ropts)


        # Transponder
        topts = dict(cls=Terminal, monitor_mode='in')
        # IRELAND
        teraie = self.addSwitch('tera_ie', transceivers=[('tx1', -1.5*dB), ('tx2', -1.5*dB)], **topts)
        # US
        teraus = self.addSwitch('tera_us', transceivers=[('tx1', -1.5*dB), ('tx2', -1.5*dB)], **topts)

        # Comb Sources (if needed)
        #comb1 = self.addSwitch('comb1', cls=CombSource, power=comb1_power, monitor_mode='out')
        #comb2 = self.addSwitch('comb2', cls=CombSource, power=comb2_power, monitor_mode='out')

        # Servers
        serverie = self.addHost('srv_ie')
        serverus = self.addHost('srv_us')
        crossatl1 = self.addHost('crossatl1')
        crossatl2 = self.addHost('crossatl2')
        servermmw = self.addHost('srv_us_mmw')

        # Inter-ROADM links
        # 50km between rdm1-rdm2, 25kn between rdm2-rdm3 and rdm1-rdm3.
        # Default fiber length is 1m if not specified

        # IRELAND
        self.wdmLink(rdm1lum1ie, rdm2lum4ie, LINEOUT, LINEIN,
            spans=[0.0*m,
                ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                50.0*km,
                ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
            delay='33us')

        self.wdmLink(rdm2lum5ie, rdm1lum3ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm2lum4ie, rdm3lum6ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm3lum6ie, rdm2lum5ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm3lum7ie, rdm1lum1ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm1lum3ie, rdm3lum7ie, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        # US
        self.wdmLink(rdm1lum1us, rdm2lum4us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm2lum5us, rdm1lum3us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            50.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm2lum4us, rdm3lum6us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm3lum6us, rdm2lum5us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            1.0*m,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm3lum7us, rdm1lum1us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')

        self.wdmLink(rdm1lum3us, rdm3lum7us, LINEOUT, LINEIN,
                     spans=[0.0*m,
                            ('boost', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'}),
                            25.0*km,
                            ('preamp', {'target_gain': 18.0*dB, 'wdg_id': 'wdg1', 'monitor_mode': 'out'})],
                     delay='33us')


        # Passthrough rdm links
        # IRELAND
        self.wdmLink(rdm1lum2ie, rdm1lum1ie, DROP+1, ADD+1)
        self.wdmLink(rdm2lum4ie, rdm2lum4ie, DROP+1, ADD+1)
        self.wdmLink(rdm3lum6ie, rdm3lum7ie, DROP+1, ADD+1)
        self.wdmLink(rdm1lum1ie, rdm1lum2ie, DROP+1, ADD+1)

        # US
        self.wdmLink(rdm1lum2us, rdm1lum1us, DROP+1, ADD+1)
        self.wdmLink(rdm2lum4us, rdm2lum4us, DROP+1, ADD+1)
        self.wdmLink(rdm3lum6us, rdm3lum7us, DROP+1, ADD+1)
        self.wdmLink(rdm1lum1us, rdm1lum2us, DROP+1, ADD+1)

        # Sub-millisecond delays won't be accurate (due to scheduler timing
        # granularity and running in a VM) but this will add observable
        # propagation delay for the longer links.

        # ROADM add/drop 2 <-> Txp transceiver links
        # IRELAND
        self.wdmLink(teraie, rdm1lum2ie, 1, LINEIN)
        self.wdmLink(rdm1lum2ie, teraie, LINEOUT, 2)
        # US
        self.wdmLink(teraus, rdm1lum2us, 1, LINEIN)
        self.wdmLink(rdm1lum2us, teraus, LINEOUT, 2)

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

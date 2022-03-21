#!/usr/bin/env python3

"""
lroadmring.py: ring test topology for LROADM
"""

from mnoptical.dataplane import (
    UnidirectionalOpticalLink as ULink,
    ROADM, Terminal,
    OpticalNet as Mininet,
    km, m, dB, dBm)

from mnoptical.ofcdemo.demolib import OpticalCLI as CLI, cleanup
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.lroadm import LROADM, NetconfPortBase
from mnoptical.ofcdemo.netconfserver import NetconfServer
from mnoptical.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.log import setLogLevel, info, debug
from mininet.node import OVSSwitch

from os.path import dirname, realpath, join
from subprocess import run
from sys import argv

### Default netconf username and password for testing
username = 'admin'
password = 'admin'

### Simple LROADM() topologies

class LumentumBase( Topo ):
    """Simple ring topology using Lumentum-link ROADM model
       nodes: hN<->sN<->tN<->rN (host/switch/terminal/roadm)
       Note WDM links are unidirectional and ethernet
       links are bidirectional."""

    # Ethernet and WDM port numbering for Switch + Terminal
    # Note Ethernet uses a single port for tx/rx while
    # WDM uses split tx/rx ports and unidirectional links
    ethbase = 0
    hostport = 200  # Switch only
    txbase = 100
    rxbase = 200

    # Passive OpenFlow TCP port base for packet switches
    listenPortBase = 6653

    # Make pylint happy
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.txcount = 1

    # Helper functions

    def wdmLink( self, src, dst, port1, port2, spans=(1*m,), **params ):
        "Add a (default unidirectional) WDM link"
        params.setdefault( 'cls', ULink )
        params.setdefault( 'spans', [1.0*m] )
        self.addLink( src, dst, port1, port2, **params )

    # Node creation

    @staticmethod
    def nodeNames(i):
        "Return host, switch, terminal, roadm names for node i"
        assert not isinstance(i, bool)
        return f'h{i} s{i} t{i} r{i}'.split()

    def addNetworkNodes(self, i, power=0*dBm):
        """Add a host-switch-terminal-ROADM nodes,
           named hN, sN, tN, rN"""
        # Add network elements
        transceivers = tuple(
            (f'tx{i}', power) for i in range( self.txcount ))
        topts = {'transceivers': transceivers, 'monitor_mode': 'in'}
        host, switch, term, roadm = self.nodeNames(i)
        self.addHost(host)
        self.addSwitch(switch, listenPort=self.listenPortBase+i)
        self.addSwitch(term, cls=Terminal, **topts)
        ncport = NetconfPortBase + i
        self.addSwitch(roadm, cls=LROADM, netconfPort=ncport )

    def addNodeLinks(self, i):
        "Add internal links for network node i"
        host, switch, term, roadm = self.nodeNames(i)
        self.addLink(host, switch, port2=self.hostport)
        for i in range(1, self.txcount+1):
            # src, dst, port1, port2
            self.addLink(switch, term, self.ethbase+i, self.ethbase+i)
            # Terminal:txN -> ROADM:addN
            self.wdmLink(
                term, roadm, self.txbase+i, LROADM.addbase+i)
            # ROADM:dropN -> Terminal:rxN
            self.wdmLink(
                roadm, term, LROADM.dropbase+i, self.rxbase+i)


class LumentumRing( LumentumBase ):
    """Unidrectional ring topology using Lumentum-like ROADM model
       nodes: hN<->sN<->tN<->rN... (host/switch/terminal/roadm)
       Note WDM links are unidirectional and ethernet
       links are bidirectional."""

    def build( self, N=4, txcount=16):
        "Build lumentum ring"
        self.N, self.txcount = N, txcount
        # Add host, switch, terminal, roadm nodes
        for i in range(1, N+1):
            self.addNetworkNodes(i)
            self.addNodeLinks(i)
        # Connect roadm nodes
        for i in range(1, N+1):
            src, dst = f'r{i}', f'r{i%N+1}'
            # Fiber length, compensating edfa
            spans = [25*km, ('amp1', .2*25*dB)]
            # Note: it's very important that line out goes to line in!
            self.wdmLink(src, dst, LROADM.lineout, LROADM.linein, spans)

def test(net):
    "Run config script and simple test"
    info( '** Checking that network is not configured...\n')
    dropped = net.ping(net.hosts, timeout=.5)
    assert dropped == 100
    info( '*** Configuring network...\n' )
    testdir = dirname(realpath(argv[0]))
    script = join(testdir, 'config_lroadmring.py')
    run(script)
    info( '*** Checking connectivity...\n' )
    dropped = net.ping(net.hosts, timeout=.5)
    assert dropped == 0

if __name__ == '__main__':
    print("*** Cleaning up...")
    cleanup()
    if 'clean' in argv: exit(0)
    setLogLevel('info')
    topo = LumentumRing(N=4, txcount=4)
    net = Mininet(topo=topo, controller=None)
    restServer = RestServer(net)
    netconfServer = NetconfServer(net, username=username, password=password)
    plotNet(net, outfile='lumentumring.png', directed=True,
            colorMap={LROADM: 'red', OVSSwitch: 'darkgreen'})
    net.start()
    restServer.start()
    netconfServer.start()
    test(net) if 'test' in argv else CLI(net)
    netconfServer.stop()
    restServer.stop()
    net.stop()
    info('Done.\n')

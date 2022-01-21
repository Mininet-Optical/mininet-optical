#!/usr/bin/env python3

"""
hwtopo.py: hardware-like topology for OFC 2021 demo

Implements LumentumLinear, a topology intended to
mimic the hardware testbed topology for the OFC 2021
demo.
"""

from mnoptical.dataplane import ( OpticalLink,
                        UnidirectionalOpticalLink as ULink,
                        ROADM, Terminal,
                        OpticalNet as Mininet,
                        km, m, dB, dBm )

from sys import argv
from mnoptical.ofcdemo.demolib import OpticalCLI as CLI, cleanup
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.netconfserver import NetconfServer
from mnoptical.ofcdemo.lroadm import LROADM
from mnoptical.ofcdemo.lumentum_NETCONF_API import USERNAME, PASSWORD
from mnoptical.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

from time import sleep

### Customized network elements

netconfPortBase = 1830

class Lumentum( LROADM ):
    "Add default netconf username and password"
    username = USERNAME
    password = PASSWORD

class MUX( ROADM ):
    "A MUX is just the mux part of a roadm"
    pass


### Topology

class LumentumLinear( Topo ):

    """
    Demo-like topology of lumentum-like ROADMs:
        L1 === L2-L3 === L4-L5 ==== L6

    Also multiplexes transceivers into single add/drop
    ports to mirror comb source in COSMOS testbed.
    """

    # Port numbering
    linein, lineout = 5101, 4201
    addbase, dropbase = 4100, 5200
    def addport( self, i ): return self.addbase + i
    def dropport( self, i ): return self.dropbase + i

    # Helper functions
    def wdmLink( self, src, dst, port1, port2, **params ):
        "Add a (default unidirectional) WDM link"
        params.setdefault( 'cls', ULink )
        params.setdefault( 'spans', [1.0*m] )
        self.addLink( src, dst, port1, port2, **params )

    def hostname( self, i, adjust=False ):
        "Optionally return alternate hostname for host i"
        if not adjust:
            return f'h{i}'
        if i == 1: return 'DC1'
        if i == self.nodecount: return 'DC2'
        return f'DU{i-1}'

    def build( self, nodecount=4, power=0*dBm, txcount=10 ):
        "Build demo-like topology"
        self.nodecount, self.txcount = nodecount, txcount

        # Add non-ROADM elements: host, switch, terminal, mux
        # This corresponds to the hardware's "comb source"
        transceivers = tuple( (f'tx{ch}', power)
                              for ch in range( txcount ) )
        topts = { 'transceivers': transceivers, 'monitor_mode': 'in' }
        for i in range( 1, nodecount+3 ):
            h = self.hostname( i )
            self.addHost( h )
            self.addSwitch( f's{i}' )
            self.addSwitch( f't{i}', cls=Terminal, **topts)
            self.addSwitch( f'mux{i}', cls=MUX )
            port = netconfPortBase + i
            self.addSwitch( f'R{i}', cls=Lumentum, netconfPort=port )

        # Links
        linein, lineout = self.linein, self.lineout
        muxin, muxout = txcount+1, txcount+2
        self.muxin, self.muxout = muxin, muxout
        addcomb, dropcomb = self.addport(1), self.dropport(1)
        addthru, dropthru = self.addport(4), self.dropport(4)
        for i in range( 1, nodecount+3 ):
            # "Comb": host<->switch<->terminal<->mux(/demux)
            for tx in range( 1, txcount+1 ):
                self.addLink( f's{i}', f't{i}', tx, tx )
                # Bidirectional term<->mux links
                self.wdmLink( f't{i}', f'mux{i}', txcount+tx, tx,
                              cls=OpticalLink, spans=[1.0*m] )
            h = self.hostname( i )
            self.addLink( h, f's{i}', port2=txcount+1 )
            r = i
            self.wdmLink( f'mux{i}', f'R{r}', muxout, addcomb)
            self.wdmLink( f'R{r}', f'mux{i}', dropcomb, muxin )
            # Cross-connects for intermediate ROADM pairs
            if 1 < i <= nodecount and r%2 == 0:
                self.wdmLink( f'R{r}', f'R{r+1}', dropthru, addthru )
                self.wdmLink( f'R{r+1}', f'R{r}', dropthru, addthru )
            # Line ports
            if i < nodecount+3 and r%2 == 1:
                # BL: not sure if this matches hardware or not
                if r == 1:
                    spans = [10.0*km]
                else:
                    spans = [25.0*km]
                self.wdmLink(f'R{r}', f'R{r+1}',
                             lineout, linein, spans=spans )
                self.wdmLink(f'R{r+1}', f'R{r}',
                             lineout, linein, spans=spans )


def configComb( net, chbase=1 ):
    """Statically configure Terminal + mux into 'comb source'
       to model testbed hardware"""
    info( '*** Configuring terminals + muxes \n' )
    # Parameters and ports
    topo = net.topo
    txcount, nodecount = topo.txcount, topo.nodecount
    muxin, muxout = topo.muxin, topo.muxout
    for i in range( 1, nodecount+3):
        term, mux = net.get( f't{i}', f'mux{i}')
        for tx in range( 1, txcount+1 ):
            ch = chbase-1+tx
            # Terminal: eth{ch} <-> wdm{txcount+ch}
            term.connect( ethPort=tx, wdmPort=txcount+tx,
                          channel=ch)
            # Mux: (tx,rx) <-> (muxout, muxin)
            mux.connect( tx, muxout, [ch] )
            mux.connect( muxin, tx, [ch] )
    for i in range( 1, nodecount+1 ):
        net[ f't{i}' ].turn_on()
    info( '*** Done configuring terminals + muxes')
    # Question: how do we want to configure the switch?
    # Perhaps ecmp or something???


if __name__ == '__main__':
    cleanup()  # Just in case!
    setLogLevel('info')
    if 'clean' in argv: exit( 0 )
    if len(argv) == 1:
        argv.extend('netconf cli'.split())
    topo = LumentumLinear( nodecount=4, txcount=5 ) #90
    net = Mininet( topo=topo, controller=None )
    restServer = RestServer( net )
    net.start()
    configComb( net )
    restServer.start()
    if 'netconf' in argv:
        netconfServer = NetconfServer( net )
        netconfServer.start()
    if 'plot' in argv:
       plotNet(net, outfile='hwtopo.png', directed=True,
               layout='dot', colorMap={Lumentum: 'red', MUX: 'darkGreen'})
    if 'cli' in argv:
        CLI(net)
    if 'hang' in argv:
        while True:
            sleep(20)
    if 'netconf' in argv:
        netconfServer.stop()
    restServer.stop()
    net.stop()
    info( 'Done.\n')

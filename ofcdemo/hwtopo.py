#!/usr/bin/env python3

"""
hwtopo.py: hardware-like topology for OFC 2021 demo

Implements LumentumLinear, a topology intended to
mimic the hardware testbed topology for the OFC 2021
demo.
"""

from dataplane import ( OpticalLink,
                        UnidirectionalOpticalLink as ULink,
                        ROADM, Terminal,
                        OpticalNet as Mininet,
                        km, m, dB, dBm )

from sys import argv
from mno.ofcdemo.demolib import OpticalCLI as CLI, cleanup
from mno.rest import RestServer
if 'netconf' in argv:
    from mno.ofcdemo.netconfserver import NetconfServer
from mno.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup



### Lumentum ROADM class

netconfPortBase = 1830

class Lumentum( ROADM ):
    "ROADM with a netconf port"
    def __init__( self, *args, netconfPort=None, **kwargs):
        if not netconfPort:
            raise Exception('Lumnentum: netconfPort required')
        super().__init__(*args, **kwargs)
        self.netconfPort = netconfPort


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

    def hostname( self, i ):
        "Return hostname for host i"
        if i == 1: return 'RRU1'
        if i == self.nodecount: return 'RRU2'
        return f'BBU{i-1}'

    def build( self, nodecount=4, power=0*dBm, txcount=10 ):
        "Build demo-like topology"
        self.nodecount, self.txcount = nodecount, txcount

        # Add non-ROADM elements: host, switch, terminal, mux
        # This corresponds to the hardware's "comb source"
        transceivers = tuple( (f'tx{ch}', power)
                              for ch in range( txcount ) )
        topts = { 'transceivers': transceivers, 'monitor_mode': 'in' }
        for i in range( 1, nodecount+1 ):
            h = self.hostname( i )
            self.addHost( h )
            self.addSwitch( f's{i}' )
            self.addSwitch( f't{i}', cls=Terminal, **topts)
            self.addSwitch( f'mux{i}', cls=ROADM )

        # Add ROADMS
        for i in range( 1, nodecount+3 ):
            port = netconfPortBase + i
            self.addSwitch( f'R{i}', cls=Lumentum, netconfPort=port )

        # Links
        linein, lineout = self.linein, self.lineout
        muxin, muxout = txcount+1, txcount+2
        self.muxin, self.muxout = muxin, muxout
        addcomb, dropcomb = self.addport(1), self.dropport(1)
        addthru, dropthru = self.addport(4), self.dropport(4)
        r = 1
        for i in range( 1, nodecount+1 ):
            # "Comb": host<->switch<->terminal<->mux(/demux)
            for tx in range( 1, txcount+1 ):
                self.addLink( f's{i}', f't{i}', tx, tx )
                # Bidirectional term<->mux links
                self.wdmLink( f't{i}', f'mux{i}', txcount+tx, tx,
                              cls=OpticalLink, spans=[1.0*m] )
            h = self.hostname( i )
            self.addLink( h, f's{i}', port2=txcount+1 )
            self.wdmLink( f'mux{i}', f'R{r}', muxout, addcomb)
            self.wdmLink( f'R{r}', f'mux{i}', dropcomb, muxin )
            # Cross-connects for intermediate ROADM pairs
            if 1 < i < nodecount and r%2 == 0:
                self.wdmLink( f'R{r}', f'R{r+1}', dropthru, addthru )
                self.wdmLink( f'R{r+1}', f'R{r}', dropthru, addthru )
                r += 1
            # Line ports
            if i < nodecount:
                # BL: not sure if this matches hardware or not
                if r == 1:
                    spans = [10.0*km]
                else:
                    spans = [25.0*km]
                self.wdmLink(f'R{r}', f'R{r+1}',
                             lineout, linein, spans=spans )
                self.wdmLink(f'R{r+1}', f'R{r}',
                             lineout, linein, spans=spans )
            r += 1


def configComb( net, chbase=1 ):
    """Statically configure Terminal + mux into 'comb source'
       to model testbed hardware"""
    info( '*** Configuring terminals + muxes \n' )
    # Parameters and ports
    topo = net.topo
    txcount, nodecount = topo.txcount, topo.nodecount
    muxin, muxout = topo.muxin, topo.muxout
    for i in range( 1, nodecount+1):
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
    # Question: how do we want to configure the switch?
    # Perhaps ecmp or something???


if __name__ == '__main__':
    cleanup()  # Just in case!
    setLogLevel('info')
    if 'clean' in argv: exit( 0 )

    topo = LumentumLinear( nodecount=4, txcount=10 )
    net = Mininet( topo=topo, controller=None )
    restServer = RestServer( net )
    net.start()
    restServer.start()
    if 'netconf' in argv:
        netconfServer = NetconfServer( net )
        netconfServer.start()
    configComb( net )
    if 'plot' in argv:
       plotNet(net, outfile='lroadm.png', directed=True,
               layout='neato', colorMap={Lumentum: 'darkGreen'})
    CLI(net)
    if 'netconf' in argv:
        netconfServer.stop()
    restServer.stop()
    net.stop()
    info( 'Done.\n')

#!/usr/bin/env python3

"""
unilinear1.py: unidirectional linear network with
               1-degree ROADMs and split Terminal uplink/downlink.

This may be more complicated than what we
actually want. We are using the base unidirectional
ROADMs without any interconnection between them,
in order to avoid the looping bug in the simulator.

This does have the nice feature of minimizing ports at
the expense of cabling complexity.

An alternate design, simpler in some ways, is to
interconnect the ROADMs vertically to create real
2-degree, bi-directional ROADMs.
"""

from dataplane import ( OpticalLink,
                        UnidirectionalOpticalLink as ULink,
                        ROADM, Terminal,
                        OpticalNet as Mininet,
                        km, m, dB, dBm )

# from rest import RestServer

from mno.ofcdemo.demolib import OpticalCLI, cleanup
from mno.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.link import Link
from mininet.nodelib import LinuxBridge
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

from sys import argv


class OpticalTopo( Topo ):
    "Topo with convenience methods for optical networks"

    def wdmLink( self, node1, node2, port1, port2,  **kwargs ):
        "Convenience function to add a unidirectional link"
        kwargs.update(cls=ULink)
        self.addLink( node1, node2, port1=port1, port2=port2, **kwargs )

    def ethLink( self, *args, **kwargs ):
        "Clarifying alias for addLink"
        self.addLink( *args, **kwargs, cls=Link )

    def addTerminal( self, *args, **kwargs ):
        "Convenience alias for addSwitch( ... cls=Terminal )"
        kwargs.setdefault( 'cls', Terminal )
        return self.addSwitch( *args, **kwargs )

    def addROADM( self, *args, **kwargs ):
        "Convenience alias for addSwitch( ... cls=ROADM )"
        kwargs.setdefault( 'cls', ROADM )
        return self.addSwitch( *args, **kwargs )



class UniLinearTopo( OpticalTopo ):
    """A linear network connected by two strings of
       unidirectional ROADMs in opposite directions."""

    # ROADM port numbering
    # Note port 0 seems to conflict with lo0/management port
    linein  = 1
    lineout = 2
    def addport(self, dst): return 2+dst
    def dropport(self, src): return 2+self.nodecount+src

    # Terminal port numbering (switch uses same ethport)
    def ethport(self, dst): return dst
    def uplink(self, dst):  return self.nodecount+dst
    def downlink(self, src): return 2*self.nodecount+src

    # Network topology
    def build(self, power=0*dBm, nodecount=3):
        """Create a unidirectional linear network with the specified
           operational power and node and transceiver counts"""
        self.nodecount = nodecount
        # Add nodes: (host, switch, terminal, ROADMS (east, west))
        # Note doubled transceivers for unidirectional links!
        # We also waste a transceiver/port pair for loopback
        transceivers = tuple((f'tx{ch}', power, 'C')
                             for ch in range(1, 2*nodecount+1))
        topts = {'transceivers': transceivers, 'monitor_mode': 'in'}
        ropts = {} # was: { 'wss_dict': {ch:(7.0,None) for ch in range(1,91)}}
        sopts = {'cls': LinuxBridge}
        for i in range(1, nodecount+1):
            self.addHost(f'h{i}')
            self.addSwitch(f's{i}', **sopts)
            self.addTerminal(f't{i}', **topts)
            self.addROADM(f're{i}', **ropts)
            self.addROADM(f'rw{i}', **ropts)

        # WAN Optical link parameters
        boost = ('boost', {'target_gain':17*dB},)
        aparams = {'target_gain': 50*km*.22, 'monitor_mode':'out'}
        spans = [50*km, ('amp1', aparams), 50*km, ('amp2', aparams)]

        # Port number helper function aliases
        linein, lineout = self.linein, self.lineout
        addport, dropport = self.addport, self.dropport
        uplink, downlink = self.uplink, self.downlink

        # Add links for each node/POP
        for node in range(1, nodecount+1):
            # Unidirectional roadm->roadm optical links
            lopts = dict(boost=boost, spans=spans)
            if node < nodecount:
                self.wdmLink(f're{node}', f're{node+1}', **lopts,
                             port1=lineout, port2=linein)
            if node > 1:
                self.wdmLink(f'rw{node}', f'rw{node-1}', **lopts,
                             port1=lineout, port2=linein)
            # Uplinks/downlinks to/from destination nodes
            for dest in range(1, nodecount+1):
                if dest == node: continue
                # One switch<->terminal link per remote node
                port1 = port2 = self.ethport(dest)
                self.ethLink(
                    f's{node}', f't{node}', port1=port1, port2=port2)
                # Inbound and outbound links
                outbound = f're{node}' if dest>node else f'rw{node}'
                inbound = f'rw{node}' if dest>node else f're{node}'
                self.wdmLink(f't{node}', outbound, spans=[1*m],
                             port1=uplink(dest), port2=addport(dest))
                self.wdmLink(inbound, f't{node}', spans=[1*m],
                             port1=dropport(dest), port2=downlink(dest))
            # Host-switch links
            self.ethLink(f'h{node}', f's{node}', port1=1, port2=0)

# Configuration

def config(net, mesh=False, root=1):
    """Configure linear, unidirectional network
       mesh: configure full mesh? False
       root: root node of star topology if not mesh
       Routing strategy:
       - We assign a channel to each (src, dst) pair to avoid conflicts.
       - For the star topology, we root everything at root.
       - For the full mesh, we route signals eastbound or westbound
         as needed."""

    info("*** Configuring network...\n")

    # Helper functions
    topo, nodecount = net.topo, net.topo.nodecount
    linein, lineout = topo.linein, topo.lineout
    addport, dropport = topo.addport, topo.dropport
    uplink, downlink, ethport = topo.uplink, topo.downlink, topo.ethport

    # Allocate Channels:
    # Each distinct (src, dst) pair gets its own channel,
    # which eliminates lightpath routing conflicts.
    channels = {}
    ch = 1
    for src in range(1, nodecount+1):
        for dst in range(1, nodecount+1):
            if not mesh and src != root and dst != root:
                continue
            # We ignore loopback for now
            if src == dst: continue
            channels[src, dst] = ch
            ch += 1
    print("Channel assignment:")
    print(channels)

    # Set of all channels for calculating pass channels
    chset = set(channels.values())

    for i in range(1, nodecount+1):  # local node
        for j in range(1, nodecount+1):  # remote node
            if i == j: continue
            # Star topology is rooted at root
            if not mesh and i != root and j != root:
                continue
            # Configure ROADMS with add/drop/pass channels
            outbound = net[f're{i}'] if j>i else net[f'rw{i}']
            inbound = net[f'rw{i}'] if j>i else net[f're{i}']
            # Channels that are not added/dropped are passed/forwarded
            addch, dropch = channels[i,j], channels[j,i]
            print(f'{outbound} add  ch{addch} port {addport(j)}')
            outbound.connect(addport(j), lineout, [addch])
            print(f'{inbound} drop ch{dropch} port {dropport(j)}')
            inbound.connect(linein, dropport(j), [dropch])
            if 1 < i < nodecount:
                passchannels = chset - {addch, dropch}
                print(inbound, 'pass', passchannels)
                inbound.connect(linein, lineout, passchannels)
                print(outbound, 'pass', passchannels)
                outbound.connect(linein, lineout, passchannels)
            # Configure terminal uplinks and downlinks
            terminal = net[f't{i}']
            terminal.connect(
                ethPort=ethport(j), wdmPort=uplink(j), channel=addch)
            terminal.connect(
                wdmPort=downlink(j), ethPort=ethport(j), channel=dropch)

    # Turn on terminals
    for i in range(1, nodecount+1):
        net[f't{i}'].turn_on()


class CLI( OpticalCLI ):
    "CLI with config command"
    def do_config(self, _line):
        config(self.mn)


if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')
    if len(argv) == 2 and argv[1] == 'clean': exit(0)

    topo = UniLinearTopo(nodecount=4)
    net = Mininet(topo=topo, controller=None)
    # restServer = RestServer(net)
    net.start()
    # restServer.start()
    plotNet(net, outfile='unilinear1.png', directed=True,
            layout='neato')
    info( '*** Use config command to configure network \n' )
    # config(net)
    CLI(net)
    # restServer.stop()
    net.stop()

#!/usr/bin/env python3

"""
unilinear2.py: unidirectional linear network with
               2-degree ROADMs and split Terminal uplink/downlink.

This is somewhat simpler than unilinear1.py because
the middle ROADMs are 2-degree (though the endpoint ROADMs
are still 1-degre.)
"""

from mnoptical.dataplane import ( OpticalLink,
                        UnidirectionalOpticalLink as ULink,
                        ROADM, Terminal,
                        OpticalNet as Mininet,
                        km, m, dB, dBm )

# from mnoptical.rest import RestServer

from mnoptical.ofcdemo.demolib import OpticalCLI, cleanup
from mnoptical.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.link import Link
from mininet.node import OVSBridge
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


class UniLinearTopo2( OpticalTopo ):
    """A linear network connected by a string of
       2-degree unidirectional ROADMs."""

    # ROADM port numbering
    # Eastbound route and Westbound route line ports
    # (Note port 0 seems to conflict with lo0/management port!)
    eastin = 1
    eastout = 2
    westin = 3
    westout = 4
    # Select line in and out from i to j
    def linein(self, i, j): return self.eastin if i<j else self.westin
    def lineout(self, i, j): return self.eastout if i<j else self.westout
    # Local add and drop ports
    def addport(self, dst): return 4+dst
    def dropport(self, src): return 4+self.nodecount+src

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
        ropts = {}  # was: {'wss_dict': {ch:(7.0,None) for ch in range(1,91)}}
        for i in range(1, nodecount+1):
            self.addHost(f'h{i}')
            self.addSwitch(f's{i}')
            self.addTerminal(f't{i}', **topts)
            self.addROADM(f'r{i}', **ropts)

        # WAN Optical link parameters
        boost = ('boost', {'target_gain':17*dB},)
        aparams = {'target_gain': 50*km*.22, 'monitor_mode':'out'}
        spans = [50*km, ('amp1', aparams), 50*km, ('amp2', aparams)]

        # Aliases for convenience
        eastin, eastout = self.eastin, self.eastout
        westin, westout = self.westin, self.westout
        addport, dropport = self.addport, self.dropport
        uplink, downlink = self.uplink, self.downlink

        # Add links for each node/POP
        for node in range(1, nodecount+1):
            # Eastbound and westbound roadm->roadm links
            lopts = dict(boost=boost, spans=spans)
            if node < nodecount:
                self.wdmLink(f'r{node}', f'r{node+1}', **lopts,
                             port1=eastout, port2=eastin)
            if node > 1:
                self.wdmLink(f'r{node}', f'r{node-1}', **lopts,
                             port1=westout, port2=westin)
            # Uplinks/downlinks to/from destination nodes
            for dest in range(1, nodecount+1):
                # One switch<->terminal link per dest node
                port1 = port2 = self.ethport(dest)
                if dest == node:
                    # Host link for local traffic
                    self.ethLink(f'h{node}', f's{node}', port2=port2)
                    continue
                # Terminal link for remote traffic
                self.ethLink(
                    f's{node}', f't{node}', port1=port1, port2=port2)
                # Terminal uplink and downlink to/from roadm
                self.wdmLink(f't{node}', f'r{node}', spans=[1*m],
                             port1=uplink(dest), port2=addport(dest))
                self.wdmLink(f'r{node}', f't{node}', spans=[1*m],
                             port1=dropport(dest), port2=downlink(dest))

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
    eastin, eastout = topo.eastin, topo.eastout
    westin, westout = topo.westin, topo.westout
    linein, lineout = topo.linein, topo.lineout
    addport, dropport = topo.addport, topo.dropport
    uplink, downlink, ethport = topo.uplink, topo.downlink, topo.ethport

    # Allocate Channels:
    # Each distinct (src, dst) pair gets its own channel,
    # which eliminates lightpath routing conflicts.
    channels, pairs = {}, {}
    ch = 1
    for src in range(1, nodecount+1):
        for dst in range(1, nodecount+1):
            if not mesh and src != root and dst != root:
                continue
            # We ignore loopback for now
            if src == dst: continue
            channels[src, dst] = ch
            pairs[ch] = (src, dst)
            ch += 1
    print("Channel assignment:")
    print('\n'.join(f"ch{ch}: r{pair[0]} -> r{pair[1]}"
                    for ch, pair in pairs.items()))

    for i in range(1, nodecount+1):  # local node
        # Pass all channels that are not added or dropped
        passchannels = set(channels.values())
        roadm = net[f'r{i}']
        for j in range(1, nodecount+1):  # remote node
            # Skip loopback connections
            if i == j: continue
            # Star topology only connects to/from root
            if not mesh and root not in (i, j): continue
            # Add and drop channels for i->j, j->i
            addch, dropch = channels[i,j], channels[j,i]
            print(roadm, f'add  ch{addch} port {addport(j)} -> {j}')
            roadm.connect(addport(j), lineout(i,j), [addch])
            print(roadm, f'drop ch{dropch} port {dropport(j)} <- {j}')
            roadm.connect(linein(j,i), dropport(j), [dropch])
            # Don't pass add/drop channels
            passchannels.remove(addch)
            passchannels.remove(dropch)
            # Configure terminal uplinks and downlinks
            terminal = net[f't{i}']
            terminal.connect(
                ethPort=ethport(j), wdmPort=uplink(j), channel=addch)
            terminal.connect(
                wdmPort=downlink(j), ethPort=ethport(j), channel=dropch)
        # Pass all channels that were not added or dropped
        if 1 < i < nodecount:
            print(roadm, 'pass', passchannels)
            roadm.connect(eastin, eastout, passchannels)
            roadm.connect(westin, westout, passchannels)

    # Turn on terminals
    for i in range(1, nodecount+1):
        net[f't{i}'].turn_on()


class CLI( OpticalCLI ):
    "CLI with config command"
    def do_config(self, _line):
        config(self.mn)


def test(net):
    "Configure and test network"
    config(net)
    assert net.pingAll() == 0   # 0% loss


if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')
    if len(argv) == 2 and argv[1] == 'clean': exit(0)

    topo = UniLinearTopo2(nodecount=4)
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    # restServer = RestServer(net)
    net.start()
    # restServer.start()
    plotNet(net, outfile='unilinear2.png', directed=True,
            layout='neato')
    info( '*** Use config command to configure network \n' )
    if 'test' in argv:
        test(net)
    else:
        CLI(net)
    # restServer.stop()
    net.stop()

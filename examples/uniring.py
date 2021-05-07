#!/usr/bin/env python3

"""
uniring.py: unidirectional ring network,
            with bidirectional Terminal links.
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
from mininet.examples.linuxrouter import LinuxRouter
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

from functools import partial
from sys import argv


class OpticalTopo( Topo ):
    "Topo with convenience methods for optical networks"

    def wdmLink1( self, *args, **kwargs ):
        "Convenience function to add a unidirectional link"
        kwargs.update(cls=ULink)
        self.addLink( *args, **kwargs )

    def wdmLink2( self, *args, **kwargs ):
        "Convenience function to add a bidirectional link"
        kwargs.update(cls=OpticalLink)
        self.addLink( *args, **kwargs )

    def ethLink( self, *args, **kwargs ):
        "Clarifying alias for addLink"
        self.addLink( *args, **kwargs )

    def addTerminal( self, *args, **kwargs ):
        "Convenience alias for addSwitch( ... cls=Terminal )"
        kwargs.setdefault( 'cls', Terminal )
        return self.addSwitch( *args, **kwargs )

    def addROADM( self, *args, **kwargs ):
        "Convenience alias for addSwitch( ... cls=ROADM )"
        kwargs.setdefault( 'cls', ROADM )
        return self.addSwitch( *args, **kwargs )


class UniRingTopo( OpticalTopo ):
    """Parametrized unidirectional ring network
       Switch/router port numbering (n==nodecount):
       - 0: local port, connected to host
       - 1..n: uplinks/downlinks to terminal transceivers
               1..n and routers 1..n
       Terminal port numbering:
       - 1..n: transceiver WDM in/out ports (bidirectional)
               to/from routers 1..n
       - n+1..2*n ethernet ports (bidirectional)
       ROADM port numbering:
       - 1: line in
       - 2: line out
       - 3..txcount+2: add/drop ports to terminal
    """
    def build(self, power=0*dBm, nodecount=3):
        """Create a simple(?) ring network with the specified
           operational power and node and transceiver counts"""
        self.nodecount = nodecount
        self.txcount = txcount = nodecount
        # Nodes/POPs: Terminals, ROADMs, switches, switches and hosts
        terminals, roadms, switches, hosts = [], [], [], []
        transceivers = tuple((f'tx{ch}', power, 'C')
                             for ch in range(1, txcount+1))
        tparams = {'transceivers': transceivers, 'monitor_mode': 'in'}
        rparams = { 'monitor_mode': 'in'}
        # was :{'wss_dict': {ch:(7.0,None) for ch in range(1,91)}}
        sparams = {'cls': LinuxRouter}
        for i in range(1, nodecount+1):
            terminals += [self.addTerminal(f't{i}', **tparams)]
            roadms += [self.addROADM(f'r{i}', **rparams)]
            switches += [self.addNode(f's{i}', **sparams)]
            hosts += [self.addHost(f'h{i}')]

        # Optical link parameters
        boost = ('boost', {'target_gain':17*dB})
        aparams = {'target_gain': 50*km*.22 }
        spans = [50*km, ('amp1', aparams), 50*km, ('amp2', aparams)]

        linein, lineout = 1, 2
        for i in range(nodecount):
            # Unidirectional roadm->roadm optical links
            self.wdmLink1(roadms[i], roadms[(i+1) % nodecount],
                          port1=lineout, port2=linein,
                          boost=boost, spans=spans)
            # Bidirectional terminal <-> roadm optical links
            for port in range(1, txcount+1):
                self.wdmLink2(roadms[i], terminals[i],
                              port1=port+lineout, port2=port,
                              spans=[1*m])
            # Terminal<->router and host<->router links
            for txport in range(1, txcount+1):
                self.ethLink(switches[i], terminals[i],
                             port1=txport, port2=txcount+txport)
            # Host-switch links
            self.ethLink(hosts[i], switches[i], port2=txcount+1)



# Helper functions

linein, lineout = 1, 2

def fwd(roadm, channels):
    print(roadm, 'fwd', channels)
    roadm.connect(linein, lineout, channels)
def drop(roadm, dst, channel):
    print(roadm, 'drop', channel)
    roadm.connect(linein, lineout+dst, [channel])
def add(roadm, src, channel):
    print(roadm, 'add', channel)
    roadm.connect(lineout+src, lineout, [channel])


# Configuration (for testing, etc.)

def config(net):
    """Configure routed ring network.
       This is complicated because we are configuring
       both the optical and packet networks,
       and because we're configuring a full mesh
       of IP routers."""
    info("*** Configuring network...\n")
    nodecount = net.topo.nodecount
    # Allocate channel for each pair of nodes
    channels, ch = {}, 1
    for i in range(1, nodecount+1):
        for j in range(i+1, nodecount+1):
            channels[i,j] = channels[j,i] = ch
            ch += 1
    allchannels = set(channels.values())
    # Configure devices
    for i in range(1, nodecount+1):
        # ROADMs (unidirectional)
        # Add and drop local channels and pass others
        roadm = net[f'r{i}']
        localchannels = set()
        for j in range(1, nodecount+1):
            if i == j: continue
            addch, dropch = channels[i,j], channels[j,i]
            add(roadm, j, addch)
            drop(roadm, j, dropch)
            localchannels.update({addch, dropch})
        fwd(roadm, allchannels - localchannels)
        # Terminals (bidirectional)
        # Pass Ethernet ports through to WDM ports
        # on the appropriate channel
        terminal = net[f't{i}']
        for j in range(1, nodecount+1):
            if i == j: continue
            ethPort, wdmPort = j+nodecount, j
            info(f'*** {terminal}-eth{ethPort} <->'
                 f' {terminal}-wdm{wdmPort}\n')
            terminal.connect(ethPort=ethPort, wdmPort=wdmPort,
                             channel=channels[i,j])
        # Hosts and LinuxRouters
        # Hosts use their local router as a gateway
        host, router = net.get(f'h{i}', f's{i}')
        ip = router.IP()
        host.cmd('ip route flush all')
        host.cmd('ip route add', ip, 'dev', host.defaultIntf())
        host.cmd('ip route add 10.0.0.0/24 via', ip)
        # Routers assign their IP address to all ports
        for intf in router.intfs.values():
            router.cmd('ip addr add dev', intf, ip)
        router.cmd('ip route flush all')
        # Routers set their local downlink route,
        # As well as their point-to-point and next-hop
        # routes to remote routers and hosts
        for j in range(1, nodecount+1):
            # Downlink to local host
            if i == j:
                dev = router.intfs[nodecount+1]
                router.cmd('ip route add', host.IP(), 'dev', dev)
            # Uplink to remote routers/hosts
            else:
                destrouter, dest  = net.get(f's{j}', f'h{j}')
                dev  = router.intfs[j]
                router.cmd('ip route add', destrouter.IP(),
                           'dev', dev)
                router.cmd('ip route add', dest.IP(),
                           'via', destrouter.IP())
    # Turn on Terminals/transceivers
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

    topo = UniRingTopo(nodecount=4)
    net = Mininet(topo=topo)
    # restServer = RestServer(net)
    net.start()
    # restServer.start()
    plotNet(net, outfile='uniring.png', directed=True)
    info( '*** Use config command to configure network \n' )
    # config(net)
    CLI(net)
    # restServer.stop()
    net.stop()

#!/usr/bin/env python3

"""
uniring.py: unidirectional ring network with 1-degree ROADMs
            and bidirectional Terminal<->ROADM links
"""

from dataplane import ( OpticalLink as OLink,
                        UnidirectionalOpticalLink as ULink,
                        ROADM, Terminal,
                        OpticalNet as Mininet,
                        km, m, dB, dBm )

# from rest import RestServer

from mno.ofcdemo.demolib import OpticalCLI, cleanup
from mno.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.examples.linuxrouter import LinuxRouter
from mininet.log import setLogLevel, info, debug
from mininet.clean import cleanup

from functools import partial
from sys import argv


class UniRingTopo(Topo):
    """Parametrized unidirectional ROADM ring network
       ROADM r{i} port numbering:
       - 1: line in
       - 2: line out
       - 3..N+2: add/drop ports from/to terminal
       Terminal t{i} port numbering:
       - 1..N: transceiver uplink/downlink ports (bidirectional)
               to/from ROADM
       - N+1..2*N ethernet ports (bidirectional) to/from router
       Router s{i} port numbering (N==nodecount==txcount):
       - 1..N: uplinks/downlinks to/from terminal
       - N+1: local port, connected to host
    """
    def build(self, power=0*dBm, N=3):
        """Create a 1-degree ROADM ring network, with the specified
           operational power and N ROADM/Terminal/Router/Host nodes"""
        self.N = N

        # Nodes/POPs: ROADM/Terminal/Router/Host
        rparams = { 'monitor_mode': 'in'}
        transceivers = tuple((f'tx{ch}', power) for ch in range(1, N+1))
        tparams = {'transceivers': transceivers, 'monitor_mode': 'in'}
        for i in range(1, N+1):
            self.addSwitch(f'r{i}', cls=ROADM, **rparams)
            self.addSwitch(f't{i}', cls=Terminal, **tparams)
            self.addNode(f's{i}', cls=LinuxRouter )
            self.addHost(f'h{i}')

        # Optical WAN link parameters
        boost = ('boost', {'target_gain': 17*dB})
        aparams = {'target_gain': 50*km*.22}
        spans = [50*km, ('amp1', aparams), 50*km, ('amp2', aparams)]
        linein, lineout = 1, 2

        # Optical and packet links
        for i in range(1, N+1):
            # Unidirectional roadm->roadm optical links
            self.addLink(f'r{i}', f'r{i%N + 1}',
                      port1=lineout, port2=linein,
                      boost=boost, spans=spans, cls=ULink)
            for port in range(1, N+1):
                # Bidirectional terminal <-> roadm optical links
                self.addLink(f't{i}', f'r{i}',
                          port1=port, port2=lineout+port,
                          spans=[1*m], cls=OLink)
                # Terminal<->router ethernet links
                self.addLink(f's{i}', f't{i}', port1=port, port2=N+port)
            # Host-switch ethernet link
            self.addLink(f'h{i}', f's{i}', port2=N+1)


# Helper functions

linein, lineout = 1, 2

def fwd(roadm, channels):
    info(roadm, 'fwd', channels, '\n')
    roadm.connect(linein, lineout, channels)
def drop(roadm, dst, channel):
    info(roadm, 'drop', channel, '\n')
    roadm.connect(linein, lineout+dst, [channel])
def add(roadm, src, channel):
    info(roadm, 'add', channel, '\n')
    roadm.connect(lineout+src, lineout, [channel])


# Configuration (for testing, etc.) using internal/native control API

def configOpticalNet(net):
    """Configure ring of ROADMS and Terminals.
       We connect a full mesh of t{1..N}<->t{1..N}"""
    info("*** Configuring network...\n")
    N = net.topo.N
    # Allocate channel for each pair of nodes
    channels, ch = {}, 1
    for i in range(1, N+1):
        for j in range(i+1, N+1):
            channels[i,j] = channels[j,i] = ch
            ch += 1
    allchannels = set(channels.values())
    # Configure devices
    for i in range(1, N+1):
        # 1-degree/unidirectional ROADMs:
        # Add and drop local channels and pass others
        roadm = net[f'r{i}']
        localchannels = set()
        for j in range(1, N+1):
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
        for j in range(1, N+1):
            if i == j: continue
            ethPort, wdmPort = j+N, j
            debug(f'*** {terminal}-eth{ethPort} <->'
                  f' {terminal}-wdm{wdmPort}\n')
            terminal.connect(ethPort=ethPort, wdmPort=wdmPort,
                             channel=channels[i,j])
    # Turn on Terminals/transceivers
    for i in range(1, N+1):
        net[f't{i}'].turn_on()


def configPacketNet(net):
    """Configure mesh of LinuxRouters and attached hosts.
       This is somewhat complicated because we are connecting
       a full mesh of IP routers connected with point-to-point links.
       The "subnets" are basically /32, i.e. single IP addresses."""
    N = net.topo.N
    for i in range(1, N+1):
        # Hosts and LinuxRouters
        host, router = net.get(f'h{i}', f's{i}')
        # Hosts set their local router as a gateway
        ip, dev = router.IP(), host.defaultIntf()
        host.cmd('ip route flush all &&',
                 'ip route add', ip, 'dev', host.defaultIntf(), '&&',
                 'ip route add default via', ip)
        # Routers assign their IP address to all ports
        for intf in router.intfs.values():
            router.cmd('ip addr add dev', intf, ip)
        # Routers set their local downlink route,
        # and set their point-to-point/next-hop
        # routes to remote routers and hosts
        router.cmd('ip route flush all')
        for j in range(1, N+1):
            # Downlink to local host
            if i == j:
                dev = router.intfs[N+1]
                router.cmd('ip route add', host.IP(), 'dev', dev)
            # Uplink to remote routers/hosts
            else:
                destrouter, dest  = net.get(f's{j}', f'h{j}')
                dev = router.intfs[j]
                router.cmd(
                    'ip route add', destrouter.IP(), 'dev', dev, '&&'
                    'ip route add', dest.IP(), 'via', destrouter.IP())


class CLI( OpticalCLI ):
    "CLI with config command"
    def do_config(self, _line):
        configOpticalNet(self.mn)
        configPacketNet(self.mn)


if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')
    if len(argv) == 2 and argv[1] == 'clean': exit(0)

    topo = UniRingTopo(N=4)
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

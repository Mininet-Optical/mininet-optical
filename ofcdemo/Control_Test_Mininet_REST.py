#!/usr/bin/env python3

"""
apsp.py: all-pairs-shortest-paths routing for ofc demo

The goal is *not* to demonstrate an elaborate routing and
rebalancing algorithm, but to demonstrate how
mininet-optical enables packet-optical SDN controller
development and experimentation!!

So our routing is extremely simple:

1. Every pair of nodes gets a unique channel
2. Routes are shortest paths

Since all the links are the same length, we don't even
have to use Dijkstra's algorithm - BFS works just fine!

"""
import random

from ofcdemo.demolib import DemoTopo
from dataplane import OpticalLink, ROADM

from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR )

from collections import defaultdict
from datetime import datetime
from itertools import chain
from time import sleep



class Mininet_Control_REST(object):

    def __init__(self):
        self.net = RESTProxy()
        # Fetch nodes
        self.net.allNodes = fetchNodes(self.net)
        self.net.switches = sorted(node for node, cls in self.net.allNodes.items()
                              if cls == 'OVSSwitch')
        self.net.terminals = sorted(node for node, cls in self.net.allNodes.items()
                               if cls == 'Terminal')
        self.net.roadms = sorted(node for node, cls in self.net.allNodes.items()
                            if cls == 'ROADM')
        self.net.nodes = self.net.terminals + self.net.roadms

        # Fetch links
        self.net.allLinks, self.net.roadmLinks, self.net.terminalLinks = fetchLinks(self.net)

        # Create adjacency dict
        self.net.graph = self.buildGraph(self.net.allLinks)

        # Fetch ports
        self.net.ports = fetchPorts(self.net, self.net.roadms + self.net.terminals + self.net.switches)

        # Calculate inter-pop routes
        self.net.routes = {node: self.route(node, self.net.graph, self.net.terminals)
                      for node in self.net.terminals}


    ###################### Aamir's code ##############################################
    def getOSNR(self):
        "Return fetchOSNR "
        fetchOSNR(self.net)

    def monitorKeyAndLightpaths(self):
        Monitors_and_Signals ={}
        monitors = self.net.get('monitors').json()['monitors']
        for key in sorted(monitors, key=self.monitorKey):
            response = self.net.get('monitor', params=dict(monitor=key))
            osnrdata = response.json()['osnr']
            Monitors_and_Signals[key] = osnrdata.keys()
        return Monitors_and_Signals
    ##########################################################################################

    def monitorKey(self, monitor):
        "Key for sorting monitor names"
        items = monitor.split('-')
        return items

    def getMonitorKey(self, src_id, dst_id, spanID=1):

        return 'r{}-r{}-amp{}-monitor'.format(src_id, dst_id, spanID)

    def monitorOSNRbyKey(self, key, channel):

        monitors = self.net.get('monitors').json()['monitors']
        for monitor in sorted(monitors, key=self.monitorKey):
            if monitor == key:
                response = self.net.get('monitor', params=dict(monitor=monitor))
                osnrdata = response.json()['osnr']
                for ch, data in osnrdata.items():
                    if ch != str(channel):
                        continue
                    THz = float(data['freq']) / 1e12
                    osnr, gosnr = data['osnr'], data['gosnr']
                    return osnr, gosnr
        return 0, 0

    def monitorOSNR(self, channel, gosnrThreshold=18.0 ):
        """Monitor gOSNR continuously; if any monitored gOSNR drops
           below threshold, return list of (monitor, channel, link)"""
        monitors = self.net.get( 'monitors' ).json()['monitors']
        channel, osnrs, gosnrs, isWorking = channel, list(), list(), 1

        for monitor in sorted( monitors, key=self.monitorKey ):
            response = self.net.get( 'monitor', params=dict( monitor=monitor ) )
            osnrdata = response.json()[ 'osnr' ]
            print(monitor, '\n', osnrdata.items())
            # print( monitor + ':', end=' ' )
            for ch, data in osnrdata.items():
                if ch != str(channel):
                    continue
                THz = float( data['freq'] )/1e12
                osnr, gosnr = data['osnr'], data['gosnr']
                osnrs.append(osnr)
                gosnrs.append(gosnr)
                # print( fmt % ( channel, osnr, gosnr ), end='' )
                #print('ch, osnr, gosnr: ', ch, osnr, gosnr)
                if gosnr < gosnrThreshold:
                    isWorking = 0
                    print( "WARNING! gOSNR %.2f below %.2f dB threshold:" %
                           ( gosnr, gosnrThreshold ) )
                    link = monitors[ monitor ][ 'link' ]
                    print( monitor, '<ch%s:%.2fTHz OSNR=%.2fdB gOSNR=%.2fdB>' %
                           (channel, THz, osnr, gosnr ) )
                    print ( monitor, channel, link )

        return channel, osnrs, gosnrs, isWorking


    def buildGraph(self, links):
        "Return an adjacency dict for links"
        neighbors = defaultdict( defaultdict )
        for link in links:
            src, dst = link  # link is a dict but order doesn't matter
            srcport, dstport = link[ src ], link[ dst ]
            neighbors.setdefault( src, {} )
            neighbors[ src ][ dst ] = dstport
            neighbors[ dst ][ src ] = srcport
        return dict( neighbors )


    def route(self, src, graph, destinations ):
        """Route from src to destinations
           neighbors: adjacency list
           returns: routes dict"""
        routes, seen, paths = {}, set( (src,) ), [ (src,) ]
        while paths:
            path = paths.pop( 0 )
            lastNode = path[ -1 ]
            for neighbor in graph[ lastNode ]:
                if neighbor not in seen:
                    newPath = ( path + (neighbor, ) )
                    paths.append( newPath )
                    if neighbor in destinations:
                        routes[ neighbor ] = newPath
                    seen.add( neighbor)
        return routes



    def configureTerminal(self, terminal, channel, power=0.0):
        "Configure terminals statically: ethN <-> wdmM:channel"
        print("*** Configuring terminals")
        proxies = { terminal: TerminalProxy(terminal) }
        termProxy = proxies[ terminal ]
        ethPorts = sorted( int(port) for port, intf in self.net.ports[ terminal ].items()
                           if 'eth' in intf )
        wdmPorts = sorted( int(port) for port, intf in self.net.ports[ terminal ].items()
                           if 'wdm' in intf )
        #print('ethports, wdmports', ethPorts, wdmPorts)
        print(termProxy)
        ethPort, wdmPort = ethPorts[channel-1], wdmPorts[channel-1]
        #print('Pin-Pout-channel', ethPort, wdmPort, channel)
        termProxy.connect( ethPort=ethPort, wdmPort=wdmPort,
                           channel=channel, power=power )
        print("*** Turning on terminals")


    def turnonTerminal(self, terminal):
        "turn on terminal"
        proxies = {terminal: TerminalProxy(terminal)}
        proxies[terminal].turn_on()


    def configurePacketSwitch(self, src, dst, channel, router, port):
        "Configure Open vSwitch 'routers' using OpenFlow"

        print( "*** Configuring Open vSwitch 'routers' remotely... " )

        def subnet( pop ):
            return '10.%d.0.0/24' % pop

        routerProxy = OFSwitchProxy( name=router, port=port )

        # Initialize flow table
        print( 'Configuring', router, 'at', routerProxy.remote, 'via OpenFlow...' )
        routerProxy.dpctl( 'del-flows' )

        # Find local port
        ethports = sorted( int(port) for port, intf in self.net.ports[ router ].items()
                           if 'eth' in intf )
        print('==router ethports==', ethports)
        localport = ethports[ -1 ]

        # to local
        for protocol in 'ip', 'icmp', 'arp':
            #print('add-flow, proto, dst, port', protocol, subnet(src), localport)
            flow = ( protocol + ',ip_dst=' + subnet( src )+
                     ',actions=dec_ttl,output:%d' % localport )
            # print( router, 'add-flow',  flow )
            routerProxy.dpctl( 'add-flow', flow )
        # to destination
        for protocol in 'ip', 'icmp', 'arp':
            #print('add-flow, proto, dst, port', protocol, subnet(dst), channel)
            flow = ( protocol + ',ip_dst=' + subnet( dst )+
                     ',actions=dec_ttl,output:%d' % channel )
            # print( router, 'add-flow',  flow )
            routerProxy.dpctl( 'add-flow', flow )


    def installPath(self, path, channels):
        "Program a lightpath into the network"
        print("*** Installing path", path, "channels", channels)
        # Install ROADM rules
        for i in range(1, len(path) - 1 ):
            node1, roadm, node2 = path[i-1], path[i], path[i+1]
            port1 = self.net.graph[ node1 ][ roadm ]
            port2 = self.net.graph[ node2 ][ roadm ]
            # For terminal nodes, use the proper channel port(s)
            if i == 1:
                for channel in channels:
                    #print('pin-pout', channel, port2)
                    ROADMProxy( roadm ).connect( channel, port2, [channel] )
            elif i == len(path) - 2:
                for channel in channels:
                    #print('pin-pout', port1, channel)
                    ROADMProxy( roadm ).connect( port1, channel, [channel] )
            # For roadm nodes, forward the channels en masse
            else:
                #print('pin-pout', port1, port2)
                ROADMProxy( roadm ).connect( port1, port2, channels )


    def uninstallPath(self, path, channels):
        "Program a lightpath into the network"
        print("*** Removing path", path, "channels", channels)
        # Uninnstall ROADM rules
        for i in range(1, len(path) - 1 ):
            node1, roadm, node2 = path[i-1], path[i], path[i+1]

            port1 = self.net.graph[ node1 ][ roadm ]
            port2 = self.net.graph[ node2 ][ roadm ]
            # For terminal nodes, use the proper channel port(s)
            if i == 1:
                for channel in channels:
                    print('pin-pout', channel, port2)
                    ROADMProxy( roadm ).connect( channel, port2, [channel], action='remove' )
            elif i == len(path) - 2:
                for channel in channels:
                    print('pin-pout', port1, channel)
                    ROADMProxy( roadm ).connect( port1, channel, [channel], action='remove' )
            # For roadm nodes, forward the channels en masse
            else:
                print('pin-pout', port1, port2)
                ROADMProxy( roadm ).connect( port1, port2, channels, action='remove' )


def Test():
    "Configure and monitor network with N=3 channels for each path"


    def install_lightpath(path, src_id, dst_id, channel, power, net):

        # Install a route
        control.installPath(path=path, channels=[channel])
        # Configure terminals and start transmitting
        terminal = net.terminals[src_id-1]
        control.configureTerminal(terminal=terminal, channel=channel, power=power)
        terminal2 = net.terminals[dst_id-1]
        control.configureTerminal(terminal=terminal2, channel=channel, power=power)
        control.turnonTerminal(terminal=terminal)
        control.turnonTerminal(terminal=terminal2)
        # Configure routers
        router = net.switches[src_id-1]
        router2 = net.switches[dst_id-1]
        control.configurePacketSwitch(src=src_id, dst=dst_id, channel=channel, router=router)
        control.configurePacketSwitch(src=dst_id, dst=src_id, channel=channel, router=router2)

    def uninstall_lightpath(path, channel):
        control.uninstallPath(path=path, channels=[channel])

    control = Mininet_Control_REST()
    net = control.net

    # install ,delete, re-install a lighpath
    src_id, dst_id = 1, 4
    src, dst = net.terminals[src_id-1], net.terminals[dst_id-1]
    path = net.routes[src][dst]
    print(src, '->', dst, path)
    channel = 12
    install_lightpath(path=path, src_id=src_id, dst_id=dst_id, channel=channel, power=0, net=net)
    uninstall_lightpath(path, channel)
    install_lightpath(path=path, src_id=src_id, dst_id=dst_id, channel=channel, power=0, net=net)
    control.monitorOSNR(channel=12, gosnrThreshold=15)
    print('first hop osnr', control.monitorOSNRbyKey('r1-r2-amp1-monitor',channel=12))
    #"""

    # install lightpaths
    """channel_sd = {}
    NUM_WAV = 14
    for channel in range(1,NUM_WAV+1):
        src_id = random.randint(1,4)
        dst_id = random.randint(1,4)
        while dst_id==src_id:
            dst_id = random.randint(1, 4)
        src, dst = net.terminals[src_id-1], net.terminals[dst_id-1]
        path = net.routes[src][dst]
        channel_sd[channel] = (src_id,dst_id)
        install_lightpath(path=path, src_id=src_id, dst_id=dst_id, channel=channel, power=0, net=net)
        ch, osnrs, gosnrs, isWorking = control.monitorOSNR(channel=channel, gosnrThreshold=15)
        print(ch, osnrs, gosnrs, isWorking )
    # """

    # delete these lightpaths
    """for channel in range(1,NUM_WAV+1):
        src_id, dst_id = channel_sd[channel]
        src, dst = net.terminals[src_id-1], net.terminals[dst_id-1]
        path = net.routes[src][dst]
        uninstall_lightpath(path, channel)
    # """

#Test()

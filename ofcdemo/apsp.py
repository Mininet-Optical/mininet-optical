#!/usr/bin/python

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

from ofcdemo.demolib import DemoTopo
from dataplane import OpticalLink, ROADM

from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR )

from collections import defaultdict
from itertools import chain


### Do it!

# FIXME: N > 1 doesn't work yet

def run( net, N=1 ):

    # Fetch nodes
    net.allNodes = fetchNodes( net )
    net.switches = sorted( node for node, cls in net.allNodes.items()
                           if cls == 'OVSSwitch' )
    net.terminals = sorted( node for node, cls in net.allNodes.items()
                        if cls == 'Terminal' )
    net.roadms =  sorted( node for node, cls in net.allNodes.items()
                       if cls == 'ROADM' )
    net.nodes = net.terminals + net.roadms

    # Assign POPs for convenience
    count = len( net.switches )
    net.pops = {}
    for i in range( count ):
        for node in net.switches[i], net.terminals[i], net.roadms[i]:
            net.pops[ node ] = i+1

    # Fetch links
    net.allLinks, net.roadmLinks, net.terminalLinks = fetchLinks( net )

    # Fetch ports
    net.ports = fetchPorts( net, net.roadms + net.terminals + net.switches )

    # Adjacency list
    # Note we only have to worry about single links between nodes
    # We handle the terminals separately
    net.neighbors = defaultdict( defaultdict )
    for link in net.allLinks:
        src, dst = link
        srcport, dstport = link[ src ], link[ dst ]
        net.neighbors.setdefault( src, {} )
        net.neighbors[ src ][ dst ] = dstport
        net.neighbors[ dst ][ src ] = srcport

    #  Calculate inter-pop routes
    net.routes = { node: route( node, net.neighbors, net.terminals )
                   for node in net.terminals }

    # Channel allocation: N channels per endpoint pair

    pops = len( net.terminals )
    net.pairs = set( (net.terminals[i], net.terminals[j] )
                 for i in range(0, pops)
                 for j in range(i+1, pops))
    net.pairChannels, net.channelPairs = {}, {}
    channel = 1
    for pair in net.pairs:
        src, dst = pair
        net.pairChannels.setdefault( (src, dst), [] )
        net.pairChannels.setdefault( (dst, src), [] )
        for _ in range( N ):
            net.pairChannels[src, dst].append( channel )
            net.pairChannels[dst, src].append( channel )
            net.channelPairs[ channel ] = ( src, dst )
            channel += 1
    print( list(net.pairChannels[pair] for pair in net.pairs) )

    # Compute remote channels for each pop
    count = len( net.roadms )
    net.remoteChannels = {}
    for i in range( count ):
        pop = i+1
        src = net.terminals[ i ]
        channels = [ net.pairChannels[src, dst] for dst in net.terminals if src != dst ]
        net.remoteChannels[pop] = channels

    # Print routes
    print( '*** Routes:' )
    for src, entries in net.routes.items():
        for dst, path in entries.items():
            print(src, '->', dst, path, net.pairChannels[src, dst])

    # Install all routes
    installRoutes( net )

    # Configure terminals and start transmitting
    configureTerminals( net )

    # Configure routers
    configurePacketSwitches( net )

    # Count average signal allocation per link
    countSignals( net.channelPairs, net.routes )

    # Fetch OSNR
    fetchOSNR( net )


### Support routines

def canonical( link ):
    "Return link in canonical (sorted) format"
    # Note that we don't have to worry about numerical sorting
    return tuple( sorted( link ) )


### Routing (sorry Dijkstra, we don't need you)

def route( src, neighbors, destinations ):
    """Route from src to destinations
       neighbors: adjacency list
       returns: routes dict"""
    routes, seen, paths = {}, set( (src,) ), [ (src,) ]
    while paths:
        path = paths.pop( 0 )
        lastNode = path[ -1 ]
        for neighbor in neighbors[ lastNode ]:
            if neighbor not in seen:
                newPath = ( path + (neighbor, ) )
                paths.append( newPath )
                if neighbor in destinations:
                    routes[ neighbor ] = newPath
                seen.add( neighbor)
    return routes


### Endpoint configuration


def configureTerminals( net, power=0.0):
    "Configure terminals statically: ethN <-> wdmM:channel"
    print("*** Configuring terminals")
    count = len( net.terminals )
    for i, terminal in enumerate( net.terminals ):
        termProxy = TerminalProxy( terminal )
        # XXX Hacky - should implement port info and use that
        ethPorts = sorted( int(port) for port, intf in net.ports[ terminal ].items()
                           if 'eth' in intf )
        wdmPorts = sorted( int(port) for port, intf in net.ports[ terminal ].items()
                           if 'wdm' in intf )
        channels = sum( net.remoteChannels[ i + 1 ], [] )
        for ethPort, wdmPort, channel in zip(ethPorts, wdmPorts, channels):
            termProxy.connect( ethPort=ethPort, wdmPort=wdmPort,
                               channel=channel, power=power )

def configurePacketSwitches( net ):
    "Configure Open vSwitch 'routers' using OpenFlow"

    print( "*** Configuring Open vSwitch 'routers' remotely... " )

    def subnet( pop ):
        return '10.%d.0.0/24' % pop

    count = len( net.terminals )
    for i in range( count ):
        router = net.switches[ i ]
        routerProxy = OFSwitchProxy( router )
        pop = i+1
        # Initialize flow table
        print( 'Configuring', router, 'at', routerProxy.remote, 'via OpenFlow...' )
        routerProxy.dpctl( 'del-flows' )
        # Same low port assignment as terminals
        ethports = sorted( int( port ) for port, intf in net.ports[ router ].items()
                           if 'eth' in intf )
        channels = net.remoteChannels[pop]
        dests = list(range(1, count+1))
        dests.remove( pop )
        outports = { dest: port for dest, port in zip( dests, ethports ) }
        outports[ pop ] = localport = ethports[-1]
        # print( pop, "OUTPORTS", outports)
        for j in range( count ):
            destpop = j+1
            # Only route to a single channel for now
            for protocol in 'ip', 'icmp', 'arp':
                flow = ( protocol + ',ip_dst=' + subnet( destpop )+
                         ',actions=dec_ttl,output:%d' % outports[ destpop ] )
                # print( router, 'add-flow',  flow )
                routerProxy.dpctl( 'add-flow', flow )


### Route installation

def installPath( path, channels, net):
    "Program a lightpath into the network"
    print("*** Installing path", path, "channels", channels)
    # Install ROADM rules
    for i in range(1, len(path) - 1 ):
        node1, roadm, node2 = path[i-1], path[i], path[i+1]
        # This is a bit tricky. neighbors[node1] is a
        # dict of src:srcport, dst:dstport, so we
        # need to extract the dstport!!
        port1 = net.neighbors[ node1 ][ roadm ]
        port2 = net.neighbors[ node2 ][ roadm ]
        # For terminal nodes, use the proper channel port(s)
        if i == 1:
            ports1 = channelPorts( node1, channels, net )
            for channel in channels:
                ROADMProxy( roadm ).connect( ports1[channel], port2, [channel] )
        elif i == len(path) - 2:
            ports2 = channelPorts( node2, channels, net )
            for channel in channels:
                ROADMProxy( roadm ).connect( port1, ports2[channel], [channel] )
        # For roadm nodes, forward the channels en masse
        else:
            ROADMProxy( roadm ).connect( port1, port2, channels )

    print("*** Done with", path)


def channelPorts( node, channels, net ):
    "Return the {router, terminal, roadm} ports for node/channels"
    pop = net.pops[ node ]
    # FIXME: shouldn't recompute this every time
    # Note that this channelPort is the same on the router,
    # terminal, and roadm and can be used for all of them
    channelPorts = { channel: port for port, channel
                     in enumerate( sum(net.remoteChannels[pop], []), start=1) }
    return channelPorts


def installRoutes( net):
    print( '*** Configuring ROADMs' )
    for src, dst in net.pairs:
        path = net.routes[src][dst]
        channels = net.pairChannels[ src, dst ]
        installPath( path, channels, net )


def countSignals( channelPairs, routes):
    "Calculate average channel count per link"

    # Calculate signals for each link
    linkSignals = defaultdict( list )
    for channel, pair in channelPairs.items():
        src, dst = pair
        path = routes[ src ][ dst ]
        assert path[0] == src and path[-1] == dst
        for i in range( 0, len(path) - 1):
            link = path[i], path[i+1]
            link = canonical( link )
            assert channel not in linkSignals[ link ]
            linkSignals[ link ].append( channel )

    print("*** Link signals:")
    for link in sorted( linkSignals ):
        print( link, linkSignals[link] )

    # Compute average signal count
    signalCount = sum( len(clist) for clist in linkSignals.values() )
    avgCount = signalCount / len( linkSignals )
    print("Average signal count = %.2f" % avgCount )


if __name__ == '__main__':
    net = RESTProxy()
    run( net )

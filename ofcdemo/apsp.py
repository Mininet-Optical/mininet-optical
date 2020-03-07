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
from datetime import datetime
from itertools import chain
from time import sleep


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
    net.pops = { node: i+1
                 for i in range( count )
                 for node in ( net.switches[i], net.terminals[i], net.roadms[i] ) }

    # Fetch links
    net.allLinks, net.roadmLinks, net.terminalLinks = fetchLinks( net )

    # Create adjacency dict
    net.neighbors = adjacencyDict( net.allLinks )

    # Fetch ports
    net.ports = fetchPorts( net, net.roadms + net.terminals + net.switches )

    # Calculate inter-pop routes
    net.routes = { node: route( node, net.neighbors, net.terminals )
                   for node in net.terminals }

    # Allocate N channels per endpoint pair
    print( '*** Allocating channels' )
    net.pairs, net.pairChannels, net.channelPairs = allocateChannels(
        net.terminals, N )

    # Compute remote channels for each pop
    count = len( net.roadms )
    net.remoteChannels = {}
    for i in range( count ):
        pop, src  = i+1, net.terminals[ i ]
        channels = [ net.pairChannels[src, dst] for dst in net.terminals
                     if src != dst ]
        net.remoteChannels[ pop ] = channels

    # Print routes
    print( '*** Routes:' )
    for src, dst in net.pairs:
        path = net.routes[src][dst]
        print(src, '->', dst, path, net.pairChannels[src, dst])

    # Install all routes
    installRoutes( net )

    # Configure terminals and start transmitting
    configureTerminals( net )

    # Configure routers
    configurePacketSwitches( net )

    # Count average signal allocation per link
    countSignals( net.channelPairs, net.routes )

    # Monitor OSNR
    print( '*** Monitoring OSNR...' )
    failures = monitorOSNR( net )
    reroutes = [ (channel, link)
                 for _monitor, channel, link in failures ]

    # Reroute (not yet implemented )
    reroute( net, reroutes )



### Support routines

def canonical( link ):
    "Return link in canonical (sorted) format"
    # Note that we don't have to worry about numerical sorting
    return tuple( sorted( link ) )


def monitorKey( monitor ):
    "Key for sorting monitor names"
    items =  monitor.split( '-' )
    return items

def monitorOSNR( net, gosnrThreshold=18.0 ):
    """Monitor gOSNR continuously; if any monitored gOSNR drops
       below threshold, return list of (monitor, channel, link)"""
    monitors = net.get( 'monitors' ).json()['monitors']
    fmt = '%s:(%.0f,%.0f) '
    failures = []
    while not failures:
        logtime = datetime.now().strftime("%H:%M:%S")
        # print( logtime, 'OSNR, gOSNR from monitors:' )
        for monitor in sorted( monitors, key=monitorKey ):
            response = net.get( 'monitor', params=dict( monitor=monitor ) )
            osnrdata = response.json()[ 'osnr' ]
            # print( monitor + ':', end=' ' )
            for channel, data in osnrdata.items():
                THz = float( data['freq'] )/1e12
                osnr, gosnr = data['osnr'], data['gosnr']
                # print( fmt % ( channel, osnr, gosnr ), end='' )
                if gosnr < gosnrThreshold:
                    print( "WARNING! gOSNR %.2f below %.2f dB threshold:" %
                           ( gosnr, gosnrThreshold ) )
                    link = monitors[ monitor ][ 'link' ]
                    print( monitor, '<ch%s:%.2fTHz OSNR=%.2fdB gOSNR=%.2fdB>' %
                           (channel, THz, osnr, gosnr ) )
                    failures.append( ( monitor, channel, link ) )
            # print()
        sleep( 1)
    return failures


def adjacencyDict( links ):
    "Return an adjacency dict for links"
    # Note we only have to worry about single links between nodes
    # We handle the terminals separately
    neighbors = defaultdict( defaultdict )
    for link in links:
        src, dst = link  # link is a dict but order doesn't matter
        srcport, dstport = link[ src ], link[ dst ]
        neighbors.setdefault( src, {} )
        neighbors[ src ][ dst ] = dstport
        neighbors[ dst ][ src ] = srcport
    return dict( neighbors )


# Channel allocation

def allocateChannels( terminals, N ):
    "Allocate N channels per endpoint pair"
    pops = len( terminals )
    pairs = [ (terminals[i], terminals[j])
              for i in range(0, pops)
              for j in range(i+1, pops) ]
    pairChannels, channelPairs = {}, {}
    channel = 1
    for pair in pairs:
        src, dst = pair
        pairChannels.setdefault( (src, dst), [] )
        pairChannels.setdefault( (dst, src), [] )
        for _ in range( N ):
            pairChannels[src, dst].append( channel )
            pairChannels[dst, src].append( channel )
            channelPairs[ channel ] = ( src, dst )
            channel += 1
    return pairs, pairChannels, channelPairs


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


def entriesToReroute( paths, badlink ):
    "Return list of entries in paths containing badlink"
    pair1, pair2 = list( pair ), list( reversed( pair ) )
    result = []
    for entry, paths in paths.items():
        for i in range( len( path ) - 1):
            if path[i:i+2] == pair:
                paths.append( path )
                break

def reroute( net, failures):
    "Reroute failures"
    print( 'failures:', failures)


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

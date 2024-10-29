#!/usr/bin/env python3

"""
pp_control.py: all-pairs-shortest-paths routing for ofc demo

uses demo.py (cf demolib.py for 9 nodes configuration.

The goal is *not* to demonstrate an elaborate routing and
rebalancing algorithm, but to demonstrate how
mininet-optical enables packet-optical SDN controller
development and experimentation!!

Demo:

1. Generating 236 random pairs to fully populate the network
2. Routes are shortest paths
3. Install as many lightpaths as possible
4. Configure the network to install them
5. Simulate a link break
6. Try to reroute the failed LP using the same simple algorithm
7. For the LP that cannot be re-routed, use wavelength discontinuity to route the new potential LPs.
8. Configure the new Terminal end points, the ROADMs and the intermediate Terminal/PP
9. Install the rules in the emulated network

Since all the links are the same length, we don't even
have to use Dijkstra's algorithm - BFS works just fine!

"""

from mnoptical.ofcdemo.demolib import DemoTopo
from mnoptical.dataplane import OpticalLink, ROADM

from mnoptical.ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR )

from collections import defaultdict
from datetime import datetime
from itertools import chain
from time import sleep
import random
import copy
import time

### Do it!

def run( net ):
    "Configure and monitor network with N=3 channels for each path"

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
    print("net.allLinks: ", net.allLinks)

    # Create adjacency dict
    net.neighbors = adjacencyDict( net.allLinks )
    print( '*** Neighbors: ', net.neighbors)

    # Save a copy of net.neighbors for when path need to be removed
    # FIXME: not used at the moment
    # neighbors_old = copy.deepcopy(net.neighbors)

    # Fetch ports
    net.ports = fetchPorts( net, net.roadms + net.terminals + net.switches )

    # Calculate inter-pop routes
    net.routes = { node: route( node, net.neighbors, net.terminals )
                   for node in net.terminals }
    net.routes_old = net.routes
    print( '*** Routing/routes: ', net.routes)

    # Allocate N channels per endpoint pair
    print( '*** Allocating channels' )
    net.pairs, net.pairChannels, net.channelPairs, net.linkSignals, net.channelcount, net.listchannels = allocateChannels_bis(
        net.terminals, net.routes)

    print("channelPairs: ", net.channelPairs)

    # Compute remote channels for each pop
    net.remoteChannels = computeRemoteChannels(net)
    # remoteChannels_old = copy.deepcopy(net.remoteChannels)

    # Print routes
    print( '*** Routes:' )
    for src, dst in net.pairs[:36]:
        path = net.routes[src][dst]
        print(src, '->', dst, path, net.pairChannels[src, dst])

    # Install all routes
    installRoutes( net )

    # Configure terminals and start transmitting
    configureTerminals( net )

    # Configure routers
    # configurePacketSwitches( net )

    # print number of channel used
    print("Number of channel used: ", net.channelcount)

    # Count average signal allocation per link
    # countSignals( net.channelPairs, net.routes )
    countSignals_bis( net.linkSignals )

    # Empty spectrum in each link (for debugging):
    # missinglink, misslistchannels = emptyspectrum( net.linkSignals, net.listchannels )


    ########################################## Re-route ########################################################

    # Create a link break
    print("*** Re routing after a failure")
    src_f = input("Enter the source (src) of the link failure: ")
    dst_f = input("Enter the destination (dst) of the link failure: ")

    count_failed = countfailed(src_f, dst_f, net.linkSignals)

    # Update net.neighbors based on the failure
    # Remove 'dst': XX from 'src' neighbors
    if src_f in net.neighbors and dst_f in net.neighbors[src_f]:
        net.neighbors[src_f].pop(dst_f)

    # Remove 'src': 81 from 'dst' neighbors
    if dst_f in net.neighbors and src_f in net.neighbors[dst_f]:
        net.neighbors[dst_f].pop(src_f)

    print( '*** New neighbors: ', net.neighbors)

    # Re- Calculate inter-pop routes
    net.routes = { node: route( node, net.neighbors, net.terminals )
                   for node in net.terminals }
    print( '*** Re-Routing/routes: ', net.routes)

    # Re-allocate channels per endpoint pair
    print( '*** Re-Allocating channels' )

    (net.pairs, net.pairChannels, net.linkSignals, net.channelcount, net.listchannels,
     net.pairChannels_new, net.pairChannels_old, net.nonrouted, net.pair_to_reroute) = (
        reallocateChannels( src_f, dst_f, net.routes, net.routes_old, net.pairs, net.pairChannels,
                            net.linkSignals, net.listchannels))

    # Re-compute remote channels for each pop
    net.remoteChannels = computeRemoteChannels(net)

    # Print new routes
    print( '*** Re-Routes:' )
    for src, dst in net.pairs[:36]:
        path = net.routes[src][dst]
        print(src, '->', dst, path, net.pairChannels[src, dst])

    # FIXME: Remove old routes + Install new routes only
    # loop issue when removing-adding new only.

    # If any of the failed LP has another available channel using standard RWA,
    if net.channelcount != 0:
        installnewRoutes( net )
        configureTerminalsbis( net)
        turnonterm( net )

    # Configure routers
    #configurePacketSwitches( net )

    # print number of channel used
    print("Number of channel rerouted from the failed one: ", net.channelcount)

    # Count average signal allocation per link
    countSignals_bis( net.linkSignals )

    ################################## Try new eRWA ##################################

    # find subpath for the non rerouted path:
    net.subpaths_dict = subpaths( net.nonrouted, net.routes )

    # Calculate new paths with new channels associated
    newch, pairChannels_justnew, pprules, remoteChannels_new = rerouting(net) #, remoteChannels_new

    # Compute remote channels for each pop
    net.remoteChannels = computeRemoteChannels(net)

    # Install new routes with wavelength discontinuity
    installnewRoutes( net )

    # Configure terminals and start transmitting
    configureTerminalsbis( net)
    # Configure packetponder terminal
    configurePP(net, pprules)
    turnonterm( net )

    # here need to compute new remoteChannels with added path.
    remoteChannels_newpath = computeRemoteChannelsnew(net, remoteChannels_new)

    # Configure routers
    configurePacketSwitches( net, remoteChannels_newpath )

    #FIXME: Install just new rules
    # installnewroutewavechange( net , pairChannels_justnew)

    # debug
    # print("channelPairs: ", pairChannels_justnew)

    # print improvement with eRWA after sRWA
    print("improvement of: ", ((newch / count_failed)* 100), "%")

    countSignals_bis( net.linkSignals )

### Support routines
def computeRemoteChannelsnew(net, remoteChannels_new):
    merge_remoteChannels = {}
    for key in net.remoteChannels:
        merge_remoteChannels[key] = []
        for idx, val in enumerate(remoteChannels_new[key]):
        # Merge both net.remoteChannels and remoteChannels_new so end point Terminal have channel of the new path.
            if val:
                merge_remoteChannels[key].append(val + net.remoteChannels[key][idx])
            else:
                merge_remoteChannels[key].append(net.remoteChannels[key][idx])
    return merge_remoteChannels

def computeRemoteChannels(net):
    count = len( net.roadms )
    remoteChannels = {}
    for i in range( count ):
        pop, src  = i+1, net.terminals[ i ]
        channels = [ net.pairChannels[src, dst] for dst in net.terminals
                     if src != dst]
        remoteChannels[ pop ] = channels
    print( "remoteChannels= ", remoteChannels )
    return remoteChannels

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
        if len(link) == 2:
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
    for _ in range( N ):
        for pair in pairs:
            src, dst = pair
            pairChannels.setdefault( (src, dst), [] )
            pairChannels.setdefault( (dst, src), [] )
            pairChannels[src, dst].append( channel )
            pairChannels[dst, src].append( channel )
            channelPairs[ channel ] = ( src, dst )
            channel += 1
    return pairs, pairChannels, channelPairs

def findwave( pairs, missinglink, misslistchannels, routes ):
    commonnumberlist = {}
    for pair in pairs:
        src, dst = pair
        commonnumberlist.setdefault( (src, dst), [] )
        #print("pair: ", pair)
        path = routes[src][dst]
        common_number = None
        for i in range(0, len(path)-1 ):
            link = path[i], path[i+1]
            link = canonical( link )
            if common_number is None:
                common_number = set(missinglink[link])
            else:
                common_number.intersection_update(missinglink[link])
        for j in path:
            common_number.intersection_update(misslistchannels[j])
        commonnumberlist[src, dst].extend( sorted(common_number) )
    #print("commonnumberlist: ", commonnumberlist)
    return commonnumberlist

def subpaths( pairs, routes ):
    # pairs: the pairs that couldn't be rerouted
    subpath= {}
    for pair in pairs:
        src, dst = pair
        path = routes[src][dst]
        current_subpath= []
        subpath.setdefault( (src, dst), [] )
        for i in range(1, len(path)-2 ):
            current=path[i]
            next_node = path[i + 1]
            if current.startswith('r'):
                terminal_s = 't' + current[1:]
                current_subpath.append(terminal_s)
                current_subpath.append(current)
                current_subpath.append(next_node)
                terminal_d = 't' + next_node[1:]
                current_subpath.append(terminal_d)
                subpath[src, dst].append(current_subpath)
                current_subpath = []
    print("subpath: ", subpath)
    return subpath

def reroutewavechange( pair, subpath, commonnumberlist, net, linkSignals, listchannels,
                       pairChannels_justnew, pprules):
    #for pair in pairs:
    newchannelwavechange = 0
    src, dst = pair
    remoteChannels_pair = {}
    result = wavedisbis(pair, subpath, commonnumberlist)
    print("pair: ", pair, "new path: ", result)
    remoteChannels_pair.setdefault(src, [] )
    remoteChannels_pair.setdefault(dst, [] )
    # condition for empty channel
    if any(list_channel == [] for list_channel in result.values()):
        print("cannot install a lightpath for pair: ", pair)
    else:
        # Update net values:
        for i, path in enumerate(result.keys()):
            s, d = path[0], path[-1]
            net.pairChannels.setdefault( (s, d), [] )
            net.pairChannels.setdefault( (d, s), [] )
            pairChannels_justnew.setdefault( (s, d), [] )
            pprules.setdefault(s, [])
            pprules.setdefault(d, [])
            channels = result[path]
            print("path", path, "channels ", channels)
            channel = channels[0] # take first value if several
            print("channel[0] = ", channel)
            if i == 0:
                pprules[d].append( channel )
            elif i == (len(result.keys())-1):
                pprules[s].append( channel )
            else:
                pprules[s].append( channel )
                pprules[d].append( channel )
            net.pairChannels[s, d].append( channel )
            net.pairChannels[d, s].append( channel )
            pairChannels_justnew[s, d].append( channel )
            #pairChannels_justnew[d, s].append( channel )
            for i in range(0, len(path)-1 ):
                link = path[i], path[i+1]
                link = canonical( link )
                linkSignals[link].append( channel )
                listchannels[path[i]].append( channel )
            listchannels[path[-1]].append( channel )
            if s == src:
                remoteChannels_pair[src].append(channel)
            elif d == dst:
                remoteChannels_pair[dst].append(channel)
        print(" ************ ONE LIGHT PATH HAS BEEN ADDED **************")
        newchannelwavechange += 1
        print("reroutewavechange listchannels: ", listchannels)
        print("reroutewavechange linkSignals: ", linkSignals)
    #print("pairChannels_justnew =", pairChannels_justnew)
    return newchannelwavechange, pairChannels_justnew, pprules, remoteChannels_pair



def wavedisbis( pair, subpath, commonnumberlist):
    result = {}
    # for pair in pairs:
    merged_path =[]
    src, dst = pair
    subpairs = subpath[src, dst]
    commonnumber = []
    for i in range(len(subpairs)):
        current = subpairs[i]
        terminal_start1 = current[0]  # First element of the first subpath
        terminal_end1 = current[-1]
        key = (terminal_end1, terminal_start1) if (terminal_end1, terminal_start1) in commonnumberlist \
            else (terminal_start1, terminal_end1)
        commonnumber = commonnumberlist.get(key, [])
        #print("commonnumber", commonnumber)
        if i == 0:
            result[tuple(current)] = commonnumber
            #print("result", result )
        else:
            previous = tuple(subpairs[i-1])
            if previous in result:
                number = list(set(commonnumber).intersection(result[previous]))
            else:
                last_key, last_value_list = list(result.items())[-1]
                number = list(set(commonnumber).intersection(last_value_list)) #In case the last subpath is a merged one
            if number:
                if previous in result:
                    del result[previous]
                else:
                    result.popitem() #remove last item #del result[list(result[-1])]
                merged_path = list(previous[:-1]) + list(current[2:])
                result[tuple(merged_path)] = number
            else:
                result[tuple(current)] = commonnumber
    # print("final result", result )
    return result

# main reroute with wavelength discontinuity:
def rerouting(net):
    newch = 0
    pairChannels_justnew = {}
    pprules = {}
    remoteChannels_new = {i: [[] for _ in range(len(net.terminals) - 1)] for i in range(1, len(net.terminals) + 1)} #copy.deepcopy(net.remoteChannels)
    r = net.nonrouted
    r_new = []
    for p in r:
        if p in net.pair_to_reroute:
            r_new.extend([p] * net.pair_to_reroute[p][0])
    random.shuffle(r_new)
    print("r_new: ", r_new)
    for pair in r_new:
        src, dst = pair
        missinglink, misslistchannels = emptyspectrum( net.linkSignals, net.listchannels )
        commonnumberlist = findwave( net.pairs[:36], missinglink, misslistchannels, net.routes )
        newchannelwavechange, pairChannels_justnew, pprules, remoteChannels_pair = reroutewavechange( pair,
                                                                        net.subpaths_dict, commonnumberlist, net,
                                                                        net.linkSignals, net.listchannels,
                                                                        pairChannels_justnew, pprules)
        newch = newch + newchannelwavechange
        print("remotechannels_pair: ", remoteChannels_pair)
        # Compute remoteChannels in Terminals so that both wavelength are "available" at end points
        # This is needed for Switch configuration.
        if any(v for v in remoteChannels_pair.values() if v):
            src_index = net.terminals.index(src)
            dst_index = net.terminals.index(dst)
            ch_s = remoteChannels_pair[src][0]
            ch_d = remoteChannels_pair[dst][0]
            if src_index < dst_index:
                remoteChannels_new[dst_index + 1][src_index].append(ch_d)
                remoteChannels_new[src_index + 1][dst_index-1].append(ch_s)
            else:
                remoteChannels_new[dst_index + 1][src_index-1].append(ch_d)
                remoteChannels_new[src_index + 1][dst_index].append(ch_s)
    print("remoteChannels_new of reconfigured pair: ", remoteChannels_new)
    print("New channel added: ", newch)
    print("pprules end: ", pprules)
    return newch, pairChannels_justnew, pprules, remoteChannels_new

# Channel allocation

def allocateChannels_bis( terminals, routes ): #routes has been added
    "N is the maximum channel supported by a link. Ex: 100GHz spacing channels: 73"
    pops = len( terminals )
    pairs = [ (terminals[i], terminals[j])
              for i in range(0, pops)
              for j in range(i+1, pops) ] #Have at least one demand per possible path.
    pairs.extend( (terminals[i], terminals[j])
                  for i, j in (random.sample(range(pops), 2) for _ in range(200)) ) #add random demands
    # consistent random pairs for debugging:
    # pairs = [('t1', 't2'), ('t1', 't3'), ('t1', 't4'), ('t1', 't5'), ('t1', 't6'), ('t1', 't7'), ('t1', 't8'),
    #          ('t1', 't9'), ('t2', 't3'), ('t2', 't4'), ('t2', 't5'), ('t2', 't6'), ('t2', 't7'), ('t2', 't8'),
    #          ('t2', 't9'), ('t3', 't4'), ('t3', 't5'), ('t3', 't6'), ('t3', 't7'), ('t3', 't8'), ('t3', 't9'),
    #          ('t4', 't5'), ('t4', 't6'), ('t4', 't7'), ('t4', 't8'), ('t4', 't9'), ('t5', 't6'), ('t5', 't7'),
    #          ('t5', 't8'), ('t5', 't9'), ('t6', 't7'), ('t6', 't8'), ('t6', 't9'), ('t7', 't8'), ('t7', 't9'),
    #          ('t8', 't9'), ('t1', 't8'), ('t8', 't2'), ('t6', 't3'), ('t1', 't3'), ('t4', 't5'), ('t7', 't4'),
    #          ('t9', 't7'), ('t8', 't9'), ('t8', 't3'), ('t5', 't4'), ('t8', 't9'), ('t2', 't7'), ('t8', 't1'),
    #          ('t2', 't1'), ('t7', 't4'), ('t1', 't8'), ('t9', 't4'), ('t8', 't3'), ('t5', 't4'), ('t8', 't2'),
    #          ('t7', 't5'), ('t6', 't7'), ('t2', 't5'), ('t8', 't1'), ('t2', 't9'), ('t1', 't2'), ('t1', 't2'),
    #          ('t4', 't6'), ('t2', 't3'), ('t4', 't5'), ('t9', 't8'), ('t2', 't7'), ('t9', 't1'), ('t2', 't7'),
    #          ('t7', 't5'), ('t9', 't2'), ('t6', 't4'), ('t6', 't4'), ('t6', 't4'), ('t2', 't3'), ('t2', 't4'),
    #          ('t6', 't4'), ('t9', 't1'), ('t5', 't3'), ('t8', 't6'), ('t2', 't4'), ('t1', 't7'), ('t4', 't6'),
    #          ('t3', 't5'), ('t1', 't7'), ('t4', 't3'), ('t8', 't7'), ('t9', 't6'), ('t1', 't9'), ('t2', 't3'),
    #          ('t8', 't1'), ('t4', 't7'), ('t5', 't8'), ('t9', 't5'), ('t9', 't8'), ('t1', 't9'), ('t9', 't6'),
    #          ('t9', 't1'), ('t1', 't9'), ('t3', 't7'), ('t6', 't1'), ('t5', 't4'), ('t5', 't1'), ('t9', 't4'),
    #          ('t5', 't3'), ('t1', 't4'), ('t1', 't3'), ('t4', 't5'), ('t3', 't5'), ('t7', 't9'), ('t3', 't4'),
    #          ('t4', 't6'), ('t9', 't1'), ('t8', 't7'), ('t6', 't4'), ('t3', 't1'), ('t3', 't9'), ('t1', 't7'),
    #          ('t1', 't5'), ('t4', 't3'), ('t2', 't3'), ('t1', 't4'), ('t1', 't4'), ('t6', 't8'), ('t7', 't5'),
    #          ('t3', 't9'), ('t7', 't5'), ('t1', 't6'), ('t8', 't3'), ('t6', 't7'), ('t8', 't7'), ('t7', 't4'),
    #          ('t1', 't2'), ('t6', 't5'), ('t4', 't2'), ('t5', 't8'), ('t5', 't1'), ('t4', 't1'), ('t8', 't7'),
    #          ('t4', 't1'), ('t2', 't6'), ('t8', 't7'), ('t4', 't3'), ('t4', 't5'), ('t7', 't2'), ('t4', 't1'),
    #          ('t6', 't5'), ('t5', 't2'), ('t3', 't5'), ('t6', 't5'), ('t5', 't8'), ('t9', 't7'), ('t6', 't5'),
    #          ('t7', 't4'), ('t2', 't5'), ('t9', 't2'), ('t1', 't2'), ('t8', 't1'), ('t5', 't8'), ('t1', 't2'),
    #          ('t3', 't7'), ('t9', 't7'), ('t5', 't2'), ('t6', 't7'), ('t9', 't2'), ('t2', 't7'), ('t2', 't7'),
    #          ('t9', 't4'), ('t2', 't6'), ('t6', 't7'), ('t2', 't8'), ('t6', 't4'), ('t9', 't6'), ('t4', 't1'),
    #          ('t3', 't2'), ('t3', 't9'), ('t3', 't8'), ('t2', 't1'), ('t8', 't2'), ('t3', 't2'), ('t7', 't3'),
    #          ('t7', 't1'), ('t8', 't4'), ('t4', 't7'), ('t7', 't5'), ('t8', 't9'), ('t4', 't2'), ('t4', 't7'),
    #          ('t5', 't9'), ('t4', 't6'), ('t7', 't5'), ('t2', 't5'), ('t8', 't7'), ('t9', 't8'), ('t3', 't6'),
    #          ('t5', 't3'), ('t5', 't1'), ('t1', 't5'), ('t2', 't7'), ('t8', 't6'), ('t5', 't8'), ('t2', 't3'),
    #          ('t5', 't2'), ('t3', 't5'), ('t2', 't7'), ('t3', 't8'), ('t8', 't5'), ('t3', 't1'), ('t2', 't3'),
    #          ('t9', 't3'), ('t6', 't9'), ('t3', 't7'), ('t9', 't5'), ('t3', 't7'), ('t8', 't6'), ('t6', 't9'),
    #          ('t5', 't2'), ('t4', 't3'), ('t1', 't5'), ('t8', 't1'), ('t5', 't1'), ('t8', 't5'), ('t7', 't2'),
    #          ('t2', 't4'), ('t4', 't3'), ('t6', 't7'), ('t1', 't4'), ('t1', 't7'), ('t2', 't8'), ('t1', 't4'),
    #          ('t2', 't7'), ('t6', 't2'), ('t7', 't8'), ('t5', 't4'), ('t3', 't4')]
    print("pairs: ", pairs)
    pairChannels, channelPairs = {}, {}
    linkSignals = defaultdict( list )
    listchannels = defaultdict( list )
    channelcount = 0
    for pair in pairs:
        # print("pair: ", pair)
        src, dst = pair
        channel = 1
        path = routes[src][dst]
        pairChannels.setdefault( (src, dst), [] )
        pairChannels.setdefault( (dst, src), [] )
        while channel < 73: #73-23
            if any(channel in listchannels[path[x]] for x in range(len(path))):
                channel +=1
            else:
                channelcount += 1
                pairChannels[src, dst].append( channel )
                pairChannels[dst, src].append( channel )
                channelPairs[ channel ] = ( src, dst )
                for i in range(0, len(path)-1 ):
                    link = path[i], path[i+1]
                    link = canonical( link )
                    linkSignals[link].append( channel )
                    listchannels[path[i]].append( channel )
                listchannels[path[-1]].append( channel )
                channel = 80
                # print("listchannels: ", listchannels)
                # print("linkSignals: ", linkSignals)
    return pairs, pairChannels, channelPairs, linkSignals, channelcount, listchannels

def countfailed(src_f, dst_f, linkSignals):
    link = src_f, dst_f
    count = len(linkSignals[link])
    print(" *** number of failed demands: ", count)
    return count

def reallocateChannels( src_f, dst_f, routes, routes_old, pairs, pairChannels,
                        linkSignals, listchannels):
    "Re-allocate the channels based on new routes"
    pairChannels_new, pairChannels_old = {}, {}
    channelcount = 0
    list = []
    nonrouted = []
    pair_to_reroute = {}
    for pair in pairs[:36]: # Iterate through the first 36 pairs which contain all possible cases of src,dst pair.
        print("pair: ", pair)
        src, dst = pair
        path = routes_old[src][dst]
        pair_to_reroute.setdefault( (src, dst), [] )
        pair_to_reroute.setdefault( (dst, src), [] )
        if {src_f, dst_f}.issubset(path): #ex: if {'r4', 'r6'}.issubset(path):
            pairChannels_old.setdefault( (src, dst), [] )
            pairChannels_old.setdefault( (dst, src), [] )
            list = tuple(pairChannels[src, dst])
            print("list pairchannels: ", list)
            for ch in list:
                # print("pairChannels[src][dst]: ", pairChannels[src, dst])
                print("old_channel to be removed: ", ch)
                if ch in pairChannels[src, dst]:
                    pairChannels[src, dst].remove( ch )
                    pairChannels[dst, src].remove( ch )
                    pairChannels_old[src, dst].append( ch )
                    pairChannels_old[dst, src].append( ch )
                #channelPairs[ch].remove((src, dst))
                for i in range(0, len(path)-1 ):
                    link = path[i], path[i+1]
                    link = canonical( link )
                    if ch in linkSignals[link]:
                        linkSignals[link].remove( ch )
                        listchannels[path[i]].remove( ch )
                if ch in listchannels[path[-1]]:
                    listchannels[path[-1]].remove( ch )
                new_ch = 1
                path_new = routes[src][dst]
                pairChannels.setdefault( (src, dst), [] )
                pairChannels.setdefault( (dst, src), [] )
                pairChannels_new.setdefault( (src, dst), [] )
                pairChannels_new.setdefault( (dst, src), [] )
                while new_ch < 73:
                    if any(new_ch in listchannels[path_new[x]] for x in range(len(path_new))):
                        new_ch +=1
                    else:
                        print("new_channel to be added: ", new_ch)
                        channelcount += 1
                        pairChannels[src, dst].append( new_ch )
                        pairChannels[dst, src].append( new_ch )
                        pairChannels_new[src, dst].append( new_ch )
                        pairChannels_new[dst, src].append( new_ch )
                        #channelPairs[ new_ch ] = ( src, dst )
                        for i in range(0, len(path_new)-1 ):
                            link = path_new[i], path_new[i+1]
                            link = canonical( link )
                            linkSignals[link].append( new_ch )
                            listchannels[path_new[i]].append( new_ch )
                        listchannels[path_new[-1]].append( new_ch )
                        new_ch = 80 #random number >73
                        #print("listchannels: ", listchannels)
                        #print("linkSignals: ", linkSignals)
                if new_ch != 80: #channel cannot be re-routed
                    if pair_to_reroute[src, dst]:
                        pair_to_reroute[src, dst][0] += 1
                    else:
                        pair_to_reroute[src, dst].append(1)
                    #print("pair_to_reroute: ", pair_to_reroute)
                    if pair not in nonrouted:
                        nonrouted.append(pair)
    print("non routed pairs: ", nonrouted)
    return (pairs, pairChannels, linkSignals, channelcount, listchannels, pairChannels_new, pairChannels_old,
            nonrouted, pair_to_reroute)

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

# Not used
def entriesToReroute( paths, badlink ):
    "Return list of entries in paths containing badlink"
    pair1, pair2 = list( pair ), list( reversed( pair ) )
    result = []
    for entry, paths in paths.items():
        for i in range( len( path ) - 1):
            if path[i:i+2] == pair:
                paths.append( path )
                break

# Not used
def reroute( net, failures):
    "Reroute failures"
    print( 'failures:', failures)


### Endpoint configuration


def configureTerminals( net, power=0.0):
    "Configure terminals statically: ethN <-> wdmM:channel"
    print("*** Configuring terminals")
    count = len( net.terminals )
    proxies = { terminal: TerminalProxy(terminal) for terminal in net.terminals }
    for i, terminal in enumerate( net.terminals ):
        termProxy = proxies[ terminal ]
        # XXX Hacky - should implement port info and use that
        ethPorts = sorted( int(port) for port, intf in net.ports[ terminal ].items()
                           if 'eth' in intf )
        wdmPorts = sorted( int(port) for port, intf in net.ports[ terminal ].items()
                           if 'wdm' in intf )
        channels = sum( net.remoteChannels[ i + 1 ], [] )
        print(termProxy)
        for ethPort, wdmPort, channel in zip(ethPorts, wdmPorts, channels):
            termProxy.connect( ethPort=ethPort, wdmPort=wdmPort,
                               channel=channel, power=power )
    print("*** Turning on terminals")
    for terminal in net.terminals:
        print(proxies[terminal])
        proxies[terminal].turn_on()


# Debug version of configureTerminal with consistent pairs
# FIXME: Terminal/pp will be configured with both wavelengths and pp configuration later should override the rule.
def configureTerminalsbis( net, power=0.0):
    "Configure terminals statically: ethN <-> wdmM:channel"
    print("*** Configuring terminals")
    count = len( net.terminals )
    proxies = { terminal: TerminalProxy(terminal) for terminal in net.terminals }
    for i, terminal in enumerate( net.terminals ):
        termProxy = proxies[ terminal ]
        # XXX Hacky - should implement port info and use that
        ethPorts = sorted( int(port) for port, intf in net.ports[ terminal ].items()
                           if 'eth' in intf )
        wdmPorts = sorted( int(port) for port, intf in net.ports[ terminal ].items()
                           if 'wdm' in intf )
        print("ethPorts= ", ethPorts)
        print("wdmPorts= ", wdmPorts)
        channels = sum( net.remoteChannels[ i + 1 ], [] )
        print("channels= ", channels)
        print(termProxy)
        for ethPort, wdmPort, channel in zip(ethPorts, wdmPorts, channels):
            if terminal == 't3' and channel in [27, 56, 37, 70, 41, 63]:
                print("for packetponder")
            else:
                termProxy.connect( ethPort=ethPort, wdmPort=wdmPort,
                                   channel=channel, power=power )

def turnonterm( net ):
    print("*** Turning on terminals")
    proxies = { terminal: TerminalProxy(terminal) for terminal in net.terminals }
    for terminal in net.terminals:
        print(proxies[terminal])
        proxies[terminal].turn_on()


def configurePP(net, pprules, power=0.0):
    "Configure terminals statically: ethN <-> wdmM:channel"
    print("*** Configuring packetponders")
    count = len( net.terminals )
    wdmportpp = []
    proxies = { terminal: TerminalProxy(terminal) for terminal in net.terminals }
    for i, t in enumerate( net.terminals ):
        if t in pprules and pprules[t]:
            termProxy = proxies[ t ]
            wdmPorts = sorted( int(port) for port, intf in net.ports[ t ].items()
                               if 'wdm' in intf )
            channels = sum( net.remoteChannels[ i + 1 ], [] )
            print("channels remotechannels", channels)
            for l in range(0, len(pprules[t])-1, 2): #two by two: both channels to be configured at the PP
                wdmportpp.clear()
                for j in range(len(channels)):
                    if channels[j] == pprules[t][l]:
                        channel1 = pprules[t][l]
                        wdmportpp.append(wdmPorts[j])
                for k in range(len(channels)): #order matters
                    if channels[k] == pprules[t][l+1]:
                        channel2 = pprules[t][l+1]
                        wdmportpp.append(wdmPorts[k])
                print("wdmportpp: ", wdmportpp)
                print("packetponder connect wdm port 1: ", wdmportpp[0], " and wdm port 2: ", wdmportpp[1])
                print(termProxy)
                termProxy.connect( wdmInPort=wdmportpp[0], wdmPort=wdmportpp[1], inChannel=channel1, channel=channel2)


def configurePacketSwitches( net, remoteChannels_newpath ):
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
        # XXX This is more painful and complicated than it should be,
        # and it relies on a priori knowledge of the topology...
        # Find local port
        ethports = sorted( int(port) for port, intf in net.ports[ router ].items()
                           if 'eth' in intf )
        localport = ethports[ -1 ]
        # Only route one channel for now
        ports = channelPorts( router, net )
        random = list(ports.keys())[0]
        remoteChannels_port = [ channels[0] if channels else random for channels in remoteChannels_newpath[ pop ]]
        print("remotesChannels in s: ", remoteChannels_port)
        remotes = [ p for p in range( 1, count+1 ) if p != pop ]
        print("channelPorts de router: ", ports, "for router ", router)
        outports = { pop:ports[ channel ]
                     for pop, channel in zip( remotes, remoteChannels_port ) }
        outports[ pop ] = localport
        for j in range( count ):
            destpop = j+1
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
            ports1 = channelPorts( node1, net )
            for channel in channels:
                ROADMProxy( roadm ).connect( ports1[channel], port2, [channel] )
        elif i == len(path) - 2:
            ports2 = channelPorts( node2, net )
            for channel in channels:
                ROADMProxy( roadm ).connect( port1, ports2[channel], [channel] )
        # For roadm nodes, forward the channels en masse
        else:
            ROADMProxy( roadm ).connect( port1, port2, channels )

def removePath( path, channels, net, neighbors_old, remoteChannels_old):
    print("*** Removing path", path, "channels", channels)
    # Remove ROADM rules
    for i in range(1, len(path) - 1 ):
        node1, roadm, node2 = path[i-1], path[i], path[i+1]
        print("node1, roadm, node2: ", node1, roadm, node2)
        print("neighbors_old :", neighbors_old)
        # This is a bit tricky. neighbors[node1] is a
        # dict of src:srcport, dst:dstport, so we
        # need to extract the dstport!!
        port1 = neighbors_old[ node1 ][ roadm ]
        port2 = neighbors_old[ node2 ][ roadm ]
        # For terminal nodes, use the proper channel port(s)
        if i == 1:
            ports1 = channelPorts_old( node1, net, remoteChannels_old )
            print("ports1: ", ports1)
            for channel in channels:
                ROADMProxy( roadm ).connect( ports1[channel], port2, [channel], 'remove' )
        elif i == len(path) - 2:
            ports2 = channelPorts_old( node2, net, remoteChannels_old )
            for channel in channels:
                ROADMProxy( roadm ).connect( port1, ports2[channel], [channel], 'remove' )
        # For roadm nodes, forward the channels en masse
        else:
            ROADMProxy( roadm ).connect( port1, port2, channels, 'remove' )


def channelPorts( node, net ):
    "Return the {router, terminal, roadm} ports for node/channels"
    pop = net.pops[ node ]
    # FIXME: shouldn't recompute this every time
    # Note that this channelPort is the same on the router,
    # terminal, and roadm and can be used for all of them
    channelPorts = { channel: port for port, channel
                     in enumerate( sum(net.remoteChannels[pop], []), start=1) }
    #print("channelPorts: ", channelPorts)
    return channelPorts

def channelPorts_old( node, net, remoteChannels_old ): #Only used in removed path: FIXME
    "Return the {router, terminal, roadm} ports for node/channels"
    pop = net.pops[ node ]
    # FIXME: shouldn't recompute this every time
    # Note that this channelPort is the same on the router,
    # terminal, and roadm and can be used for all of them
    channelPorts_old = { channel: port for port, channel
                     in enumerate( sum(remoteChannels_old[pop], []), start=1) }
    return channelPorts_old

def installRoutes( net ):
    print( '*** Configuring ROADMs' )
    for src, dst in net.pairs[:36]:
        path = net.routes[src][dst]
        channels = net.pairChannels[ src, dst ]
        installPath( path, channels, net )

def installnewRoutes(net):
    print( '*** Reset everything first')
    proxies_t = { terminal: TerminalProxy(terminal) for terminal in net.terminals }
    proxies_r = { roadm: ROADMProxy(roadm) for roadm in net.roadms }
    for terminal in net.terminals:
        print(proxies_t[terminal])
        proxies_t[terminal].reset()
    for roadm in net.roadms:
        print(proxies_r[roadm])
        proxies_r[roadm].reset()
    # FIXME: trying to remove only failed channels and add new to be added.
    # FIXME: loop issue in simulator. Channel not removed everywhere.
    # print( '*** Remove rules ROADMs')
    # for src, dst in net.pairs[:36]:
    #     if (src, dst) in net.pairChannels_old and net.pairChannels_old[src, dst]:
    #         path = net.routes_old[src][dst]
    #         channels = net.pairChannels_old[ src, dst ]
    #         removePath( path, channels, net, neighbors_old, remoteChannels_old )
    # print( '*** Configuring new ROADMs' )
    # for src, dst in net.pairs[:36]:
    #     if (src, dst) in net.pairChannels_new and net.pairChannels_new[src, dst]:
    #         path = net.routes[src][dst]
    #         channels = net.pairChannels_new[ src, dst ]
    #         installPath( path, channels, net )
    print( '*** Configuring ROADMs' )
    for src, dst in net.pairs[:36]:
        path = net.routes[src][dst]
        channels = net.pairChannels[ src, dst ]
        installPath( path, channels, net )

def installnewroutewavechange( net , pairChannels_justnew):
    print( '*** Configuring new ROADMs' )
    list=[]
    for pair in pairChannels_justnew.keys(): #pairs are the subpairs ones.
        src, dst = pair
        path = net.routes[src][dst]
        channels = pairChannels_justnew[ src, dst ]
        installPath( path, channels, net )
        print("Finito installing new rules")
        net.remoteChannels = computeRemoteChannels(net)
        if src not in list:
            list.append(src)
        if dst not in list:
            list.append(dst)
    configureTerminalsbis(net, power=0.0 ) #configureTerminalsReroute
    proxies = { terminal: TerminalProxy(terminal) for terminal in net.terminals }
    for s in list:
        print("*** Turning on terminals")
        print(proxies[s])
        proxies[s].turn_on()
        # configureTerminalsbis(net, dst, power=0.0 ) #configureTerminalsReroute
        # TerminalProxy( path[-1] ).turn_on()


def emptyspectrum( linkSignals, listchannels ):
    missing = defaultdict( list )
    misslistchannels = {}
    for link in sorted( linkSignals ):
        missing[link] = [i for i in range(1, 72) if i not in linkSignals[link]]
    for i in listchannels.keys():  # Iterate over each key in listchannels
        misslistchannels[i] = [j for j in range(1, 72) if j not in listchannels[i]] #72
    return(missing, misslistchannels)

def countSignals_bis( linkSignals ):
    print("*** Link signals:")
    for link in sorted( linkSignals ):
        print( link, linkSignals[link] )

    # Compute average signal count
    signalCount = sum( len(clist) for clist in linkSignals.values() )
    avgCount = signalCount / len( linkSignals )
    print("Average signal count = %.2f" % avgCount )
    maximum = max( len(clist) for clist in linkSignals.values() )
    print("Maximum = %.2f" % maximum )

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

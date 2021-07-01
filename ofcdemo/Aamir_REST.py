
from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR, ListenPortBase )
from collections import defaultdict

class Mininet_Control_Rest(object):
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

    def installPath(self, path, channels):
        "Program a lightpath into the network"
        # Install ROADM rules
        for i in range(1, len(path) - 1 ):
            node1, roadm, node2 = path[i-1], path[i], path[i+1]
            port1 = self.net.graph[ node1 ][ roadm ]
            port2 = self.net.graph[ node2 ][ roadm ]
            print(f"segment {i}: {node1}-[{port1}]->{roadm}-[{port2}]->{node2}")
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

def test():
    control = Mininet_Control_Rest()
    net = control.net
    src_id, dst_id = 1, 4
    src, dst = net.terminals[src_id - 1], net.terminals[dst_id - 1]
    path = net.routes[src][dst]
    channel = 12
    control.installPath(path, [channel])
    for node in net.graph:
        print(node, net.graph[node])
test()
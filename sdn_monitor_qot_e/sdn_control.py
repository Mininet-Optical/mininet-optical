from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy,
                                    fetchNodes, fetchLinks, fetchPorts)
from collections import defaultdict


def run(net, N=3):
    "Configure and monitor network with N=3 channels for each path"

    # Fetch nodes
    net.allNodes = fetchNodes(net)
    net.switches = sorted(node for node, cls in net.allNodes.items()
                          if cls == 'OVSSwitch')
    net.terminals = sorted(node for node, cls in net.allNodes.items()
                           if cls == 'Terminal')
    net.roadms = sorted(node for node, cls in net.allNodes.items()
                        if cls == 'ROADM')
    net.nodes = net.terminals + net.roadms

    # Assign POPs for convenience
    count = len(net.switches)
    net.pops = {node: i + 1
                for i in range(count)
                for node in (net.switches[i], net.terminals[i], net.roadms[i])}

    # Fetch links
    net.allLinks, net.roadmLinks, net.terminalLinks = fetchLinks(net)

    # Create adjacency dict
    net.neighbors = adjacencyDict(net.allLinks)

    # Fetch ports
    net.ports = fetchPorts(net, net.roadms + net.terminals + net.switches)

    # Calculate inter-pop routes
    net.routes = {node: route(node, net.neighbors, net.terminals)
                  for node in net.terminals}

    install_paths(net.roadms, 10)


def adjacencyDict(links):
    "Return an adjacency dict for links"
    # Note we only have to worry about single links between nodes
    # We handle the terminals separately
    neighbors = defaultdict(defaultdict)
    for link in links:
        src, dst = link  # link is a dict but order doesn't matter
        srcport, dstport = link[src], link[dst]
        neighbors.setdefault(src, {})
        neighbors[src][dst] = dstport
        neighbors[dst][src] = srcport
    return dict(neighbors)


def route(src, neighbors, destinations):
    """Route from src to destinations
       neighbors: adjacency list
       returns: routes dict"""
    routes, seen, paths = {}, set((src,)), [(src,)]
    while paths:
        path = paths.pop(0)
        lastNode = path[-1]
        for neighbor in neighbors[lastNode]:
            if neighbor not in seen:
                newPath = (path + (neighbor,))
                paths.append(newPath)
                if neighbor in destinations:
                    routes[neighbor] = newPath
                seen.add(neighbor)
    return routes


def install_paths(roadms, channels):
    # Configure roadms
    r1, r2, r3, r4, r5 = roadms[0], roadms[1], roadms[2], roadms[3], roadms[4]
    line1, line2 = 11, 12

    # r1: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy(r1).connect(port1=local_port, port2=line1, channels=[ch])

    # # r2: pass through channels r1<->r5
    # r2.connect(port1=line1, port2=line2, channels=channels)
    #
    # # r3: pass through channels r1<->r5
    # r3.connect(port1=line1, port2=line2, channels=channels)
    #
    # # r4: pass through channels r1<->r5
    # r4.connect(port1=line1, port2=line2, channels=channels)
    #
    # # r5: add/drop channels r1<->r5
    # for local_port, ch in enumerate(channels, start=1):
    #     r5.connect(port1=line1, port2=local_port, channels=[ch])


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy, OFSwitchProxy,
                                    fetchNodes, fetchLinks, fetchPorts)
from collections import defaultdict
import numpy as np


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

    # Fetch ports
    net.ports = fetchPorts(net, net.roadms + net.terminals + net.switches)

    install_paths(net.roadms, 10)

    configure_routers(net.switches)


def install_paths(roadms, channel_no):
    channels = list(np.arange(1, channel_no + 1))
    # Configure roadms
    r1, r2, r3, r4, r5 = roadms[0], roadms[1], roadms[2], roadms[3], roadms[4]
    line1, line2 = 11, 12

    # r1: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy(r1).connect(port1=local_port, port2=line1, channels=[ch])

    # r2: pass through channels r1<->r5
    ROADMProxy(r2).connect(port1=line1, port2=line2, channels=channels)

    # r3: pass through channels r1<->r5
    ROADMProxy(r3).connect(port1=line1, port2=line2, channels=channels)

    # r4: pass through channels r1<->r5
    ROADMProxy(r4).connect(port1=line1, port2=line2, channels=channels)

    # r5: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy(r5).connect(port1=line1, port2=local_port, channels=[ch])


def configure_routers(routers):
    "Configure Open vSwitch 'routers' using OpenFlow"

    print("*** Configuring Open vSwitch 'routers' remotely... ")

    routers = s1, s5 = routers[0], routers[4]
    for pop, dests in enumerate([(s1, s5)], start=1):
        router, dest1, dest2 = routers[pop - 1], dests[0], dests[1]
        routerProxy = OFSwitchProxy(router)
        # Initialize flow table
        print('Configuring', router, 'at', routerProxy.remote, 'via OpenFlow...')
        routerProxy.dpctl('del-flows')
        # XXX Only one host for now
        hostmac = net.get('h%d' % pop).MAC()
        for eth, dest in enumerate([dest1, dest2, router], start=1):
            dstmod = ('mod_dl_dst=%s,' % hostmac) if dest == router else ''
            for protocol in 'ip', 'icmp', 'arp':
                flow = (protocol + ',ip_dst=' + dest.params['subnet'] +
                        'actions=' + dstmod +
                        'dec_ttl,output:%d' % eth)
                routerProxy.dpctl('add-flow', flow)


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

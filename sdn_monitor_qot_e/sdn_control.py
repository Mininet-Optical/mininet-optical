from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy, OFSwitchProxy, TerminalProxy,
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

    channel_no = 10
    install_paths(net.roadms, channel_no)

    configure_routers(net.switches)

    configure_terminals(net.terminals, channel_no)


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

    def subnet(pop):
        return '10.%d.0.0/24' % pop

    print("*** Configuring Open vSwitch 'routers' remotely... ")

    routers = s1, s5 = routers[0], routers[4]
    for pop, dests in enumerate([(s1, s5)], start=1):
        router, dest1, dest2 = routers[pop - 1], dests[0], dests[1]
        routerProxy = OFSwitchProxy(router)
        # Initialize flow table
        print('Configuring', router, 'at', routerProxy.remote, 'via OpenFlow...')
        routerProxy.dpctl('del-flows')
        # XXX Only one host for now
        j = 1
        for eth, dest in enumerate([dest1, dest2, router], start=1):
            for protocol in 'ip', 'icmp', 'arp':
                flow = (protocol + ',ip_dst=' + subnet(j) +
                        ',actions=dec_ttl,output:%d' % eth)
                routerProxy.dpctl('add-flow', flow)
                j += 1


def configure_terminals(terminals, channel_no):
    channels = list(np.arange(1, channel_no + 1))
    # Port numbering
    eth_ports = list(np.arange(1, channel_no + 2))
    wdm_ports = list(np.arange(channel_no + 1, channel_no * 2 + 1))

    # Configure transceivers
    t1, t5 = net.get('t1', 't5')
    termProxy1 = TerminalProxy(t1)
    termProxy5 = TerminalProxy(t5)
    for tx_id, ch in enumerate(channels):
        termProxy1.connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)
    for tx_id, ch in enumerate(channels):
        termProxy5.connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

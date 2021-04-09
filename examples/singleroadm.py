#!/usr/bin/env python3

"""
singleroadm.py:

Simple optical network with three terminals connected to a
single ROADM in a "Y" topology. H1 can talk to either H2
or H3, depending on how the ROADM is configured.

"""

from dataplane import (Terminal, ROADM, OpticalLink,
                       OpticalNet as Mininet, km, m, dB, dBm)
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.log import setLogLevel, warning
from mininet.clean import cleanup

class SingleROADMTopo(Topo):
    """
    h1 - s1 - t1 -- r1 -- t2 - s2 - h2
                    |
                    t3 - s3 - h3

    Note that t1--r1 and r2--t2 are 50km spans:
    (boost->,amp2<-) --25km-- amp1 --25km-- (amp2->,boost<-)
    """
    def build(self):
        "Build single ROADM topology"
        # Packet network elements
        hosts = [self.addHost(h) for h in ('h1', 'h2', 'h3')]
        switches = [self.addSwitch(s)
                    for s in ('s1', 's2', 's3')]
        t1, t2, t3 = terminals = [
            self.addSwitch(
                t, cls=Terminal, transceivers=[('tx1',0*dBm,'C')],
                monitor_mode='in')
            for t in ('t1', 't2', 't3')]
        r1 = self.addSwitch('r1', cls=ROADM)
        # Ethernet links
        for h, s, t in zip(hosts, switches, terminals):
            self.addLink(h, s)
            self.addLink(s, t, port2=1)
        # WDM links
        boost = ('boost', {'target_gain': 3.0*dB})
        amp1 = ('amp1', {'target_gain': 25*.22*dB})
        amp2 = ('amp2', {'target_gain': 25*.22*dB})
        spans = [25*km, amp1, 25*km, amp2]
        self.addLink(r1, t1, cls=OpticalLink, port1=1, port2=2,
                     boost1=boost, spans=spans)
        self.addLink(r1, t2, cls=OpticalLink, port1=2, port2=2,
                     boost1=boost, spans=spans)
        self.addLink(r1, t3, cls=OpticalLink, port1=3, port2=2,
                     spans=[1.0*m])


# Debugging: Plot network graph
def plotNet(net, outfile="singleroadm.png"):
    "Plot network graph to outfile"
    try:
        import pygraphviz as pgv
    except:
        warning('*** Please install python3-pygraphviz for plotting\n')
        return
    color = {ROADM: 'red', Terminal: 'blue', OVSBridge: 'orange',
             Host: 'black'}
    colors = {node: color.get(type(node), 'black')
              for node in net.values()}
    nfont = {'fontname': 'helvetica bold', 'penwidth': 3}
    g = pgv.AGraph(strict=False, directed=False, layout='circo')
    for node in net.switches:
        g.add_node(node.name, color=colors[node], **nfont)
    for node in net.hosts:
        g.add_node(node.name, color=colors[node], **nfont, shape='box')
    for link in net.links:
        intf1, intf2 = link.intf1, link.intf2
        node1, node2 = intf1.node, intf2.node
        port1, port2 = node1.ports[intf1], node2.ports[intf2]
        g.add_edge(node1.name, node2.name,
                   headlabel=f' {node2}:{port2} ',
                   taillabel=f' {node1}:{port1} ',
                   labelfontsize=10, labelfontname='helvetica bold',
                   penwidth=2)
    print("*** Plotting network topology to", outfile)
    g.layout()
    g.draw(outfile)


if __name__ == '__main__':

    cleanup()
    setLogLevel('info')

    topo = SingleROADMTopo()
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    restServer = RestServer(net)

    net.start()
    restServer.start()
    plotNet(net)
    CLI(net)
    restServer.stop()
    net.stop()

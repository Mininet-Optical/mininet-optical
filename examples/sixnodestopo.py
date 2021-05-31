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

from visualize_topo import visualize_topology

import numpy as np

class SixROADMTopo(Topo):
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
        hosts = [self.addHost(h) for h in ('BBU1', 'RRU1', 'RRU2', 'BBU2', 'RRU3', 'RRU4')]
        switches = [self.addSwitch(s)
                    for s in ('s1', 's2', 's3', 's4', 's5', 's6')]
        ran = np.arange(1, 7)
        tr_labels = ['tx%s' % str(x) for x in ran]
        transceivers = [(tr, 0*dBm, 'C') for tr in tr_labels]
        t1, t2, t3, t4, t5, t6 = terminals = [
            self.addSwitch(
                t, cls=Terminal, transceivers=transceivers,
                monitor_mode='in')
            for t in ('t1', 't2', 't3', 't4', 't5', 't6')]
        r1, r2, r3, r4, r5, r6 = roadms = [self.addSwitch(r, cls=ROADM, monitor_mode='out') for r in ('r1', 'r2', 'r3', 'r4', 'r5', 'r6')]

        # Ethernet links
        for h, s, t in zip(hosts, switches, terminals):
            self.addLink(h, s, port1=0, port2=10)
            self.addLink(s, t, port1=1, port2=1) #this add veth link
            self.addLink(s, t, port1=2, port2=2)
            self.addLink(s, t, port1=3, port2=3)
            self.addLink(s, t, port1=4, port2=4)
            self.addLink(s, t, port1=5, port2=5)
            self.addLink(s, t, port1=6, port2=6)
        # WDM links
        boost = ('boost', {'target_gain': 3.0*dB})
        amp1 = ('amp1', {'target_gain': 25*.22*dB})
        amp2 = ('amp2', {'target_gain': 25*.22*dB})
        spans = [15*km, amp1, 15*km, amp2]
        #links between Roadms and Terminals
        for r, t in zip(roadms, terminals):
            self.addLink(r, t, cls=OpticalLink, port1=1, port2=11, spans=spans) #this add optical link #boost1=boost,
            self.addLink(r, t, cls=OpticalLink, port1=2, port2=12, spans=spans) #boost1=boost,
            self.addLink(r, t, cls=OpticalLink, port1=3, port2=13, spans=spans)
            self.addLink(r, t, cls=OpticalLink, port1=4, port2=14, spans=spans)
            self.addLink(r, t, cls=OpticalLink, port1=5, port2=15, spans=spans)
            self.addLink(r, t, cls=OpticalLink, port1=6, port2=16, spans=spans)

        self.addLink(r1, r2, cls=OpticalLink, port1=222, port2=111, boost1=boost, spans=spans)
        self.addLink(r2, r3, cls=OpticalLink, port1=222, port2=111, boost1=boost, spans=spans)
        self.addLink(r3, r4, cls=OpticalLink, port1=222, port2=111, boost1=boost, spans=spans)
        self.addLink(r4, r5, cls=OpticalLink, port1=222, port2=111, boost1=boost, spans=spans)
        self.addLink(r5, r6, cls=OpticalLink, port1=222, port2=111, boost1=boost, spans=spans)
        self.addLink(r6, r1, cls=OpticalLink, port1=222, port2=111, boost1=boost, spans=spans)

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

    topo = SixROADMTopo()
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    restServer = RestServer(net)

    net.start()
    restServer.start()
    #visualize_topology(net)
    plotNet(net)
    CLI(net)
    restServer.stop()
    net.stop()

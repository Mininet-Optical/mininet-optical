#!/usr/bin/env python3

"""
sixNodeRingTopology.py:

Simple optical network with three terminals connected to a
single ROADM in a "Y" topology. H1 can talk to either H2
or H3, depending on how the ROADM is configured.

"""

from dataplane import (Terminal, ROADM, OpticalLink, UnidirectionalOpticalLink as ULink,
                       OpticalNet as Mininet, km, m, dB, dBm)
from examples.config_sixNodeRingTopology import six_node_topo_controller
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.log import setLogLevel, warning
from mininet.clean import cleanup
from mno.examples.singleroadm import plotNet

class sixNodeRingTopology(Topo):
    """

    Note that t1--r1 and r2--t2 are 50km spans:
    (boost->,amp2<-) --25km-- amp1 --25km-- (amp2->,boost<-)
    """
    def build(self):
        "Build sixNodeRing ROADM topology"
        # Packet network elements

        numNodes = 6
        num = 6
        hosts = []
        switches = []
        terminals = []
        roadms = []
        for count in range(0,numNodes):
            if(count < numNodes/2):
                h = 'RU' + str(count)
            else:
                h = 'BBU' + str(count - int(numNodes/2))
            hosts.append(self.addHost(h))
            s = 's' + str(count)
            switches.append(self.addSwitch(s))
            t = 't' + str(count)

            transceiversList = []
            for transceiverCount in range(0,num):
                transceiverName = 'tx' + str(transceiverCount)
                transceiversList.append((transceiverName,0*dBm,'C'))
            terminals.append(self.addSwitch(
                   t, cls=Terminal, transceivers=transceiversList,
                    monitor_mode='in'))
            r = 'r' + str(count)
            roadms.append(self.addSwitch(r, cls=ROADM))


        # Ethernet links
        for h, s, t in zip(hosts, switches, terminals):
            self.addLink(h, s, port1 = 100, port2 = 100)
            for portCount in range(0,num):
                self.addLink(s, t, port1 = portCount + 1, port2= portCount + 1)

        # WDM links
        boost = ('boost', {'target_gain': 3.0*dB})
        amp1 = ('amp1', {'target_gain': 5*.22*dB})
        amp2 = ('amp2', {'target_gain': 5*.22*dB})
        spans = [5*km, amp1, 5*km, amp2]

        for r, t in zip(roadms, terminals):
            for portCount in range(0, num):
                self.addLink(r, t, cls=OpticalLink, port1= portCount + 1, port2 = num + portCount + 1,
                         boost1=boost, spans=[1.0*m])
        i = 0
        for r1 in roadms:
            if(i == len(roadms)-1):
                r2 = roadms[0]
            else:
                r2 = roadms[i + 1]

            ###################For Bidirectional Links########################################
            self.addLink(r1, r2, cls=OpticalLink, port1 = 100, port2= 101,
                    boost1=boost, spans=spans)
            ###################For Bidirectional Links########################################

            ###################For unidirectional Links########################################
            # self.addLink(r1, r2, cls=ULink, port1=100, port2=101,
            #              boost1=boost, spans=spans)
            #
            # if (i == 0):
            #     r2 = roadms[len(roadms) - 1]
            # else:
            #     r2 = roadms[i - 1]
            #
            # self.addLink(r1, r2, cls=ULink, port1=102, port2=103,
            #              boost1=boost, spans=spans)
            # ###################For unidirectional Links########################################

            i = i + 1

# Debugging: Plot network graph
def plotNet(net, outfile="sixNodeRingTopology_v1.png", directed=False,):
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
    g = pgv.AGraph(strict=False, directed=directed, layout='circo')
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

    topo = sixNodeRingTopology()
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    restServer = RestServer(net)

    net.start()
    restServer.start()
    plotNet(net,  directed=False)
    six_node_topo_controller()
    CLI(net)
    restServer.stop()
    net.stop()

#!/usr/bin/env python3

from mnoptical.node import Transceiver, Amplifier, Attenuator
from mnoptical.dataplane import (Terminal, ROADM, OpticalLink,
                       OpticalNet as Mininet, km, m, dB, dBm)
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.log import setLogLevel, warning, info
from mininet.clean import cleanup

from os.path import dirname, realpath, join
from subprocess import run
import sys

from mnoptical.units import abs_to_db

# Debugging: Plot network graph
def plotNet(net, outfile="img.png", directed=False, layout='circo',
            colorMap=None):
    "Plot network graph to outfile"
    try:
        import pygraphviz as pgv
    except:
        warning('*** Please install python3-pygraphviz for plotting\n')
        return
    color = {ROADM: 'red', Terminal: 'blue', OVSBridge: 'orange',
             Host: 'black'}
    if colorMap:
        color.update(colorMap)
    colors = {node: color.get(type(node), 'black')
              for node in net.values()}
    nfont = {'fontname': 'helvetica bold', 'penwidth': 3}
    g = pgv.AGraph(strict=False, directed=directed, layout=layout)
    roadms = [node for node in net.switches if isinstance(node, ROADM)]
    terms = [node for node in net.switches if isinstance(node, Terminal)]
    other = [node for node in net.switches if node not in set(roadms+terms)]
    for node in roadms + terms + other:
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

def add_amp(node_name=None, type=None,
    gain_dB=None, monitor_mode='out'):
    """
    Create an Amplifier object to add to a ROADM node
    :param node_name: string
    :param type: string ('boost' or 'preamp'
    :param gain_dB: int or float
    """
    label = '%s-%s' % (node_name, type)
    if type == 'preamp':
        return Amplifier(name=label,
                         target_gain=float(gain_dB),
                         preamp=True,
                         monitor_mode=monitor_mode)
    else:
        return Amplifier(name=label,
                         target_gain=float(gain_dB),
                         boost=True,
                         monitor_mode=monitor_mode)

LINEIN, LINEOUT = 5101, 4201
ADD, DROP = 4100, 5200

class MultiROADMTopo(Topo):

    def build(self, operational_power=0*dB):

        h1, h2 = hosts = [self.addHost(h) for h in ('h1', 'h2')]

        t1 = self.addSwitch("t1", cls=Terminal,
                            transceivers=[Transceiver(id, str('tr1-%s')%str(id),
                                operation_power=int(operational_power)) 
                            for id in range(1,4)],
                            monitor_mode='out')

        t2 = self.addSwitch("t2", cls=Terminal,
                            transceivers=[Transceiver(id, str('tr2-%s')%str(id),
                                operation_power=int(operational_power)) 
                            for id in range(1,4)],
                            monitor_mode='in')
        terminals = (t1, t2)

        r1 = self.addSwitch('r1', cls=ROADM, monitor_mode='out')
        r2 = self.addSwitch('r2', cls=ROADM, monitor_mode='in')
        roadms = (r1, r2)

        self.addLink(h1, t1, port1=0, port2=100)
        self.addLink(h2, t2, port1=0, port2=100)

        for i in range(1,4):
            self.addLink(t1, r1, cls=OpticalLink,
                    port1=i, port2=i, spans=[1*m])
            self.addLink(r2, t2, cls=OpticalLink,
                    port1=i, port2=i, spans=[1*m])


        amp1 = ('boost', {'target_gain': 17.0*dB,
                        'monitor_mode': 'out'})
        amp2 = ('preamp', {'target_gain': 17.6*dB,
                        'monitor_mode': 'out'})
        attn = (Attenuator, 'attn', 1)
        spans = [0, amp1, 100, amp2, 0, attn, 100]
        self.addLink(r1, r2, cls=OpticalLink,
            port1=10, port2=10, spans=spans)

    def get_monitor_power(self, monitor, monitor_mode='in'):

        monitor = net[monitor].model
        monitor.modify_mode(monitor_mode)
        power_dict = list(monitor.get_dict_power().values())
        power_list = [abs_to_db(i) for i in power_dict.values()]
        return power_list

    def configNet(self, net):

        info('*** Configuring network... \n')

        net['r1'].reset()
        net['r2'].reset()

        net['t1'].connect(ethPort=100, wdmPort=1, channel=1)
        net['t2'].connect(ethPort=100, wdmPort=1, channel=1)

        net['r1'].connect(1,10,channels=[1])
        net['r2'].connect(10,1,channels=[1])

        net['t1'].turn_on()
        net['t2'].turn_on()

def test(net):

    def get_monitor_power(monitor, monitor_mode='in'):

        monitor = net[monitor].model
        monitor.modify_mode(mode=monitor_mode)
        power_list = [abs_to_db(i) for i in monitor.get_dict_power().values()]
        
        return power_list
 
    input_power = get_monitor_power('r1-r2-preamp-monitor', 'out')[0]
    output_power = get_monitor_power('r1-r2-attn-monitor', 'out')[0]

    assert net.pingAll() == 0.0
    assert (input_power-output_power) == 1.0

if __name__ == '__main__':

    cleanup()
    setLogLevel('info')

    topo = MultiROADMTopo(2*dB)
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    restServer = RestServer(net)
    net.start()
    restServer.start()
    net.topo.configNet(net)
    
    test(net) if "test" in sys.argv else CLI(net)

    net.stop()
    restServer.stop()

#!/usr/bin/env python

"""
uniroadmchain.py: chain of unidirectional ROADMS without
                  intermediate terminals

This is mainly a test case rather than something that
is actually useful, although signals can be monitored at
the intermediate ROADMs.
"""

from mnoptical.dataplane import ( OpticalLink,
                        UnidirectionalOpticalLink as ULink,
                        ROADM, Terminal,
                        OpticalNet as Mininet,
                        km, m, dB, dBm )

from mnoptical.ofcdemo.demolib import OpticalCLI, cleanup
from mnoptical.examples.singleroadm import plotNet

from mininet.topo import Topo
from mininet.link import Link
from mininet.nodelib import LinuxBridge
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

from sys import argv

class UniRoadmChain(Topo):
    """Two chains of unidirectional ROADMs linking two terminals
       h1 <-> t1 -> re1 ... reN -> t2 <-> h2
                 <- rwN ... rw1 <- t2
    """

    def build(self, power=0*dBm, roadmCount=3):
        "Build simple unidirectional ROADM chain"
        self.roadmCount = roadmCount
        # Node config
        transceivers = tuple((f'tx{ch}', power, 'C')
                             for ch in range(1, roadmCount+1))
        topts = {'cls': Terminal, 'transceivers': transceivers,
                 'monitor_mode': 'in' }
        ropts = {'cls': ROADM, 'monitor_mode': 'in',
                 # { 'wss_dict': {ch:(7.0,None) for ch in range(1,91)}
                 }
        # Nodes
        self.addHost('h1')
        self.addHost('h2')
        self.addSwitch('t1', **topts)
        self.addSwitch('t2', **topts)
        for i in range(1, roadmCount+1):
            self.addSwitch(f're{i}', **ropts)
            self.addSwitch(f'rw{i}', **ropts)
        # Packet links
        hostport = 1
        self.addLink('h1', 't1', port1=hostport, port2=hostport)
        self.addLink('h2', 't2', port1=hostport, port2=hostport)
        # Eastbound and Westbound optical links
        linein, lineout, uplink, downlink = 1, 2, 3, 4
        self.addLink('t1', 're1', port1=uplink, port2=linein, cls=ULink)
        self.addLink('t2', 'rw1', port1=uplink, port2=linein, cls=ULink)
        self.addLink(f'rw{roadmCount}', 't1',
                     port1=lineout, port2=downlink,
                     cls=ULink, spans=[1*m])
        self.addLink(f're{roadmCount}', 't2',
                     port1=lineout, port2=downlink,
                     cls=ULink, spans=[1*m])
        boost = ('boost', {'target_gain':3.0*dB, 'monitor_mode':'out'})
        amp1 = ('amp1', {'target_gain': 25*.22*dB, 'monitor_mode':'out'})
        for i in range(1, roadmCount):
            self.addLink(f're{i}', f're{i+1}',
                         port1=lineout, port2=linein,
                         cls=ULink, boost=boost, spans=[25*km, amp1])
            self.addLink(f'rw{i}', f'rw{i+1}',
                         port1=lineout, port2=linein,
                         cls=ULink, boost=boost, spans=[25*km])

    def configNet(self, net):
        "Configure unidirectional ROADM chain"
        info('*** Configuring network... \n')
        hostport = 1
        linein, lineout, uplink, downlink = 1, 2, 3, 4
        roadmCount = self.roadmCount
        # Terminal hostport<->(uplink,downlink)
        for i in 1, 2:
            net[f't{i}'].connect(hostport, wdmPort=uplink, channel=1,
                                 wdmInPort=downlink )
        # All ROADMs pass channel 1
        for i in range(1, roadmCount+1):
            net[f're{i}'].connect(linein, lineout, channels=[1])
            net[f'rw{i}'].connect(linein, lineout, channels=[1])
        # Power up transceivers
        info('*** Turning on transceivers... \n')
        net[f't1'].turn_on()
        net[f't2'].turn_on()

if __name__ == '__main__':

    cleanup()  # Just in case!
    setLogLevel('info')
    if len(argv) == 2 and argv[1] == 'clean': exit(0)

    topo = UniRoadmChain(roadmCount=4)
    net = Mininet(topo=topo, controller=None)
    net.start()
    info('*** UniRoadmChain Example \n')
    info(topo.__doc__, '\n')
    plotNet(net, outfile='uniroadmchain.png', directed=True)
    net.topo.configNet(net)
    if 'test' in argv:
        assert net.pingAll() == 0  # 0% loss
    else:
        OpticalCLI(net)
    net.stop()

from network import Network
from link import Span as Fiber, SpanTuple as Segment
from Simulation_API import Mininet_Optical_Simu_API
from lumentum_NETCONF_API import Lumentum_NETCONF
from node import Transceiver
from units import *
from collections import defaultdict
import random
from collections import defaultdict
import numpy as np
from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR )


from dataplane import (Terminal, ROADM, OpticalLink,
                       OpticalNet as Mininet, km, m, dB, dBm)
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.clean import cleanup

from os.path import dirname, realpath, join
from subprocess import run
from sys import argv


km = dB = dBm = 1.0
m = .001

# Parameters

NUM_WAV = 40
LINE_IN, LINE_OUT = NUM_WAV, NUM_WAV + 1
NUM_NODE = 5


def Span( km, amp=None ):
    "Return a fiber segment of length km with a compensating amp"
    return Segment( span=Fiber( length=km ), amplifier=amp )

class RoadmPhyNetwork(Topo):

    """ROADM network topo
    """
    ####################### Linear Topo #####################
    #
    #                    t2       t3       t4
    #                    |        |        |
    #      t1 - r1 ----- r2 ----- r3 ----- r4 ----- r5 - t5
    #
    #########################################################
    def build(self):
        "Build single ROADM topology"
        # Packet network elements
        #hosts = [self.addHost(h) for h in ('h1', 'h2', 'h3')]
        #switches = [self.addSwitch(s)
        #            for s in ('s1', 's2', 's3')]

        transceivers = [('tx%d' % i, 0 * dBm, 'C') for i in range(1, NUM_WAV + 1)]
        t1, t2, t3, t4, t5= terminals = [
            self.addSwitch(
                t, cls=Terminal, transceivers= transceivers,
                monitor_mode='in')
            for t in ('t1', 't2', 't3', 't4', 't5')]
        r1 = self.addSwitch('r1', cls=ROADM)
        r2 = self.addSwitch('r2', cls=ROADM)
        r3 = self.addSwitch('r3', cls=ROADM)
        r4 = self.addSwitch('r4', cls=ROADM)
        r5 = self.addSwitch('r5', cls=ROADM)

        # Ethernet links
        #for h, s, t in zip(hosts, switches, terminals):
        #    self.addLink(h, s)
        #    self.addLink(s, t, port2=1)

        # WDM links
        boost = ('boost', {'target_gain': 17.0*dB})
        amp1 = ('amp1', {'target_gain': 25*.22*dB})
        # amp2 = ('amp2', {'target_gain': 25*.22*dB})
        spans = [25*km, amp1]

        self.addLink(r1, r2, cls=OpticalLink, port1=LINE_OUT, port2=LINE_IN,
                     boost1=boost, spans=spans)
        self.addLink(r2, r3, cls=OpticalLink, port1=LINE_OUT, port2=LINE_IN,
                     boost1=boost, spans=spans)
        self.addLink(r3, r4, cls=OpticalLink, port1=LINE_OUT, port2=LINE_IN,
                     boost1=boost, spans=spans)
        self.addLink(r4, r5, cls=OpticalLink, port1=LINE_OUT, port2=LINE_IN,
                     boost1=boost, spans=spans)

        self.addLink(r1, t1, cls=OpticalLink, port1=18, port2=18,
                     spans=[1.0*m])
        self.addLink(r5, t5, cls=OpticalLink, port1=18, port2=18,
                     spans=[1.0*m])



    #----------------------------------------------------------
    # net = Network()
    # lengths = [15 * km]
    #
    # # Network nodes
    # transceivers = [('tx%d' % i, 0 * dBm, 'C') for i in range(1, NUM_WAV + 1)]
    #
    # # each terminal includes NUM_WAV transceivers
    # terminals = [
    #     net.add_lt(name, transceivers=transceivers, monitor_mode=mode)
    #     for name, mode in [('t%d' % i, 'in') for i in range(1, NUM_NODE + 1)]]
    # roadms = [
    #     net.add_roadm(name, monitor_mode=mode)
    #     for name, mode in [('r%d' % i, 'in') for i in range(1, NUM_NODE + 1)]]
    #
    # nodes = net.name_to_node
    # # Convenience alias
    # link = net.add_link
    #
    # for k in range(1, NUM_NODE):
    #     # Eastbound link consisting of a boost amplifier going into
    #     # one or more segments of fiber with compensating amplifiers
    #     boost = net.add_amplifier('boost{}{}'.format(k, k + 1), target_gain=17 * dB, boost=True)
    #     spans = []
    #     for i, length in enumerate(lengths, start=1):
    #         amp = net.add_amplifier(
    #             'amp{}{}-{}'.format(k, k + 1, i), target_gain=length * 0.22 * dB, monitor_mode='out')
    #         span = Span(length, amp=amp)
    #         spans.append(span)
    #
    #     link(nodes['r%d' % k], nodes['r%d' % (k + 1)], src_out_port=LINE_OUT, dst_in_port=LINE_IN, boost_amp=boost,
    #          spans=spans)
    #
    #     # Westbound link consisting of a boost amplifier going into
    #     # one or more segments of fiber with compensating amplifiers
    #     boost = net.add_amplifier('boost{}{}'.format(k + 1, k), target_gain=17 * dB, boost=True)
    #     spans = []
    #     for i, length in enumerate(lengths, start=1):
    #         amp = net.add_amplifier(
    #             'amp{}{}-{}'.format(k + 1, k, i), target_gain=length * 0.22 * dB, monitor_mode='out')
    #         span = Span(length, amp=amp)
    #         spans.append(span)
    #
    #     link(nodes['r%d' % (k + 1)], nodes['r%d' % k], src_out_port=LINE_IN, dst_in_port=LINE_OUT, boost_amp=boost,
    #          spans=spans)
    #
    # for k in range(1,NUM_NODE+1):
    #     # Local add/drop links between terminals/transceivers and ROADMs
    #     for add_drop_port in range(NUM_WAV):
    #         link( nodes['t%d' %k], nodes['r%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
    #         link( nodes['r%d' %k], nodes['t%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
    #
    # return net



Mininet_Agent = Mininet_Optical_Simu_API()


class Simple_Controller_REST(object):


    def Mininet_installPath(self, path, roadm_to_inport, roadm_to_outport, ruleID, channel):
        "intall switch rules on roadms along a lightpath with a signal channel"

        for i in range(len(path)):
            roadm = path[i]
            ROADMProxy(roadm).connect(roadm_to_inport[roadm], roadm_to_outport[roadm], channel)



class Simple_Controller_Simu(object):


    def installPath(self, path, roadm_to_inport, roadm_to_outport, ruleID, channel, nodes):
        "intall switch rules on roadms along a lightpath with a signal channel"

        for i in range(len(path)):
            roadm = path[i]
            inport = roadm_to_inport[roadm]
            outport = roadm_to_outport[roadm]

            Mininet_Agent.ROADM_installSwitchRule(nodes[roadm], ruleID, inport, outport, channel)


    def uninstallPath(self, path, ruleID, nodes):
        "delete switch rules on roadms along a lightpath for some signal channels"

        for i in range(len(path)):
            roadm = path[i]
            Mininet_Agent.ROADM_deleteSwitchRule(nodes[roadm], ruleID)


    def setupLightpath(self, path, roadm_to_inport, roadm_to_outport, ruleID, channel, terminal, power, nodes):
        "set up a lightpath: install switch rule and configure terminal"

        self.installPath(path, roadm_to_inport, roadm_to_outport, ruleID, channel, nodes)
        for i in range(len(path)):
            roadm = path[i]
            Mininet_Agent.ROADM_voaPowerLeveling(node=nodes[roadm], outport=roadm_to_outport[roadm], power=power, channel=channel)
            print('leveling info', roadm, LINE_IN, channel)
        Mininet_Agent.Terminal_configChannel(terminal=terminal, channel=channel)
        Mininet_Agent.Terminal_configChannelPower(terminal= terminal, channel=channel, power=power)
        Mininet_Agent.Terminal_turnonChannel(terminal=terminal)

        return True


    def teardownLightpath(self, path, ruleID, nodes):
        "tear down a lightpath: uninstall switch rule"

        self.uninstallPath(path, ruleID, nodes)
        return True


def Control_Test():
    " set up a lightpath from r1 to r5 with channel 5, launch_power 0 dB"


    '''
    # install switch rule
    ++port ('t5', 'r5', 'r4', 'r3', 'r2', 'r1', 't1') 19 91 90
    ++port ('t5', 'r5', 'r4', 'r3', 'r2', 'r1', 't1') 19 91 90
    ++port ('t5', 'r5', 'r4', 'r3', 'r2', 'r1', 't1') 19 91 90
    ++port ('t5', 'r5', 'r4', 'r3', 'r2', 'r1', 't1') 19 91 90
    ++port ('t5', 'r5', 'r4', 'r3', 'r2', 'r1', 't1') 19 91 18
    
    # power leveling for each roadm
    leveling info r5 90 19
    leveling info r4 90 19
    leveling info r3 90 19
    leveling info r2 90 19
    leveling info r1 18 19
    '''
    cleanup()
    topo = RoadmPhyNetwork()
    net = Mininet(topo=topo, switch=OVSBridge, controller=None)
    net.start()

    # tranceiver 0-89 for channel 1-90
    controller = Simple_Controller_Simu()
    channel = 19
    AddDrop = channel-1
    tranceiverIndx = channel-1
    #net = RoadmPhyNetwork()
    #nodes = net.name_to_node
    roadms = [node for node in net.switches if isinstance(node, ROADM)]
    terms = [node for node in net.switches if isinstance(node, Terminal)]
    allnodes = [node for node in net.switches ]
    nodes = {}
    for node in allnodes:
        nodes[node.name] = node

    path = [ 'r5','r4','r3','r2','r1' ]
    roadm_to_inport= { 'r5': AddDrop, 'r4':LINE_OUT,  'r3':LINE_OUT,  'r2':LINE_OUT, 'r1':LINE_OUT }
    roadm_to_outport= { 'r5':LINE_IN, 'r4':LINE_IN, 'r3':LINE_IN, 'r2':LINE_IN, 'r1':AddDrop }

    #controller.setupLightpath(path=path, roadm_to_inport=roadm_to_inport, roadm_to_outport=roadm_to_outport,
    #                       ruleID=1, channel=channel, terminal=nodes['t5'], power=1, nodes=nodes)

    controller.setupLightpath(path=path, roadm_to_inport=roadm_to_inport, roadm_to_outport=roadm_to_outport,
                              ruleID=1, channel=channel, terminal=nodes['t5'], power=1, nodes=nodes)

    data = Mininet_Agent.ROADM_monitor_all_gosnr(nodes['r5'])
    print(data)



Control_Test()
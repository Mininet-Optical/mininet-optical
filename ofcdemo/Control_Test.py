from network import Network
from link import Span as Fiber, SpanTuple as Segment
from Simulation_API import Mininet_Optical_Simu_API
from node import Transceiver
from units import *
from collections import defaultdict
import random
from collections import defaultdict
import numpy as np


km = dB = dBm = 1.0
m = .001

# Parameters

NUM_WAV = 90
LINE_IN, LINE_OUT = NUM_WAV, NUM_WAV + 1
NUM_NODE = 5

def Span( km, amp=None ):
    "Return a fiber segment of length km with a compensating amp"
    return Segment( span=Fiber( length=km ), amplifier=amp )

def RoadmPhyNetwork():

    """ROADM network topo
    """
    ####################### Linear Topo #####################
    #
    #                    t2       t3       t4
    #                    |        |        |
    #      t1 - r1 ----- r2 ----- r3 ----- r4 ----- r5 - t5
    #
    #########################################################

    net = Network()
    lengths = [15 * km]

    # Network nodes
    transceivers = [('tx%d' % i, 0 * dBm, 'C') for i in range(1, NUM_WAV + 1)]

    # each terminal includes NUM_WAV transceivers
    terminals = [
        net.add_lt(name, transceivers=transceivers, monitor_mode=mode)
        for name, mode in [('t%d' % i, 'in') for i in range(1, NUM_NODE + 1)]]
    roadms = [
        net.add_roadm(name, monitor_mode=mode)
        for name, mode in [('r%d' % i, 'in') for i in range(1, NUM_NODE + 1)]]

    nodes = net.name_to_node
    # Convenience alias
    link = net.add_link

    for k in range(1, NUM_NODE):
        # Eastbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers
        boost = net.add_amplifier('boost{}{}'.format(k, k + 1), target_gain=17 * dB, boost=True)
        spans = []
        for i, length in enumerate(lengths, start=1):
            amp = net.add_amplifier(
                'amp{}{}-{}'.format(k, k + 1, i), target_gain=length * 0.22 * dB, monitor_mode='out')
            span = Span(length, amp=amp)
            spans.append(span)

        link(nodes['r%d' % k], nodes['r%d' % (k + 1)], src_out_port=LINE_OUT, dst_in_port=LINE_IN, boost_amp=boost,
             spans=spans)

        # Westbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers
        boost = net.add_amplifier('boost{}{}'.format(k + 1, k), target_gain=17 * dB, boost=True)
        spans = []
        for i, length in enumerate(lengths, start=1):
            amp = net.add_amplifier(
                'amp{}{}-{}'.format(k + 1, k, i), target_gain=length * 0.22 * dB, monitor_mode='out')
            span = Span(length, amp=amp)
            spans.append(span)

        link(nodes['r%d' % (k + 1)], nodes['r%d' % k], src_out_port=LINE_IN, dst_in_port=LINE_OUT, boost_amp=boost,
             spans=spans)

    for k in range(1,NUM_NODE+1):
        # Local add/drop links between terminals/transceivers and ROADMs
        for add_drop_port in range(NUM_WAV):
            link( nodes['t%d' %k], nodes['r%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
            link( nodes['r%d' %k], nodes['t%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )

    return net



Mininet_Agent = Mininet_Optical_Simu_API()

class Simple_Controller(object):


    def Mininet_installPath(self, path, roadm_to_inport, roadm_to_outport, ruleID, channel):
        "intall switch rules on roadms along a lightpath with a signal channel"

        for i in range(len(path)):
            roadm = path[i]
            Mininet_Agent.ROADM_installSwitchRule(roadm, ruleID, roadm_to_inport[roadm], roadm_to_outport[roadm], channel)


    def Mininet_uninstallPath(self, path, ruleID):
        "delete switch rules on roadms along a lightpath for some signal channels"

        for i in range(len(path)):
            roadm = path[i]
            Mininet_Agent.ROADM_deleteSwitchRule(roadm, ruleID)


    def Mininet_setupLightpath(self, path, roadm_to_inport, roadm_to_outport, ruleID, channel, terminal, tranceiver, power):
        "set up a lightpath: install switch rule and configure terminal"

        self.Mininet_installPath(path, roadm_to_inport, roadm_to_outport, ruleID, channel)
        for i in range(len(path)):
            roadm = path[i]
            if i == len(path) - 1:
                Mininet_Agent.ROADM_voaPowerLeveling(node=roadm, outport=tranceiver, power=power, channel=channel)
            else:
                Mininet_Agent.ROADM_voaPowerLeveling(node=roadm, outport=LINE_OUT, power=power, channel=channel)
        Mininet_Agent.Terminal_configChannel(terminal=terminal, transceiverIndx=tranceiver, channel=channel)
        Mininet_Agent.Terminal_configChannelPower(terminal= terminal, transceiverIndx=tranceiver, power=power)
        Mininet_Agent.Terminal_turnonChannel(terminal=terminal)

        return True


    def Mininet_teardownLightpath(self, path, ruleID):
        "tear down a lightpath: uninstall switch rule"

        self.Mininet_uninstallPath(path, ruleID)
        return True


def Control_Test():
    " set up a lightpath from r1 to r5 with channel 5, launch_power 0 dB"

    # tranceiver 0-89 for channel 1-90
    controller = Simple_Controller()
    channel = 6
    AddDrop = channel-1
    tranceiverIndx = channel-1
    net = RoadmPhyNetwork()
    nodes = net.name_to_node
    print(nodes)

    path = [ nodes['r1'],nodes['r2'],nodes['r3'],nodes['r4'],nodes['r5'] ]
    roadm_to_inport= { nodes['r1']: AddDrop, nodes['r2']:LINE_IN,  nodes['r3']:LINE_IN,  nodes['r4']:LINE_IN,  nodes['r5']:LINE_IN }
    roadm_to_outport= { nodes['r1']:LINE_OUT, nodes['r2']:LINE_OUT, nodes['r3']:LINE_OUT, nodes['r4']:LINE_OUT, nodes['r5']:AddDrop }

    controller.Mininet_setupLightpath(path=path, roadm_to_inport=roadm_to_inport, roadm_to_outport=roadm_to_outport,
                           ruleID=1, channel=channel, terminal=nodes['t1'], tranceiver=tranceiverIndx, power=1)



Control_Test()
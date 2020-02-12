#!/usr/bin/python

"""
WIP: Simplified test of ring topology
"""

from network import Network
from link import Span as FiberSpan, SpanTuple

km = db = dbM = 1.0
m = .001

def Span(km, amp=None):
    "Return a usable span of length km with amplifer amp"
    return SpanTuple(FiberSpan(km), amp)


def ringTopology(n=3):
    "Create ring topology of size n"
    net = Network()

    # Network elements at each POP in ring
    transceivers = [('t1', -2*dbM, 'C')]
    terminals = [net.add_lt('lt%s' % (i + 1), transceivers=transceivers)
                 for i in range(n)]
    wss_dict = {1: (3, None), 2: (3, None)}
    roadms = [net.add_roadm('roadm%s' % (i + 1), wss_dict=wss_dict, voa_function='flatten') for i in range(n)]

    # Links between this POP's LT and ROADM at ports 1, 101
    for i in range(n):
        net.add_link(terminals[i], roadms[i], spans=[Span(1*m)])
        net.add_link(roadms[i], terminals[i], spans=[Span(1*m)])

    # Helper function to create a link between POPs on ports 2, 102
    def link(src, dst, p=1, m='a'):
        "Create 100km link m, from src to dst, for pop p, with amps and monitors"
        boost = net.add_amplifier('boost%d'%p+m, target_gain=6*db, boost=True, constant_power=-2)
        net.add_monitor('mon%d-1'%p+m, amplifier=boost)
        span = Span(100*km)
        amp = net.add_amplifier('amp%d'%p+m, target_gain=22.0*db)
        net.add_link(src, dst, boost_amp=boost, spans=[span])
        net.add_monitor('mon%d-2'%p+m, link=link, span=span, amplifier=amp)

    # Links to/from next POP in ring
    for i in range(n):
        roadm, nextroadm = roadms[i], roadms[(i+1) % n]
        link(roadm, nextroadm, p=i+1, m='a')
        link(nextroadm, roadm, p=i+1, m='b')

    return net


def testRingTopo():
    """
    This script will build the Ring topology and run a single
    2-channel transmission with the default configuration of the simulator,
    and will monitor their OSNR levels. The latter will then be plotted.
    Then, one of the signal will be re-routed through different ports, and
    the reconfiguration on the other channels should be automatic through
    the Traffic wrapper.
    """

    print("*** Building Ring network topology")
    net = ringTopology()

    n = net.name_to_node
    lt1, lt2, lt3 = [n['lt%d' % i] for i in (1, 2, 3)]
    roadm1, roadm2, roadm3 = [n['roadm%d' % i] for i in (1, 2, 3)]

    # Install switch rules into the ROADM nodes
    channels1 = [1, 2]
    channels2 = [3, 4]
    channels3 = [5, 6]

    roadm1.install_switch_rule(1, 0, 102, channels1)  # switches to roadm3
    roadm1.install_switch_rule(2, 0, 101, channels2)  # switches to roadm2
    roadm1.install_switch_rule(3, 0, 101, channels3)  # switches to roadm2

    roadm2.install_switch_rule(1, 1, 102, channels2)  # switches TO roadm3
    roadm2.install_switch_rule(2, 1, 102, channels3)  # switches TO roadm3

    roadm3.install_switch_rule(1, 2, 100, channels1)  # switches FROM roadm1
    roadm3.install_switch_rule(2, 1, 100, channels2)  # switches FROM roadm2
    roadm3.install_switch_rule(3, 1, 100, channels3)  # switches FROM roadm2

    rw = channels1 + channels2 + channels3

    # Set resources to use and initiate transmission
    resources = {'transceiver': lt1.name_to_transceivers['t1'],
                 'required_wavelengths': rw}
    net.transmit(lt1, roadm1, resources=resources)

    print("*** Updating switch rule in roadm_1...")
    roadm2.delete_switch_rule(1)
    roadm3.delete_switch_rule(2)
    roadm3.install_switch_rule(4, 1, 100, channels2)
    roadm1.update_switch_rule(2, 102)


if __name__ == '__main__':
    testRingTopo()
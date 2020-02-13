from network import Network
from link import Span as FiberSpan, SpanTuple


def Span(km, amp=None):
    "Return a usable span of length km with amplifer amp"
    return SpanTuple(FiberSpan(km), amp)


def build(op=0, n=6):
    """
    :param op: operational power in dBm
    :param n: number of nodes (integer)
    :return: Network object
    """
    # Create an optical-network object
    net = Network()

    # Network elements at each POP in ring
    transceivers = [('t1', op, 'C')]
    terminals = [net.add_lt('lt%s' % (i + 1), transceivers=transceivers)
                 for i in range(n)]
    wss_dict = {1: (3, None), 2: (3, None)}
    roadms = [net.add_roadm('roadm%s' % (i + 1), wss_dict=wss_dict, voa_function='flatten') for i in range(n)]
    name_to_roadm = {roadm.name: roadm for roadm in roadms}

    # Links between this POP's LT and ROADM at ports 1, 101
    for i in range(n):
        net.add_link(terminals[i], roadms[i], spans=[Span(0.001)])
        net.add_link(roadms[i], terminals[i], spans=[Span(0.001)])

    # Helper function to create a link between POPs on ports 2, 102
    def link(src, dst, p=1, m='a'):
        "Create 50 km link m, from src to dst, for pop p, with amps and monitors"
        boost = net.add_amplifier('boost%d' % p + m, target_gain=6, boost=True, constant_power=op)
        net.add_monitor('mon%d-1' % p + m, amplifier=boost)
        span = Span(50.0)
        amp = net.add_amplifier('amp%d' % p + m, target_gain=11.0)
        net.add_link(src, dst, boost_amp=boost, spans=[span])
        net.add_monitor('mon%d-2' % p + m, link=link, span=span, amplifier=amp)

    link(name_to_roadm['roadm1'], name_to_roadm['roadm2'], p=1, m='a')
    link(name_to_roadm['roadm2'], name_to_roadm['roadm1'], p=2, m='b')

    link(name_to_roadm['roadm1'], name_to_roadm['roadm3'], p=3, m='c')
    link(name_to_roadm['roadm3'], name_to_roadm['roadm1'], p=4, m='d')

    link(name_to_roadm['roadm2'], name_to_roadm['roadm3'], p=5, m='e')
    link(name_to_roadm['roadm3'], name_to_roadm['roadm2'], p=6, m='f')

    link(name_to_roadm['roadm2'], name_to_roadm['roadm4'], p=7, m='g')
    link(name_to_roadm['roadm4'], name_to_roadm['roadm2'], p=8, m='h')

    link(name_to_roadm['roadm3'], name_to_roadm['roadm5'], p=9, m='i')
    link(name_to_roadm['roadm5'], name_to_roadm['roadm3'], p=10, m='j')

    link(name_to_roadm['roadm4'], name_to_roadm['roadm5'], p=11, m='k')
    link(name_to_roadm['roadm5'], name_to_roadm['roadm4'], p=12, m='l')

    link(name_to_roadm['roadm4'], name_to_roadm['roadm6'], p=13, m='m')
    link(name_to_roadm['roadm6'], name_to_roadm['roadm4'], p=14, m='n')

    link(name_to_roadm['roadm5'], name_to_roadm['roadm6'], p=15, m='o')
    link(name_to_roadm['roadm6'], name_to_roadm['roadm5'], p=16, m='p')

    return net

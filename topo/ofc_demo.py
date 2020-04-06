from network import Network
from link import Span  # as FiberSpan, SpanTuple


# def Span(km, amp=None):
#     "Return a usable span of length km with amplifer amp"
#     return SpanTuple(FiberSpan(km), amp)


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
    wss_dict = {1: (7.0, None), 2: (7.0, None)}
    roadms = [net.add_roadm('roadm%s' % (i + 1), wss_dict=wss_dict,
                            voa_function='flatten', voa_target_out_power=op) for i in range(n)]
    name_to_roadm = {roadm.name: roadm for roadm in roadms}

    # Links between this POP's LT and ROADM at ports 1, 101
    for i in range(n):
        l = net.add_link(terminals[i], roadms[i])
        l.add_span(Span('SMF', 0.001), amplifier=None)
        lb = net.add_link(roadms[i], terminals[i])
        lb.add_span(Span(length=0.001), amplifier=None)

    # Helper function to create a link between POPs on ports 2, 102
    def link(src, dst, p=0):
        "Create 50 km link m, from src to dst, for pop p, with amps and monitors"

        boost = net.add_amplifier('boost%d' % p, target_gain=17.0, boost=True)
        l = net.add_link(src, dst, boost_amp=boost)
        net.add_monitor('mon%d-b' % p, amplifier=boost)
        for span_no in range(4):
            span = Span(fibre_type='SMF', length=50)
            amp = net.add_amplifier('amp%d' % p, target_gain=11.0)
            l.add_span(span, amp)
            net.add_monitor('mon%d' % p, link=l, span=span, amplifier=amp)
            p += 1

    nodes = [1, 2, 3, 4, 5]
    n = name_to_roadm
    p = 1
    for i in nodes:
        j = i + 1
        if i is 5:
            roadm, nextroadm = n['roadm%s' % str(i)], n['roadm%s' % str(j)]
            link(roadm, nextroadm, p=p)
            link(nextroadm, roadm, p=p + 4)
        elif i is 3:
            roadm, nextroadm = n['roadm%s' % str(i)], n['roadm%s' % str(j + 1)]
            link(roadm, nextroadm, p=p)
            link(nextroadm, roadm, p=p + 4)
            p += 2 * 4
        else:
            while j <= i + 2:
                roadm, nextroadm = n['roadm%s' % str(i)], n['roadm%s' % str(j)]
                link(roadm, nextroadm, p=p)
                link(nextroadm, roadm, p=p + 4)
                p += 2 * 4
                j += 1

    return net

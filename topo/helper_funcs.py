from link import Span as Fiber, SpanTuple as Segment


km = dB = dBm = 1.0
m = .001

def Span(km, amp=None):
    """Return a fiber segment of length km with a compensating amp"""
    return Segment(span=Fiber(length=km), amplifier=amp)

def build_spans(net, r1, r2, span_no, span_length, port_no, amp=False, debugger=True):
    # store all spans (sequentially) in a list
    spans = []

    for i in range(1, span_no + 1):
        # append all spans except last one
        amplifier = None
        if amp:
            amplifier = net.add_amplifier(
                '%s-%s-amp%d-%d' % (r1, r2, i, port_no),
                target_gain=span_length * 0.22 * dB,
                monitor_mode='out',
                debugger=debugger)
        span = Span(span_length, amp=amplifier)
        spans.append(span)

    return net, spans

def build_link(net, r1, r2, span_no, span_length, debugger=True):
    net, spans = build_spans(net, r1, r2, span_no, span_length, debugger=debugger)
    for step, span in enumerate(spans, start=1):
        net.spans.append(span)

    # link object
    net.add_link(r1, r2, spans=spans)

def add_amp(net, node_name=None, type=None, gain_dB=None, debugger=True):
    """
    Create an Amplifier object to add to a ROADM node
    :param node_name: string
    :param type: string ('boost' or 'preamp'
    :param gain_dB: int or float
    """
    label = '%s-%s' % (node_name, type)
    if type == 'preamp':
        return net.add_amplifier(name=label,
                                 target_gain=float(gain_dB),
                                 boost=True,
                                 monitor_mode='out',
                                 debugger=debugger)
    else:
        return net.add_amplifier(name=label,
                                 target_gain=float(gain_dB),
                                 preamp=True,
                                 monitor_mode='out',
                                 debugger=debugger)
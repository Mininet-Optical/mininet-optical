import mininet_optical.network as network
from mininet_optical.link import Span
import numpy as np


def build_spans(total_len):
    """
    Helper function for building spans of
    fixed length of 50km and handling those
    that require different lengths
    """
    # store all spans (sequentially) in a list
    spans = []
    # get number of spans (int)
    span_no = int(total_len / 50)
    # get a residual length if not fixed
    res_len = total_len - 50 * span_no

    # extra span for residual
    extra_span = None
    last_span = 50
    if res_len > 20:
        # if exceeding 20 km, save
        # as an extra span
        extra_span = res_len
    else:
        # otherwise, add to the last span
        last_span += res_len

    for i in range(span_no - 1):
        # append all spans except last one
        spans.append(Span('SMF', 50.0))
    # append last span (length might have changed)
    spans.append(Span('SMF', last_span))

    if extra_span:
        # add an extra span (if needed)
        spans.append(Span('SMF', extra_span))

    return spans


def build_link(net, r1, r2, total_len):
    # boost amplifier object
    boost_l = '%s-%s-boost' % (r1, r2)  # label boost amp
    boost_amp = net.add_amplifier(boost_l, 'EDFA', target_gain=17.0, boost=True, monitor_mode='out')

    # link object
    link_r1_r2 = net.add_link(r1, r2, boost_amp=boost_amp)
    spans = build_spans(total_len)

    for step, span in enumerate(spans, start=1):
        net.spans.append(span)
        in_l = '%s-%s-amp%d' % (r1, r2, step)  # label inline amp
        in_line_amp = net.add_amplifier(in_l, 'EDFA', target_gain=span.length / 1e3 * 0.22, monitor_mode='out')
        # adding span and in-line amplifier to link
        link_r1_r2.add_span(span, in_line_amp)


def build_links(net, r1, r2, total_len):
    build_link(net, r1, r2, total_len)
    build_link(net, r2, r1, total_len)


class Cost239Topology:

    @staticmethod
    def build(op=0):
        """
        :param op: operational power in dBm
        :return: Network object
        """
        # Create an optical-network object
        net = network.Network()

        # Create line terminals
        operational_power = op  # power in dBm
        tr_no = np.arange(90)
        tr_labels = ['t%s' % str(x) for x in tr_no]
        transceivers = [(tr, operational_power, 'C') for tr in tr_labels]
        city_names = ['amsterdam', 'berlin', 'brussels', 'copenhagen', 'london',
                      'luxembourg', 'milan', 'paris', 'prague', 'vienna', 'zurich']
        line_terminals = [net.add_lt('lt_%s' % name, transceivers=transceivers) for name in city_names]

        # Create ROADMs
        wss_dict = {1: (7.0, None), 2: (7.0, None)}
        roadms = [net.add_roadm('r_%s' % name, wss_dict=wss_dict,
                                equalization_function='flatten',
                                equalization_target_out_power=op) for name in city_names]
        name_to_roadm = {roadm.name: roadm for roadm in roadms}

        # Create bi-directional links between LTs and ROADMs
        for lt, roadm in zip(line_terminals, roadms):
            for _ in lt.transceivers:
                link = net.add_link(lt, roadm)
                link.add_span(Span('SMF', 0.001), amplifier=None)
                bi_link = net.add_link(roadm, lt)
                bi_link.add_span(Span('SMF', 0.001), amplifier=None)

        # build links per roadm
        ams = name_to_roadm['r_amsterdam']
        ber = name_to_roadm['r_berlin']
        bxl = name_to_roadm['r_brussels']
        cph = name_to_roadm['r_copenhagen']
        ldn = name_to_roadm['r_london']
        lux = name_to_roadm['r_luxembourg']
        mil = name_to_roadm['r_milan']
        par = name_to_roadm['r_paris']
        pra = name_to_roadm['r_prague']
        vie = name_to_roadm['r_vienna']
        zur = name_to_roadm['r_zurich']

        # Main Amsterdam bi-links
        build_links(net, ams, ldn, 390)
        build_links(net, ams, bxl, 200)
        build_links(net, ams, lux, 310)
        build_links(net, ams, ber, 600)
        build_links(net, ams, cph, 750)

        # Main Berlin bi-links
        build_links(net, ber, cph, 400)
        build_links(net, ber, par, 900)
        build_links(net, ber, pra, 320)
        build_links(net, ber, vie, 710)

        # Main Brussels bi-links
        build_links(net, bxl, ldn, 340)
        build_links(net, bxl, par, 270)
        build_links(net, bxl, mil, 850)
        build_links(net, bxl, lux, 100)

        # Main Copenhagen bi-links
        build_links(net, cph, ldn, 1000)
        build_links(net, cph, pra, 760)

        # Main London bi-links
        build_links(net, ldn, par, 410)

        # Main Luxembourg bi-links
        build_links(net, lux, par, 370)
        build_links(net, lux, zur, 440)
        build_links(net, lux, pra, 900)

        # Main Milan bi-links
        build_links(net, mil, par, 810)
        build_links(net, mil, zur, 100)
        build_links(net, mil, vie, 720)

        # Main Paris bi-links
        build_links(net, par, zur, 590)

        # Main Prague bi-links
        build_links(net, pra, zur, 100)
        build_links(net, pra, vie, 350)

        # Main Vienna bi-links
        build_links(net, vie, zur, 710)

        return net

import network
from link import Span
import numpy as np


class LinearTopology:

    @staticmethod
    def build(op=0, non=3):
        """
        :param op: operational power in dBm
        :param non: number of nodes (integer)
        :return: Network object
        """
        # Create an optical-network object
        net = network.Network()

        # Create line terminals
        operational_power = op  # power in dBm
        ran = np.arange(1, 82)
        tr_labels = ['t%s' % str(x) for x in ran]
        transceivers = [(tr, operational_power, 'C') for tr in tr_labels]
        line_terminals = [net.add_lt('lt_%s' % (i + 1), transceivers=transceivers) for i in range(non)]

        # Create ROADMs
        wss_dict = {1: (7.0, None), 2: (7.0, None)}
        roadms = [net.add_roadm('roadm_%s' % (i + 1), wss_dict=wss_dict,
                                voa_function='flatten', voa_target_out_power=op) for i in range(non)]
        name_to_roadm = {roadm.name: roadm for roadm in roadms}

        # Create bi-directional links between LTs and ROADMs
        for lt, roadm in zip(line_terminals, roadms):
            link = net.add_link(lt, roadm)
            link.add_span(Span('SMF', 0.001), amplifier=None)
            bi_link = net.add_link(roadm, lt)
            bi_link.add_span(Span('SMF', 0.001), amplifier=None)

        opm_i = 0
        # number of spans per link
        span_no = 6
        # span distance in km
        span_distance = 100
        # target gain
        target_gain = 0.22 * span_distance
        for i in range(non-1):
            # Iterate through the number of nodes linearly connected
            r1 = i + 1  # init node
            r2 = i + 2  # next node
            boost_label = 'boost_roadm' + str(r1) + '_roadm' + str(r2)  # label of boost amplifier
            # boost amplifier object
            boost_amp = net.add_amplifier(boost_label, 'EDFA', target_gain=17.0, boost=True)
            # label of init node
            rl_1 = 'roadm_' + str(r1)
            # label of next node
            rl_2 = 'roadm_' + str(r2)
            # link object
            link_r1_r2 = net.add_link(name_to_roadm[rl_1],
                                      name_to_roadm[rl_2],
                                      boost_amp=boost_amp)
            opm_l = 'opm_' + str(opm_i + 1)  # label OPM boost
            # OPM object
            net.add_monitor(opm_l, link=None,
                            span=None, amplifier=boost_amp)

            # id of in line amplifiers
            in_apm_no = 0
            # id of OPM at end of spans
            opm_no = opm_i + 1
            for sp in range(span_no):
                # Iterate through number of spans in link
                # span object
                span = Span('SMF', span_distance)
                net.spans.append(span)
                in_l = 'amp' + str(in_apm_no+1) + '_l_roadm' + str(r1) + '_roadm' + str(r2)

                in_line_amp = net.add_amplifier(in_l, 'EDFA', target_gain=target_gain)
                # adding span and in-line amplifier to link
                link_r1_r2.add_span(span, in_line_amp)
                opm_l = 'opm_' + str(opm_no + 1)  # label OPM
                # OPM object
                net.add_monitor(opm_l, link=link_r1_r2,
                                span=span, amplifier=in_line_amp)
                # increment amplifier count
                in_apm_no = in_apm_no + 1
                # increment OPM count
                opm_no = opm_no + 1

            # bidirectional flows
            boost_label = 'boost_roadm' + str(r2) + '_roadm' + str(r1)
            boost_amp = net.add_amplifier(boost_label, 'EDFA', target_gain=17.0, boost=True)
            link_r2_r1 = net.add_link(name_to_roadm[rl_2],
                                      name_to_roadm[rl_1],
                                      boost_amp=boost_amp)
            in_apm_no = 0
            for sp in range(span_no):
                span = Span('SMF', span_distance)
                in_l = 'amp' + str(in_apm_no + 1) + '_l_roadm' + str(r2) + '_roadm' + str(r1)
                in_line_amp = net.add_amplifier(in_l, 'EDFA', target_gain=target_gain)
                link_r2_r1.add_span(span, in_line_amp)
                in_apm_no = in_apm_no + 1

            opm_i = opm_no

        return net

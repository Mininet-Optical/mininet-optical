import network
from link import Span
import numpy as np


class LinearTopology:

    @staticmethod
    def build(op=-2, non=3):
        """

        :param op: operational power in dBm
        :param non: number of nodes (integer)
        :return: Network object
        """
        # Create an optical-network object
        net = network.Network()

        # Create line terminals
        operational_power = op  # power in dBm
        transceivers = [('t1', operational_power, 'C')]
        line_terminals = [net.add_lt('lt_%s' % (i + 1), transceivers=transceivers) for i in range(non)]

        # Create ROADMs
        wss_dict = {1: (3, None), 2: (3, None)}
        roadms = [net.add_roadm('roadm_%s' % (i + 1), wss_dict=wss_dict) for i in range(non)]
        name_to_roadm = {roadm.name: roadm for roadm in roadms}

        # Create bi-directional links between LTs and ROADMs
        for lt, roadm in zip(line_terminals, roadms):
            link = net.add_link(lt, roadm)
            link.add_span(Span('SMF', 0.001), amplifier=None)
            bi_link = net.add_link(roadm, lt)
            bi_link.add_span(Span('SMF', 0.001), amplifier=None)

        """
            Create links between inter-city ROADM nodes
        """
        # Labels for object creation
        us = '_'
        boost_lab = 'boost'
        amp_lab = 'amp'
        roadm_lab = 'roadm'
        opm_lab = 'opm'

        opm_i = 0
        span_no = 6
        tmp_qot_id = 1
        for i in range(non-1):
            # Iterate through the number of nodes linearly connected
            r1 = i + 1  # ROADM 1 index
            r2 = i + 2  # ROADM 2 index
            boost_label = boost_lab + us + roadm_lab + str(r1) + us + roadm_lab + str(r2)  # label of boost amplifier
            # boost amplifier object
            boost_amp = net.add_amplifier(boost_label, 'EDFA', target_gain=6, boost=True, tmp_qot_id=tmp_qot_id)
            rl_1 = roadm_lab + us + str(r1)  # label of ROADM1
            rl_2 = roadm_lab + us + str(r2)  # label of ROADM1
            # link object
            link_r1_r2 = net.add_link(name_to_roadm[rl_1],
                                      name_to_roadm[rl_2],
                                      boost_amp=boost_amp)
            opm_l = opm_lab + us + str(opm_i + 1)  # label OPM boost
            # OPM object
            net.add_monitor(opm_l, link=None,
                            span=None, amplifier=boost_amp)

            in_apm_no = 0  # id of in line amplifiers
            opm_no = opm_i + 1  # id of OPM at end of spans
            tmp_qot_id += 1
            for sp in range(span_no):
                # Iterate through number of spans in link
                # span object
                span = Span('SMF', 80)
                in_l = amp_lab + str(in_apm_no+1) + us + 'l' + us + roadm_lab + str(r1) + us + roadm_lab + str(r2)
                if sp is 5:
                    # in-line amplifier object
                    in_line_amp = net.add_amplifier(in_l, 'EDFA', target_gain=17.6, equalizer=False,
                                                    eq_power=op, tmp_qot_id=tmp_qot_id)
                else:
                    in_line_amp = net.add_amplifier(in_l, 'EDFA', target_gain=17.6, tmp_qot_id=tmp_qot_id)
                # adding span and in-line amplifier to link
                link_r1_r2.add_span(span, in_line_amp)
                opm_l = opm_lab + us + str(opm_no + 1)  # label OPM
                # OPM object
                net.add_monitor(opm_l, link=link_r1_r2,
                                span=span, amplifier=in_line_amp)
                # increment amplifier count
                in_apm_no = in_apm_no + 1
                # increment OPM count
                opm_no = opm_no + 1
                tmp_qot_id += 1

            # bidirectional
            boost_label = boost_lab + us + roadm_lab + str(r2) + us + roadm_lab + str(r1)
            boost_amp = net.add_amplifier(boost_label, 'EDFA', target_gain=6, boost=True)
            link_r2_r1 = net.add_link(name_to_roadm[rl_2],
                                      name_to_roadm[rl_1],
                                      boost_amp=boost_amp)
            in_apm_no = 0
            for sp in range(span_no):
                span = Span('SMF', 80)
                in_l = amp_lab + str(in_apm_no + 1) + us + 'l' + us + roadm_lab + str(r2) + us + roadm_lab + str(r1)
                in_line_amp = net.add_amplifier(in_l, 'EDFA', target_gain=17.6)
                link_r2_r1.add_span(span, in_line_amp)
                in_apm_no = in_apm_no + 1

            opm_i = opm_no

        return net

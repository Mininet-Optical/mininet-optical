import mininet_optical.network as network
from mininet_optical.link import Span


class RingTopology:

    @staticmethod
    def build():
        # Create an optical-network object
        net = network.Network()

        non = 3  # number of nodes

        # Create line terminals
        operational_power = -2  # power in dBm
        transceivers = [('t1', operational_power, 'C')]
        line_terminals = [net.add_lt('lt_%s' % (i + 1), transceivers=transceivers) for i in range(non)]

        # Create ROADMs
        roadms = [net.add_roadm('roadm_%s' % (i + 1)) for i in range(non)]
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
        # Link between ROADM1 and ROADM2 - 100 km
        # and the bidirectional (independent) link
        boost_roadm1_roadm2 = net.add_amplifier('boost_roadm1_roadm2', 'EDFA', target_gain=17.0, boost=True)
        l_roadm1_roadm2 = net.add_link(name_to_roadm['roadm_1'],
                                       name_to_roadm['roadm_2'],
                                       boost_amp=boost_roadm1_roadm2)
        net.add_monitor('opm_boost_roadm1_roadm2', link=None,
                        span=None, amplifier=boost_roadm1_roadm2)
        s1_l_roadm1_roadm2 = Span('SMF', 100)
        amp1_l_roadm1_roadm2 = net.add_amplifier('amp1_l_roadm1_roadm2', 'EDFA', target_gain=22.0)
        l_roadm1_roadm2.add_span(s1_l_roadm1_roadm2, amp1_l_roadm1_roadm2)
        net.add_monitor('opm_s1_roadm1_roadm2', link=l_roadm1_roadm2,
                        span=s1_l_roadm1_roadm2, amplifier=amp1_l_roadm1_roadm2)

        boost_roadm2_roadm1 = net.add_amplifier('boost_roadm2_roadm1', 'EDFA', target_gain=17.0, boost=True)
        l_roadm2_roadm1 = net.add_link(name_to_roadm['roadm_2'],
                                       name_to_roadm['roadm_1'],
                                       boost_amp=boost_roadm2_roadm1)
        net.add_monitor('opm_boost_roadm2_roadm1', link=None,
                        span=None, amplifier=boost_roadm2_roadm1)
        s1_l_roadm2_roadm1 = Span('SMF', 100)
        amp1_l_roadm2_roadm1 = net.add_amplifier('amp1_l_roadm2_roadm1', 'EDFA', target_gain=22.0)
        l_roadm2_roadm1.add_span(s1_l_roadm2_roadm1, amp1_l_roadm2_roadm1)
        net.add_monitor('opm_s1_roadm2_roadm1', link=l_roadm2_roadm1,
                        span=s1_l_roadm2_roadm1, amplifier=amp1_l_roadm2_roadm1)

        # Link between ROADM1 and ROADM3 - 100 km
        # and the bidirectional (independent) link
        boost_roadm1_roadm3 = net.add_amplifier('boost_roadm1_roadm3', 'EDFA', target_gain=17.0, boost=True)
        l_roadm1_roadm3 = net.add_link(name_to_roadm['roadm_1'],
                                       name_to_roadm['roadm_3'],
                                       boost_amp=boost_roadm1_roadm3)
        net.add_monitor('opm_boost_roadm1_roadm3', link=None,
                        span=None, amplifier=boost_roadm1_roadm3)
        s1_l_roadm1_roadm3 = Span('SMF', 100)
        amp1_l_roadm1_roadm3 = net.add_amplifier('amp1_l_roadm1_roadm3', 'EDFA', target_gain=22.0)
        l_roadm1_roadm3.add_span(s1_l_roadm1_roadm3, amp1_l_roadm1_roadm3)
        net.add_monitor('opm_s1_roadm1_roadm3', link=l_roadm1_roadm3,
                        span=s1_l_roadm1_roadm3, amplifier=amp1_l_roadm1_roadm3)

        boost_roadm3_roadm1 = net.add_amplifier('boost_roadm3_roadm1', 'EDFA', target_gain=17.0, boost=True)
        l_roadm3_roadm1 = net.add_link(name_to_roadm['roadm_3'],
                                       name_to_roadm['roadm_1'],
                                       boost_amp=boost_roadm3_roadm1)
        net.add_monitor('opm_boost_roadm3_roadm1', link=None,
                        span=None, amplifier=boost_roadm3_roadm1)
        s1_l_roadm3_roadm1 = Span('SMF', 100)
        amp1_l_roadm3_roadm1 = net.add_amplifier('amp1_l_roadm3_roadm1', 'EDFA', target_gain=22.0)
        l_roadm3_roadm1.add_span(s1_l_roadm3_roadm1, amp1_l_roadm3_roadm1)
        net.add_monitor('opm_s1_roadm3_roadm1', link=l_roadm3_roadm1,
                        span=s1_l_roadm3_roadm1, amplifier=amp1_l_roadm3_roadm1)

        # Link between ROADM2 and ROADM3 - 100 km
        # and the bidirectional (independent) link
        boost_roadm2_roadm3 = net.add_amplifier('boost_roadm2_roadm3', 'EDFA', target_gain=17.0, boost=True)
        l_roadm2_roadm3 = net.add_link(name_to_roadm['roadm_2'],
                                       name_to_roadm['roadm_3'],
                                       boost_amp=boost_roadm2_roadm3)
        net.add_monitor('opm_boost_roadm2_roadm3', link=None,
                        span=None, amplifier=boost_roadm2_roadm3)
        s1_l_roadm2_roadm3 = Span('SMF', 100)
        amp1_l_roadm2_roadm3 = net.add_amplifier('amp1_l_roadm2_roadm3', 'EDFA', target_gain=22.0)
        l_roadm2_roadm3.add_span(s1_l_roadm2_roadm3, amp1_l_roadm2_roadm3)
        net.add_monitor('opm_s1_roadm2_roadm3', link=l_roadm2_roadm3,
                        span=s1_l_roadm2_roadm3, amplifier=amp1_l_roadm2_roadm3)

        boost_roadm3_roadm2 = net.add_amplifier('boost_roadm3_roadm2', 'EDFA', target_gain=17.0, boost=True)
        l_roadm3_roadm2 = net.add_link(name_to_roadm['roadm_3'],
                                       name_to_roadm['roadm_2'],
                                       boost_amp=boost_roadm3_roadm2)
        net.add_monitor('opm_boost_roadm3_roadm2', link=None,
                        span=None, amplifier=boost_roadm3_roadm2)
        s1_l_roadm3_roadm2 = Span('SMF', 100)
        amp1_l_roadm3_roadm2 = net.add_amplifier('amp1_l_roadm3_roadm2', 'EDFA', target_gain=22.0)
        l_roadm3_roadm2.add_span(s1_l_roadm3_roadm2, amp1_l_roadm3_roadm2)
        net.add_monitor('opm_s1_roadm3_roadm2', link=l_roadm3_roadm2,
                        span=s1_l_roadm3_roadm2, amplifier=amp1_l_roadm3_roadm2)

        return net

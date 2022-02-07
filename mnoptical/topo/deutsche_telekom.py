import mnoptical.network as network
from mnoptical.link import Span


class DeutscheTelekom:

    @staticmethod
    def build(op=-2):
        """
            TOPOLOGY CREATION

            Nomenclature conventions:
            lt_: Line Terminal
            roadm_: ROADM node
            l_: Link between two nodes
            s_: Span in a Link
            boost_: Boost amplifier
            amp: inline amplifier
        """
        # Create an optical-network object
        net = network.Network()

        """
            Create line terminals and their immediate ROADM nodes
            and create bi-directional links between them.
        """
        cities = ['berlin', 'bremen', 'dortmund', 'dusseldorf',
                  'essen', 'frankfurt', 'hamburg', 'hannover',
                  'koln', 'leipzig', 'munchen', 'nurnberg',
                  'stuttgart', 'ulm']

        # Create line terminals
        operational_power = op  # power in dBm
        transceivers = [('t1', operational_power, 'C')]
        line_terminals = [net.add_lt('lt_%s' % s, transceivers=transceivers) for s in cities]

        # Create ROADMs
        roadms = [net.add_roadm('roadm_%s' % s) for s in cities]
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
        # Link between Berlin and Hamburg - 306.3 km
        # and the bidirectional (independent) link
        boost_berlin_hamburg = net.add_amplifier('boost_berlin_hamburg', 'EDFA', target_gain=17.0, boost=True)
        l_berlin_hamburg = net.add_link(name_to_roadm['roadm_berlin'],
                                        name_to_roadm['roadm_hamburg'],
                                        boost_amp=boost_berlin_hamburg)
        s1_l_berlin_hamburg = Span('SMF', 80)
        amp1_l_berlin_hamburg = net.add_amplifier('amp1_l_berlin_hamburg', 'EDFA', target_gain=17.6)
        l_berlin_hamburg.add_span(s1_l_berlin_hamburg, amp1_l_berlin_hamburg)
        s2_l_berlin_hamburg = Span('SMF', 80)
        amp2_l_berlin_hamburg = net.add_amplifier('amp2_l_berlin_hamburg', 'EDFA', target_gain=17.6)
        l_berlin_hamburg.add_span(s2_l_berlin_hamburg, amp2_l_berlin_hamburg)
        s3_l_berlin_hamburg = Span('SMF', 80)
        amp3_l_berlin_hamburg = net.add_amplifier('amp3_l_berlin_hamburg', 'EDFA', target_gain=17.6)
        l_berlin_hamburg.add_span(s3_l_berlin_hamburg, amp3_l_berlin_hamburg)
        s4_l_berlin_hamburg = Span('SMF', 33.7)
        amp4_l_berlin_hamburg = net.add_amplifier('amp4_l_berlin_hamburg', 'EDFA', target_gain=7.4)
        l_berlin_hamburg.add_span(s4_l_berlin_hamburg, amp4_l_berlin_hamburg)

        boost_hamburg_berlin = net.add_amplifier('boost_hamburg_berlin', 'EDFA', target_gain=17.0, boost=True)
        l_hamburg_berlin = net.add_link(name_to_roadm['roadm_hamburg'],
                                        name_to_roadm['roadm_berlin'],
                                        boost_amp=boost_hamburg_berlin)
        s1_l_hamburg_berlin = Span('SMF', 80)
        amp1_l_hamburg_berlin = net.add_amplifier('amp1_l_hamburg_berlin', 'EDFA', target_gain=17.6)
        l_hamburg_berlin.add_span(s1_l_hamburg_berlin, amp1_l_hamburg_berlin)
        s2_l_hamburg_berlin = Span('SMF', 80)
        amp2_l_hamburg_berlin = net.add_amplifier('amp2_l_hamburg_berlin', 'EDFA', target_gain=17.6)
        l_hamburg_berlin.add_span(s2_l_hamburg_berlin, amp2_l_hamburg_berlin)
        s3_l_hamburg_berlin = Span('SMF', 80)
        amp3_l_hamburg_berlin = net.add_amplifier('amp3_l_hamburg_berlin', 'EDFA', target_gain=17.6)
        l_hamburg_berlin.add_span(s3_l_hamburg_berlin, amp3_l_hamburg_berlin)
        s4_l_hamburg_berlin = Span('SMF', 33.7)
        amp4_l_hamburg_berlin = net.add_amplifier('amp4_l_hamburg_berlin', 'EDFA', target_gain=7.4)
        l_hamburg_berlin.add_span(s4_l_hamburg_berlin, amp4_l_hamburg_berlin)

        # Link between Berlin and Hannover - 294.9 km
        # and the bidirectional (independent) link
        boost_berlin_hannover = net.add_amplifier('boost_berlin_hannover', 'EDFA', target_gain=17.0, boost=True)
        l_berlin_hannover = net.add_link(name_to_roadm['roadm_berlin'],
                                         name_to_roadm['roadm_hannover'],
                                         boost_amp=boost_berlin_hannover)
        s1_l_berlin_hannover = Span('SMF', 80)
        amp1_l_berlin_hannover = net.add_amplifier('amp1_l_berlin_hannover', 'EDFA', target_gain=22)
        l_berlin_hannover.add_span(s1_l_berlin_hannover, amp1_l_berlin_hannover)
        s2_l_berlin_hannover = Span('SMF', 80)
        amp2_l_berlin_hannover = net.add_amplifier('amp2_l_berlin_hannover', 'EDFA', target_gain=17.6)
        l_berlin_hannover.add_span(s2_l_berlin_hannover, amp2_l_berlin_hannover)
        s3_l_berlin_hannover = Span('SMF', 80)
        amp3_l_berlin_hannover = net.add_amplifier('amp3_l_berlin_hannover', 'EDFA', target_gain=17.6)
        l_berlin_hannover.add_span(s3_l_berlin_hannover, amp3_l_berlin_hannover)
        s4_l_berlin_hannover = Span('SMF', 54.9)
        amp4_l_berlin_hannover = net.add_amplifier('amp4_l_berlin_hannover', 'EDFA', target_gain=13.18)
        l_berlin_hannover.add_span(s4_l_berlin_hannover, amp4_l_berlin_hannover)

        boost_hannover_berlin = net.add_amplifier('boost_hannover_berlin', 'EDFA', target_gain=17.0, boost=True)
        l_hannover_berlin = net.add_link(name_to_roadm['roadm_hannover'],
                                         name_to_roadm['roadm_berlin'],
                                         boost_amp=boost_hannover_berlin)
        s1_l_hannover_berlin = Span('SMF', 80)
        amp1_l_hannover_berlin = net.add_amplifier('amp1_l_hannover_berlin', 'EDFA', target_gain=17.6)
        l_hannover_berlin.add_span(s1_l_hannover_berlin, amp1_l_hannover_berlin)
        s2_l_hannover_berlin = Span('SMF', 80)
        amp2_l_hannover_berlin = net.add_amplifier('amp2_l_hannover_berlin', 'EDFA', target_gain=17.6)
        l_hannover_berlin.add_span(s2_l_hannover_berlin, amp2_l_hannover_berlin)
        s3_l_hannover_berlin = Span('SMF', 80)
        amp3_l_hannover_berlin = net.add_amplifier('amp3_l_hannover_berlin', 'EDFA', target_gain=17.6)
        l_hannover_berlin.add_span(s3_l_hannover_berlin, amp3_l_hannover_berlin)
        s4_l_hannover_berlin = Span('SMF', 54.9)
        amp4_l_hannover_berlin = net.add_amplifier('amp4_l_hannover_berlin', 'EDFA', target_gain=13.18)
        l_hannover_berlin.add_span(s4_l_hannover_berlin, amp4_l_hannover_berlin)

        # Link between Berlin and Leipzig - 173.3 km
        # and the bidirectional (independent) link
        boost_berlin_leipzig = net.add_amplifier('boost_berlin_leipzig', 'EDFA', target_gain=17.0, boost=True)
        l_berlin_leipzig = net.add_link(name_to_roadm['roadm_berlin'],
                                        name_to_roadm['roadm_leipzig'],
                                        boost_amp=boost_berlin_leipzig)
        s1_l_berlin_leipzig = Span('SMF', 80)
        amp1_l_berlin_leipzig = net.add_amplifier('amp1_l_berlin_leipzig', 'EDFA', target_gain=17.6)
        l_berlin_leipzig.add_span(s1_l_berlin_leipzig, amp1_l_berlin_leipzig)
        s2_l_berlin_leipzig = Span('SMF', 80)
        amp2_l_berlin_leipzig = net.add_amplifier('amp2_l_berlin_leipzig', 'EDFA', target_gain=17.6)
        l_berlin_leipzig.add_span(s2_l_berlin_leipzig, amp2_l_berlin_leipzig)
        s3_l_berlin_leipzig = Span('SMF', 13.3)
        amp3_l_berlin_leipzig = net.add_amplifier('amp3_l_berlin_leipzig', 'EDFA', target_gain=2.9)
        l_berlin_leipzig.add_span(s3_l_berlin_leipzig, amp3_l_berlin_leipzig)

        boost_leipzig_berlin = net.add_amplifier('boost_leipzig_berlin', 'EDFA', target_gain=17.0, boost=True)
        l_leipzig_berlin = net.add_link(name_to_roadm['roadm_leipzig'],
                                        name_to_roadm['roadm_berlin'],
                                        boost_amp=boost_leipzig_berlin)
        s1_l_leipzig_berlin = Span('SMF', 80)
        amp1_l_leipzig_berlin = net.add_amplifier('amp1_l_leipzig_berlin', 'EDFA', target_gain=17.6)
        l_leipzig_berlin.add_span(s1_l_leipzig_berlin, amp1_l_leipzig_berlin)
        s2_l_leipzig_berlin = Span('SMF', 80)
        amp2_l_leipzig_berlin = net.add_amplifier('amp2_l_leipzig_berlin', 'EDFA', target_gain=17.6)
        l_leipzig_berlin.add_span(s2_l_leipzig_berlin, amp2_l_leipzig_berlin)
        s3_l_leipzig_berlin = Span('SMF', 13.3)
        amp3_l_leipzig_berlin = net.add_amplifier('amp3_l_leipzig_berlin', 'EDFA', target_gain=17.0)
        l_leipzig_berlin.add_span(s3_l_leipzig_berlin, amp3_l_leipzig_berlin)

        # Link between Bremen and Hamburg - 114.7 km
        # and the bidirectional (independent) link
        boost_bremen_hamburg = net.add_amplifier('boost_bremen_hamburg', 'EDFA', target_gain=17.0, boost=True)
        l_bremen_hamburg = net.add_link(name_to_roadm['roadm_bremen'],
                                        name_to_roadm['roadm_hamburg'],
                                        boost_amp=boost_bremen_hamburg)
        s1_l_bremen_hamburg = Span('SMF', 80)
        amp1_l_bremen_hamburg = net.add_amplifier('amp1_l_bremen_hamburg', 'EDFA', target_gain=17.6)
        l_bremen_hamburg.add_span(s1_l_bremen_hamburg, amp1_l_bremen_hamburg)
        s2_l_bremen_hamburg = Span('SMF', 34.7)
        amp2_l_bremen_hamburg = net.add_amplifier('amp2_l_bremen_hamburg', 'EDFA', target_gain=7.63)
        l_bremen_hamburg.add_span(s2_l_bremen_hamburg, amp2_l_bremen_hamburg)

        boost_hamburg_bremen = net.add_amplifier('boost_hamburg_bremen', 'EDFA', target_gain=17.0, boost=True)
        l_hamburg_bremen = net.add_link(name_to_roadm['roadm_hamburg'],
                                        name_to_roadm['roadm_bremen'],
                                        boost_amp=boost_hamburg_bremen)
        s1_l_hamburg_bremen = Span('SMF', 80)
        amp1_l_hamburg_bremen = net.add_amplifier('amp1_l_hamburg_bremen', 'EDFA', target_gain=17.6)
        l_hamburg_bremen.add_span(s1_l_hamburg_bremen, amp1_l_hamburg_bremen)
        s2_l_hamburg_bremen = Span('SMF', 34.7)
        amp2_l_hamburg_bremen = net.add_amplifier('amp2_l_hamburg_bremen', 'EDFA', target_gain=7.63)
        l_hamburg_bremen.add_span(s2_l_hamburg_bremen, amp2_l_hamburg_bremen)

        # Link between Bremen and Hannover - 121.3 km
        # and the bidirectional (independent) link
        boost_bremen_hannover = net.add_amplifier('boost_bremen_hannover', 'EDFA', target_gain=17.0, boost=True)
        l_bremen_hannover = net.add_link(name_to_roadm['roadm_bremen'],
                                         name_to_roadm['roadm_hannover'],
                                         boost_amp=boost_bremen_hannover)
        s1_l_bremen_hannover = Span('SMF', 80)
        amp1_l_bremen_hannover = net.add_amplifier('amp1_l_bremen_hannover', 'EDFA', target_gain=17.6)
        l_bremen_hannover.add_span(s1_l_bremen_hannover, amp1_l_bremen_hannover)
        s2_l_bremen_hannover = Span('SMF', 41.3)
        amp2_l_bremen_hannover = net.add_amplifier('amp2_l_bremen_hannover', 'EDFA', target_gain=9.1)
        l_bremen_hannover.add_span(s2_l_bremen_hannover, amp2_l_bremen_hannover)

        boost_hannover_bremen = net.add_amplifier('boost_hannover_bremen', 'EDFA', target_gain=17.0, boost=True)
        l_hannover_bremen = net.add_link(name_to_roadm['roadm_hannover'],
                                         name_to_roadm['roadm_bremen'],
                                         boost_amp=boost_hannover_bremen)
        s1_l_hannover_bremen = Span('SMF', 80)
        amp1_l_hannover_bremen = net.add_amplifier('amp1_l_hannover_bremen', 'EDFA', target_gain=17.6)
        l_hannover_bremen.add_span(s1_l_hannover_bremen, amp1_l_hannover_bremen)
        s2_l_hannover_bremen = Span('SMF', 41.3)
        amp2_l_hannover_bremen = net.add_amplifier('amp2_l_hannover_bremen', 'EDFA', target_gain=9.1)
        l_hannover_bremen.add_span(s2_l_hannover_bremen, amp2_l_hannover_bremen)

        # Link between Bremen and Essen - 278.5 km
        # and the bidirectional (independent) link
        boost_bremen_essen = net.add_amplifier('boost_bremen_essen', 'EDFA', target_gain=17.0, boost=True)
        l_bremen_essen = net.add_link(name_to_roadm['roadm_bremen'],
                                      name_to_roadm['roadm_essen'],
                                      boost_amp=boost_bremen_essen)
        s1_l_bremen_essen = Span('SMF', 80)
        amp1_l_bremen_essen = net.add_amplifier('amp1_l_bremen_essen', 'EDFA', target_gain=17.6)
        l_bremen_essen.add_span(s1_l_bremen_essen, amp1_l_bremen_essen)
        s2_l_bremen_essen = Span('SMF', 80)
        amp2_l_bremen_essen = net.add_amplifier('amp2_l_bremen_essen', 'EDFA', target_gain=17.6)
        l_bremen_essen.add_span(s2_l_bremen_essen, amp2_l_bremen_essen)
        s3_l_bremen_essen = Span('SMF', 80)
        amp3_l_bremen_essen = net.add_amplifier('amp3_l_bremen_essen', 'EDFA', target_gain=17.6)
        l_bremen_essen.add_span(s3_l_bremen_essen, amp3_l_bremen_essen)
        s4_l_bremen_essen = Span('SMF', 38.5)
        amp4_l_bremen_essen = net.add_amplifier('amp4_l_bremen_essen', 'EDFA', target_gain=8.5)
        l_bremen_essen.add_span(s4_l_bremen_essen, amp4_l_bremen_essen)

        boost_essen_bremen = net.add_amplifier('boost_essen_bremen', 'EDFA', target_gain=17.0, boost=True)
        l_essen_bremen = net.add_link(name_to_roadm['roadm_essen'],
                                      name_to_roadm['roadm_bremen'],
                                      boost_amp=boost_essen_bremen)
        s1_l_essen_bremen = Span('SMF', 80)
        amp1_l_essen_bremen = net.add_amplifier('amp1_l_essen_bremen', 'EDFA', target_gain=17.6)
        l_essen_bremen.add_span(s1_l_essen_bremen, amp1_l_essen_bremen)
        s2_l_essen_bremen = Span('SMF', 80)
        amp2_l_essen_bremen = net.add_amplifier('amp2_l_essen_bremen', 'EDFA', target_gain=17.6)
        l_essen_bremen.add_span(s2_l_essen_bremen, amp2_l_essen_bremen)
        s3_l_essen_bremen = Span('SMF', 80)
        amp3_l_essen_bremen = net.add_amplifier('amp3_l_essen_bremen', 'EDFA', target_gain=17.6)
        l_essen_bremen.add_span(s3_l_essen_bremen, amp3_l_essen_bremen)
        s4_l_essen_bremen = Span('SMF', 38.5)
        amp4_l_essen_bremen = net.add_amplifier('amp4_l_essen_bremen', 'EDFA', target_gain=8.5)
        l_essen_bremen.add_span(s4_l_essen_bremen, amp4_l_essen_bremen)

        # Link between Dortmund and Essen - 37.4 km
        # and the bidirectional (independent) link
        boost_dortmund_essen = net.add_amplifier('boost_dortmund_essen', 'EDFA', target_gain=17.0, boost=True)
        l_dortmund_essen = net.add_link(name_to_roadm['roadm_dortmund'],
                                        name_to_roadm['roadm_essen'],
                                        boost_amp=boost_dortmund_essen)
        s1_l_dortmund_essen = Span('SMF', 37.4)
        amp1_l_dortmund_essen = net.add_amplifier('amp1_l_dortmund_essen', 'EDFA', target_gain=8.2)
        l_dortmund_essen.add_span(s1_l_dortmund_essen, amp1_l_dortmund_essen)

        boost_essen_dortmund = net.add_amplifier('boost_essen_dortmund', 'EDFA', target_gain=17.0, boost=True)
        l_essen_dortmund = net.add_link(name_to_roadm['roadm_essen'],
                                        name_to_roadm['roadm_dortmund'],
                                        boost_amp=boost_essen_dortmund)
        s1_l_essen_dortmund = Span('SMF', 37.4)
        amp1_l_essen_dortmund = net.add_amplifier('amp1_l_essen_dortmund', 'EDFA', target_gain=8.2)
        l_essen_dortmund.add_span(s1_l_essen_dortmund, amp1_l_essen_dortmund)

        # Link between Dortmund and Hannover - 220.4 km
        # and the bidirectional (independent) link
        boost_dortmund_hannover = net.add_amplifier('boost_dortmund_hannover', 'EDFA', target_gain=17.0, boost=True)
        l_dortmund_hannover = net.add_link(name_to_roadm['roadm_dortmund'],
                                           name_to_roadm['roadm_hannover'],
                                           boost_amp=boost_dortmund_hannover)
        s1_l_dortmund_hannover = Span('SMF', 80)
        amp1_l_dortmund_hannover = net.add_amplifier('amp1_l_dortmund_hannover', 'EDFA', target_gain=17.6)
        l_dortmund_hannover.add_span(s1_l_dortmund_hannover, amp1_l_dortmund_hannover)
        s2_l_dortmund_hannover = Span('SMF', 80)
        amp2_l_dortmund_hannover = net.add_amplifier('amp2_l_dortmund_hannover', 'EDFA', target_gain=17.6)
        l_dortmund_hannover.add_span(s2_l_dortmund_hannover, amp2_l_dortmund_hannover)
        s3_l_dortmund_hannover = Span('SMF', 60.4)
        amp3_l_dortmund_hannover = net.add_amplifier('amp3_l_dortmund_hannover', 'EDFA', target_gain=13.3)
        l_dortmund_hannover.add_span(s3_l_dortmund_hannover, amp3_l_dortmund_hannover)

        boost_hannover_dortmund = net.add_amplifier('boost_hannover_dortmund', 'EDFA', target_gain=17.0, boost=True)
        l_hannover_dortmund = net.add_link(name_to_roadm['roadm_hannover'],
                                           name_to_roadm['roadm_dortmund'],
                                           boost_amp=boost_hannover_dortmund)
        s1_l_hannover_dortmund = Span('SMF', 80)
        amp1_l_hannover_dortmund = net.add_amplifier('amp1_l_hannover_dortmund', 'EDFA', target_gain=17.6)
        l_hannover_dortmund.add_span(s1_l_hannover_dortmund, amp1_l_hannover_dortmund)
        s2_l_hannover_dortmund = Span('SMF', 80)
        amp2_l_hannover_dortmund = net.add_amplifier('amp2_l_hannover_dortmund', 'EDFA', target_gain=17.6)
        l_hannover_dortmund.add_span(s2_l_hannover_dortmund, amp2_l_hannover_dortmund)
        s3_l_hannover_dortmund = Span('SMF', 60.4)
        amp3_l_hannover_dortmund = net.add_amplifier('amp3_l_hannover_dortmund', 'EDFA', target_gain=13.3)
        l_hannover_dortmund.add_span(s3_l_hannover_dortmund, amp3_l_hannover_dortmund)

        # Link between Dortmund and Koln - 84.3 km
        # and the bidirectional (independent) link
        boost_dortmund_koln = net.add_amplifier('boost_dortmund_koln', 'EDFA', target_gain=17.0, boost=True)
        l_dortmund_koln = net.add_link(name_to_roadm['roadm_dortmund'],
                                       name_to_roadm['roadm_koln'],
                                       boost_amp=boost_dortmund_koln)
        s1_l_dortmund_koln = Span('SMF', 84.3)
        amp1_l_dortmund_koln = net.add_amplifier('amp1_l_dortmund_koln', 'EDFA', target_gain=18.6)
        l_dortmund_koln.add_span(s1_l_dortmund_koln, amp1_l_dortmund_koln)

        boost_koln_dortmund = net.add_amplifier('boost_koln_dortmund', 'EDFA', target_gain=17.0, boost=True)
        l_koln_dortmund = net.add_link(name_to_roadm['roadm_koln'],
                                       name_to_roadm['roadm_dortmund'],
                                       boost_amp=boost_koln_dortmund)
        s1_l_koln_dortmund = Span('SMF', 1000)  # 84.3
        amp1_l_koln_dortmund = net.add_amplifier('amp1_l_koln_dortmund', 'EDFA', target_gain=18.6)
        l_koln_dortmund.add_span(s1_l_koln_dortmund, amp1_l_koln_dortmund)

        # Link between Dusseldorf and Essen - 36.9 km
        # and the bidirectional (independent) link
        boost_dusseldorf_essen = net.add_amplifier('boost_dusseldorf_essen', 'EDFA', target_gain=17.0, boost=True)
        l_dusseldorf_essen = net.add_link(name_to_roadm['roadm_dusseldorf'],
                                          name_to_roadm['roadm_essen'],
                                          boost_amp=boost_dusseldorf_essen)
        s1_l_dusseldorf_essen = Span('SMF', 36.9)
        amp1_l_dusseldorf_essen = net.add_amplifier('amp1_l_dusseldorf_essen', 'EDFA', target_gain=8.1)
        l_dusseldorf_essen.add_span(s1_l_dusseldorf_essen, amp1_l_dusseldorf_essen)

        boost_essen_dusseldorf = net.add_amplifier('boost_essen_dusseldorf', 'EDFA', target_gain=17.0, boost=True)
        l_essen_dusseldorf = net.add_link(name_to_roadm['roadm_essen'],
                                          name_to_roadm['roadm_dusseldorf'],
                                          boost_amp=boost_essen_dusseldorf)
        s1_l_essen_dusseldorf = Span('SMF', 36.9)
        amp1_l_essen_dusseldorf = net.add_amplifier('amp1_l_essen_dusseldorf', 'EDFA', target_gain=8.1)
        l_essen_dusseldorf.add_span(s1_l_essen_dusseldorf, amp1_l_essen_dusseldorf)

        # Link between Dusseldorf and Koln - 40.9 km
        # and the bidirectional (independent) link
        boost_dusseldorf_koln = net.add_amplifier('boost_dusseldorf_koln', 'EDFA', target_gain=17.0, boost=True)
        l_dusseldorf_koln = net.add_link(name_to_roadm['roadm_dusseldorf'],
                                         name_to_roadm['roadm_koln'],
                                         boost_amp=boost_dusseldorf_koln)
        s1_l_dusseldorf_koln = Span('SMF', 40.9)
        amp1_l_dusseldorf_koln = net.add_amplifier('amp1_l_dusseldorf_koln', 'EDFA', target_gain=9)
        l_dusseldorf_koln.add_span(s1_l_dusseldorf_koln, amp1_l_dusseldorf_koln)

        boost_koln_dusseldorf = net.add_amplifier('boost_koln_dusseldorf', 'EDFA', target_gain=17.0, boost=True)
        l_koln_dusseldorf = net.add_link(name_to_roadm['roadm_koln'],
                                         name_to_roadm['roadm_dusseldorf'],
                                         boost_amp=boost_koln_dusseldorf)
        s1_l_koln_dusseldorf = Span('SMF', 1000)  # 40.9
        amp1_l_koln_dusseldorf = net.add_amplifier('amp1_l_koln_dusseldorf', 'EDFA', target_gain=9)
        l_koln_dusseldorf.add_span(s1_l_koln_dusseldorf, amp1_l_koln_dusseldorf)

        # Link between Frankfurt and Hannover - 313.9 km
        # and the bidirectional (independent) link
        boost_frankfurt_hannover = net.add_amplifier('boost_frankfurt_hannover', 'EDFA', target_gain=17.0, boost=True)
        l_frankfurt_hannover = net.add_link(name_to_roadm['roadm_frankfurt'],
                                            name_to_roadm['roadm_hannover'],
                                            boost_amp=boost_frankfurt_hannover)
        s1_l_frankfurt_hannover = Span('SMF', 80)
        amp1_l_frankfurt_hannover = net.add_amplifier('amp1_l_frankfurt_hannover', 'EDFA', target_gain=17.6)
        l_frankfurt_hannover.add_span(s1_l_frankfurt_hannover, amp1_l_frankfurt_hannover)
        s2_l_frankfurt_hannover = Span('SMF', 80)
        amp2_l_frankfurt_hannover = net.add_amplifier('amp2_l_frankfurt_hannover', 'EDFA', target_gain=17.6)
        l_frankfurt_hannover.add_span(s2_l_frankfurt_hannover, amp2_l_frankfurt_hannover)
        s3_l_frankfurt_hannover = Span('SMF', 80)
        amp3_l_frankfurt_hannover = net.add_amplifier('amp3_l_frankfurt_hannover', 'EDFA', target_gain=17.6)
        l_frankfurt_hannover.add_span(s3_l_frankfurt_hannover, amp3_l_frankfurt_hannover)
        s4_l_frankfurt_hannover = Span('SMF', 73.9)
        amp4_l_frankfurt_hannover = net.add_amplifier('amp4_l_frankfurt_hannover', 'EDFA', target_gain=16.3)
        l_frankfurt_hannover.add_span(s4_l_frankfurt_hannover, amp4_l_frankfurt_hannover)

        boost_hannover_frankfurt = net.add_amplifier('boost_hannover_frankfurt', 'EDFA', target_gain=17.0, boost=True)
        l_hannover_frankfurt = net.add_link(name_to_roadm['roadm_hannover'],
                                            name_to_roadm['roadm_frankfurt'],
                                            boost_amp=boost_hannover_frankfurt)
        s1_l_hannover_frankfurt = Span('SMF', 80)
        amp1_l_hannover_frankfurt = net.add_amplifier('amp1_l_hannover_frankfurt', 'EDFA', target_gain=17.6)
        l_hannover_frankfurt.add_span(s1_l_hannover_frankfurt, amp1_l_hannover_frankfurt)
        s2_l_hannover_frankfurt = Span('SMF', 80)
        amp2_l_hannover_frankfurt = net.add_amplifier('amp2_l_hannover_frankfurt', 'EDFA', target_gain=17.6)
        l_hannover_frankfurt.add_span(s2_l_hannover_frankfurt, amp2_l_hannover_frankfurt)
        s3_l_hannover_frankfurt = Span('SMF', 80)
        amp3_l_hannover_frankfurt = net.add_amplifier('amp3_l_hannover_frankfurt', 'EDFA', target_gain=17.6)
        l_hannover_frankfurt.add_span(s3_l_hannover_frankfurt, amp3_l_hannover_frankfurt)
        s4_l_hannover_frankfurt = Span('SMF', 73.9)
        amp4_l_hannover_frankfurt = net.add_amplifier('amp4_l_hannover_frankfurt', 'EDFA', target_gain=16.3)
        l_hannover_frankfurt.add_span(s4_l_hannover_frankfurt, amp4_l_hannover_frankfurt)

        # Link between Frankfurt and Koln - 182 km
        # and the bidirectional (independent) link
        boost_frankfurt_koln = net.add_amplifier('boost_frankfurt_koln', 'EDFA', target_gain=17.0, boost=True)
        l_frankfurt_koln = net.add_link(name_to_roadm['roadm_frankfurt'],
                                        name_to_roadm['roadm_koln'],
                                        boost_amp=boost_frankfurt_koln)
        s1_l_frankfurt_koln = Span('SMF', 80)
        amp1_l_frankfurt_koln = net.add_amplifier('amp1_l_frankfurt_koln', 'EDFA', target_gain=17.6)
        l_frankfurt_koln.add_span(s1_l_frankfurt_koln, amp1_l_frankfurt_koln)
        s2_l_frankfurt_koln = Span('SMF', 80)
        amp2_l_frankfurt_koln = net.add_amplifier('amp2_l_frankfurt_koln', 'EDFA', target_gain=17.6)
        l_frankfurt_koln.add_span(s2_l_frankfurt_koln, amp2_l_frankfurt_koln)
        s3_l_frankfurt_koln = Span('SMF', 22)
        amp3_l_frankfurt_koln = net.add_amplifier('amp3_l_frankfurt_koln', 'EDFA', target_gain=4.9)
        l_frankfurt_koln.add_span(s3_l_frankfurt_koln, amp3_l_frankfurt_koln)

        boost_koln_frankfurt = net.add_amplifier('boost_koln_frankfurt', 'EDFA', target_gain=17.0, boost=True)
        l_koln_frankfurt = net.add_link(name_to_roadm['roadm_koln'],
                                        name_to_roadm['roadm_frankfurt'],
                                        boost_amp=boost_koln_frankfurt)
        net.add_monitor('verification_opm0', link=None,
                        span=None, amplifier=boost_koln_frankfurt)

        s1_l_koln_frankfurt = Span('SMF', 80)
        amp1_l_koln_frankfurt = net.add_amplifier('amp1_l_koln_frankfurt', 'EDFA', target_gain=17.6)
        l_koln_frankfurt.add_span(s1_l_koln_frankfurt, amp1_l_koln_frankfurt)
        net.add_monitor('verification_opm1', link=l_koln_frankfurt,
                        span=s1_l_koln_frankfurt, amplifier=amp1_l_koln_frankfurt)

        s2_l_koln_frankfurt = Span('SMF', 80)
        amp2_l_koln_frankfurt = net.add_amplifier('amp2_l_koln_frankfurt', 'EDFA', target_gain=17.6)
        l_koln_frankfurt.add_span(s2_l_koln_frankfurt, amp2_l_koln_frankfurt)
        net.add_monitor('verification_opm2', link=l_koln_frankfurt,
                        span=s2_l_koln_frankfurt, amplifier=amp2_l_koln_frankfurt)

        s3_l_koln_frankfurt = Span('SMF', 80)
        amp3_l_koln_frankfurt = net.add_amplifier('amp3_l_koln_frankfurt', 'EDFA', target_gain=17.6)
        l_koln_frankfurt.add_span(s3_l_koln_frankfurt, amp3_l_koln_frankfurt)
        net.add_monitor('verification_opm3', link=l_koln_frankfurt,
                        span=s3_l_koln_frankfurt, amplifier=amp3_l_koln_frankfurt)

        s4_l_koln_frankfurt = Span('SMF', 80)
        amp4_l_koln_frankfurt = net.add_amplifier('amp4_l_koln_frankfurt', 'EDFA', target_gain=17.6)
        l_koln_frankfurt.add_span(s4_l_koln_frankfurt, amp4_l_koln_frankfurt)
        net.add_monitor('verification_opm4', link=l_koln_frankfurt,
                        span=s4_l_koln_frankfurt, amplifier=amp4_l_koln_frankfurt)
        
        s5_l_koln_frankfurt = Span('SMF', 80)
        amp5_l_koln_frankfurt = net.add_amplifier('amp5_l_koln_frankfurt', 'EDFA', target_gain=17.6)
        l_koln_frankfurt.add_span(s5_l_koln_frankfurt, amp5_l_koln_frankfurt)
        net.add_monitor('verification_opm5', link=l_koln_frankfurt,
                        span=s5_l_koln_frankfurt, amplifier=amp5_l_koln_frankfurt)

        # Link between Frankfurt and Leipzig - 313.9 km
        # and the bidirectional (independent) link
        boost_frankfurt_leipzig = net.add_amplifier('boost_frankfurt_leipzig', 'EDFA', target_gain=17.0, boost=True)
        l_frankfurt_leipzig = net.add_link(name_to_roadm['roadm_frankfurt'],
                                           name_to_roadm['roadm_leipzig'],
                                           boost_amp=boost_frankfurt_leipzig)
        s1_l_frankfurt_leipzig = Span('SMF', 80)
        amp1_l_frankfurt_leipzig = net.add_amplifier('amp1_l_frankfurt_leipzig', 'EDFA', target_gain=17.6)
        l_frankfurt_leipzig.add_span(s1_l_frankfurt_leipzig, amp1_l_frankfurt_leipzig)
        s2_l_frankfurt_leipzig = Span('SMF', 80)
        amp2_l_frankfurt_leipzig = net.add_amplifier('amp2_l_frankfurt_leipzig', 'EDFA', target_gain=17.6)
        l_frankfurt_leipzig.add_span(s2_l_frankfurt_leipzig, amp2_l_frankfurt_leipzig)
        s3_l_frankfurt_leipzig = Span('SMF', 80)
        amp3_l_frankfurt_leipzig = net.add_amplifier('amp3_l_frankfurt_leipzig', 'EDFA', target_gain=17.6)
        l_frankfurt_leipzig.add_span(s3_l_frankfurt_leipzig, amp3_l_frankfurt_leipzig)
        s4_l_frankfurt_leipzig = Span('SMF', 73.9)
        amp4_l_frankfurt_leipzig = net.add_amplifier('amp4_l_frankfurt_leipzig', 'EDFA', target_gain=16.3)
        l_frankfurt_leipzig.add_span(s4_l_frankfurt_leipzig, amp4_l_frankfurt_leipzig)

        boost_leipzig_frankfurt = net.add_amplifier('boost_leipzig_frankfurt', 'EDFA', target_gain=17.0, boost=True)
        l_leipzig_frankfurt = net.add_link(name_to_roadm['roadm_leipzig'],
                                           name_to_roadm['roadm_frankfurt'],
                                           boost_amp=boost_leipzig_frankfurt)
        s1_l_leipzig_frankfurt = Span('SMF', 80)
        amp1_l_leipzig_frankfurt = net.add_amplifier('amp1_l_leipzig_frankfurt', 'EDFA', target_gain=17.6)
        l_leipzig_frankfurt.add_span(s1_l_leipzig_frankfurt, amp1_l_leipzig_frankfurt)
        s2_l_leipzig_frankfurt = Span('SMF', 80)
        amp2_l_leipzig_frankfurt = net.add_amplifier('amp2_l_leipzig_frankfurt', 'EDFA', target_gain=17.6)
        l_leipzig_frankfurt.add_span(s2_l_leipzig_frankfurt, amp2_l_leipzig_frankfurt)
        s3_l_leipzig_frankfurt = Span('SMF', 80)
        amp3_l_leipzig_frankfurt = net.add_amplifier('amp3_l_leipzig_frankfurt', 'EDFA', target_gain=17.6)
        l_leipzig_frankfurt.add_span(s3_l_leipzig_frankfurt, amp3_l_leipzig_frankfurt)
        s4_l_leipzig_frankfurt = Span('SMF', 73.9)
        amp4_l_leipzig_frankfurt = net.add_amplifier('amp4_l_leipzig_frankfurt', 'EDFA', target_gain=16.3)
        l_leipzig_frankfurt.add_span(s4_l_leipzig_frankfurt, amp4_l_leipzig_frankfurt)

        # Link between Frankfurt and Nurnberg - 224.1 km
        # and the bidirectional (independent) link
        boost_frankfurt_nurnberg = net.add_amplifier('boost_frankfurt_nurnberg', 'EDFA', target_gain=17.0, boost=True)
        l_frankfurt_nurnberg = net.add_link(name_to_roadm['roadm_frankfurt'],
                                            name_to_roadm['roadm_nurnberg'],
                                            boost_amp=boost_frankfurt_nurnberg)
        net.add_monitor('verification_opm6', link=None,
                        span=None, amplifier=boost_frankfurt_nurnberg)
        s1_l_frankfurt_nurnberg = Span('SMF', 80)
        amp1_l_frankfurt_nurnberg = net.add_amplifier('amp1_l_frankfurt_nurnberg', 'EDFA', target_gain=17.6)
        l_frankfurt_nurnberg.add_span(s1_l_frankfurt_nurnberg, amp1_l_frankfurt_nurnberg)
        net.add_monitor('verification_opm7', link=l_frankfurt_nurnberg,
                        span=s1_l_frankfurt_nurnberg, amplifier=amp1_l_frankfurt_nurnberg)
        s2_l_frankfurt_nurnberg = Span('SMF', 80)
        amp2_l_frankfurt_nurnberg = net.add_amplifier('amp2_l_frankfurt_nurnberg', 'EDFA', target_gain=17.6)
        l_frankfurt_nurnberg.add_span(s2_l_frankfurt_nurnberg, amp2_l_frankfurt_nurnberg)
        net.add_monitor('verification_opm8', link=l_frankfurt_nurnberg,
                        span=s2_l_frankfurt_nurnberg, amplifier=amp2_l_frankfurt_nurnberg)
        s3_l_frankfurt_nurnberg = Span('SMF', 80)
        amp3_l_frankfurt_nurnberg = net.add_amplifier('amp3_l_frankfurt_nurnberg', 'EDFA', target_gain=17.6)
        l_frankfurt_nurnberg.add_span(s3_l_frankfurt_nurnberg, amp3_l_frankfurt_nurnberg)
        net.add_monitor('verification_opm9', link=l_frankfurt_nurnberg,
                        span=s3_l_frankfurt_nurnberg, amplifier=amp3_l_frankfurt_nurnberg)
        s4_l_frankfurt_nurnberg = Span('SMF', 80)
        amp4_l_frankfurt_nurnberg = net.add_amplifier('amp4_l_frankfurt_nurnberg', 'EDFA', target_gain=17.6)
        l_frankfurt_nurnberg.add_span(s4_l_frankfurt_nurnberg, amp4_l_frankfurt_nurnberg)
        net.add_monitor('verification_opm10', link=l_frankfurt_nurnberg,
                        span=s4_l_frankfurt_nurnberg, amplifier=amp4_l_frankfurt_nurnberg)
        s5_l_frankfurt_nurnberg = Span('SMF', 80)
        amp5_l_frankfurt_nurnberg = net.add_amplifier('amp5_l_frankfurt_nurnberg', 'EDFA', target_gain=17.6)
        l_frankfurt_nurnberg.add_span(s5_l_frankfurt_nurnberg, amp5_l_frankfurt_nurnberg)
        net.add_monitor('verification_opm11', link=l_frankfurt_nurnberg,
                        span=s5_l_frankfurt_nurnberg, amplifier=amp5_l_frankfurt_nurnberg)

        boost_nurnberg_frankfurt = net.add_amplifier('boost_nurnberg_frankfurt', 'EDFA', target_gain=17.0, boost=True)
        l_nurnberg_frankfurt = net.add_link(name_to_roadm['roadm_nurnberg'],
                                            name_to_roadm['roadm_frankfurt'],
                                            boost_amp=boost_nurnberg_frankfurt)
        s1_l_nurnberg_frankfurt = Span('SMF', 80)
        amp1_l_nurnberg_frankfurt = net.add_amplifier('amp1_l_nurnberg_frankfurt', 'EDFA', target_gain=17.6)
        l_nurnberg_frankfurt.add_span(s1_l_nurnberg_frankfurt, amp1_l_nurnberg_frankfurt)
        s2_l_nurnberg_frankfurt = Span('SMF', 80)
        amp2_l_nurnberg_frankfurt = net.add_amplifier('amp2_l_nurnberg_frankfurt', 'EDFA', target_gain=17.6)
        l_nurnberg_frankfurt.add_span(s2_l_nurnberg_frankfurt, amp2_l_nurnberg_frankfurt)
        s3_l_nurnberg_frankfurt = Span('SMF', 64.1)
        amp3_l_nurnberg_frankfurt = net.add_amplifier('amp3_l_nurnberg_frankfurt', 'EDFA', target_gain=14.1)
        l_nurnberg_frankfurt.add_span(s3_l_nurnberg_frankfurt, amp3_l_nurnberg_frankfurt)

        # Link between Frankfurt and Stuttgart - 207.4 km
        # and the bidirectional (independent) link
        boost_frankfurt_stuttgart = net.add_amplifier('boost_frankfurt_stuttgart', 'EDFA', target_gain=17.0, boost=True)
        l_frankfurt_stuttgart = net.add_link(name_to_roadm['roadm_frankfurt'],
                                             name_to_roadm['roadm_stuttgart'],
                                             boost_amp=boost_frankfurt_stuttgart)
        s1_l_frankfurt_stuttgart = Span('SMF', 1000)  # 80
        amp1_l_frankfurt_stuttgart = net.add_amplifier('amp1_l_frankfurt_stuttgart', 'EDFA', target_gain=17.6)
        l_frankfurt_stuttgart.add_span(s1_l_frankfurt_stuttgart, amp1_l_frankfurt_stuttgart)
        s2_l_frankfurt_stuttgart = Span('SMF', 80)
        amp2_l_frankfurt_stuttgart = net.add_amplifier('amp2_l_frankfurt_stuttgart', 'EDFA', target_gain=17.6)
        l_frankfurt_stuttgart.add_span(s2_l_frankfurt_stuttgart, amp2_l_frankfurt_stuttgart)
        s3_l_frankfurt_stuttgart = Span('SMF', 47.4)
        amp3_l_frankfurt_stuttgart = net.add_amplifier('amp3_l_frankfurt_stuttgart', 'EDFA', target_gain=10.4)
        l_frankfurt_stuttgart.add_span(s3_l_frankfurt_stuttgart, amp3_l_frankfurt_stuttgart)

        boost_stuttgart_frankfurt = net.add_amplifier('boost_stuttgart_frankfurt', 'EDFA', target_gain=17.0, boost=True)
        l_stuttgart_frankfurt = net.add_link(name_to_roadm['roadm_stuttgart'],
                                             name_to_roadm['roadm_frankfurt'],
                                             boost_amp=boost_stuttgart_frankfurt)
        s1_l_stuttgart_frankfurt = Span('SMF', 80)
        amp1_l_stuttgart_frankfurt = net.add_amplifier('amp1_l_stuttgart_frankfurt', 'EDFA', target_gain=17.6)
        l_stuttgart_frankfurt.add_span(s1_l_stuttgart_frankfurt, amp1_l_stuttgart_frankfurt)
        s2_l_stuttgart_frankfurt = Span('SMF', 80)
        amp2_l_stuttgart_frankfurt = net.add_amplifier('amp2_l_stuttgart_frankfurt', 'EDFA', target_gain=17.6)
        l_stuttgart_frankfurt.add_span(s2_l_stuttgart_frankfurt, amp2_l_stuttgart_frankfurt)
        s3_l_stuttgart_frankfurt = Span('SMF', 47.4)
        amp3_l_stuttgart_frankfurt = net.add_amplifier('amp3_l_stuttgart_frankfurt', 'EDFA', target_gain=10.4)
        l_stuttgart_frankfurt.add_span(s3_l_stuttgart_frankfurt, amp3_l_stuttgart_frankfurt)

        # Link between Hamburg and Hannover - 160.9 km
        # and the bidirectional (independent) link
        boost_hamburg_hannover = net.add_amplifier('boost_hamburg_hannover', 'EDFA', target_gain=17.0, boost=True)
        l_hamburg_hannover = net.add_link(name_to_roadm['roadm_hamburg'],
                                          name_to_roadm['roadm_hannover'],
                                          boost_amp=boost_hamburg_hannover)
        s1_l_hamburg_hannover = Span('SMF', 80)
        amp1_l_hamburg_hannover = net.add_amplifier('amp1_l_hamburg_hannover', 'EDFA', target_gain=17.6)
        l_hamburg_hannover.add_span(s1_l_hamburg_hannover, amp1_l_hamburg_hannover)
        s2_l_hamburg_hannover = Span('SMF', 80.9)
        amp2_l_hamburg_hannover = net.add_amplifier('amp2_l_hamburg_hannover', 'EDFA', target_gain=17.8)
        l_hamburg_hannover.add_span(s2_l_hamburg_hannover, amp2_l_hamburg_hannover)

        boost_hannover_hamburg = net.add_amplifier('boost_hannover_hamburg', 'EDFA', target_gain=17.0, boost=True)
        l_hannover_hamburg = net.add_link(name_to_roadm['roadm_hannover'],
                                          name_to_roadm['roadm_hamburg'],
                                          boost_amp=boost_hannover_hamburg)
        s1_l_hannover_hamburg = Span('SMF', 80)
        amp1_l_hannover_hamburg = net.add_amplifier('amp1_l_hannover_hamburg', 'EDFA', target_gain=17.6)
        l_hannover_hamburg.add_span(s1_l_hannover_hamburg, amp1_l_hannover_hamburg)
        s2_l_hannover_hamburg = Span('SMF', 80.9)
        amp2_l_hannover_hamburg = net.add_amplifier('amp2_l_hannover_hamburg', 'EDFA', target_gain=17.8)
        l_hannover_hamburg.add_span(s2_l_hannover_hamburg, amp2_l_hannover_hamburg)

        # Link between Hannover and Leipzig - 257.2 km
        # and the bidirectional (independent) link
        boost_hannover_leipzig = net.add_amplifier('boost_hannover_leipzig', 'EDFA', target_gain=17.0, boost=True)
        l_hannover_leipzig = net.add_link(name_to_roadm['roadm_hannover'],
                                          name_to_roadm['roadm_leipzig'],
                                          boost_amp=boost_hannover_leipzig)
        s1_l_hannover_leipzig = Span('SMF', 80)
        amp1_l_hannover_leipzig = net.add_amplifier('amp1_l_hannover_leipzig', 'EDFA', target_gain=17.6)
        l_hannover_leipzig.add_span(s1_l_hannover_leipzig, amp1_l_hannover_leipzig)
        s2_l_hannover_leipzig = Span('SMF', 80)
        amp2_l_hannover_leipzig = net.add_amplifier('amp2_l_hannover_leipzig', 'EDFA', target_gain=17.6)
        l_hannover_leipzig.add_span(s2_l_hannover_leipzig, amp2_l_hannover_leipzig)
        s3_l_hannover_leipzig = Span('SMF', 80)
        amp3_l_hannover_leipzig = net.add_amplifier('amp3_l_hannover_leipzig', 'EDFA', target_gain=17.6)
        l_hannover_leipzig.add_span(s3_l_hannover_leipzig, amp3_l_hannover_leipzig)
        s4_l_hannover_leipzig = Span('SMF', 17.2)
        amp4_l_hannover_leipzig = net.add_amplifier('amp4_l_hannover_leipzig', 'EDFA', target_gain=3.8)
        l_hannover_leipzig.add_span(s4_l_hannover_leipzig, amp4_l_hannover_leipzig)

        boost_leipzig_hannover = net.add_amplifier('boost_leipzig_hannover', 'EDFA', target_gain=17.0, boost=True)
        l_leipzig_hannover = net.add_link(name_to_roadm['roadm_leipzig'],
                                          name_to_roadm['roadm_hannover'],
                                          boost_amp=boost_leipzig_hannover)
        s1_l_leipzig_hannover = Span('SMF', 80)
        amp1_l_leipzig_hannover = net.add_amplifier('amp1_l_leipzig_hannover', 'EDFA', target_gain=17.6)
        l_leipzig_hannover.add_span(s1_l_leipzig_hannover, amp1_l_leipzig_hannover)
        s2_l_leipzig_hannover = Span('SMF', 80)
        amp2_l_leipzig_hannover = net.add_amplifier('amp2_l_leipzig_hannover', 'EDFA', target_gain=17.6)
        l_leipzig_hannover.add_span(s2_l_leipzig_hannover, amp2_l_leipzig_hannover)
        s3_l_leipzig_hannover = Span('SMF', 80)
        amp3_l_leipzig_hannover = net.add_amplifier('amp3_l_leipzig_hannover', 'EDFA', target_gain=17.6)
        l_leipzig_hannover.add_span(s3_l_leipzig_hannover, amp3_l_leipzig_hannover)
        s4_l_leipzig_hannover = Span('SMF', 17.2)
        amp4_l_leipzig_hannover = net.add_amplifier('amp4_l_leipzig_hannover', 'EDFA', target_gain=3.8)
        l_leipzig_hannover.add_span(s4_l_leipzig_hannover, amp4_l_leipzig_hannover)

        # Link between Leipzig and Nurnberg - 274.7 km
        # and the bidirectional (independent) link
        boost_leipzig_nurnberg = net.add_amplifier('boost_leipzig_nurnberg', 'EDFA', target_gain=17.0, boost=True)
        l_leipzig_nurnberg = net.add_link(name_to_roadm['roadm_leipzig'],
                                          name_to_roadm['roadm_nurnberg'],
                                          boost_amp=boost_leipzig_nurnberg)
        s1_l_leipzig_nurnberg = Span('SMF', 80)
        amp1_l_leipzig_nurnberg = net.add_amplifier('amp1_l_leipzig_nurnberg', 'EDFA', target_gain=17.6)
        l_leipzig_nurnberg.add_span(s1_l_leipzig_nurnberg, amp1_l_leipzig_nurnberg)
        s2_l_leipzig_nurnberg = Span('SMF', 80)
        amp2_l_leipzig_nurnberg = net.add_amplifier('amp2_l_leipzig_nurnberg', 'EDFA', target_gain=17.6)
        l_leipzig_nurnberg.add_span(s2_l_leipzig_nurnberg, amp2_l_leipzig_nurnberg)
        s3_l_leipzig_nurnberg = Span('SMF', 80)
        amp3_l_leipzig_nurnberg = net.add_amplifier('amp3_l_leipzig_nurnberg', 'EDFA', target_gain=17.6)
        l_leipzig_nurnberg.add_span(s3_l_leipzig_nurnberg, amp3_l_leipzig_nurnberg)
        s4_l_leipzig_nurnberg = Span('SMF', 34.7)
        amp4_l_leipzig_nurnberg = net.add_amplifier('amp4_l_leipzig_nurnberg', 'EDFA', target_gain=7.6)
        l_leipzig_nurnberg.add_span(s4_l_leipzig_nurnberg, amp4_l_leipzig_nurnberg)

        boost_nurnberg_leipzig = net.add_amplifier('boost_nurnberg_leipzig', 'EDFA', target_gain=17.0, boost=True)
        l_nurnberg_leipzig = net.add_link(name_to_roadm['roadm_nurnberg'],
                                          name_to_roadm['roadm_leipzig'],
                                          boost_amp=boost_nurnberg_leipzig)
        s1_l_nurnberg_leipzig = Span('SMF', 80)
        amp1_l_nurnberg_leipzig = net.add_amplifier('amp1_l_nurnberg_leipzig', 'EDFA', target_gain=17.6)
        l_nurnberg_leipzig.add_span(s1_l_nurnberg_leipzig, amp1_l_nurnberg_leipzig)
        s2_l_nurnberg_leipzig = Span('SMF', 80)
        amp2_l_nurnberg_leipzig = net.add_amplifier('amp2_l_nurnberg_leipzig', 'EDFA', target_gain=17.6)
        l_nurnberg_leipzig.add_span(s2_l_nurnberg_leipzig, amp2_l_nurnberg_leipzig)
        s3_l_nurnberg_leipzig = Span('SMF', 80)
        amp3_l_nurnberg_leipzig = net.add_amplifier('amp3_l_nurnberg_leipzig', 'EDFA', target_gain=17.6)
        l_nurnberg_leipzig.add_span(s3_l_nurnberg_leipzig, amp3_l_nurnberg_leipzig)
        s4_l_nurnberg_leipzig = Span('SMF', 34.7)
        amp4_l_nurnberg_leipzig = net.add_amplifier('amp4_l_nurnberg_leipzig', 'EDFA', target_gain=7.6)
        l_nurnberg_leipzig.add_span(s4_l_nurnberg_leipzig, amp4_l_nurnberg_leipzig)

        # Link between Munchen and Nurnberg - 180.8 km
        # and the bidirectional (independent) link
        boost_munchen_nurnberg = net.add_amplifier('boost_munchen_nurnberg', 'EDFA', target_gain=17.0, boost=True)
        l_munchen_nurnberg = net.add_link(name_to_roadm['roadm_munchen'],
                                          name_to_roadm['roadm_nurnberg'],
                                          boost_amp=boost_munchen_nurnberg)
        s1_l_munchen_nurnberg = Span('SMF', 80)
        amp1_l_munchen_nurnberg = net.add_amplifier('amp1_l_munchen_nurnberg', 'EDFA', target_gain=17.6)
        l_munchen_nurnberg.add_span(s1_l_munchen_nurnberg, amp1_l_munchen_nurnberg)
        s2_l_munchen_nurnberg = Span('SMF', 80)
        amp2_l_munchen_nurnberg = net.add_amplifier('amp2_l_munchen_nurnberg', 'EDFA', target_gain=17.6)
        l_munchen_nurnberg.add_span(s2_l_munchen_nurnberg, amp2_l_munchen_nurnberg)
        s3_l_munchen_nurnberg = Span('SMF', 20.8)
        amp3_l_munchen_nurnberg = net.add_amplifier('amp3_l_munchen_nurnberg', 'EDFA', target_gain=4.6)
        l_munchen_nurnberg.add_span(s3_l_munchen_nurnberg, amp3_l_munchen_nurnberg)

        boost_nurnberg_munchen = net.add_amplifier('boost_nurnberg_munchen', 'EDFA', target_gain=17.0, boost=True)
        l_nurnberg_munchen = net.add_link(name_to_roadm['roadm_nurnberg'],
                                          name_to_roadm['roadm_munchen'],
                                          boost_amp=boost_nurnberg_munchen)
        net.add_monitor('verification_opm12', link=None,
                        span=None, amplifier=boost_nurnberg_munchen)
        s1_l_nurnberg_munchen = Span('SMF', 80)
        amp1_l_nurnberg_munchen = net.add_amplifier('amp1_l_nurnberg_munchen', 'EDFA', target_gain=17.6)
        l_nurnberg_munchen.add_span(s1_l_nurnberg_munchen, amp1_l_nurnberg_munchen)
        net.add_monitor('verification_opm13', link=l_nurnberg_munchen,
                        span=s1_l_nurnberg_munchen, amplifier=amp1_l_nurnberg_munchen)
        s2_l_nurnberg_munchen = Span('SMF', 80)
        amp2_l_nurnberg_munchen = net.add_amplifier('amp2_l_nurnberg_munchen', 'EDFA', target_gain=17.6)
        l_nurnberg_munchen.add_span(s2_l_nurnberg_munchen, amp2_l_nurnberg_munchen)
        net.add_monitor('verification_opm14', link=l_nurnberg_munchen,
                        span=s2_l_nurnberg_munchen, amplifier=amp2_l_nurnberg_munchen)
        s3_l_nurnberg_munchen = Span('SMF', 80)
        amp3_l_nurnberg_munchen = net.add_amplifier('amp3_l_nurnberg_munchen', 'EDFA', target_gain=17.6)
        l_nurnberg_munchen.add_span(s3_l_nurnberg_munchen, amp3_l_nurnberg_munchen)
        net.add_monitor('verification_opm15', link=l_nurnberg_munchen,
                        span=s3_l_nurnberg_munchen, amplifier=amp3_l_nurnberg_munchen)
        s4_l_nurnberg_munchen = Span('SMF', 80)
        amp4_l_nurnberg_munchen = net.add_amplifier('amp4_l_nurnberg_munchen', 'EDFA', target_gain=17.6)
        l_nurnberg_munchen.add_span(s4_l_nurnberg_munchen, amp4_l_nurnberg_munchen)
        net.add_monitor('verification_opm16', link=l_nurnberg_munchen,
                        span=s4_l_nurnberg_munchen, amplifier=amp4_l_nurnberg_munchen)
        s5_l_nurnberg_munchen = Span('SMF', 80)
        amp5_l_nurnberg_munchen = net.add_amplifier('amp5_l_nurnberg_munchen', 'EDFA', target_gain=17.6)
        l_nurnberg_munchen.add_span(s5_l_nurnberg_munchen, amp5_l_nurnberg_munchen)
        net.add_monitor('verification_opm17', link=l_nurnberg_munchen,
                        span=s5_l_nurnberg_munchen, amplifier=amp5_l_nurnberg_munchen)

        # Link between Munchen and Ulm - 145.6 km
        # and the bidirectional (independent) link
        boost_munchen_ulm = net.add_amplifier('boost_munchen_ulm', 'EDFA', target_gain=17.0, boost=True)
        l_munchen_ulm = net.add_link(name_to_roadm['roadm_munchen'],
                                     name_to_roadm['roadm_ulm'],
                                     boost_amp=boost_munchen_ulm)
        s1_l_munchen_ulm = Span('SMF', 80)
        amp1_l_munchen_ulm = net.add_amplifier('amp1_l_munchen_ulm', 'EDFA', target_gain=17.6)
        l_munchen_ulm.add_span(s1_l_munchen_ulm, amp1_l_munchen_ulm)
        s2_l_munchen_ulm = Span('SMF', 65.6)
        amp2_l_munchen_ulm = net.add_amplifier('amp2_l_munchen_ulm', 'EDFA', target_gain=14.4)
        l_munchen_ulm.add_span(s2_l_munchen_ulm, amp2_l_munchen_ulm)

        boost_ulm_munchen = net.add_amplifier('boost_ulm_munchen', 'EDFA', target_gain=17.0, boost=True)
        l_ulm_munchen = net.add_link(name_to_roadm['roadm_ulm'],
                                     name_to_roadm['roadm_munchen'],
                                     boost_amp=boost_ulm_munchen)
        s1_l_ulm_munchen = Span('SMF', 80)
        amp1_l_ulm_munchen = net.add_amplifier('amp1_l_ulm_munchen', 'EDFA', target_gain=17.6)
        l_ulm_munchen.add_span(s1_l_ulm_munchen, amp1_l_ulm_munchen)
        s2_l_ulm_munchen = Span('SMF', 65.6)
        amp2_l_ulm_munchen = net.add_amplifier('amp2_l_ulm_munchen', 'EDFA', target_gain=14.4)
        l_ulm_munchen.add_span(s2_l_ulm_munchen, amp2_l_ulm_munchen)

        # Link between Nurnberg and Stuttgart - 188.7 km
        # and the bidirectional (independent) link
        boost_nurnberg_stuttgart = net.add_amplifier('boost_nurnberg_stuttgart', 'EDFA', target_gain=17.0, boost=True)
        l_nurnberg_stuttgart = net.add_link(name_to_roadm['roadm_nurnberg'],
                                            name_to_roadm['roadm_stuttgart'],
                                            boost_amp=boost_nurnberg_stuttgart)
        s1_l_nurnberg_stuttgart = Span('SMF', 80)
        amp1_l_nurnberg_stuttgart = net.add_amplifier('amp1_l_nurnberg_stuttgart', 'EDFA', target_gain=17.6)
        l_nurnberg_stuttgart.add_span(s1_l_nurnberg_stuttgart, amp1_l_nurnberg_stuttgart)
        s2_l_nurnberg_stuttgart = Span('SMF', 80)
        amp2_l_nurnberg_stuttgart = net.add_amplifier('amp2_l_nurnberg_stuttgart', 'EDFA', target_gain=17.6)
        l_nurnberg_stuttgart.add_span(s2_l_nurnberg_stuttgart, amp2_l_nurnberg_stuttgart)
        s3_l_nurnberg_stuttgart = Span('SMF', 28.7)
        amp3_l_nurnberg_stuttgart = net.add_amplifier('amp3_l_nurnberg_stuttgart', 'EDFA', target_gain=3.3)
        l_nurnberg_stuttgart.add_span(s3_l_nurnberg_stuttgart, amp3_l_nurnberg_stuttgart)

        boost_stuttgart_nurnberg = net.add_amplifier('boost_stuttgart_nurnberg', 'EDFA', target_gain=17.0, boost=True)
        l_stuttgart_nurnberg = net.add_link(name_to_roadm['roadm_stuttgart'],
                                            name_to_roadm['roadm_nurnberg'],
                                            boost_amp=boost_stuttgart_nurnberg)
        s1_l_stuttgart_nurnberg = Span('SMF', 80)
        amp1_l_stuttgart_nurnberg = net.add_amplifier('amp1_l_stuttgart_nurnberg', 'EDFA', target_gain=17.6)
        l_stuttgart_nurnberg.add_span(s1_l_stuttgart_nurnberg, amp1_l_stuttgart_nurnberg)
        s2_l_stuttgart_nurnberg = Span('SMF', 80)
        amp2_l_stuttgart_nurnberg = net.add_amplifier('amp2_l_stuttgart_nurnberg', 'EDFA', target_gain=17.6)
        l_stuttgart_nurnberg.add_span(s2_l_stuttgart_nurnberg, amp2_l_stuttgart_nurnberg)
        s3_l_stuttgart_nurnberg = Span('SMF', 28.7)
        amp3_l_stuttgart_nurnberg = net.add_amplifier('amp3_l_stuttgart_nurnberg', 'EDFA', target_gain=3.3)
        l_stuttgart_nurnberg.add_span(s3_l_stuttgart_nurnberg, amp3_l_stuttgart_nurnberg)

        # Link between Stuttgart and Ulm - 87.1 km
        # and the bidirectional (independent) link
        boost_stuttgart_ulm = net.add_amplifier('boost_stuttgart_ulm', 'EDFA', target_gain=17.0, boost=True)
        l_stuttgart_ulm = net.add_link(name_to_roadm['roadm_stuttgart'],
                                       name_to_roadm['roadm_ulm'], boost_amp=boost_stuttgart_ulm)
        s1_l_stuttgart_ulm = Span('SMF', 87.1)
        amp1_l_stuttgart_ulm = net.add_amplifier('amp1_l_stuttgart_ulm', 'EDFA', target_gain=19.2)
        l_stuttgart_ulm.add_span(s1_l_stuttgart_ulm, amp1_l_stuttgart_ulm)

        boost_ulm_stuttgart = net.add_amplifier('boost_ulm_stuttgart', 'EDFA', target_gain=17.0, boost=True)
        l_ulm_stuttgart = net.add_link(name_to_roadm['roadm_ulm'],
                                       name_to_roadm['roadm_stuttgart'],
                                       boost_amp=boost_ulm_stuttgart)
        s1_l_ulm_stuttgart = Span('SMF', 87.1)
        amp1_l_ulm_stuttgart = net.add_amplifier('amp1_l_ulm_stuttgart', 'EDFA', target_gain=19.2)
        l_ulm_stuttgart.add_span(s1_l_ulm_stuttgart, amp1_l_ulm_stuttgart)

        return net

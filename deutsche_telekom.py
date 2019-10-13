import network


class DeutscheTelekom:

    def __init__(self):

        """
            TOPOLOGY CREATION

            Nomenclature conventions:
            OLS follow: olsX - X always a number - (i.e., ols1)
            ROADMS follow: roadmA - A always a letter - (i.e., roadmA)
            Amplifiers follow: ampX - X always a number - followed
            by the name of the link they belong to (i.e., amp1_link_ols1_roadmA)
            Spans follow: spanX - X always a number - followed by the
            name of the link they belong to (i.e., span1_link_ols1_roadmA)
        """
        # Create an optical-network object
        self.net = network.Network()

        self.nodes = []
        self.links = []

        self.name_to_node = {}

        """
            Create nodes in the topology
        """
        # Create line terminals for each city
        lt_berlin = self.net.add_ols('lt_berlin')
        lt_berlin.add_transceiver('t1', 'C')
        self.add_node(lt_berlin)

        lt_bremen = self.net.add_ols('lt_bremen')
        lt_bremen.add_transceiver('t1', 'C')
        self.add_node(lt_bremen)

        lt_dortmund = self.net.add_ols('lt_dortmund')
        lt_dortmund.add_transceiver('t1', 'C')
        self.add_node(lt_dortmund)

        lt_dusseldorf = self.net.add_ols('lt_dusseldorf')
        lt_dusseldorf.add_transceiver('t1', 'C')
        self.add_node(lt_dusseldorf)

        lt_essen = self.net.add_ols('lt_essen')
        lt_essen.add_transceiver('t1', 'C')
        self.add_node(lt_essen)

        lt_frankfurt = self.net.add_ols('lt_frankfurt')
        lt_frankfurt.add_transceiver('t1', 'C')
        self.add_node(lt_frankfurt)

        lt_hamburg = self.net.add_ols('lt_hamburg')
        lt_hamburg.add_transceiver('t1', 'C')
        self.add_node(lt_hamburg)

        lt_hannover = self.net.add_ols('lt_hannover')
        lt_hannover.add_transceiver('t1', 'C')
        self.add_node(lt_hannover)

        lt_koln = self.net.add_ols('lt_koln')
        lt_koln.add_transceiver('t1', 'C')
        self.add_node(lt_koln)

        lt_leipzig = self.net.add_ols('lt_leipzig')
        lt_leipzig.add_transceiver('t1', 'C')
        self.add_node(lt_leipzig)

        lt_munchen = self.net.add_ols('lt_munchen')
        lt_munchen.add_transceiver('t1', 'C')
        self.add_node(lt_munchen)

        lt_nurnberg = self.net.add_ols('lt_nurnberg')
        lt_nurnberg.add_transceiver('t1', 'C')
        self.add_node(lt_nurnberg)

        lt_stuttgart = self.net.add_ols('lt_stuttgart')
        lt_stuttgart.add_transceiver('t1', 'C')
        self.add_node(lt_stuttgart)

        lt_ulm = self.net.add_ols('lt_ulm')
        lt_ulm.add_transceiver('t1', 'C')
        self.add_node(lt_ulm)

        # Create ROADM nodes for each city
        roadm_berlin = self.net.add_roadm('roadm_berlin')
        self.add_node(roadm_berlin)

        roadm_bremen = self.net.add_roadm('roadm_bremen')
        self.add_node(roadm_bremen)

        roadm_dortmund = self.net.add_roadm('roadm_dortmund')
        self.add_node(roadm_dortmund)

        roadm_dusseldorf = self.net.add_roadm('roadm_dusseldorf')
        self.add_node(roadm_dusseldorf)

        roadm_essen = self.net.add_roadm('roadm_essen')
        self.add_node(roadm_essen)

        roadm_frankfurt = self.net.add_roadm('roadm_frankfurt')
        self.add_node(roadm_frankfurt)

        roadm_hamburg = self.net.add_roadm('roadm_hamburg')
        self.add_node(roadm_hamburg)

        roadm_hannover = self.net.add_roadm('roadm_hannover')
        self.add_node(roadm_hannover)

        roadm_koln = self.net.add_roadm('roadm_koln')
        self.add_node(roadm_koln)

        roadm_leipzig = self.net.add_roadm('roadm_leipzig')
        self.add_node(roadm_leipzig)

        roadm_munchen = self.net.add_roadm('roadm_munchen')
        self.add_node(roadm_munchen)

        roadm_nurnberg = self.net.add_roadm('roadm_nurnberg')
        self.add_node(roadm_nurnberg)

        roadm_stuttgart = self.net.add_roadm('roadm_stuttgart')
        self.add_node(roadm_stuttgart)

        roadm_ulm = self.net.add_roadm('roadm_ulm')
        self.add_node(roadm_ulm)

        """
            Create links between line terminals and immediate ROADM nodes
        """
        # Link between lt_berlin and roadm_berlin
        link_lt_roadm_berlin = self.net.add_link(lt_berlin, roadm_berlin)
        self.links.append(link_lt_roadm_berlin)

        # Link between lt_bremen and roadm_bremen
        link_lt_roadm_bremen = self.net.add_link(lt_bremen, roadm_bremen)
        self.links.append(link_lt_roadm_bremen)

        # Link between lt_dortmund and roadm_dortmund
        link_lt_roadm_dortmund = self.net.add_link(lt_dortmund, roadm_dortmund)
        self.links.append(link_lt_roadm_dortmund)

        # Link between lt_dusseldorf and roadm_dusseldorf
        link_lt_roadm_dusseldorf = self.net.add_link(lt_dusseldorf, roadm_dusseldorf)
        self.links.append(link_lt_roadm_dusseldorf)

        # Link between lt_essen and roadm_essen
        link_lt_roadm_essen = self.net.add_link(lt_essen, roadm_essen)
        self.links.append(link_lt_roadm_essen)

        # Link between lt_frankfurt and roadm_frankfurt
        link_lt_roadm_frankfurt = self.net.add_link(lt_frankfurt, roadm_frankfurt)
        self.links.append(link_lt_roadm_frankfurt)

        # Link between lt_hamburg and roadm_hamburg
        link_lt_roadm_hamburg = self.net.add_link(lt_hamburg, roadm_hamburg)
        self.links.append(link_lt_roadm_hamburg)

        # Link between lt_hannover and roadm_hannover
        link_lt_roadm_hannover = self.net.add_link(lt_hannover, roadm_hannover)
        self.links.append(link_lt_roadm_hannover)

        # Link between lt_koln and roadm_koln
        link_lt_roadm_koln = self.net.add_link(lt_koln, roadm_koln)
        self.links.append(link_lt_roadm_koln)

        # Link between lt_leipzig and roadm_leipzig
        link_lt_roadm_leipzig = self.net.add_link(lt_leipzig, roadm_leipzig)
        self.links.append(link_lt_roadm_leipzig)

        # Link between lt_munchen and roadm_munchen
        link_lt_roadm_munchen = self.net.add_link(lt_munchen, roadm_munchen)
        self.links.append(link_lt_roadm_munchen)

        # Link between lt_nurnberg and roadm_nurnberg
        link_lt_roadm_nurnberg = self.net.add_link(lt_nurnberg, roadm_nurnberg)
        self.links.append(link_lt_roadm_nurnberg)

        # Link between lt_stuttgart and roadm_stuttgart
        link_lt_roadm_stuttgart = self.net.add_link(lt_stuttgart, roadm_stuttgart)
        self.links.append(link_lt_roadm_stuttgart)

        # Link between lt_ulm and roadm_ulm
        link_lt_roadm_ulm = self.net.add_link(lt_ulm, roadm_ulm)
        self.links.append(link_lt_roadm_ulm)

        """
            Create links between inter-city ROADM nodes
        """
        # Link between Berlin and Hamburg - 306.3 km
        # and the bidirectional (independent) link
        boost_amp_berlin_hamburg = self.net.add_amplifier('boost_amp_berlin_hamburg', 'EDFA', target_gain=6)
        self.add_node(boost_amp_berlin_hamburg)
        link_berlin_hamburg = self.net.add_link(roadm_berlin, roadm_hamburg, boost_amp=boost_amp_berlin_hamburg)
        self.links.append(link_berlin_hamburg)
        span1_link_berlin_hamburg = self.net.add_span('SMF', 100)
        amp1_link_berlin_hamburg = self.net.add_amplifier('amp1_link_berlin_hamburg', 'EDFA', target_gain=22)
        self.add_node(amp1_link_berlin_hamburg)
        self.net.add_span_to_link(link_berlin_hamburg, span1_link_berlin_hamburg, amp1_link_berlin_hamburg)

        boost_amp_hamburg_berlin = self.net.add_amplifier('boost_amp_hamburg_berlin', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hamburg_berlin)
        link_hamburg_berlin = self.net.add_link(roadm_berlin, roadm_hamburg, boost_amp=boost_amp_hamburg_berlin)
        self.links.append(link_hamburg_berlin)
        span1_link_hamburg_berlin = self.net.add_span('SMF', 100)
        amp1_link_hamburg_berlin = self.net.add_amplifier('amp1_link_hamburg_berlin', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hamburg_berlin)
        self.net.add_span_to_link(link_hamburg_berlin, span1_link_hamburg_berlin, amp1_link_hamburg_berlin)

        # Link between Berlin and Hannover - 294.9 km
        # and the bidirectional (independent) link
        boost_amp_berlin_hannover = self.net.add_amplifier('boost_amp_berlin_hannover', 'EDFA', target_gain=6)
        self.add_node(boost_amp_berlin_hannover)
        link_berlin_hannover = self.net.add_link(roadm_berlin, roadm_hannover, boost_amp=boost_amp_berlin_hannover)
        self.links.append(link_berlin_hannover)
        span1_link_berlin_hannover = self.net.add_span('SMF', 100)
        amp1_link_berlin_hannover = self.net.add_amplifier('amp1_link_berlin_hannover', 'EDFA', target_gain=22)
        self.add_node(amp1_link_berlin_hannover)
        self.net.add_span_to_link(link_berlin_hannover, span1_link_berlin_hannover, amp1_link_berlin_hannover)

        boost_amp_hannover_berlin = self.net.add_amplifier('boost_amp_hannover_berlin', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hannover_berlin)
        link_hannover_berlin = self.net.add_link(roadm_berlin, roadm_hannover, boost_amp=boost_amp_hannover_berlin)
        self.links.append(link_hannover_berlin)
        span1_link_hannover_berlin = self.net.add_span('SMF', 100)
        amp1_link_hannover_berlin = self.net.add_amplifier('amp1_link_hannover_berlin', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hannover_berlin)
        self.net.add_span_to_link(link_hannover_berlin, span1_link_hannover_berlin, amp1_link_hannover_berlin)

        # Link between Berlin and Leipzig - 173.3 km
        # and the bidirectional (independent) link
        boost_amp_berlin_leipzig = self.net.add_amplifier('boost_amp_berlin_leipzig', 'EDFA', target_gain=6)
        self.add_node(boost_amp_berlin_leipzig)
        link_berlin_leipzig = self.net.add_link(roadm_berlin, roadm_leipzig, boost_amp=boost_amp_berlin_leipzig)
        self.links.append(link_berlin_leipzig)
        span1_link_berlin_leipzig = self.net.add_span('SMF', 100)
        amp1_link_berlin_leipzig = self.net.add_amplifier('amp1_link_berlin_leipzig', 'EDFA', target_gain=22)
        self.add_node(amp1_link_berlin_leipzig)
        self.net.add_span_to_link(link_berlin_leipzig, span1_link_berlin_leipzig, amp1_link_berlin_leipzig)

        boost_amp_leipzig_berlin = self.net.add_amplifier('boost_amp_leipzig_berlin', 'EDFA', target_gain=6)
        self.add_node(boost_amp_leipzig_berlin)
        link_leipzig_berlin = self.net.add_link(roadm_berlin, roadm_leipzig, boost_amp=boost_amp_leipzig_berlin)
        self.links.append(link_leipzig_berlin)
        span1_link_leipzig_berlin = self.net.add_span('SMF', 100)
        amp1_link_leipzig_berlin = self.net.add_amplifier('amp1_link_leipzig_berlin', 'EDFA', target_gain=22)
        self.add_node(amp1_link_leipzig_berlin)
        self.net.add_span_to_link(link_leipzig_berlin, span1_link_leipzig_berlin, amp1_link_leipzig_berlin)

        # Link between Bremen and Hamburg - 114.7 km
        # and the bidirectional (independent) link
        boost_amp_bremen_hamburg = self.net.add_amplifier('boost_amp_bremen_hamburg', 'EDFA', target_gain=6)
        self.add_node(boost_amp_bremen_hamburg)
        link_bremen_hamburg = self.net.add_link(roadm_bremen, roadm_hamburg, boost_amp=boost_amp_bremen_hamburg)
        self.links.append(link_bremen_hamburg)
        span1_link_bremen_hamburg = self.net.add_span('SMF', 100)
        amp1_link_bremen_hamburg = self.net.add_amplifier('amp1_link_bremen_hamburg', 'EDFA', target_gain=22)
        self.add_node(amp1_link_bremen_hamburg)
        self.net.add_span_to_link(link_bremen_hamburg, span1_link_bremen_hamburg, amp1_link_bremen_hamburg)

        boost_amp_hamburg_bremen = self.net.add_amplifier('boost_amp_hamburg_bremen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hamburg_bremen)
        link_hamburg_bremen = self.net.add_link(roadm_bremen, roadm_hamburg, boost_amp=boost_amp_hamburg_bremen)
        self.links.append(link_hamburg_bremen)
        span1_link_hamburg_bremen = self.net.add_span('SMF', 100)
        amp1_link_hamburg_bremen = self.net.add_amplifier('amp1_link_hamburg_bremen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hamburg_bremen)
        self.net.add_span_to_link(link_hamburg_bremen, span1_link_hamburg_bremen, amp1_link_hamburg_bremen)

        # Link between Bremen and Hannover - 121.3 km
        # and the bidirectional (independent) link
        boost_amp_bremen_hannover = self.net.add_amplifier('boost_amp_bremen_hannover', 'EDFA', target_gain=6)
        self.add_node(boost_amp_bremen_hannover)
        link_bremen_hannover = self.net.add_link(roadm_bremen, roadm_hannover, boost_amp=boost_amp_bremen_hannover)
        self.links.append(link_bremen_hannover)
        span1_link_bremen_hannover = self.net.add_span('SMF', 100)
        amp1_link_bremen_hannover = self.net.add_amplifier('amp1_link_bremen_hannover', 'EDFA', target_gain=22)
        self.add_node(amp1_link_bremen_hannover)
        self.net.add_span_to_link(link_bremen_hannover, span1_link_bremen_hannover, amp1_link_bremen_hannover)

        boost_amp_hannover_bremen = self.net.add_amplifier('boost_amp_hannover_bremen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hannover_bremen)
        link_hannover_bremen = self.net.add_link(roadm_bremen, roadm_hannover, boost_amp=boost_amp_hannover_bremen)
        self.links.append(link_hannover_bremen)
        span1_link_hannover_bremen = self.net.add_span('SMF', 100)
        amp1_link_hannover_bremen = self.net.add_amplifier('amp1_link_hannover_bremen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hannover_bremen)
        self.net.add_span_to_link(link_hannover_bremen, span1_link_hannover_bremen, amp1_link_hannover_bremen)

        # Link between Bremen and Essen - 278.5 km
        # and the bidirectional (independent) link
        boost_amp_bremen_essen = self.net.add_amplifier('boost_amp_bremen_essen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_bremen_essen)
        link_bremen_essen = self.net.add_link(roadm_bremen, roadm_essen, boost_amp=boost_amp_bremen_essen)
        self.links.append(link_bremen_essen)
        span1_link_bremen_essen = self.net.add_span('SMF', 100)
        amp1_link_bremen_essen = self.net.add_amplifier('amp1_link_bremen_essen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_bremen_essen)
        self.net.add_span_to_link(link_bremen_essen, span1_link_bremen_essen, amp1_link_bremen_essen)

        boost_amp_essen_bremen = self.net.add_amplifier('boost_amp_essen_bremen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_essen_bremen)
        link_essen_bremen = self.net.add_link(roadm_bremen, roadm_essen, boost_amp=boost_amp_essen_bremen)
        self.links.append(link_essen_bremen)
        span1_link_essen_bremen = self.net.add_span('SMF', 100)
        amp1_link_essen_bremen = self.net.add_amplifier('amp1_link_essen_bremen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_essen_bremen)
        self.net.add_span_to_link(link_essen_bremen, span1_link_essen_bremen, amp1_link_essen_bremen)

        # Link between Dortmund and Essen - 37.4 km
        # and the bidirectional (independent) link
        boost_amp_dortmund_essen = self.net.add_amplifier('boost_amp_dortmund_essen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_dortmund_essen)
        link_dortmund_essen = self.net.add_link(roadm_dortmund, roadm_essen, boost_amp=boost_amp_dortmund_essen)
        self.links.append(link_dortmund_essen)
        span1_link_dortmund_essen = self.net.add_span('SMF', 100)
        amp1_link_dortmund_essen = self.net.add_amplifier('amp1_link_dortmund_essen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_dortmund_essen)
        self.net.add_span_to_link(link_dortmund_essen, span1_link_dortmund_essen, amp1_link_dortmund_essen)

        boost_amp_essen_dortmund = self.net.add_amplifier('boost_amp_essen_dortmund', 'EDFA', target_gain=6)
        self.add_node(boost_amp_essen_dortmund)
        link_essen_dortmund = self.net.add_link(roadm_dortmund, roadm_essen, boost_amp=boost_amp_essen_dortmund)
        self.links.append(link_essen_dortmund)
        span1_link_essen_dortmund = self.net.add_span('SMF', 100)
        amp1_link_essen_dortmund = self.net.add_amplifier('amp1_link_essen_dortmund', 'EDFA', target_gain=22)
        self.add_node(amp1_link_essen_dortmund)
        self.net.add_span_to_link(link_essen_dortmund, span1_link_essen_dortmund, amp1_link_essen_dortmund)

        # Link between Dortmund and Hannover - 220.4 km
        # and the bidirectional (independent) link
        boost_amp_dortmund_hannover = self.net.add_amplifier('boost_amp_dortmund_hannover', 'EDFA', target_gain=6)
        self.add_node(boost_amp_dortmund_hannover)
        link_dortmund_hannover = self.net.add_link(roadm_dortmund, roadm_hannover,
                                                   boost_amp=boost_amp_dortmund_hannover)
        self.links.append(link_dortmund_hannover)
        span1_link_dortmund_hannover = self.net.add_span('SMF', 100)
        amp1_link_dortmund_hannover = self.net.add_amplifier('amp1_link_dortmund_hannover', 'EDFA', target_gain=22)
        self.add_node(amp1_link_dortmund_hannover)
        self.net.add_span_to_link(link_dortmund_hannover, span1_link_dortmund_hannover, amp1_link_dortmund_hannover)

        boost_amp_hannover_dortmund = self.net.add_amplifier('boost_amp_hannover_dortmund', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hannover_dortmund)
        link_hannover_dortmund = self.net.add_link(roadm_dortmund, roadm_hannover,
                                                   boost_amp=boost_amp_hannover_dortmund)
        self.links.append(link_hannover_dortmund)
        span1_link_hannover_dortmund = self.net.add_span('SMF', 100)
        amp1_link_hannover_dortmund = self.net.add_amplifier('amp1_link_hannover_dortmund', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hannover_dortmund)
        self.net.add_span_to_link(link_hannover_dortmund, span1_link_hannover_dortmund, amp1_link_hannover_dortmund)

        # Link between Dortmund and Koln - 84.3 km
        # and the bidirectional (independent) link
        boost_amp_dortmund_koln = self.net.add_amplifier('boost_amp_dortmund_koln', 'EDFA', target_gain=6)
        self.add_node(boost_amp_dortmund_koln)
        link_dortmund_koln = self.net.add_link(roadm_dortmund, roadm_koln, boost_amp=boost_amp_dortmund_koln)
        self.links.append(link_dortmund_koln)
        span1_link_dortmund_koln = self.net.add_span('SMF', 100)
        amp1_link_dortmund_koln = self.net.add_amplifier('amp1_link_dortmund_koln', 'EDFA', target_gain=22)
        self.add_node(amp1_link_dortmund_koln)
        self.net.add_span_to_link(link_dortmund_koln, span1_link_dortmund_koln, amp1_link_dortmund_koln)

        boost_amp_koln_dortmund = self.net.add_amplifier('boost_amp_koln_dortmund', 'EDFA', target_gain=6)
        self.add_node(boost_amp_koln_dortmund)
        link_koln_dortmund = self.net.add_link(roadm_dortmund, roadm_koln, boost_amp=boost_amp_koln_dortmund)
        self.links.append(link_koln_dortmund)
        span1_link_koln_dortmund = self.net.add_span('SMF', 100)
        amp1_link_koln_dortmund = self.net.add_amplifier('amp1_link_koln_dortmund', 'EDFA', target_gain=22)
        self.add_node(amp1_link_koln_dortmund)
        self.net.add_span_to_link(link_koln_dortmund, span1_link_koln_dortmund, amp1_link_koln_dortmund)

        # Link between Dusseldorf and Essen - 36.9 km
        # and the bidirectional (independent) link
        boost_amp_dusseldorf_essen = self.net.add_amplifier('boost_amp_dusseldorf_essen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_dusseldorf_essen)
        link_dusseldorf_essen = self.net.add_link(roadm_dusseldorf, roadm_essen, boost_amp=boost_amp_dusseldorf_essen)
        self.links.append(link_dusseldorf_essen)
        span1_link_dusseldorf_essen = self.net.add_span('SMF', 100)
        amp1_link_dusseldorf_essen = self.net.add_amplifier('amp1_link_dusseldorf_essen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_dusseldorf_essen)
        self.net.add_span_to_link(link_dusseldorf_essen, span1_link_dusseldorf_essen, amp1_link_dusseldorf_essen)

        boost_amp_essen_dusseldorf = self.net.add_amplifier('boost_amp_essen_dusseldorf', 'EDFA', target_gain=6)
        self.add_node(boost_amp_essen_dusseldorf)
        link_essen_dusseldorf = self.net.add_link(roadm_dusseldorf, roadm_essen, boost_amp=boost_amp_essen_dusseldorf)
        self.links.append(link_essen_dusseldorf)
        span1_link_essen_dusseldorf = self.net.add_span('SMF', 100)
        amp1_link_essen_dusseldorf = self.net.add_amplifier('amp1_link_essen_dusseldorf', 'EDFA', target_gain=22)
        self.add_node(amp1_link_essen_dusseldorf)
        self.net.add_span_to_link(link_essen_dusseldorf, span1_link_essen_dusseldorf, amp1_link_essen_dusseldorf)

        # Link between Dusseldorf and Koln - 40.9 km
        # and the bidirectional (independent) link
        boost_amp_dusseldorf_koln = self.net.add_amplifier('boost_amp_dusseldorf_koln', 'EDFA', target_gain=6)
        self.add_node(boost_amp_dusseldorf_koln)
        link_dusseldorf_koln = self.net.add_link(roadm_dusseldorf, roadm_koln, boost_amp=boost_amp_dusseldorf_koln)
        self.links.append(link_dusseldorf_koln)
        span1_link_dusseldorf_koln = self.net.add_span('SMF', 100)
        amp1_link_dusseldorf_koln = self.net.add_amplifier('amp1_link_dusseldorf_koln', 'EDFA', target_gain=22)
        self.add_node(amp1_link_dusseldorf_koln)
        self.net.add_span_to_link(link_dusseldorf_koln, span1_link_dusseldorf_koln, amp1_link_dusseldorf_koln)

        boost_amp_koln_dusseldorf = self.net.add_amplifier('boost_amp_koln_dusseldorf', 'EDFA', target_gain=6)
        self.add_node(boost_amp_koln_dusseldorf)
        link_koln_dusseldorf = self.net.add_link(roadm_dusseldorf, roadm_koln, boost_amp=boost_amp_koln_dusseldorf)
        self.links.append(link_koln_dusseldorf)
        span1_link_koln_dusseldorf = self.net.add_span('SMF', 100)
        amp1_link_koln_dusseldorf = self.net.add_amplifier('amp1_link_koln_dusseldorf', 'EDFA', target_gain=22)
        self.add_node(amp1_link_koln_dusseldorf)
        self.net.add_span_to_link(link_koln_dusseldorf, span1_link_koln_dusseldorf, amp1_link_koln_dusseldorf)

        # Link between Frankfurt and Hannover - 313.9 km
        # and the bidirectional (independent) link
        boost_amp_frankfurt_hannover = self.net.add_amplifier('boost_amp_frankfurt_hannover', 'EDFA', target_gain=6)
        self.add_node(boost_amp_frankfurt_hannover)
        link_frankfurt_hannover = self.net.add_link(roadm_frankfurt, roadm_hannover,
                                                    boost_amp=boost_amp_frankfurt_hannover)
        self.links.append(link_frankfurt_hannover)
        span1_link_frankfurt_hannover = self.net.add_span('SMF', 100)
        amp1_link_frankfurt_hannover = self.net.add_amplifier('amp1_link_frankfurt_hannover', 'EDFA', target_gain=22)
        self.add_node(amp1_link_frankfurt_hannover)
        self.net.add_span_to_link(link_frankfurt_hannover, span1_link_frankfurt_hannover, amp1_link_frankfurt_hannover)

        boost_amp_hannover_frankfurt = self.net.add_amplifier('boost_amp_hannover_frankfurt', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hannover_frankfurt)
        link_hannover_frankfurt = self.net.add_link(roadm_frankfurt, roadm_hannover,
                                                    boost_amp=boost_amp_hannover_frankfurt)
        self.links.append(link_hannover_frankfurt)
        span1_link_hannover_frankfurt = self.net.add_span('SMF', 100)
        amp1_link_hannover_frankfurt = self.net.add_amplifier('amp1_link_hannover_frankfurt', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hannover_frankfurt)
        self.net.add_span_to_link(link_hannover_frankfurt, span1_link_hannover_frankfurt, amp1_link_hannover_frankfurt)

        # Link between Frankfurt and Koln - 182 km
        # and the bidirectional (independent) link
        boost_amp_frankfurt_koln = self.net.add_amplifier('boost_amp_frankfurt_koln', 'EDFA', target_gain=6)
        self.add_node(boost_amp_frankfurt_koln)
        link_frankfurt_koln = self.net.add_link(roadm_frankfurt, roadm_koln, boost_amp=boost_amp_frankfurt_koln)
        self.links.append(link_frankfurt_koln)
        span1_link_frankfurt_koln = self.net.add_span('SMF', 100)
        amp1_link_frankfurt_koln = self.net.add_amplifier('amp1_link_frankfurt_koln', 'EDFA', target_gain=22)
        self.add_node(amp1_link_frankfurt_koln)
        self.net.add_span_to_link(link_frankfurt_koln, span1_link_frankfurt_koln, amp1_link_frankfurt_koln)

        boost_amp_koln_frankfurt = self.net.add_amplifier('boost_amp_koln_frankfurt', 'EDFA', target_gain=6)
        self.add_node(boost_amp_koln_frankfurt)
        link_koln_frankfurt = self.net.add_link(roadm_frankfurt, roadm_koln, boost_amp=boost_amp_koln_frankfurt)
        self.links.append(link_koln_frankfurt)
        span1_link_koln_frankfurt = self.net.add_span('SMF', 100)
        amp1_link_koln_frankfurt = self.net.add_amplifier('amp1_link_koln_frankfurt', 'EDFA', target_gain=22)
        self.add_node(amp1_link_koln_frankfurt)
        self.net.add_span_to_link(link_koln_frankfurt, span1_link_koln_frankfurt, amp1_link_koln_frankfurt)

        # Link between Frankfurt and Leipzig - 313.9 km
        # and the bidirectional (independent) link
        boost_amp_frankfurt_leipzig = self.net.add_amplifier('boost_amp_frankfurt_leipzig', 'EDFA', target_gain=6)
        self.add_node(boost_amp_frankfurt_leipzig)
        link_frankfurt_leipzig = self.net.add_link(roadm_frankfurt, roadm_leipzig,
                                                   boost_amp=boost_amp_frankfurt_leipzig)
        self.links.append(link_frankfurt_leipzig)
        span1_link_frankfurt_leipzig = self.net.add_span('SMF', 100)
        amp1_link_frankfurt_leipzig = self.net.add_amplifier('amp1_link_frankfurt_leipzig', 'EDFA', target_gain=22)
        self.add_node(amp1_link_frankfurt_leipzig)
        self.net.add_span_to_link(link_frankfurt_leipzig, span1_link_frankfurt_leipzig, amp1_link_frankfurt_leipzig)

        boost_amp_leipzig_frankfurt = self.net.add_amplifier('boost_amp_leipzig_frankfurt', 'EDFA', target_gain=6)
        self.add_node(boost_amp_leipzig_frankfurt)
        link_leipzig_frankfurt = self.net.add_link(roadm_frankfurt, roadm_leipzig,
                                                   boost_amp=boost_amp_leipzig_frankfurt)
        self.links.append(link_leipzig_frankfurt)
        span1_link_leipzig_frankfurt = self.net.add_span('SMF', 100)
        amp1_link_leipzig_frankfurt = self.net.add_amplifier('amp1_link_leipzig_frankfurt', 'EDFA', target_gain=22)
        self.add_node(amp1_link_leipzig_frankfurt)
        self.net.add_span_to_link(link_leipzig_frankfurt, span1_link_leipzig_frankfurt, amp1_link_leipzig_frankfurt)

        # Link between Frankfurt and Nurnberg - 224.1 km
        # and the bidirectional (independent) link
        boost_amp_frankfurt_nurnberg = self.net.add_amplifier('boost_amp_frankfurt_nurnberg', 'EDFA', target_gain=6)
        self.add_node(boost_amp_frankfurt_nurnberg)
        link_frankfurt_nurnberg = self.net.add_link(roadm_frankfurt, roadm_nurnberg,
                                                    boost_amp=boost_amp_frankfurt_nurnberg)
        self.links.append(link_frankfurt_nurnberg)
        span1_link_frankfurt_nurnberg = self.net.add_span('SMF', 100)
        amp1_link_frankfurt_nurnberg = self.net.add_amplifier('amp1_link_frankfurt_nurnberg', 'EDFA', target_gain=22)
        self.add_node(amp1_link_frankfurt_nurnberg)
        self.net.add_span_to_link(link_frankfurt_nurnberg, span1_link_frankfurt_nurnberg, amp1_link_frankfurt_nurnberg)

        boost_amp_nurnberg_frankfurt = self.net.add_amplifier('boost_amp_nurnberg_frankfurt', 'EDFA', target_gain=6)
        self.add_node(boost_amp_nurnberg_frankfurt)
        link_nurnberg_frankfurt = self.net.add_link(roadm_frankfurt, roadm_nurnberg,
                                                    boost_amp=boost_amp_nurnberg_frankfurt)
        self.links.append(link_nurnberg_frankfurt)
        span1_link_nurnberg_frankfurt = self.net.add_span('SMF', 100)
        amp1_link_nurnberg_frankfurt = self.net.add_amplifier('amp1_link_nurnberg_frankfurt', 'EDFA', target_gain=22)
        self.add_node(amp1_link_nurnberg_frankfurt)
        self.net.add_span_to_link(link_nurnberg_frankfurt, span1_link_nurnberg_frankfurt, amp1_link_nurnberg_frankfurt)

        # Link between Frankfurt and Stuttgart - 207.4 km
        # and the bidirectional (independent) link
        boost_amp_frankfurt_stuttgart = self.net.add_amplifier('boost_amp_frankfurt_stuttgart', 'EDFA', target_gain=6)
        self.add_node(boost_amp_frankfurt_stuttgart)
        link_frankfurt_stuttgart = self.net.add_link(roadm_frankfurt, roadm_stuttgart,
                                                     boost_amp=boost_amp_frankfurt_stuttgart)
        self.links.append(link_frankfurt_stuttgart)
        span1_link_frankfurt_stuttgart = self.net.add_span('SMF', 100)
        amp1_link_frankfurt_stuttgart = self.net.add_amplifier('amp1_link_frankfurt_stuttgart', 'EDFA', target_gain=22)
        self.add_node(amp1_link_frankfurt_stuttgart)
        self.net.add_span_to_link(link_frankfurt_stuttgart, span1_link_frankfurt_stuttgart,
                                  amp1_link_frankfurt_stuttgart)

        boost_amp_stuttgart_frankfurt = self.net.add_amplifier('boost_amp_stuttgart_frankfurt', 'EDFA', target_gain=6)
        self.add_node(boost_amp_stuttgart_frankfurt)
        link_stuttgart_frankfurt = self.net.add_link(roadm_frankfurt, roadm_stuttgart,
                                                     boost_amp=boost_amp_stuttgart_frankfurt)
        self.links.append(link_stuttgart_frankfurt)
        span1_link_stuttgart_frankfurt = self.net.add_span('SMF', 100)
        amp1_link_stuttgart_frankfurt = self.net.add_amplifier('amp1_link_stuttgart_frankfurt', 'EDFA', target_gain=22)
        self.add_node(amp1_link_stuttgart_frankfurt)
        self.net.add_span_to_link(link_stuttgart_frankfurt, span1_link_stuttgart_frankfurt,
                                  amp1_link_stuttgart_frankfurt)

        # Link between Hamburg and Hannover - 160.9 km
        # and the bidirectional (independent) link
        boost_amp_hamburg_hannover = self.net.add_amplifier('boost_amp_hamburg_hannover', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hamburg_hannover)
        link_hamburg_hannover = self.net.add_link(roadm_hamburg, roadm_hannover, boost_amp=boost_amp_hamburg_hannover)
        self.links.append(link_hamburg_hannover)
        span1_link_hamburg_hannover = self.net.add_span('SMF', 100)
        amp1_link_hamburg_hannover = self.net.add_amplifier('amp1_link_hamburg_hannover', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hamburg_hannover)
        self.net.add_span_to_link(link_hamburg_hannover, span1_link_hamburg_hannover, amp1_link_hamburg_hannover)

        boost_amp_hannover_hamburg = self.net.add_amplifier('boost_amp_hannover_hamburg', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hannover_hamburg)
        link_hannover_hamburg = self.net.add_link(roadm_hamburg, roadm_hannover, boost_amp=boost_amp_hannover_hamburg)
        self.links.append(link_hannover_hamburg)
        span1_link_hannover_hamburg = self.net.add_span('SMF', 100)
        amp1_link_hannover_hamburg = self.net.add_amplifier('amp1_link_hannover_hamburg', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hannover_hamburg)
        self.net.add_span_to_link(link_hannover_hamburg, span1_link_hannover_hamburg, amp1_link_hannover_hamburg)

        # Link between Hannover and Leipzig - 257.2 km
        # and the bidirectional (independent) link
        boost_amp_hannover_leipzig = self.net.add_amplifier('boost_amp_hannover_leipzig', 'EDFA', target_gain=6)
        self.add_node(boost_amp_hannover_leipzig)
        link_hannover_leipzig = self.net.add_link(roadm_hannover, roadm_leipzig, boost_amp=boost_amp_hannover_leipzig)
        self.links.append(link_hannover_leipzig)
        span1_link_hannover_leipzig = self.net.add_span('SMF', 100)
        amp1_link_hannover_leipzig = self.net.add_amplifier('amp1_link_hannover_leipzig', 'EDFA', target_gain=22)
        self.add_node(amp1_link_hannover_leipzig)
        self.net.add_span_to_link(link_hannover_leipzig, span1_link_hannover_leipzig, amp1_link_hannover_leipzig)

        boost_amp_leipzig_hannover = self.net.add_amplifier('boost_amp_leipzig_hannover', 'EDFA', target_gain=6)
        self.add_node(boost_amp_leipzig_hannover)
        link_leipzig_hannover = self.net.add_link(roadm_hannover, roadm_leipzig, boost_amp=boost_amp_leipzig_hannover)
        self.links.append(link_leipzig_hannover)
        span1_link_leipzig_hannover = self.net.add_span('SMF', 100)
        amp1_link_leipzig_hannover = self.net.add_amplifier('amp1_link_leipzig_hannover', 'EDFA', target_gain=22)
        self.add_node(amp1_link_leipzig_hannover)
        self.net.add_span_to_link(link_leipzig_hannover, span1_link_leipzig_hannover, amp1_link_leipzig_hannover)

        # Link between Leipzig and Nurnberg - 274.7 km
        # and the bidirectional (independent) link
        boost_amp_leipzig_nurnberg = self.net.add_amplifier('boost_amp_leipzig_nurnberg', 'EDFA', target_gain=6)
        self.add_node(boost_amp_leipzig_nurnberg)
        link_leipzig_nurnberg = self.net.add_link(roadm_leipzig, roadm_nurnberg, boost_amp=boost_amp_leipzig_nurnberg)
        self.links.append(link_leipzig_nurnberg)
        span1_link_leipzig_nurnberg = self.net.add_span('SMF', 100)
        amp1_link_leipzig_nurnberg = self.net.add_amplifier('amp1_link_leipzig_nurnberg', 'EDFA', target_gain=22)
        self.add_node(amp1_link_leipzig_nurnberg)
        self.net.add_span_to_link(link_leipzig_nurnberg, span1_link_leipzig_nurnberg, amp1_link_leipzig_nurnberg)

        boost_amp_nurnberg_leipzig = self.net.add_amplifier('boost_amp_nurnberg_leipzig', 'EDFA', target_gain=6)
        self.add_node(boost_amp_nurnberg_leipzig)
        link_nurnberg_leipzig = self.net.add_link(roadm_leipzig, roadm_nurnberg, boost_amp=boost_amp_nurnberg_leipzig)
        self.links.append(link_nurnberg_leipzig)
        span1_link_nurnberg_leipzig = self.net.add_span('SMF', 100)
        amp1_link_nurnberg_leipzig = self.net.add_amplifier('amp1_link_nurnberg_leipzig', 'EDFA', target_gain=22)
        self.add_node(amp1_link_nurnberg_leipzig)
        self.net.add_span_to_link(link_nurnberg_leipzig, span1_link_nurnberg_leipzig, amp1_link_nurnberg_leipzig)

        # Link between Munchen and Nurnberg - 180.8 km
        # and the bidirectional (independent) link
        boost_amp_munchen_nurnberg = self.net.add_amplifier('boost_amp_munchen_nurnberg', 'EDFA', target_gain=6)
        self.add_node(boost_amp_munchen_nurnberg)
        link_munchen_nurnberg = self.net.add_link(roadm_munchen, roadm_nurnberg, boost_amp=boost_amp_munchen_nurnberg)
        self.links.append(link_munchen_nurnberg)
        span1_link_munchen_nurnberg = self.net.add_span('SMF', 100)
        amp1_link_munchen_nurnberg = self.net.add_amplifier('amp1_link_munchen_nurnberg', 'EDFA', target_gain=22)
        self.add_node(amp1_link_munchen_nurnberg)
        self.net.add_span_to_link(link_munchen_nurnberg, span1_link_munchen_nurnberg, amp1_link_munchen_nurnberg)

        boost_amp_nurnberg_munchen = self.net.add_amplifier('boost_amp_nurnberg_munchen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_nurnberg_munchen)
        link_nurnberg_munchen = self.net.add_link(roadm_munchen, roadm_nurnberg, boost_amp=boost_amp_nurnberg_munchen)
        self.links.append(link_nurnberg_munchen)
        span1_link_nurnberg_munchen = self.net.add_span('SMF', 100)
        amp1_link_nurnberg_munchen = self.net.add_amplifier('amp1_link_nurnberg_munchen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_nurnberg_munchen)
        self.net.add_span_to_link(link_nurnberg_munchen, span1_link_nurnberg_munchen, amp1_link_nurnberg_munchen)

        # Link between Munchen and Ulm - 145.6 km
        # and the bidirectional (independent) link
        boost_amp_munchen_ulm = self.net.add_amplifier('boost_amp_munchen_ulm', 'EDFA', target_gain=6)
        self.add_node(boost_amp_munchen_ulm)
        link_munchen_ulm = self.net.add_link(roadm_munchen, roadm_ulm, boost_amp=boost_amp_munchen_ulm)
        self.links.append(link_munchen_ulm)
        span1_link_munchen_ulm = self.net.add_span('SMF', 100)
        amp1_link_munchen_ulm = self.net.add_amplifier('amp1_link_munchen_ulm', 'EDFA', target_gain=22)
        self.add_node(amp1_link_munchen_ulm)
        self.net.add_span_to_link(link_munchen_ulm, span1_link_munchen_ulm, amp1_link_munchen_ulm)

        boost_amp_ulm_munchen = self.net.add_amplifier('boost_amp_ulm_munchen', 'EDFA', target_gain=6)
        self.add_node(boost_amp_ulm_munchen)
        link_ulm_munchen = self.net.add_link(roadm_munchen, roadm_ulm, boost_amp=boost_amp_ulm_munchen)
        self.links.append(link_ulm_munchen)
        span1_link_ulm_munchen = self.net.add_span('SMF', 100)
        amp1_link_ulm_munchen = self.net.add_amplifier('amp1_link_ulm_munchen', 'EDFA', target_gain=22)
        self.add_node(amp1_link_ulm_munchen)
        self.net.add_span_to_link(link_ulm_munchen, span1_link_ulm_munchen, amp1_link_ulm_munchen)

        # Link between Nurnberg and Stuttgart - 188.7 km
        # and the bidirectional (independent) link
        boost_amp_nurnberg_stuttgart = self.net.add_amplifier('boost_amp_nurnberg_stuttgart', 'EDFA', target_gain=6)
        self.add_node(boost_amp_nurnberg_stuttgart)
        link_nurnberg_stuttgart = self.net.add_link(roadm_nurnberg, roadm_stuttgart,
                                                    boost_amp=boost_amp_nurnberg_stuttgart)
        self.links.append(link_nurnberg_stuttgart)
        span1_link_nurnberg_stuttgart = self.net.add_span('SMF', 100)
        amp1_link_nurnberg_stuttgart = self.net.add_amplifier('amp1_link_nurnberg_stuttgart', 'EDFA', target_gain=22)
        self.add_node(amp1_link_nurnberg_stuttgart)
        self.net.add_span_to_link(link_nurnberg_stuttgart, span1_link_nurnberg_stuttgart, amp1_link_nurnberg_stuttgart)

        boost_amp_stuttgart_nurnberg = self.net.add_amplifier('boost_amp_stuttgart_nurnberg', 'EDFA', target_gain=6)
        self.add_node(boost_amp_stuttgart_nurnberg)
        link_stuttgart_nurnberg = self.net.add_link(roadm_nurnberg, roadm_stuttgart,
                                                    boost_amp=boost_amp_stuttgart_nurnberg)
        self.links.append(link_stuttgart_nurnberg)
        span1_link_stuttgart_nurnberg = self.net.add_span('SMF', 100)
        amp1_link_stuttgart_nurnberg = self.net.add_amplifier('amp1_link_stuttgart_nurnberg', 'EDFA', target_gain=22)
        self.add_node(amp1_link_stuttgart_nurnberg)
        self.net.add_span_to_link(link_stuttgart_nurnberg, span1_link_stuttgart_nurnberg, amp1_link_stuttgart_nurnberg)

        # Link between Stuttgart and Ulm - 87.1 km
        # and the bidirectional (independent) link
        boost_amp_stuttgart_ulm = self.net.add_amplifier('boost_amp_stuttgart_ulm', 'EDFA', target_gain=6)
        self.add_node(boost_amp_stuttgart_ulm)
        link_stuttgart_ulm = self.net.add_link(roadm_stuttgart, roadm_ulm, boost_amp=boost_amp_stuttgart_ulm)
        self.links.append(link_stuttgart_ulm)
        span1_link_stuttgart_ulm = self.net.add_span('SMF', 100)
        amp1_link_stuttgart_ulm = self.net.add_amplifier('amp1_link_stuttgart_ulm', 'EDFA', target_gain=22)
        self.add_node(amp1_link_stuttgart_ulm)
        self.net.add_span_to_link(link_stuttgart_ulm, span1_link_stuttgart_ulm, amp1_link_stuttgart_ulm)

        boost_amp_ulm_stuttgart = self.net.add_amplifier('boost_amp_ulm_stuttgart', 'EDFA', target_gain=6)
        self.add_node(boost_amp_ulm_stuttgart)
        link_ulm_stuttgart = self.net.add_link(roadm_stuttgart, roadm_ulm, boost_amp=boost_amp_ulm_stuttgart)
        self.links.append(link_ulm_stuttgart)
        span1_link_ulm_stuttgart = self.net.add_span('SMF', 100)
        amp1_link_ulm_stuttgart = self.net.add_amplifier('amp1_link_ulm_stuttgart', 'EDFA', target_gain=22)
        self.add_node(amp1_link_ulm_stuttgart)
        self.net.add_span_to_link(link_ulm_stuttgart, span1_link_ulm_stuttgart, amp1_link_ulm_stuttgart)
        
    def add_node(self, node):
        self.nodes.append(node)
        self.name_to_node[node.name] = node

    def add_link(self, link):
        self.links.append(link)

import network


class TestTopology:

    def __init__(self):

        """
            TOPOLOGY CREATION

            Nomenclature conventions:
            lt follow: ltX - X always a number - (i.e., lt1)
            ROADMS follow: roadmA - A always a letter - (i.e., roadmA)
            Amplifiers follow: ampX - X always a number - followed
            by the name of the link they belong to (i.e., amp1_link_lt1_roadmA)
            Spans follow: spanX - X always a number - followed by the
            name of the link they belong to (i.e., span1_link_lt1_roadmA)
        """
        # Create an optical-network object
        self.net = network.Network()

        self.nodes = []
        self.links = []

        self.name_to_node = {}

        # Create nodes in the network
        # lt, ROADM and EDFA
        
        lt1 = self.net.add_lt('lt1')
        lt1.add_transceiver('t1', 'C')
        self.add_node(lt1)
        
        lt2 = self.net.add_lt('lt2')
        lt2.add_transceiver('t1', 'C')
        self.add_node(lt2)
        
        lt3 = self.net.add_lt('lt3')
        lt3.add_transceiver('t1', 'C')
        self.add_node(lt3)

        roadmA = self.net.add_roadm('roadmA')
        self.add_node(roadmA)

        roadmB = self.net.add_roadm('roadmB')
        self.add_node(roadmB)

        roadmC = self.net.add_roadm('roadmC')
        self.add_node(roadmC)

        # Link between lt-1 and ROADM-A
        amp1_link_lt1_roadmA = self.net.add_amplifier('amp1_link_lt1_roadmA', 'EDFA', target_gain=6)
        self.add_node(amp1_link_lt1_roadmA)
        link_lt1_roadmA = self.net.add_link(lt1, roadmA, boost_amp=amp1_link_lt1_roadmA)
        self.links.append(link_lt1_roadmA)
        span1_link_lt1_roadmA = self.net.add_span('SMF', 100)
        amp2_link_lt1_roadmA = self.net.add_amplifier('amp2_link_lt1_roadmA', 'EDFA', target_gain=22)
        self.add_node(amp2_link_lt1_roadmA)
        self.net.add_span_to_link(link_lt1_roadmA, span1_link_lt1_roadmA, amp2_link_lt1_roadmA)

        # Link between ROADM-A and ROADM-B
        amp1_link_roadmA_roadmB = self.net.add_amplifier('amp1_link_roadmA_roadmB', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmA_roadmB)
        link_roadmA_roadmB = self.net.add_link(roadmA, roadmB, boost_amp=amp1_link_roadmA_roadmB)
        self.links.append(link_roadmA_roadmB)
        span1_link_roadmA_roadmB = self.net.add_span('SMF', 100)
        amp2_link_roadmA_roadmB = self.net.add_amplifier('amp2_link_roadmA_roadmB', 'EDFA', target_gain=22)
        self.add_node(amp2_link_lt1_roadmA)
        self.net.add_span_to_link(link_roadmA_roadmB, span1_link_roadmA_roadmB, amp2_link_roadmA_roadmB)

        # Link between ROADM-A and ROADM-C
        amp1_link_roadmA_roadmC = self.net.add_amplifier('amp1_link_roadmA_roadmC', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmA_roadmC)
        link_roadmA_roadmC = self.net.add_link(roadmA, roadmC, boost_amp=amp1_link_roadmA_roadmC)
        self.links.append(link_roadmA_roadmC)
        span1_link_roadmA_roadmC = self.net.add_span('SMF', 100)
        amp2_link_roadmA_roadmC = self.net.add_amplifier('amp2_link_roadmA_roadmC', 'EDFA', target_gain=22)
        self.add_node(amp2_link_lt1_roadmA)
        self.net.add_span_to_link(link_roadmA_roadmC, span1_link_roadmA_roadmC, amp2_link_roadmA_roadmC)

        # Link between ROADM-B and lt-2
        amp1_link_roadmB_lt2 = self.net.add_amplifier('amp1_link_roadmB_lt2', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmB_lt2)
        link_roadmB_lt2 = self.net.add_link(roadmB, lt2, boost_amp=amp1_link_roadmB_lt2)
        self.links.append(link_roadmB_lt2)
        span1_link_roadmB_lt2 = self.net.add_span('SMF', 100)
        amp2_link_roadmB_lt2 = self.net.add_amplifier('amp2_link_roadmB_lt2', 'EDFA', target_gain=22)
        self.add_node(amp2_link_lt1_roadmA)
        self.net.add_span_to_link(link_roadmB_lt2, span1_link_roadmB_lt2, amp2_link_roadmB_lt2)

        # Link between ROADM-C and lt-2
        amp1_link_roadmC_lt2 = self.net.add_amplifier('amp1_link_roadmC_lt2', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmC_lt2)
        link_roadmC_lt2 = self.net.add_link(roadmC, lt2, boost_amp=amp1_link_roadmC_lt2)
        self.links.append(link_roadmC_lt2)
        span1_link_roadmC_lt2 = self.net.add_span('SMF', 100)
        amp2_link_roadmC_lt2 = self.net.add_amplifier('amp2_link_roadmC_lt2', 'EDFA', target_gain=22)
        self.add_node(amp2_link_lt1_roadmA)
        self.net.add_span_to_link(link_roadmC_lt2, span1_link_roadmC_lt2, amp2_link_roadmC_lt2)

        # Link between ROADM-C and lt-3
        amp1_link_roadmC_lt3 = self.net.add_amplifier('amp1_link_roadmC_lt3', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmC_lt3)
        link_roadmC_lt3 = self.net.add_link(roadmC, lt3, boost_amp=amp1_link_roadmC_lt3)
        self.links.append(link_roadmC_lt3)
        span1_link_roadmC_lt3 = self.net.add_span('SMF', 100)
        amp2_link_roadmC_lt3 = self.net.add_amplifier('amp2_link_roadmC_lt3', 'EDFA', target_gain=22)
        self.add_node(amp2_link_lt1_roadmA)
        self.net.add_span_to_link(link_roadmC_lt3, span1_link_roadmC_lt3, amp2_link_roadmC_lt3)

    def add_node(self, node):
        self.nodes.append(node)
        self.name_to_node[node.name] = node

    def add_link(self, link):
        self.links.append(link)

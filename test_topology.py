import network


class TestTopology:

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

        # Create nodes in the network
        # OLS, ROADM and EDFA
        
        ols1 = self.net.add_ols('ols1')
        ols1.add_transceiver('t1', 'C')
        self.add_node(ols1)
        
        ols2 = self.net.add_ols('ols2')
        ols2.add_transceiver('t1', 'C')
        self.add_node(ols2)
        
        ols3 = self.net.add_ols('ols3')
        ols3.add_transceiver('t1', 'C')
        self.add_node(ols3)

        roadmA = self.net.add_roadm('roadmA')
        self.add_node(roadmA)

        roadmB = self.net.add_roadm('roadmB')
        self.add_node(roadmB)

        roadmC = self.net.add_roadm('roadmC')
        self.add_node(roadmC)

        # Link between OLS-1 and ROADM-A
        amp1_link_ols1_roadmA = self.net.add_amplifier('amp1_link_ols1_roadmA', 'EDFA', target_gain=6)
        self.add_node(amp1_link_ols1_roadmA)
        link_ols1_roadmA = self.net.add_link(ols1, roadmA, preamp=amp1_link_ols1_roadmA)
        self.links.append(link_ols1_roadmA)
        span1_link_ols1_roadmA = self.net.add_span('SMF', 100)
        amp2_link_ols1_roadmA = self.net.add_amplifier('amp2_link_ols1_roadmA', 'EDFA', target_gain=22)
        self.add_node(amp2_link_ols1_roadmA)
        self.net.add_span_to_link(link_ols1_roadmA, span1_link_ols1_roadmA, amp2_link_ols1_roadmA)

        # Link between ROADM-A and ROADM-B
        amp1_link_roadmA_roadmB = self.net.add_amplifier('amp1_link_roadmA_roadmB', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmA_roadmB)
        link_roadmA_roadmB = self.net.add_link(roadmA, roadmB, preamp=amp1_link_roadmA_roadmB)
        self.links.append(link_roadmA_roadmB)
        span1_link_roadmA_roadmB = self.net.add_span('SMF', 100)
        amp2_link_roadmA_roadmB = self.net.add_amplifier('amp2_link_roadmA_roadmB', 'EDFA', target_gain=22)
        self.add_node(amp2_link_ols1_roadmA)
        self.net.add_span_to_link(link_roadmA_roadmB, span1_link_roadmA_roadmB, amp2_link_roadmA_roadmB)

        # Link between ROADM-A and ROADM-C
        amp1_link_roadmA_roadmC = self.net.add_amplifier('amp1_link_roadmA_roadmC', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmA_roadmC)
        link_roadmA_roadmC = self.net.add_link(roadmA, roadmC, preamp=amp1_link_roadmA_roadmC)
        self.links.append(link_roadmA_roadmC)
        span1_link_roadmA_roadmC = self.net.add_span('SMF', 100)
        amp2_link_roadmA_roadmC = self.net.add_amplifier('amp2_link_roadmA_roadmC', 'EDFA', target_gain=22)
        self.add_node(amp2_link_ols1_roadmA)
        self.net.add_span_to_link(link_roadmA_roadmC, span1_link_roadmA_roadmC, amp2_link_roadmA_roadmC)

        # Link between ROADM-B and OLS-2
        amp1_link_roadmB_ols2 = self.net.add_amplifier('amp1_link_roadmB_ols2', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmB_ols2)
        link_roadmB_ols2 = self.net.add_link(roadmB, ols2, preamp=amp1_link_roadmB_ols2)
        self.links.append(link_roadmB_ols2)
        span1_link_roadmB_ols2 = self.net.add_span('SMF', 100)
        amp2_link_roadmB_ols2 = self.net.add_amplifier('amp2_link_roadmB_ols2', 'EDFA', target_gain=22)
        self.add_node(amp2_link_ols1_roadmA)
        self.net.add_span_to_link(link_roadmB_ols2, span1_link_roadmB_ols2, amp2_link_roadmB_ols2)

        # Link between ROADM-C and OLS-2
        amp1_link_roadmC_ols2 = self.net.add_amplifier('amp1_link_roadmC_ols2', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmC_ols2)
        link_roadmC_ols2 = self.net.add_link(roadmC, ols2, preamp=amp1_link_roadmC_ols2)
        self.links.append(link_roadmC_ols2)
        span1_link_roadmC_ols2 = self.net.add_span('SMF', 100)
        amp2_link_roadmC_ols2 = self.net.add_amplifier('amp2_link_roadmC_ols2', 'EDFA', target_gain=22)
        self.add_node(amp2_link_ols1_roadmA)
        self.net.add_span_to_link(link_roadmC_ols2, span1_link_roadmC_ols2, amp2_link_roadmC_ols2)

        # Link between ROADM-C and OLS-3
        amp1_link_roadmC_ols3 = self.net.add_amplifier('amp1_link_roadmC_ols3', 'EDFA', target_gain=6)
        self.add_node(amp1_link_roadmC_ols3)
        link_roadmC_ols3 = self.net.add_link(roadmC, ols3, preamp=amp1_link_roadmC_ols3)
        self.links.append(link_roadmC_ols3)
        span1_link_roadmC_ols3 = self.net.add_span('SMF', 100)
        amp2_link_roadmC_ols3 = self.net.add_amplifier('amp2_link_roadmC_ols3', 'EDFA', target_gain=22)
        self.add_node(amp2_link_ols1_roadmA)
        self.net.add_span_to_link(link_roadmC_ols3, span1_link_roadmC_ols3, amp2_link_roadmC_ols3)

    def add_node(self, node):
        self.nodes.append(node)
        self.name_to_node[node.name] = node

    def add_link(self, link):
        self.links.append(link)

from node import *
from link import *
from pprint import pprint


class Network(object):

    # Generate the abstract topology
    def __init__(self, transceiver=Transceiver, roadm=Roadm):
        self.transceiver = transceiver  # class of transceiver
        self.roadm = roadm  # class of ROADM

        self.line_terminals = []
        self.roadms = []
        self.links = []
        self.spans = []
        self.amplifiers = []

        self.links_to_span = {}
        self.topology = {}

        self.name_to_node = {}

    def add_lt(self, name, transceivers=None, **params):
        """
        Add lt node
        :param name: name of lt
        :param transceivers: transceivers of LT for automated instantiation
        :return: added lt
        """
        if name in self.name_to_node:
            raise ValueError("Network.add_lt: lt with this name already exist!")
        configs = {'name': name,
                   'transceivers': transceivers}
        configs.update(params)
        lt = LineTerminal(**configs)
        self.name_to_node[name] = lt
        self.line_terminals.append(lt)
        self.topology[lt] = []
        return lt

    def add_transceiver_to_lt(self, lt, transceiver_name, spectrum_band, **params):
        """
        Add transceiver to lt node
        :param lt: lt object
        :param transceiver_name: name of transceiver
        :param spectrum_band: configured spectrum band for transceiver
        :return:
        """
        if lt not in self.line_terminals:
            raise ValueError("Network.add_transceiver_to_lt: lt does not exist!")
        configs = {'transceiver_name': transceiver_name,
                   'spectrum_band': spectrum_band}
        configs.update(params)
        lt.add_transceiver(**configs)

    def add_roadm(self, name, **params):
        """
        Add a ROADM node.
        :param name: name of ROADM
        :return: added ROADM
        """
        if name in self.name_to_node:
            raise ValueError("Network.add_roadm: ROADM with this name already exist!!")
        configs = {'name': name}
        configs.update(params)
        roadm = Roadm(**configs)
        self.name_to_node[name] = roadm
        self.roadms.append(roadm)
        self.topology[roadm] = []
        return roadm

    def add_amplifier(self, name, amplifier_type='EDFA', **params):
        """
        Add an Amplifier node.
        :param name: name of Amplifier
        :param amplifier_type: amplifier type (currently supporting only EDFA)
        :return: added Amplifier
        """
        if name in self.name_to_node:
            raise ValueError("Network.add_amplifier: Amplifier with this name already exist!!")
        configs = {'name': name,
                   'amplifier_type': amplifier_type}
        configs.update(params)
        amplifier = Amplifier(**configs)
        self.name_to_node[name] = amplifier
        self.amplifiers.append(amplifier)
        return amplifier

    def add_link(self, node1, node2, boost_amp=None, spans=None):
        """
        Add a uni-directional link
        :param node1: source node in link
        :param node2: destination node in link
        :param boost_amp: optional amplifier object for boost_amplification
        :param spans:
        :return: created and added link
        """
        link = Link(node1, node2, boost_amp=boost_amp,
                    spans=spans)
        node1_output_port = link.output_port_node1
        node1.port_out_to_link[node1_output_port] = link
        self.links.append(link)
        self.topology[node1].append((node2, link))
        return link

    def find_link_and_out_port_from_nodes(self, src_node, dst_node):
        out_port = None
        for link in self.links:
            if link.node1 == src_node and link.node2 == dst_node:
                out_port = link.output_port_node1
        return out_port

    def find_link_and_in_port_from_nodes(self, src_node, dst_node):
        out_port = None
        for link in self.links:
            if link.node1 == src_node and link.node2 == dst_node:
                out_port = link.input_port_node2
        return out_port

    def find_link_from_nodes(self, src_node, dst_node):
        for link in self.links:
            if link.node1 == src_node and link.node2 == dst_node:
                return link

    @staticmethod
    def find_out_port_from_link(link):
        return link.output_port_node1

    def describe(self):
        pprint(vars(self))

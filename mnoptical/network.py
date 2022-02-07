from mnoptical.node import *
from mnoptical.link import *
from pprint import pprint


class Network(object):

    # Generate the abstract topology
    def __init__(self):
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
            raise ValueError("Network.add_amplifier: Amplifier with this name already exist!! %s" % str(name))
        configs = {'name': name,
                   'amplifier_type': amplifier_type}
        configs.update(params)
        amplifier = Amplifier(**configs)
        self.name_to_node[name] = amplifier
        self.amplifiers.append(amplifier)
        return amplifier

    def add_link(self, src_node, dst_node, src_out_port=-1,
                 dst_in_port=-1, boost_amp=None, spans=None):
        """
        Add a uni-directional link
        :param src_node: source node in link
        :param dst_node: destination node in link
        :param src_out_port: src_node output port
        :param dst_in_port: dst_node input port
        :param boost_amp: optional amplifier object for boost_amplification
        :param spans:
        :return: created and added link
        """
        link = Link(src_node, dst_node,
                    src_out_port=src_out_port,
                    dst_in_port=dst_in_port,
                    boost_amp=boost_amp,
                    spans=spans)

        self.links.append(link)
        self.topology[src_node].append((dst_node, link))
        return link

    def find_link_and_out_port_from_nodes(self, src_node, dst_node):
        """This does not consider if there are multiple output ports
        to the dst_node, as it is the case of the LTs and ROADMs"""
        out_port = None
        # AD: Links could be dictionaries with (src, dst) nodes as key
        for link in self.links:
            if link.src_node == src_node and link.dst_node == dst_node:
                tmplink = link
                out_port = src_node.node_to_port_out[dst_node][0]
        return out_port

    def find_link_and_in_port_from_nodes(self, src_node, dst_node):
        """This checks"""
        in_port = None
        for link in self.links:
            if link.src_node == src_node and link.dst_node == dst_node:
                in_port = dst_node.node_to_port_in[src_node][0]
        return in_port

    def find_link_from_nodes(self, src_node, dst_node):
        for link in self.links:
            if link.src_node == src_node and link.dst_node == dst_node:
                return link

    @staticmethod
    def find_out_port_from_link(link):
        return link.output_port_src_node

    def describe(self):
        pprint(vars(self))

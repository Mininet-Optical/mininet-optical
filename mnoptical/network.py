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

    def add_node(self, name, cls, *args, nodes=None, **params):
        """
        Add node to network
        :param name: name of node
        :param cls: node class/constructor
        :param nodes: list that node will be appended to
        """
        if nodes is None: nodes = []
        if name in self.name_to_node:
            raise ValueError(f"Network.add_node: node {name} already exists!")
        node = cls(name, *args, **params)
        self.name_to_node[name] = node
        nodes.append(node)
        self.topology[node] = []
        return node

    def add_lt(self, name, *args, cls=LineTerminal, **params):
        """
        Add lt node
        :param name: name of lt
        :param transceivers: transceivers of LT for automated instantiation
        :param cls: optional LineTerminal class/constructor
        :return: added lt
        """
        return self.add_node(name, cls, *args, nodes=self.line_terminals,
                             **params)

    def add_roadm(self, name, *args, cls=Roadm, **params):
        """
        Add a ROADM node.
        :param name: name of ROADM
        :cls: optional Roadm class/constructor
        :return: added ROADM
        """
        return self.add_node(name, cls, *args, nodes=self.roadms,
                             **params)

    def add_amplifier(self, name, *args, cls=Amplifier, **params):
        """
        Add an Amplifier node.
        :param name: name of Amplifier
        :param amplifier_type: amplifier type (currently supporting only EDFA)
        :param cls: optional Amplifier class/constructor
        :return: added Amplifier
        """
        return self.add_node(name, cls, *args, nodes=self.amplifiers,
                             **params)

    def add_link(self, src_node, dst_node, src_out_port=-1,
                 dst_in_port=-1, boost_amp=None, spans=None, cls=Link):
        """
        Add a uni-directional link
        :param src_node: source node in link
        :param dst_node: destination node in link
        :param src_out_port: src_node output port
        :param dst_in_port: dst_node input port
        :param boost_amp: optional amplifier object for boost_amplification
        :param spans:
        :param cls: optional Link class/constructor
        :return: created and added link
        """
        link = cls(src_node, dst_node,
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

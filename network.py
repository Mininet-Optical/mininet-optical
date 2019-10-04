from node import *
from link import *
import numpy as np


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10 * np.log10(absolute_value)
    return db_value


class Network(object):

    # Generate the abstract topology
    def __init__(self, transceiver=Transceiver, roadm=Roadm):
        self.transceiver = transceiver  # class of transceiver
        self.roadm = roadm  # class of ROADM

        self.olts = []
        self.roadms = []
        self.links = []
        self.spans = []
        self.amplifiers = []

        self.links_to_span = {}
        self.network = {}

        self.name_to_node = {}

    def add_olt(self, name, **params):
        """
        Add OLT node
        :param name: name of OLT
        :return: added OLT
        """
        if name in self.name_to_node:
            raise ValueError("Network.add_olt: OLT with this name already exist!")
        configs = {'name': name}
        configs.update(params)
        olt = OpticalLineTerminal(**configs)
        self.name_to_node[name] = olt
        self.olts.append(olt)
        return olt

    def add_transceiver_to_olt(self, olt, transceiver_name, spectrum_band, **params):
        """
        Add transceiver to OLT node
        :param transceiver_name: name of transceiver
        :param spectrum_band: configured spectrum band for transceiver
        :return:
        """
        if olt not in self.olts:
            raise ValueError("Network.add_transceiver_to_olt: OLT does not exist!")
        configs = {'transceiver_name': transceiver_name,
                   'spectrum_band': spectrum_band}
        configs.update(params)
        olt.add_transceiver(**configs)

    def add_roadm(self, name, **params):
        """
        Add a ROADM node.
        :param name: name of ROADM
        :return: added ROADM
        """
        if name in self.name_to_node:
            raise ValueError("Network.add_roadm: ROADM with this name already exist!!")
        configs = {'name': name,
                   'attenuation': 18}
        configs.update(params)
        roadm = Roadm(**configs)
        self.name_to_node[name] = roadm
        self.roadms.append(roadm)
        return roadm

    def add_amplifier(self, name, amplifier_type, **params):
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

    def add_link(self, node1, node2, ports=None):
        """
        Add a link between two nodes
        :param node1: node1 in the connection
        :param node2: node1 in the connection
        :param ports: optional
        :return:
        """
        if ports is None:
            ports1 = node1.new_connection_ports(node2)
            ports2 = node2.new_connection_ports(node1)
            ports = (ports1, ports2)

        link = Link(node1, node2, ports)
        self.links.append(link)
        return link

    def add_span(self, fiber_type, length):
        """
        Add span
        :param fiber_type: fiber type (currently supporting only SMF)
        :param length: fiber span length (km)
        :return: added span
        """
        span = Span(fiber_type, length)
        self.spans.append(span)
        return span

    def add_span_to_link(self, link, span, amplifier=None):
        """
        Add span to link in the network and in the link class
        :param link: link to be extended
        :param span: span to be added to link
        :param amplifier: amplifier compensating for span
        :return:
        """
        if link.id not in self.links_to_span:
            self.links_to_span[link.id] = []
        self.links_to_span[link.id].append((span, amplifier))

        link.add_span(span, amplifier)

    # Dijkstra algorithm for finding shortest path
    def find_path(self, src_node, dst_node):
        """
        :param src_node: source Node() object
        :param dst_node: destination Node() object
        :return:
        """
        # shortest paths is a dict of nodes
        # whose value is a tuple of (previous node, weight, Link())
        shortest_paths = {src_node: (None, 0, None)}
        current_node = src_node
        visited = set()
        while current_node != dst_node:
            visited.add(current_node)
            destinations = self.network[current_node]
            weight_to_current_node = shortest_paths[current_node][1]
            for node_to_link_relation in destinations:
                next_node = node_to_link_relation[0]
                link_to_next_node = node_to_link_relation[1]
                length_of_link = link_to_next_node.length()
                weight = length_of_link + weight_to_current_node
                if next_node not in shortest_paths:
                    shortest_paths[next_node] = (current_node, weight, link_to_next_node)
                else:
                    current_shortest_weight = shortest_paths[next_node][1]
                    if current_shortest_weight > weight:
                        shortest_paths[next_node] = (current_node, weight)

            next_destinations = {node: shortest_paths[node] for node in shortest_paths if node not in visited}
            if not next_destinations:
                return "network.find_path: Route Not Possible"
            # next node is the destination with the lowest weight
            current_node = min(next_destinations, key=lambda k: next_destinations[k][1])

        # Work back through destinations in shortest path
        path = []
        link_to_next_node = None
        while current_node is not None:
            path.append((current_node, link_to_next_node))
            next_node = shortest_paths[current_node][0]
            link_to_next_node = shortest_paths[current_node][2]
            current_node = next_node
        # Reverse path
        path = path[::-1]
        return path

    def topology(self):
        """
        This function NEEDS fixing.
        :return: dummy representation of the built network
        """
        for link in self.links:
            src_node = link.src_node
            dst_node = link.dst_node
            link_string_representation = ""
            roadm = "ROADM"
            edfa = "EDFA-"
            for span_obj in sorted(self.links[link]):
                span = span_obj[0]
                span_length = span.length

                amplifier = span_obj[1]
                if amplifier is not None:
                    link_string_representation += (" ---" + str(span_length) + "km---" +
                                                   edfa + str(amplifier.target_gain) + "dB")
                else:
                    link_string_representation += " ---" + str(span_length) + "km---"
            str_src_node = roadm + str(src_node.label)
            str_dst_node = roadm + str(dst_node.label)
            print(str_src_node + link_string_representation + "> " + str_dst_node)

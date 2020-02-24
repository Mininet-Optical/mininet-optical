from node import *
from link import *
import numpy as np
import math
from pprint import pprint


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

    def add_link(self, node1, node2, ports=None, boost_amp=None, spans=None):
        """
        Add a uni-directional link
        :param node1: source node in link
        :param node2: destination node in link
        :param ports: optional dict of ports per node
        :param boost_amp: optional amplifier object for boost_amplification
        :return: created and added link
        """
        ports = ports or {}
        node1_output_port = ports.get('node1_output_port')
        node2_input_port = ports.get('node2_input_port')
        link = Link(node1, node2, node1_output_port, node2_input_port, boost_amp=boost_amp,
                    spans=spans)
        node1.out_port_to_link[node1_output_port] = link
        self.links.append(link)
        self.topology[node1].append((node2, link))
        return link

    def add_monitor(self, name, link=None, span=None, amplifier=None):
        assert link or span or amplifier
        monitor = Monitor(name, link, span, amplifier)
        self.name_to_node[name] = monitor

    def add_span(self, fiber_type, length):
        """
        OBSOLETE
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
        OBSOLETE
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

    def transmit(self, src_node, dst_node, bit_rate=100*1e9, resources=None):
        if resources:
            transceiver = resources['transceiver']
            wavelengths = resources['required_wavelengths']
        else:
            transceiver, wavelengths = self.wavelength_allocation(src_node, bit_rate)

        out_port = self.find_link_and_out_port_from_nodes(src_node, dst_node)
        src_node.transmit(transceiver, out_port, wavelengths)

    def find_link_and_out_port_from_nodes(self, src_node, dst_node):
        out_port = None
        for l in self.links:
            if l.node1 == src_node and l.node2 == dst_node:
                out_port = l.output_port_node1
        return out_port

    def routing(self, src_node, dst_node):
        """
        Dijkstra algorithm for finding shortest path
        :param src_node: source Node() object
        :param dst_node: destination Node() object
        :return: shortest route from src to dst
        """
        # shortest paths is a dict of nodes
        # whose value is a tuple of (previous node, weight, Link())
        shortest_paths = {src_node: (None, 0, None)}
        current_node = src_node
        visited = set()
        while current_node != dst_node:
            visited.add(current_node)
            destinations = self.topology[current_node]
            weight_to_current_node = shortest_paths[current_node][1]
            for node_to_link in destinations:
                next_node = node_to_link[0]
                link_to_next_node = node_to_link[1]
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
                return "Network.routing: Route Not Found."
            # next node is the destination with the lowest weight
            current_node = min(next_destinations, key=lambda k: next_destinations[k][1])
        # Work back through destinations in shortest path
        route = []
        link_to_next_node = None
        while current_node is not None:
            route.append((current_node, link_to_next_node))
            next_node = shortest_paths[current_node][0]
            link_to_next_node = shortest_paths[current_node][2]
            current_node = next_node
        # Reverse path
        route = route[::-1]
        return route

    @staticmethod
    def wavelength_allocation(src_node, bit_rate):
        """
        From the transmission lt select a transceiver suitable for
        the bit rate request.
        :param src_node: src_node lt
        :param bit_rate: required bit rate
        :return: transceiver object and wavelengths to use !wavelengths might be extended here!
        """
        transceiver_to_wavelengths = {}  # dict of available transceivers to needed wavelengths
        for transceiver in src_node.transceivers:
            tx_bit_rate = transceiver.gross_bit_rate
            required_wavelengths = math.ceil(bit_rate / tx_bit_rate)  # required wavelengths for bit rate
            transceiver_to_wavelengths[transceiver] = required_wavelengths
        # Select the transceiver that requires the least number of wavelengths
        transceiver = min(transceiver_to_wavelengths, key=transceiver_to_wavelengths.get)
        required_wavelengths = transceiver_to_wavelengths[transceiver]

        available_wavelengths = src_node.available_wavelengths()
        # Here we can add an algorithm to select the wavelengths.
        # At the moment we use first available resources.
        wavelength_indexes = available_wavelengths[:required_wavelengths]
        return transceiver, wavelength_indexes

    def describe(self):
        pprint(vars(self))

    # ADDITIONS FOR OFC DEMO USE-CASES
    def mock_nf_adjust(self, amp_name, new_nf, src_roadm_name, dst_roadm_name):
        """
        Note: contains hard-coded features due to the lack of OO-design with regard
        to the Link, Spans and EDFAs. For the demo there's no time to change it,
        but it can certainly be improved in the future.
        :param amp_name: string
        :param new_nf: float (dB)
        :param src_roadm_name:
        :param dst_roadm_name:
        :return:
        """
        print("*** net.mock_nf_adjust start...")
        if amp_name not in self.name_to_node:
            print("*** net.mock_nf_adjust  amplifier name not found!")
            return
        if src_roadm_name not in self.name_to_node or dst_roadm_name not in self.name_to_node:
            print("*** net.mock_nf_adjust  roadm name not found!")
            return
        amp = self.name_to_node[amp_name]
        # Assign new NF to amplifier
        amp.mock_nf_adjust(new_nf)

        # retrieve ROADM objects
        src_roadm = self.name_to_node[src_roadm_name]
        dst_roadm = self.name_to_node[dst_roadm_name]
        # find link between nodes
        l = self.find_link_from_nodes(src_roadm, dst_roadm)
        # reset the signal-propagation structures along the link
        l.reset_propagation_struct()
        op = self.find_out_port_from_link(l)
        # Pass only the signals corresponding to the output port
        pass_through_signals = src_roadm.port_to_optical_signal_power_out[op]
        ase = {}
        nli = {}
        print("*** Recomputing propagation out of %s" % src_roadm_name)
        l.propagate(pass_through_signals, ase, nli)

        print("*** net.mock_nf_adjust end...")

    def mock_amp_gain_adjust(self, amp_name, new_gain, src_roadm_name, dst_roadm_name):
        """
        Note: contains hard-coded features due to the lack of OO-design with regard
        to the Link, Spans and EDFAs. For the demo there's no time to change it,
        but it can certainly be improved in the future.
        :param amp_name: string
        :param new_gain: float (dB)
        :param src_roadm_name:
        :param dst_roadm_name:
        :return:
        """
        print("*** net.mock_amp_gain_adjust start...")
        if amp_name not in self.name_to_node:
            print("*** net.mock_amp_gain_adjust  amplifier name not found!")
            return
        if src_roadm_name not in self.name_to_node or dst_roadm_name not in self.name_to_node:
            print("*** net.mock_amp_gain_adjust  roadm name not found!")
            return
        amp = self.name_to_node[amp_name]
        # Assign new NF to amplifier
        amp.mock_amp_gain_adjust(new_gain)

        # retrieve ROADM objects
        src_roadm = self.name_to_node[src_roadm_name]
        dst_roadm = self.name_to_node[dst_roadm_name]
        # find link between nodes
        l = self.find_link_from_nodes(src_roadm, dst_roadm)
        # reset the signal-propagation structures along the link
        l.reset_propagation_struct()
        op = self.find_out_port_from_link(l)
        # Pass only the signals corresponding to the output port
        pass_through_signals = src_roadm.port_to_optical_signal_power_out[op]
        ase = {}
        nli = {}
        print("*** Recomputing propagation out of %s" % src_roadm_name)
        l.propagate(pass_through_signals, ase, nli)

        print("*** net.mock_amp_gain_adjust end...")

    def find_link_from_nodes(self, src_node, dst_node):
        for l in self.links:
            if l.node1 == src_node and l.node2 == dst_node:
                return l

    @staticmethod
    def find_out_port_from_link(l):
        return l.output_port_node1

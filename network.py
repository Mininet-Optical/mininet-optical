from node import *
from link import *
import numpy as np
import math
import time
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

        self.ols = []
        self.roadms = []
        self.links = []
        self.spans = []
        self.amplifiers = []

        self.links_to_span = {}
        self.topology = {}

        self.name_to_node = {}

        self.traffic = []  # list of Traffic objects on the network

    def add_ols(self, name, **params):
        """
        Add ols node
        :param name: name of OLS
        :return: added ols
        """
        if name in self.name_to_node:
            raise ValueError("Network.add_ols: OLS with this name already exist!")
        configs = {'name': name}
        configs.update(params)
        ols = OpticalLineSystem(**configs)
        self.name_to_node[name] = ols
        self.ols.append(ols)
        self.topology[ols] = []
        return ols

    def add_transceiver_to_ols(self, ols, transceiver_name, spectrum_band, **params):
        """
        Add transceiver to ols node
        :param ols: OLS object
        :param transceiver_name: name of transceiver
        :param spectrum_band: configured spectrum band for transceiver
        :return:
        """
        if ols not in self.ols:
            raise ValueError("Network.add_transceiver_to_ols: ols does not exist!")
        configs = {'transceiver_name': transceiver_name,
                   'spectrum_band': spectrum_band}
        configs.update(params)
        ols.add_transceiver(**configs)

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
        self.topology[roadm] = []
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

    def add_link(self, node1, node2, ports=None, boost_amp=None):
        """
        Add a uni-directional link
        :param node1: source node in link
        :param node2: destination node in link
        :param ports: optional dict of ports per node
        :param boost_amp: optional amplifier object for boost_amplification
        :return: created and added link
        """
        if ports is None:
            node1_output_port = node1.new_output_port(node2)
            node2_input_port = node2.new_input_port(node1)
        else:
            node1_output_port = ports['node1_output_port']
            node2_input_port = ports['node2_input_port']

        link = Link(node1, node2, node1_output_port, node2_input_port, boost_amp=boost_amp)
        self.links.append(link)
        self.topology[node1].append((node2, link))
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

    def transmit(self, src_node, dst_node, bit_rate=100*1e9, route=None, resources=None):
        """
        Oct. 9th
        NEED TO CHANGE THIS IMPLEMENTATION TO COMPLY WITH THE CONTROL SYSTEM BEHAVIOUR
        Create and start a Traffic object
        :param src_node: OLS transmitter node
        :param dst_node: OLS receiver node
        :param bit_rate: bit rate in Gbps
        :param route: list of tuples (node, link)
        :param resources: dict with transceiver and wavelength(s) to use !Wavelengths still not specified!
        :return:
        """
        if not route:
            route = self.routing(src_node, dst_node)
        if resources:
            transceiver = resources['transceiver']
            wavelengths = resources['required_wavelengths']
        else:
            transceiver, wavelengths = self.wavelength_allocation(src_node, bit_rate)
        new_traffic_request = Traffic(src_node, dst_node, bit_rate,
                                      route, transceiver, wavelengths)
        self.traffic.append(new_traffic_request)
        new_traffic_request.start()
        # The following might have to be a function on its own
        for t, n in new_traffic_request.altered_traffic.items():
            if t is not new_traffic_request:
                t.revisiting = True
                t.next_link_in_route(n)
        return new_traffic_request

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
        From the transmission OLS select a transceiver suitable for
        the bit rate request.
        :param src_node: src_node OLS
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


class Traffic(object):
    def __init__(self, src_node, dst_node, bit_rate,
                 route, transceiver, wavelength_indexes):
        self.id = id(self)
        self.timestamp = time.time()
        self.src_node = src_node
        self.dst_node = dst_node
        self.bit_rate = bit_rate
        self.route = route
        self.transceiver = transceiver
        self.wavelength_indexes = wavelength_indexes
        self.signals = None

        self.next_link = None
        self.next_node = None

        self.next_link_update = None
        self.next_node_update = None

        self.altered_traffic = {self: None}
        self.revisiting = False

    def start(self):
        """
        Begin transmission simulation from initial
        node in the given route
        :return:
        """
        self.next_link = self.route[0][1]
        self.next_node = self.route[1][0]
        out_port = self.next_link.output_port_node1
        self.src_node.add_channel_transmitter(self, self.transceiver, out_port, self.wavelength_indexes)

    def reset(self, out_port, rule_id):
        """
        Remove the traces of this traffic in the network
        :param out_port: output port of the src node in this traffic
        :param rule_id: rule ID that will no longer be valid
        :return:
        """
        self.src_node.reset(self, self.transceiver, out_port, rule_id)

    def next_link_in_route(self, node):
        """
        Continue propagating simulation in the next
        link of the given route
        :param node: node1 in link
        :return:
        """
        if self.revisiting:
            # Go back to save node where incoming
            # signals have been updated/modified
            self.next_node = node
            self.next_link, self.next_node = self.find_next_in_route()
        self.next_link.incoming_transmission(self, node)

    def next_link_in_route_rule_update(self, node, rule_id):
        # Find the next link and node on the route for
        # this given updated traffic
        self.next_node_update = node
        self.next_link_update, self.next_node_update = self.find_next_in_route_update()
        self.next_link_update.link_updated_rule(self, rule_id)

    def next_node_in_route_update(self, link, rule_id):
        # Get attributes of current 'next' node
        next_node = self.next_node_update
        next_node_in_port = link.input_port_node2
        if next_node is self.dst_node:
            next_node.update_channel_receiver(self, next_node_in_port)
            return
        next_node.update_channel_roadm(self, rule_id)

    def next_node_in_route(self, link):
        """
        Continue propagating simulation in the next
        node of the given route
        :param link: link from node1 to current 'next' node
        :return:
        """
        # Get attributes of current 'next' node
        next_node = self.next_node
        next_node_in_port = link.input_port_node2

        if next_node is self.dst_node:
            next_node.add_channel_receiver(self, next_node_in_port, link)
            # print for debugging purposes
            print("At RX node %s, tmp_e2e: %i\nRevisit: %s\n***" % (next_node.name, next_node.tmp_e2e, self.revisiting))
            return

        # update node traffic with incoming traffic from link
        next_node.port_to_signal_power_in[next_node_in_port].update(link.signal_power_out)

        # Find next two objects in route
        self.next_link, self.next_node = self.find_next_in_route()
        next_node_out_port = self.next_link.output_port_node1
        next_node.add_channel_roadm(self, next_node_in_port, next_node_out_port)

    def find_next_in_route(self):
        """
        Find next link and node in the route
        :return: next_link, next_node
        """
        flag = False
        next_link = None
        for item in self.route:
            if flag:
                next_node = item[0]
                return next_link, next_node
            if item[0] is self.next_node:
                next_link = item[1]
                flag = True

    def find_next_in_route_update(self):
        """
        Find next link and node in the route
        :return: next_link, next_node
        """
        flag = False
        next_link = None
        for item in self.route:
            if flag:
                next_node = item[0]
                return next_link, next_node
            if item[0] is self.next_node_update:
                next_link = item[1]
                flag = True

    def describe(self):
        pprint(vars(self))

#!/usr/bin/env python3

"""
linear_topo_watts_strogatz.py: bidirectional linear network with 1-degree ROADMs
            and bidirectional Terminal<->ROADM links
"""
import copy
import os
import random
import csv
from mnoptical.dataplane import (OpticalLink as OLink,
                                 ROADM, Terminal,
                                 OpticalNet as Mininet,
                                 km, m, dB, dBm)
from mnoptical.edfa_params import ripple_functions
from mnoptical.ofcdemo.fakecontroller import (
    RESTProxy)
from mnoptical.rest import RestServer
from mnoptical.node import abs_to_dbm
from mnoptical.ofcdemo.demolib import OpticalCLI, cleanup
import matplotlib.pyplot as plt
from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.examples.linuxrouter import LinuxRouter
from mininet.log import setLogLevel, info, debug, warning
from mininet.clean import cleanup

from functools import partial
from sys import argv
import numpy as np
import networkx as nx
from utils import Queue
from utils import NodeInformation

connection_detail = []
roadm_links = {}
terminal_ports = {}
distance = 17
roadm_line = 70  # 45 #29


class LinearTopo(Topo):
    """Parametrized unidirectional ROADM ring network
       ROADM r{i} port numbering:
       - 1: line in
       - 2: line out
       - 3..N+2: add/drop ports from/to terminal
       Terminal t{i} port numbering:
       - 1..N: transceiver uplink/downlink ports (bidirectional)
               to/from ROADM
       - N+1..2*N ethernet ports (bidirectional) to/from router
       Router s{i} port numbering (N==nodecount==txcount):
       - 1..N: uplinks/downlinks to/from terminal
       - N+1: local port, connected to host
       p: probability value for watts-strogatz model
       N: number of adjacent neighbours.
       connection: list of connection details.
    """

    def build(self, power=0 * dBm, N=3, k=4, p=0, connection=[]):
        """Create a 1-degree ROADM ring network, with the specified
           operational power and N ROADM/Terminal/Router/Host nodes"""
        self.N = N
        halfk = k // 2
        # number of channels used for numbering ports
        ch_link = 90
        links = {}
        neigh_list = {}
        neigh_metadata = {}
        neigh_graph = nx.Graph()
        seed = np.random.RandomState(42)
        nodes = list(range(1, N + 1))
        global roadm_links
        # Nodes/POPs: ROADM/Terminal/Router/Host
        rparams = {'monitor_mode': 'in'}
        transceivers = tuple((f'tx{ch}', power) for ch in range(1, ch_link + 1))
        tparams = {'transceivers': transceivers, 'monitor_mode': 'in'}
        for i in range(1, N + 1):
            self.addSwitch(f'r{i}', cls=ROADM, **rparams)
            self.addSwitch(f't{i}', cls=Terminal, **tparams)
            self.addNode(f's{i}', cls=LinuxRouter)
            self.addHost(f'h{i}')
        # Optical WAN link parameters
        boost = ('boost', {'target_gain': 17 * dB})
        spans = []
        for c in range(1, 5):
            ripple_func = random.choice(list(ripple_functions.keys()))
            aparams = {'target_gain': distance * km * .22, 'wdg_id': ripple_func}
            spans.extend([distance * km, (f'amp{c}', aparams)])
        # spans = [distance * km, ('amp1', aparams), distance * km, ('amp2', aparams), distance * km, ('amp3', aparams), distance * km, ('amp4', aparams)]
        # Optical and packet links
        for i in range(1, N + 1):
            # Unidirectional roadm->roadm optical links
            for j in range(1, halfk + 1):
                neig_node = i % N + j
                neig_node = neig_node if neig_node <= N else neig_node - N
                if neig_node == 1 and i == N:
                    print(f"last node connection {i} {neig_node}")
                    continue
                neigh_node = self.watts_strogatz_calc(i, neig_node, nodes, p, seed)
                # maintain neighbour list
                roadm_links.setdefault(i, []).append(neigh_node)
                roadm_links.setdefault(neigh_node, []).append(i)
                # maintain used ports of each node.
                links[f'r{i}'] = links.get(f'r{i}', {'linein': 1, 'lineout': 2})
                links[f'r{neigh_node}'] = links.get(f'r{neigh_node}', {'linein': 1, 'lineout': 2})
                lineout = links[f'r{i}']['lineout']
                linein = links[f'r{neigh_node}']['linein']
                # connected_node = NodeInformation(f'r{neigh_node}', f'r{i}', linein, lineout)
                neigh_list.setdefault(f'r{i}', []).append(f'r{neigh_node}')
                # neigh_metadata.setdefault(f'r{i}', []).append({f'r{neigh_node}': connected_node})
                neigh_graph.add_edge(f'r{i}', f'r{neigh_node}')
                linein_con = []
                lineout_con = []
                # create 5 links (it may increase with no. of connections) between roadms.
                for _ in range(5):
                    print(f'connecting roadms - r{i} r{neigh_node} {lineout} {linein}')
                    self.addLink(f'r{i}', f'r{neigh_node}',
                                 port1=lineout, port2=linein,
                                 boost=boost, spans=spans, cls=OLink)  # ULink
                    linein_con.append(linein)
                    lineout_con.append(lineout)
                    lineout += 2
                    linein += 2
                # maintain neigh metadata with node information of neigh and line in/out port connected between them.
                connected_node = NodeInformation(f'r{neigh_node}', f'r{i}', linein_con, lineout_con)
                neigh_metadata.setdefault(f'r{i}', []).append({f'r{neigh_node}': connected_node})
                links[f'r{i}']['lineout'] = lineout
                links[f'r{neigh_node}']['linein'] = linein
            # lineout = links[f'r{i}']['lineout']
            # roadm_line = 29
            for port in range(1, ch_link - 1):
                # Bidirectional terminal <-> roadm optical links
                debug(f't{i} r{i} {port + 2} {roadm_line + port + 2}\n')
                self.addLink(f't{i}', f'r{i}',
                             port1=port + 2, port2=roadm_line + port + 2,
                             spans=[1 * m], cls=OLink)
                # Terminal<->router ethernet links
            for port in range(1, ch_link + 1):
                self.addLink(f's{i}', f't{i}', port1=port, port2=ch_link + port)
            # Host-switch ethernet link
            self.addLink(f'h{i}', f's{i}', port2=ch_link + 1)
        global connection_detail
        for conn_node in connection:
            get_path = self.bfs(neigh_graph, f'r{conn_node["start"]}', f'r{conn_node["end"]}')
            print(f"bfs path = {get_path}")
            connection_detail.append(self.get_connection_detail(get_path, neigh_list, neigh_metadata, f'r{conn_node["start"]}'))

    @staticmethod
    def get_connection_detail(shortest_path, neigh_list, neigh_metadata, initial_node):
        """ generate route information with line in/out information between each hop."""
        debug(f"path from {initial_node} {shortest_path}\n")
        connection = []
        for path in shortest_path:
            if path in neigh_list[initial_node]:
                neigh_node = neigh_metadata[initial_node]
                reverse = False
                find_node, node = path, initial_node
            elif initial_node in neigh_list[path]:
                neigh_node = neigh_metadata[path]
                reverse = True
                find_node, node = initial_node, path
            else:
                debug(f"something a miss {initial_node} {path}\n")
                break
            neigh_obj = [list(k.values())[0] for k in neigh_node if list(k.keys())[0] == find_node][0]
            lineout, linein = neigh_obj.get_link()
            if reverse:
                find_node, node = node, find_node
            node_info = NodeInformation(node, find_node, linein, lineout, reverse)
            connection.append(node_info)
            initial_node = path
        info(f"Connection {[i.__dict__ for i in connection]} \n")
        return connection

    @staticmethod
    def watts_strogatz_calc(curr_node, neigh_node, nodes, p, seed):
        if seed.random() < p:
            # to avoid loop connection
            choices = [e for e in nodes if e not in (curr_node, neigh_node)]
            new_neigh_node = seed.choice(choices)
            if curr_node in roadm_links:
                if new_neigh_node in roadm_links[curr_node]:
                    return neigh_node
                if new_neigh_node in roadm_links:
                    if curr_node in roadm_links[new_neigh_node]:
                        return neigh_node
            debug(f"watts new connection -> {curr_node} {new_neigh_node}\n")
            return new_neigh_node
        else:
            debug(f"no change for {curr_node}")
            return neigh_node

    @staticmethod
    def bfs(graph, node, target):
        visited = []
        actions = []
        queue = Queue()
        start_node = node
        if start_node == target:
            return []
        queue.push((start_node, actions))
        while not queue.isEmpty():
            node, action = queue.pop()
            if node not in visited:
                visited.append(node)
                if node == target:
                    return action
                for neighbour in graph[node]:
                    new_action = action + [neighbour]
                    queue.push((neighbour, new_action))
        return []


# Helper functions

linein, lineout = 1, 2


def fwd(roadm, channels):
    info(roadm, 'fwd', channels, '\n')
    roadm.connect(linein, lineout, channels)


def drop(roadm, dst, channel):
    info(roadm, 'drop', channel, '\n')
    roadm.connect(linein, lineout + dst, [channel])


def add(roadm, src, channel):
    info(roadm, 'add', channel, '\n')
    roadm.connect(lineout + src, lineout, [channel])


# Configuration (for testing, etc.) using internal/native control API
def configNet(net, connection, start, end, ctr, ch):
    """
    Configure connection between ROADMs and Terminals for ring topology
    """
    info("Configuring network...\n")
    N = net.topo.N
    # channels = [1] #, 3, 5, 7, 9, 11, 15]
    channels = ch
    defaultEthPort = 90
    defaultWDMPort = 2
    counter = ctr
    # Terminal hostport<->(uplink,downlink)
    for ch in channels:
        ethPort = defaultEthPort + counter
        wdmPort = defaultWDMPort + counter
        info(f"t{start} t{end} line terminal connection - {ethPort} {wdmPort} \n")
        net[f't{start}'].connect(ethPort=ethPort, wdmPort=wdmPort, channel=ch)
        net[f't{end}'].connect(ethPort=ethPort, wdmPort=wdmPort, channel=ch)
        counter += 1
    # Configuring ROADM to forward ch1 from t1 to t2"
    for index, conn in enumerate(connection):
        counter = ctr
        for ch in channels:
            terminal_port = neigh_forward_port = counter + roadm_line + 2
            counter += 1
            node = conn.node_id
            neigh_node = conn.neigh_id
            default_linein = conn.linein
            default_lineout = conn.lineout
            if conn.reverse:
                default_lineout, default_linein = default_linein, default_lineout
            if index != 0:
                if (conn.reverse and connection[index - 1].reverse) or (not conn.reverse and connection[index - 1].reverse):
                    terminal_port = connection[index - 1].lineout
                else:
                    terminal_port = connection[index - 1].linein
            if index != (len(connection) - 1):
                if conn.reverse and connection[index + 1].reverse:
                    neigh_forward_port = connection[index + 1].linein
                elif connection[index + 1].reverse:
                    if conn.reverse:
                        neigh_forward_port = connection[index + 1].lineout
                    else:
                        neigh_forward_port = connection[index + 1].linein
                else:
                    neigh_forward_port = connection[index + 1].lineout
            net[node].connect(terminal_port, default_lineout, channels=[ch])
            net[neigh_node].connect(default_linein, neigh_forward_port, channels=[ch])


def start_transceiver(net, connection):
    # Power up transceivers
    info('*** Turning on transceivers... \n')
    for trans_conn in connection:
        net[f't{trans_conn["start"]}'].turn_on()
        net[f't{trans_conn["end"]}'].turn_on()


# Debugging: Plot network graph
def plotNet(net, outfile="singleroadm.png", directed=False, layout='circo',
            colorMap=None):
    "Plot network graph to outfile"
    try:
        import pygraphviz as pgv
    except:
        warning('*** Please install python3-pygraphviz for plotting\n')
        return
    color = {ROADM: 'red', Terminal: 'blue', OVSBridge: 'orange',
             Host: 'black'}
    if colorMap:
        color.update(colorMap)
    colors = {node: color.get(type(node), 'black')
              for node in net.values()}
    nfont = {'fontname': 'helvetica bold', 'penwidth': 3}
    g = pgv.AGraph(strict=False, directed=directed, layout=layout)
    roadms = [node for node in net.switches if isinstance(node, ROADM)]
    terms = [node for node in net.switches if isinstance(node, Terminal)]
    other = [node for node in net.switches if node not in set(roadms + terms)]
    for node in roadms + terms + other:
        g.add_node(node.name, color=colors[node], **nfont)
    for node in net.hosts:
        g.add_node(node.name, color=colors[node], **nfont, shape='box')
    for link in net.links:
        intf1, intf2 = link.intf1, link.intf2
        node1, node2 = intf1.node, intf2.node
        port1, port2 = node1.ports[intf1], node2.ports[intf2]
        g.add_edge(node1.name, node2.name,
                   headlabel=f' {node2}:{port2} ',
                   taillabel=f' {node1}:{port1} ',
                   labelfontsize=10, labelfontname='helvetica bold',
                   penwidth=2)
    print("*** Plotting network topology to", outfile)
    g.layout()
    g.draw(outfile)


def config(net):
    """Configure optical and packet network"""
    # configNet(net)
    pass


class CLI(OpticalCLI):
    """CLI with config command"""

    def do_config(self, _line):
        config(self.mn)


def test(net):
    """Run script in test mode"""
    config(net)
    assert net.pingAll() == 0  # 0% loss


def get_path_distance(path):
    print(f'get_path {path}')
    hop_count = len(path)
    term2roadm = m
    roadm2roadm = 4 * distance * km * hop_count
    dist = term2roadm + roadm2roadm
    print(f'total path - {dist}')
    return dist


def monitorOSNR(request, conn, conn_detail):
    for conn_index in range(0, len(conn)):
        start = conn[conn_index]['start']
        end = conn[conn_index]['end']
        writer = conn[conn_index]['file']
        ch_enabled = conn[conn_index]['ch']
        path = get_path_distance(conn_detail[conn_index])
        start_response = request.get('monitor', params=dict(monitor=f't{start}-monitor', port=None, mode='in'))
        end_response = request.get('monitor', params=dict(monitor=f't{end}-monitor', port=None, mode='in'))
        start_osnr = start_response.json()['osnr']
        end_osnr = end_response.json()['osnr']
        # populate csv row with initial data
        csv_row = [0] * channels_length
        csv_row = [1 if x + 1 in ch_enabled else y for x, y in enumerate(csv_row)]
        for (channel1, data1), (channel2, data2) in zip(start_osnr.items(), end_osnr.items()):
            start_THz = float(data1['freq']) / 1e12
            end_THz = float(data2['freq']) / 1e12
            s_osnr, s_gosnr = data1['osnr'], data1['gosnr']
            e_osnr, e_gosnr = data2['osnr'], data2['gosnr']
            s_ase, e_ase = data1['ase'], data2['ase']
            s_power_abs = data1['power']
            s_power_dbm = abs_to_dbm(s_power_abs)
            e_power_abs = data2['power']
            e_power_dbm = abs_to_dbm(e_power_abs)
            # prepare data for writing the dataset to file
            row = copy.deepcopy(csv_row)
            row.extend([channel1, e_power_dbm, path, s_ase, e_ase, s_osnr, e_osnr, s_gosnr, e_gosnr])
            writer.writerow(row)


def create_header(writer, ch_len):
    header = list(range(1, ch_len + 1))
    header.extend(['ch', 'pw', 'path', 's_ase', 'e_ase', 's_osnr', 'e_osnr', 's_gosnr', 'e_gosnr'])
    writer.writerow(header)


if __name__ == '__main__':
    cleanup()  # Just in case!
    setLogLevel('info')
    if 'clean' in argv: exit(0)
    channels_length = 80
    channels = []
    prob = 0.75
    prob_file = "075"
    channel_file = "dataset/saved_channels.csv"
    if not os.path.isfile(channel_file):
        print("File not exists")
        with open(channel_file, 'w', encoding='UTF8', newline='') as file:
            writer = csv.writer(file)
            for _ in range(8):
                channels.append(random.sample(range(1, 81), channels_length))
            writer.writerows(channels)
            file.flush()
    else:
        with open(channel_file, newline='') as f:
            channels = [list(map(int, rec)) for rec in csv.reader(f, delimiter=',')]
    print(channels)
    conn1_file = open(f"first__connection_topo2_p{prob_file}.csv", 'w')
    conn1_writer = csv.writer(conn1_file)
    conn2_file = open(f"second__connection_topo2_p{prob_file}.csv", 'w')
    conn2_writer = csv.writer(conn2_file)
    conn3_file = open(f"third__connection_topo2_p{prob_file}.csv", 'w')
    conn3_writer = csv.writer(conn3_file)
    conn4_file = open(f"fourth__connection_topo2_p{prob_file}.csv", 'w')
    conn4_writer = csv.writer(conn4_file)
    conn5_file = open(f"fifth__connection_topo2_p{prob_file}.csv", 'w')
    conn5_writer = csv.writer(conn5_file)
    conn6_file = open(f"sixth__connection_topo2_p{prob_file}.csv", 'w')
    conn6_writer = csv.writer(conn6_file)
    conn7_file = open(f"seventh__connection_topo2_p{prob_file}.csv", 'w')
    conn7_writer = csv.writer(conn7_file)
    conn8_file = open(f"eighth__connection_topo2_p{prob_file}.csv", 'w')
    conn8_writer = csv.writer(conn8_file)
    create_header(conn1_writer, channels_length)
    create_header(conn2_writer, channels_length)
    create_header(conn3_writer, channels_length)
    create_header(conn4_writer, channels_length)
    create_header(conn5_writer, channels_length)
    create_header(conn6_writer, channels_length)
    create_header(conn7_writer, channels_length)
    create_header(conn8_writer, channels_length)
    conn = [{'start': 1, 'end': 13, 'ch': [], 'file': conn1_writer}, {'start': 2, 'end': 17, 'ch': [], 'file': conn2_writer},
            {'start': 4, 'end': 16, 'ch': [], 'file': conn3_writer}, {'start': 5, 'end': 18, 'ch': [], 'file': conn4_writer},
            {'start': 3, 'end': 15, 'ch': [], 'file': conn5_writer}, {'start': 6, 'end': 19, 'ch': [], 'file': conn6_writer},
            {'start': 7, 'end': 20, 'ch': [], 'file': conn7_writer}, {'start': 8, 'end': 14, 'ch': [], 'file': conn8_writer}]
    topo = LinearTopo(N=20, p=prob, connection=conn)
    net = Mininet(topo=topo)
    print("starting model --- ")
    restServer = RestServer(net)
    net.start()
    restServer.start()
    requestHandler = RESTProxy()
    plotNet(net, outfile=f'eight_conn_linear_topo2-watts_plot_{prob_file}.png', directed=True)
    counter = 1
    for ch in range(channels_length):
        count = 0
        for end_conn in conn:
            configNet(net, connection_detail[count], end_conn['start'], end_conn['end'], counter, [channels[count][ch]])
            end_conn['ch'].append(channels[count][ch])
            count += 1
        start_transceiver(net, conn)
        monitorOSNR(requestHandler, conn, connection_detail)
        counter += 1
    conn1_file.close()
    conn2_file.close()
    conn3_file.close()
    conn4_file.close()
    conn5_file.close()
    conn6_file.close()
    conn7_file.close()
    conn8_file.close()
    if 'test' in argv:
        test(net)
    else:
        CLI(net)
    restServer.stop()
    net.stop()

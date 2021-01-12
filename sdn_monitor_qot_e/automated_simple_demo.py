"""
    This script is a demo to test:
     - deployment of the Cost239 topology
     - installation of traffic into the network depending upon the selected node pairs
     - configuration of network devices for the paths with certain sharing degree and number of hops
     - deployment of OPM nodes following various strategies
     - monitoring (writing log files)

    The Cost239 is a mesh topology with a mean ROADM degree of 4.
    In the network, all links are bidirectional. Though,
    transmissions are launched uni-directionally.

"""

from topo.cost239 import Cost239Topology
from estimation_module import *
import numpy as np
from operator import attrgetter
import os
import json
from visualize_topo import visualize

from collections import defaultdict

link_in_consideration=[]

class Graph:

    def __init__(self, vertices):
        # No. of vertices
        self.V = vertices
        self.edge_description = {}

        # default dictionary to store graph
        self.graph = defaultdict(list)

        # function to add an edge to graph

    def addEdge(self, u, v):
        self.graph[u].append(v)

    def AllPathsUtil(self, u, d, visited, path, paths_list,max_hops):

        # Mark the current node as visited and store in path
        visited[u] = True
        path.append(list(self.edge_description.keys())[list(self.edge_description.values()).index(u)])

        # If current vertex is same as destination, then print
        # current path[]
        if u == d:
            if (len(path) <= max_hops):
                paths_list.append(list(path))

        else:
            # If current vertex is not destination
            # Recur for all the vertices adjacent to this vertex
            for i in self.graph[u]:
                if visited[i] == False:
                    self.AllPathsUtil(i, d, visited, path, paths_list,max_hops)

                    # Remove current vertex from path[] and mark it as unvisited
        path.pop()
        visited[u] = False

    def AllPaths(self, s, d,max_hops=4):

        # Mark all the vertices as not visited
        visited = [False] * (self.V)

        # Create an array to store paths
        path = []
        paths_list = []

        # Call the recursive helper function to print all paths
        self.AllPathsUtil(s, d, visited, path, paths_list,max_hops)
        return paths_list

    def find_routes(self,max_hops=4,sharing_degree=1,node_pairs=[]):

        """
         node pairs : currently takes two node pairs as input
         max_hops :  Maximum nodes in the path
         sharing_degree : no. of links shared in the paths
         output paths : the available paths depending upon the constraints and also the common-link

        """
        path_list=[]
        overlap_paths=[]
        for pairs in node_pairs:
            src,dst=pairs
            path_list.append(self.AllPaths(self.edge_description[src], self.edge_description[dst],max_hops=max_hops))



        for index in range(0,len(path_list)-1):
            path_1 = path_list[index]
            path_2 = path_list[index+1]
            for lst1 in path_1:
                for lst2 in path_2:
                    
                    overlap_link=(
                        list({tuple(lst1[i:i + 2]) for i in range(0, len(lst1) - 1)} & {tuple(lst2[i:i + 2]) for i in
                                                                                        range(0, len(lst2) - 1)}))

                    overlaps = len(overlap_link)

                    if overlaps == sharing_degree:
                        print("Sharing Degree - " + str(overlaps) + " paths:" + str([lst1, lst2]))
                        overlap_paths.append([overlap_link,[lst1, lst2]])

        return overlap_paths


def run(net):
    # the estimation module needs to be launched only once.

    cos239_dict = {'amsterdam': 0, 'berlin': 1, 'brussels': 2, 'copenhagen': 3, 'london': 4,
                   'luxembourg': 5,
                   'milan': 6, 'paris': 7, 'prague': 8, 'vienna': 9, 'zurich': 10,'hop1': 11, 'hop2': 12, 'hop3': 13, 'hop4': 14, 'hop5': 15, 'hop6': 16, 'hop7': 17, 'hop8': 18, 'hop9': 19}
    cos239 = [('amsterdam', 'london',390),
              ('amsterdam', 'brussels',200),
              ('amsterdam', 'luxembourg',310),
              ('amsterdam', 'berlin',600),
              ('amsterdam', 'copenhagen',750),
              ('berlin', 'copenhagen',400),
              ('berlin', 'paris',900),
              ('berlin', 'prague',320),
              ('berlin', 'vienna',710),

              # Main Brussels bi-links
              ('brussels', 'london',340),
              ('brussels', 'paris',270),
              ('brussels', 'milan',850),
              ('brussels', 'luxembourg',100),

              # Main Copenhagen bi-links
              ('copenhagen', 'london',1000),
              ('copenhagen', 'prague',760),

              # Main London bi-links
              ('london', 'paris',410),

              # Main Luxembourg bi-links
              ('luxembourg', 'paris',370),
              ('luxembourg', 'zurich',440),
              ('luxembourg', 'prague',900),

              # Main Milan bi-links
              ('milan', 'paris',810),
              ('milan', 'zurich',100),
              ('milan', 'vienna',720),

              # Main Paris bi-links
              ('paris', 'zurich',590),

              # Main Prague bi-links
              ('prague', 'zurich',100),
              ('prague', 'vienna',350),

              # Main Vienna bi-links
              ('vienna', 'zurich',710),
              ('hop1', 'hop2', 50), ('hop2', 'hop3', 50), ('hop3', 'hop4', 50), ('hop4', 'hop5', 50), ('hop5', 'hop6', 50), ('hop6', 'hop7', 50), ('hop7', 'hop8', 50), ('hop8', 'hop9', 50)]
    g = Graph(20)
    g.edge_description = cos239_dict
    monitor_distance_dict={}
    for elements in cos239:
        src, dst, dist= elements
        g.addEdge(cos239_dict[src], cos239_dict[dst])
        g.addEdge(cos239_dict[dst], cos239_dict[src])
        monitor_distance_dict[(src,dst)]=dist
        monitor_distance_dict[(dst,src)] = dist

    # 2 node pairs as input if multiple paths needed re-run it with another node pairs and pass the paths

    print(monitor_distance_dict)

    paths = g.find_routes(max_hops=10, sharing_degree=0, node_pairs=[('london', 'amsterdam'), ('london', 'zurich')])

    #channels_list = [range(1, 16), range(16, 31), range(75, 91)]  # estimation
    #channels_list = [range(1, 16), range(16, 31), range(31, 46)]  # estimation
    #channels_list = [range(1, 16), range(1, 16), range(31, 46)]
    channelsa_list = [
        59, 25, 71, 79, 10, 34, 57, 15, 40, 23, 39, 66, 46, 17, 53, 67, 61, 55, 26, 76, 24, 11, 28, 60, 47, 62, 50, 86,
        19, 6, 73, 69, 3, 89, 14, 27, 84, 35, 68, 16, 72, 80, 51, 7, 21, 85, 41, 45, 38, 5, 77, 8, 42, 81, 52, 64, 43,
        2, 87, 88, 65, 36, 30, 78, 70, 18, 37, 29, 63, 74, 56, 4, 20, 83, 1, 12, 9, 58, 44, 49, 54]

    channels_list = [[1, 2, 3, 4, 5, 6, 7, 8, 73, 74, 75, 85, 86], channelsa_list[16:30], range(75, 91)]
    used_path=paths[65]
    used_path=[[], [['london', 'brussels', 'paris', 'berlin', 'amsterdam'],['london', 'copenhagen', 'prague', 'luxembourg', 'zurich']]]

    # Currently we pass the first path out of the list but can be changed depending upon the the distance of the overall path or the common link
    if len(paths)!=0:
        print(used_path)

        estimation(net, channels_list, path_list=[used_path], monitor_dist_dict=monitor_distance_dict)
        configure_terminals(net, channels_list, path_list=[used_path])
        configure_roadms(net, channels_list, path_list=[used_path])
        transmit(net, channels_list, path_list=[used_path])

        densities = [100]
        for density in densities:
            monitor(net, density=density, path_list=[used_path], monitor_dist=monitor_distance_dict)

        visualize(net, amplifiers=False, transceivers=False, display_mode="breadthfirst")



def estimation(net, channels_list,path_list=[],monitor_dist_dict={}):
    node_list = {}
    links_dir1=[]
    links=[]
    for paths in path_list:
        for route in paths[1]:
            route_folder = []
            link_route = []
            for index in range(0, len(route) - 1):
                src = route[index]
                dst = route[index + 1]
                if src not in node_list.keys():
                    node_list[src] = net.name_to_node['r_' + str(src)]
                if dst not in node_list.keys():
                    node_list[dst] = net.name_to_node['r_' + str(dst)]
                string_folder = str(src) + '-' + str(dst) + '/'
                route_folder.append(string_folder)
                link_route.append((node_list[src], node_list[dst]))
            links_dir1.append(tuple(route_folder))
            links.append(tuple(link_route))

    for _tuple, channels, link_dir in zip(links, channels_list, links_dir1):
        main_struct = build_struct(15, signal_ids=channels)
        if type(_tuple[0]) is not tuple:
            link = net.find_link_from_nodes(_tuple[0], _tuple[1])
            spans = []
            for span in link.spans:
                spans.append(span.span.length / 1.0e3)
            estimation_module_simpledemo(main_struct, spans, link_dir,monitor_dist_dict=monitor_dist_dict,to_write_files=True)
        else:
            for i, (subtuple, link_dir_it) in enumerate(zip(_tuple, link_dir), start=1):
                link = net.find_link_from_nodes(subtuple[0], subtuple[1])
                spans = []
                for span in link.spans:
                    spans.append(span.span.length / 1.0e3)
                if i == len(_tuple):
                    estimation_module_simpledemo(main_struct, spans, link_dir_it,monitor_dist_dict=monitor_dist_dict,to_write_files=True)
                else:
                    main_struct = estimation_module_simpledemo(main_struct, spans, link_dir_it, last=False,monitor_dist_dict=monitor_dist_dict,to_write_files=True)


def configure_terminals(net, channels_list,path_list=[]):
    # retrieve the terminal objects from net

    lt_list1=[]

    for paths in path_list:
        for route in paths[1]:
            if route[0] not in lt_list1:
                lt_list1.append(net.name_to_node['lt_' + str(route[0])])



    for lt, channels in zip(lt_list1, channels_list):
        transceivers = lt.transceivers
        for i, channel in enumerate(channels, start=channels[0]):
            # channels are enumerated starting from 1
            # transceivers and their ports are enumerated starting from 0
            t = transceivers[i - 1]
            # associate transceiver to channel in LineTerminal
            lt.configure_terminal(t, [channel])


def configure_roadms(net, channels_list,path_list=[]):
    """
    This procedure is long because everything is done manually.
    """

    dst_lt_list=[]
    links1 = []

    for paths in path_list:
        for route in paths[1]:
            link_route = []
            node_list={}
            if route[-1] not in dst_lt_list:
                dst_lt_list.append(net.name_to_node['lt_' + str(route[-1])])
            for index in range(0, len(route) - 1):
                src = route[index]
                dst = route[index + 1]
                if src not in node_list.keys():
                    node_list[src] = net.name_to_node['r_' + str(src)]
                if dst not in node_list.keys():
                    node_list[dst] = net.name_to_node['r_' + str(dst)]
                link_route.append((node_list[src], node_list[dst]))
            links1.append(tuple(link_route))



    for _tuples, channels, dst_lt in zip(links1, channels_list,dst_lt_list):
        in_port_lt=channels[0]-1
        out_port = net.find_link_and_out_port_from_nodes(_tuples[0][0],_tuples[0][1])
        for i, channel in enumerate(channels, start=1):
            _tuples[0][0].install_switch_rule(i, in_port_lt, out_port, [channel])
            in_port_lt =in_port_lt+1


        for index in range(0,len(_tuples)-1):
            src_in,dst_in=_tuples[index]
            src_out, dst_out = _tuples[index+1]
            in_port = net.find_link_and_in_port_from_nodes(src_in,dst_in)
            out_port = net.find_link_and_out_port_from_nodes(src_out, dst_out)
            dst_in.install_switch_rule(1, in_port, out_port, channels)


        in_port = net.find_link_and_in_port_from_nodes(_tuples[-1][0], _tuples[-1][1])
        out_port = net.find_link_and_out_port_from_nodes(_tuples[-1][1],dst_lt)
        _tuples[-1][1].install_switch_rule(2, in_port, out_port, channels)



def transmit(net, channels_list,path_list=[]):
    lt_list1 = []

    for paths in path_list:
        for route in paths[1]:
            if route[0] not in lt_list1:
                lt_list1.append(net.name_to_node['lt_' + str(route[0])])


    for lt, channels in zip(lt_list1, channels_list):
       lt.turn_on()



def monitor(net, density=10, first_last='first',path_list=[],monitor_dist={}):
    """
    net: network object
    density: density percentage (10 = 10%, 30 = 30%, etc)
    first_last: when 1 OPM is to be used, decide whether using
    the first one (boost-monitor) or last one (pre-amp-monitor) in the link
    """

    node_list=[]
    step=50

    for paths in path_list:
        for route in paths[1]:
            monitor_list=[]
            for index in range(0, len(route) - 1):
                src = route[index]
                dst = route[index + 1]
                no_monitors=round(monitor_dist[(src,dst)]/step)
                monitor_list = ['r_'+str(src)+'-r_'+str(dst)+'-amp'+str(i) for i in range(1, no_monitors+1)]
                monitor_list.insert(0,'r_'+str(src)+'-r_'+str(dst)+'-boost')
                monitor_list = monitor_deployment(monitor_list, density=density, first_last=first_last)
                for monitor_name in monitor_list:
                   monitor_query(net, monitor_name, density)
                print(monitor_list)





def monitor_deployment(monitor_link, density=10, first_last='first'):
    # if using 100% OPM density
    if density == 100:
        return monitor_link

    # compute number of OPMs given the density
    monitor_no = int(len(monitor_link) * density*1e-2)
    # list with the monitors to be used
    monitors = []

    if monitor_no <= 1:
        # if monitor_no is 0 or 1, use either the
        # first one (boost) or last one (pre-amp)
        if first_last == 'first':
            monitors.append(monitor_link[0])
        else:
            monitors.append(monitor_link[-1])
    else:
        # if monitor_no >= 2, select monitors in an even manner
        monitors = monitor_select(monitor_link, monitor_no)
    return monitors


def monitor_select(monitor_link, monitor_no):
    n = len(monitor_link)
    # select indices from even_select algorithm
    indices = even_select(n, monitor_no)
    monitors = []
    for i, k in enumerate(indices):
        if k == 0:
            monitors.append(monitor_link[i])
    return monitors


def even_select(n, m):
    """
    n: number of OPMs in link
    m: number of OPMs required
    return: list [0,1] with location of OPMs
    to be considered (0) and ignored (1) as per
    their location in the link
    """
    if m > n/2:
        cut = np.zeros(n, dtype=int)
        q, r = divmod(n, n-m)
        indices = [q*i + min(i, r) for i in range(n-m)]
        cut[indices] = True
    else:
        cut = np.ones(n, dtype=int)
        q, r = divmod(n, m)
        indices = [q*i + min(i, r) for i in range(m)]
        cut[indices] = False
    return cut


def monitor_query(net, component_name, density):
    x = component_name.split('-', 2)
    link_label = x[0] + '-' + x[1]
    monitor = net.name_to_node[component_name].monitor

    osnrdata = {int(signal.index):
                    dict(freq=signal.frequency, osnr=monitor.get_osnr(signal),
                         gosnr=monitor.get_gosnr(signal),
                         power=monitor.get_power(signal),
                         ase=monitor.get_ase_noise(signal),
                         nli=monitor.get_nli_noise(signal))
                for signal in net.name_to_node[component_name].optical_signals}

    osnrs, gosnrs = {}, {}
    powers, ases, nlis = {}, {}, {}
    for channel, data in osnrdata.items():
        osnr, gosnr = data['osnr'], data['gosnr']
        power, ase, nli = data['power'], data['ase'], data['nli']
        osnrs[channel] = osnr
        gosnrs[channel] = gosnr
        powers[channel] = power
        ases[channel] = ase
        nlis[channel] = nli

    json_struct = {'tests': []}
    write_files(osnrs, gosnrs, powers, ases, nlis,
                json_struct, link_label, component_name, density)


def write_files(osnr, gosnr, powers, ases, nlis,
                json_struct, link_label, monitor_name, density):
    """
    Write a file with osnr and gosnr information from a given OPM node
    """
    _osnr_id = 'osnr'
    _gosnr_id = 'gosnr'
    _power_id = 'power'
    _ase_id = 'ase'
    _nli_id = 'nli'
    json_struct['tests'].append({_osnr_id: osnr})
    json_struct['tests'].append({_gosnr_id: gosnr})
    json_struct['tests'].append({_power_id: powers})
    json_struct['tests'].append({_ase_id: ases})
    json_struct['tests'].append({_nli_id: nlis})

    if link_label not in link_in_consideration:
        link_in_consideration.append(link_label)


    test = 'cost239-monitor/monitor-module-new/'
    dir_ = test + link_label + '/'
    #dir_ = test + link_label + '/density_' + str(density) + '/'
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    json_file_name = dir_ + monitor_name + '.json'
    with open(json_file_name, 'w+') as outfile:
        json.dump(json_struct, outfile)


if __name__ == '__main__':
    with open('seeds/wdg_seed_simpledemo.txt', 'r') as filename:
        data = filename.readline()
        seeds2 = data.split(',')
        seeds2 = seeds2[:-1]
    net = Cost239Topology.build()
    for amp, ripple in zip(net.amplifiers, seeds2):
        amp.set_ripple_function(ripple)
    run(net)
    print(link_in_consideration)

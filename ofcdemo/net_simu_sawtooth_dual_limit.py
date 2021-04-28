#!/usr/bin/python
"""
single_link_test.py: test monitoring on a single link

Note this version uses and depends on explicit port assignment!
"""

from network import Network
from link import Span as Fiber, SpanTuple as Segment
from node import Transceiver
from units import *
from collections import defaultdict
import random
from collections import defaultdict
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from scipy import signal


km = dB = dBm = 1.0
m = .001

# Parameters


NUM_WAV = 90
LINK_CAP = 200
DOWN_LINK_CAP = 100
CPRI_CAP = 25
# ROADM port numbers (input and output)
LINE_PORT1, LINE_PORT2, LINE_PORT3, LINE_PORT4, LINE_PORT5, LINE_PORT6 = NUM_WAV, NUM_WAV+1, NUM_WAV+2, NUM_WAV+3, NUM_WAV+4, NUM_WAV+5
NETLINKS = []
GRAPH = defaultdict()
NODES = defaultdict()
NETLINK_INFO = defaultdict( defaultdict ) # ('node_name', 'node_name'): {channel_id: lightpath_id}
TRAFFIC_INFO = defaultdict( defaultdict ) # id : {'src':src, 'dst':dst, 'lightpath_id': lightpath_id, 'up_time':s_time, 'down_time': d_time, 'latency': 0}     # id : {'path':path, 'channel':channel_id, 'up_time':s_time, 'down_time': d_time}
LIGHTPATH_INFO = defaultdict( defaultdict ) # id : {'path':path, 'channel_id': channel_id, 'traf_set': set(), 'up_time':s_time, 'down_time': d_time, 'OSNR': 25, 'GOSNR': 24.5 }
SRC_DST_TO_LIGHTPATH = defaultdict( set ) # (src, dst) : {set[lightpath_id]}
PATH_CH_TO_LIGHTPATH = defaultdict(defaultdict) # (src, hop, dst) : {'channel_id': lightpath_id}
TRAFFIC_ID = 0
LIGHTPATH_ID = 0
NUM_NODE = 7
NAME_ROADM = []
UP_TRAF_TIME_LIST = []
UP_TRAF_ID_SET = set()
UP_LIGHTPATH_TIME_LIST = []
UP_LIGHTPATH_ID_SET = set()
ALL_CHANNELS = [ i for i in range(1,NUM_WAV+1)]
RU_ROADMS = []
DU_ROADMS = ['r1', 'r4', 'r7']
ROADM_TRAF = defaultdict(set)

# Mininet-Optical
name_roadms = []
name_terminals = []
Roadm_Rule_ID_dict = {}
ROADM_TO_TERMINAL = {}
TERMINAL_TO_ROADM = {}
for i in range(NUM_NODE):
    name_roadms.append('r%d'%(i+1))
    name_terminals.append('t%d'%(i+1))
    Roadm_Rule_ID_dict['r%d' % (i + 1)] = 1
    ROADM_TO_TERMINAL['r%d' % (i + 1)] = 't%d' % (i + 1)
    TERMINAL_TO_ROADM['t%d' % (i + 1)] = 'r%d' % (i + 1)
    node = 'r%d' %(i+1)
    if node not in DU_ROADMS:
        RU_ROADMS.append(node)


for i in range(NUM_NODE):
    NAME_ROADM.append('r%d' % (i + 1))



# Physical model API helpers

def Span( km, amp=None ):
    "Return a fiber segment of length km with a compensating amp"
    return Segment( span=Fiber( length=km ), amplifier=amp )

# Physical Network simulation, created out of base PHY model objects

def RoadmPhyNetwork():

    """ROADM network topo
    """
    ###############################
    #      t1 - r1 ----- r2 - t2
    #                    |
    #                    r3 - t3
    #                    |
    #      t5 - r5 ----- r4 - t4
    ################################

    net = Network()
    lengths = [15 * km]

    # Network nodes
    transceivers = [('tx%d' % i, 0 * dBm, 'C') for i in range(1, NUM_WAV + 1)]

    # each terminal includes NUM_WAV transceivers
    terminals = [
        net.add_lt(name, transceivers=transceivers, monitor_mode=mode)
        for name, mode in [('t%d' % i, 'in') for i in range(1, NUM_NODE + 1)]]
    roadms = [
        net.add_roadm(name, monitor_mode=mode)
        for name, mode in [('r%d' % i, 'in') for i in range(1, NUM_NODE + 1)]]

    # roadms = [ net.add_roadm( 'r%d' % i ) for i in (1, 2, 3) ]
    nodes = net.name_to_node
    # Convenience alias
    link = net.add_link

    for k in range(1, NUM_NODE):
        print('==range=', k)
        # Eastbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers
        boost = net.add_amplifier('boost{}{}'.format(k, k + 1), target_gain=17 * dB, boost=True)
        spans = []
        for i, length in enumerate(lengths, start=1):
            amp = net.add_amplifier(
                'amp{}{}-{}'.format(k, k + 1, i), target_gain=length * 0.22 * dB, monitor_mode='out')
            span = Span(length, amp=amp)
            spans.append(span)

        link(nodes['r%d' % k], nodes['r%d' % (k + 1)], src_out_port=LINE_PORT2, dst_in_port=LINE_PORT1, boost_amp=boost,
             spans=spans)
        NETLINKS.append(('r%d' % k, LINE_PORT2, 'r%d' % (k + 1), LINE_PORT1))
        NETLINK_INFO['r%d' % k, 'r%d' % (k + 1)] = {0: 0}

        # Westbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers
        boost = net.add_amplifier('boost{}{}'.format(k + 1, k), target_gain=17 * dB, boost=True)
        spans = []
        for i, length in enumerate(lengths, start=1):
            amp = net.add_amplifier(
                'amp{}{}-{}'.format(k + 1, k, i), target_gain=length * 0.22 * dB, monitor_mode='out')
            span = Span(length, amp=amp)
            spans.append(span)

        link(nodes['r%d' % (k + 1)], nodes['r%d' % k], src_out_port=LINE_PORT1, dst_in_port=LINE_PORT2, boost_amp=boost,
             spans=spans)
        NETLINKS.append(('r%d' % (k + 1), LINE_PORT1, 'r%d' % k, LINE_PORT2))
        NETLINK_INFO['r%d' % (k + 1), 'r%d' % k] = {0: 0}

    for k in range(1,NUM_NODE+1):
        # Local add/drop links between terminals/transceivers and ROADMs
        for add_drop_port in range(NUM_WAV):
            link( nodes['t%d' %k], nodes['r%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
            link( nodes['r%d' %k], nodes['t%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )

            NETLINKS.append(('t%d' %k, add_drop_port, 'r%d' %k, add_drop_port))
            NETLINKS.append(('r%d' %k, add_drop_port, 't%d' %k, add_drop_port))

    return net

############# Mininet Optical############

def Mininet_installPath(lightpath_id, path, channels, graph, nodes):
    "intall switch rules on roadms along a lightpath for some signal channels"

    # Install ROADM rules
    print(graph, nodes)
    for channel in channels:
        #print(channel)
        rule_path = {}
        #print(path)
        for i in range(1, len(path) - 1 ):
            node1, roadm, node2 = path[i-1], path[i], path[i+1]
            port1 = graph[ node1 ][ roadm ]
            port2 = graph[ node2 ][ roadm ]
            #print('==route port', i,(node1,roadm,port1), (node2,roadm,port2))
            if i == 1:
                    nodes[roadm].install_switch_rule(rule_id=Roadm_Rule_ID_dict[roadm], in_port=channel - 1, out_port=port2,
                                                     signal_indices=[channel])
                    rule_path[roadm] = Roadm_Rule_ID_dict[roadm]
                    Roadm_Rule_ID_dict[roadm] += 1
            elif i == len(path) - 2:
                nodes[roadm].install_switch_rule(rule_id=Roadm_Rule_ID_dict[roadm], in_port=port1, out_port=channel - 1,
                                                 signal_indices=[channel])
                rule_path[roadm] = Roadm_Rule_ID_dict[roadm]
                Roadm_Rule_ID_dict[roadm] += 1
            else:
                nodes[roadm].install_switch_rule(rule_id=Roadm_Rule_ID_dict[roadm], in_port=port1, out_port=port2,
                                                 signal_indices=[channel])
                rule_path[roadm] = Roadm_Rule_ID_dict[roadm]
                Roadm_Rule_ID_dict[roadm] += 1
            LIGHTPATH_INFO[lightpath_id]['rule_path'] = rule_path


def Mininet_uninstallPath(lightpath_id, nodes):
    "delete switch rules on roadms along a lightpath for some signal channels"


    path = LIGHTPATH_INFO[lightpath_id]['path']
    rule_path = LIGHTPATH_INFO[lightpath_id]['rule_path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    Mininet_turnoffTerminalChannel(terminal=nodes[path[0]], channel=channel)
    for i in range(1, len(path) - 1):
        roadm = path[i]
        nodes[roadm].delete_switch_rule(rule_path[roadm])



def Mininet_setupLightpath(lightpath_id, path, channel, power, graph, nodes):
    channel = channel[0]
    Mininet_installPath(lightpath_id, path, [channel], graph, nodes)
    Mininet_configTerminalChannelPower(terminal= nodes[path[0]], channel=channel, power=power)
    Mininet_voaPowerLeveling(path=path, channel=channel, power=power, graph=graph, nodes=nodes)
    Mininet_configTerminalChannel(terminal=nodes[path[0]], channel=channel)
    return True


def Mininet_teardownLightpath(lightpath_id, nodes):

    Mininet_uninstallPath(lightpath_id, nodes)
    return True


def Mininet_voaPowerLeveling(path, channel, power, graph, nodes):
    "Power control for a signal channel at a roadm using VOA leveling"

    for i in range(1, len(path) - 1):
        node1, roadm, node2 = path[i - 1], path[i], path[i + 1]
        if i == len(path) - 2:
            nodes[roadm].configure_voa(channel_id=channel, output_port=channel - 1, operational_power_dB=power)
        else:
            nodes[roadm].configure_voa(channel_id=channel, output_port=graph[node2][roadm], operational_power_dB=power)


def Mininet_configTerminalChannelPower(terminal, channel, power):
    "Congifure Terminal Launch power for a channel"

    terminal.name_to_transceivers['tx%d'% channel].operation_power = db_to_abs(power)


def Mininet_configTerminalChannel(terminal, channel):
    "Turn on a Terminal with a given channel"

    terminal.configure_terminal(transceiver=terminal.transceivers[channel-1], channel=channel)
    terminal.turn_on()


def Mininet_turnoffTerminalChannel(terminal, channel):
    "Turn on a Terminal with a given channel"

    terminal.turn_off([channel-1])


def Mininet_monitorAll(node):
    "monitoring all data at a node"

    return node.monitor.get_dict_power(),node.monitor.get_dict_osnr(), node.monitor.get_dict_gosnr()


def Mininet_monitorLightpath(path, channel, nodes):
    "monitoring a signal along a lightpath"
    #print('monitor_path_ch', path, channel)

    powers = list()
    osnrs = list()
    gosnrs = list()
    ase_noise = list()
    nli_noise = list()
    freq = round((191.30 + 0.05*channel)*10**12,1)
    for i in range(1, len(path) - 1):
        name = path[i]
        node = nodes[name]
        optical_signals = node.monitor.extract_optical_signal()
        for sig in optical_signals:
            if freq==sig[0].frequency:
                if node.monitor.mode == 'out':
                    output_power = (sig[0].loc_out_to_state[node.monitor.component]['power'])
                    ase = (sig[0].loc_out_to_state[node.monitor.component]['ase_noise'])
                    nli = (sig[0].loc_out_to_state[node.monitor.component]['nli_noise'])
                else:
                    output_power = (sig[0].loc_in_to_state[node.monitor.component]['power'])
                    ase = (sig[0].loc_in_to_state[node.monitor.component]['ase_noise'])
                    nli = (sig[0].loc_in_to_state[node.monitor.component]['nli_noise'])
                gosnr_linear = output_power / (ase + nli * (12.5e9 / 32.0e9))
                gosnr = abs_to_db(gosnr_linear)
                osnr_linear = output_power / ase
                osnr = abs_to_db(osnr_linear)
                powers.append(output_power)
                osnrs.append(osnr)
                gosnrs.append(gosnr)
                ase_noise.append(ase)
                nli_noise.append(nli)
                #powers.append((name,output_power))
                #osnrs.append((name,osnr))
                #gosnrs.append((name,gosnr))
    return powers, osnrs, gosnrs, ase_noise, nli_noise

################# END ####################


################ CONTROL PLANE #####################

def linkspec( link ):
    "Return specifier dict(node1, port1, node2, port2) for link"
    node1, node2, port1, port2 = link[0], link[2], link[1], link[3]
    return { node1:port1, node2:port2 }


def getLinks():

    return dict( links=[ linkspec( link ) for link in NETLINKS ] )


def netGraph( links ):
    "Return an adjacency dict for links"
    # Note we only have to worry about single links between nodes
    # We handle the terminals separately
    neighbors = defaultdict( defaultdict )
    for link in links:
        #print(link)
        src, dst = link  # link is a dict but order doesn't matter
        srcport, dstport = link[ src ], link[ dst ]
        neighbors.setdefault( src, {} )
        neighbors[ src ][ dst ] = dstport
        neighbors[ dst ][ src ] = srcport
    return dict( neighbors )


def FindRoute( src, graph, destinations, k=10):
    """Route from src to destinations
       neighbors: adjacency list
       returns: routes dict"""
    routes, seen, paths = defaultdict(list), set( (src,) ), [ (src,) ]
    while paths:
        path = paths.pop( 0 )
        lastNode = path[ -1 ]
        for neighbor in graph[ lastNode ]:
            if neighbor not in path:
                newPath = ( path + (neighbor, ) )
                paths.append( newPath )
                if neighbor in destinations and len(routes[ neighbor ]) < k:
                    routes[ neighbor ].append(newPath)
    return routes


def shortestPath():
    return

def pathSelection(paths, cur_time, waiting_time_threshold=5.0, short_duration=False):
    new_paths = []
    for path in paths:
        avai_channels = waveAvailibility(path)
        occupied_channels = set(ALL_CHANNELS).difference(avai_channels)
        max_waiting_time = defaultdict(lambda: 0)
        for i in range(len(path) - 1):
            for j in occupied_channels:
                if j in NETLINK_INFO[path[i], path[i + 1]].keys():
                    lightpath_id = NETLINK_INFO[path[i], path[i + 1]][j]
                    waiting_time = LIGHTPATH_INFO[lightpath_id]['down_time'] - cur_time
                    # print('waiting', j, waiting_time)
                    max_waiting_time[j] = max(waiting_time, max_waiting_time[j])
        possible_channels = set()
        # print('waiting', path, max_waiting_time)
        for ch in occupied_channels:
            # print(max_waiting_time[ch])
            if max_waiting_time[ch] < waiting_time_threshold:
                possible_channels.add(ch)
        ## if this lightpath will be teared town soon
        ## if this lightpath will be teared town soon
        if short_duration:
            new_paths.append((-len(possible_channels), -len(avai_channels), len(path), path))
        else:
            new_paths.append((-len(possible_channels)-len(avai_channels), -len(avai_channels), len(path), path))
    new_paths.sort()
    #print('sort_path', new_paths)
    return new_paths


def waveAvailibility(path):
    avai_channels = set([i for i in range(NUM_WAV + 1)])
    for i in range(len(path) - 1):
        link_channels = set(NETLINK_INFO[path[i], path[i + 1]].keys())
        avai_channels = avai_channels.difference(link_channels)
    return avai_channels


def waveSelection(channels):
    channels = list(channels)
    return random.choice(channels)


def install_Lightpath(path, channel, up_time=0.0, down_time = float('inf')):
    "intall switch rules on roadms along a lightpath for some signal channels"

    ## Install ROADM rules
    global LIGHTPATH_ID
    LIGHTPATH_ID += 1
    for i in range(len(path) - 1):
        NETLINK_INFO[path[i], path[i + 1]][channel] = LIGHTPATH_ID  # channel with lightpath_id
        NETLINK_INFO[path[i + 1], path[i]][channel] = LIGHTPATH_ID
    # id : {'path':path, 'channel': channel_id, 'traf': set(), 'up_time':s_time, 'down_time': d_time, 'OSNR': 25, 'GOSNR': 24.5 }
    Mininet_setupLightpath(lightpath_id=LIGHTPATH_ID, path=path, power=-1, channel=[channel], graph=GRAPH, nodes=NODES)
    powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path, channel, NODES)
    LIGHTPATH_INFO[LIGHTPATH_ID]['path'] = path
    LIGHTPATH_INFO[LIGHTPATH_ID]['channel_id'] = channel
    LIGHTPATH_INFO[LIGHTPATH_ID]['link_cap'] = LINK_CAP
    LIGHTPATH_INFO[LIGHTPATH_ID]['traf_set'] = set()
    LIGHTPATH_INFO[LIGHTPATH_ID]['up_time'] = up_time
    LIGHTPATH_INFO[LIGHTPATH_ID]['down_time'] = down_time
    LIGHTPATH_INFO[LIGHTPATH_ID]['power'] = abs_to_db(powers[-1])
    LIGHTPATH_INFO[LIGHTPATH_ID]['OSNR'] = osnrs[-1]
    LIGHTPATH_INFO[LIGHTPATH_ID]['GOSNR'] = gosnrs[-1]
    # (src, dst) : {1,2,3,4,5}  ##lightpath_id
    SRC_DST_TO_LIGHTPATH[path[0], path[-1]].add(LIGHTPATH_ID)
    # (src, hop, dst) : {'channel_id': lightpath_id}
    PATH_CH_TO_LIGHTPATH[path][channel] = LIGHTPATH_ID
    UP_LIGHTPATH_TIME_LIST.append((down_time, LIGHTPATH_ID))
    UP_LIGHTPATH_TIME_LIST.sort()
    UP_LIGHTPATH_ID_SET.add(LIGHTPATH_ID)


    return LIGHTPATH_ID


def check_lightpath_for_traf(src, dst):
    '''
    check if there are some provisioned lighpaths for CPRI traf
    '''
    lighpaths = SRC_DST_TO_LIGHTPATH[src,dst]
    avai_lightpaths = set()
    for lighpath_id in lighpaths:
        if len(LIGHTPATH_INFO[lighpath_id]['traf_set']) < LIGHTPATH_INFO[lighpath_id]['link_cap']/CPRI_CAP:
            avai_lightpaths.add(lighpath_id)
    return avai_lightpaths


def select_lightpath_by_latency(avai_lightpaths, latency=0):
    for lightpath_id in avai_lightpaths:
        path = LIGHTPATH_INFO[lightpath_id]['path']
        GOSNR = LIGHTPATH_INFO[lightpath_id]['GOSNR']
        if latency == 0 or latency == 1:
            if len(path) < 4 and GOSNR > 25:
                return lightpath_id
        else:
            return lightpath_id
    return False


def update_lightpath_down_time(lightpath_id, down_time):
    for d_time, id in UP_LIGHTPATH_TIME_LIST:
        if id == lightpath_id:
            UP_LIGHTPATH_TIME_LIST.remove((d_time, id))
            UP_LIGHTPATH_TIME_LIST.append((down_time, lightpath_id))
            UP_LIGHTPATH_TIME_LIST.sort()


def traf_to_lightpah_Assignment(traf_id, lightpath_id, down_time = float('inf')):
    # (src, hop, dst) : {'channel_id': lightpath_id}
    LIGHTPATH_INFO[lightpath_id]['traf_set'].add(traf_id)
    path = LIGHTPATH_INFO[lightpath_id]['path']
    if down_time > LIGHTPATH_INFO[lightpath_id]['down_time']:
        LIGHTPATH_INFO[lightpath_id]['down_time'] = down_time
        update_lightpath_down_time(lightpath_id, down_time)
    # traf_id : {'src':src, 'dst':dst, 'lightpath_id': lightpath_id, 'up_time':s_time, 'down_time': d_time, 'latency': 0}
    TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst'], TRAFFIC_INFO[traf_id]['lightpath_id'] = path[0], path[-1], lightpath_id
    UP_TRAF_TIME_LIST.append((down_time, traf_id))
    UP_TRAF_TIME_LIST.sort()
    UP_TRAF_ID_SET.add(traf_id)
    return traf_id


def install_Traf(src, dst, routes, cur_time, down_time=float('inf'), latency = 0, RWA = True):
    '''
    source RRH node to destination BBU node
    latency: 0 for ultra-low: only use provisioned lightpaths with high BW and BER,
            1 low latency: can setup lightpath but need high BW and high BER/GOSNR,
            2 no latency requirement: any lightpath
    '''
    global TRAFFIC_ID
    avai_lightpaths = check_lightpath_for_traf(src, dst)
    lightpath_id = select_lightpath_by_latency(avai_lightpaths, latency)
    #print('---avai_lightpaths, select lightpath_id--', avai_lightpaths, lightpath_id)
    if latency == 0 :
        if lightpath_id:
            TRAFFIC_ID += 1
            traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
            return traf_id
    elif latency == 1:
        if lightpath_id:
            TRAFFIC_ID += 1
            traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
            return traf_id
        else:
            if RWA:
                all_path_info = pathSelection(paths= routes[src][dst], cur_time = cur_time, waiting_time_threshold=5.0, short_duration=True)
            else:
                all_path_info = routes[src][dst]
            # [ (len(possible_channels), len(ava_channls), len(path), paths), ... ]
            for path_info in all_path_info:
                if RWA:
                    path = path_info[3]
                else:
                    path = path_info
                if len(path)>=4:
                    continue
                chs = waveAvailibility(path=path)
                if chs:
                    count = 0
                    while count < 5 and chs:
                        count += 1
                        ch = waveSelection(chs)
                        chs.remove(ch)
                        lightpath_id = install_Lightpath(path=path, channel=ch, up_time=cur_time, down_time=down_time)
                        GOSNR = LIGHTPATH_INFO[lightpath_id]['GOSNR']
                        if GOSNR > 25:
                            TRAFFIC_ID += 1
                            traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
                            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
                            return traf_id
                        else:
                            uninstall_Lightpath(lightpath_id)
    elif latency == 2:
        if lightpath_id:
            TRAFFIC_ID += 1
            traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
            return traf_id
        else:
            if RWA:
                all_path_info = pathSelection(paths=routes[src][dst], cur_time=cur_time, waiting_time_threshold=5.0,
                                              short_duration=True)
            else:
                all_path_info = routes[src][dst]
            # [ (len(possible_channels), len(ava_channls), len(path), paths), ... ]
            for path_info in all_path_info:
                if RWA:
                    path = path_info[3]
                else:
                    path = path_info
                chs = waveAvailibility(path=path)
                if chs:
                    count = 0
                    while count < 5 and chs:
                        count += 1
                        ch = waveSelection(chs)
                        chs.remove(ch)
                        lightpath_id = install_Lightpath(path=path, channel=ch, up_time=cur_time, down_time=down_time)
                        TRAFFIC_ID += 1
                        traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
                        LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
                        return traf_id
    return False


def uninstall_Lightpath(lightpath_id):
    "delete switch rules on roadms along a lightpath for some signal channels"
    Mininet_uninstallPath(lightpath_id=lightpath_id, nodes=NODES)
    path = LIGHTPATH_INFO[lightpath_id]['path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    for i in range(len(path) - 1):
        del NETLINK_INFO[path[i], path[i + 1]][channel]
        del NETLINK_INFO[path[i + 1], path[i]][channel]
    #print(PATH_CH_TO_LIGHTPATH)
    lightpath_id = PATH_CH_TO_LIGHTPATH[path][channel]
    #print('==', lightpath_id)
    del LIGHTPATH_INFO[lightpath_id]
    del PATH_CH_TO_LIGHTPATH[path][channel]
    SRC_DST_TO_LIGHTPATH[path[0], path[-1]].remove(lightpath_id)
    UP_LIGHTPATH_ID_SET.remove(lightpath_id)

    return lightpath_id


def traf_to_lightpath_Release(traf_id):
    lightpath_id = TRAFFIC_INFO[traf_id]['lightpath_id']
    LIGHTPATH_INFO[lightpath_id]['traf_set'].remove(traf_id)
    del TRAFFIC_INFO[traf_id]
    UP_TRAF_ID_SET.remove(traf_id)
    return traf_id

################# END ###################

def analytic_traffic(time, shift=0, floor=0.0001, timelength=8, days=1, pattern = 'sawtooth', source='office'):
    """Graphs a sawtooth traffic pattern as a means to analytically study the system.
    _/\_/\_/\_/\_/\_/\_/\_/\ This allows is to examine analytical properties of the
    system."""
    time = time - 0.000125
    if pattern == 'sawtooth':
        if source == 'office':
            if time % 24 < timelength:
                factor = ((sp.signal.sawtooth(2 * np.pi * (time % 24) / timelength, 0) + 1) / 2) * (1-floor) + floor
                return factor
            else:
                return floor
        if source == 'resident':
            if shift < (float(time) % 24) and (float(time) % 24) < (timelength + shift):
                factor = ((sp.signal.sawtooth(2 * np.pi * ((time % 24) -shift) / timelength, 0) + 1) / 2) * (1-floor) + floor
                return factor
            else:
                return  floor
    if pattern == 'triangle':
        if source == 'office':
            if time % 24 < timelength:
                factor = ((sp.signal.sawtooth(2 * np.pi * (time % 24)  / timelength, 0.5) + 1) / 2) * (1-floor) + floor
                return factor
            else:
                return floor
        if source == 'resident':
            if shift < (float(time) % 24) and (float(time) % 24) < (timelength + shift):
                factor = ((sp.signal.sawtooth(2 * np.pi * ((time % 24) -shift) / timelength, 0.5) + 1) / 2) * (1-floor) + floor
                return factor
            else:
                return  floor

    if pattern == 'impulse':
        if source == 'office':
            if time % 24 < timelength:
                factor = 1
                return factor
            else:
                return floor
        if source == 'resident':
            if shift < (float(time) % 24) and (float(time) % 24) < (timelength + shift):
                factor = 1
                return factor
            else:
                return floor
    if pattern == 'step_down':
        if source == 'office':
            if time % (24*days) < timelength:
                factor = 1
                return factor
            else:
                return floor
        if source == 'resident':
            if shift < (float(time) % (24*days)) and (float(time) % (24*days)) < (timelength + shift):
                factor = 1
                return factor
            else:
                return floor

    else:
        raise ValueError('Error: function not found')



def TrafficTest(shift=0, floor=0.0001, timelength=8, pattern = 'sawtooth',load=35000, days=7, filename = 'sawtooth_results.txt'):
    """Create an analytical study of Mininet Optical's behavious. This will be done using
    a sawtooth simulation of relevent data to produce results."""
    net = RoadmPhyNetwork()
    AllLinks = getLinks()
    global  GRAPH, NODES
    GRAPH = netGraph(AllLinks['links'])
    NODES = net.name_to_node
    routes = {node: FindRoute(node, GRAPH, name_terminals)
               for node in name_terminals}

    print('===links', AllLinks['links'])
    print('===graph', GRAPH)
    print('==link_info', NETLINK_INFO)
    print('==route')

    for key in routes.keys():
        print(key, routes[key])


    Total_Rej = 0
    N = 24*days #Hours
    file = open(filename, 'w')
    # Overall Traffic information
    Total_traf = load # Gbps
    MAX_traf = {}
    for i in range(2,NUM_NODE): #Includes ROADMs 2,3,4,5, ROADM 1,2 are BBU nodes
        MAX_traf['r%d' %(i)] = 1.0*Total_traf/(len(RU_ROADMS))
    print('---max_traf',MAX_traf)


    BBU_traf = {}
    BBU_limit = {}
    BBU_limit['t1'] = 250 #* float('inf')
    BBU_limit['t%d' % NUM_NODE] = 250 #* float('inf')
    for node in DU_ROADMS:
        BBU_traf[ROADM_TO_TERMINAL[node]] = 0
    RRH_traf = {}
    for node in RU_ROADMS:
        RRH_traf[ROADM_TO_TERMINAL[node]] = 0

    ROADM_TYPE = {'r2':'office', 'r3':'resident', 'r5':'resident', 'r6':'office'}

    file.write(
        'time, r2-office_traf, r3-resident_traf, r5-resident_traf, r6-office_traf, '
        'number_of_lightpath, avg_wav_per_link, r1_BBU_traf, r6_BBU_traf, r4_BBU_traf,'
        ' r2-office_rej, r3-resident_rej, r5-resident_rej, r6-office_rej,'
        ' 50G, 100G, 200G, underutilized, Total_cap, Total_traffic\n')

    for i in range(N):
        Rej = {}
        for key in TERMINAL_TO_ROADM.keys():
            Rej[key] = 0
        print(i) #Prints the hour
        factors = {}
        for src in RU_ROADMS:
            f = analytic_traffic(time=i, shift=shift, floor=floor, timelength=timelength, days=days, pattern=pattern,
                                 source=ROADM_TYPE[src])
            factors[src] = f
            factor = f
            src_t = ROADM_TO_TERMINAL[src]
            count = 0
            while factor*MAX_traf[src]/CPRI_CAP > len(ROADM_TRAF[src]):
                ADD_TRAF = False
                print(factor*MAX_traf[src]/CPRI_CAP, len(ROADM_TRAF[src]), Rej)
                dst = random.choice(DU_ROADMS)

                RRH_traf[src_t] += 1
                path_first = routes[src_t]['t1'][0]
                path_last = routes[src_t]['t%d' % NUM_NODE][0]
                print('two_paths', path_first, path_last)
                if len(path_last)<len(path_first) and BBU_traf['t%d' % NUM_NODE] < BBU_limit['t%d' % NUM_NODE]:
                    print('BBU R7 resource',BBU_traf['t%d' % NUM_NODE], BBU_limit['t%d' % NUM_NODE])
                    dst = 'r%d' % NUM_NODE
                    dst_t = 't%d' % NUM_NODE
                    dst_back = 'r1'
                    dst_t_back = 't1'
                elif len(path_first)<len(path_last) and BBU_traf['t1'] < BBU_limit['t1']:
                    print('BBU R1 resource', BBU_traf['t1'], BBU_limit['t1'])
                    dst = 'r1'
                    dst_t = 't1'
                    dst_back = 'r%d' % NUM_NODE
                    dst_t_back = 't%d' % NUM_NODE
                else:
                    print('BBU R1 resource', BBU_traf['t1'], BBU_limit['t1'])
                    dst = 'r4'
                    dst_t = 't4'
                    dst_back = 'r4'
                    dst_t_back = 't4'


                traf_id = install_Traf(src_t, dst_t, routes, cur_time=0, down_time=float('inf'), latency=2, RWA=False)
                if traf_id:
                    ADD_TRAF = True
                    ROADM_TRAF[src].add(traf_id)
                    BBU_traf[dst_t] += 1
                    reassign_traf = []
                    fail_lightpaths = []
                    for lightpath_id, info in LIGHTPATH_INFO.items():
                        powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path=info['path'], channel=info['channel_id'], nodes=NODES)
                        LIGHTPATH_INFO[lightpath_id]['GOSNR'] = gosnrs[-1]
                        LIGHTPATH_INFO[lightpath_id]['OSNR'] = osnrs[-1]
                        if 18< gosnrs[-1] < 24:
                            LIGHTPATH_INFO[lightpath_id]['link_cap'] = DOWN_LINK_CAP
                            traf_set =  LIGHTPATH_INFO[lightpath_id]['traf_set']
                            while len(traf_set) > DOWN_LINK_CAP/CPRI_CAP:
                                 traf_id = random.choice(list(traf_set))
                                 s_t, d_t = TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst']
                                 ROADM_TRAF[TERMINAL_TO_ROADM[s_t]].remove(traf_id)
                                 traf_to_lightpath_Release(traf_id=traf_id)
                                 reassign_traf.append((s_t, d_t))
                        elif gosnrs[-1] < 16:
                            LIGHTPATH_INFO[lightpath_id]['link_cap'] = 50
                            traf_set =  LIGHTPATH_INFO[lightpath_id]['traf_set']
                            while len(traf_set) > DOWN_LINK_CAP/CPRI_CAP:
                                 traf_id = random.choice(list(traf_set))
                                 s_t, d_t = TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst']
                                 ROADM_TRAF[TERMINAL_TO_ROADM[s_t]].remove(traf_id)
                                 traf_to_lightpath_Release(traf_id=traf_id)
                                 reassign_traf.append((s_t, d_t))
                        else:
                            LIGHTPATH_INFO[lightpath_id]['link_cap'] = LINK_CAP


                    for s_t, d_t in reassign_traf:
                        traf_id = install_Traf(s_t, d_t, routes, cur_time=0, down_time=float('inf'), latency=2,
                                     RWA=False)
                        if traf_id:
                            ROADM_TRAF[TERMINAL_TO_ROADM[s_t]].add(traf_id)
                        else:
                            Rej[s_t] += 1
                            Total_Rej += 1
                            BBU_traf[d_t] -= 1

                elif dst_back:
                    dst = dst_back
                    dst_t = dst_t_back
                    print('try_backup_path', src, dst)
                    traf_id = install_Traf(src_t, dst_t, routes, cur_time=0, down_time=float('inf'), latency=2,
                                           RWA=False)
                    if traf_id:
                        ADD_TRAF = True
                        ROADM_TRAF[src].add(traf_id)
                        BBU_traf[dst_t] += 1
                        reassign_traf = []
                        fail_lightpaths = []
                        for lightpath_id, info in LIGHTPATH_INFO.items():
                            powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path=info['path'],
                                                                                       channel=info['channel_id'],
                                                                                       nodes=NODES)
                            LIGHTPATH_INFO[lightpath_id]['GOSNR'] = gosnrs[-1]
                            LIGHTPATH_INFO[lightpath_id]['OSNR'] = osnrs[-1]
                            if 18 < gosnrs[-1] < 24:
                                LIGHTPATH_INFO[lightpath_id]['link_cap'] = DOWN_LINK_CAP
                                traf_set = LIGHTPATH_INFO[lightpath_id]['traf_set']
                                while len(traf_set) > DOWN_LINK_CAP / CPRI_CAP:
                                    traf_id = random.choice(list(traf_set))
                                    s_t, d_t = TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst']
                                    ROADM_TRAF[TERMINAL_TO_ROADM[s_t]].remove(traf_id)
                                    traf_to_lightpath_Release(traf_id=traf_id)
                                    reassign_traf.append((s_t, d_t))
                            elif gosnrs[-1] < 16:
                                LIGHTPATH_INFO[lightpath_id]['link_cap'] = 50
                                traf_set = LIGHTPATH_INFO[lightpath_id]['traf_set']
                                while len(traf_set) > DOWN_LINK_CAP / CPRI_CAP:
                                    traf_id = random.choice(list(traf_set))
                                    s_t, d_t = TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst']
                                    ROADM_TRAF[TERMINAL_TO_ROADM[s_t]].remove(traf_id)
                                    traf_to_lightpath_Release(traf_id=traf_id)
                                    reassign_traf.append((s_t, d_t))
                            else:
                                LIGHTPATH_INFO[lightpath_id]['link_cap'] = LINK_CAP

                        for s_t, d_t in reassign_traf:
                            traf_id = install_Traf(s_t, d_t, routes, cur_time=0, down_time=float('inf'), latency=2,
                                                   RWA=False)
                            if traf_id:
                                ROADM_TRAF[TERMINAL_TO_ROADM[s_t]].add(traf_id)
                            else:
                                Rej[s_t] += 1
                                Total_Rej += 1
                                BBU_traf[d_t] -= 1

                if not ADD_TRAF:
                    Rej[src_t] += 1
                    Total_Rej += 1
                    count += 1
                    if count == 10:
                        fails = factor*MAX_traf[src]/CPRI_CAP - len(ROADM_TRAF[src])
                        RRH_traf[src_t] += fails
                        Rej[src_t] += fails
                        Total_Rej += fails
                        break

            while factor * MAX_traf[src] / CPRI_CAP < len(ROADM_TRAF[src]):
                traf_id = random.choice(list(ROADM_TRAF[src]))
                dst = TRAFFIC_INFO[traf_id]['dst']
                BBU_traf[dst] -= 1
                lightpath_id = TRAFFIC_INFO[traf_id]['lightpath_id']
                traf_set = LIGHTPATH_INFO[lightpath_id]['traf_set']
                traf_to_lightpath_Release(traf_id=traf_id)
                ROADM_TRAF[src].remove(traf_id)
                if not traf_set:
                    uninstall_Lightpath(lightpath_id=lightpath_id)



        """while UP_LIGHTPATH_TIME_LIST and UP_LIGHTPATH_TIME_LIST[0][0]< time:
            lightpath_id = UP_LIGHTPATH_TIME_LIST.pop(0)[1]
            uninstall_Lightpath(lightpath_id=lightpath_id)
        #"""
        OneG = 0
        TwoG = 0
        FiftyG = 0
        UnderUse = 0
        for lightpath_id, info in LIGHTPATH_INFO.items():
            if LIGHTPATH_INFO[lightpath_id]['link_cap']/CPRI_CAP/2 > len(LIGHTPATH_INFO[lightpath_id]['traf_set']):
                UnderUse += 1
            link_cap = LIGHTPATH_INFO[lightpath_id]['link_cap']
            if link_cap == 100:
                OneG += 1
            elif link_cap ==200:
                TwoG += 1
            elif link_cap ==50:
                FiftyG += 1
        total_wav = 0
        for key in NETLINK_INFO.keys():
            total_wav += len(NETLINK_INFO[key].items())
        avg_wav = (1.0 * total_wav ) / (NUM_NODE-1)

        """file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(i, factors['r2'] * MAX_traf['r2'], factors['r3'] * MAX_traf['r3'],
                                                                                 len(LIGHTPATH_INFO.keys()), avg_wav,BBU_traf['t1'], BBU_traf['t%d' % NUM_NODE],
                                                                                 1.0*Rej['t2']/(factors['r2']*MAX_traf['r2']/CPRI_CAP), 1.0*Rej['t3']/(factors['r3']*MAX_traf['r3']/CPRI_CAP),
                                                                                 OneG, TwoG, UnderUse, OneG*100+TwoG*200))
        #"""
        print(Rej['t2'], '/', factors['r2'], MAX_traf['r2'], CPRI_CAP)
        file.write('{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {} \n'.format(
            i,
            factors['r2'] * MAX_traf['r2'],
            factors['r3'] * MAX_traf['r3'],
            factors['r5'] * MAX_traf['r5'],
            factors['r6'] * MAX_traf['r6'],
            len(LIGHTPATH_INFO.keys()), avg_wav,
            BBU_traf['t1'],
            BBU_traf['t7'],
            BBU_traf['t4'],
            1.0 * Rej['t2'] / (factors['r2']*MAX_traf['r2']/CPRI_CAP),
            1.0 * Rej['t3'] / (factors['r3']*MAX_traf['r3']/CPRI_CAP),
            1.0 * Rej['t5'] / (factors['r5']*MAX_traf['r5']/CPRI_CAP),
            1.0 * Rej['t6'] / (factors['r6']*MAX_traf['r6']/CPRI_CAP),
            FiftyG, OneG,TwoG, UnderUse,
            OneG * 100 + TwoG * 200 +FiftyG*50,
            (factors['r2'] * MAX_traf['r2']) + (factors['r3'] * MAX_traf['r3']) + (factors['r5'] * MAX_traf['r5'])+(factors['r6'] * MAX_traf['r6']))
        )
        #"""
    print('==traf')
    for item in TRAFFIC_INFO.items():
        print(item)
    print('==Lightpath')
    fail_paths= []
    for item in LIGHTPATH_INFO.items():
        print(item)
        path = item[1]['path']
        ch = item[1]['channel_id']
        gosnr = item[1]['GOSNR']
        powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path=path, channel=ch, nodes=NODES)
        print('gosnr', gosnr, gosnrs[-1])
        if gosnrs[-1]< 24:
            fail_paths.append((gosnrs[-1],osnrs[-1], powers[-1], item))
    for gosnr, osnr, power, item in fail_paths:
        print('fail', gosnr, osnr, abs_to_db(power), item)
    #print('==rej', Rej, 1.0*Rej/N)
    print('r2-r1, chs', len(NETLINK_INFO['r2', 'r1'].items()))
    print('r2-r3, chs', len(NETLINK_INFO['r2', 'r3'].items()))
    print('r3-r4, chs', len(NETLINK_INFO['r3', 'r4'].items()))
    for roadm in ROADM_TRAF:
        print(roadm, ROADM_TRAF[roadm])
    print('BBU_Processing_traf', BBU_traf)
    print('rej', Rej)
    print('RRH_TRAF', RRH_traf)
    print('rej_ratio', 1.0*Rej['t2']/RRH_traf['t2'], 1.0*Rej['t3']/RRH_traf['t3'])
    print('total_rej_rate', 1.0* Total_Rej/sum(RRH_traf.values()) )

    # for lightpath_id, info in LIGHTPATH_INFO.items():
    #     powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path=info['path'], channel=info['channel_id'],
    #                                                                nodes=NODES)
    #     print('id: {}, path: {}, power: {}'.format( lightpath_id, info['path'], powers ) )


# Physical model test
def RoadmPhyTest():
    # ROADM port numbers (input and output)
    LINE_PORT1 = NUM_WAV
    LINE_PORT2 = NUM_WAV+1

    "Create a single link and monitor its OSNR and gOSNR"
    net = RoadmPhyNetwork()
    AllLinks = getLinks()
    global  GRAPH, NODES
    GRAPH = netGraph(AllLinks['links'])
    NODES = net.name_to_node
    routes = {node: FindRoute(node, GRAPH, name_terminals)
               for node in name_terminals}
    # routes = {node: FindRoute(node, GRAPH, NAME_ROADM)
    #           for node in NAME_ROADM}
    print('===links', AllLinks['links'])
    print('===graph', GRAPH)
    print('==link_info', NETLINK_INFO)
    print('==route')
    for key in routes.keys():
        print(key, routes[key])

    ## add traffic and delete traffic
    Rej = 0
    time = 0  # 86400s for one day
    setup_time = 0.5/60.0  # MINUTE
    N = 2000 # 1000000 for one day
    file = open('record.txt', 'w')
    # CPRI Request
    arrival_rate = 50  # request/minute
    holding_time = 30  # minute
    factor = 1
    for i in range(N):
        print(i)
        #factor = trafficPattern(time)
        t_arrival_rate = arrival_rate*factor
        s_time = 1.0/t_arrival_rate + time #random.uniform(0.01, 0.02) + time  #
        duration = random.choice(np.random.poisson(holding_time, 10000))
        #duration = random.uniform(30, 600)
        d_time = s_time + duration
        time = s_time + setup_time
        src = random.choice(RU_ROADMS)
        dst = random.choice(DU_ROADMS)
        #src = random.choice(NAME_ROADM)
        #dst = random.choice(NAME_ROADM)
        while dst == src:
            dst = random.choice(NAME_ROADM)

        latency = random.uniform(0, 1)
        if latency<0.1:
            latency = 0
        elif latency<0.4:
            latency = 1
        else:
            latency = 2
        src = ROADM_TO_TERMINAL[src]
        dst = ROADM_TO_TERMINAL[dst]
        if not install_Traf(src, dst, routes, cur_time= s_time, down_time=d_time, latency=2, RWA= False):
            Rej += 1
        else:
            ROADM_TRAF[src].add(TRAFFIC_ID)
        while UP_TRAF_TIME_LIST and UP_TRAF_TIME_LIST[0][0]< time:
            traf_id = UP_TRAF_TIME_LIST.pop(0)[1]
            traf_to_lightpath_Release(traf_id=traf_id)
            print('~~', traf_id)
            ROADM_TRAF[src].remove(traf_id)
        while UP_LIGHTPATH_TIME_LIST and UP_LIGHTPATH_TIME_LIST[0][0]< time:
            lightpath_id = UP_LIGHTPATH_TIME_LIST.pop(0)[1]
            uninstall_Lightpath(lightpath_id=lightpath_id)
        #"""
        file.write('{}\t{}\n'.format(time, 1.0*Rej/(i+1)))
    print('==traf')
    for item in TRAFFIC_INFO.items():
        print(item)
    print('==Lightpath')
    fail_paths= []
    for item in LIGHTPATH_INFO.items():
        print(item)
        if item[-1]['GOSNR']< 24:
            fail_paths.append(item)
    print('==time', time)
    for item in fail_paths:
        print('fail',item)
    print('==rej', Rej, 1.0*Rej/N)
    print('r2-r1, chs', len(NETLINK_INFO['r2', 'r1'].items()))
    print('r2-r3, chs', len(NETLINK_INFO['r2', 'r3'].items()))
    print('r3-r4, chs', len(NETLINK_INFO['r3', 'r4'].items()))
    print(ROADM_TRAF)

def QuickTest(shift=0, floor=0.0001, timelength=8, pattern = 'sawtooth',load=35000, days=7, filename = 'sawtooth_results.txt'):
    days = 7
    time = np.arange(0, 24 * days)
    office = []
    resident = []
    for hour in time:
        office.append(analytic_traffic(hour, shift=shift, floor=floor, timelength=timelength, days=days,
                                       pattern = pattern, source='office'))
        resident.append(analytic_traffic(hour, shift=shift, floor=floor, timelength=timelength, days=days,
                                         pattern = pattern, source='resident'))
    plt.plot(time, resident, office)
    plt.show()
if __name__ == '__main__':
    #TrafficTest(shift=0, floor=0.01, timelength=4, pattern='triangle', load=35000, days=7, filename='Control.txt')
    #TrafficTest(shift=0, floor=0.01, timelength=8, pattern='triangle', load=35000, days=7, filename='Control_s1.txt')
    #TrafficTest(shift=0, floor=0.01, timelength=10, pattern='triangle', load=35000, days=7, filename='Control_s2.txt')
    #TrafficTest(shift=0, floor=0.01, timelength=12, pattern='triangle', load=35000, days=7, filename='Control_s4.txt')
    #TrafficTest(shift=0, floor=0.01, timelength=20, pattern='sawtooth', load=35000, days=7, filename='Control_s8 (2).txt') #check for wierd traffic_load error

    #TrafficTest(shift=0, floor=0.1, timelength=1, pattern='step_down', load=35000, days=7, filename='step_1.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=8, pattern='step_down', load=35000, days=7, filename='step_8.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=24, pattern='step_down', load=35000, days=7, filename='step_24.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=48, pattern='step_down', load=35000, days=7, filename='step_48.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=96, pattern='step_down', load=35000, days=7, filename='step_96.txt')

    #TrafficTest(shift=2, floor=0.001, timelength=8, pattern='impulse', load=35000, days=7, filename='Control_f=e-32.txt')
    #TrafficTest(shift=2, floor=0.01, timelength=8, pattern='impulse', load=35000, days=7, filename='Control_f=e-2.txt')
    #TrafficTest(shift=2, floor=0.1, timelength=8, pattern='impulse', load=35000, days=7, filename='Control_f=e-1.txt')
    #TrafficTest(shift=2, floor=0.2, timelength=8, pattern='impulse', load=35000, days=7, filename='Control_f=2e-1.txt')

    #TrafficTest(shift=0, floor=0.1, timelength=1, pattern='step_down', load=35000, days=7, filename='step_1.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=8, pattern='step_down', load=35000, days=7, filename='step_8.txt')

    #TrafficTest(shift=0, floor=0.1, timelength=24, pattern='step_down', load=35000, days=7, filename='step_24.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=48, pattern='step_down', load=35000, days=7, filename='step_48.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=96, pattern='step_down', load=35000, days=7, filename='step_96.txt')

    #TrafficTest(shift=0, floor=0.0001, timelength=8, pattern='sawtooth', load=35000, days=7, filename='Control.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=4, pattern='sawtooth', load=35000, days=7, filename='rev-sawtooth-4.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=6, pattern='sawtooth', load=35000, days=7, filename='rev-sawtooth-6.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=8, pattern='sawtooth', load=35000, days=7, filename='rev-sawtooth-8.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=10, pattern='sawtooth', load=35010, days=7, filename='rev-sawtooth-10.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=12, pattern='sawtooth', load=35000, days=7, filename='rev-sawtooth-12.txt')

    #TrafficTest(shift=0, floor=0.1, timelength=16, pattern='triangle', load=35010, days=2, filename='triangle-6-dual_limits[Test].txt')
    #TrafficTest(shift=0, floor=0.1, timelength=6, pattern='triangle', load=35010, days=7, filename='triangle-6-dual_limits.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=8, pattern='triangle', load=35010, days=7, filename='triangle-8-dual_limits.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=10, pattern='triangle', load=35010, days=7, filename='triangle-10-dual_limits.txt')
    #TrafficTest(shift=0, floor=0.1, timelength=12, pattern='triangle', load=35010, days=7, filename='triangle-12-dual_limits.txt')
    TrafficTest(shift=0, floor=0.1, timelength=14, pattern='triangle', load=35010, days=7, filename='triangle-14-dual_limits.txt')
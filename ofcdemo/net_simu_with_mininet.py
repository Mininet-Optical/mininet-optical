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


km = dB = dBm = 1.0
m = .001

# Parameters

NUM_WAV = 90
LINK_CAP = 100
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
TRAFFIC_ID = 1
LIGHTPATH_ID = 1
NUM_NODE = 4
NAME_ROADM = []
UP_TRAF_TIME_LIST = []
UP_TRAF_ID_SET = set()
UP_LIGHTPATH_TIME_LIST = []
UP_LIGHTPATH_ID_SET = set()
ALL_CHANNELS = [ i for i in range(1,NUM_WAV+1)]
RU_ROADMS = ['r2', 'r3']
DU_ROADMS = ['r1', 'r4']

# Mininet-Optical
name_roadms = []
name_terminals = []
Roadm_Rule_ID_dict = {}
ROADM_TO_TERMINAL = {}
for i in range(NUM_NODE):
    name_roadms.append('r%d'%(i+1))
    name_terminals.append('t%d'%(i+1))
    Roadm_Rule_ID_dict['r%d' % (i + 1)] = 1
    ROADM_TO_TERMINAL['r%d' % (i + 1)] = 't%d' % (i + 1)


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
    #      t4 - r4 ----- r3 - t3
    ################################

    net = Network()
    lengths = [50 * km]

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
        if len(LIGHTPATH_INFO[lighpath_id]['traf_set']) < LINK_CAP/CPRI_CAP:
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
            traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
            return True
    elif latency == 1:
        if lightpath_id:
            TRAFFIC_ID += 1
            traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
            return True
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
                            traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
                            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
                            return True
                        else:
                            uninstall_Lightpath(lightpath_id)
    elif latency == 2:
        if lightpath_id:
            TRAFFIC_ID += 1
            traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
            LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
            return True
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
                        traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
                        LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
                        return True
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


def trafficPattern(time, day= True):
    """
    24 hour normalized traffic
    resident area: 40% resident, 20% entertainment, 18% office, 22% transport
    office area: 37% office, 18% entertainment, 16% resident, 29% transport
    entertainment area: 39% entertainment, 23% office, 11% resident, 28% transport

    (1) 24.33 Gbps CPRI OPTION 10 -> 1.5 Gbps
    (2) 9600 towers, Maximum wireless traffic is 8.5 * 10**11 bytes/ 10 mins -> 6.8*10**12 bit -> 6800 G/ 10 min = 11.3 Gbps
    -> 183.8 Gbps CPRI OPTION 10
    (3) Max traffic: 8 requests per second for CPRI OPTION 8
    """


    comprehensive = [0.52,
                 0.36, 0.26, 0.20, 0.14, 0.15,
                 0.24, 0.40, 0.58, 0.81, 0.94,
                 0.97, 1.0, 0.99, 0.98, 0.975,
                 0.95, 0.92, 0.925, 0.94, 0.96,
                 0.98, 0.94, 0.86
                 ]
    # 0.85*
    comprehensive_weekend = [0.62,
                 0.36, 0.26, 0.20, 0.14, 0.15,
                 0.24, 0.40, 0.58, 0.81, 0.92,
                 0.96, 1.0, 0.99, 0.98, 0.96,
                 0.95, 0.94, 0.94, 0.96, 0.975,
                 0.985, 0.96, 0.86
                 ]

    transport = [0.0,
                 0.0, 0.0, 0.0, 0.05,
                 0.10, 0.5, 0.80, 1,
                 0.9, 0.70, 0.50, 0.4,
                 0.42, 0.44, 0.47, 0.5,
                 0.65, 0.90, 0.75, 0.45,
                 0.36, 0.20, 0.10
                 ]
    transport_weekend = [0.0,
                         0.0, 0.0, 0.0, 0.0,
                         0.05, 0.15, 0.27, 0.38,
                         0.39, 0.40, 0.41, 0.40,
                         0.39, 0.40, 0.42, 0.43,
                         0.41, 0.39, 0.37, 0.36,
                         0.30, 0.20, 0.10
                         ]

    office = [0.2,
              0.17, 0.14, 0.11, 0.09,
              0.10, 0.24, 0.40, 0.52,
              0.81, 0.94, 1.0, 0.98,
              0.99, 0.98, 0.955, 0.90,
              0.75, 0.60, 0.50, 0.40,
              0.36, 0.32, 0.25
              ]
    office_weekend = [0.20,
                      0.17, 0.14, 0.11, 0.09,
                      0.13, 0.24, 0.27, 0.38,
                      0.41, 0.43, 0.44, 0.43,
                      0.42, 0.41, 0.40, 0.39,
                      0.38, 0.37, 0.36, 0.36,
                      0.35, 0.32, 0.25
                      ]

    resident = [0.52,
                0.42, 0.32, 0.24, 0.20,
                0.18, 0.24, 0.40, 0.45,
                0.50, 0.55, 0.56, 0.55,
                0.56, 0.58, 0.60, 0.63,
                0.73, 0.83, 0.91, 0.98,
                1.0, 0.97, 0.70
                ]
    resident_weekend = [0.52,
                        0.42, 0.32, 0.24, 0.20,
                        0.28, 0.34, 0.50, 0.55,
                        0.70, 0.78, 0.81, 0.82,
                        0.81, 0.81, 0.82, 0.84,
                        0.85, 0.87, 0.91, 0.96,
                        0.97, 0.96, 0.70
                        ]

    entertainment = [0.23,
                     0.20, 0.16, 0.15, 0.14,
                     0.15, 0.24, 0.40, 0.58,
                     0.81, 0.93, 0.94, 0.955,
                     0.96, 0.95, 0.94, 0.94,
                     0.95, 0.96, 0.97, 0.99,
                     1.0, 0.94, 0.86
                     ]
    entertainment_weekend = [0.42,
                             0.36, 0.26, 0.20, 0.14,
                             0.15, 0.24, 0.40, 0.58,
                             0.81, 0.92, 0.96, 0.97,
                             0.985, 0.99, 1.0, 0.99,
                             0.98, 0.975, 0.97, 0.96,
                             0.95, 0.92, 0.86
                             ]

    tem_t = time
    day = int(tem_t/3600/24)
    tem_t = tem_t - day*3600*24
    h = int(tem_t/3600)
    #print(h)

    return comprehensive[int(h)]


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
    arrival_rate = 5  # request/minute
    holding_time = 5  # minute
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
        src = random.choice(RU_ROADMS+DU_ROADMS)
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
        while UP_TRAF_TIME_LIST and UP_TRAF_TIME_LIST[0][0]< time:
            traf_id = UP_TRAF_TIME_LIST.pop(0)[1]
            traf_to_lightpath_Release(traf_id=traf_id)
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
        if item[-1]['GOSNR']< 26.5:
            fail_paths.append(item)
        # path = item[1]['path']
        # channel = item[1]['channel_id']
        # powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path, channel, NODES)
        # print('channel', channel, 'path', path, 'power', powers, 'osnr', osnrs, 'ase', ase, 'nli', nli, 'gosnr', gosnrs)
    print('==time', time)
    for item in fail_paths:
        print('fail',item)
    print('==rej', Rej, 1.0*Rej/N)


if __name__ == '__main__':
    RoadmPhyTest()

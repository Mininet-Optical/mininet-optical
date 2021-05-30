#!/usr/bin/python
"""
single_link_test.py: test monitoring on a single link

Note this version uses and depends on explicit port assignment!
"""

#from network import Network
#from link import Span as Fiber, SpanTuple as Segment
#from node import Transceiver
#from units import *
from collections import defaultdict
import random
from collections import defaultdict
#import numpy as np
from Control_Test_Lum import Lumentum_Control_NETCONF


km = dB = dBm = 1.0
m = .001

# Parameters
Controller_Lum = Lumentum_Control_NETCONF()

NUM_WAV = 10
LINK_CAP = 200
DOWN_LINK_CAP = 100
CPRI_CAP = 25
# ROADM port numbers (input and output)
LINE_PORT1, LINE_PORT2, LINE_PORT3, LINE_PORT4, LINE_PORT5, LINE_PORT6 = NUM_WAV, NUM_WAV+1, NUM_WAV+2, NUM_WAV+3, NUM_WAV+4, NUM_WAV+5
NETLINKS = []
GRAPH = defaultdict()
NODES = defaultdict()
NETLINK_INFO = defaultdict( defaultdict ) # ('node_name', 'node_name'): {channel_id: lightpath_id}
TRAFFIC_INFO = defaultdict( defaultdict ) # id : {'src':src, 'dst':dst, 'lightpath_id': lightpath_id, 'up_time':s_time, 'down_time': d_time}
LIGHTPATH_INFO = defaultdict( defaultdict ) # id : {'path':path, 'channel_id': channel_id, 'traf_set': set(), 'up_time':s_time, 'down_time': d_time, 'OSNR': 25, 'GOSNR': 24.5 }
SRC_DST_TO_LIGHTPATH = defaultdict( set ) # (src, dst) : {set[lightpath_id]}
PATH_CH_TO_LIGHTPATH = defaultdict(defaultdict) # (src, hop, dst) : {'channel_id': lightpath_id}
TRAFFIC_ID = 0
LIGHTPATH_ID = 0
NUM_NODE = 4
NAME_ROADM = []
UP_TRAF_TIME_LIST = []
UP_TRAF_ID_SET = set()
UP_LIGHTPATH_TIME_LIST = []
UP_LIGHTPATH_ID_SET = set()
ALL_CHANNELS = [ i for i in range(1,NUM_WAV+1)]
RU_ROADMS = []
DU_ROADMS = ['r1', 'r%d' %NUM_NODE]
ROADM_TRAF = defaultdict(set)

# Mininet-Optical
name_roadms = []
name_terminals = []
ROADM_TO_TERMINAL = {}
TERMINAL_TO_ROADM = {}
for i in range(NUM_NODE):
    name_roadms.append('r%d'%(i+1))
    name_terminals.append('t%d'%(i+1))
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
    #      t4 - r4 ----- r3 - t3
    ################################

    #net = Network()

    for k in range(1, NUM_NODE):
        print('==range=', k)
        # Eastbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers

        NETLINKS.append(('r%d' % k, LINE_PORT2, 'r%d' % (k + 1), LINE_PORT1))
        NETLINK_INFO['r%d' % k, 'r%d' % (k + 1)] = {0: 0}

        # Westbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers

        NETLINKS.append(('r%d' % (k + 1), LINE_PORT1, 'r%d' % k, LINE_PORT2))
        NETLINK_INFO['r%d' % (k + 1), 'r%d' % k] = {0: 0}

    for k in range(1,NUM_NODE+1):
        # Local add/drop links between terminals/transceivers and ROADMs
        for add_drop_port in range(NUM_WAV):

            NETLINKS.append(('t%d' %k, add_drop_port, 'r%d' %k, add_drop_port))
            NETLINKS.append(('r%d' %k, add_drop_port, 't%d' %k, add_drop_port))

    return

############# Mininet Optical############

def Mininet_installPath(lightpath_id, path, channels, graph, nodes):
    "intall switch rules on roadms along a lightpath for some signal channels"

    # Install ROADM rules
    print(graph, nodes)
    for channel in channels:

        LIGHTPATH_INFO[lightpath_id]['rule_path'] = None


def Mininet_uninstallPath(lightpath_id, nodes):
    "delete switch rules on roadms along a lightpath for some signal channels"


    path = LIGHTPATH_INFO[lightpath_id]['path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    Mininet_turnoffTerminalChannel(terminal=nodes[path[0]], channel=channel)
    nodes[roadm].delete_switch_rule(rule_path[roadm])



def Mininet_setupLightpath(lightpath_id, path, channel, power, graph, nodes):
    channel = channel[0]
    Mininet_installPath(lightpath_id, path, [channel], graph, nodes)
    Mininet_configTerminalChannelPower(terminal= nodes[path[0]], channel=channel, power=power)
    Mininet_configTerminalChannel(terminal=nodes[path[0]], channel=channel)
    return True


def Mininet_teardownLightpath(lightpath_id, nodes):

    Mininet_uninstallPath(lightpath_id, nodes)
    return True



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



############### COSMOS Lumentum ###############

def Lumentum_installPath(lightpath_id, path, channel):
    "intall switch rules on roadms along a lightpath for some signal channels"

    Controller_Lum.installPath(path=path, channel=channel, lightpathID=lightpath_id)


def Lumentum_uninstallPath(lightpath_id):
    "delete switch rules on roadms along a lightpath for some signal channels"

    path = LIGHTPATH_INFO[lightpath_id]['path']
    Controller_Lum.uninstallPath(path=path, lightpathID=lightpath_id)


def Lumentum_setupLightpath(lightpath_id, path, channel):
    "configure a lightpath "

    Lumentum_installPath(lightpath_id, path, channel)
    return True


def Lumentum_teardownLightpath(lightpath_id):
    "remove a lightpath"

    Lumentum_uninstallPath(lightpath_id)
    return True

def Lumentum_MonitorLightpath(lightpath_id):
    path = LIGHTPATH_INFO[lightpath_id]['path']
    Controller_Lum.channel_monitor(path=path, lightpathID=lightpath_id)

############### COSMOS Lumentum END ###############





################ CONTROL PLANE #####################


def linkspec( link ):
    "Return specifier dict(node1, port1, node2, port2) for link"
    node1, node2, port1, port2 = link[0], link[2], link[1], link[3]
    return { node1:port1, node2:port2 }


def getLinks(links):

    return dict( links=[ linkspec( link ) for link in links ] )


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


def FindRoute( src, graph, destinations, k=1):
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
    "intall switch rules on roadms along a lightpath for some signal channels, update control database"

    ## Install ROADM rules
    global LIGHTPATH_ID
    LIGHTPATH_ID += 1
    for i in range(len(path) - 1):
        NETLINK_INFO[path[i], path[i + 1]][channel] = LIGHTPATH_ID  # channel with lightpath_id
        NETLINK_INFO[path[i + 1], path[i]][channel] = LIGHTPATH_ID
    # id : {'path':path, 'channel': channel_id, 'traf': set(), 'up_time':s_time, 'down_time': d_time, 'OSNR': 25, 'GOSNR': 24.5 }
    Lumentum_setupLightpath(lightpath_id=LIGHTPATH_ID, path=path, channel=channel)
    #powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path, channel, NODES)
    LIGHTPATH_INFO[LIGHTPATH_ID]['path'] = path
    LIGHTPATH_INFO[LIGHTPATH_ID]['channel_id'] = channel
    LIGHTPATH_INFO[LIGHTPATH_ID]['link_cap'] = LINK_CAP
    LIGHTPATH_INFO[LIGHTPATH_ID]['traf_set'] = set()
    LIGHTPATH_INFO[LIGHTPATH_ID]['up_time'] = up_time
    LIGHTPATH_INFO[LIGHTPATH_ID]['down_time'] = down_time
    LIGHTPATH_INFO[LIGHTPATH_ID]['power'] = 0
    LIGHTPATH_INFO[LIGHTPATH_ID]['OSNR'] = 0
    LIGHTPATH_INFO[LIGHTPATH_ID]['GOSNR'] = 0
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


def update_lightpath_down_time(lightpath_id, down_time):
    "if there is a traf, update lightpath teardown time"

    for d_time, id in UP_LIGHTPATH_TIME_LIST:
        if id == lightpath_id:
            UP_LIGHTPATH_TIME_LIST.remove((d_time, id))
            UP_LIGHTPATH_TIME_LIST.append((down_time, lightpath_id))
            UP_LIGHTPATH_TIME_LIST.sort()


def traf_to_lightpah_Assignment(traf_id, lightpath_id, down_time = float('inf')):
    "assign a traffic to a lightpath, update control database"

    # (src, hop, dst) : {'channel_id': lightpath_id}
    LIGHTPATH_INFO[lightpath_id]['traf_set'].add(traf_id)
    path = LIGHTPATH_INFO[lightpath_id]['path']
    if down_time > LIGHTPATH_INFO[lightpath_id]['down_time']:
        LIGHTPATH_INFO[lightpath_id]['down_time'] = down_time
        update_lightpath_down_time(lightpath_id, down_time)
    # traf_id : {'src':src, 'dst':dst, 'lightpath_id': lightpath_id, 'up_time':s_time, 'down_time': d_time}
    TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst'], TRAFFIC_INFO[traf_id]['lightpath_id'] = path[0], path[-1], lightpath_id
    UP_TRAF_TIME_LIST.append((down_time, traf_id))
    UP_TRAF_TIME_LIST.sort()
    UP_TRAF_ID_SET.add(traf_id)
    return traf_id


def install_Traf(src, dst, routes, cur_time, down_time=float('inf')):
    '''
    source RRH node to destination BBU node
    '''
    global TRAFFIC_ID
    avai_lightpaths = check_lightpath_for_traf(src, dst)
    lightpath_id = None
    if avai_lightpaths:
        lightpath_id = avai_lightpaths[0]

    if lightpath_id:
        TRAFFIC_ID += 1
        traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
        LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
        return traf_id
    else:
        all_path_info = routes[src][dst]
        for path_info in all_path_info:
            path = path_info
            path = path[1:-1]
            chs = waveAvailibility(path=path)
            if chs:
                ch = waveSelection(chs)
                lightpath_id = install_Lightpath(path=path, channel=ch, up_time=cur_time, down_time=down_time)
                TRAFFIC_ID += 1
                traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
                return traf_id
    return False


def uninstall_Lightpath(lightpath_id):
    "delete switch rules on roadms along a lightpath for some signal channels"
    Lumentum_uninstallPath(lightpath_id=lightpath_id)
    path = LIGHTPATH_INFO[lightpath_id]['path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    for i in range(len(path) - 1):
        del NETLINK_INFO[path[i], path[i + 1]][channel]
        del NETLINK_INFO[path[i + 1], path[i]][channel]
    #print(PATH_CH_TO_LIGHTPATH)
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


def trafficPattern(pattern, time):
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
                        0.85, 0.87, 0.91, 0.98,
                        1.0, 0.97, 0.70
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
    traffic_week = [1]*24
    traffic_weeked = [1]*24
    hour = time % 24
    if pattern == 'office':
        traffic_week = office
        traffic_weeked = office_weekend
    if pattern == 'resident':
        traffic_week = resident
        traffic_weeked = resident_weekend
    return traffic_week[hour], traffic_weeked[hour]

def TrafficTest():
    # ROADM port numbers (input and output)
    random.seed(1000)
    "Create a single link and monitor its OSNR and gOSNR"
    RoadmPhyNetwork()
    AllLinks = getLinks(NETLINKS)
    print(NETLINKS)
    global  GRAPH, NODES
    GRAPH = netGraph(AllLinks['links'])
    #NODES = net.name_to_node
    NODES = ['t1','t2','t3','t4']
    routes = {node: FindRoute(node, GRAPH, name_terminals)
               for node in name_terminals}

    print('===links', AllLinks['links'])
    print('===graph', GRAPH)
    print('==link_info', NETLINK_INFO)
    print('==route')
    for key in routes.keys():
        print(key, routes[key])

    file = open('record.txt', 'w')

    # CPRI Request initilization, assign total max traffic to network, and each RRH ROADM traffic peak
    Total_Rej = 0
    N = 24 * 1  # total emulation time : 24 hour * y days
    Total_traf = 35000 # Gbps
    MAX_traf = {}
    traffic_ratio = [random.uniform(0.8, 1.1) for i in range(len(RU_ROADMS))]
    for i in range(2,NUM_NODE):
        MAX_traf['r%d' %i] = 1.0*Total_traf*traffic_ratio[i-2]/sum(traffic_ratio)
    print('---max_traf',MAX_traf)

    # Initial number of processing traffic in BBU ROADMs
    BBU_traf = {}
    for node in DU_ROADMS:
        BBU_traf[ROADM_TO_TERMINAL[node]] = 0

    # Assign max number of processing traffic in a BBU ROADM (any endpoints)
    BBU_limit = {}
    BBU_limit['t%d' % NUM_NODE] = 500

    # Initial number of requested traffic in RRH ROADMs
    RRH_traf = {}
    for node in RU_ROADMS:
        RRH_traf[ROADM_TO_TERMINAL[node]] = 0

    # Traffic type in RRH ROADMs
    Traf_Type = ['office', 'resident']
    ROADM_TYPE = {}
    for i in range(2, NUM_NODE):
        ROADM_TYPE['r%d' %i] = random.choice(Traf_Type)

    for i in range(N):
        Rej = {} # rejected CPRI requests in each ROADM/terminal
        for key in TERMINAL_TO_ROADM.keys():
            Rej[key] = 0
        print(i)
        factors = {}
        for src in RU_ROADMS:
            # weekdays
            if i%(24*7) < 24 * 5:
                factor = trafficPattern(pattern=ROADM_TYPE[src], time=i)[0] * random.uniform(0.8, 1.1)
            # weekends
            else:
                factor = trafficPattern(pattern=ROADM_TYPE[src], time=i)[1] * random.uniform(0.8, 1.1)
            factors[src] = factor
            src_t = ROADM_TO_TERMINAL[src]


            # if # of processing traffic < max processing traffic of certain hour in a RRH ROADM, handle this traf
            while factor*MAX_traf[src]/CPRI_CAP > len(ROADM_TRAF[src]):
                count = 0
                ADD_TRAF = False

                print(factor*MAX_traf[src]/CPRI_CAP, len(ROADM_TRAF[src]), Rej)
                dst = random.choice(DU_ROADMS)
                RRH_traf[src_t] += 1
                dst_t = ROADM_TO_TERMINAL[dst]
                path_first = routes[src_t]['t1'][0]
                path_last = routes[src_t]['t%d' % NUM_NODE][0]
                dst_back = None
                print('two_paths', path_first, path_last)

                # check which BBU ROADM can handle more traffic
                if len(path_last)<len(path_first) and BBU_traf['t%d' % NUM_NODE] < BBU_limit['t%d' % NUM_NODE]:
                    print('BBU R4 resource',BBU_traf['t%d' % NUM_NODE], BBU_limit['t%d' % NUM_NODE])
                    dst = 'r%d' % NUM_NODE
                    dst_t = 't%d' % NUM_NODE
                    dst_back = 'r1'
                    dst_t_back = 't1'
                else:
                    dst = 'r1'
                    dst_t = 't1'
                    dst_back = 'r%d' % NUM_NODE
                    dst_t_back = 't%d' % NUM_NODE

                print("route info", src_t, dst_t, routes)
                #return

                # install this traf to a lighpath
                traf_id = install_Traf(src_t, dst_t, routes, cur_time=0, down_time=float('inf'))
                print('request', src, dst)
                if traf_id:
                    ADD_TRAF = True
                    ROADM_TRAF[src].add(traf_id)
                    BBU_traf[dst_t] += 1
                    # if a lightpath is downgraded, some traf needs to be reassigned
                    reassign_traf = []
                    for lightpath_id, info in LIGHTPATH_INFO.items():
                        #powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path=info['path'], channel=info['channel_id'], nodes=NODES)
                        osnr, gosnr = 25, 25
                        LIGHTPATH_INFO[lightpath_id]['GOSNR'] = gosnr
                        LIGHTPATH_INFO[lightpath_id]['OSNR'] = osnr

                        # upgrade or downgrade the modulation/capacity of a lightpath based on gosnr
                        if 18< gosnr < 24:
                            LIGHTPATH_INFO[lightpath_id]['link_cap'] = DOWN_LINK_CAP
                            traf_set =  LIGHTPATH_INFO[lightpath_id]['traf_set']
                            while len(traf_set) > DOWN_LINK_CAP/CPRI_CAP:
                                 traf_id = random.choice(list(traf_set))
                                 s_t, d_t = TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst']
                                 ROADM_TRAF[TERMINAL_TO_ROADM[s_t]].remove(traf_id)
                                 traf_to_lightpath_Release(traf_id=traf_id)
                                 reassign_traf.append((s_t, d_t))
                        elif gosnr < 16:
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
                        traf_id = install_Traf(s_t, d_t, routes, cur_time=0, down_time=float('inf'))
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
                    traf_id = install_Traf(src_t, dst_t, routes, cur_time=0, down_time=float('inf'))
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
                            traf_id = install_Traf(s_t, d_t, routes, cur_time=0, down_time=float('inf'))
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
                    # if # of continously failed requests >3, discard remained requests
                    if count == 4:
                        fails = factor*MAX_traf[src]/CPRI_CAP - len(ROADM_TRAF[src])
                        RRH_traf[src_t] += fails
                        Rej[src_t] += fails
                        Total_Rej += fails
                        break
            # check if there are more traffic than max processing traf, if yeas, release some
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

    #     OneG = 0
    #     TwoG = 0
    #     FiftyG = 0
    #     UnderUse = 0
    #     for lightpath_id, info in LIGHTPATH_INFO.items():
    #         if LIGHTPATH_INFO[lightpath_id]['link_cap']/CPRI_CAP/2 > len(LIGHTPATH_INFO[lightpath_id]['traf_set']):
    #             UnderUse += 1
    #         link_cap = LIGHTPATH_INFO[lightpath_id]['link_cap']
    #         if link_cap == 100:
    #             OneG += 1
    #         elif link_cap ==200:
    #             TwoG += 1
    #         elif link_cap ==50:
    #             FiftyG += 1
    #     total_wav = 0
    #     for key in NETLINK_INFO.keys():
    #         total_wav += len(NETLINK_INFO[key].items())
    #     avg_wav = (1.0 * total_wav ) / (NUM_NODE-1)
    #
    #
    # print('==traf')
    # for item in TRAFFIC_INFO.items():
    #     print(item)
    # print('==Lightpath')
    # fail_paths= []
    # for item in LIGHTPATH_INFO.items():
    #     print(item)
    #     path = item[1]['path']
    #     ch = item[1]['channel_id']
    #     gosnr = item[1]['GOSNR']
    #     powers, osnrs, gosnrs, ase, nli = Mininet_monitorLightpath(path=path, channel=ch, nodes=NODES)
    #     print('gosnr', gosnr, gosnrs[-1])
    #     if gosnrs[-1]< 24:
    #         fail_paths.append((gosnrs[-1],osnrs[-1], powers[-1], item))
    # for gosnr, osnr, power, item in fail_paths:
    #     print('fail',gosnr, osnr, abs_to_db(power), item)
    # #print('==rej', Rej, 1.0*Rej/N)
    # print('r2-r1, chs', len(NETLINK_INFO['r2', 'r1'].items()))
    # print('r2-r3, chs', len(NETLINK_INFO['r2', 'r3'].items()))
    # print('r3-r4, chs', len(NETLINK_INFO['r3', 'r4'].items()))
    # print(ROADM_TRAF)
    # print('BBU_Processing_traf', BBU_traf)
    # print('rej', Rej)
    # print('RRH_TRAF', RRH_traf)
    # print('rej_ratio', 1.0*Rej['t2']/RRH_traf['t2'], 1.0*Rej['t3']/RRH_traf['t3'])
    # print('total_rej_rate', 1.0* Total_Rej/sum(RRH_traf.values()) )


if __name__ == '__main__':
    #RoadmPhyTest()
    TrafficTest()


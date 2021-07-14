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
#from Control_Test_Lum import Lumentum_Control_NETCONF
from Control_Test_Mininet_REST import Mininet_Control_REST
from fakecontroller import ListenPortBase

km = dB = dBm = 1.0
m = .001

# Parameters
Controller_Lum = None#Lumentum_Control_NETCONF()
print(f"Starting Mininet rest controller")
Controller_Mininet = Mininet_Control_REST()

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
TRAFFIC_INFO = defaultdict( defaultdict ) # id : {'src':src, 'dst':dst, 'lightpath_id': lightpath_id, 'up_time':s_time, 'down_time': d_time}
LIGHTPATH_INFO = defaultdict( defaultdict ) # id : {'path':path, 'channel_id': channel_id, 'traf_set': set(), 'up_time':s_time, 'down_time': d_time, 'OSNR': 25, 'GOSNR': 24.5 }
SRC_DST_TO_LIGHTPATH = defaultdict( set ) # (src, dst) : {set[lightpath_id]}
SRC_DST_TO_CHANNEL = defaultdict( set ) # (src, dst) : {set[channels]}
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
ROADM_TO_ID = {}
TERMINAL_TO_ID = {}
for i in range(NUM_NODE):
    name_roadms.append('r%d'%(i+1))
    name_terminals.append('t%d'%(i+1))
    ROADM_TO_TERMINAL['r%d' % (i + 1)] = 't%d' % (i + 1)
    TERMINAL_TO_ROADM['t%d' % (i + 1)] = 'r%d' % (i + 1)
    ROADM_TO_ID['r%d' % (i + 1)] = (i + 1)
    TERMINAL_TO_ID['t%d' % (i + 1)] = (i + 1)
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

def Mininet_installPath(lightpath_id, path, channel, power=0):
    "intall switch rules on roadms along a lightpath for some signal channels"
    print(f"INSTALLING new lightpath onto the mininet System! ch.{channel} from {path[0]}->{path[-1]}")
    src_id, dst_id = TERMINAL_TO_ID[path[0]], TERMINAL_TO_ID[path[-1]]
    # Install a route
    Controller_Mininet.installPath(path=path, channels=[channel])
    # Configure terminals and start transmitting
    terminal = Controller_Mininet.net.terminals[src_id - 1]
    terminal2 = Controller_Mininet.net.terminals[dst_id - 1]
    Controller_Mininet.configureTerminal(terminal=terminal, channel=channel, power=power, type='transceiver')
    Controller_Mininet.configureTerminal(terminal=terminal2, channel=channel, power=power, type='receiver')
    Controller_Mininet.turnonTerminal(terminal=terminal)
    #Controller_Mininet.turnonTerminal(terminal=terminal2)
    # Configure routers
    router = Controller_Mininet.net.switches[src_id - 1]
    router2 = Controller_Mininet.net.switches[dst_id - 1]
    Controller_Mininet.configurePacketSwitch(src=src_id, dst=dst_id, channel=channel, router=router, port=ListenPortBase+src_id)
    Controller_Mininet.configurePacketSwitch(src=dst_id, dst=src_id, channel=channel, router=router2, port=ListenPortBase+dst_id)
    return lightpath_id


def Mininet_uninstallPath(lightpath_id):
    "delete switch rules on roadms along a lightpath for some signal channels"


    path = LIGHTPATH_INFO[lightpath_id]['path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    Controller_Mininet.uninstallPath(path=path, channels=[channel])
    return lightpath_id


def Mininet_setupLightpath(lightpath_id, path, channel):
    "configure a lightpath "
    print(f"Installing Lightpath {lightpath_id} on channel {channel} along path {path}")
    return Mininet_installPath(lightpath_id, path, channel)


def Mininet_teardownLightpath(lightpath_id):
    "remove a lightpath"

    return Mininet_uninstallPath(lightpath_id)


def Mininet_monitorLightpath(lightpath_id):
    "monitoring a signal along a lightpath"

    path = LIGHTPATH_INFO[lightpath_id]['path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    osnrs, gosnrs = list(), list()
    for i in range(1,len(path)-2):
        node1, node2 = path[i], path[i+1]
        ID1, ID2 = ROADM_TO_ID[node1], ROADM_TO_ID[node2]
        monitorKey = Controller_Mininet.getMonitorKey(src_id=ID1, dst_id=ID2)
        osnr, gosnr = Controller_Mininet.monitorOSNRbyKey(key=monitorKey, channel=channel)
        osnrs.append(osnr)
        gosnrs.append(gosnr)
    return osnrs, gosnrs
    #Controller_Mininet.monitorOSNR(channel=channel, gosnrThreshold=15)

def Mininet_monitorDifference(file=None):
    Monitors = Controller_Mininet.monitorKeyAndLightpaths()
    print('------------------------------------------------------------------------------------------\n')
    if file: file.write('------------------------------------------------------------------------------------------\n')
    for monitor in Monitors:
        print(f'Mininet_Monitor {monitor} has CHANNELS \t{ Monitors[monitor]}')
        if file: file.write(f'Mininet_Monitor {monitor} has CHANNELS \t{Monitors[monitor]}\n')
        MonKey = Controller_Mininet.monitorKey(monitor)
        Light_IDs = sorted(NETLINK_INFO[MonKey[0], MonKey[1]].keys())
        string_Light_IDs = [str(x) for x in Light_IDs]
        zero='0'
        if zero in string_Light_IDs: string_Light_IDs.remove(zero)
        print(f'NETLINK_info: {MonKey[0]}-{MonKey[1]} has channels \t\t\t          {string_Light_IDs}')
        if file: file.write(f'NETLINK_info: {MonKey[0]}-{MonKey[1]} has channels \t\t\t          {string_Light_IDs}\n')
        print('------------------------------------------------------------------------------------------\n')
        if file: file.write('------------------------------------------------------------------------------------------\n')

################# END ####################



############### COSMOS Lumentum ###############

def Lumentum_installPath(lightpath_id, path, channel):
    "intall switch rules on roadms along a lightpath for some signal channels"

    return Controller_Lum.installPath(path=path, channel=channel, lightpathID=lightpath_id)


def Lumentum_uninstallPath(lightpath_id):
    "delete switch rules on roadms along a lightpath for some signal channels"

    path = LIGHTPATH_INFO[lightpath_id]['path']
    return Controller_Lum.uninstallPath(path=path, lightpathID=lightpath_id)


def Lumentum_setupLightpath(lightpath_id, path, channel):
    "configure a lightpath "

    return Lumentum_installPath(lightpath_id, path, channel)


def Lumentum_teardownLightpath(lightpath_id):
    "remove a lightpath"

    return Lumentum_uninstallPath(lightpath_id)


def Lumentum_MonitorLightpath(lightpath_id):
    path = LIGHTPATH_INFO[lightpath_id]['path']
    s_d_info = Controller_Lum.channel_monitor(path=path, lightpathID=lightpath_id)
    return s_d_info

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


def install_Lightpath(path, channel, up_time=0.0, down_time = float('inf'), Mininet = False):
    "intall switch rules on roadms along a lightpath for some signal channels, update control database"

    ## Install ROADM rules
    global LIGHTPATH_ID
    LIGHTPATH_ID += 1
    if not Mininet:
        # id : {'path':path, 'channel': channel_id, 'traf': set(), 'up_time':s_time, 'down_time': d_time, 'OSNR': 25, 'GOSNR': 24.5 }
        res = Lumentum_setupLightpath(lightpath_id=LIGHTPATH_ID, path=path, channel=channel)
        count =0
        while not res and count<5:
            res = Lumentum_setupLightpath(lightpath_id=LIGHTPATH_ID, path=path, channel=channel)
            count += 1

    else:
        res = Mininet_setupLightpath(lightpath_id=LIGHTPATH_ID, path=path, channel=channel)
    if not res:
        LIGHTPATH_ID -= 1
        return None
    for i in range(len(path) - 1):
        NETLINK_INFO[path[i], path[i + 1]][channel] = LIGHTPATH_ID  # channel with lightpath_id
        #NETLINK_INFO[path[i + 1], path[i]][channel] = LIGHTPATH_ID
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
    SRC_DST_TO_CHANNEL[path[0], path[-1]].add(channel)
    # (src, hop, dst) : {'channel_id': lightpath_id}

    PATH_CH_TO_LIGHTPATH[tuple(path)][channel] = int(LIGHTPATH_ID)
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
    return list(avai_lightpaths)


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


def install_Traf(src, dst, routes, cur_time, down_time=float('inf'), Mininet = False):
    '''
    source RRH node to destination BBU node
    '''
    global TRAFFIC_ID
    avai_lightpaths = check_lightpath_for_traf(src, dst)
    lightpath_id = None
    if avai_lightpaths:
        lightpath_id = avai_lightpaths[0]

    if lightpath_id:
        print("\nGrooming Traffic into existing lightpath")
        if not Mininet:
            info=Lumentum_MonitorLightpath(lightpath_id=lightpath_id)
            print('source ROADM', info[0])
            print('destination ROADM', info[1])
        else:
            info=Mininet_monitorLightpath(lightpath_id=lightpath_id)
            print('osnr', info[0])
            print('gosnr', info[1])
        TRAFFIC_ID += 1
        traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
        LIGHTPATH_INFO[lightpath_id]['traf_set'].add(TRAFFIC_ID)
        channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
        print(f"Grooming traf_id {traf_id} into channel {channel} | {src}->{dst}")
        return traf_id
    else:
        print('\ninstall a new lightpath for traffic!')
        all_path_info = routes[src][dst]
        for path_info in all_path_info:
            path = path_info
            if not Mininet:
                path = path[1:-1]
            chs = waveAvailibility(path=path)
            if chs:
                ch = waveSelection(chs)
                lightpath_id = install_Lightpath(path=path, channel=ch, up_time=cur_time, down_time=down_time, Mininet=Mininet)
                if lightpath_id:
                    TRAFFIC_ID += 1
                    traf_id = traf_to_lightpah_Assignment(TRAFFIC_ID, lightpath_id, down_time=down_time)
                    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
                    if not Mininet:
                        info = Lumentum_MonitorLightpath(lightpath_id=lightpath_id)
                        print('source ROADM', info[0])
                        print('destination ROADM', info[1])
                    else:
                        info = Mininet_monitorLightpath(lightpath_id=lightpath_id)
                        print('osnr', info[0])
                        print('gosnr', info[1])
                    print(f"Grooming traf_id {traf_id} into channel {channel} | {src}->{dst} | INSTALLED NEW PATH | ")
                    return traf_id
    print('traffic is rejected!')
    return False


def uninstall_Lightpath(lightpath_id, Mininet = False):
    "delete switch rules on roadms along a lightpath for some signal channels"

    print('tear down a lightpath!')
    if not Mininet:
        res = Lumentum_uninstallPath(lightpath_id=lightpath_id)
        count = 0
        while not res and count<5:
            res = Lumentum_uninstallPath(lightpath_id=lightpath_id)
            count+=1
    else:
        res = Mininet_uninstallPath(lightpath_id=lightpath_id)
    if not res:
        return None
    path = LIGHTPATH_INFO[lightpath_id]['path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    for i in range(len(path) - 1):
        del NETLINK_INFO[path[i], path[i + 1]][channel]
        #del NETLINK_INFO[path[i + 1], path[i]][channel]
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

def testMininet(Mininet_Enable = False):
    file = open('Monitor_Lightpath.txt','w')
    RoadmPhyNetwork()
    AllLinks = getLinks(NETLINKS)
    global GRAPH, NODES
    GRAPH = netGraph(AllLinks['links'])
    routes = {node: FindRoute(node, GRAPH, name_terminals)
              for node in name_terminals}

    t1 = ROADM_TO_TERMINAL['r1']
    t2 = ROADM_TO_TERMINAL['r2']
    t3 = ROADM_TO_TERMINAL['r3']
    t4 = ROADM_TO_TERMINAL['r4']

    Forward_paths =  [(t1,t4),(t1,t3),(t2,t4),(t1,t2),(t2,t3),(t3,t4)]
    Backward_paths = [(t4,t1),(t3,t1),(t4,t2),(t2,t1),(t3,t2),(t4,t3)]

    def Test_Loop(node1, node2):
        print(f" Setting up path from {node1}->{node2}")
        file.write(f" Setting up path from {node1}->{node2}\n")
        traf_id = install_Traf(node1, node2, routes, cur_time=0, down_time=float('inf'), Mininet=Mininet_Enable)
        lightpath_id = TRAFFIC_INFO[traf_id]['lightpath_id']
        osnrs, gosnrs = Mininet_monitorLightpath(lightpath_id=lightpath_id)
        osnr, gosnr = min(osnrs), min(gosnrs)
        LIGHTPATH_INFO[lightpath_id]['GOSNR'] = gosnr
        LIGHTPATH_INFO[lightpath_id]['OSNR'] = osnr
        channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
        print(f"+++ Installed path: {node1}->{node2}, channel: {channel} osnr: {osnr} gosnr:{gosnr} +++")
        file.write(f"+++ Installed path: {node1}->{node2}, channel: {channel} osnr: {osnr} gosnr:{gosnr} +++\n")
        Mininet_monitorDifference(file)
    count=0
    countstop=10
    for i in range(1, 3):
        print("**************************************************")
        print("************** STARTING ROUND", i, " ************")
        print("**************************************************")
        file.write(f"************************Starting round {i}**********************\n")
        for path in Forward_paths:
            Test_Loop(path[0], path[1])
        print(f"\n**************Reverse paths {i}*******************")
        file.write(f"************************Starting REVERSE round {i}**********************\n")
        for path in Backward_paths:
            Test_Loop(path[0], path[1])

    for path in sorted(SRC_DST_TO_CHANNEL):
        print(path, SRC_DST_TO_CHANNEL[path])

if __name__ == '__main__':
    #RoadmPhyTest()
    testMininet(Mininet_Enable=True)
    #testMininet()

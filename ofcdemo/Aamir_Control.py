from fakecontroller import ListenPortBase
from Aamir_REST import Mininet_Control_Rest
Controller_Mininet = Mininet_Control_Rest
from collections import defaultdict
import random, copy
from inspect import currentframe, getframeinfo

def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno


km = db = dbm = 1.0
m = 0.001

#Mininet variables
control = Mininet_Control_Rest()
net = control.net

NUM_NODE = 4
NUM_WAVES = 90
LIGHTPATH_INFO = defaultdict(defaultdict)
LINK_CAP = 200
#DOWNLINK_CAP = 100
CPRI_CAP = 25

NETLINK_INFO = defaultdict( defaultdict ) # ('node_name', 'node_name'): {channel_id: lightpath_id}
SRC_DST_TO_LIGHTPATH = defaultdict( set ) # (src, dst) : {set[lightpath_id]}
TRAFFIC_INFO = defaultdict( defaultdict ) # id : {'src':src, 'dst':dst, 'lightpath_id': lightpath_id}
CHANNEL_TO_LIGHTPATH = defaultdict( set ) #Channel: {lightpath_id:lightoath_id, path:path}

TERMINALS = net.terminals
ROADMS = net.roadms
TRAFFIC_ID = 0
LIGHTPATH_ID = 0
TERMINAL_ID = {}
ROADM_ID = {}
for i in range(NUM_NODE):
    TERMINAL_ID['t%d'%(i+1)] = (i+1)
    ROADM_ID['r%d'%(i+1)]=(i+1)

################ MININET FUNCTIONS ########################################333

def check_lightpaths(node1, node2):
    "Checks the lightpaths from src_id to dst_id"
    src_id, dst_id = ROADM_ID[node1], ROADM_ID[node2]
    key = control.getMonitorKey(src_id,dst_id)
    channel_list = control.lightpathsInMonitor(key=key)
    if channel_list:
        channels = [int(channel) for channel in channel_list]
    else:
        """This basically returns an epty list if we can't find the keys"""
        channels = channel_list
    return channels

def install_lightpath(path, channel, power=0.0, net=net):
    "Installs lightpath from point a to point b"
    # Install a route
    src, dst = path[0], path[-1]
    src_id, dst_id = TERMINAL_ID[src], TERMINAL_ID[dst]
    control.installPath(path=path, channels=[channel])
    # Configure terminals and start transmitting
    terminal = net.terminals[src_id-1]
    terminal2 = net.terminals[dst_id-1]
    control.configureTerminal(terminal=terminal, channel=channel, power=power)
    control.configureTerminal(terminal=terminal2, channel=channel, power=power)
    control.turnonTerminal(terminal=terminal)
    control.turnonTerminal(terminal=terminal2)
    # Configure routers
    router = net.switches[src_id-1]
    router2 = net.switches[dst_id-1]
    control.configurePacketSwitch(src=src_id, dst=dst_id, channel=channel,
                                  router=router ,port=ListenPortBase + src_id)
    control.configurePacketSwitch(src=dst_id, dst=src_id, channel=channel,
                                  router=router2, port=ListenPortBase + dst_id)

def monitorLightpath(path, channel):
    "Monirors the channels"
    osnrs, gosnrs = list(), list()
    for i in range(1,len(path)-2):
        node1,node2 = path[i], path[i+1]
        ID1, ID2 = ROADM_ID[node1], ROADM_ID[node2]
        key = control.getMonitorKey(ID1, ID2)
        osnr, gosnr = control.monitorOSNRbyKey(key, channel)
        osnrs.append(osnr)
        gosnrs.append(gosnr)
    return osnrs, gosnrs

def signalsInMonitors():
    control.signalsInMonitors()

def Mininet_reset():
    'Should reset Mininet TODO: DOES NOT WORK'
    control.reset()

######################## INSTALL LIGHTPATH AND TRACK INFORMATION ################

def install_Lightpath(path, channel):
    "iNSTALLS A NEW LIGHTPATH AND STORES THE INFORMATION"
    global LIGHTPATH_ID
    LIGHTPATH_ID+=1
    install_lightpath(path=path, channel=channel)
    osnrs, gosnrs = monitorLightpath(path, channel)
    osnr = min(osnrs)
    gosnr = min(gosnrs)
    print(f"osnrs:{osnrs}, gosnrs:{gosnrs}, lightpath:{LIGHTPATH_ID}  LINE# {get_linenumber()}")

    for i in range(1,len(path)-1):
        NETLINK_INFO[path[i], path[i+1]][channel] = LIGHTPATH_ID
        NETLINK_INFO[path[i+1], path[i]][channel] = LIGHTPATH_ID



    LIGHTPATH_INFO[LIGHTPATH_ID]['path'] = tuple(path)
    LIGHTPATH_INFO[LIGHTPATH_ID]['channel_id'] = channel
    LIGHTPATH_INFO[LIGHTPATH_ID]['link_cap'] = LINK_CAP
    LIGHTPATH_INFO[LIGHTPATH_ID]['traf_set'] = set()
    LIGHTPATH_INFO[LIGHTPATH_ID]['power'] = 0
    LIGHTPATH_INFO[LIGHTPATH_ID]['OSNR'] = osnr
    LIGHTPATH_INFO[LIGHTPATH_ID]['GOSNR'] = gosnr
    # (src, dst) Add a lightpath
    SRC_DST_TO_LIGHTPATH[path[0], path[-1]].add(LIGHTPATH_ID)
    CHANNEL_TO_LIGHTPATH[channel].add((LIGHTPATH_ID, tuple(path), tuple(osnrs), tuple(gosnrs)))

    #CHANNEL_TO_LIGHTPATH[channel][LIGHTPATH_ID]['path'] = tuple(path)
    #print(F"\n LIGHTPATH_INFO:{LIGHTPATH_INFO[LIGHTPATH_ID]} LINE#{get_linenumber()}")

    return LIGHTPATH_ID



def waveSelection(channels):
    "Selects wavelength from a list of channels"
    channels = list(channels)
    return random.choice(channels)
    #return channels[0]

def waveAvailability(path):
    "Returns a list of channels unused by the system"
    available_channels = set([i for i in range(1, NUM_WAVES + 1)])
    links_in_channels =[]
    for i in range(len(path)-3):
        link_channels = check_lightpaths(path[i+1], path[i+2])
        #link_channels = set(NETLINK_INFO[path[i], path[i + 1]].keys())
        links_in_channels.extend(link_channels)
    Available_links = available_channels.difference(links_in_channels)
    return list(Available_links)

def check_lightpath_for_traf(src, dst):
    ''' Check if there is underprovisioned lightpaths for CPRI traffic'''
    lighpaths = SRC_DST_TO_LIGHTPATH[src,dst]
    avai_lightpaths = set()
    for lighpath_id in lighpaths:
        if len(LIGHTPATH_INFO[lighpath_id]['traf_set']) < LIGHTPATH_INFO[lighpath_id]['link_cap']/CPRI_CAP:
            avai_lightpaths.add(lighpath_id)
    return list(avai_lightpaths)

def monitorLightpathbyID(lightpath_id):
    "Checks osnr and gosnr of a lightpath given the id"
    path = LIGHTPATH_INFO[lightpath_id]['path']
    channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
    osnrs, gosnrs = monitorLightpath(path=path, channel=channel)
    return osnrs, gosnrs
def groomTraffficOnLightpath(traf_id, lightpath_id):
    "Groom Traffic request into lightpath"
    LIGHTPATH_INFO[lightpath_id]["traf_set"].add(traf_id)
    path = LIGHTPATH_INFO[lightpath_id]["path"]
    src, dst = path[0], path[-1]
    TRAFFIC_INFO[traf_id]['src'], TRAFFIC_INFO[traf_id]['dst'], \
    TRAFFIC_INFO[traf_id]['lightpath_id'] = src, dst, lightpath_id
    return traf_id
# This is the main function which the controller uses. Here what happens is
# Here we install traffic until all the routes are made up

def install_Traf(src, dst, routes):
    '''
    Install traffic onto the system
    '''
    global TRAFFIC_ID
    availableLightpaths = check_lightpath_for_traf(src, dst)
    lightpath_id = None
    if availableLightpaths:
        lightpath_id = availableLightpaths[0]

    if lightpath_id:
        print("\nGrooming Traffic into existing lightpath")
        TRAFFIC_ID += 1
        traf_id = groomTraffficOnLightpath(TRAFFIC_ID, lightpath_id)
        channel = LIGHTPATH_INFO[lightpath_id]['channel_id']
        print(f"Grooming traf_id {traf_id} in channel {channel} "
              #f"| {src}->{dst} | osnr: {osnrs}, gosnr:{gosnrs}"
              f"")
        return traf_id

    else:
        print("\nInstalling new lightpath for traffic")
        potential_paths = [routes[src][dst]]
        print(potential_paths)
        for path in potential_paths:
            print(path)
            available_channels = waveAvailability(path)
            if available_channels:
                TRAFFIC_ID += 1
                channel = waveSelection(available_channels)
                lightpath_id = install_Lightpath(path=path, channel=channel)
                traf_id = groomTraffficOnLightpath(TRAFFIC_ID, lightpath_id)
                #info = monitorLightpathbyID(lightpath_id=lightpath_id)
                print(f"Grooming traf_id {traf_id} in channel {channel} "
                      #f"| {src}->{dst} | osnr: {info[0]}, gosnr{info[1]}"
                      f"")
                return traf_id
    print(f"Traffic request rejected for {src}->{dst}")
    return False

def TEST_Install_traf(src, dst, routes):
    "A test install function which monitors a signal from a to b"
    global TRAFFIC_ID
    TRAFFIC_ID +=1
    path = routes[src][dst]
    available_channels = waveAvailability(path)
    channel = waveSelection(available_channels)
    lightpath_id = install_Lightpath(path=path, channel=channel)
    traf_id = groomTraffficOnLightpath(TRAFFIC_ID, lightpath_id)
    return traf_id

def test():
    file = open('checkpath.txt','w')
    file2 = open('checkpath2.txt','w')


    file.write('checking lightpath allocations')
    control = Mininet_Control_Rest()
    net = control.net
    t1,t2,t3,t4 = net.terminals
    routes = net.routes

    Forward_paths   = [(t1, t4), (t1, t3), (t2, t4), (t1, t2), (t2, t3), (t3, t4)]
    Backward_paths  = [(t4, t1), (t3, t1), (t4, t2), (t2, t1), (t3, t2), (t4, t3)]


    def TestLoop(node1, node2):
        "Ultimately my goal is for this to be working, with no errors"
        print(f"\nTransmitting from {node1}->{node2}")
        traf_id = install_Traf(node1, node2, routes)
        lightpath_id = TRAFFIC_INFO[traf_id]['lightpath_id']
        osnrs, gosnrs = monitorLightpathbyID(lightpath_id)
        #print(f"osnrs:{osnrs}, \ngosnrs:{gosnrs}")

    def TestLoop2(node1, node2):
        "Need to start by getting this to work"
        print(f"\nTransmitting from {node1}->{node2}")
        traf_id = TEST_Install_traf(node1, node2, routes)
        lightpath_id = TRAFFIC_INFO[traf_id]['lightpath_id']
        osnrs, gosnrs = monitorLightpathbyID(lightpath_id)
        #print(f"osnrs:{osnrs}, \ngosnrs:{gosnrs}")

    channel = 1
    for i in range(0,10):
        file.write(f"\n Round # {i}")
        for path in Forward_paths:
            channel +=1
            if channel == 90: break
            node1 = path[0]
            node2 = path[1]
            #TestLoop(node1, node2)
            TestLoop2(node1, node2)
            TestLoop2(node2, node1)
            #TestLoop(node2, node1)
            signalsInMonitors()
        LIGHTPATH_INFO_COPY = copy.deepcopy(LIGHTPATH_INFO)
        if channel == 90: break
        for lightpath in LIGHTPATH_INFO:
            file.write(f"\nlightpath {lightpath}, channel {LIGHTPATH_INFO[lightpath]['channel_id']}:"
                       f":\t{LIGHTPATH_INFO[lightpath]}")
        for lightpath in LIGHTPATH_INFO_COPY:
            osnrs, gosnrs = monitorLightpathbyID(lightpath_id=lightpath)
            osnr, gosnr = min(osnrs), min(gosnrs)
            LIGHTPATH_INFO_COPY[lightpath]['OSNR'] = osnr
            LIGHTPATH_INFO_COPY[lightpath]['GOSNR'] = gosnr
            file2.write(f"\nlightpath {lightpath}, channel {LIGHTPATH_INFO_COPY[lightpath]['channel_id']}:"
                       f":\t{LIGHTPATH_INFO_COPY[lightpath]}")

        file.write("\n")
        file2.write("\n")


    for lightpath in sorted(LIGHTPATH_INFO):
        print(lightpath, LIGHTPATH_INFO[lightpath])
    for channel in sorted(CHANNEL_TO_LIGHTPATH):
        print(channel, CHANNEL_TO_LIGHTPATH[channel])

test()



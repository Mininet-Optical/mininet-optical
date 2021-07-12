import random

from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR, ListenPortBase )
from collections import defaultdict

class Mininet_Control_Rest(object):
    def __init__(self):
        self.net = RESTProxy()
        # Fetch nodes
        self.net.allNodes = fetchNodes(self.net)
        self.net.switches = sorted(node for node, cls in self.net.allNodes.items()
                                   if cls == 'OVSSwitch')
        self.net.terminals = sorted(node for node, cls in self.net.allNodes.items()
                                    if cls == 'Terminal')
        self.net.roadms = sorted(node for node, cls in self.net.allNodes.items()
                                 if cls == 'ROADM')
        self.net.monitors = sorted(node for node, cls in self.net.allNodes.items()
                                   if cls == 'Monitor')
        self.net.nodes = self.net.terminals + self.net.roadms

        # Fetch links
        self.net.allLinks, self.net.roadmLinks, self.net.terminalLinks = fetchLinks(self.net)

        # Create adjacency dict
        self.net.graph = self.buildGraph(self.net.allLinks)

        # Fetch ports
        self.net.ports = fetchPorts(self.net, self.net.roadms + self.net.terminals + self.net.switches)

        # Calculate inter-pop routes
        self.net.routes = {node: self.route(node, self.net.graph, self.net.terminals)
                           for node in self.net.terminals}

    def reset(self):
        for terminal in self.net.terminals:
            TerminalProxy(terminal).reset()
        for roadm in self.net.roadms:
            ROADMProxy(roadm).reset()

    def monitorKey(self, monitor):
        "Key for sorting monitor names"
        items = monitor.split('-')
        return items

    def getMonitorKey(self, src_id, dst_id, spanID=1):
        "Generate key for monitors"
        return 'r{}-r{}-amp{}-monitor'.format(src_id, dst_id, spanID)


    def monitorOSNRs(self):

        monitors = self.net.monitors
        for key in sorted(monitors):
            print(key)
            response = self.net.get('monitor', params=dict(monitor=key))
            osnrdata = response.json()['osnr']
            #print(osnrdata)
            return key, osnrdata

    def monitorOSNRbyKey(self, key, channel):

        monitors = self.net.get('monitors').json()['monitors']
        if key in sorted(monitors, key=self.monitorKey):
            response = self.net.get('monitor', params=dict(monitor=key))
            osnrdata = response.json()['osnr']
            if str(channel) in osnrdata.keys():
                THz = float(osnrdata[str(channel)]['freq']) / 1e12
                osnr, gosnr = osnrdata[str(channel)]['osnr'], osnrdata[str(channel)]['gosnr']
                return osnr, gosnr
            elif str(channel) not in osnrdata.keys():
                #print(f"ERROR: Can't find channel {channel} on monitor {key}, response: {response}")
                #print(f"{key} has the following channels: {osnrdata.keys()}")
        return 0, 0

    def signalsInMonitors(self):
        monitors = self.net.get('monitors').json()['monitors']
        for key in sorted(monitors, key=self.monitorKey):
            response = self.net.get('monitor', params=dict(monitor=key))
            osnrdata = response.json()['osnr']
            print(key, osnrdata.keys())

    def lightpathsInMonitor(self, key=None):
        monitors = self.net.get('monitors').json()['monitors']
        if key in sorted(monitors, key=self.monitorKey):
            response = self.net.get('monitor', params=dict(monitor=key))
            osnrdata = response.json()['osnr']
            #print(key, osnrdata.keys())
            return osnrdata.keys()


    def buildGraph(self, links):
        "Return an adjacency dict for links"
        neighbors = defaultdict( defaultdict )
        for link in links:
            src, dst = link  # link is a dict but order doesn't matter
            srcport, dstport = link[ src ], link[ dst ]
            neighbors.setdefault( src, {} )
            neighbors[ src ][ dst ] = dstport
            neighbors[ dst ][ src ] = srcport
        return dict( neighbors )

    def route(self, src, graph, destinations ):
        """Route from src to destinations
           neighbors: adjacency list
           returns: routes dict"""
        routes, seen, paths = {}, set( (src,) ), [ (src,) ]
        while paths:
            path = paths.pop( 0 )
            lastNode = path[ -1 ]
            for neighbor in graph[ lastNode ]:
                if neighbor not in seen:
                    newPath = ( path + (neighbor, ) )
                    paths.append( newPath )
                    if neighbor in destinations:
                        routes[ neighbor ] = newPath
                    seen.add( neighbor)
        return routes

    def configureTerminal(self, terminal, channel, power=0.0):
        "Configure terminals statically: ethN <-> wdmM:channel"
        print("*** Configuring terminals")
        proxies = { terminal: TerminalProxy(terminal) }
        termProxy = proxies[ terminal ]
        ethPorts = sorted( int(port) for port, intf in self.net.ports[ terminal ].items()
                           if 'eth' in intf )
        wdmPorts = sorted( int(port) for port, intf in self.net.ports[ terminal ].items()
                           if 'wdm' in intf )
        print(f"+++TERMINAL configurations: proxies: {proxies} termProxy: {termProxy}"
              #f"wdmPorts {terminal}: {wdmPorts} \n"
              #f"ethPorts {terminal}: {ethPorts} \n"
              #f"All ports: {self.net.ports[ terminal ].items()}"
              f"")
        if channel is not None:
            ethPort, wdmPort = ethPorts[channel-1], wdmPorts[channel-1]
        #print('Pin-Pout-channel', ethPort, wdmPort, channel)
        termProxy.connect( ethPort=ethPort, wdmPort=wdmPort,
                           channel=channel, power=power )
        print(f"*** Turning on terminal {terminal} *** Channel: {channel}, ethPort:{ethPort}, wdmPort:{wdmPort}")


    def turnonTerminal(self, terminal):
        "turn on terminal"
        proxies = {terminal: TerminalProxy(terminal)}
        proxies[terminal].turn_on()


    def configurePacketSwitch(self, src, dst, channel, router, port):
        "Configure Open vSwitch 'routers' using OpenFlow"

        print( "*** Configuring Open vSwitch 'routers' remotely... " )

        def subnet( pop ):
            return '10.%d.0.0/24' % pop

        routerProxy = OFSwitchProxy( name=router, port=port )

        # Initialize flow table
        print( 'Configuring', router, 'at', routerProxy.remote, 'via OpenFlow...' )
        routerProxy.dpctl( 'del-flows' )

        # Find local port
        ethports = sorted( int(port) for port, intf in self.net.ports[ router ].items()
                           if 'eth' in intf )
        #print('==router ethports==', ethports)
        localport = ethports[ -1 ]

        # to local
        for protocol in 'ip', 'icmp', 'arp':
            #print('add-flow, proto, dst, port', protocol, subnet(src), localport)
            flow = ( protocol + ',ip_dst=' + subnet( src )+
                     ',actions=dec_ttl,output:%d' % localport )
            # print( router, 'add-flow',  flow )
            routerProxy.dpctl( 'add-flow', flow )
        # to destination
        for protocol in 'ip', 'icmp', 'arp':
            #print('add-flow, proto, dst, port', protocol, subnet(dst), channel)
            flow = ( protocol + ',ip_dst=' + subnet( dst )+
                     ',actions=dec_ttl,output:%d' % channel )
            # print( router, 'add-flow',  flow )
            routerProxy.dpctl( 'add-flow', flow )



    def installPath(self, path, channels):
        "Program a lightpath into the network"
        # Install ROADM rules
        for i in range(1, len(path) - 1 ):
            node1, roadm, node2 = path[i-1], path[i], path[i+1]
            port1 = self.net.graph[ node1 ][ roadm ]
            port2 = self.net.graph[ node2 ][ roadm ]
            print(f"segment {i}: {node1}-[{port1}]->{roadm}-[{port2}]->{node2}")
            # For terminal nodes, use the proper channel port(s)
            if i == 1:
                for channel in channels:
                    #print('pin-pout', channel, port2)
                    ROADMProxy( roadm ).connect( channel, port2, [channel] )
            elif i == len(path) - 2:
                for channel in channels:
                    #print('pin-pout', port1, channel)
                    ROADMProxy( roadm ).connect( port1, channel, [channel] )
            # For roadm nodes, forward the channels en masse
            else:
                #print('pin-pout', port1, port2)
                ROADMProxy( roadm ).connect( port1, port2, channels )

def test_1():
    control = Mininet_Control_Rest()
    net = control.net
    control.reset()
    #src_id, dst_id = 1, 4
    #src, dst = net.terminals[src_id - 1], net.terminals[dst_id - 1]
    t1,t2,t3,t4 = net.terminals
    TERMINAL_ID={}
    ROADM_ID={}
    id=1
    for terminal in net.terminals:
        TERMINAL_ID['t%d' %id] = id
        ROADM_ID['r%d' %id] = id
        id+=1
    print(TERMINAL_ID)

    Forward_paths = [(t1, t4), (t1, t3), (t2, t4), (t1, t2), (t2, t3), (t3, t4)]
    Backward_paths = [(t4, t1), (t3, t1), (t4, t2), (t2, t1), (t3, t2), (t4, t3)]

    def install_lightpath(path, src_id, dst_id, channel, power, net):

        # Install a route
        control.installPath(path=path, channels=[channel])
        # Configure terminals and start transmitting
        terminal = net.terminals[src_id-1]
        control.configureTerminal(terminal=terminal, channel=channel, power=power)
        terminal2 = net.terminals[dst_id-1]
        control.configureTerminal(terminal=terminal2, channel=channel, power=power)
        control.turnonTerminal(terminal=terminal)
        control.turnonTerminal(terminal=terminal2)
        # Configure routers
        router = net.switches[src_id-1]
        router2 = net.switches[dst_id-1]
        control.configurePacketSwitch(src=src_id, dst=dst_id, channel=channel, router=router ,port=ListenPortBase+src_id)
        control.configurePacketSwitch(src=dst_id, dst=src_id, channel=channel, router=router2, port=ListenPortBase + dst_id)

    def monitorLightpath(path, channel):
        osnrs, gosnrs = list(), list()
        for i in range(1,len(path)-2):
            node1,node2 = path[i], path[i+1]
            ID1, ID2 = ROADM_ID[node1], ROADM_ID[node2]
            key = control.getMonitorKey(ID1, ID2)
            osnr, gosnr = control.monitorOSNRbyKey(key, channel)
            osnrs.append(osnr)
            gosnrs.append(gosnr)
        return osnrs, gosnrs

    def TestLoop(node1, node2, channel):
        path = net.routes[node1][node2]
        src_id = TERMINAL_ID[path[0]]
        dst_id = TERMINAL_ID[path[-1]]
        install_lightpath(path, src_id, dst_id, channel, 0.0, net)
        osnrs, gosnrs = monitorLightpath(path, channel)
        print(f"osnrs:{osnrs}, \ngosnrs:{gosnrs}")


    channel=0
    for path in Forward_paths:
        node1 = path[0]
        node2 = path[1]
        channel+=1
        print(f"\n Transmitting channel {channel} from {node1}->{node2}")
        TestLoop(node1,node2,channel)

    channel = 0
    for path in Forward_paths:
        node1 = path[0]
        node2 = path[1]
        channel +=1
        print(f"\n checking channel {channel} from {node1}->{node2}")
        monpath = net.routes[node1][node2]
        monitorLightpath(monpath, channel)

    channel=0
    for path in Backward_paths:
        node1 = path[0]
        node2 = path[1]
        channel+=1
        print(f"\n Transmitting channel {channel} from {node1}->{node2}")
        TestLoop(node1,node2,channel)

    channel = 0
    for path in Backward_paths:
        node1 = path[0]
        node2 = path[1]
        channel +=1
        print(f"\n checking channel {channel} from {node1}->{node2}")
        monpath = net.routes[node1][node2]
        monitorLightpath(monpath, channel)

    key, osnrdata = control.monitorOSNRs()
    for osnr in osnrdata:
        print(key, osnr, osnrdata[osnr])
def test():

    control = Mininet_Control_Rest()
    net = control.net

    t1,t2,t3,t4 = net.terminals
    TERMINAL_ID={}
    ROADM_ID={}
    id=1
    for terminal in net.terminals:
        TERMINAL_ID['t%d' %id] = id
        ROADM_ID['r%d' %id] = id
        id+=1
    print(TERMINAL_ID)

    Forward_paths = [(t1, t4), (t1, t3), (t2, t4), (t1, t2), (t2, t3), (t3, t4)]
    Backward_paths = [(t4, t1), (t3, t1), (t4, t2), (t2, t1), (t3, t2), (t4, t3)]

    def install_lightpath(path, src_id, dst_id, channel, power, net):

        # Install a route
        control.installPath(path=path, channels=[channel])
        # Configure terminals and start transmitting
        terminal = net.terminals[src_id-1]
        control.configureTerminal(terminal=terminal, channel=channel, power=power)
        terminal2 = net.terminals[dst_id-1]
        control.configureTerminal(terminal=terminal2, channel=channel, power=power)
        control.turnonTerminal(terminal=terminal)
        control.turnonTerminal(terminal=terminal2)
        # Configure routers
        router = net.switches[src_id-1]
        router2 = net.switches[dst_id-1]
        control.configurePacketSwitch(src=src_id, dst=dst_id, channel=channel, router=router ,port=ListenPortBase+src_id)
        control.configurePacketSwitch(src=dst_id, dst=src_id, channel=channel, router=router2, port=ListenPortBase + dst_id)

    def TestLoop(node1, node2, channel):
        path = net.routes[node1][node2]
        src_id = TERMINAL_ID[path[0]]
        dst_id = TERMINAL_ID[path[-1]]
        install_lightpath(path, src_id, dst_id, channel, 0.0, net)

    def monitorLightpath(path, channel):
        osnrs, gosnrs = list(), list()
        for i in range(1,len(path)-2):
            node1,node2 = path[i], path[i+1]
            ID1, ID2 = ROADM_ID[node1], ROADM_ID[node2]
            key = control.getMonitorKey(ID1, ID2)
            print(key)
            osnr, gosnr = control.monitorOSNRbyKey(key, channel)
            osnrs.append(osnr)
            gosnrs.append(gosnr)
        print(osnrs, gosnrs)
        return osnrs, gosnrs

    channel=0
    for path in Forward_paths:
        node1 = path[0]
        node2 = path[1]
        channel+=1
        print(f"\n Transmitting channel {channel} from {node1}->{node2}")
        TestLoop(node1,node2,channel)

    for path in Forward_paths:
        node1 = path[0]
        node2 = path[1]
        channel +=1
        print(f"\n checking channel {channel} from {node1}->{node2}")
        monpath = net.routes[node1][node2]
        monitorLightpath(monpath, channel)

    key, osnrdata = control.monitorOSNRs()
    for osnr in osnrdata:
        print(key, osnr, osnrdata[osnr])
    # control.monitorOutputs()

#test_1()
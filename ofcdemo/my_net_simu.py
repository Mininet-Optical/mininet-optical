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

# Units


km = dB = dBm = 1.0
m = .001

# Parameters

NUM_WAV = 5
# ROADM port numbers (input and output)
LINE_PORT1 = NUM_WAV
LINE_PORT2 = NUM_WAV+1
NETLINKS = []
Traffics = defaultdict( defaultdict ) # id : {'path':path, 'signals':ch1, 'rule_path':[2,2]}
LIGHTPATH_ID = 1
NUM_NODE =4
name_roadms = []
name_terminals = []
Roadm_Rule_ID_dict = {}
for i in range(NUM_NODE):
    name_roadms.append('r%d'%(i+1))
    name_terminals.append('t%d'%(i+1))
    Roadm_Rule_ID_dict['r%d' % (i + 1)] = 1


# Physical model API helpers

def Span( km, amp=None ):
    "Return a fiber segment of length km with a compensating amp"
    return Segment( span=Fiber( length=km ), amplifier=amp )


# Physical Network simulation, created out of base PHY model objects

def RoadmPhyNetwork(lengths=[50 * km]):

    """Two ROADMs connected bidirectionally over a single link consisting
       of a boost amplifier and one or more fiber spans with compensating
       amplifiers. Source terminal t1 is connected to source ROADM r1,
       and destination ROADM r2 is connected to destination terminal t2,
       as follows:

       Eastbound:
       t1 -> r1 -> boost1e -> fiber span -> amp1e (...) -> r2 -> t2

       Westbound:
       t1 <- r1 <- (...) amp1w <- fiber span <- boost1w <- r2 <- t2

       We assign the port numbers explicitly and symmetrically:

       t1:0 -> 1:r1:0 -> 0:r2:1 -> 0:t2
       t1:0 <- 1:r1:0 <- 0:r2:1 <- 0:t2

       Which is to say ROADM ports in:0 and out:0 are LINE ports
       and ROADM ports in:1 and out:1 are ADD/DROP ports.

       Getting the port assignment right and the rules right
       is an essential, but tricky, part of getting any SDN
       network to work properly.
    """
    ###############################
    #      t1 - r1 ----- r2 - t2
    #           |         |
    #      t4 - r4 ----- r3 - t3
    ################################

    net = Network()

    # Network nodes
    transceivers = [ ( 'tx%d' % i, 0*dBm, 'C' )  for i in range(1, NUM_WAV+1) ]

    # each terminal includes NUM_WAV transceivers
    terminals = [
        net.add_lt( name, transceivers=transceivers, monitor_mode=mode )
        for name,mode in [('t%d'%i,'in') for i in range(1, NUM_NODE+1)] ]
    roadms = [
        net.add_roadm(name, monitor_mode=mode)
        for name, mode in [('r%d'%i,'in') for i in range(1, NUM_NODE+1)]]

    #roadms = [ net.add_roadm( 'r%d' % i ) for i in (1, 2, 3) ]
    nodes = net.name_to_node
    # Convenience alias
    link = net.add_link

    for k in range(1,NUM_NODE):
        print('==range=',k)
        # Eastbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers
        boost = net.add_amplifier( 'boost{}{}'.format(k,k+1), target_gain=17*dB, boost=True )
        spans = []
        for i, length in enumerate( lengths, start=1 ):
            amp = net.add_amplifier(
                'amp{}{}-{}'.format(k,k+1,i), target_gain=length*0.22*dB, monitor_mode='out')
            span = Span( length, amp=amp )
            spans.append( span )

        link(nodes['r%d' %k], nodes['r%d' %(k+1)], src_out_port=LINE_PORT2, dst_in_port=LINE_PORT1, boost_amp=boost,
             spans=spans)
        NETLINKS.append(('r%d' % k, LINE_PORT2, 'r%d' % (k + 1), LINE_PORT1))

        # Westbound link consisting of a boost amplifier going into
        # one or more segments of fiber with compensating amplifiers
        boost = net.add_amplifier( 'boost{}{}'.format(k+1,k), target_gain=17*dB, boost=True )
        spans = []
        for i, length in enumerate( lengths, start=1 ):
            amp = net.add_amplifier(
                'amp{}{}-{}'.format(k+1,k,i), target_gain=length*0.22*dB, monitor_mode='out')
            span = Span( length, amp=amp )
            spans.append( span )

        link(nodes['r%d' %(k+1)], nodes['r%d' %k], src_out_port=LINE_PORT1, dst_in_port=LINE_PORT2, boost_amp=boost,
             spans=spans)
        NETLINKS.append(('r%d' % (k+1), LINE_PORT1, 'r%d' % k, LINE_PORT2))

        if k == NUM_NODE-1:
            boost = net.add_amplifier('boost{}{}'.format(k+1, 1), target_gain=17 * dB, boost=True)
            spans = []
            for i, length in enumerate(lengths, start=1):
                amp = net.add_amplifier(
                    'amp{}{}{}'.format(k+1, 1, i), target_gain=length*0.22 * dB, monitor_mode='out')
                span = Span(length, amp=amp)
                spans.append(span)

            link(nodes['r%d' % (k+1)], nodes['r1'], src_out_port=LINE_PORT2, dst_in_port=LINE_PORT1,
                 boost_amp=boost,
                 spans=spans)
            NETLINKS.append(('r%d' % (k+1), LINE_PORT2, 'r%d' % 1, LINE_PORT1))

            # Westbound WAN link consisting of a boost amplifier going into
            # one or more segments of fiber with compensating amplifiers
            boost = net.add_amplifier('boost{}{}'.format(1, k+1), target_gain=17 * dB, boost=True)
            spans = []
            for i, length in enumerate(lengths, start=1):
                amp = net.add_amplifier(
                    'amp{}{}{}'.format(1, k+1, i), target_gain=length*0.22 * dB, monitor_mode='out')
                span = Span(length, amp=amp)
                spans.append(span)

            link(nodes['r%d' % (1)], nodes['r%d' % (k+1)], src_out_port=LINE_PORT1, dst_in_port=LINE_PORT2,
                 boost_amp=boost,
                 spans=spans)
            NETLINKS.append(('r%d' % 1, LINE_PORT1, 'r%d' % (k+1), LINE_PORT2))
        #"""

    for k in range(1,NUM_NODE+1):
        # Local add/drop links between terminals/transceivers and ROADMs
        for add_drop_port in range(NUM_WAV):
            link( nodes['t%d' %k], nodes['r%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )
            link( nodes['r%d' %k], nodes['t%d' %k], src_out_port=add_drop_port, dst_in_port=add_drop_port, spans=[Span(1*m)] )

            NETLINKS.append(('t%d' %k, add_drop_port, 'r%d' %k, add_drop_port))
            NETLINKS.append(('r%d' %k, add_drop_port, 't%d' %k, add_drop_port))

    return net


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


def FindRoute( src, graph, destinations ):
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


def setupLightpath(event, routes, graph, nodes):

    src = event.src
    dst = event.dst
    power = event.power
    path = routes[src,dst]
    channel = waveAssignment(path)
    count = 1
    while not channel and count<3:
        print('**Reroute')
        channel = waveAssignment(path, k=count)
        count += 1
    if not channel:
        return False
    installPath( path, [channel], graph, nodes)
    configTerminalChannelPower(terminal=nodes['t1'], channel=channel, power=power)
    voaPowerLeveling(path=path, channel=channel, power=-2, graph=graph, nodes=nodes)
    configTerminalChannel(terminal=nodes[path[0]], channel=channel)
    return True


def teardownLightpath(event, nodes):

    lightpath_id = event.dst
    uninstallPath(lightpath_id, nodes)
    return True


def waveAssignment(path, k=0):

    return 1

def installPath( path, channels, graph, nodes):
    "intall switch rules on roadms along a lightpath for some signal channels"

    global LIGHTPATH_ID
    # Install ROADM rules
    for channel in channels:
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
            Traffics[LIGHTPATH_ID]['path'], Traffics[LIGHTPATH_ID]['signal'], Traffics[LIGHTPATH_ID]['rule_path'] = path, channel, rule_path
        LIGHTPATH_ID += 1


def uninstallPath( lightpath_id, nodes):
    "delete switch rules on roadms along a lightpath for some signal channels"

    path = Traffics[lightpath_id]['path']
    rule_path = Traffics[lightpath_id]['rule_path']
    channel = Traffics[lightpath_id]['signal']
    for i in range(1, len(path) - 1):
        roadm = path[i]
        nodes[roadm].delete_switch_rule(rule_path[roadm])
    turnoffTerminalChannel(terminal = nodes[path[0]], channel = channel)
    del Traffics[lightpath_id]


def voaPowerLeveling(path, channel, power, graph, nodes):
    "Power control for a signal channel at a roadm using VOA leveling"

    for i in range(1, len(path) - 1):
        node1, roadm, node2 = path[i - 1], path[i], path[i + 1]
        if i == len(path) - 2:
            nodes[roadm].configure_voa(channel_id=channel, output_port=channel - 1, operational_power_dB=power)
        else:
            nodes[roadm].configure_voa(channel_id=channel, output_port=graph[node2][roadm], operational_power_dB=power)


def configTerminalChannelPower(terminal, channel, power):
    "Congifure Terminal Launch power for a channel"

    terminal.name_to_transceivers['tx%d'% channel].operation_power = db_to_abs(power)


def configTerminalChannel(terminal, channel):
    "Turn on a Terminal with a given channel"

    terminal.configure_terminal(transceiver=terminal.transceivers[channel-1], channel=channel)
    terminal.turn_on()


def turnoffTerminalChannel(terminal, channel):
    "Turn on a Terminal with a given channel"

    terminal.turn_off([channel-1])


def monitorAll(node):
    "monitoring all data at a node"

    return node.monitor.get_dict_power(),node.monitor.get_dict_osnr(), node.monitor.get_dict_gosnr()


def monitorLightpath(path, channel, nodes):
    "monitoring a signal along a lightpath"

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

# Physical model test

def RoadmPhyTest():
    # ROADM port numbers (input and output)
    LINE_PORT1 = NUM_WAV
    LINE_PORT2 = NUM_WAV+1

    "Create a single link and monitor its OSNR and gOSNR"
    net = RoadmPhyNetwork(lengths=[30 * km])
    AllLinks = getLinks()
    Graph = netGraph(AllLinks['links'])
    nodes = net.name_to_node
    routes = {node: FindRoute(node, Graph, name_terminals)
              for node in name_terminals}
    print('===links', AllLinks['links'])
    print('===graph', Graph)
    print('==route', routes)

    # Configure ROADMS switch rule
    lauch_p = {}
    for i in range(1,NUM_WAV+2):
        lauch_p[i]= random.randint(-3,3)
        lauch_p[i] = 0

    channels = []
    for j in range(1,NUM_WAV):
        channels.append([m for m in range(j,j+1)])
    # left, right = 0, 1
    # for k in range(20):
    #     if right >= NUM_WAV:
    #         channels.append(range(left,NUM_WAV))
    #         break
    #     left = right
    #     right = random.randint(left+1, NUM_WAV)
    #     print((left,right))
    #     channels.append(range(left,right))
    paths = {}
    start, end = 1, 3
    routes['t1']['t3'] = ('t1', 'r1', 'r4', 'r3', 't3')
    #random.seed(1000)
    for chs in channels:
        #chs = [i for i in range(1,50)]
        src = 't%s' %start#random.choice(name_terminals)
        dst = 't%s' %end #random.choice(name_terminals)
        start += 1
        end += 1
        if start == 5:
            start = 1
        if end == 5:
            end = 1
        while dst == src:
            dst = random.choice(name_terminals)
        path = routes[src][dst]
        print('===path, wav===', path, chs)
        installPath(path, chs, Graph, nodes)

        for ch in chs:
            paths[ch] = path
            configTerminalChannelPower(terminal=nodes[src], channel=ch, power=lauch_p[ch])
            voaPowerLeveling(path=path, channel=ch, power=lauch_p[ch], graph=Graph, nodes=nodes)
            configTerminalChannel(terminal=nodes[path[0]], channel=ch)

    """chs = [i for i in range(1,10)]
    src, dst = 't1', 't3'
    path1 = routes[src][dst]
    installPath(path1, chs, Graph, nodes)
    print('===Traffics===', Traffics.items())
    print('===path===', path1)
    for ch in chs:
        configTerminalChannelPower(terminal=nodes[src], channel=ch, power=lauch_p[ch])
        voaPowerLeveling(path= path1, channel=ch, power=lauch_p[ch], graph=Graph, nodes=nodes)
        configTerminalChannel(terminal =nodes[path1[0]], channel = ch)
    #"""

    """chs = [i for i in range(10, 20)]
    src, dst = 't1', 't3'
    path2 = routes[src][dst]
    installPath(path2, chs, Graph, nodes)
    print('===Traffics===', Traffics.items())
    print('===path===', path2)
    for ch in chs:
        configTerminalChannelPower(terminal=nodes[src], channel=ch, power=lauch_p[ch])
        voaPowerLeveling(path=path2, channel=ch, power=lauch_p[ch], graph=Graph, nodes=nodes)
        configTerminalChannel(terminal=nodes[path2[0]], channel=ch)
    #"""

    """chs = [i for i in range(20, 30)]
    src, dst = 't1', 't3'
    path3 = routes[src][dst]
    installPath(path3, chs, Graph, nodes)
    print('===Traffics===', Traffics.items())
    print('===path===', path3)
    for ch in chs:
        configTerminalChannelPower(terminal=nodes[src], channel=ch, power=lauch_p[ch])
        voaPowerLeveling(path=path3, channel=ch, power=lauch_p[ch], graph=Graph, nodes=nodes)
        configTerminalChannel(terminal=nodes[path3[0]], channel=ch)
    #"""

    """# test teardown paths
    uninstallPath(lightpath_id=1, nodes=nodes)
    uninstallPath(lightpath_id=5, nodes=nodes)
    uninstallPath(lightpath_id=9, nodes=nodes)
    #"""

    """print( '*** Initial OSNR and gOSNR:' )
    monitors = [ monitorAll(nodes[node]) for node in NAME_ROADM]
    for mon in monitors:
        print( 'monitor:', mon )
        print( 'OSNR', mon[1], '\n', 'gOSNR', mon[2], '\n', 'power', mon[0])
    #"""

    low_v = []
    for ch in range(1, NUM_WAV):
        powers,osnrs,gosnrs,ase,nli = monitorLightpath(path=paths[ch], channel=ch, nodes=nodes)
        if gosnrs[-1]<25:
            low_v.append((ch,paths[ch],osnrs,gosnrs))
        print('channel', ch, 'path', paths[ch], 'power', powers, 'osnr', osnrs, 'ase', ase, 'nli', nli, 'gosnr', gosnrs)
    for i in range(len(low_v)):
        print(low_v[i])
    #"""

    """for ch in range(10, 20):
        powers,osnrs,gosnrs,ase,nli = monitorLightpath(path=path2, channel=ch, nodes=nodes)
        print('channel', ch, 'path', path2, 'power', powers, 'osnr', osnrs, 'ase', ase, 'nli', nli, 'gosnr', gosnrs)
    #"""

    """for ch in range(20, 30):
        powers,osnrs,gosnrs,ase,nli = monitorLightpath(path=path3, channel=ch, nodes=nodes)
        print('channel', ch, 'path', path3, 'power', powers, 'osnr', osnrs, 'ase', ase, 'nli', nli,  'gosnr', gosnrs)
    #"""


    #t1.turn_off([0])


if __name__ == '__main__':
    RoadmPhyTest()

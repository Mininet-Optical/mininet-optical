from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy, OFSwitchProxy, TerminalProxy,
                                    fetchNodes, fetchLinks, fetchPorts)
import numpy as np


# optionally: retrieve WDG seed to pass to EDFAs
# this seed is created with the wdg_seed.py script
# currently in my computer at utils/
with open('seeds/wdg_seed.txt', 'r') as f:
    lines = f.readlines()
wdg_seeds = []
for line in lines:
    wdg_seed = line.split(',')
    wdg_seed[-1] = wdg_seed[-1][:-1]
    wdg_seeds.append(wdg_seed)


def run(net):
    "Configure and monitor network with N=3 channels for each path"

    # Fetch nodes
    net.allNodes = fetchNodes(net)
    net.switches = sorted(node for node, cls in net.allNodes.items()
                          if cls == 'OVSSwitch')
    net.terminals = sorted(node for node, cls in net.allNodes.items()
                           if cls == 'Terminal')
    net.roadms = sorted(node for node, cls in net.allNodes.items()
                        if cls == 'ROADM')
    net.nodes = net.terminals + net.roadms

    # Assign POPs for convenience
    count = len(net.switches)
    net.pops = {node: i + 1
                for i in range(count)
                for node in (net.switches[i], net.terminals[i], net.roadms[i])}

    # Fetch links
    net.allLinks, net.roadmLinks, net.terminalLinks = fetchLinks(net)

    # Fetch ports
    net.ports = fetchPorts(net, net.roadms + net.terminals + net.switches)

    channel_no = 5
    install_paths(net.roadms, channel_no)

    configure_routers(net.switches)

    configure_terminals(net.terminals, channel_no)

    monitor(net)

    reset_terminals(net.terminals)
    clean_roadms(net.roadms)

    test_run = 0
    configure_amps(net, test_run)


def reset_terminals(terminals):
    t1, t5 = terminals[0], terminals[4]
    TerminalProxy(t1).reset()
    TerminalProxy(t5).reset()


def clean_roadms(roadms):
    for roadm in roadms:
        ROADMProxy(roadm).cleanme()


def configure_amps(net, tr):
    rip_func = wdg_seeds[tr]

    amps = amplifiers(15, 1, [])
    for (amp_name, ripple) in zip(amps, rip_func):
        params = dict(amp_name=amp_name, ripple=ripple)
        print('set_ripple', params)
        response = net.get('set_ripple', params=params)
        print(response)


def appending(n, i, j, amps):
    "Helper function of the helper function to get the names of amplifiers"
    if j == n:
        return amps

    if j == 0:
        name = 'r' + str(i) + '-' + 'r' + str(i + 1) + '-' + 'boost'
    else:
        name = 'r' + str(i) + '-' + 'r' + str(i + 1) + '-' + 'amp' + str(j)
    amps.append(name)
    return appending(7, i, j+1, amps)


def amplifiers(n, i, amps):
    "Helper function to get the names of the amplifiers in linear topology"
    if i == n:
        return amps
    amps = appending(7, i, 0, amps)
    return amplifiers(n, i+1, amps)



def install_paths(roadms, channel_no):
    channels = list(np.arange(1, channel_no + 1))
    # Configure roadms
    r1, r2, r3, r4, r5 = roadms[0], roadms[1], roadms[2], roadms[3], roadms[4]
    line1, line2 = channel_no + 1, channel_no + 2

    # r1: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy(r1).connect(port1=local_port, port2=line1, channels=[ch])

    # r2: pass through channels r1<->r5
    ROADMProxy(r2).connect(port1=line1, port2=line2, channels=channels)

    # r3: pass through channels r1<->r5
    ROADMProxy(r3).connect(port1=line1, port2=line2, channels=channels)

    # r4: pass through channels r1<->r5
    ROADMProxy(r4).connect(port1=line1, port2=line2, channels=channels)

    # r5: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy(r5).connect(port1=line1, port2=local_port, channels=[ch])


def configure_routers(routers):
    "Configure Open vSwitch 'routers' using OpenFlow"

    def subnet(pop):
        return '10.%d.0.0/24' % pop

    print("*** Configuring Open vSwitch 'routers' remotely... ")

    routers = s1, s5 = routers[0], routers[4]
    for pop, dests in enumerate([(s1, s5)], start=1):
        router, dest1, dest2 = routers[pop - 1], dests[0], dests[1]
        routerProxy = OFSwitchProxy(router)
        # Initialize flow table
        print('Configuring', router, 'at', routerProxy.remote, 'via OpenFlow...')
        routerProxy.dpctl('del-flows')
        # XXX Only one host for now
        j = 1
        for eth, dest in enumerate([dest1, dest2, router], start=1):
            for protocol in 'ip', 'icmp', 'arp':
                flow = (protocol + ',ip_dst=' + subnet(j) +
                        ',actions=dec_ttl,output:%d' % eth)
                routerProxy.dpctl('add-flow', flow)
                j += 1


def configure_terminals(terminals, channel_no):
    channels = list(np.arange(1, channel_no + 1))
    # Port numbering
    eth_ports = list(np.arange(1, channel_no + 2))
    wdm_ports = list(np.arange(channel_no + 1, channel_no * 2 + 1))

    # Configure transceivers
    t1, t5 = terminals[0], terminals[4]
    termProxy1 = TerminalProxy(t1)
    termProxy5 = TerminalProxy(t5)
    for tx_id, ch in enumerate(channels):
        termProxy1.connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)
    for tx_id, ch in enumerate(channels):
        termProxy5.connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)


def monitorKey(monitor):
    "Key for sorting monitor names"
    items = monitor.split('-')
    return items


def monitor_osnr(net):
    monitors = net.get('monitors').json()['monitors']
    mon_keys = simple_keys([], 1, 2, len(net.roadms))
    ptl_monitor_keys = []
    for k in mon_keys:
        for k2 in monitors.keys():
            if k in k2:
                ptl_monitor_keys.append(k2)
    ptl_monitors = {}
    for k in ptl_monitor_keys:
        ptl_monitors[k] = monitors[k]

    gosnrs = []
    for monitor in sorted(ptl_monitors, key=monitorKey):
        response = net.get('monitor', params=dict(monitor=monitor))
        osnrdata = response.json()['osnr']

        print(monitor)
        i = 0
        for channel, data in osnrdata.items():
            THz = float(data['freq']) / 1e12
            osnr, gosnr = data['osnr'], data['gosnr']
            if i == 1:
                gosnrs.append(gosnr)
            i += 1
            # print("OSNR for channel %s is %s" % (str(THz), str(osnr)))
            # print("gOSNR for channel %s is %s" % (str(THz), str(gosnr)))
            # print()
    print(gosnrs)


def monitor(net):
    monitor_keys = [
        'r1-r2-boost', 'r1-r2-amp1-monitor', 'r1-r2-amp2-monitor', 'r1-r2-amp3-monitor',
        'r2-r3-boost', 'r2-r3-amp1-monitor', 'r2-r3-amp2-monitor', 'r2-r3-amp3-monitor',
        'r3-r4-boost', 'r3-r4-amp1-monitor', 'r3-r4-amp2-monitor', 'r3-r4-amp3-monitor',
        'r4-r5-boost', 'r4-r5-amp1-monitor', 'r4-r5-amp2-monitor', 'r4-r5-amp3-monitor',
    ]

    gosnrs = []
    for key in monitor_keys:
        response = net.get('monitor', params=dict(monitor=key))
        osnrdata = response.json()['osnr']
        i = 0
        for channel, data in osnrdata.items():
            osnr, gosnr = data['osnr'], data['gosnr']
            if i == 1:
                gosnrs.append(gosnr)
            i += 1
    print(gosnrs)


def simple_keys(mon_keys, i, j, N):
    if j is N + 1:
        return mon_keys
    k1, k2 = 'r' + str(i) + '-', 'r' + str(j)
    mon_keys.append(k1 + k2)
    i = j
    j = i + 1
    return simple_keys(mon_keys, i, j, N)


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy, OFSwitchProxy, TerminalProxy,
                                    fetchNodes, fetchLinks, fetchPorts)
import numpy as np
import os
import json
import subprocess


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

    configure_routers(net.switches)

    test_run = 0
    test_num = 1
    _loads = [81, 27, 9]
    for load in _loads:
        while test_run < test_num:

            install_paths(net.roadms, load)

            configure_amps(net, 15, test_run)
            configure_terminals(net.terminals, load)
            monitor(net, str(test_run), str(load))

            reset_terminals(net.terminals)
            clean_roadms(net.roadms)

            test_run += 1


def reset_terminals(terminals):
    t1, t15 = terminals[0], terminals[14]
    TerminalProxy(t1).reset()
    TerminalProxy(t15).reset()


def clean_roadms(roadms):
    for roadm in roadms:
        ROADMProxy(roadm).cleanme()


def configure_amps(net, roadm_no, tr):
    rip_func = wdg_seeds[tr]

    amps = amplifiers(roadm_no, 1, [])
    for (amp_name, ripple) in zip(amps, rip_func):
        params = dict(amp_name=amp_name, ripple=ripple)
        print('set_ripple', params)
        response = net.get('set_ripple', params=params)
        print(response)


def appending(n, i, j, amps):
    """
        Helper function of the helper function to get the names of amplifiers
        n : number of spans
        i: node num
        j: node num + 1
        amps: list of amps
    """
    if j == n:
        return amps

    if j == 0:
        name = 'r' + str(i) + '-' + 'r' + str(i + 1) + '-' + 'boost'
    else:
        name = 'r' + str(i) + '-' + 'r' + str(i + 1) + '-' + 'amp' + str(j)
    amps.append(name)
    return appending(7, i, j+1, amps)


def amplifiers(n, i, amps):
    """
        Helper function to get the names of the amplifiers in linear topology
        n: number of roadms
        i: node num
        amps: list of amps
    """
    if i == n:
        return amps
    amps = appending(7, i, 0, amps)
    return amplifiers(n, i+1, amps)


def install_paths(roadms, channel_no):
    channels = list(np.arange(1, channel_no + 1))
    # Configure roadms
    r1, r15 = roadms[0], roadms[-1]
    line1, line2 = channel_no + 1, channel_no + 2

    # r1: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy(r1).connect(port1=local_port, port2=line1, channels=[ch])

    for roadm in roadms[1:14]:
        # next roadms: pass through channels r1<->r15
        ROADMProxy(roadm).connect(port1=line1, port2=line2, channels=channels)

    # r15: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy(r15).connect(port1=line1, port2=local_port, channels=[ch])


def configure_routers(routers):
    "Configure Open vSwitch 'routers' using OpenFlow"

    def subnet(pop):
        return '10.%d.0.0/24' % pop

    print("*** Configuring Open vSwitch 'routers' remotely... ")

    routers = s1, s15 = routers[0], routers[14]
    for pop, dests in enumerate([(s1, s15)], start=1):
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
    t1, t15 = terminals[0], terminals[14]
    termProxy1 = TerminalProxy(t1)
    termProxy15 = TerminalProxy(t15)
    for tx_id, ch in enumerate(channels):
        termProxy1.connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)
    for tx_id, ch in enumerate(channels):
        termProxy15.connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)


def monitor(net, test_id, load_id):
    monitor_keys = [
        'r1-r2-boost', 'r1-r2-amp1-monitor', 'r1-r2-amp2-monitor', 'r1-r2-amp3-monitor',
        'r2-r3-boost', 'r2-r3-amp1-monitor', 'r2-r3-amp2-monitor', 'r2-r3-amp3-monitor',
        'r3-r4-boost', 'r3-r4-amp1-monitor', 'r3-r4-amp2-monitor', 'r3-r4-amp3-monitor',
        'r4-r5-boost', 'r4-r5-amp1-monitor', 'r4-r5-amp2-monitor', 'r4-r5-amp3-monitor',
    ]

    for monitor_key in monitor_keys:
        json_struct = {'tests': []}
        response = net.get('monitor', params=dict(monitor=monitor_key))
        osnrdata = response.json()['osnr']

        osnrs, gosnrs = [], []
        for channel, data in osnrdata.items():
            osnr, gosnr = data['osnr'], data['gosnr']
            osnrs.append(osnr)
            gosnrs.append(gosnr)
        write_files(osnrs, gosnrs, json_struct, load_id, monitor_key, test_id)


def write_files(osnr, gosnr, json_struct, load_id, monitor_key, test_id):
    _osnr_id = 'osnr_load_' + load_id
    _gosnr_id = 'gosnr_load_' + load_id
    json_struct['tests'].append({_osnr_id: osnr})
    json_struct['tests'].append({_gosnr_id: gosnr})

    test = 'metrics-monitor/'
    dir_ = test + 'opm-sim-no-m/' + monitor_key
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    json_file_name = dir_ + '/' + test_id + '_' + str(load_id) + '.json'
    with open(json_file_name, 'w+') as outfile:
        json.dump(json_struct, outfile)
    process_file(json_file_name, monitor_key)


def process_file(outfile, monitor_key):
    # send file to flash drive
    print("processing file")
    print(outfile)
    cmd1 = ['rsync', '-r', outfile, 'adiaz@192.168.56.1:/Volumes/LEXAR/opm-sim-no-m/' + monitor_key + '/']
    # delete file
    cmd2 = ['rm', outfile]
    subprocess.call(cmd1)
    subprocess.call(cmd2)


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

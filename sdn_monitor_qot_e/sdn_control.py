"""

sdn_control.py: script to replicate PTL 2020 data collection.

The data collection process consists in:
1) Deploy a linear 15 x ROADM network connected by 6 x 80km.
    Each span is optically compensated with an EDFA.
    At each ROADM we apply signal leveling.
    There is an OPM node at the output port of each EDFA.
2) Using 3 channel loads: 10%, 30% and 90%.
3) Using 2 channel loading strategies: sequential and random.
4) For each test case (load and strategy) we assign different
    (randomly allocated) ripple functions to all EDFAs.
5) After transmission, we collect OSNR and gOSNR data for all
    channels.

We repeat this for 150 tests.

This script extends functionality from the fakecontroller,
which is simply a mock-SDN-control API to manage a virtual
optical network created with Mininet Optical.

"""


from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy,
                                    OFSwitchProxy, TerminalProxy,
                                    fetchNodes)
import numpy as np
import os
import json
import subprocess


# Optionally: retrieve WDG seed to pass to EDFAs.
# This seed is created with the wdg_seed.py script
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

    configure_routers(net.switches)

    test_num = 10
    _loads = [9, 27, 81]
    for load in _loads:
        test_run = 0
        while test_run < test_num:

            install_paths(load)
            configure_amps(net, 15, test_run)
            term_out_ports = configure_terminals(load)

            transmit(term_out_ports)
            monitor(net, str(test_run), str(load))

            reset_terminals()
            clean_roadms(net.roadms)

            test_run += 1


def transmit(out_ports):
    """
    Turn on the channels of a line terminal for all outports.
    Connection is configured with configure_terminals().
    """
    TerminalProxy('t1').turn_on(out_ports)
    # FIXME: AD: There is a problem with this out_ports
    # need to check the correct ones, otherwise
    # it loops forever, triggering a recursion error.
    # TerminalProxy('t15').turn_on(out_ports)


def reset_terminals():
    """
    Reset the structures handling the signals
    within the line terminals.
    """
    TerminalProxy('t1').reset()
    TerminalProxy('t15').reset()


def clean_roadms(roadms):
    """
    Reset the structures handling the signals
    within the roadms.
    """
    for roadm in roadms:
        ROADMProxy(roadm).cleanme()


def configure_amps(net, roadm_no, tr):
    """
    Assign ripple functions at run-time
    to all amplifiers
    """
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


def install_paths(channel_no):
    """
    Create switching table for the roadms
    """
    channels = list(np.arange(1, channel_no + 1))
    # Configure roadms
    line1, line2 = 82, 83
    # line1, line2 = 10, 11

    # r1: add/drop channels r1<->r5
    for local_port, ch in enumerate(channels, start=1):
        ROADMProxy('r1').connect(port1=local_port, port2=line1, channels=[ch])

    roadm_list = ['r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14']
    for roadm in roadm_list:
        # next roadms: pass through channels r1<->r15
        ROADMProxy(roadm).connect(port1=line1, port2=line2, channels=channels)

    # r15: add/drop channels r1<->r5
    # for local_port, ch in enumerate(channels, start=1):
    #     ROADMProxy('r15').connect(port1=line1, port2=local_port, channels=[ch])


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


def configure_terminals(channel_no):
    """
    Configure the transceivers from the terminals.
    """
    channels = list(np.arange(1, channel_no + 1))
    # Port numbering
    eth_ports = list(np.arange(1, channel_no + 2))
    wdm_ports = list(np.arange(82, 82 + channel_no))
    # wdm_ports = list(np.arange(10, 10 + channel_no))

    # Configure transceivers
    for tx_id, ch in enumerate(channels):
        TerminalProxy('t1').connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)
    # for tx_id, ch in enumerate(channels):
    #     TerminalProxy('t15').connect(ethPort=eth_ports[tx_id], wdmPort=wdm_ports[tx_id], channel=ch)

    return wdm_ports


def monitor(net, test_id, load_id):
    """
    Monitor the osnr and gosnr at each OPM location,
    then write a file with these values
    """
    monitor_keys = [
        'r1-r2-boost', 'r1-r2-amp1-monitor', 'r1-r2-amp2-monitor', 'r1-r2-amp3-monitor',
        'r2-r3-boost', 'r2-r3-amp1-monitor', 'r2-r3-amp2-monitor', 'r2-r3-amp3-monitor',
        'r3-r4-boost', 'r3-r4-amp1-monitor', 'r3-r4-amp2-monitor', 'r3-r4-amp3-monitor',
        'r4-r5-boost', 'r4-r5-amp1-monitor', 'r4-r5-amp2-monitor', 'r4-r5-amp3-monitor',
    ]

    for monitor_key in monitor_keys:
        json_struct = {'tests': []}
        print('monitor', dict(monitor=monitor_key))
        response = net.get('monitor', params=dict(monitor=monitor_key))
        osnrdata = response.json()['osnr']

        osnrs, gosnrs = [], []
        for channel, data in osnrdata.items():
            osnr, gosnr = data['osnr'], data['gosnr']
            osnrs.append(osnr)
            gosnrs.append(gosnr)
        write_files(osnrs, gosnrs, json_struct, load_id, monitor_key, test_id)


def write_files(osnr, gosnr, json_struct, load_id, monitor_key, test_id):
    """
    Write a file with osnr and gosnr information from a given OPM node
    """
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
    """
    To avoid memory exhaustion in VM, transfer recently created
    file to a remote location (flash drive) and remove them
    from local (VM).
    """
    # send file to flash drive
    print("processing file: ", outfile)
    dest_file = 'adiaz@192.168.56.1:/Volumes/LEXAR/opm-sim-no-m/' + monitor_key + '/'
    cmd1 = ['rsync', '-r', outfile, dest_file]
    # delete file
    cmd2 = ['rm', outfile]
    subprocess.call(cmd1)
    subprocess.call(cmd2)


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

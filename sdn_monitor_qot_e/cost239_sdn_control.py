from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy,
                                    OFSwitchProxy, TerminalProxy,
                                    fetchNodes, fetchPorts)
import os
import json


def run(net):
    """Configure and monitor network with N=3 channels for each path"""

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

    # Fetch ports
    net.ports = fetchPorts(net, net.roadms + net.terminals + net.switches)

    install_paths()

    configure_terminals()

    transmit()

    monitor(net)


def monitor(net):
    monitors = net.get('monitors').json()['monitors']
    for monitor, desc in monitors.items():
        osnr = net.get('monitor', params=dict(monitor=monitor))
        if bool(osnr.json()['osnr']):
            x = monitor.split('-', 2)
            link_label = x[0] + '-' + x[1]
            osnrs, gosnrs = {}, {}
            powers, ases, nlis = {}, {}, {}
            for channel, data in osnr.json()['osnr'].items():
                osnr, gosnr = data['osnr'], data['gosnr']
                power, ase, nli = data['power'], data['ase'], data['nli']
                osnrs[channel] = osnr
                gosnrs[channel] = gosnr
                powers[channel] = power
                ases[channel] = ase
                nlis[channel] = nli

            json_struct = {'tests': []}

            write_files(monitor, osnrs, gosnrs, powers, ases, nlis, json_struct, link_label)


def write_files(monitor, osnrs, gosnrs,
                powers, ases, nlis, json_struct,
                link_label):
    _osnr_id = 'osnr'
    _gosnr_id = 'gosnr'
    _power_id = 'power'
    _ase_id = 'ase'
    _nli_id = 'nli'

    json_struct['tests'].append({_osnr_id: osnrs})
    json_struct['tests'].append({_gosnr_id: gosnrs})
    json_struct['tests'].append({_power_id: powers})
    json_struct['tests'].append({_ase_id: ases})
    json_struct['tests'].append({_nli_id: nlis})

    test = 'cost239-monitor/monitor-module-new-emulation/'

    dir_ = test + link_label + '/'
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    json_file_name = dir_ + monitor + '.json'
    with open(json_file_name, 'w+') as outfile:
        print("*** writing file: %s" % json_file_name)
        json.dump(json_struct, outfile)


def install_paths():
    # retrieve the network elements to use
    # for this test from the network
    ber = 'r2'
    cph = 'r4'
    ldn = 'r5'
    par = 'r8'
    pra = 'r9'
    vie = 'r10'

    # First transmission from London to Berlin
    # passing through Copenhagen
    channels_list = range(1, 16)

    line1 = 33
    # ldn to cph (r5 --> r4)
    for local_port, ch in enumerate(channels_list, start=1):
        ROADMProxy('r5').connect(port1=local_port, port2=line1, channels=[ch], op=0)

    line2 = 32
    # cph to ber (r4 --> r2)
    ROADMProxy('r4').connect(port1=line1, port2=line2, channels=channels_list, op=0)

    # ber to lt_berX (r2 --> localX)
    for local_port, ch in enumerate(channels_list, start=1):
        ROADMProxy('r2').connect(port1=line2, port2=local_port, channels=[ch], op=0)


    # Second transmission from Paris to Berlin
    channels_list = range(16, 31)
    line1 = 31
    # par to ber (r8 --> r2)
    for _, ch in enumerate(channels_list, start=1):
        ROADMProxy('r8').connect(port1=ch, port2=line1, channels=[ch], op=0)

        # ber to lt_berX (r2 --> localX)
        for _, ch in enumerate(channels_list, start=1):
            ROADMProxy('r2').connect(port1=33, port2=ch, channels=[ch], op=0)

def configure_terminals():
    # First transmission from London to Berlin
    # passing through Copenhagen
    channels_list = range(1, 16)
    # ldn: t5
    for eth_port, ch in enumerate(channels_list, start=1):
        wdm_port = 30 + eth_port
        TerminalProxy('t5').connect(ethPort=eth_port, wdmPort=wdm_port, channel=ch)

    # Second transmission from Paris to Berlin
    channels_list = range(16, 31)
    # ldn: t5
    for _, ch in enumerate(channels_list, start=1):
        wdm_port = 30 + ch
        TerminalProxy('t8').connect(ethPort=ch, wdmPort=wdm_port, channel=ch)

def transmit():
    TerminalProxy('t5').turn_on()
    TerminalProxy('t8').turn_on()


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

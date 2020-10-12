"""
This is a helper script to check fast and easy
performance of the physical models.

"""


from topo.linear import LinearTopology
from estimation_module import *
import numpy as np
import os
from operator import attrgetter
import json
import matplotlib.pyplot as plt


def db_to_abs(db_value):
    """
    :param db_value: list or float
    :return: Convert dB to absolute value
    """
    absolute_value = 10**(db_value/float(10))
    return absolute_value


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10*np.log10(absolute_value)
    return db_value


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
    lt_1 = net.name_to_node['lt_1']

    test_num = 10
    _loads = [9, 27, 81]
    for load in _loads:
        print("Processing load", load)
        estimation_module(load, str(load), str(0))
        test_run = 1
        while test_run < test_num:
            print("Running test no. ", test_run)

            configure_amps(net, 15, test_run)

            configure_terminal(lt_1, load)

            configure_roadms(net, load)

            transmit(lt_1)

            monitor(net, str(test_run), str(load))

            reset_terminal(lt_1)

            clean_roadms()

            test_run += 1


def configure_amps(net, roadm_no, tr):
    """
    Assign ripple functions at run-time
    to all amplifiers
    """
    rip_func = wdg_seeds[tr]

    amps = amplifiers(roadm_no, 1, [])
    for (amp_name, ripple) in zip(amps, rip_func):
        amp = net.name_to_node[amp_name]
        amp.set_ripple_function(ripple)


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


def configure_terminal(term, channel_no, signal_ids=None):
    """
    Configure the transceivers from the terminals.
    """
    if signal_ids:
        channels = signal_ids
    else:
        channels = list(np.arange(1, channel_no + 1))

    transceivers = term.transceivers
    out_port = 100
    # transceiver, out_port, channels
    for i, ch in enumerate(channels):
        t = transceivers[i]
        term.configure_terminal(t, out_port, [ch])


def configure_roadms(net, channel_no):
    channels = list(np.arange(1, channel_no + 1))

    for i in range(1, 16):
        roadm = net.name_to_node['r' + str(i)]

        if i == 1:
            roadm.install_switch_rule(1, 0, 101, channels)
        elif i == 15:
            roadm.install_switch_rule(1, 1, 100, channels)
        else:
            roadm.install_switch_rule(1, 1, 102, channels)


def transmit(term):
    out_port = [100]
    term.turn_on(out_port)


def reset_terminal(term):
    term.reset()


def clean_roadms():
    for i in range(1, 16):
        roadm = net.name_to_node['r' + str(i)]
        roadm.clean()


def plot_monitor(net):
    print("*** Monitoring interfaces")
    # Retrieve number of amplifiers (or monitoring nodes)
    num_amplifiers = int((len(net.amplifiers) / 2) + 1)
    osnrs = {i: [] for i in range(1, num_amplifiers)}
    gosnrs = {i: [] for i in range(1, num_amplifiers)}

    # Retrieve from each monitoring points the
    # OSNR and gOSNR of all the channels
    opm_name_base = 'opm_'
    cut = 0
    plotting_osnr = []
    plotting_gosnr = []
    for key, _ in osnrs.items():
        opm_name = opm_name_base + str(key)
        opm = net.name_to_node[opm_name]
        osnrs[key] = opm.get_list_osnr()
        gosnrs[key] = opm.get_list_gosnr()

    # Retrieve only the channels of interest
    osnr_cut = []
    for opm, _list in osnrs.items():
        osnr_cut.append(_list[cut])
    plotting_osnr.append(osnr_cut)

    gosnr_cut = []
    for opm, _list in gosnrs.items():
        gosnr_cut.append(_list[cut])
    plotting_gosnr.append(gosnr_cut)

    for o, g in zip(plotting_osnr, plotting_gosnr):
        plt.plot(o, color='g', label='OSNR')
        plt.plot(g, 'b', label='gOSNR')
    plt.legend()
    plt.yticks(np.arange(12.5, 35, 0.5))
    plt.xlabel('amplifier number')
    plt.ylabel('OSNR and gOSNR [dB]')
    plt.grid(True)
    plt.show()


def monitor(net, test_id, load_id):
    """
    Monitor the osnr and gosnr at each OPM location,
    then write a file with these values.
    Return gosnr for all OPM nodes to be used by the
    QoT-E module.
    """
    monitor_keys = [
        'r1-r2-boost-monitor', 'r1-r2-amp1-monitor', 'r1-r2-amp2-monitor', 'r1-r2-amp3-monitor', 'r1-r2-amp4-monitor',
        'r1-r2-amp5-monitor', 'r1-r2-amp6-monitor', 'r2-r3-boost-monitor', 'r2-r3-amp1-monitor', 'r2-r3-amp2-monitor',
        'r2-r3-amp3-monitor', 'r2-r3-amp4-monitor', 'r2-r3-amp5-monitor', 'r2-r3-amp6-monitor', 'r3-r4-boost-monitor',
        'r3-r4-amp1-monitor', 'r3-r4-amp2-monitor', 'r3-r4-amp3-monitor', 'r3-r4-amp4-monitor', 'r3-r4-amp5-monitor',
        'r3-r4-amp6-monitor', 'r4-r5-boost-monitor', 'r4-r5-amp1-monitor', 'r4-r5-amp2-monitor', 'r4-r5-amp3-monitor',
        'r4-r5-amp4-monitor', 'r4-r5-amp5-monitor', 'r4-r5-amp6-monitor', 'r5-r6-boost-monitor', 'r5-r6-amp1-monitor',
        'r5-r6-amp2-monitor', 'r5-r6-amp3-monitor', 'r5-r6-amp4-monitor', 'r5-r6-amp5-monitor', 'r5-r6-amp6-monitor',
        'r6-r7-boost-monitor', 'r6-r7-amp1-monitor', 'r6-r7-amp2-monitor', 'r6-r7-amp3-monitor', 'r6-r7-amp4-monitor',
        'r6-r7-amp5-monitor', 'r6-r7-amp6-monitor', 'r7-r8-boost-monitor', 'r7-r8-amp1-monitor', 'r7-r8-amp2-monitor',
        'r7-r8-amp3-monitor', 'r7-r8-amp4-monitor', 'r7-r8-amp5-monitor', 'r7-r8-amp6-monitor', 'r8-r9-boost-monitor',
        'r8-r9-amp1-monitor', 'r8-r9-amp2-monitor', 'r8-r9-amp3-monitor', 'r8-r9-amp4-monitor', 'r8-r9-amp5-monitor',
        'r8-r9-amp6-monitor', 'r9-r10-boost-monitor', 'r9-r10-amp1-monitor', 'r9-r10-amp2-monitor', 'r9-r10-amp3-monitor',
        'r9-r10-amp4-monitor', 'r9-r10-amp5-monitor', 'r9-r10-amp6-monitor', 'r10-r11-boost-monitor', 'r10-r11-amp1-monitor',
        'r10-r11-amp2-monitor', 'r10-r11-amp3-monitor', 'r10-r11-amp4-monitor', 'r10-r11-amp5-monitor',
        'r10-r11-amp6-monitor', 'r11-r12-boost-monitor', 'r11-r12-amp1-monitor', 'r11-r12-amp2-monitor',
        'r11-r12-amp3-monitor', 'r11-r12-amp4-monitor', 'r11-r12-amp5-monitor', 'r11-r12-amp6-monitor',
        'r12-r13-boost-monitor', 'r12-r13-amp1-monitor', 'r12-r13-amp2-monitor', 'r12-r13-amp3-monitor',
        'r12-r13-amp4-monitor', 'r12-r13-amp5-monitor', 'r12-r13-amp6-monitor', 'r13-r14-boost-monitor',
        'r13-r14-amp1-monitor', 'r13-r14-amp2-monitor', 'r13-r14-amp3-monitor', 'r13-r14-amp4-monitor',
        'r13-r14-amp5-monitor', 'r13-r14-amp6-monitor', 'r14-r15-boost-monitor', 'r14-r15-amp1-monitor',
        'r14-r15-amp2-monitor', 'r14-r15-amp3-monitor', 'r14-r15-amp4-monitor', 'r14-r15-amp5-monitor',
        'r14-r15-amp6-monitor'
    ]

    for monitor_key in monitor_keys:
        json_struct = {'tests': []}
        # print('monitor', dict(monitor=monitor_key))
        monitor = net.name_to_node[monitor_key]

        osnrdata = {int(signal.index):
                    dict(freq=signal.frequency, osnr=monitor.get_osnr(signal),
                         gosnr=monitor.get_gosnr(signal),
                         power=monitor.get_power(signal),
                         ase=monitor.get_ase_noise(signal),
                         nli=monitor.get_nli_noise(signal))
                for signal in sorted(monitor.amplifier.output_power,
                                     key=attrgetter('index'))}

        osnrs, gosnrs = {}, {}
        powers, ases, nlis = {}, {}, {}
        for channel, data in osnrdata.items():
            osnr, gosnr = data['osnr'], data['gosnr']
            power, ase, nli = data['power'], data['ase'], data['nli']
            osnrs[channel] = osnr
            gosnrs[channel] = gosnr
            powers[channel] = power
            ases[channel] = ase
            nlis[channel] = nli

        write_files(osnrs, gosnrs, powers, ases, nlis,
                    json_struct, load_id, monitor_key, test_id)


def write_files(osnr, gosnr, powers, ases, nlis,
                json_struct, load_id, monitor_key, test_id):
    """
    Write a file with osnr and gosnr information from a given OPM node
    """
    _osnr_id = 'osnr_load_' + load_id
    _gosnr_id = 'gosnr_load_' + load_id
    _power_id = 'power_load_' + load_id
    _ase_id = 'ase_load_' + load_id
    _nli_id = 'nli_load_' + load_id
    json_struct['tests'].append({_osnr_id: osnr})
    json_struct['tests'].append({_gosnr_id: gosnr})
    json_struct['tests'].append({_power_id: powers})
    json_struct['tests'].append({_ase_id: ases})
    json_struct['tests'].append({_nli_id: nlis})

    test = 'metrics-monitor/'
    dir_ = test + 'opm-all/' + monitor_key
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    json_file_name = dir_ + '/' + test_id + '_' + str(load_id) + '.json'
    with open(json_file_name, 'w+') as outfile:
        json.dump(json_struct, outfile)


if __name__ == '__main__':
    # simple_analysis()
    net = LinearTopology.build(op=0, non=15)
    run(net)

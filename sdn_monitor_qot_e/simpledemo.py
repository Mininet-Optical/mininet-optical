from topo.cost239 import Cost239Topology
import numpy as np
from operator import attrgetter
import os
import json


def run(net):
    configure_terminals(net)
    configure_roadms(net)
    transmit(net)
    monitor(net, density=10)


def configure_terminals(net):
    lt_london = net.name_to_node['lt_london']
    lt_paris = net.name_to_node['lt_paris']
    lt_prague = net.name_to_node['lt_prague']

    transceivers_ldn = lt_london.transceivers
    channels1 = range(1, 16)
    out_port = 100
    for i, ch in enumerate(channels1):
        t = transceivers_ldn[i]
        # transceiver, out_port, channels
        lt_london.configure_terminal(t, out_port, [ch])

    transceivers_par = lt_paris.transceivers
    channels2 = range(16, 31)
    for i, ch in enumerate(channels2):
        t = transceivers_par[i]
        # transceiver, out_port, channels
        lt_paris.configure_terminal(t, out_port, [ch])

    transceivers_pra = lt_prague.transceivers
    channels3 = range(31, 46)
    for i, ch in enumerate(channels3):
        t = transceivers_pra[i]
        # transceiver, out_port, channels
        lt_prague.configure_terminal(t, out_port, [ch])


def configure_roadms(net):
    """
    For this simple configuration, we're only using locations:
    ldn, cph, ber, par, pra and vie.
    The configuration corresponds to the installation of the
    following lightpaths:
    ldn -> cph -> ber (1400 km, 28 inline EDFAs + 2 boosters)
    par -> ber (900 km, 18 inline EDFAs + 1 booster)
    pra -> vie (350 km, 7 inline EDFAs + 1 booster)
    """
    ber = net.name_to_node['r_berlin']
    cph = net.name_to_node['r_copenhagen']
    ldn = net.name_to_node['r_london']
    par = net.name_to_node['r_paris']
    pra = net.name_to_node['r_prague']
    vie = net.name_to_node['r_vienna']

    channels1 = range(1, 16)
    # ldn to cph
    ldn.install_switch_rule(1, 0, 103, channels1)
    # cph to ber
    cph.install_switch_rule(1, 3, 102, channels1)
    ber.install_switch_rule(1, 2, 100, channels1)

    channels2 = range(16, 31)
    # par to ber
    par.install_switch_rule(1, 0, 101, channels2)
    ber.install_switch_rule(2, 3, 100, channels2)

    channels3 = range(31, 46)
    # pra to vie
    pra.install_switch_rule(1, 0, 105, channels3)
    vie.install_switch_rule(1, 3, 100, channels3)


def transmit(net):
    lt_london = net.name_to_node['lt_london']
    lt_paris = net.name_to_node['lt_paris']
    lt_prague = net.name_to_node['lt_prague']
    out_port = [100]

    lt_london.turn_on(out_port)
    lt_paris.turn_on(out_port)
    lt_prague.turn_on(out_port)


def monitor(net, density=10, first_last='first'):
    mon_ldn_cph = ['r_london-r_copenhagen-amp%s-monitor' % str(i) for i in range(1, 21)]
    mon_ldn_cph.insert(0, 'r_london-r_copenhagen-boost-monitor')
    mon_ldn_cph = monitor_deployment(mon_ldn_cph, density=density, first_last=first_last)
    for monitor_name in mon_ldn_cph:
        monitor_query(net, monitor_name)

    mon_cph_ber = ['r_copenhagen-r_berlin-amp%s-monitor' % str(i) for i in range(1, 9)]
    mon_cph_ber.insert(0, 'r_copenhagen-r_berlin-boost-monitor')
    mon_cph_ber = monitor_deployment(mon_cph_ber, density=density, first_last=first_last)
    for monitor_name in mon_cph_ber:
        monitor_query(net, monitor_name)

    mon_par_ber = ['r_paris-r_berlin-amp%s-monitor' % str(i) for i in range(1, 19)]
    mon_par_ber.insert(0, 'r_paris-r_berlin-boost-monitor')
    mon_par_ber = monitor_deployment(mon_par_ber, density=density, first_last=first_last)
    for monitor_name in mon_par_ber:
        monitor_query(net, monitor_name)

    mon_pra_vie = ['r_prague-r_vienna-amp%s-monitor' % str(i) for i in range(1, 8)]
    mon_pra_vie.insert(0, 'r_prague-r_vienna-boost-monitor')
    mon_pra_vie = monitor_deployment(mon_pra_vie, density=density, first_last=first_last)
    for monitor_name in mon_pra_vie:
        monitor_query(net, monitor_name)


def monitor_deployment(monitor_link, density=10, first_last='first'):
    if density == 100:
        return monitor_link

    monitor_no = int(len(monitor_link) * density*1e-2)
    monitors = []

    if monitor_no <= 1:
        if first_last == 'first':
            monitors.append(monitor_link[0])
        else:
            monitors.append(monitor_link[-1])
    else:
        monitors = monitor_select(monitor_link, monitor_no)
    return monitors


def monitor_select(monitor_link, monitor_no):
    n = len(monitor_link)
    indices = even_select(n, monitor_no)
    monitors = []
    for i, k in enumerate(indices):
        if k == 0:
            monitors.append(monitor_link[i])
    return monitors


def even_select(n, m):
    if m > n/2:
        cut = np.zeros(n, dtype=int)
        q, r = divmod(n, n-m)
        indices = [q*i + min(i, r) for i in range(n-m)]
        cut[indices] = True
    else:
        cut = np.ones(n, dtype=int)
        q, r = divmod(n, m)
        indices = [q*i + min(i, r) for i in range(m)]
        cut[indices] = False
    return cut


def monitor_query(net, monitor_name):
    x = monitor_name.split('-', 2)
    link_label = x[0] + '-' + x[1]
    monitor = net.name_to_node[monitor_name]

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

    json_struct = {'tests': []}
    write_files(osnrs, gosnrs, powers, ases, nlis,
                json_struct, link_label, monitor_name)


def write_files(osnr, gosnr, powers, ases, nlis,
                json_struct, link_label, monitor_name):
    """
    Write a file with osnr and gosnr information from a given OPM node
    """
    _osnr_id = 'osnr'
    _gosnr_id = 'gosnr'
    _power_id = 'power'
    _ase_id = 'ase'
    _nli_id = 'nli'
    json_struct['tests'].append({_osnr_id: osnr})
    json_struct['tests'].append({_gosnr_id: gosnr})
    json_struct['tests'].append({_power_id: powers})
    json_struct['tests'].append({_ase_id: ases})
    json_struct['tests'].append({_nli_id: nlis})

    test = 'cost239-monitor/'
    dir_ = test + link_label + '/'
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    json_file_name = dir_ + monitor_name + '.json'
    with open(json_file_name, 'w+') as outfile:
        json.dump(json_struct, outfile)


if __name__ == '__main__':
    net = Cost239Topology.build()
    run(net)

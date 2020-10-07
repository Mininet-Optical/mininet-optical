"""
    This script is a simple demo to test:
     - deployment of the Cost239 topology
     - installation of traffic into the network
     - configuration of network devices
     - deployment of OPM nodes following various strategies
     - monitoring (writing log files)

    The Cost239 is a mesh topology with a mean ROADM degree of 4.
    In the network, all links are bidirectional. Though,
    transmissions are launched uni-directionally.

    For this simple demo, we're only using locations:
    ldn, cph, ber, par, pra and vie.
    The configuration corresponds to the installation of the
    following 15 channels for end-to-end link:
    ldn -> cph -> ber (1400 km, 28 inline EDFAs + 2 boosters) - ch1-15
    par -> ber (900 km, 18 inline EDFAs + 1 booster) - ch16-30
    pra -> vie (350 km, 7 inline EDFAs + 1 booster) - ch31-45

"""

from topo.cost239 import Cost239Topology
from sdn_monitor_qot_e.estimation_module import *
import os
import json


def run(net):
    # the estimation module needs to be launched only once.
    channels_list = [range(1, 16), range(16, 31), range(75, 91)]  # estimation
    # channels_list = [range(1, 16), range(16, 31), range(31, 46)]  # estimation

    # estimation(net, channels_list)
    configure_terminals(net, channels_list)
    configure_roadms(net, channels_list)
    transmit(net, channels_list)
    # monitor(net)


def estimation(net, channels_list):
    ber = net.name_to_node['r_berlin']
    cph = net.name_to_node['r_copenhagen']
    ldn = net.name_to_node['r_london']
    par = net.name_to_node['r_paris']
    pra = net.name_to_node['r_prague']
    vie = net.name_to_node['r_vienna']

    links_dir = [('r_london-r_copenhagen/', 'r_copenhagen-r_berlin/'), 'r_paris-r_berlin/', 'r_prague-r_vienna/']
    links = [((ldn, cph), (cph, ber)), (par, ber), (pra, vie)]

    for _tuple, channels, link_dir in zip(links, channels_list, links_dir):
        main_struct = build_struct(15, signal_ids=channels)
        if type(_tuple[0]) is not tuple:
            link = net.find_link_from_nodes(_tuple[0], _tuple[1])
            spans = []
            for span in link.spans:
                spans.append(span.span.length / 1.0e3)
            estimation_module_simpledemo(main_struct, spans, link_dir)
        else:
            for i, (subtuple, link_dir_it) in enumerate(zip(_tuple, link_dir), start=1):
                link = net.find_link_from_nodes(subtuple[0], subtuple[1])
                spans = []
                for span in link.spans:
                    spans.append(span.span.length / 1.0e3)
                if i == len(_tuple):
                    estimation_module_simpledemo(main_struct, spans, link_dir_it)
                else:
                    main_struct = estimation_module_simpledemo(main_struct, spans, link_dir_it, last=False)


def configure_terminals(net, channels_list):
    # retrieve the terminal objects from net
    lt_london = net.name_to_node['lt_london']
    lt_paris = net.name_to_node['lt_paris']
    lt_prague = net.name_to_node['lt_prague']

    lt_list = [lt_london, lt_paris, lt_prague]

    for lt, channels in zip(lt_list, channels_list):
        transceivers = lt.transceivers
        for i, ch in enumerate(channels, start=channels[0]):
            t = transceivers[i - 1]
            # transceiver, out_port and channels
            lt.configure_terminal(t, [ch])


def configure_roadms(net, channels_list):
    """
    This procedure is long because everything is done manually.
    """
    ber = net.name_to_node['r_berlin']
    cph = net.name_to_node['r_copenhagen']
    ldn = net.name_to_node['r_london']
    par = net.name_to_node['r_paris']
    pra = net.name_to_node['r_prague']
    vie = net.name_to_node['r_vienna']

    ber_lt = net.name_to_node['lt_berlin']
    vie_lt = net.name_to_node['lt_vienna']

    # first setup: configure channels 1-15 from
    # london to berlin following:
    # ldn -> cph -> ber.
    channels1 = channels_list[0]
    # input port of roadm when coming from terminal
    in_port_lt = channels1[0] - 1
    # ldn -> cph
    out_port = net.find_link_and_out_port_from_nodes(ldn, cph)
    for i, channel in enumerate(channels1, start=1):
        ldn.install_switch_rule(i, in_port_lt, out_port, [channel])
        in_port_lt += 1
    # cph -> ber
    # this input port is the one of cph when coming from ldn
    in_port = net.find_link_and_in_port_from_nodes(ldn, cph)
    out_port = net.find_link_and_out_port_from_nodes(cph, ber)
    cph.install_switch_rule(1, in_port, out_port, channels1)
    # cph -> ber and ber -> ber_lt
    in_port = net.find_link_and_in_port_from_nodes(cph, ber)
    out_port = net.find_link_and_out_port_from_nodes(ber, ber_lt)
    ber.install_switch_rule(1, in_port, out_port, channels1)

    # second setup: configure channel 16-30 from
    # paris to berlin following:
    # par -> ber
    channels2 = channels_list[1]
    in_port_lt = channels2[0] - 1
    # par to ber
    out_port = net.find_link_and_out_port_from_nodes(par, ber)
    for i, channel in enumerate(channels2, start=1):
        par.install_switch_rule(i, in_port_lt, out_port, [channel])
        in_port_lt += 1
    # par -> ber and ber -> bet_lt
    in_port = net.find_link_and_in_port_from_nodes(par, ber)
    out_port = net.find_link_and_out_port_from_nodes(ber, ber_lt)
    ber.install_switch_rule(2, in_port, out_port, channels2)

    # third setup: configure channels 31-45 from
    # prague to vienna following:
    # pra -> vie
    channels3 = channels_list[2]
    in_port_lt = channels3[0] - 1
    # pra -> vie
    out_port = net.find_link_and_out_port_from_nodes(pra, vie)
    for i, channel in enumerate(channels3, start=1):
        pra.install_switch_rule(i, in_port_lt, out_port, [channel])
        in_port_lt += 1
    # pra -> vie and vie -> vie_lt
    in_port = net.find_link_and_in_port_from_nodes(pra, vie)
    out_port = net.find_link_and_out_port_from_nodes(vie, vie_lt)
    vie.install_switch_rule(1, in_port, out_port, channels3)


def transmit(net, channels_list):
    lt_london = net.name_to_node['lt_london']
    lt_paris = net.name_to_node['lt_paris']
    lt_prague = net.name_to_node['lt_prague']

    out_ports = [i - 1 for i in channels_list[0]]
    lt_london.turn_on(out_ports)
    out_ports = [i - 1 for i in channels_list[1]]
    lt_paris.turn_on(out_ports)
    out_ports = [i - 1 for i in channels_list[2]]
    lt_prague.turn_on(out_ports)


def monitor(net):
    """
    net: network object
    density: density percentage (10 = 10%, 30 = 30%, etc)
    first_last: when 1 OPM is to be used, decide whether using
    the first one (boost-monitor) or last one (pre-amp-monitor) in the link
    """
    # build the monitors list
    mon_ldn_cph = ['r_london-r_copenhagen-amp%s' % str(i) for i in range(1, 21)]
    # insert booster monitor at the beginning
    mon_ldn_cph.insert(0, 'r_london-r_copenhagen-boost')
    # query the OPMs and write log files
    for monitor_name in mon_ldn_cph:
        monitor_query(net, monitor_name)

    mon_cph_ber = ['r_copenhagen-r_berlin-amp%s' % str(i) for i in range(1, 9)]
    mon_cph_ber.insert(0, 'r_copenhagen-r_berlin-boost')
    for monitor_name in mon_cph_ber:
        monitor_query(net, monitor_name)

    mon_par_ber = ['r_paris-r_berlin-amp%s' % str(i) for i in range(1, 19)]
    mon_par_ber.insert(0, 'r_paris-r_berlin-boost')
    for monitor_name in mon_par_ber:
        monitor_query(net, monitor_name)

    mon_pra_vie = ['r_prague-r_vienna-amp%s' % str(i) for i in range(1, 8)]
    mon_pra_vie.insert(0, 'r_prague-r_vienna-boost')
    for monitor_name in mon_pra_vie:
        monitor_query(net, monitor_name)


def monitor_query(net, component_name):
    x = component_name.split('-', 2)
    link_label = x[0] + '-' + x[1]
    monitor = net.name_to_node[component_name].monitor

    osnrdata = {int(signal.index):
                    dict(freq=signal.frequency, osnr=monitor.get_osnr(signal),
                         gosnr=monitor.get_gosnr(signal),
                         power=monitor.get_power(signal),
                         ase=monitor.get_ase_noise(signal),
                         nli=monitor.get_nli_noise(signal))
                for signal in net.name_to_node[component_name].optical_signals}

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
                json_struct, link_label, component_name)


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

    test = 'cost239-monitor/monitor-module-new/'
    dir_ = test + link_label + '/'
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    json_file_name = dir_ + monitor_name + '.json'
    with open(json_file_name, 'w+') as outfile:
        json.dump(json_struct, outfile)


if __name__ == '__main__':
    with open('seeds/wdg_seed_simpledemo.txt', 'r') as filename:
        data = filename.readline()
        seeds2 = data.split(',')
        seeds2 = seeds2[:-1]
    net = Cost239Topology.build()
    for amp, ripple in zip(net.amplifiers, seeds2):
        amp.set_ripple_function(ripple)
    run(net)

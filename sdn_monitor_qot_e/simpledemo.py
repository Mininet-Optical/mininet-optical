"""
    This script contains a series of functions that represent
    five different tests run on the Cost239 network topology:
        - install_traffic_and_launch
        - remove_single_signal
        - remove_all_signals
        - reroute
        - estimate_and_monitor

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

    To execute the tests is only required to uncomment the desired
    line of code with the name of the test within the __main__ function.

"""

from topo.cost239 import Cost239Topology
from sdn_monitor_qot_e.estimation_module import *
import os
import json


# Functions for test install_traffic_and_launch
# and reusable code - START
def install_traffic_and_launch():
    # declare three groups of channels to be launched
    channels_list = [range(1, 16), range(16, 31), range(75, 91)]
    configure_terminals_1(channels_list)
    configure_roadms_1(channels_list)
    transmit_1()


def configure_terminals_1(channels_list):
    # retrieve the terminal objects from net and,
    # to ease iteration put them in a list
    lt_list = [net.name_to_node['lt_london'],
               net.name_to_node['lt_paris'],
               net.name_to_node['lt_prague']]

    for lt, channels in zip(lt_list, channels_list):
        transceivers = lt.transceivers
        for i, channel in enumerate(channels, start=channels[0]):
            # channels are enumerated starting from 1
            # transceivers and their ports are enumerated starting from 0
            t = transceivers[i - 1]
            # associate transceiver to channel in LineTerminal
            lt.configure_terminal(t, channel)


def configure_roadms_1(channels_list):
    # retrieve the network elements to use
    # for this test from the network
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
        ldn.configure_voa(channel_id=channel, output_port=out_port, operational_power_dB=0)
        in_port_lt += 1
    # cph -> ber
    # this input port is the one of cph when coming from ldn
    in_port = net.find_link_and_in_port_from_nodes(ldn, cph)
    out_port = net.find_link_and_out_port_from_nodes(cph, ber)
    cph.install_switch_rule(1, in_port, out_port, channels1)
    for chx in channels1:
        cph.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)
    # cph -> ber and ber -> ber_lt
    in_port = net.find_link_and_in_port_from_nodes(cph, ber)
    out_port = net.find_link_and_out_port_from_nodes(ber, ber_lt)
    ber.install_switch_rule(1, in_port, out_port, channels1)
    for chx in channels1:
        ber.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)

    # second setup: configure channel 16-30 from
    # paris to berlin following:
    # par -> ber
    channels2 = channels_list[1]
    in_port_lt = channels2[0] - 1
    # par to ber
    out_port = net.find_link_and_out_port_from_nodes(par, ber)
    for i, channel in enumerate(channels2, start=1):
        par.install_switch_rule(i, in_port_lt, out_port, [channel])
        par.configure_voa(channel_id=channel, output_port=out_port, operational_power_dB=0)
        in_port_lt += 1
    # par -> ber and ber -> bet_lt
    in_port = net.find_link_and_in_port_from_nodes(par, ber)
    out_port = net.find_link_and_out_port_from_nodes(ber, ber_lt)
    ber.install_switch_rule(2, in_port, out_port, channels2)
    for chx in channels2:
        ber.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)

    # third setup: configure channels 31-45 from
    # prague to vienna following:
    # pra -> vie
    channels3 = channels_list[2]
    in_port_lt = channels3[0] - 1
    # pra -> vie
    out_port = net.find_link_and_out_port_from_nodes(pra, vie)
    for i, channel in enumerate(channels3, start=1):
        pra.install_switch_rule(i, in_port_lt, out_port, [channel])
        pra.configure_voa(channel_id=channel, output_port=out_port, operational_power_dB=0)
        in_port_lt += 1
    # pra -> vie and vie -> vie_lt
    in_port = net.find_link_and_in_port_from_nodes(pra, vie)
    out_port = net.find_link_and_out_port_from_nodes(vie, vie_lt)
    vie.install_switch_rule(1, in_port, out_port, channels3)
    for chx in channels3:
        vie.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)


def transmit_1():
    lt_london = net.name_to_node['lt_london']
    lt_paris = net.name_to_node['lt_paris']
    lt_prague = net.name_to_node['lt_prague']

    # everything is configured at this point,
    # let's just turn the LTs on!
    lt_london.turn_on()
    lt_paris.turn_on()
    lt_prague.turn_on()
# Functions for test install_traffic_and_launch
# and reusable code - END


# Functions for test remove_single_signal
# and reusable code - START
def remove_single_signal(channel_to_remove):
    channels = range(1, 31)
    configure_terminals_2(channels)
    configure_roadms_2(channels)
    transmit_2()
    lt_london = net.name_to_node['lt_london']
    out_ports = [channel_to_remove - 1]  # must be passed as a list
    lt_london.turn_off(out_ports)


def configure_terminals_2(channels):
    # retrieve the terminal objects from net and,
    # to ease iteration put them in a list
    lt_ldn = net.name_to_node['lt_london']

    transceivers = lt_ldn.transceivers
    for i, channel in enumerate(channels, start=channels[0]):
        # channels are enumerated starting from 1
        # transceivers and their ports are enumerated starting from 0
        t = transceivers[i - 1]
        # associate transceiver to channel in LineTerminal
        lt_ldn.configure_terminal(t, channel)


def configure_roadms_2(channels):
    ber = net.name_to_node['r_berlin']
    cph = net.name_to_node['r_copenhagen']
    ldn = net.name_to_node['r_london']

    ber_lt = net.name_to_node['lt_berlin']

    # setup: configure channels 1-15 from
    # london to berlin following:
    # ldn -> cph -> ber.
    # input port of roadm when coming from terminal
    in_port_lt = channels[0] - 1
    # ldn -> cph
    out_port = net.find_link_and_out_port_from_nodes(ldn, cph)
    for i, channel in enumerate(channels, start=1):
        ldn.install_switch_rule(i, in_port_lt, out_port, [channel])
        ldn.configure_voa(channel_id=channel, output_port=out_port, operational_power_dB=0)
        in_port_lt += 1
    # cph -> ber
    # this input port is the one of cph when coming from ldn
    in_port = net.find_link_and_in_port_from_nodes(ldn, cph)
    out_port = net.find_link_and_out_port_from_nodes(cph, ber)
    cph.install_switch_rule(1, in_port, out_port, channels)
    for chx in channels:
        cph.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)
    # cph -> ber and ber -> ber_lt
    in_port = net.find_link_and_in_port_from_nodes(cph, ber)
    out_port = net.find_link_and_out_port_from_nodes(ber, ber_lt)
    ber.install_switch_rule(1, in_port, out_port, channels)
    for chx in channels:
        ber.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)


def transmit_2():
    lt_london = net.name_to_node['lt_london']
    lt_london.turn_on()
# Functions for test remove_single_signal
# and reusable code - END


# Functions for test remove_all_signals
# and reusable code - START
def remove_all_signals():
    channels_list = [range(1, 16), range(16, 31)]
    configure_terminals_3(channels_list)
    configure_roadms_3(channels_list)
    transmit_2()

    channels_to_remove = range(1, 16)
    remove(channels_to_remove)


def configure_terminals_3(channels_list):
    # retrieve the terminal objects from net
    lt_london = net.name_to_node['lt_london']

    lt_list = [lt_london, lt_london]

    for lt, channels in zip(lt_list, channels_list):
        transceivers = lt.transceivers
        for i, ch in enumerate(channels, start=channels[0]):
            t = transceivers[i - 1]
            # transceiver and channels
            lt.configure_terminal(t, ch)


def configure_roadms_3(channels_list):
    ber = net.name_to_node['r_berlin']
    cph = net.name_to_node['r_copenhagen']
    ldn = net.name_to_node['r_london']

    ber_lt = net.name_to_node['lt_berlin']

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
        ldn.configure_voa(channel_id=channel, output_port=out_port, operational_power_dB=0)
        in_port_lt += 1
    # cph -> ber
    # this input port is the one of cph when coming from ldn
    in_port = net.find_link_and_in_port_from_nodes(ldn, cph)
    out_port = net.find_link_and_out_port_from_nodes(cph, ber)
    cph.install_switch_rule(1, in_port, out_port, channels1)
    for chx in channels1:
        cph.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)
    # cph -> ber and ber -> ber_lt
    in_port = net.find_link_and_in_port_from_nodes(cph, ber)
    out_port = net.find_link_and_out_port_from_nodes(ber, ber_lt)
    ber.install_switch_rule(1, in_port, out_port, channels1)
    for chx in channels1:
        ber.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)

    channels2 = channels_list[1]
    in_port_lt = channels2[0] - 1
    # par to ber
    out_port = net.find_link_and_out_port_from_nodes(ldn, cph)
    for i, channel in enumerate(channels2, start=16):
        ldn.install_switch_rule(i, in_port_lt, out_port, [channel])
        ldn.configure_voa(channel_id=channel, output_port=out_port, operational_power_dB=0)
        in_port_lt += 1
    # par -> ber and ber -> bet_lt
    in_port = net.find_link_and_in_port_from_nodes(ldn, cph)
    out_port = net.find_link_and_out_port_from_nodes(cph, ber)
    cph.install_switch_rule(2, in_port, out_port, channels2)
    for chx in channels2:
        cph.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)
    # cph -> ber and ber -> ber_lt
    in_port = net.find_link_and_in_port_from_nodes(cph, ber)
    out_port = net.find_link_and_out_port_from_nodes(ber, ber_lt)
    ber.install_switch_rule(2, in_port, out_port, channels2)
    for chx in channels2:
        ber.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)


def remove(channels):
    lt_london = net.name_to_node['lt_london']
    out_ports = [i - 1 for i in channels]
    lt_london.turn_off(out_ports)
# Functions for test remove_all_signals
# and reusable code - END


# Functions for test reroute
# and reusable code - START
def reroute():
    channels_list = [range(1, 16), range(16, 31)]
    configure_terminals_3(channels_list)
    configure_roadms_3(channels_list)
    transmit_2()

    channels_to_reroute = range(16, 31)
    rerouting(channels_to_reroute)


def rerouting(channels):
    # This is currently not working
    cph = net.name_to_node['r_copenhagen']
    ams = net.name_to_node['r_amsterdam']

    ams_lt = net.name_to_node['lt_amsterdam']

    # place this below the lines below for updating switch rule
    # to see the effect of rerouting without having the rules
    # installed beforehand.
    in_port = net.find_link_and_in_port_from_nodes(cph, ams)
    out_port = net.find_link_and_out_port_from_nodes(ams, ams_lt)
    ams.install_switch_rule(1, in_port, out_port, channels)
    for chx in channels:
        ams.configure_voa(channel_id=chx, output_port=out_port, operational_power_dB=0)

    out_port = net.find_link_and_out_port_from_nodes(cph, ams)
    cph.update_switch_rule(2, out_port)
# Functions for test reroute
# and reusable code - END


# Functions for test estimate_and_monitor
# and reusable code - START
def estimate_and_monitor():
    # This needs to update the monitoring
    channels_list = [range(1, 31), range(16, 31), range(75, 91)]
    estimation(channels_list)
    install_traffic_and_launch()
    monitor()


def estimation(channels_list):
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


def monitor(to_write_files=False):
    """
    net: network object
    density: density percentage (10 = 10%, 30 = 30%, etc)
    first_last: when 1 OPM is to be used, decide whether using
    the first one (boost-monitor) or last one (pre-amp-monitor) in the link
    """
    # build the monitors list
    mon_ldn_cph = ['r_london-r_copenhagen-amp%s' % str(i) for i in range(1, 20)]
    # insert booster monitor at the beginning
    mon_ldn_cph.insert(0, 'r_london-r_copenhagen-boost')
    # query the OPMs and write log files
    for monitor_name in mon_ldn_cph:
        monitor_query(monitor_name, to_write_files=to_write_files)

    mon_cph_ber = ['r_copenhagen-r_berlin-amp%s' % str(i) for i in range(1, 8)]
    mon_cph_ber.insert(0, 'r_copenhagen-r_berlin-boost')
    for monitor_name in mon_cph_ber:
        monitor_query(monitor_name, to_write_files=to_write_files)

    mon_par_ber = ['r_paris-r_berlin-amp%s' % str(i) for i in range(1, 18)]
    mon_par_ber.insert(0, 'r_paris-r_berlin-boost')
    for monitor_name in mon_par_ber:
        monitor_query(monitor_name, to_write_files=to_write_files)

    mon_pra_vie = ['r_prague-r_vienna-amp%s' % str(i) for i in range(1, 7)]
    mon_pra_vie.insert(0, 'r_prague-r_vienna-boost')
    for monitor_name in mon_pra_vie:
        monitor_query(monitor_name, to_write_files=to_write_files)


def monitor_query(component_name, to_write_files=False):
    x = component_name.split('-', 2)
    link_label = x[0] + '-' + x[1]
    component = net.name_to_node[component_name]
    monitor = net.name_to_node[component_name].monitor_query()

    # need to get signals from component to be able to iterate through them
    osnrdata = {int(signal[0].index):
                    dict(freq=signal[0].frequency, osnr=monitor.get_osnr(signal),
                         gosnr=monitor.get_gosnr(signal),
                         power=monitor.get_power(signal),
                         ase=monitor.get_ase_noise(signal),
                         nli=monitor.get_nli_noise(signal))
                for signal in monitor.optical_signals}

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

    if to_write_files:
        write_files(osnrs, gosnrs, powers, ases, nlis,
                    json_struct, link_label, component_name)
    else:
        print(gosnrs)


def write_files(osnr, gosnr, powers, ases, nlis,
                json_struct, link_label, monitor_name):
    """
    Write a file with osnr and gosnr information from a given OPM node
    """
    return
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
# Functions for test estimate_and_monitor
# and reusable code - END


if __name__ == '__main__':
    # access the ripple function seed to assign to the EDFAs
    # seed the generator!
    with open('seeds/wdg_seed_simpledemo.txt', 'r') as filename:
        data = filename.readline()
        seeds2 = data.split(',')
        seeds2 = seeds2[:-1]
    # Create the Cost239 network object
    net = Cost239Topology.build()
    # this controls the assignation of ripple functions
    # to the EDFAs in the network
    for amp, ripple in zip(net.amplifiers, seeds2):
        amp.set_ripple_function(ripple)

    # These lines may be uncommented ONE-AT-A-TIME
    # # Test 1
    install_traffic_and_launch()
    # # Test 2
    # remove_single_signal(1)
    # # Test 3
    # remove_all_signals()
    # # Test 4
    # reroute()
    # # Test 5
    estimate_and_monitor()

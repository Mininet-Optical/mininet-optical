from topo.cost239 import Cost239Topology
from sdn_monitor_qot_e.estimation_module import *
import os
import json
from dataplane import Mininet, ROADM, Terminal, disableIPv6
from ofcdemo.demolib import LinearRoadmTopo, CLI
from rest import RestServer

from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController


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

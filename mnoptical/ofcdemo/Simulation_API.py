from mnoptical.network import Network
from mnoptical.link import Span as Fiber, SpanTuple as Segment
from mnoptical.node import Transceiver
from mnoptical.units import *
from collections import defaultdict
import random
from collections import defaultdict
import numpy as np



class Mininet_Optical_Simu_API(object):

    def ROADM_installSwitchRule(self, node, ruleID, inport, outport, channelID):
        "install a switch rule in a ROADM"

        node.install_switch_rule(rule_id=ruleID, in_port=inport, out_port=outport, signal_indices=[channelID])
        print('install switch rule', node, ruleID, inport, outport, channelID)

    def ROADM_deleteSwitchRule(self, node, ruleID):
        "delete a switch rule in a ROADM using rule ID"

        node.delete_switch_rule(rule_id=ruleID)


    def ROADM_voaPowerLeveling(self, node, outport, power, channel):
        "Power control for a signal channel at a roadm using VOA leveling"

        #print('leveling power, port, channel:', power, outport, channel)
        node.configure_voa(channel_id=channel, output_port=outport, operational_power_dB=power)


    def Terminal_configChannelPower(self, terminal, channel, power):
        "Congifure Terminal Launch power for a channel"

        terminal.transceivers[channel-1].operation_power = db_to_abs(power)
        #terminal.name_to_transceivers['tx%d' % channel].operation_power = db_to_abs(power)


    def Terminal_configChannel(self, terminal, channel):
        "configure a Terminal with a given channel"

        #terminal.configure_terminal(transceiver=terminal.transceivers[transceiverIndx], channel=channel)
        terminal.configure_terminal(transceiver=terminal.transceivers[channel - 1], channel=channel)
        #terminal.turn_on()
        #print(terminal, channel)


    def Terminal_turnonChannel(self, terminal):
        "Turn on a Terminal"

        terminal.turn_on()

    def Terminal_turnoffChannel(self, terminal, channel):
        "Turn off a Terminal with a given channel"

        terminal.turn_off([channel-1])

    def Terminal_Reset_Threshold(self, terminal, threshold):
        terminal.update_rx_threshold(threshold)


    def ROADM_monitor_all_power(self, node):
        "monitoring all power data at a node"

        return node.monitor.get_dict_power()

    def ROADM_monitor_all_osnr(self, node):
        "monitoring all osnr data at a node"

        return node.monitor.get_dict_osnr()

    def ROADM_monitor_all_gosnr(self, node):
        "monitoring all gosnr data at a node"

        return node.monitor.get_dict_gosnr()

    def ROADM_monitor_channel_data(self, node, channel):
        "monitoring a signal channel in a ROADM node"

        output_power = None
        osnr = None
        gosnr = None
        freq = round((191.30 + 0.05 * channel) * 10 ** 12, 1)
        optical_signals = node.monitor.extract_optical_signal()
        for sig in optical_signals:
            if freq == sig[0].frequency:
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

        return output_power, osnr, gosnr





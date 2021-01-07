from units import *
from edfa_params import *
from pprint import pprint
import random
from collections import namedtuple
from scipy.special import erfc
from math import sqrt


class Node(object):
    input_port_base = 0
    output_port_base = 0

    def __init__(self, name):
        self.name = name

        # static attributes - inputs
        self.ports_in = []
        self.port_to_node_in = {}
        self.node_to_port_in = {}
        self.node_to_link_in = {}
        self.link_to_node_in = {}
        self.port_to_link_in = {}
        self.link_to_port_in = {}

        # static attributes - outputs
        self.ports_out = []
        self.port_to_node_out = {}
        # AD: used by helper functions in Network.
        # Probably will need to be part of the Network
        # class instead
        self.node_to_port_out = {}
        self.node_to_link_out = {}
        self.link_to_node_out = {}
        self.port_to_link_out = {}
        self.link_to_port_out = {}

        # dynamic attributes - inputs
        self.port_to_optical_signal_in = {}
        self.optical_signal_to_port_in = {}
        self.node_to_optical_signal_in = {}
        self.optical_signal_to_node_in = {}

        # dynamic attributes - outputs
        self.port_to_optical_signal_out = {}
        self.optical_signal_to_port_out = {}
        self.node_to_optical_signal_out = {}
        self.optical_signal_to_node_out = {}

    def set_output_port(self, dst_node, link, output_port=-1):
        if output_port < 0:
            output_port = self.output_port_base
            self.output_port_base += 1
        else:
            self.output_port_base = output_port + 1

        # set static attributes
        self.ports_out.append(output_port)
        self.port_to_node_out[output_port] = dst_node
        self.link_to_node_out[link] = dst_node
        self.port_to_link_out[output_port] = link
        self.link_to_port_out[link] = output_port

        # a node can have multiple
        # output ports to another node
        self.node_to_port_out.setdefault(dst_node, []).append(output_port)
        self.node_to_link_out.setdefault(dst_node, []).append(link)

        # initialize dynamic attributes
        self.port_to_optical_signal_out[output_port] = []
        self.node_to_optical_signal_out[dst_node] = []
        return output_port

    def set_input_port(self, src_node, link, input_port=-1):
        if input_port < 0:
            input_port = self.input_port_base
            self.input_port_base += 1
        else:
            self.input_port_base = input_port + 1

        # set static attributes
        self.ports_in.append(input_port)
        self.port_to_node_in[input_port] = src_node
        self.port_to_link_in[input_port] = link
        self.link_to_port_in[link] = input_port
        self.link_to_node_in[link] = src_node

        # a node can have multiple input
        # ports from another node
        self.node_to_port_in.setdefault(src_node, []).append(input_port)
        self.node_to_link_in.setdefault(src_node, []).append(link)

        # initialize dynamic attributes
        self.port_to_optical_signal_in[input_port] = []
        self.node_to_optical_signal_in[src_node] = []
        return input_port

    def include_optical_signal_in(self, optical_signal, power=None, ase_noise=None,
                                  nli_noise=None, in_port=None, src_node=None):
        """
        :param optical_signal: OpticalSignal object, OpticalSignal uid
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param in_port: input port of node (optional)
        :param src_node: src node (optional)
        """
        # update structures with the input ports of the current node
        self.port_to_optical_signal_in.setdefault(in_port, [])
        if optical_signal not in self.port_to_optical_signal_in[in_port]:
            # a port can carry multiple signals
            self.port_to_optical_signal_in[in_port].append(optical_signal)
            # for symmetry:
            self.optical_signal_to_port_in[optical_signal] = in_port

        # update the structures with the source nodes (where signals are coming from)
        self.node_to_optical_signal_in.setdefault(src_node, [])
        if optical_signal not in self.node_to_optical_signal_in[src_node]:
            self.node_to_optical_signal_in[src_node].append(optical_signal)
            self.optical_signal_to_node_in[optical_signal] = src_node

        # but we need to associate a component with the state of the signal
        optical_signal.assoc_loc_in(self, power, ase_noise, nli_noise)

    def include_optical_signal_out(self, optical_signal, power=None, ase_noise=None,
                                   nli_noise=None, out_port=None, dst_node=None):
        """
        :param optical_signal: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param out_port: output port of node (optional)
        :param dst_node: dst node (optional)
        """
        if out_port is not None or out_port == 0:
            self.port_to_optical_signal_out.setdefault(out_port, [])
            if optical_signal not in self.port_to_optical_signal_out[out_port]:
                self.port_to_optical_signal_out[out_port].append(optical_signal)
                self.optical_signal_to_port_out[optical_signal] = out_port

        if dst_node is not None:
            self.node_to_optical_signal_out.setdefault(dst_node, [])
            if optical_signal not in self.node_to_optical_signal_out[dst_node]:
                self.node_to_optical_signal_out[dst_node].append(optical_signal)
                self.optical_signal_to_node_out[optical_signal] = dst_node

        optical_signal.assoc_loc_out(self, power, ase_noise, nli_noise)

    def remove_optical_signal(self, optical_signal):
        print("*** %s - %s removing signal: OpticalSignal:%s" % (self.__class__.__name__,
                                                                 self.name, optical_signal))

        if optical_signal in self.optical_signal_to_node_in:
            src_node = self.optical_signal_to_node_in[optical_signal]
            if optical_signal in self.node_to_optical_signal_in[src_node]:
                self.node_to_optical_signal_in[src_node].remove(optical_signal)
            del self.optical_signal_to_node_in[optical_signal]

        if optical_signal in self.optical_signal_to_node_out:
            dst_node = self.optical_signal_to_node_out[optical_signal]
            if optical_signal in self.node_to_optical_signal_out[dst_node]:
                self.node_to_optical_signal_out[dst_node].remove(optical_signal)
            del self.optical_signal_to_node_out[optical_signal]

        if optical_signal in self.optical_signal_to_port_in:
            port_in = self.optical_signal_to_port_in[optical_signal]
            self.port_to_optical_signal_in[port_in].remove(optical_signal)

            del self.optical_signal_to_port_in[optical_signal]

        if optical_signal in self.optical_signal_to_port_out:
            port_out = self.optical_signal_to_port_out[optical_signal]
            self.port_to_optical_signal_out[port_out].remove(optical_signal)
            del self.optical_signal_to_port_out[optical_signal]
            link = self.port_to_link_out[port_out]
            link.remove_optical_signal(optical_signal)

    def remove_signal_from_out_port(self, port_out, optical_signal):
        if optical_signal in self.optical_signal_to_port_out:
            del self.optical_signal_to_port_out[optical_signal]
        if port_out in self.port_to_optical_signal_out:
            if optical_signal in self.port_to_optical_signal_out[port_out]:
                self.port_to_optical_signal_out[port_out].remove(optical_signal)

        link = self.port_to_link_out[port_out]
        link.remove_optical_signal(optical_signal)

        if optical_signal in self.optical_signal_to_node_out:
            dst_node = self.optical_signal_to_node_out[optical_signal]
            if optical_signal in self.node_to_optical_signal_out[dst_node]:
                self.node_to_optical_signal_out[dst_node].remove(optical_signal)
            del self.optical_signal_to_node_out[optical_signal]

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        """Human-readable representation"""
        return '%s' % self.name


class LineTerminal(Node):

    def __init__(self, name, transceivers=None, receiver_threshold=20, monitor_mode='out'):
        Node.__init__(self, name)
        # list of transceivers in LineTerminal
        if transceivers is None:
            transceivers = []
        self.transceivers = []
        # dict of name of transceiver to transceiver objects
        self.name_to_transceivers = {}
        # dict of id (or WDM port) to transceiver
        self.id_to_transceivers = {}
        self.add_transceivers(transceivers)

        self.monitor = Monitor(name + "-monitor", component=self, mode=monitor_mode)

        # dynamic attributes
        self.optical_signals_out = 0
        self.rx_to_channel = {}
        self.channel_to_rx = {}

        # will become obsolete, threshold moved to the Transceiver
        self.rx_threshold_dB = receiver_threshold

    def monitor_query(self):
        if self.monitor:
            return self.monitor

    def reset(self):
        """
        This should reset all the dynamic attributes
        """
        # clean output ports
        for out_port, _ in self.port_to_optical_signal_out.items():
            self.port_to_optical_signal_out[out_port] = []
        # clean input ports
        for in_port, _ in self.port_to_optical_signal_in.items():
            self.port_to_optical_signal_in[in_port] = []

    def add_transceivers(self, transceivers):
        """
        For-loop for adding transceivers to LT
        :param transceivers: list of tuples (t_name, operational_power, spectrum band)
        :return:
        """
        for transceiver in transceivers:
            self.add_transceiver(transceiver)

    def existing_transceiver(self, transceiver):
        if transceiver.name in self.name_to_transceivers:
            return True
        else:
            return False

    def add_transceiver(self, transceiver):
        """
        Add a new transceiver to the Terminal
        :return: added transceiver
        """
        if self.existing_transceiver(transceiver):
            raise ValueError("Node.LineTerminal.add_transceiver: Transceiver with this name already exist!")
        # enable to retrieve Transceiver object by name and ID
        self.name_to_transceivers[transceiver.name] = transceiver
        self.id_to_transceivers[transceiver.id] = transceiver
        # add transceiver to LineTerminal list
        self.transceivers.append(transceiver)

    def update_transceiver(self, transceiver, args):
        """
        AD: Probably needs to be revisited
        Update/modify the configuration attributes of a transceiver
        :param transceiver: transceiver object to configure
        :param args: dict with parameters to update
        :return:
        """
        transceiver.__dict__.update(args)
        if 'modulation_format' in args:
            transceiver.compute_gross_bit_rate()

    def update_rx_threshold(self, new_rx_threshold):
        # AD: Probably obsolete, threshold is a feature of Transceivers
        self.rx_threshold_dB = new_rx_threshold

    def assoc_tx_to_channel(self, transceiver, channel, in_port=-1, out_port=-1):
        """
        PREVIOUSLY configure_terminal()
        Program the channels that will be launched at transceivers
        :param transceiver: transceiver to use for transmission
        :param channel: the channels to be transmitted
        :param in_port: input port to terminal, -1 if none.
        :param out_port: input port to terminal, -1 if none.
        :return: associate a transceiver to an optical signal
        """
        # instantiate OpticalSignal object
        optical_signal = OpticalSignal(channel,
                                       transceiver.channel_spacing_H, transceiver.channel_spacing_nm,
                                       transceiver.symbol_rate, transceiver.bits_per_symbol,
                                       power=transceiver.operation_power)

        # associate transceiver to optical_signal
        transceiver.assoc_optical_signal(optical_signal)

        # signals are originated at the Line Terminals, unless run in emulation mode
        # in_port=-1 in simulation mode, otherwise is the eth-port
        # src_node=self always, needed for querying
        self.include_optical_signal_in(optical_signal, in_port=in_port, src_node=self)
        if out_port == -1:
            out_port = transceiver.id
        # the goal of this function
        dst_node = self.port_to_node_out[out_port]
        self.include_optical_signal_out(optical_signal, out_port=out_port, dst_node=dst_node)
        self.optical_signals_out += 1

    def assoc_rx_to_channel(self, transceiver, channel_id):
        self.rx_to_channel[transceiver] = channel_id
        self.channel_to_rx[channel_id] = transceiver

    def turn_on(self):
        """Propagate signals to the link that the transceivers point to"""
        signal_count = 0
        for out_port, transceiver in self.id_to_transceivers.items():
            if transceiver.optical_signal is not None:
                signal_count += 1
                transceiver.optical_signal.reset()
                # pass signal info to link
                link = self.port_to_link_out[out_port]
                link.include_optical_signal_in(transceiver.optical_signal)

                if signal_count == self.optical_signals_out:
                    link.propagate(is_last_port=True)
                else:
                    link.propagate()

    def turn_off(self, ports_out):
        optical_signals = []
        # find transceiver objects and create list
        for tr in self.transceivers:
            if tr.id in ports_out:
                optical_signal = tr.optical_signal
                optical_signals.append(optical_signal)
                tr.remove_optical_signal()
        for optical_signal in optical_signals:
            self.remove_optical_signal(optical_signal)
        # call propagation with left-over signals (if any)
        self.turn_on()

    @staticmethod
    def osnr(power, ase_noise):
        return abs_to_db(power / ase_noise)

    @staticmethod
    def gosnr(power, ase_noise, nli_noise, baud_rate):
        gosnr_linear = power / (ase_noise + nli_noise)
        return abs_to_db(gosnr_linear) - (12.5e9 / baud_rate)

    def receiver(self, optical_signal, in_port):
        """
        Will verify that the signal can be received, then compute
        the OSNR and gOSNR levels of the signal, and will do a
        callback to dataplane (if run in emulation mode).
        """
        signalInfoDict = {optical_signal: {'osnr': None, 'gosnr': None,
                                           'ber': None, 'success': False}}

        if not (optical_signal.index in self.channel_to_rx):
            # Need to extend this to catch all possible problems at RX
            self.receiver_callback(in_port, signalInfoDict)
            raise ValueError("@%s, optical signal: %s not configured for Rx in LineTerminal.\n"
                             "Try calling %s.assoc_rx_to_channel() before launching transmission." %
                             (self, optical_signal, self))

        # Get signal info
        power = optical_signal.loc_in_to_state[self]['power']
        ase_noise = optical_signal.loc_in_to_state[self]['ase_noise']
        nli_noise = optical_signal.loc_in_to_state[self]['nli_noise']

        # Compute OSNR and gOSNR
        osnr = self.osnr(power, ase_noise)
        gosnr = self.gosnr(power, ase_noise, nli_noise, optical_signal.symbol_rate)

        signalInfoDict[optical_signal]['osnr'] = osnr
        signalInfoDict[optical_signal]['gosnr'] = gosnr

        if gosnr < 20:  # rx_transceiver.rx_threshold_dB:
            print("*** %s - %s.receiver.%s: Failure!\ngOSNR: %f dB - rx-thd:%s dB" %
                  (optical_signal, self.__class__.__name__,
                   self.name, gosnr, self.rx_threshold_dB))
            print("OSNR:", osnr)

            signalInfoDict[optical_signal]['success'] = False
            self.receiver_callback(in_port, signalInfoDict)
        else:
            print("*** %s - %s.receiver.%s: Success!\ngOSNR: %f dB" %
                  (optical_signal, self.__class__.__name__, self.name, gosnr))
            print("OSNR:", osnr)

            signalInfoDict[optical_signal]['success'] = True
            self.receiver_callback(in_port, signalInfoDict)

    def receiver_callback(self, in_port, signalDictInfo):
        return


class Transceiver(object):
    def __init__(self, tr_id, name, operation_power=0,
                 channel_spacing_nm=0.4 * 1e-9, channel_spacing_H=50e9,
                 bandwidth=2.99792458 * 1e9, modulation_format='16-QAM',
                 bits_per_symbol=4.0, symbol_rate=32.0e9, rx_threshold_dB=20.0):
        """
        :param name: human readable ID
        :param operation_power: operation power in dB
        :param channel_spacing_nm: channel spacing in nm
        :param channel_spacing_H: channel spacing in Hz
        :param bandwidth: channel bandwidth in GHz - float
        :param modulation_format: modulation format name - string
        :param bits_per_symbol: bits per symbol according to modulation format = float
        :param symbol_rate: symbol rate in GBaud - float
        :param rx_threshold_dB: receiver gOSNR sensitivity in dB - float
        """
        # configuration attributes
        self.name = name
        self.id = tr_id
        self.operation_power = db_to_abs(operation_power) * 1e-3  # in Watts
        self.channel_spacing_nm = channel_spacing_nm
        self.channel_spacing_H = channel_spacing_H
        self.bandwidth = bandwidth
        self.modulation_format = modulation_format
        self.bits_per_symbol = bits_per_symbol
        self.symbol_rate = symbol_rate
        self.rx_threshold_dB = rx_threshold_dB
        self.gross_bit_rate = symbol_rate * np.log2(bits_per_symbol)

        # state attributes
        self.optical_signal = None

    def assoc_optical_signal(self, optical_signal):
        self.optical_signal = optical_signal

    def remove_optical_signal(self):
        self.optical_signal = None

    def compute_gross_bit_rate(self):
        self.gross_bit_rate = self.symbol_rate * np.log2(self.bits_per_symbol)

    def describe(self):
        pprint(vars(self))


class OpticalSignal(object):
    spectrum_band_init_nm = 1567.132556194459
    spectrum_band_init_H = 191.3e12

    def __init__(self, index, channel_spacing_H,
                 channel_spacing_nm, symbol_rate, bits_per_symbol,
                 power=0, ase_noise=0, nli_noise=0):
        self.uid = id(self)
        # configuration attributes
        self.index = index
        self.frequency = self.spectrum_band_init_H + (channel_spacing_H * int(index))
        self.wavelength = c / self.frequency
        self.wavelength2 = self.spectrum_band_init_nm * nm + index * channel_spacing_nm
        self.symbol_rate = symbol_rate
        self.bits_per_symbol = bits_per_symbol

        # state attributes
        self.power_start = power
        self.ase_noise_start = ase_noise
        self.nli_noise_start = nli_noise
        self.power = power
        self.ase_noise = ase_noise
        self.nli_noise = nli_noise
        # loc_in/out: (power:p, ase:a, nli:n)
        self.loc_in_to_state = {}  # looping back to the same component?
        self.loc_out_to_state = {}  # detect and don't allow!

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        return '<ch%d:%.2fTHz>' % (
            self.index, self.frequency / THz)

    def assoc_loc_in(self, loc, power=None, ase_noise=None, nli_noise=None):
        """
        Associate a location to signal performance values
        at the input interface of this point
        :param loc: location (i.e., node, span)
        :param power: power levels [mW]
        :param ase_noise: ase levels [mW]
        :param nli_noise: nli levels [mW]
        """
        if not power and power != 0:
            power = self.power
        if not ase_noise and ase_noise != 0:
            ase_noise = self.ase_noise
        if not nli_noise and nli_noise != 0:
            nli_noise = self.nli_noise
        self.power = power
        self.ase_noise = ase_noise
        self.nli_noise = nli_noise
        self.loc_in_to_state[loc] = {'power': power, 'ase_noise': ase_noise, 'nli_noise': nli_noise}

    def assoc_loc_out(self, loc, power=None, ase_noise=None, nli_noise=None):
        """
        Associate a location to signal performance values
        at the output interface of this point
        :param loc: location (i.e., node, span)
        :param power: power levels [mW]
        :param ase_noise: ase levels [mW]
        :param nli_noise: nli levels [mW]
        """
        if not power and power != 0:
            power = self.power
        if not ase_noise and ase_noise != 0:
            ase_noise = self.ase_noise
        if not nli_noise and nli_noise != 0:
            nli_noise = self.nli_noise
        self.power = power
        self.ase_noise = ase_noise
        self.nli_noise = nli_noise
        self.loc_out_to_state[loc] = {'power': power, 'ase_noise': ase_noise, 'nli_noise': nli_noise}

    def reset(self):
        self.power = self.power_start
        self.ase_noise = self.ase_noise_start
        self.nli_noise = self.nli_noise_start
        self.loc_in_to_state = {}
        self.loc_out_to_state = {}


SwitchRule = namedtuple('SwitchRule', 'in_port out_port signal_indices')


class Roadm(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """

    def __init__(self, name,
                 target_output_power_dB=0,
                 effective_output_power_dB=0,
                 reference_power=0, monitor_mode=None):
        """
        :param name:
        :param target_output_power_dB:
        :param effective_output_power_dB:
        :param reference_power:
        :param monitor_mode:
        """
        Node.__init__(self, name)
        # configuration attributes
        # dict of rule id to dict with keys in_port, out_port and signal_indices
        self.switch_table = {}
        # initialized for dynamic performance
        self.port_check_range_out = {}

        self.check_range_th = 2

        self.node_to_rule_id_in = {}
        self.rule_id_to_node_in = {}

        if monitor_mode:
            self.monitor = Monitor(name + "-monitor", component=self, mode=monitor_mode)

        self.target_output_power_dB = target_output_power_dB
        self.effective_output_power_dB = effective_output_power_dB
        self.reference_power = reference_power

    def monitor_query(self):
        if self.monitor:
            return self.monitor

    def install_switch_rule(self, in_port, out_port, signal_indices, src_node=None):
        """
        Switching rule installation, accessible from a Control System
        :param in_port: input port for incoming signals
        :param out_port: switching/output port for incoming signals
        :param signal_indices: signal indices involved in switching procedure
        :param src_node: source node
        :return:
        """
        # Used for update and delete rules
        self.node_to_rule_id_in.setdefault(src_node, [])
        # arbitrary rule identifier
        # the keys are tuples and the stored values int
        for signal_index in signal_indices:
            self.switch_table[in_port, signal_index] = out_port

            self.node_to_rule_id_in[src_node].append((in_port, signal_index))
            self.rule_id_to_node_in[in_port, signal_index] = src_node

    def update_switch_rule(self, rule_id, new_port_out, switch=False):
        """
        Update/create a new rule for switching
        :return:
        """
        # self.switch_table[in_port, signal_index]
        # Get the rule that corresponds to the rule_id
        if rule_id not in self.switch_table:
            pass
        else:
            in_port = rule_id[0]
            optical_signal = self.port_to_optical_signal_in[in_port]
            out_port = self.switch_table[rule_id]
            # remove signal from out port at a Node level
            self.remove_signal_from_out_port(out_port, optical_signal)

            # replace the out port of the rule (ROADM)
            self.switch_table[rule_id] = new_port_out

            if switch:
                src_node = self.rule_id_to_node_in[rule_id]
                self.switch(src_node, in_port)

    def delete_switch_rule(self, rule_id, switch=False):
        """
        Switching rule deletion from Control System
        :return:
        """
        # self.switch_table: [in_port, signal_index] = out_port
        if rule_id not in self.switch_table:
            pass
        else:
            in_port = rule_id[0]
            optical_signal = self.port_to_optical_signal_in[in_port]

            # Remove signal at Node level
            self.remove_optical_signal(optical_signal)
            # Remove switch rule
            del self.switch_table[rule_id]

            if switch:
                src_node = self.port_to_node_in[in_port]
                self.switch(src_node, in_port)

    def delete_switch_rules(self):
        """Delete all switching rules"""
        for ruleId in list(self.switch_table):
            self.delete_switch_rule(ruleId[0])

    def can_switch(self, in_port):
        # Track which out ports are going to carry which signals
        port_to_optical_signal_out = {}
        port_out_to_port_in_signals = {}
        # First check if there are switch rules, and store
        # the out ports that would be used in any case
        for optical_signal in self.port_to_optical_signal_in[in_port]:
            # checking if there is a rule for each signal
            switch_rule = False
            for rule_id, out_port in self.switch_table.items():
                if rule_id[0] == in_port and rule_id[1] == optical_signal.index:
                    # found a match of in_port and signal index
                    switch_rule = True

                    # keep track of which signals would be switched at this out port
                    port_to_optical_signal_out.setdefault(out_port, [])
                    port_to_optical_signal_out[out_port].append(optical_signal)

                    # keep track of which signals would be switched at this outport, and
                    # what is the in_port of these signals
                    port_out_to_port_in_signals.setdefault(out_port, {})
                    port_out_to_port_in_signals[out_port].setdefault(in_port, [])
                    port_out_to_port_in_signals[out_port][in_port].append(optical_signal)
            if not switch_rule:
                print(self, "Unable to find switch rule for signal:", optical_signal)

        # Note: this procedures is not checking for
        # ALL the other output ports, only the output ports
        # used by the switching rules found for the input port.
        port_to_optical_signal_out_copy = port_to_optical_signal_out.copy()
        # include all other signals at each out port (for switching)
        for out_port, optical_signals in port_to_optical_signal_out_copy.items():
            for optical_signal in self.port_to_optical_signal_out[out_port]:
                # checking which other signals are at this out port
                if optical_signal not in optical_signals:
                    port_to_optical_signal_out[out_port].append(optical_signal)
                    in_port = self.optical_signal_to_port_in[optical_signal]
                    # the input ports can be different
                    port_out_to_port_in_signals[out_port].setdefault(in_port, [])
                    port_out_to_port_in_signals[out_port][in_port].append(optical_signal)

        # now we check if we can switch
        port_to_optical_signal_out_copy = port_to_optical_signal_out.copy()
        # this if-clause is in case there is not a single switch rule
        if len(port_to_optical_signal_out) > 0:
            for out_port, optical_signals in port_to_optical_signal_out_copy.items():
                # check if optical_signals == self.port_to_optical_signal_out[out_port]
                if all(optical_signal in optical_signals for optical_signal in
                       self.port_to_optical_signal_out[out_port]) \
                        and len(optical_signals) == len(self.port_to_optical_signal_out[out_port]):
                    # If this is the case, then we have routed them before,
                    # thus, check the switching counter threshold
                    self.port_check_range_out[out_port] += 1
                    if self.port_check_range_out[out_port] >= self.check_range_th:
                        if not isinstance(self.port_to_node_out[out_port], LineTerminal):
                            print('RoadmWarning:', self, "loop detected. Stopping propagation.")
                            print("Blocking:", port_to_optical_signal_out[out_port], "port:", out_port)
                            # Disable the usage of this output port
                            del port_to_optical_signal_out[out_port]
                            del port_out_to_port_in_signals[out_port]
                else:
                    # The out port can be used
                    self.port_check_range_out[out_port] = 0
        return port_to_optical_signal_out, port_out_to_port_in_signals

    def can_switch_from_lt(self, src_node):
        """
        What I want to do is to be sure that when calling switch() for signals coming from
        a LineTerminal all INPUT PORTS are being checked. Otherwise not all signals will be checked

        Partly, this can be solved at can_switch()
        """
        port_to_optical_signal_out = {}
        port_out_to_port_in_signals = {}
        for in_port in self.node_to_port_in[src_node]:
            if len(self.port_to_optical_signal_in[in_port]) > 0:
                tmp_port_to_optical_signal_out, tmp_port_out_to_port_in_signals = self.can_switch(in_port)

                for out_port, optical_signals in tmp_port_to_optical_signal_out.items():
                    port_to_optical_signal_out.setdefault(out_port, [])
                    for optical_signal in optical_signals:
                        if optical_signal not in port_to_optical_signal_out[out_port]:
                            port_to_optical_signal_out[out_port].append(optical_signal)

                for out_port, _dict in tmp_port_out_to_port_in_signals.items():
                    port_out_to_port_in_signals.setdefault(out_port, {})
                    port_out_to_port_in_signals[out_port].update(_dict)
        return port_to_optical_signal_out, port_out_to_port_in_signals

    def switch(self, in_port, src_node):
        if isinstance(src_node, LineTerminal):
            # need to check for all (possible) input ports coming from LineTerminal
            port_to_optical_signal_out, port_out_to_port_in_signals = self.can_switch_from_lt(src_node)
        else:
            port_to_optical_signal_out, port_out_to_port_in_signals = self.can_switch(in_port)
        # we will propagate and route signals at each out port individually
        for out_port, in_port_signals in port_out_to_port_in_signals.items():
            # we need to pass all the signals at a given in port to compute
            # the carrier's attenuation in self.propagate()
            for in_port, optical_signals in in_port_signals.items():
                self.propagate(out_port, in_port, optical_signals)
            self.route(out_port)

    def compute_carrier_attenuation(self, in_port):
        """
        Compute the total power at an input port, and
        use it to compute the carriers attenuation
        AD: Should this be a function of the ROADM or the Node class?
        """
        carriers_power = []
        for optical_signal in self.port_to_optical_signal_in[in_port]:
            power_in = optical_signal.loc_in_to_state[self]['power']
            ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
            nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']

            total_power = power_in + ase_noise_in + nli_noise_in
            carriers_power.append(total_power)
        carriers_att = list(map(lambda x: abs_to_db(x * 1e3) - self.target_output_power_dB, carriers_power))
        exceeding_att = -min(list(filter(lambda x: x < 0, carriers_att)), default=0)
        carriers_att = list(map(lambda x: db_to_abs(x + exceeding_att), carriers_att))

        return carriers_att

    def propagate(self, out_port, in_port, optical_signals):
        self.effective_output_power_dB = min(self.reference_power, self.target_output_power_dB)
        self.effective_loss = self.reference_power - self.target_output_power_dB
        carriers_att = self.compute_carrier_attenuation(in_port)

        link = self.port_to_link_out[out_port]
        for i, optical_signal in enumerate(optical_signals):
            # attenuate signal power
            power_in = optical_signal.loc_in_to_state[self]['power']
            ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
            nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']

            power_out = power_in / carriers_att[i]
            ase_noise_out = ase_noise_in / carriers_att[i]
            nli_noise_out = nli_noise_in / carriers_att[i]

            # update the structures for that direction
            # all these signals are going towards the same out port
            link.include_optical_signal_in(optical_signal, power=power_out,
                                           ase_noise=ase_noise_out, nli_noise=nli_noise_out)
            dst_node = self.port_to_node_out[out_port]
            self.include_optical_signal_out(optical_signal, power=power_out,
                                            ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                                            out_port=out_port, dst_node=dst_node)

    def route(self, out_port):
        """Calling route will continue to propagate the signals in this link"""
        link = self.port_to_link_out[out_port]
        link.propagate(is_last_port=True)


class Amplifier(Node):

    def __init__(self, name, amplifier_type='EDFA', target_gain=17.6,
                 noise_figure=(5.5, 91), noise_figure_function=None,
                 bandwidth=32.0e9, wavelength_dependent_gain_id=None,
                 boost=False, monitor_mode=None, equalization_function=None,
                 equalization_target_out_power=0):
        """
        :param target_gain: units: dB - float
        :param noise_figure: tuple with NF value in dB and number of channels (def. 90)
        :param noise_figure_function: custom NF function with values in dB
        :param bandwidth: measurement optical bandwidth units: GHz - float
        :param wavelength_dependent_gain_id: file name id (see top of script) units: dB - string
        """
        Node.__init__(self, name)
        self.id = id(self)
        self.type = amplifier_type
        self.target_gain = target_gain
        self.system_gain = target_gain
        self.noise_figure = self.get_noise_figure(noise_figure, noise_figure_function)
        self.bandwidth = bandwidth
        self.wdgfunc = None
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

        if monitor_mode:
            self.monitor = Monitor(name + "-monitor", component=self, mode=monitor_mode)

        # When both flags are True system gain balancing is complete
        self.power_excursions_flag_1 = False
        self.power_excursions_flag_2 = False

        if equalization_function:
            self.equalization_attenuation = db_to_abs(3)
            self.equalization_function = equalization_function
            self.equalization_target_out_power = None
            self.equalization_compensation = \
                self.equalization_safety_check(equalization_function, equalization_target_out_power)
            self.equalization_flag_1 = True
            self.equalization_flag_2 = True
        else:
            self.equalization_flag_1 = False
            self.equalization_flag_2 = False

        self.boost = boost

    def monitor_query(self):
        if self.monitor:
            return self.monitor

    def equalization_safety_check(self, equalization_function, equalization_target_out_power):
        """
        AD: TO BE UPDATED.
        Safety check for the declaration of equalization reconfiguration parameters
        :param equalization_function: string (i.e., 'flatten')
        :param equalization_target_out_power: float
        :return: True equalization reconf False otherwise
        """
        if equalization_target_out_power is not None:
            # This check is to avoid pythonic-responses
            # if equalization_target_out_power is set to zero
            equalization_target_out_power = db_to_abs(equalization_target_out_power)
            self.equalization_target_out_power = equalization_target_out_power
        try:
            err_msg = "Roadm.equalization_safety_check: inconsistent declaration of equalization params."
            # Either both are passed or None
            assert all([equalization_function, equalization_target_out_power]) or \
                   all(x is None for x in [equalization_function, equalization_target_out_power]), err_msg
        except AssertionError as err:
            raise err
        if all([equalization_function, equalization_target_out_power]):
            return True
        return False

    def equalization_reconf(self, link, output_power_dict):
        """
        AD: TO BE UPDATED or removed, is this even used?
        wavelength dependent attenuation
        """
        pass
        # if self.equalization_function == 'flatten':
        #     # compute equalization compensation and re-propagate only if there is a function
        #     out_difference = {}
        #     for k, out_power in output_power_dict.items():
        #         # From the boost-amp, compute the difference between output power levels
        #         # and the target output power. Set this as the compensation function.
        #         delta = self.equalization_target_out_power / out_power
        #         out_difference[k] = delta
        #
        #     for optical_signal, equalization_att in out_difference.items():
        #         power = optical_signal.loc_in_to_state[self]['power'] * equalization_att
        #         ase_noise = optical_signal.loc_in_to_state[self]['ase_noise'] * equalization_att
        #         nli_noise = optical_signal.loc_in_to_state[self]['nli_noise'] * equalization_att
        #         self.include_optical_signal_in((optical_signal, optical_signal.uid), power=power,
        #                                        ase_noise=ase_noise, nli_noise=nli_noise)

    def reset_gain(self):
        self.system_gain = self.target_gain

    def power_excursions_flags_off(self):
        self.power_excursions_flag_1 = False
        self.power_excursions_flag_2 = False

    def load_wavelength_dependent_gain(self, wavelength_dependent_gain_id):
        """
        :param wavelength_dependent_gain_id: file name id (see top of script) - string
        :return: Return wavelength dependent gain array
        """
        if wavelength_dependent_gain_id is None:
            ripple_functions.keys()
            k = random.choice(list(ripple_functions.keys()))
            self.wdgfunc = k
            wavelength_dependent_gain_id = k
        return ripple_functions[wavelength_dependent_gain_id]

    def set_ripple_function(self, wavelength_dependent_gain_id):
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

    def get_wavelength_dependent_gain(self, signal_index):
        """
        Retrieve WDG by signal index
        :param signal_index:
        :return: WDG of signal
        """
        return self.wavelength_dependent_gain[signal_index - 1]

    @staticmethod
    def get_noise_figure(noise_figure, noise_figure_function):
        """
        If noise figure is not passed as a function, create one
        with constant values from established NF (default value is 6 dB)
        :param noise_figure: tuple with NF value in dB and number of channels (def. 90)
        :param noise_figure_function: custom NF function with values in dB
        :return:
        """
        if noise_figure is not None:
            dict_noise_figure = {}
            for i in range(1, noise_figure[1]):
                dict_noise_figure[i] = noise_figure[0]
            return dict_noise_figure
        elif noise_figure_function is not None:
            return noise_figure_function
        else:
            raise Exception("Amplifier.get_noise_figure: couldn't retrieve noise figure as a function.")

    def propagate(self):
        return

    def output_amplified_power(self, optical_signal, dst_node=None):
        """
        Compute the output power levels of each signal after amplification
        :param optical_signal: signal object
        :param dst_node: dst_node
        """
        # process output power
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        # Conversion from dB to linear
        system_gain_linear = db_to_abs(self.system_gain)
        wavelength_dependent_gain_linear = db_to_abs(wavelength_dependent_gain)
        input_power = optical_signal.loc_in_to_state[self]['power']
        output_power = input_power * system_gain_linear * \
                       wavelength_dependent_gain_linear

        # associate amp to optical signal at output interface
        # and update the optical signal state (power)
        self.include_optical_signal_out(optical_signal, power=output_power,
                                        out_port=0, dst_node=dst_node)

        return output_power

    def nli_compensation(self, optical_signal, dst_node=None):
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        # Conversion from dB to linear
        system_gain_linear = db_to_abs(self.system_gain)
        wavelength_dependent_gain_linear = db_to_abs(wavelength_dependent_gain)

        # the NLI noise als gets affected
        nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']
        nli_noise_out = nli_noise_in * system_gain_linear * wavelength_dependent_gain_linear

        # print("attempt to update at amplifier with nli noise", nli_noise_out)
        self.include_optical_signal_out(optical_signal,
                                        nli_noise=nli_noise_out, out_port=0, dst_node=dst_node)

    def stage_amplified_spontaneous_emission_noise(self, optical_signal, dst_node=None):
        """
        :return:
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """
        # Set parameters needed for ASE model
        noise_figure_linear = db_to_abs(self.noise_figure[optical_signal.index])
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        system_gain = self.system_gain

        ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
        gain_linear = db_to_abs(system_gain)  # * db_to_abs(wavelength_dependent_gain)
        ase_noise_out = ase_noise_in * gain_linear + (noise_figure_linear * h * optical_signal.frequency *
                                                      self.bandwidth * (gain_linear - 1))
        # associate amp to optical signal at output interface
        # and update the optical signal state (power)
        self.include_optical_signal_out(optical_signal,
                                        ase_noise=ase_noise_out, out_port=0, dst_node=dst_node)

    def compute_power_excursions(self):
        """
        TO BE UPDATED
        Balance system gain with respect with the mean
        gain of the signals in the amplifier: power excursions
        :return:
        """
        # optical_signals_in = self.port_to_optical_signal_in[0]
        #
        # output_power_target_dBm = []
        # output_power_real_dBm = []
        # for optical_signal_tuple in optical_signals_in:
        #     # compute output_power * target gain for all signals
        #     optical_signal = optical_signal_tuple[0]
        #     output_power_dBm = abs_to_db(optical_signal.loc_in_to_state[self]['power'] * db_to_abs(self.target_gain))
        #     output_power_target_dBm.append(output_power_dBm)
        #
        #     output_power_real_dBm.append(abs_to_db(optical_signal.loc_out_to_state[self]['power']))
        #
        # # compute power excursions using the means
        # power_excursions = np.mean(output_power_target_dBm) - np.mean(output_power_real_dBm)
        # update EDFA system gain
        # self.system_gain += power_excursions

        # Flag-check for enabling the repeated computation of balancing
        if self.power_excursions_flag_1 and (not self.power_excursions_flag_2):
            self.power_excursions_flag_2 = True
        if not (self.power_excursions_flag_1 and self.power_excursions_flag_2):
            self.power_excursions_flag_1 = True

    def clean_optical_signals(self):
        return

    def __repr__(self):
        """String representation"""
        return '<%s %.1fdB>' % (self.name, self.target_gain)

    # ADDITIONS FOR OFC DEMO USE-CASES
    def mock_amp_gain_adjust(self, new_gain):
        self.target_gain = new_gain
        self.system_gain = new_gain


class Monitor(Node):
    """
    This implementation of Monitors could be used for ROADMs and Amplifiers.
    """

    def __init__(self, name, component, mode='out'):
        """
        :param name: name of the monitor.
        :param component: Node object currently ROADM and Amplifiers.
        :param mode: The power values to extracted from input or output mode
        """
        Node.__init__(self, name)
        self.node_id = id(self)
        self.component = component
        self.mode = mode

    def modify_mode(self, mode='out'):
        """Change the monitoring interface;
        options are 'in' and 'out'"""
        self.mode = mode

    def get_optical_signals(self):
        """
        :return power: Returns Optical signals for the required objects
        """
        if self.mode == 'in':
            in_signals = []
            for _list in list(self.component.port_to_optical_signal_in.values()):
                for optical_signal in _list:
                    in_signals.append(optical_signal)
            return in_signals
        else:
            out_signals = []
            for _list in list(self.component.port_to_optical_signal_out.values()):
                for optical_signal in _list:
                    out_signals.append(optical_signal)
            return out_signals

    def get_list_osnr(self):
        """
        Get the OSNR values at this OPM as a list of tuples (optical signal, OSNR)
        """
        ordered_signals = sorted(self.get_optical_signals(), key=lambda s: s.index)
        return [(optical_signal, self.get_osnr(optical_signal))
                for optical_signal in ordered_signals]

    def get_dict_osnr(self):
        """
        Get the OSNR values at this OPM as a dictionary {optical signal: OSNR}
        """
        return {sigtuple[0]: self.get_osnr(sigtuple)
                for sigtuple in self.get_optical_signals()}

    def get_list_gosnr(self):
        """
        Get the gOSNR values at this OPM as a list of tuples (optical signal, gOSNR)
        """
        ordered_signals = sorted(self.get_optical_signals(), key=lambda s: s.index)
        return [(optical_signal, self.get_gosnr(optical_signal))
                for optical_signal in ordered_signals]

    def get_dict_gosnr(self):
        """
        Get the gOSNR values at this OPM as a dictionary {optical signal: gOSNR}
        """
        return {sigtuple[0]: self.get_gosnr(sigtuple)
                for sigtuple in self.get_optical_signals()}

    def get_ber(self, ber_method=None):
        """
        AD: We need to check this function
        Get's the bit error rate based on gOSNR
        :return: BitErrorRate at this OPM
        Calculates Bit Error Rate based on equations from F. Forghieri
        doi: 10.1109/JLT.1012.2.2189198
        """
        gosnr = self.get_list_gosnr()
        ber = ber_method
        if ber_method == 'bpsk':
            ber = 0.5 * erfc(sqrt(gosnr[0]))
        if ber_method == 'qpsk':
            ber = 0.5 * erfc(sqrt(gosnr[0] / 2))
        if ber_method == '8psk':
            ber = (2 / 3) * erfc(sqrt((3 / 14) * gosnr[0]))
        if ber_method == '16psk':
            ber = (3 / 8) * erfc(sqrt(gosnr[0]) / 10)
        return ber

    def get_dict_power(self):
        """
        Get the power values at this OPM as a dict
        """
        return {sigtuple[0]: self.get_power(sigtuple)
                for sigtuple in self.get_optical_signals()}

    def get_power(self, optical_signal):
        if self.mode == 'out':
            power = optical_signal.loc_out_to_state[self.component]['power']
        else:
            power = optical_signal.loc_in_to_state[self.component]['power']
        return power

    def get_ase_noise(self, optical_signal):
        if self.mode == 'out':
            ase_noise = optical_signal.loc_out_to_state[self.component]['ase_noise']
        else:
            ase_noise = optical_signal.loc_in_to_state[self.component]['ase_noise']
        return ase_noise

    def get_nli_noise(self, optical_signal):
        if self.mode == 'out':
            nli_noise = optical_signal.loc_out_to_state[self.component]['nli_noise']
        else:
            nli_noise = optical_signal.loc_in_to_state[self.component]['nli_noise']
        return nli_noise

    def get_osnr(self, optical_signal):
        """
        Compute OSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :return: OSNR (linear)
        """
        if self.mode == 'out':
            power = optical_signal.loc_out_to_state[self.component]['power']
            ase_noise = optical_signal.loc_out_to_state[self.component]['ase_noise']
        else:
            power = optical_signal.loc_in_to_state[self.component]['power']
            ase_noise = optical_signal.loc_in_to_state[self.component]['ase_noise']
        osnr_linear = power / ase_noise
        osnr = abs_to_db(osnr_linear)
        return osnr

    def get_gosnr(self, optical_signal):
        """
        Compute gOSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :return: gOSNR (linear)
        """
        if self.mode == 'out':
            output_power = optical_signal.loc_out_to_state[self.component]['power']
            ase_noise = optical_signal.loc_out_to_state[self.component]['ase_noise']
            nli_noise = optical_signal.loc_out_to_state[self.component]['nli_noise']
        else:
            output_power = optical_signal.loc_in_to_state[self.component]['power']
            ase_noise = optical_signal.loc_in_to_state[self.component]['ase_noise']
            nli_noise = optical_signal.loc_in_to_state[self.component]['nli_noise']

        gosnr_linear = output_power / (ase_noise + nli_noise)
        gosnr = abs_to_db(gosnr_linear) - (12.5e9 / optical_signal.symbol_rate)
        return gosnr

    def __repr__(self):
        return "<name: %s, component: %s, mode: %s>" % (
            self.name, self.component, self.mode)

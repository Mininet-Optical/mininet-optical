from units import *
from edfa_params import *
from terminal_params import *
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
        self.link_to_port_in = {}

        # static attributes - outputs
        self.ports_out = []
        self.port_to_node_out = {}
        self.node_to_port_out = {}
        self.port_to_link_out = {}

        # dynamic attributes - inputs
        self.port_to_optical_signal_in = {}
        self.optical_signal_to_port_in = {}

        # dynamic attributes - outputs
        self.port_to_optical_signal_out = {}
        self.optical_signal_to_port_out = {}

    def set_output_port(self, dst_node, link, output_port=-1):
        if output_port < 0:
            output_port = self.output_port_base
            self.output_port_base += 1
        else:
            self.output_port_base = output_port + 1

        # set static attributes
        self.ports_out.append(output_port)
        self.port_to_node_out[output_port] = dst_node
        self.port_to_link_out[output_port] = link

        # a node can have multiple
        # output ports to another node
        self.node_to_port_out.setdefault(dst_node, []).append(output_port)

        # initialize dynamic attributes
        self.port_to_optical_signal_out[output_port] = []
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
        self.link_to_port_in[link] = input_port

        # a node can have multiple input
        # ports from another node
        self.node_to_port_in.setdefault(src_node, []).append(input_port)

        # initialize dynamic attributes
        self.port_to_optical_signal_in[input_port] = []
        return input_port

    def include_optical_signal_in(self, optical_signal, power=None, ase_noise=None,
                                  nli_noise=None, in_port=None):
        """
        :param optical_signal: OpticalSignal object, OpticalSignal uid
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param in_port: input port of node (optional)
        """
        # update structures with the input ports of the current node
        self.port_to_optical_signal_in.setdefault(in_port, [])
        if optical_signal not in self.port_to_optical_signal_in[in_port]:
            # a port can carry multiple signals
            self.port_to_optical_signal_in[in_port].append(optical_signal)
            # for symmetry:
            self.optical_signal_to_port_in[optical_signal] = in_port

        # but we need to associate a component with the state of the signal
        optical_signal.assoc_loc_in(self, power, ase_noise, nli_noise)

    def include_optical_signal_out(self, optical_signal, power=None, ase_noise=None,
                                   nli_noise=None, out_port=None):
        """
        :param optical_signal: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param out_port: output port of node (optional)
        """
        if out_port is not None or out_port == 0:
            self.port_to_optical_signal_out.setdefault(out_port, [])
            if optical_signal not in self.port_to_optical_signal_out[out_port]:
                self.port_to_optical_signal_out[out_port].append(optical_signal)
                self.optical_signal_to_port_out[optical_signal] = out_port

        optical_signal.assoc_loc_out(self, power, ase_noise, nli_noise)

    def remove_optical_signal(self, optical_signal):
        print("*** %s removing: %s" % (self, optical_signal))

        if optical_signal in self.optical_signal_to_port_in:
            port_in = self.optical_signal_to_port_in[optical_signal]
            self.port_to_optical_signal_in[port_in].remove(optical_signal)

            del self.optical_signal_to_port_in[optical_signal]

        if optical_signal in self.optical_signal_to_port_out:
            port_out = self.optical_signal_to_port_out[optical_signal]
            self.port_to_optical_signal_out[port_out].remove(optical_signal)
            del self.optical_signal_to_port_out[optical_signal]
            if not isinstance(self, Amplifier):
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

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        """Human-readable representation"""
        return '%s' % self.name


class LineTerminal(Node):

    def __init__(self, name, transceivers=None, monitor_mode='out'):
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
        self.tx_to_channel = {}
        """rx_transceiver and channel will be used when enabling
        multiple channels on a single port"""
        self.rx_to_channel = {}

    def monitor_query(self):
        if self.monitor:
            return self.monitor

    def reset(self):
        """
        FIXME: (AD) This should reset all the dynamic attributes
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
        return transceiver.name in self.name_to_transceivers

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

    def set_modulation_format(self, transceiver, modulation_format, tx=False):
        """
        Update the modulation format of a transceiver
        :param transceiver: transmit transceiver object to configure
        :param modulation_format: string, i.e., '16_QAM' (see units.py)
        :return:
        """
        print("*** %s update modulation format of %s to: %s " %
              (self, transceiver.name, modulation_format))
        transceiver.set_modulation_format(modulation_format, tx)
        if tx:
            self.turn_on(safe_switch=True)

    def tx_config(self, transceiver, operational_power_dBm):
        """ Configure the operational power of the transceiver """
        transceiver.operation_power = db_to_abs(operational_power_dBm) * 1e-3

    def assoc_tx_to_channel(self, transceiver, channel, out_port=-1):
        """
        Configures a Terminal by
        associating a transmission (tx) transceiver to a channel (int);
        the out_port is previously defined at Network creation
        :param transceiver: transceiver to use for transmission
        :param channel: the channel to be transmitted
        :param out_port: input port to terminal, -1 if none.
        :return: associate a transceiver to an optical signal
        """
        # instantiate OpticalSignal object
        optical_signal = OpticalSignal(channel, transceiver.channel_spacing_H,
                                       transceiver.channel_spacing_nm,
                                       transceiver.modulation_format, transceiver.symbol_rate,
                                       transceiver.bits_per_symbol,
                                       power=transceiver.operation_power)

        # associate transceiver to optical_signal
        transceiver.assoc_optical_signal(optical_signal)

        dst_node = self.port_to_node_out[out_port]
        # the goal of this function
        self.include_optical_signal_out(optical_signal, out_port=out_port)
        self.tx_to_channel[out_port] = {'optical_signal': optical_signal, 'transceiver': transceiver}
        self.optical_signals_out += 1

    def disassoc_tx_to_channel(self, out_port):
        """
        Disassociate a transmitter transceiver (tx) to an output port
        """
        _dict = self.tx_to_channel[out_port]
        # remove optical_signal from LT and propagate deletion
        optical_signal = _dict['optical_signal']
        self.remove_optical_signal(optical_signal)

        # remove optical_signal from transceiver
        # and delete tx_to_channel register for out_port
        transceiver = _dict['transceiver']
        transceiver.remove_optical_signal()
        del self.tx_to_channel[out_port]
        self.optical_signals_out -= 1

    def assoc_rx_to_channel(self, transceiver, channel_id, in_port):
        """
        Associate a receiver transceiver (rx) to a signal at an input port
        :param transceiver: Transceiver object
        :param channel_id: int, channel index
        :param in_port: int, input port
        """
        self.rx_to_channel[in_port] = {'channel_id': channel_id, 'transceiver':transceiver}

    def disassoc_rx_to_channel(self, in_port):
        """
        Disassociate a receiver transceiver (rx) to an input port
        :param in_port: int, input port
        """
        del self.rx_to_channel[in_port]

    def turn_on(self, safe_switch=False):
        """Propagate signals to the link that the transceivers point to"""
        for signal_count, out_port in enumerate(self.tx_to_channel, start=1):
            optical_signal = self.tx_to_channel[out_port]['optical_signal']
            transceiver = self.tx_to_channel[out_port]['transceiver']
            transceiver.optical_signal.reset(component=self)

            # pass signal info to link
            link = self.port_to_link_out[out_port]
            link.include_optical_signal_in(optical_signal)

            if signal_count == self.optical_signals_out:
                link.propagate(is_last_port=True, safe_switch=safe_switch)
            else:
                link.propagate()

    def turn_off(self, ports_out):
        for out_port in ports_out:
            self.disassoc_tx_to_channel(out_port)
        # call propagation with left-over signals (if any)
        self.turn_on(safe_switch=True)

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
        :param optical_signal: OpticalSignal object
        :param in_port: int, input port
        """
        signalInfoDict = {optical_signal: {'osnr': None, 'gosnr': None,
                                           'ber': None, 'success': False}}

        if in_port in self.rx_to_channel:
            if self.rx_to_channel[in_port]['channel_id'] is optical_signal.index:
                rx_transceiver = self.rx_to_channel[in_port]['transceiver']
                # Get signal info
                power = optical_signal.loc_in_to_state[self]['power']
                ase_noise = optical_signal.loc_in_to_state[self]['ase_noise']
                nli_noise = optical_signal.loc_in_to_state[self]['nli_noise']

                # Compute OSNR and gOSNR
                osnr = self.osnr(power, ase_noise)
                gosnr = self.gosnr(power, ase_noise, nli_noise, optical_signal.symbol_rate)

                signalInfoDict[optical_signal]['osnr'] = osnr
                signalInfoDict[optical_signal]['gosnr'] = gosnr

                if gosnr < rx_transceiver.rx_threshold_dB:
                    print("*** %s receiving %s at port %s: Failure!\ngOSNR: %f dB - rx-thd:%s dB" %
                          (self.name, optical_signal, in_port,
                           gosnr, rx_transceiver.rx_threshold_dB))
                    print("OSNR: %f dB" % osnr)

                    signalInfoDict[optical_signal]['success'] = False
                    self.receiver_callback(in_port, signalInfoDict)
                else:
                    print("*** %s receiving %s at port %s: Success!\ngOSNR: %f dB" %
                          (self.name, optical_signal, in_port, gosnr))
                    print("OSNR: %f dB" % osnr)

                    signalInfoDict[optical_signal]['success'] = True
                    self.receiver_callback(in_port, signalInfoDict)
            else:
                self.receiver_callback(in_port, signalInfoDict)
                raise ValueError("@%s, optical signal: %s not configured for Rx in LineTerminal.\n"
                                 "Try calling %s.assoc_rx_to_channel() before launching transmission." %
                                 (self, optical_signal, self))
        else:
            self.receiver_callback(in_port, signalInfoDict)
            raise ValueError("@%s, input port: %s not configured correctly for "
                             "optical signal: %s in LineTerminal.\n"
                             "You can configure it with %s.assoc_rx_to_channel() before launching transmission." %
                             (self, in_port, optical_signal, self))

    def receiver_callback(self, in_port, signalDictInfo):
        return


class Transceiver(object):

    def __init__(self, tr_id, name, operation_power=0,
                 channel_spacing_nm=0.4 * 1e-9, channel_spacing_H=50e9,
                 bandwidth=2.99792458 * 1e9, modulation_format='16QAM',
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

        # state attributes
        self.optical_signal = None

    def assoc_optical_signal(self, optical_signal):
        self.optical_signal = optical_signal

    def remove_optical_signal(self):
        self.optical_signal = None

    def set_modulation_format(self, modulation_format, tx):
        """
        Update modulation format, bits per symbol, symbol rate and
        rx-threshold based on a modulation format label (i.e., 16QAM).
        :param modulation_format: string i.e., '16QAM' (see units.py)
        :param tx: boolean; True if transceiver is a transmitter
        """
        self.modulation_format = modulation_format
        self.bits_per_symbol = bps[modulation_format]
        self.symbol_rate = sr[modulation_format]
        self.rx_threshold_dB = rx_thresholds[modulation_format]
        if tx:
            self.optical_signal.set_modulation_format(modulation_format)

    def describe(self):
        pprint(vars(self))


class OpticalSignal(object):
    spectrum_band_init_nm = 1567.132556194459
    spectrum_band_init_H = 191.3e12

    def __init__(self, index, channel_spacing_H,
                 channel_spacing_nm, modulation_format,
                 symbol_rate, bits_per_symbol,
                 power=0, ase_noise=0, nli_noise=0):
        self.uid = id(self)
        # configuration attributes
        self.index = index
        self.frequency = self.spectrum_band_init_H + (channel_spacing_H * int(index))
        self.wavelength = c / self.frequency
        self.wavelength2 = self.spectrum_band_init_nm * nm + index * channel_spacing_nm
        self.modulation_format = modulation_format
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

    def reset(self, component=None):
        self.power = self.power_start
        self.ase_noise = self.ase_noise_start
        self.nli_noise = self.nli_noise_start
        if component:
            if component in self.loc_in_to_state:
                self.loc_in_to_state = {component: self.loc_in_to_state[component]}
            if component in self.loc_out_to_state:
                self.loc_out_to_state = {component: self.loc_out_to_state[component]}
        else:
            self.loc_in_to_state = {}
            self.loc_out_to_state = {}

    def set_modulation_format(self, modulation_format):
        self.modulation_format = modulation_format
        self.bits_per_symbol = bps[modulation_format]
        self.symbol_rate = sr[modulation_format]


SwitchRule = namedtuple('SwitchRule', 'in_port out_port signal_indices')


class Roadm(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """

    def __init__(self, name, insertion_loss_dB=17, reference_power_dBm=0,
                 preamp=None, boost=None, monitor_mode=None):
        """
        :param name: string, name tag of ROADM
        :param insertion_loss_dB: int, linear insertion loss of ROADM (default 17 dB)
        :param reference_power_dBm: int,
                                    reference power for ROADM-variable optical attenuator (VOA) - (default 0 dBm)
        :param preamp: Amplifier object
        :param boost: Amplifier object
        :param monitor_mode: Monitor object
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

        # By default ROADMs support up to 90 channels indexed 1-90
        channel_no = 90
        self.insertion_loss_dB = {k: insertion_loss_dB for k in range(1, channel_no + 1)}
        self.reference_power_dBm = {k: reference_power_dBm for k in range(1, channel_no + 1)}
        # expected output power of signals
        self.target_output_power_dBm = {k: self.reference_power_dBm[k] - self.insertion_loss_dB[k]
                                        for k in range(1, channel_no + 1)}

        self.preamp = preamp
        self.boost = boost

    def monitor_query(self):
        if self.monitor:
            return self.monitor

    def include_optical_signal_in_roadm(self, optical_signal, in_port):
        """
        Include optical signals in preamp if object exists, and include
        input signals at a Node level
        :param optical_signal: OpticalSignal object
        :param in_port: int, input port
        """
        if self.preamp:
            self.preamp.include_optical_signal_in(optical_signal, in_port=0)
        self.include_optical_signal_in(optical_signal,in_port=in_port)

    def install_switch_rule(self, in_port, out_port, signal_indices, src_node=None):
        """
        Switching rule installation, accessible from a Control System
        :param in_port: input port for incoming signals
        :param out_port: switching/output port for incoming signals
        :param signal_indices: int or list, signal index or indices
        :param src_node: source node
        :return:
        """
        # Used for update and delete rules
        self.node_to_rule_id_in.setdefault(src_node, [])
        # arbitrary rule identifier
        # the keys are tuples and the stored values int
        if type(signal_indices) is list or type(signal_indices) is set:
            for signal_index in signal_indices:
                self.switch_table[in_port, signal_index] = out_port

                self.node_to_rule_id_in[src_node].append((in_port, signal_index))
                self.rule_id_to_node_in[in_port, signal_index] = src_node
        else:
            self.switch_table[in_port, signal_indices] = out_port

            self.node_to_rule_id_in[src_node].append((in_port, signal_indices))
            self.rule_id_to_node_in[in_port, signal_indices] = src_node
        self.switch(in_port, src_node)


    def update_switch_rule(self, in_port, signal_index, new_port_out, switch=False):
        """
        Update/create a new rule for switching
        :param in_port: int, input port of existing rule
        :param signal_index: int, signal index of existing rule
        :param new_port_out: int, new output port
        :param switch: boolean, specify if we want to switch
                        to avoid unecessary switching checkups
                        in self.can_switch()
        """
        # Get the rule that corresponds to the rule_id
        if (in_port, signal_index) not in self.switch_table:
            print("*** %s.update_switch_rule couldn't find "
                  "switch rule for in_port: %d and channel: %d" %
                  (self, in_port, signal_index))
        else:
            for s in self.port_to_optical_signal_in[in_port]:
                if s.index == signal_index:
                    optical_signal = s
                    out_port = self.switch_table[in_port, signal_index]
                    # remove signal from out port at a Node level
                    self.remove_signal_from_out_port(out_port, optical_signal)

                    # replace the out port of the rule (ROADM)
                    self.switch_table[in_port, signal_index] = new_port_out

            if switch:
                src_node = self.rule_id_to_node_in[in_port, signal_index]
                self.switch(in_port, src_node)

    def delete_switch_rule(self, in_port, signal_index, switch=False):
        """
        Delete a switch rule from switch_table and remove the signal(s)
        associated with that rule at a Node level. Then switch.
        Switch rules are identified by in_port and signal_index
        :param in_port: int, input port associated with switch rule
        :param signal_index: int, signal index associated with switch rule
        :param switch: boolean, , specify if we want to switch
                        to avoid unecessary switching checkups
                        in self.can_switch()
        """
        # self.switch_table: [in_port, signal_index] = out_port
        if (in_port, signal_index) not in self.switch_table:
            print("*** %s.update_switch_rule couldn't find "
                  "switch rule for in_port: %d and channel: %d" %
                  (self, in_port, signal_index))
        else:
            for s in self.port_to_optical_signal_in[in_port]:
                if s.index == signal_index:
                    optical_signal = s
                    out_port = self.switch_table[in_port, signal_index]
                    # remove signal from out port at a Node level
                    self.remove_signal_from_out_port(out_port, optical_signal)
                    # Remove switch rule
                    del self.switch_table[in_port, signal_index]

            if switch:
                src_node = self.rule_id_to_node_in[in_port, signal_index]
                self.switch(in_port, src_node)

    def delete_switch_rules(self):
        """Delete all switching rules"""
        for ruleId in self.switch_table.keys():
            in_port = ruleId[0]
            signal_index = ruleId[1]
            self.delete_switch_rule(in_port, signal_index)

    def can_switch(self, in_port, safe_switch):
        """
        Check if switching is possible (i.e., no loops)
        :param in_port: int, input port triggering switching
        :param safe_switch: boolean, indicates whether it needs
                            to check for switch feasibility.
        """
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

        # Note: this procedure is not checking for
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

        if not safe_switch:
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

    def can_switch_from_lt(self, src_node, safe_switch):
        """
        Check all input ports for signals coming from a LineTerminal.
        :param src_node: LineTerminal object
        :param safe_switch: boolean, indicates whether it needs
                            to check for switch feasibility.
        """
        port_to_optical_signal_out = {}
        port_out_to_port_in_signals = {}
        if src_node in self.node_to_port_in:
            for in_port in self.node_to_port_in[src_node]:
                if len(self.port_to_optical_signal_in[in_port]) > 0:
                    tmp_port_to_optical_signal_out, tmp_port_out_to_port_in_signals = \
                        self.can_switch(in_port, safe_switch)

                    for out_port, optical_signals in tmp_port_to_optical_signal_out.items():
                        port_to_optical_signal_out.setdefault(out_port, [])
                        for optical_signal in optical_signals:
                            if optical_signal not in port_to_optical_signal_out[out_port]:
                                port_to_optical_signal_out[out_port].append(optical_signal)

                    for out_port, _dict in tmp_port_out_to_port_in_signals.items():
                        port_out_to_port_in_signals.setdefault(out_port, {})
                        port_out_to_port_in_signals[out_port].update(_dict)
        return port_to_optical_signal_out, port_out_to_port_in_signals

    def switch(self, in_port, src_node, safe_switch=False):
        """
        Check for switch feasibility
        Prepare switch internal configuration (i.e., preamp)
        Propagate (physical layer simulation)
        Route (relay signals to next Link)
        :param in_port: int, input port triggering switching
        :param src_node: LineTerminal, ROADM or Amplifier object
        :param safe_switch: boolean, indicates whether it needs
                            to check for switch feasibility.
        Note: check for switch feasibility unless performing tasks
            independent of switching (i.e., EDFA gain configuration).
        """
        if isinstance(src_node, LineTerminal):
            # need to check for all (possible) input ports coming from LineTerminal
            port_to_optical_signal_out, port_out_to_port_in_signals = self.can_switch_from_lt(src_node, safe_switch)
        else:
            port_to_optical_signal_out, port_out_to_port_in_signals = self.can_switch(in_port, safe_switch)

        self.prepropagation(port_out_to_port_in_signals, src_node)

        # we will propagate and route signals at each out port individually
        for out_port, in_port_signals in port_out_to_port_in_signals.items():
            # we need to pass all the signals at a given in port to compute
            # the carrier's attenuation in self.propagate()
            for in_port, optical_signals in in_port_signals.items():
                self.propagate(out_port, in_port, optical_signals)
            self.route(out_port, safe_switch)

    def prepropagation(self, port_out_to_port_in_signals, src_node):
        """
        Preparing structures for propagation
        :param port_out_to_port_in_signals: dict, hash of switch rules
        :param src_node: LineTerminal, ROADM or Amplifier object
        """
        for out_port, in_port_signals in port_out_to_port_in_signals.items():
            dst_node = self.port_to_node_out[out_port]
            if isinstance(dst_node, LineTerminal) or \
                    (self.preamp and not isinstance(src_node, LineTerminal)
                     and not isinstance(dst_node, LineTerminal)):
                for in_port, optical_signals in in_port_signals.items():
                    if self.preamp:
                        for optical_signal in optical_signals:
                            self.preamp.include_optical_signal_in(optical_signal)
                # we need to pass all the signals at a given in port to compute
                # the carrier's attenuation in self.propagate()
                for in_port, optical_signals in in_port_signals.items():
                    if self.preamp:
                        # need to process signal before switch-based propagation
                        self.preamp.propagate(optical_signals)

    def compute_carrier_attenuation(self, in_port, amp=None):
        """
        Compute the total power at an input port, and
        use it to compute the carriers attenuation
        :param in_port: int, input port for total power calculation
        :param amp: Amplifier object, if there are boost and preamp
                    the signals are contained within these objects
        """

        carriers_att = {}
        for optical_signal in self.port_to_optical_signal_in[in_port]:
            if amp:
                power_in = optical_signal.loc_out_to_state[amp]['power']
                ase_noise_in = optical_signal.loc_out_to_state[amp]['ase_noise']
                nli_noise_in = optical_signal.loc_out_to_state[amp]['nli_noise']
            else:
                power_in = optical_signal.loc_in_to_state[self]['power']
                ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
                nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']

            total_power = power_in + ase_noise_in + nli_noise_in
            carriers_att[optical_signal.index] = abs_to_db(total_power * 1e3) - \
                                                 self.target_output_power_dBm[optical_signal.index]

        exceeding_att = -min(list(filter(lambda x: x < 0, carriers_att.values())), default=0)
        for k, x in carriers_att.items():
            carriers_att[k] = db_to_abs(x + exceeding_att)

        return carriers_att

    def process_att(self, out_port, in_port, optical_signals, src_node, dst_node, link, amp=None):
        """
        Compute the attenuation effects at the ROADM
        :param out_port: int, output port (direction of signals)
        :param in_port: int, input port (direction of signals)
        :param optical_signals: list of optical signals
        :param src_node: LineTerminal or Amplifier object
        :param dst_node: LineTerminal or Amplifier object
        :param link: Link object (direction of signals)
        :param amp: Amplifier object, if there are boost and preamp
                    the signals are contained within these objects
        """
        # Compute per carrier attenuation
        carriers_att = self.compute_carrier_attenuation(in_port, amp=amp)

        for optical_signal in optical_signals:
            if amp:
                # attenuate signals at output interface of amp
                power_out = optical_signal.loc_out_to_state[amp]['power'] / carriers_att[optical_signal.index]
                ase_noise_out = optical_signal.loc_out_to_state[amp]['ase_noise'] / carriers_att[optical_signal.index]
                nli_noise_out = optical_signal.loc_out_to_state[amp]['nli_noise'] / carriers_att[optical_signal.index]
            else:
                # attenuate signals as they entered the ROADM (self)
                power_out = optical_signal.loc_in_to_state[self]['power'] / carriers_att[optical_signal.index]
                ase_noise_out = optical_signal.loc_in_to_state[self]['ase_noise'] / carriers_att[optical_signal.index]
                nli_noise_out = optical_signal.loc_in_to_state[self]['nli_noise'] / carriers_att[optical_signal.index]

            if self.boost and not isinstance(dst_node, LineTerminal):
                # need to pass signals to boost for processing
                self.boost.include_optical_signal_in(optical_signal, power=power_out,
                                                     ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                                                     in_port=0)
            else:
                # update the structures for that direction
                # all these signals are going towards the same out port
                link.include_optical_signal_in(optical_signal, power=power_out,
                                               ase_noise=ase_noise_out, nli_noise=nli_noise_out)
                self.include_optical_signal_out(optical_signal, power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                                                out_port=out_port)

        if self.boost and not isinstance(dst_node, LineTerminal):
            # process boost amp
            self.boost.propagate(optical_signals)

            # pass signals to link and update state at ROADM (self)
            for i, optical_signal in enumerate(optical_signals):
                power_out = optical_signal.loc_out_to_state[self.boost]['power']
                ase_noise_out = optical_signal.loc_out_to_state[self.boost]['ase_noise']
                nli_noise_out = optical_signal.loc_out_to_state[self.boost]['nli_noise']

                # update the structures for that direction
                # all these signals are going towards the same out port
                link.include_optical_signal_in(optical_signal, power=power_out,
                                               ase_noise=ase_noise_out, nli_noise=nli_noise_out)
                self.include_optical_signal_out(optical_signal, power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                                                out_port=out_port)

    def propagate(self, out_port, in_port, optical_signals):
        """
        Compute physical layer simulation for one direction given by the out_port
        :param out_port: int, output port (direction of signals)
        :param in_port: int, input port (direction of signals)
        :param optical_signals: list of optical signals
        """
        src_node = self.port_to_node_in[in_port]
        dst_node = self.port_to_node_out[out_port]
        link = self.port_to_link_out[out_port]

        if isinstance(dst_node, LineTerminal) or \
                    (self.preamp and not isinstance(src_node, LineTerminal)
                     and not isinstance(dst_node, LineTerminal)):
            self.process_att(out_port, in_port, optical_signals, src_node, dst_node, link, amp=self.preamp)
        else:
            self.process_att(out_port, in_port, optical_signals, src_node, dst_node, link)


    def route(self, out_port, safe_switch):
        """Calling route will continue to propagate the signals in this link
        :param out_port: int, output port indicating direction
        :param safe_switch: boolean, indicates whether it needs
                            to check for switch feasibility.
        """
        link = self.port_to_link_out[out_port]
        link.propagate(is_last_port=True, safe_switch=safe_switch)

    def set_boost_gain(self, gain_dB):
        """
        Configure the gain of the boost amplifier
        and call fast_switch()
        :param gain_dB: int or float, gain to set
        """
        self.boost.set_gain(gain_dB)
        self.fast_switch()

    def set_preamp_gain(self, gain_dB):
        """
        Configure the gain of the preamp amplifier
        and call fast_switch()
        :param gain_dB: int or float, gain to set
        """
        self.preamp.set_gain(gain_dB)
        self.fast_switch()

    def set_reference_power(self, ref_power_dBm, ch_index=None):
        """
        Configure the reference power for ROADM to act upon,
        similar to setting a VOA reference power.
        and call fast_switch()
        :param gain_dB: int or float, gain to set
        """
        if ch_index or ch_index == 1:
            self.target_output_power_dBm[ch_index] = ref_power_dBm - self.insertion_loss_dB[ch_index]
        else:
            for i, x in self.target_output_power_dBm.items():
                self.target_output_power_dBm[i] = ref_power_dBm - self.insertion_loss_dB[i]
        self.fast_switch()

    def fast_switch(self):
        """
        Call switch for all switching rules with safe_switch=True
        """
        for component, rule_list in self.node_to_rule_id_in.items():
            # it's just necessary to pass one in_port to the switch
            # function, since safe_switch is passed as True
            in_port = rule_list[0][0]
            self.switch(in_port, component, safe_switch=True)


class Amplifier(Node):

    def __init__(self, name, amplifier_type='EDFA', target_gain=17.6,
                 noise_figure=(5.5, 91), noise_figure_function=None,
                 bandwidth=32.0e9, wavelength_dependent_gain_id=None,
                 preamp=False, boost=False, monitor_mode=None):
        """
        :param amplifier_type: OBSOLETE; kept for backwards compatibility
        :param target_gain: units: dB - float
        :param noise_figure: tuple with NF value in dB and number of channels (def. 90)
        :param noise_figure_function: custom NF function with values in dB
        :param bandwidth: measurement optical bandwidth units: GHz - float
        :param wavelength_dependent_gain_id: file name id (see top of script) units: dB - string
        :param preamp: OBSOLETE; kept for backwards compatibility
        :param boost: OBSOLETE; kept for backwards compatibility
        """
        Node.__init__(self, name)
        self.target_gain = target_gain
        self.system_gain = target_gain
        self.noise_figure = self.get_noise_figure(noise_figure, noise_figure_function)
        self.bandwidth = bandwidth
        wavelength_dependent_gain_id = 'linear'
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

        if monitor_mode:
            self.monitor = Monitor(name + "-monitor", component=self, mode=monitor_mode)

        # When both flags are True system gain balancing is complete
        self.power_excursions_flag_1 = False
        self.power_excursions_flag_2 = False

        self.prev_component = None
        self.next_component = None
        self.link = None

    def monitor_query(self):
        if self.monitor:
            return self.monitor

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

    def output_amplified_power(self, optical_signal):
        """
        Compute the output power levels of each signal after amplification
        :param optical_signal: signal object
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
                                        out_port=0)

        return output_power

    def nli_compensation(self, optical_signal):
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        # Conversion from dB to linear
        system_gain_linear = db_to_abs(self.system_gain)
        wavelength_dependent_gain_linear = db_to_abs(wavelength_dependent_gain)

        # the NLI noise als gets affected
        nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']
        nli_noise_out = nli_noise_in * system_gain_linear * wavelength_dependent_gain_linear

        self.include_optical_signal_out(optical_signal,
                                        nli_noise=nli_noise_out, out_port=0)

    def stage_amplified_spontaneous_emission_noise(self, optical_signal):
        """
        :return:
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """
        # Set parameters needed for ASE model
        noise_figure_linear = db_to_abs(self.noise_figure[optical_signal.index])
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        system_gain = self.system_gain

        ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
        gain_linear = db_to_abs(system_gain) * db_to_abs(wavelength_dependent_gain)
        ase_noise_out = ase_noise_in * gain_linear + (noise_figure_linear * h * optical_signal.frequency *
                                                      self.bandwidth * (gain_linear - 1))
        # associate amp to optical signal at output interface
        # and update the optical signal state (power)
        self.include_optical_signal_out(optical_signal,
                                        ase_noise=ase_noise_out, out_port=0)

    def compute_power_excursions(self):
        """
        FIXME: fix algorithm based on new model
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

    def propagate(self, optical_signals, is_last_port=False, safe_switch=False):
        """
        Compute the amplification process
        :param optical_signals: list
        """
        # Enabling balancing check
        while not (self.power_excursions_flag_1 and self.power_excursions_flag_2):
            for optical_signal in optical_signals:
                self.output_amplified_power(optical_signal)
            self.compute_power_excursions()
        # Reset balancing flags to original settings
        self.power_excursions_flags_off()

        # Compute for the power
        for optical_signal in optical_signals:
            self.nli_compensation(optical_signal)
            # Compute ASE noise generation
            self.stage_amplified_spontaneous_emission_noise(optical_signal)

            if self.next_component:
                power_out = optical_signal.loc_out_to_state[self]['power']
                ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise']
                nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise']

                if isinstance(self.next_component, LineTerminal):
                    in_port = self.next_component.link_to_port_in[self.link]
                    self.next_component.include_optical_signal_in(
                        optical_signal, power=power_out,
                        ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                        in_port=in_port)
                    self.next_component.receiver(optical_signal, in_port)
                elif isinstance(self.next_component, Roadm):
                    in_port = self.next_component.link_to_port_in[self.link]
                    self.next_component.include_optical_signal_in(
                        optical_signal, power=power_out,
                        ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                        in_port=in_port)
                else:
                    self.next_component.include_optical_signal_in(
                        optical_signal, power=power_out,
                        ase_noise=ase_noise_out, nli_noise=nli_noise_out)

        if self.next_component:
            if self.next_component.__class__.__name__ == 'Span':
                self.next_component.propagate(is_last_port=is_last_port, safe_switch=safe_switch)
            elif isinstance(self.next_component, Roadm):
                self.next_component.switch(in_port, self.link.src_node, safe_switch=safe_switch)

    def set_gain(self, gain_dB):
        self.system_gain = gain_dB
        self.target_gain = gain_dB

        if 0 in self.port_to_optical_signal_in:
            optical_signals = self.port_to_optical_signal_in[0]
            self.propagate(optical_signals, is_last_port=True, safe_switch=True)


    def __repr__(self):
        """String representation"""
        return '<%s %.1fdB>' % (self.name, self.target_gain)

    # FIXME: (AD) This will change
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
            optical_signal_list = []
            for value in self.component.port_to_optical_signal_in.values():
                if value:
                    for optical_signal in value:
                        if self.component in optical_signal.loc_in_to_state:
                            optical_signal_list.append(optical_signal)
            return optical_signal_list
        else:
            optical_signal_list = []
            for value in self.component.port_to_optical_signal_out.values():
                if value:
                    for optical_signal in value:
                        if self.component in optical_signal.loc_out_to_state:
                            optical_signal_list.append(optical_signal)
            return optical_signal_list

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
        return {signal: self.get_osnr(signal)
            for signal in self.get_optical_signals()}

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
        return {signal: self.get_gosnr(signal)
            for signal in self.get_optical_signals()}

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
        if ase_noise != 0:
            osnr_linear = power / ase_noise
        else:
            osnr_linear = 1
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

        if ase_noise != 0 and nli_noise != 0:
            gosnr_linear = output_power / (ase_noise + nli_noise)
        else:
            gosnr_linear = 1
        gosnr = abs_to_db(gosnr_linear) - (12.5e9 / optical_signal.symbol_rate)
        if gosnr < 0:
            gosnr = 0
        return gosnr

    def __repr__(self):
        return "<name: %s, component: %s, mode: %s>" % (
            self.name, self.component, self.mode)

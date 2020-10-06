import units as unit
from pprint import pprint
import numpy as np
import scipy.constants as sc
import random
from collections import namedtuple


def db_to_abs(db_value):
    """
    :param db_value: list or float
    :return: Convert dB to absolute value
    """
    absolute_value = 10 ** (db_value / float(10))
    return absolute_value


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10 * np.log10(absolute_value)
    return db_value


def common_entries(*dcts):
    """
    Helper function
    Creates a generator object that can be set as a list
    when invoked, and will be a list of tuples in the form of
    [(common_key, value_dict1, value_dict2), ...]
    """
    for i in set(dcts[0]).intersection(*dcts[1:]):
        yield (i,) + tuple(d[i] for d in dcts)


class Node(object):
    input_port_base = 0
    output_port_base = 0

    def __init__(self, name):
        self.name = name
        self.ports_in = []
        self.ports_out = []  # are these needed/used?
        self.port_to_node_in = {}  # dict of port no. to ingress connecting nodes
        self.port_to_node_out = {}  # dict of port no. to egress connecting nodes
        self.port_to_optical_signal_in = {}  # dict of ports to input signals
        self.port_to_optical_signal_out = {}  # dict of ports to output signals
        self.out_port_to_link = {}

        self.optical_signals = []

    def new_output_port(self, connected_node, portnum=None):
        """
        Create a new output port for a node
        to connect to another node
        :param connected_node:
        :param portnum:
        :return: new output port
        """
        if portnum:
            assert portnum not in self.ports_out
            new_output_port = portnum
        else:
            if self.ports_out:
                new_output_port = max(self.ports_out) + 1
            else:
                new_output_port = self.output_port_base
        # Enable discovery of output ports
        self.ports_out.append(new_output_port)
        # Enable discovery of connected node through output port
        self.port_to_node_out[new_output_port] = connected_node
        # Enable monitoring of signals at output port
        self.port_to_optical_signal_out[new_output_port] = []
        return new_output_port

    def new_input_port(self, connected_node, portnum=None):
        """
        Create a new input port for a node
        to connect to another node
        :param connected_node:
        :param portnum:
        :return: new input port
        """
        if portnum is not None:
            assert portnum not in self.ports_in
            new_input_port = portnum
        else:
            if self.ports_in:
                new_input_port = max(self.ports_in) + 1
            else:
                new_input_port = self.input_port_base
        # Enable discovery of input ports
        self.ports_in.append(new_input_port)
        # Enable discovery of connected node through input port
        self.port_to_node_in[new_input_port] = connected_node
        # Enable monitoring of signals at input port
        self.port_to_optical_signal_in[new_input_port] = []
        return new_input_port

    def include_optical_signal(self, optical_signal, power=None, ase_noise=None, nli_noise=None, in_port=None):
        """
        Include optical signal in optical_signals
        :param optical_signal: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param in_port: input port of node (optional)
        """
        if optical_signal not in self.optical_signals:
            self.optical_signals.append(optical_signal)
        optical_signal.assoc_loc_in(self, power, ase_noise, nli_noise)

        if in_port:
            self.port_to_optical_signal_in[in_port] = optical_signal

    def describe(self):
        pprint(vars(self))

    def print_signals(self, names=(('input', 'input'), ('output', 'output'))):
        """
        obsolete?
        Debugging: print input and output signals
        """
        print(self, "signals:")
        # signal_map = {
        #     'input': self.port_to_optical_signal_power_in,
        #     'output': self.port_to_optical_signal_power_out}
        # for direction, name in names:
        #     port_signals = signal_map[direction]
        #     for port in sorted(port_signals):
        #         signal_powers = port_signals[port]
        #         if signal_powers:
        #             print(name, '%s:' % port, end='')
        #             for signal, power in signal_powers.items():
        #                 print('%s@%.1fdBm' % (signal, abs_to_db(power)), end=' ')
        #             print()

    def __repr__(self):
        """Human-readable representation"""
        return '%s' % self.name


class LineTerminal(Node):

    def __init__(self, name, transceivers=None, monitor_mode=None):
        Node.__init__(self, name)
        # list of transceivers in LineTerminal
        self.transceivers = []
        # dict of name of transceiver to transceiver objects
        self.name_to_transceivers = {}
        self.signal_info_dict_transceiver = {}  # what is this? used in receiver, but, is it needed?

        if monitor_mode:
            self.monitor = Monitor(name + "-opm", component=self, mode=monitor_mode)

        if transceivers:
            self.add_transceivers(transceivers)

    def reset(self):
        # clean output ports
        for out_port, _ in self.port_to_optical_signal_out.items():
            self.port_to_optical_signal_out[out_port] = []
        # clean input ports
        for in_port, _ in self.port_to_optical_signal_in.items():
            self.port_to_optical_signal_in[in_port] = []

        self.optical_signals = []

        for out_port, link in self.out_port_to_link.items():
            link.reset_propagation_struct()

    def add_transceivers(self, transceivers):
        """
        For-loop for adding transceivers to LT
        :param transceivers: list of tuples (t_name, operational_power, spectrum band)
        :return:
        """
        for _tuple in transceivers:
            self.add_transceiver(_tuple[0], _tuple[1], _tuple[2])

    def add_transceiver(self, transceiver_name, operational_power, spectrum_band):
        """
        Add a new transceiver to the OLT
        :param transceiver_name: name of transceiver to add
        :param operational_power: name of transceiver to add
        :param spectrum_band: spectrum band to function
        :return: added transceiver
        """
        if transceiver_name in self.name_to_transceivers:
            raise ValueError("Node.LineTerminal.add_transceiver: Transceiver with this name already exist!")
        # enable incremental id configuration
        transceiver_id = len(self.transceivers) + 1
        # instantiate the Transceiver object
        transceiver = Transceiver(transceiver_id, transceiver_name, operational_power, spectrum_band)
        # enable to retrieve Transceiver object by name
        self.name_to_transceivers[transceiver_name] = transceiver
        # add transceiver to LineTerminal list
        self.transceivers.append(transceiver)

    def update_transceiver(self, transceiver_name, args):
        """
        Update/modify the configuration attributes of a transceiver
        :param transceiver_name: transceiver to configure
        :param args: dict with parameters to update
        :return:
        """
        transceiver = self.name_to_transceivers[transceiver_name]
        transceiver.__dict__.update(args)
        if 'modulation_format' in args:
            transceiver.compute_gross_bit_rate()

    def delete_transceiver(self, transceiver_name):
        """
        Delete transceiver from OLT
        :param transceiver_name: name of transceiver to be deleted
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.LineTerminal.delete_transceiver: transceiver does not exist!")
        transceiver = self.name_to_transceivers[transceiver_name]
        self.transceivers.remove(transceiver)
        del self.name_to_transceivers[transceiver_name]

    def configure_terminal(self, transceiver, channel):
        """
        Program the channels that will be launched at transceivers
        :param transceiver: transceiver to use for transmission
        :param channel: the channels to be transmitted
        :return:
        """
        # instantiate OpticalSignal object
        ase_noise, nli_noise = self.init_noise_structs(transceiver.operation_power)
        optical_signal = OpticalSignal(channel, transceiver.spectrum_band,
                                       transceiver.channel_spacing_H, transceiver.channel_spacing_nm,
                                       transceiver.symbol_rate, transceiver.bits_per_symbol,
                                       transceiver.operation_power, ase_noise, nli_noise)

        # update optical_signal state data
        optical_signal.assoc_loc_in(transceiver)
        optical_signal.assoc_loc_out(transceiver)

        # include optical signal in LineTerminal list
        self.include_optical_signal(optical_signal)

        # associate transceiver to optical_signal
        transceiver.assoc_optical_signal(optical_signal)

        # associate an output port to the signal
        self.port_to_optical_signal_out[transceiver.id].append(optical_signal)

    def turn_on(self, out_ports):
        last_port = out_ports[-1]
        for out_port in out_ports:
            link = self.out_port_to_link[out_port]
            if out_port == last_port:
                link.propagate()
            link.include_optical_signal(self.port_to_optical_signal_out[out_port][0])

    @staticmethod
    def init_noise_structs(operation_power):
        noise = operation_power / db_to_abs(50)
        return noise, noise

    @staticmethod
    def osnr(power, ase_noise):
        return abs_to_db(power / ase_noise)

    @staticmethod
    def gosnr(power, ase_noise, nli_noise):
        return abs_to_db(power / (ase_noise + nli_noise))

    def receiver(self, in_port, signal_power, accumulated_ASE_noise, accumulated_NLI_noise):

        signalInfoDict = {}
        optical_signals = signal_power.keys()
        for signal in optical_signals:
            signalInfoDict[signal] = {'osnr': None, 'gosnr': None,
                                      'ber': None, 'success': False}

            # Get signal info
            power = signal_power[signal]
            ase_noise = accumulated_ASE_noise[signal]
            nli_noise = accumulated_NLI_noise[signal]

            # Compute OSNR and gOSNR
            osnr = self.osnr(power, ase_noise)
            gosnr = self.gosnr(power, ase_noise, nli_noise)

            signalInfoDict[signal]['osnr'] = osnr
            signalInfoDict[signal]['gosnr'] = gosnr
            if gosnr < 20:
                print("*** %s.receiver.%s: Failure!\ngOSNR: %f dB" %
                      (self.__class__.__name__, self.name, abs_to_db(gosnr)))
                signalInfoDict[signal]['success'] = False
                self.signal_info_dict_transceiver[in_port] = signalInfoDict
                self.receiver_callback(in_port, signalInfoDict)
            else:
                print("*** %s.receiver.%s: Success!" % (self.__class__.__name__, self.name))
                signalInfoDict[signal]['success'] = True
                self.signal_info_dict_transceiver[in_port] = signalInfoDict
                self.receiver_callback(in_port, signalInfoDict)

    def receiver_callback(self, in_port, signalDictInfo):
        return

    def delete_optical_signal(self, transceiver_name, optical_signal):
        """
        Delete signal reference attributed to a transceiver
        :param transceiver_name: name of transceiver containing the signal
        :param optical_signal: optical signal object to be deleted
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.LineTerminal.delete_signal: transceiver does not exist!")
        transceiver = self.name_to_transceivers[transceiver_name]
        # output ports match the transceiver ID
        self.port_to_optical_signal_out[transceiver.id] = []
        self.optical_signals.remove(optical_signal)
        transceiver.delete_optical_signal()
        del optical_signal  # would this delete the optical signal from the system?

    def print_signals(self, names=(('output', 'tx ->'), ('input', 'rx <-'))):
        """Print TX and RX signals"""
        super().print_signals(names)


class Transceiver(object):
    def __init__(self, name, operation_power=0, spectrum_band='C', optical_carrier=1550.0,
                 channel_spacing_nm=0.4 * 1e-9, channel_spacing_H=50e9,
                 bandwidth=2.99792458 * 1e9, modulation_format='16-QAM',
                 bits_per_symbol=4.0, symbol_rate=25e9):
        """
        :param name: human readable ID
        :param operation_power: operation power in dB
        :param spectrum_band: character of transmission band (i.e, C, L)
        :param optical_carrier: ideal optical carrier
        :param channel_spacing_nm: channel spacing in nm
        :param channel_spacing_H: channel spacing in Hz
        :param bandwidth: channel bandwidth in GHz - float
        :param modulation_format: modulation format name - string
        :param bits_per_symbol: bits per symbol according to modulation format = float
        :param symbol_rate: symbol rate in GBaud - float
        """
        # configuration attributes
        self.name = name
        # operation power input in dBm to convert to linear
        self.operation_power = db_to_abs(operation_power)
        self.spectrum_band = spectrum_band
        self.optical_carrier = optical_carrier
        self.channel_spacing_nm = channel_spacing_nm
        self.channel_spacing_H = channel_spacing_H
        self.bandwidth = bandwidth
        self.modulation_format = modulation_format
        self.bits_per_symbol = bits_per_symbol
        self.symbol_rate = symbol_rate
        self.gross_bit_rate = symbol_rate * np.log2(bits_per_symbol)

        # state attributes
        self.optical_signal = None

    def assoc_optical_signal(self, optical_signal):
        self.optical_signal = optical_signal

    def delete_optical_signal(self):
        self.optical_signal = None

    def compute_gross_bit_rate(self):
        self.gross_bit_rate = self.symbol_rate * np.log2(self.bits_per_symbol)

    def describe(self):
        pprint(vars(self))


class OpticalSignal(object):
    instances = {}
    spectrum_band_init_nm = {'C': 1567.132556194459}
    spectrum_band_init_H = {'C': 191.3e12}

    def __init__(self, index, spectrum_band, channel_spacing_H,
                 channel_spacing_nm, symbol_rate, bits_per_symbol,
                 power=None, ase_noise=None, nli_noise=None, data=None):
        # configuration attributes
        self.index = index
        self.frequency = self.spectrum_band_init_H[spectrum_band] + (channel_spacing_H * index)
        self.wavelength = unit.c / self.frequency
        self.wavelength2 = self.spectrum_band_init_nm[spectrum_band] * unit.nm + index * channel_spacing_nm
        self.data = data
        self.symbol_rate = symbol_rate
        self.bits_per_symbol = bits_per_symbol

        # state attributes
        self.power = power
        self.ase_noise = ase_noise
        self.nli_noise = nli_noise
        # loc_in/out: (power:p, ase:a, nli:n)
        self.loc_in_to_state = {}
        self.loc_out_to_state = {}

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        return '<ch%d:%.2fTHz>' % (
            self.index, self.frequency / unit.THz)

    def assoc_loc_in(self, loc, power=None, ase_noise=None, nli_noise=None):
        """
        Associate a location to signal performance values
        at the input interface of this point
        :param loc: location (i.e., node, span)
        :param power: power levels [mW]
        :param ase_noise: ase levels [mW]
        :param nli_noise: nli levels [mW]
        """
        if not power:
            power = self.power
        if not ase_noise:
            ase_noise = self.ase_noise
        if not nli_noise:
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
        if not power:
            power = self.power
        if not ase_noise:
            ase_noise = self.ase_noise
        if not nli_noise:
            nli_noise = self.nli_noise
        self.power = power
        self.ase_noise = ase_noise
        self.nli_noise = nli_noise
        self.loc_out_to_state[loc] = {'power': power, 'ase_noise': ase_noise, 'nli_noise': nli_noise}

    @classmethod
    def getOpticalSignal(cls, index, spectrum_band, channel_spacing,
                         symbol_rate, bits_per_symbol, data=None):
        """Return a unique OpticalSignal instance"""
        params = (index, spectrum_band, channel_spacing,
                  symbol_rate, bits_per_symbol, data)
        signal = cls.instances.get(params)
        if not signal:
            signal = cls.instances[params] = cls(*params)
        return signal


# Replace class constructor with factory method
OpticalSignal = OpticalSignal.getOpticalSignal

SwitchRule = namedtuple('SwitchRule', 'in_port out_port signal_indices')


class Roadm(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """

    def __init__(self, name, wss_dict=None, equalization_function='flatten',
                 equalization_target_out_power=-2, monitor_mode=None):

        """
        :param name:
        :param wss_dict:
        :param equalization_function:
        :param equalization_target_out_power:
        :param monitor_mode:
        """
        Node.__init__(self, name)
        # configuration attributes
        self.wss_dict = None
        # dict of WSS_id (int): (tuple); (attenuation - float; wd-attenuation - list)
        self.unpack_wss_dict(wss_dict)
        self.equalization_attenuation = db_to_abs(3)
        self.equalization_function = equalization_function
        self.equalization_target_out_power = None
        self.equalization_compensation = \
            self.equalization_safety_check(equalization_function, equalization_target_out_power)
        # dict of rule id to dict with keys in_port, out_port and signal_indices
        self.switch_table = {}
        # dict (port, signal_index) to output port in ROADM
        self.signal_index_to_out_port = {}

        if monitor_mode:
            self.monitor = Monitor(name + "-opm", component=self, mode=monitor_mode)

    def equalization_safety_check(self, equalization_function, equalization_target_out_power):
        """
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

    def unpack_wss_dict(self, wss_dict):
        """
        Unpack the corresponding values to the WSS dictionary, in the format of:
        WSS_id (int): (attenuation, wd-attenuation) (tuple)
        """
        if not wss_dict:
            # Default wss_dict with 2xWSS w/7 dB attenuation each,
            # and no wavelength-dependent attenuation.
            wss_dict = {1: (7.0, None), 2: (7.0, None)}
        tmp_dict = {}
        for wss_id, wd_tuple in wss_dict.items():
            if wd_tuple[1]:
                tmp_dict[wss_id] = wd_tuple
            else:
                wd_func = [0.0] * 91  # linear function with no extra attenuation
                tmp_dict[wss_id] = (wd_tuple[0], wd_func)
        self.wss_dict = tmp_dict

    def install_switch_rule(self, rule_id, in_port, out_port, signal_indices):
        """
        Switching rule installation, accessible from a Control System
        :param rule_id: ID of rule (similar to VLAN id)
        :param in_port: input port for incoming signals
        :param out_port: switching/output port for incoming signals
        :param signal_indices: signal indices involved in switching procedure
        :return:
        """
        # arbitrary rule identifier
        self.switch_table[rule_id] = SwitchRule(in_port, out_port, signal_indices)
        for signal_index in signal_indices:
            self.signal_index_to_out_port[in_port, signal_index] = out_port

        # AD: this may need to be commented for PTL scripts
        if len(self.port_to_optical_signal_in[in_port]) > 0:
            self.switch()

    def update_switch_rule(self, rule_id, new_out_port):
        """
        Update/create a new rule for switching
        :param rule_id: rule ID
        :param new_out_port: new output port for rule
        :return:
        """
        in_port, prev_out_port, signal_indices = self.switch_table[rule_id]
        self.switch_table[rule_id] = SwitchRule(in_port, new_out_port, signal_indices)

        for signal_index in signal_indices:
            self.signal_index_to_out_port[in_port, signal_index] = new_out_port

        self.switch()

    def clean(self):
        for port, _ in self.port_to_optical_signal_out.items():
            self.port_to_optical_signal_in[port] = []
            self.port_to_optical_signal_out[port] = []

        self.delete_switch_rules()

        for _, link in self.out_port_to_link.items():
            link.reset_propagation_struct()

    def propagate_cleanup(self):
        # Clean and prevent signals from link propagation
        for op, link in self.out_port_to_link.items():
            link.reset_propagation_struct()
            node2 = self.port_to_node_out[op]
            if isinstance(node2, LineTerminal):
                return
            else:
                node2.propagate_cleanup()

    def delete_switch_rule(self, rule_id):
        """
        Switching rule deletion from Control System
        :param rule_id: ID of rule
        :return:
        """
        in_port, out_port, signal_indices = self.switch_table[rule_id]

        # Delete rule indication of output port
        for signal_index in signal_indices:
            del self.signal_index_to_out_port[in_port, signal_index]

        # Get the optical signal objects to be removed
        optical_signals = [optical_signal for optical_signal in
                           self.port_to_optical_signal_out[out_port]
                           if optical_signal.index in signal_indices]

        # Delete signals from structures in the switch
        self.port_to_optical_signal_out[out_port] = []

        del self.switch_table[rule_id]

        # Clean signals from link propagation
        link = self.out_port_to_link[out_port]
        link.clean_optical_signals(optical_signals)

    def delete_switch_rules(self):
        """Delete all switching rules"""
        for ruleId in list(self.switch_table):
            self.delete_switch_rule(ruleId)

    def switch(self):

        # Keep track of which output ports/links have signals
        out_ports_to_links = {}

        for in_port in self.ports_in:
            # retrieve the WSS wavelength-dependent attenuation
            node_attenuation = self.get_node_attenuation(in_port)
            # Iterate over input port's signals since they all might have changed
            for optical_signal in self.port_to_optical_signal_in[in_port].items():
                # Find the output port as established when installing a rule
                out_port = self.signal_index_to_out_port.get((in_port, optical_signal.index), None)

                if out_port is None:
                    # We can trigger an Exception, but the signals wouldn't be propagated anyway
                    print("*** %s.%s.switch unable to find rule for signal %s" % (
                        self.__class__.__name__, self.name, optical_signal.index))
                    continue

                # retrieve the equalization attenuation function at the output ports
                equalization_attenuation = self.equalization_attenuation

                # attenuate signal power
                in_power = optical_signal.assoc_loc_in[self]['power']
                optical_signal.assoc_loc_out[self]['power'] = \
                    in_power / node_attenuation[optical_signal] / equalization_attenuation
                # attenuate signal ase noise
                ase_noise = optical_signal.assoc_loc_in[self]['ase_noise']
                optical_signal.assoc_loc_out[self]['ase_noise'] = \
                    ase_noise / node_attenuation[optical_signal] / equalization_attenuation
                # attenuate signal nli noise
                nli_noise = optical_signal.assoc_loc_in[self]['nli_noise']
                optical_signal.assoc_loc_out[self]['nli_noise'] = \
                    nli_noise / node_attenuation[optical_signal] / equalization_attenuation

                if out_port not in out_ports_to_links.keys():
                    # keep track of the ports where signals will pass through
                    out_ports_to_links[out_port] = self.out_port_to_link[out_port]

        for out_port, link in out_ports_to_links.items():
            for optical_signal in self.port_to_optical_signal_out[out_port]:
                link.include_optical_signal(optical_signal)
            # Propagate signals through link
            link.propagate(equalization=self.equalization_compensation)

    def get_node_attenuation(self, in_port):
        """
        When switching, it computes the total node attenuation only
        for the signals passing through
        """
        node_attenuation = {}
        for optical_signal in self.port_to_optical_signal_in[in_port]:
            wss_attenuation = 0.0
            wss_wd_attenuation = 0.0
            for wss_id, attenuation_tuple in self.wss_dict.items():
                wss_attenuation += attenuation_tuple[0]
                wss_wd_attenuation += attenuation_tuple[1][optical_signal.index - 1]
            total_attenuation = db_to_abs(wss_attenuation + wss_wd_attenuation)
            node_attenuation[optical_signal] = total_attenuation
        return node_attenuation

    def equalization_reconf(self, link, output_power_dict):
        """
        wavelength dependent attenuation
        """
        if self.equalization_function is 'flatten':
            # compute equalization compensation and re-propagate only if there is a function
            out_difference = {}
            for k, out_power in output_power_dict.items():
                # From the boost-amp, compute the difference between output power levels
                # and the target output power. Set this as the compensation function.
                delta = self.equalization_target_out_power / out_power
                out_difference[k] = delta

            for optical_signal, equalization_att in out_difference.items():
                # WSS attenuation and fixed equalization attenuation was inflicted at switching time,
                # hence, only inflict now the additional equalization attenuation to compensate
                # for the excursions generated at the boost-amp.
                optical_signal.assoc_loc_out[self]['power'] *= equalization_att
                optical_signal.assoc_loc_out[self]['ase_noise'] *= equalization_att
                optical_signal.assoc_loc_out[self]['nli_noise'] *= equalization_att

                link.include_optical_signal(optical_signal)
        link.propagate(equalization=False)

    # def print_signals(self):
    #     "Debugging: print input and output signals"
    #     print(self, "signal paths:")
        # for inport in sorted(self.port_to_optical_signal_power_in):
        #     inpowers = self.port_to_optical_signal_power_in[inport]
        #     if inpowers:
        #         for signal, inpower in inpowers.items():
        #             outport = self.signal_index_to_out_port.get((inport, signal.index), None)
        #             print('%d:%s@%.1fdBm' % (inport, signal, abs_to_db(inpower)), '->', end=' ')
        #             if outport is not None:
        #                 outpowers = self.port_to_optical_signal_power_out.get(outport, {})
        #                 outpower = outpowers.get(signal, float('nan'))
        #                 print('%d:%s@%.1fdBm' % (outport, signal, abs_to_db(outpower)))
        #             else:
        #                 print('***DROP***')


class Equalizer(Node):
    """
    Dynamic gain equalizer (DGE)
    """

    def __init__(self, name, wavelength_dependent_gain_id=None):
        Node.__init__(self, name)
        self.insertion_loss = db_to_abs(6)
        self.input_power = {}  # dict of OpticalSignal to input power levels
        self.output_power = {}  # dict of OpticalSignal to output power levels
        self.wdgfunc = None
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

    def load_wavelength_dependent_gain(self, wavelength_dependent_gain_id):
        """
        :param wavelength_dependent_gain_id: file name id (see top of script) - string
        :return: Return wavelength dependent gain array
        """
        if wavelength_dependent_gain_id is None:
            k = random.choice(list(description_files.keys()))
            self.wdgfunc = k
            wavelength_dependent_gain_id = k
        wdg_file = description_files[wavelength_dependent_gain_id]
        with open(description_files_dir + wdg_file, "r") as f:
            return [float(line) for line in f]


description_files_dir = '../description-files/'
# description_files_dir = '../../Research/optical-network-emulator/description-files/'
# description_files = {'linear': 'linear.txt'}
description_files = {'wdg1': 'wdg1_3.txt',
                     'wdg2': 'wdg2_2.txt'}


# 'wdg1_yj': 'wdg1_yeo_johnson.txt',
# 'wdg2_yj': 'wdg2_yeo_johnson.txt'}


class Amplifier(Node):

    def __init__(self, name, amplifier_type='EDFA', target_gain=18.0,
                 noise_figure=(5.5, 91), noise_figure_function=None,
                 bandwidth=12.5e9, wavelength_dependent_gain_id=None,
                 boost=False, monitor_mode=None):
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

        if monitor_mode is not None:
            self.monitor = Monitor(name + "-opm", component=self, mode=monitor_mode)

        self.power_excursions_flag_1 = False  # When both are True system gain balancing is complete
        self.power_excursions_flag_2 = False

        self.boost = boost

    def power_excursions_flags_off(self):
        self.power_excursions_flag_1 = False
        self.power_excursions_flag_2 = False

    def load_wavelength_dependent_gain(self, wavelength_dependent_gain_id):
        """
        :param wavelength_dependent_gain_id: file name id (see top of script) - string
        :return: Return wavelength dependent gain array
        """
        if wavelength_dependent_gain_id is None:
            k = random.choice(list(description_files.keys()))
            self.wdgfunc = k
            wavelength_dependent_gain_id = k
        wdg_file = description_files[wavelength_dependent_gain_id]
        with open(description_files_dir + wdg_file, "r") as f:
            return [float(line) for line in f]

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

    def active_wavelength_dependent_gain(self):
        """
        Retrieve in a list the WDG of the active channels
        :return: list active channels in amplifier
        """
        list_wdg = []
        for optical_signal in self.optical_signals:
            list_wdg.append(self.get_wavelength_dependent_gain(optical_signal.index))
        return list_wdg

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

    def output_amplified_power(self, optical_signal, p_exc=False):
        """
        Compute the output power levels of each signal after amplification
        :param optical_signal: signal object
        :param p_exc:
        """
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        # Conversion from dB to linear
        system_gain_linear = db_to_abs(self.system_gain)
        wavelength_dependent_gain_linear = db_to_abs(wavelength_dependent_gain)
        output_power = optical_signal.loc_in_to_state[self]['power'] * system_gain_linear * \
                       wavelength_dependent_gain_linear
        optical_signal.assoc_loc_out(self, power=output_power)
        if p_exc:
            return output_power / wavelength_dependent_gain_linear
        else:
            return output_power

    def stage_amplified_spontaneous_emission_noise(self, optical_signal):
        """
        :return:
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """
        # Set parameters needed for ASE model
        noise_figure_linear = db_to_abs(self.noise_figure[optical_signal.index])
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        system_gain = self.system_gain

        ase_noise_in = optical_signal.assoc_loc_in[self]['ase_noise']
        gain_linear = db_to_abs(system_gain) * db_to_abs(wavelength_dependent_gain)
        ase_noise_out = ase_noise_in * gain_linear + (noise_figure_linear * sc.h * optical_signal.frequency *
                                                      self.bandwidth * (gain_linear - 1) * 1000)
        optical_signal.assoc_loc_out[self]['ase_noise'] = ase_noise_out

    def compute_power_excursions(self):
        """
        Balance system gain with respect with the mean
        gain of the signals in the amplifier: power excursions
        :return:
        """
        # Convert power levels from linear to dBm
        output_power_dBm = []
        input_power_dBm = []
        for optical_signal in self.optical_signals:
            output_power_dBm.append(abs_to_db(optical_signal.assoc_loc_out[self]['power']))
            input_power_dBm.append(abs_to_db(optical_signal.assoc_loc_in[self]['power']))

        # Mean difference between output and input power levels
        out_in_difference = np.mean(output_power_dBm) - np.mean(input_power_dBm)
        # Compute the balanced system gain
        power_excursions = out_in_difference - self.target_gain
        system_gain_balance = self.system_gain - power_excursions
        self.system_gain = system_gain_balance
        # Flag check for enabling the repeated computation of balancing
        if self.power_excursions_flag_1 and (not self.power_excursions_flag_2):
            self.power_excursions_flag_2 = True
        if not (self.power_excursions_flag_1 and self.power_excursions_flag_2):
            self.power_excursions_flag_1 = True

    def nli_compensation(self):
        """
        As the signal power and ASE noise suffer the impact from the
        amplification, the NLI noise also gets amplified.
        """
        for optical_signal in self.optical_signals:
            wavelength_dependent_gain = db_to_abs(self.get_wavelength_dependent_gain(optical_signal.index))
            nli_noise_in = optical_signal.assoc_loc_in[self]['nli_noise']
            optical_signal.assoc_loc_out[self]['nli_noise'] = \
                nli_noise_in * db_to_abs(self.system_gain) * wavelength_dependent_gain

    def clean_optical_signals(self):
        self.optical_signals = []

    # ADDITIONS FOR OFC DEMO USE-CASES
    def mock_nf_adjust(self, new_nf):
        # Could be improved to allow for input an NF function too
        self.noise_figure = self.get_noise_figure(new_nf, None)

    def mock_amp_gain_adjust(self, new_gain):
        self.target_gain = new_gain
        self.system_gain = new_gain

    def __repr__(self):
        "String representation"
        return '<%s %.1fdB>' % (self.name, self.target_gain)


class MonitorOld(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """

    def __init__(self, name, link=None, span=None, amplifier=None):
        """
        :param name:
        set to 6 dB per task needed (Add/Drop/Pass-through).
        """
        Node.__init__(self, name)
        self.node_id = id(self)
        self.link = link
        self.span = span
        self.amplifier = amplifier

    def get_list_osnr(self):
        """
        Get the OSNR values at this OPM as a list
        :return: OSNR values at this OPM as a list
        """
        optical_signals = self.amplifier.output_power.keys()
        signals_list = []
        ordered_signals = self.order_signals(optical_signals)
        for optical_signal in ordered_signals:
            signals_list.append(self.get_osnr(optical_signal))
        return signals_list

    @staticmethod
    def order_signals(optical_signals):
        """
        Sort OpticalSignal objects by index
        :param optical_signals: list[OpticalSignal, ]
        :return: sorted list[OpticalSignal, ]
        """
        signal_by_index = {signal.index: signal for signal in optical_signals}
        indices = [signal.index for signal in optical_signals]
        ordered_optical_signals_by_index = sorted(indices)
        ordered_optical_signals = [signal_by_index[i] for i in ordered_optical_signals_by_index]
        return ordered_optical_signals

    def get_power(self, optical_signal):
        return self.amplifier.output_power[optical_signal]

    def get_ase_noise(self, optical_signal):
        return self.amplifier.ase_noise[optical_signal]

    def get_nli_noise(self, optical_signal):
        return self.amplifier.nonlinear_noise[optical_signal]

    def get_list_gosnr(self):
        """
        Get the gOSNR values at this OPM as a list
        :return: gOSNR values at this OPM as a list
        """
        optical_signals = self.amplifier.output_power.keys()
        optical_signals_list = []
        for optical_signal in optical_signals:
            optical_signals_list.append(self.get_gosnr(optical_signal))
        return optical_signals_list

    def get_dict_gosnr(self):
        """
        Get the gOSNR values at this OPM as a list
        :return: gOSNR values at this OPM as a list
        """
        optical_signals = self.amplifier.output_power.keys()
        optical_signals_dict = {}
        for optical_signal in optical_signals:
            optical_signals_dict[optical_signal] = self.get_gosnr(optical_signal)
        return optical_signals_dict

    def get_osnr(self, optical_signal):
        """
        Compute OSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :return: OSNR (linear)
        """
        output_power = self.amplifier.output_power[optical_signal]
        ase_noise = self.amplifier.ase_noise[optical_signal]
        osnr_linear = output_power / ase_noise
        osnr = abs_to_db(osnr_linear)
        return osnr

    def get_gosnr(self, optical_signal):
        """
        Compute gOSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :return: gOSNR (linear)
        """
        output_power = self.amplifier.output_power[optical_signal]
        ase_noise = self.amplifier.ase_noise[optical_signal]
        nli_noise = self.amplifier.nonlinear_noise[optical_signal]
        gosnr_linear = output_power / (ase_noise + nli_noise * (12.5e9 / 32.0e9))
        gosnr = abs_to_db(gosnr_linear)
        return gosnr

    def __repr__(self):
        return "<%s,link=%s,span=%s,amp=%s>" % (
            self.name, self.link, self.span, self.amplifier)


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
        self.mode = mode

    def extract_optical_signal(self):
        """
        :return power: Returns Optical signals for the required objects
        """

        if (isinstance(self.component, LineTerminal)):
            optical_signals = {}
            for port in sorted(self.component.signal_info_dict_transceiver):
                signals = self.component.signal_info_dict_transceiver[port]
                optical_signals[port] = signals.keys()
            return optical_signals

        if (isinstance(self.component, Amplifier)):
            optical_signals = []
            if self.mode == 'in':
                optical_signals = self.component.input_power.keys()
            if self.mode == 'out':
                optical_signals = self.component.output_power.keys()
            return optical_signals

        if (isinstance(self.component, Roadm)):
            optical_signals = {}
            roadm_power_type = {}
            if self.mode == 'in':
                roadm_power_type = self.component.port_to_optical_signal_power_in
            if self.mode == 'out':
                roadm_power_type = self.component.port_to_optical_signal_power_out

            for port in sorted(roadm_power_type):
                optical_signals_list = []
                signal_powers = roadm_power_type[port]
                signal_index = []
                if signal_powers:
                    optical_signals_list = signal_powers.keys()
                optical_signals[port] = optical_signals_list

            return optical_signals

    def get_list_osnr(self):
        """
        Get the OSNR values at this OPM as a list/dictionary
        :return: OSNR values at this OPM as a list/dictionary
        """

        if (isinstance(self.component, Amplifier)):
            optical_signals = self.extract_optical_signal()
            signals_list = []
            ordered_signals = self.order_signals(optical_signals)
            for optical_signal in ordered_signals:
                signals_list.append(self.get_osnr(optical_signal))
            return signals_list

        if (isinstance(self.component, LineTerminal)):
            optical_signals = self.extract_optical_signal()
            signal_dict = {}
            for port in sorted(optical_signals):
                signals_list = []
                ordered_signals = self.order_signals(optical_signals[port])
                for optical_signal in ordered_signals:
                    signals_list.append(self.get_gosnr(optical_signal, port=port))
                signal_dict[port] = signals_list
            return signal_dict

        if (isinstance(self.component, Roadm)):
            optical_signals = self.extract_optical_signal()
            signal_dict = {}
            for port in sorted(optical_signals):
                signals_list = []
                ordered_signals = self.order_signals(optical_signals[port])
                for optical_signal in ordered_signals:
                    signals_list.append(self.get_osnr(optical_signal, port=port))
                signal_dict[port] = signals_list
            return signal_dict

    @staticmethod
    def order_signals(optical_signals):
        """
        Sort OpticalSignal objects by index
        :param optical_signals: list[OpticalSignal, ]
        :return: sorted list[OpticalSignal, ]
        """
        signal_by_index = {signal.index: signal for signal in optical_signals}
        indices = [signal.index for signal in optical_signals]
        ordered_optical_signals_by_index = sorted(indices)
        ordered_optical_signals = [signal_by_index[i] for i in ordered_optical_signals_by_index]
        return ordered_optical_signals

    def get_list_gosnr(self):
        """
        Get the gOSNR values at this OPM as a list/dictionary
        :return: gOSNR values at this OPM as a list/dictionary
        """

        if (isinstance(self.component, Amplifier)):
            optical_signals = self.extract_optical_signal()
            signals_list = []
            ordered_signals = self.order_signals(optical_signals)
            for optical_signal in ordered_signals:
                signals_list.append(self.get_gosnr(optical_signal))
            return signals_list

        if (isinstance(self.component, LineTerminal)):
            optical_signals = self.extract_optical_signal()
            signal_dict = {}
            for port in sorted(optical_signals):
                signals_list = []
                ordered_signals = self.order_signals(optical_signals[port])
                for optical_signal in ordered_signals:
                    signals_list.append(self.get_gosnr(optical_signal, port=port))
                signal_dict[port] = signals_list
            return signal_dict

        if (isinstance(self.component, Roadm)):
            optical_signals = self.extract_optical_signal()
            signal_dict = {}
            for port in sorted(optical_signals):
                signals_list = []
                ordered_signals = self.order_signals(optical_signals[port])
                for optical_signal in ordered_signals:
                    signals_list.append(self.get_gosnr(optical_signal, port=port))
                signal_dict[port] = signals_list
            return signal_dict

    def get_osnr(self, optical_signal, port=None):
        """
        Compute OSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :param port: port for ROADMs
        :return: OSNR (linear)
        """
        if (isinstance(self.component, Amplifier)):
            output_power = self.component.output_power[optical_signal]
            ase_noise = self.component.ase_noise[optical_signal]
            osnr_linear = output_power / ase_noise
            osnr = abs_to_db(osnr_linear)
            return osnr

        if (isinstance(self.component, LineTerminal)):
            if (port != None):
                osnr = self.signal_info_dict_transceiver[port][optical_signal]['osnr']
                return osnr

        if (isinstance(self.component, Roadm)):
            if (port != None):

                if (self.mode == 'out'):
                    ase_noise = self.component.port_to_optical_signal_ase_noise_out[port][optical_signal]
                    power = self.component.port_to_optical_signal_power_out[port][optical_signal]
                if (self.mode == 'in'):
                    ase_noise = self.component.port_to_optical_signal_ase_noise_in[port][optical_signal]
                    power = self.component.port_to_optical_signal_power_in[port][optical_signal]

            osnr_linear = power / ase_noise
            osnr = abs_to_db(osnr_linear)
            return osnr

    def get_gosnr(self, optical_signal, port=None):
        """
        Compute gOSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :param port: port for ROADMs
        :return: gOSNR (linear)
        """

        if (isinstance(self.component, Amplifier)):
            output_power = self.component.output_power[optical_signal]
            ase_noise = self.component.ase_noise[optical_signal]
            nli_noise = self.component.nonlinear_noise[optical_signal]
            gosnr_linear = output_power / (ase_noise + nli_noise * (12.5e9 / 32.0e9))
            gosnr = abs_to_db(gosnr_linear)
            return gosnr

        if (isinstance(self.component, LineTerminal)):
            if (port != None):
                gosnr = self.component.signal_info_dict_transceiver[port][optical_signal]['gosnr']
                return gosnr

        if (isinstance(self.component, Roadm)):
            if (port != None):

                if (self.mode == 'out'):
                    ase_noise = self.component.port_to_optical_signal_ase_noise_out[port][optical_signal]
                    nli_noise = self.component.port_to_optical_signal_nli_noise_out[port][optical_signal]
                    power = self.component.port_to_optical_signal_power_out[port][optical_signal]
                if (self.mode == 'in'):
                    ase_noise = self.component.port_to_optical_signal_ase_noise_in[port][optical_signal]
                    nli_noise = self.component.port_to_optical_signal_nli_noise_in[port][optical_signal]
                    power = self.component.port_to_optical_signal_power_in[port][optical_signal]

            gosnr_linear = power / (ase_noise + nli_noise * (12.5e9 / 32.0e9))
            gosnr = abs_to_db(gosnr_linear)
            return gosnr

    def __repr__(self):
        return "<%s,link=%s,span=%s,amp=%s>" % (self.name, self.component)

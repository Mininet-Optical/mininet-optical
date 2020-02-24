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


class Node(object):
    input_port_base = 0
    output_port_base = 100  # higher value to ease debugging, might need to rethink its scalability

    def __init__(self, name):
        self.name = name
        self.ports_in = []
        self.ports_out = []
        self.port_to_node_in = {}  # dict of port no. to ingress connecting nodes
        self.port_to_node_out = {}  # dict of port no. to egress connecting nodes
        self.port_to_optical_signal_in = {}  # dict of ports to input signals
        self.port_to_optical_signal_out = {}  # dict of ports to output signals
        self.port_to_optical_signal_power_in = {}  # dict of ports to input signals and power levels
        self.port_to_optical_signal_power_out = {}  # dict of ports to output signals and power levels
        self.out_port_to_link = {}

        # tmp PTL
        self.port_to_optical_signal_power_in_qot = {}  # dict of ports to input signals and power levels
        self.port_to_optical_signal_power_out_qot = {}  # dict of ports to output signals and power levels

    def new_output_port(self, connected_node):
        """
        Create a new output port for a node
        to connect to another node
        :param connected_node:
        :return: new output port
        """
        if len(self.port_to_node_out) > 0:
            new_output_port = max(self.port_to_node_out.keys()) + 1
        else:
            new_output_port = self.output_port_base
        # Enable discovery of output ports
        self.ports_out.append(new_output_port)
        # Enable discovery of connected node through output port
        self.port_to_node_out[new_output_port] = connected_node
        # Enable monitoring of signals at output port
        self.port_to_optical_signal_out[new_output_port] = []
        # Enable monitoring of signal power levels at output port
        self.port_to_optical_signal_power_out[new_output_port] = {}
        self.port_to_optical_signal_power_out_qot[new_output_port] = {}
        return new_output_port

    def new_input_port(self, connected_node):
        """
        Create a new input port for a node
        to connect to another node
        :param connected_node:
        :return: new input port
        """
        if len(self.port_to_node_in) > 0:
            new_input_port = max(self.port_to_node_in.keys()) + 1
        else:
            new_input_port = self.input_port_base
        # Enable discovery of input ports
        self.ports_in.append(new_input_port)
        # Enable discovery of connected node through input port
        self.port_to_node_in[new_input_port] = connected_node
        # Enable monitoring of signals at input port
        self.port_to_optical_signal_in[new_input_port] = []
        # Enable monitoring of signal power levels at input port
        self.port_to_optical_signal_power_in[new_input_port] = {}
        self.port_to_optical_signal_power_in_qot[new_input_port] = {}
        return new_input_port

    def describe(self):
        pprint(vars(self))


class LineTerminal(Node):

    def __init__(self, name, transceivers=None):
        Node.__init__(self, name)
        self.transceivers = []
        self.name_to_transceivers = {}  # dict of name of transceiver to transceiver objects
        self.transceiver_to_optical_signals = {}  # dict of transceivers name to list of optical signal objects

        self.wavelengths = {k: 'off' for k in range(1, 91)}  # only supporting 90 channels per LT

        if transceivers:
            self.add_transceivers(transceivers)

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
        new_transceiver = Transceiver(transceiver_name, operational_power, spectrum_band)
        self.name_to_transceivers[transceiver_name] = new_transceiver
        self.transceiver_to_optical_signals[new_transceiver] = []
        self.transceivers.append(new_transceiver)
        return new_transceiver

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
        del self.transceiver_to_optical_signals[transceiver_name]

    def transmit(self, transceiver, out_port, channels):
        """
        Begin a transmission from the LT to the connected ROADM
        :param transceiver: transceiver to use for transmission
        :param out_port: output port for transmission
        :param channels: the channels to be transmitted
        :return:
        """
        # Retrieve transmission specifications to pass
        # to the signals to be installed
        spectrum_band = transceiver.spectrum_band
        channel_spacing = transceiver.channel_spacing
        symbol_rate = transceiver.symbol_rate
        bits_per_symbol = transceiver.bits_per_symbol
        # list containing the new signals
        signals = []
        for channel in channels:
            new_optical_signal = OpticalSignal(channel, spectrum_band, channel_spacing, symbol_rate, bits_per_symbol)
            signals.append(new_optical_signal)
            # Associate signals to a transceiver/modulator
            self.transceiver_to_optical_signals[transceiver].append(new_optical_signal)
        # Start transmission
        print("*** Node %s initiating transmission..." % self.name)
        self.start(transceiver, out_port)
        link = self.out_port_to_link[out_port]
        link.propagate(self.port_to_optical_signal_power_out[out_port],
                       self.port_to_optical_signal_power_out_qot[out_port],
                       accumulated_ASE_noise=None,
                       accumulated_NLI_noise=None,
                       accumulated_ASE_noise_qot=None,
                       accumulated_NLI_noise_qot=None)

    def receiver(self, in_port, signal_power, signal_power_qot):
        self.port_to_optical_signal_power_in[in_port].update(signal_power)
        self.port_to_optical_signal_power_in_qot[in_port].update(signal_power_qot)
        print("*** Node %s.receiver.%s: Success!" % (self.__class__.__name__, self.name))

    def delete_channel(self, transceiver_name, optical_signal):
        """
        Delete signal reference attributed to a transceiver
        :param transceiver_name: name of transceiver containing the signal
        :param optical_signal: optical signal object to be deleted
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.LineTerminal.delete_signal: transceiver does not exist!")
        self.transceiver_to_optical_signals[transceiver_name].remove(optical_signal)

    def available_wavelengths(self):
        """
        Check for wavelengths 'off'
        :return: wavelength indexes where 'off'
        """
        return [key for key, value in self.wavelengths.items() if value is 'off']

    def start(self, transceiver, out_port):
        """
        Begin transmission and assign the operational power to the signals
        :param transceiver: transceiver used for transmission
        :param out_port: output port where signals are transmitted
        :return:
        """
        for channel in self.transceiver_to_optical_signals[transceiver]:
            output_power = transceiver.operation_power
            channel.power_at_output_interface[self] = output_power
            self.port_to_optical_signal_power_out[out_port][channel] = output_power
            self.port_to_optical_signal_power_out_qot[out_port][channel] = output_power
            self.port_to_optical_signal_out[out_port].append(channel)


class Transceiver(object):
    def __init__(self, name, operation_power=0, spectrum_band='C', optical_carrier=1550.0,
                 channel_spacing=0.4 * 1e-9, bandwidth=2.99792458 * 1e9, modulation_format='16-QAM',
                 bits_per_symbol=4.0, symbol_rate=0.032e12):
        """
        :param channel_spacing: channel spacing in nanometers - float
        :param bandwidth: channel bandwidth in GHz - float
        :param modulation_format: modulation format name - string
        :param bits_per_symbol: bits per symbol according to modulation format = float
        :param symbol_rate: symbol rate in GBaud - float
        """
        self.id = id(self)
        self.name = name
        self.operation_power = db_to_abs(operation_power)  # operation power input in dBm to convert to linear
        self.spectrum_band = spectrum_band
        self.optical_carrier = optical_carrier
        self.channel_spacing = channel_spacing
        self.bandwidth = bandwidth
        self.modulation_format = modulation_format
        self.bits_per_symbol = bits_per_symbol
        self.symbol_rate = symbol_rate
        self.gross_bit_rate = symbol_rate * np.log2(bits_per_symbol)

    def compute_gross_bit_rate(self):
        self.gross_bit_rate = self.symbol_rate * np.log2(self.bits_per_symbol)

    def describe(self):
        pprint(vars(self))


class OpticalSignal(object):
    spectrum_band_init_nm = {'C': 1529.2}

    def __init__(self, index, spectrum_band, channel_spacing,
                 symbol_rate, bits_per_symbol, data=None):
        self.index = index
        self.wavelength = self.spectrum_band_init_nm[spectrum_band] * unit.nm + index * channel_spacing
        self.frequency = unit.c / self.wavelength
        self.data = data
        self.symbol_rate = symbol_rate
        self.bits_per_symbol = bits_per_symbol

        self.power_at_input_interface = {}
        self.power_at_output_interface = {}
        self.linear_noise_at_interface = {}
        self.nonlinear_noise_at_interface = {}

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        if self.index < 10:
            return '<0%d>' % self.index
        return '<%d>' % self.index


SwitchRule = namedtuple('SwitchRule', 'in_port out_port signal_indices')


class Roadm(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """

    def __init__(self, name, wss_dict=None, voa_function=None, voa_target_out_power=None):
        """
        :param name:
        :param wss_dict:
        :param voa_function:
        """
        Node.__init__(self, name)
        self.node_id = id(self)
        self.wss_dict = None
        self.unpack_wss_dict(wss_dict)  # dict of WSS_id (int): (tuple); (attenuation - float; wd-attenuation - list)

        self.voa_attenuation = db_to_abs(3)
        self.voa_function = voa_function
        self.voa_target_out_power = None
        self.voa_compensation = self.voa_safety_check(voa_function, voa_target_out_power)

        self.switch_table = {}  # dict of rule id to dict with keys in_port, out_port and signal_indices
        self.signal_index_to_out_port = {}  # dict signal_index to output port in ROADM

        self.port_to_optical_signal_ase_noise_in = {}
        self.port_to_optical_signal_ase_noise_in_qot = {}
        self.port_to_optical_signal_nli_noise_in = {}
        self.port_to_optical_signal_nli_noise_in_qot = {}
        self.port_to_optical_signal_ase_noise_out = {}  # dict out port to OpticalSignal and ASE noise
        self.port_to_optical_signal_ase_noise_out_qot = {}  # dict out port to OpticalSignal and ASE noise
        self.port_to_optical_signal_nli_noise_out = {}  # dict out port to OpticalSignal and NLI noise
        self.port_to_optical_signal_nli_noise_out_qot = {}  # dict out port to OpticalSignal and NLI noise

    def voa_safety_check(self, voa_function, voa_target_out_power):
        """
        Safety check for the declaration of VOA reconfiguration parameters
        :param voa_function: string (i.e., 'flatten')
        :param voa_target_out_power: float
        :return: True VOA reconf False otherwise
        """
        if voa_target_out_power is not None:
            # This check is to avoid pythonic-responses
            # if voa_target_out_power is set to zero
            voa_target_out_power = db_to_abs(voa_target_out_power)
            self.voa_target_out_power = voa_target_out_power
        try:
            err_msg = "Roadm.voa_safety_check: inconsistent declaration of VOA params."
            # Either both are passed or None
            assert all([voa_function, voa_target_out_power]) or \
                   all(x is None for x in [voa_function, voa_target_out_power]), err_msg
        except AssertionError as err:
            raise err
        if all([voa_function, voa_target_out_power]):
            return True
        return False

    def unpack_wss_dict(self, wss_dict):
        """
        Unpack the corresponding values to the WSS dictionary, in the format of:
        WSS_id (int): (attenuation, wd-attenuation) (tuple)
        """
        if not wss_dict:
            # Default wss_dict with 2xWSS w/3 dB attenuation each,
            # and no wavelength-dependent attenuation.
            wss_dict = {1: (3, None), 2: (3, None)}
        tmp_dict = {}
        for wss_id, wd_tuple in wss_dict.items():
            if wd_tuple[1]:
                tmp_dict[wss_id] = wd_tuple
            else:
                wd_func = [0.0] * 90  # linear function with no extra attenuation
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
        print("*** Installing switch rule at %s with in_port: %d out_port: %d and %s" % (self.name, in_port, out_port,
                                                                                         signal_indices))
        # arbitrary rule identifier
        self.switch_table[rule_id] = SwitchRule(in_port, out_port, signal_indices)
        for signal_index in signal_indices:
            self.signal_index_to_out_port[in_port, signal_index] = out_port

        print(self.port_to_optical_signal_power_in[in_port])
        if len(self.port_to_optical_signal_power_in[in_port]) > 0:
            self.switch(in_port)

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

        # Clean the output port instances of the signals
        prev_output_signals = self.port_to_optical_signal_power_out[prev_out_port]
        optical_signals = [optical_signal for optical_signal in prev_output_signals
                           if optical_signal.index in signal_indices]

        # Delete from structures in ROADM node
        for optical_signal in optical_signals:
            del self.port_to_optical_signal_power_out[prev_out_port][optical_signal]
            if (prev_out_port in self.port_to_optical_signal_ase_noise_out and
                    prev_out_port in self.port_to_optical_signal_nli_noise_out):
                del self.port_to_optical_signal_ase_noise_out[prev_out_port][optical_signal]
                del self.port_to_optical_signal_nli_noise_out[prev_out_port][optical_signal]

        self.propagate_cleanup()

        if (prev_out_port in self.port_to_optical_signal_ase_noise_out.keys() and
                prev_out_port in self.port_to_optical_signal_nli_noise_out.keys()):
            ase = self.port_to_optical_signal_ase_noise_out[prev_out_port].copy()
            nli = self.port_to_optical_signal_nli_noise_out[prev_out_port].copy()
        else:
            ase, nli = {}, {}

        self.port_to_optical_signal_power_out[new_out_port] = {}
        self.port_to_optical_signal_ase_noise_out[new_out_port] = {}
        self.port_to_optical_signal_nli_noise_out[new_out_port] = {}
        # Propagate the changes in the switch by switching
        self.insert_signals(in_port, self.port_to_optical_signal_power_in[in_port], ase, nli)
        self.switch(in_port)

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
                           self.port_to_optical_signal_power_out[out_port]
                           if optical_signal.index in signal_indices]

        # Delete signals from structures in the switch
        for optical_signal in optical_signals:

            # XXX BL: why should deleting a rule affect the *input* signal?
            # del self.port_to_optical_signal_power_in[in_port][optical_signal]
            del self.port_to_optical_signal_power_out[out_port][optical_signal]

            if out_port in self.port_to_optical_signal_ase_noise_out:
                del self.port_to_optical_signal_ase_noise_out[out_port][optical_signal]
            if out_port in self.port_to_optical_signal_nli_noise_out:
                del self.port_to_optical_signal_nli_noise_out[out_port][optical_signal]

        del self.switch_table[rule_id]

        # Clean signals from link propagation
        link = self.out_port_to_link[out_port]
        link.clean_optical_signals(optical_signals)

    def insert_signals(self, in_port, optical_signals, accumulated_ASE_noise=None, accumulated_NLI_noise=None):
        # Update input port structure for monitoring purposes
        self.port_to_optical_signal_power_in[in_port].update(optical_signals)
        # if in_port not in self.port_to_optical_signal_ase_noise_in:
        self.port_to_optical_signal_ase_noise_in.setdefault(in_port, {})
        self.port_to_optical_signal_ase_noise_in[in_port].update(accumulated_ASE_noise)
        self.port_to_optical_signal_nli_noise_in.setdefault(in_port, {})
        self.port_to_optical_signal_nli_noise_in[in_port].update(accumulated_NLI_noise)

    def switch(self, in_port):
        """
        Switch the input signals to the appropriate output ports as established
        by the switching rules in the switch table (if any).
        :param in_port: input port where signals are being transmitted
        :return:
        """
        # Keep track of which output ports/links have signals
        out_ports_to_links = {}

        if self.name == 'roadm2':
            print()

        # retrieve the WSS wavelength-dependent attenuation
        node_attenuation = self.get_node_attenuation(in_port)

        # Iterate over input port's signals since they all might have changed
        for optical_signal, in_power in self.port_to_optical_signal_power_in[in_port].items():
            # Find the output port as established when installing a rule
            out_port = self.signal_index_to_out_port.get((in_port, optical_signal.index), None)

            if out_port is None:
                # We can trigger an Exception, but the signals wouldn't be propagated anyway
                print("%s.%s.switch unable to find rule for signal %s" % (
                    self.__class__.__name__, self.name, optical_signal.index))
                continue

            # retrieve the VOA attenuation function at the output ports
            voa_attenuation = self.voa_attenuation

            # Attenuate signal power and update it on output port
            self.port_to_optical_signal_power_out[out_port][optical_signal] = \
                in_power / node_attenuation[optical_signal] / voa_attenuation

            # if accumulated_ASE_noise and optical_signal in accumulated_ASE_noise:
            if optical_signal in self.port_to_optical_signal_ase_noise_in[in_port]:
                # Attenuate ASE noise and update it on output port
                ase_noise = self.port_to_optical_signal_ase_noise_in[in_port][optical_signal]
                ase_noise /= node_attenuation[optical_signal] / voa_attenuation
                self.port_to_optical_signal_ase_noise_out.setdefault(out_port, {})
                self.port_to_optical_signal_ase_noise_out[out_port][optical_signal] = ase_noise

            # if accumulated_NLI_noise:
            if optical_signal in self.port_to_optical_signal_nli_noise_in[in_port]:
                nli_noise = self.port_to_optical_signal_nli_noise_in[in_port][optical_signal]
                nli_noise /= node_attenuation[optical_signal] / voa_attenuation
                self.port_to_optical_signal_nli_noise_out.setdefault(out_port, {})
                self.port_to_optical_signal_nli_noise_out[out_port][optical_signal] = nli_noise

            if out_port not in out_ports_to_links.keys():
                # keep track of the ports where signals will passed through
                out_ports_to_links[out_port] = self.out_port_to_link[out_port]

        ######################################### QOT ESTIMATION BEGINS #########################################
        for optical_signal, in_power in self.port_to_optical_signal_power_in_qot[in_port].items():
            # Find the output port as established when installing a rule
            out_port = self.signal_index_to_out_port.get((in_port, optical_signal.index), None)

            if out_port is None:
                # We can trigger an Exception, but the signals wouldn't be propagated anyway
                print("%s.%s.switch unable to find rule for signal %s" % (
                    self.__class__.__name__, self.name, optical_signal.index))
                continue

            # retrieve the VOA attenuation function at the output ports
            voa_attenuation = self.voa_attenuation
            # Attenuate signal power and update it on output port
            self.port_to_optical_signal_power_out_qot[out_port][optical_signal] = \
                in_power / node_attenuation[optical_signal] / voa_attenuation

            # if accumulated_ASE_noise and optical_signal in accumulated_ASE_noise:
            if optical_signal in self.port_to_optical_signal_ase_noise_in_qot[in_port]:
                # Attenuate ASE noise and update it on output port
                ase_noise = self.port_to_optical_signal_ase_noise_in_qot[in_port][optical_signal]
                ase_noise /= node_attenuation[optical_signal] / voa_attenuation
                self.port_to_optical_signal_ase_noise_out_qot.setdefault(out_port, {})
                self.port_to_optical_signal_ase_noise_out_qot[out_port][optical_signal] = ase_noise

            # if accumulated_NLI_noise:
            if optical_signal in self.port_to_optical_signal_nli_noise_in_qot[in_port]:
                nli_noise = self.port_to_optical_signal_nli_noise_in_qot[in_port][optical_signal]
                nli_noise /= node_attenuation[optical_signal] / voa_attenuation
                self.port_to_optical_signal_nli_noise_out_qot.setdefault(out_port, {})
                self.port_to_optical_signal_nli_noise_out_qot[out_port][optical_signal] = nli_noise

        ######################################### QOT ESTIMATION ENDS #########################################

        for op, link in out_ports_to_links.items():
            print("*** Switching at %s" % self.name)
            # Pass only the signals corresponding to the output port
            pass_through_signals = self.port_to_optical_signal_power_out[op].copy()
            pass_through_signals_qot = self.port_to_optical_signal_power_out_qot[op].copy()
            if op in self.port_to_optical_signal_ase_noise_out:
                ase = self.port_to_optical_signal_ase_noise_out[op].copy()
                ase_qot = self.port_to_optical_signal_ase_noise_out_qot[op].copy()
            else:
                ase = self.port_to_optical_signal_ase_noise_in[in_port].copy()
                ase_qot = self.port_to_optical_signal_ase_noise_in_qot[in_port].copy()

            if op in self.port_to_optical_signal_nli_noise_out:
                nli = self.port_to_optical_signal_nli_noise_out[op].copy()
                nli_qot = self.port_to_optical_signal_nli_noise_out_qot[op].copy()
            else:
                nli = self.port_to_optical_signal_nli_noise_in[in_port].copy()
                nli_qot = self.port_to_optical_signal_nli_noise_in_qot[in_port].copy()
            # Propagate signals through link
            link.propagate(pass_through_signals, ase, nli,
                           pass_through_signals_qot, ase_qot, nli_qot,
                           voa_compensation=self.voa_compensation)

    def get_node_attenuation(self, link_signals):
        """
        When switching, it computes the total node attenuation only
        for the signals passing through
        """
        node_attenuation = {}
        for optical_signal, _ in link_signals.items():
            wss_attenuation = 0.0
            wss_wd_attenuation = 0.0
            for wss_id, attenuation_tuple in self.wss_dict.items():
                wss_attenuation += attenuation_tuple[0]
                wss_wd_attenuation += attenuation_tuple[1][optical_signal.index - 1]
            total_attenuation = db_to_abs(wss_attenuation + wss_wd_attenuation)
            node_attenuation[optical_signal] = total_attenuation
        return node_attenuation

    def voa_reconf(self, link, output_power_dict, out_port,
                   accumulated_ASE_noise, accumulated_NLI_noise,
                   output_power_dict_qot, accumulated_ASE_noise_qot, accumulated_NLI_noise_qot):
        """
        wavelength dependent attenuation
        """
        if self.voa_function is 'flatten':
            # compute VOA compensation and re-propagate only if there is a function
            out_difference = {}
            for k, out_power in output_power_dict.items():
                # From the boost-amp, compute the difference between output power levels
                # and the target output power. Set this as the compensation function.
                delta = self.voa_target_out_power / out_power
                out_difference[k] = delta
            for optical_signal, voa_att in out_difference.items():
                # WSS attenuation and fixed VOA attenuation was inflicted at switching time,
                # hence, only inflict now the additional VOA attenuation to compensate
                # for the excursions generated at the boost-amp.
                if voa_att < 0:
                    self.port_to_optical_signal_power_out[out_port][optical_signal] /= voa_att
                    if len(accumulated_ASE_noise) > 0:
                        accumulated_ASE_noise[optical_signal] /= voa_att
                        self.port_to_optical_signal_ase_noise_out[out_port].update(accumulated_ASE_noise)
                    if len(accumulated_NLI_noise) > 0:
                        accumulated_NLI_noise[optical_signal] /= voa_att
                        self.port_to_optical_signal_nli_noise_out[out_port].update(accumulated_NLI_noise)
                else:
                    self.port_to_optical_signal_power_out[out_port][optical_signal] *= voa_att
                    if len(accumulated_ASE_noise) > 0:
                        accumulated_ASE_noise[optical_signal] *= voa_att
                        self.port_to_optical_signal_ase_noise_out[out_port].update(accumulated_ASE_noise)
                    if len(accumulated_NLI_noise) > 0:
                        accumulated_NLI_noise[optical_signal] *= voa_att
                        self.port_to_optical_signal_nli_noise_out[out_port].update(accumulated_NLI_noise)
            ######################################### QOT ESTIMATION BEGINS #########################################
            out_difference = {}
            for k, out_power in output_power_dict_qot.items():
                # From the boost-amp, compute the difference between output power levels
                # and the target output power. Set this as the compensation function.
                delta = self.voa_target_out_power / out_power
                out_difference[k] = delta
            for optical_signal, voa_att in out_difference.items():
                # WSS attenuation and fixed VOA attenuation was inflicted at switching time,
                # hence, only inflict now the additional VOA attenuation to compensate
                # for the excursions generated at the boost-amp.
                if voa_att < 0:
                    self.port_to_optical_signal_power_out_qot[out_port][optical_signal] /= voa_att
                    if len(accumulated_ASE_noise_qot) > 0:
                        accumulated_ASE_noise_qot[optical_signal] /= voa_att
                        self.port_to_optical_signal_ase_noise_out_qot[out_port].update(accumulated_ASE_noise_qot)
                    if len(accumulated_NLI_noise_qot) > 0:
                        accumulated_NLI_noise_qot[optical_signal] /= voa_att
                        self.port_to_optical_signal_nli_noise_out_qot[out_port].update(accumulated_NLI_noise_qot)
                else:
                    self.port_to_optical_signal_power_out_qot[out_port][optical_signal] *= voa_att
                    if len(accumulated_ASE_noise_qot) > 0:
                        accumulated_ASE_noise_qot[optical_signal] *= voa_att
                        self.port_to_optical_signal_ase_noise_out_qot[out_port].update(accumulated_ASE_noise_qot)
                    if len(accumulated_NLI_noise_qot) > 0:
                        accumulated_NLI_noise_qot[optical_signal] *= voa_att
                        self.port_to_optical_signal_nli_noise_out_qot[out_port].update(accumulated_NLI_noise_qot)
            ######################################### QOT ESTIMATION ENDS #########################################

            # Proceed with the re-propagation of effects. Same as last step in switch function.
            pass_through_signals = self.port_to_optical_signal_power_out[out_port]
            ase = accumulated_ASE_noise.copy()
            nli = accumulated_NLI_noise.copy()
            pass_through_signals_qot = self.port_to_optical_signal_power_out_qot[out_port]
            ase_qot = accumulated_ASE_noise.copy()
            nli_qot = accumulated_NLI_noise_qot.copy()
            link.reset_propagation_struct()
            # Propagate signals through link and flag voa_compensation to avoid looping
            link.propagate(pass_through_signals, ase, nli,
                           pass_through_signals_qot, ase_qot, nli_qot,
                           voa_compensation=False)


description_files_dir = 'description-files/'
description_files = {'linear': 'linear.txt'}
# description_files = {'wdg1': 'wdg1.txt',
#                      'wdg2': 'wdg2.txt',
#                      'wdg1_yj': 'wdg1_yeo_johnson.txt',
#                      'wdg2_yj': 'wdg2_yeo_johnson.txt'}


class Amplifier(Node):

    def __init__(self, name, amplifier_type='EDFA', target_gain=18.0,
                 noise_figure=(5.5, 90), noise_figure_function=None,
                 bandwidth=12.5e9, wavelength_dependent_gain_id=None,
                 boost=False, tmp_qot_id=1):
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
        self.system_gain_qot = target_gain
        self.noise_figure = self.get_noise_figure(noise_figure, noise_figure_function)
        self.input_power = {}  # dict of OpticalSignal to input power levels
        self.input_power_qot = {}  # dict of OpticalSignal to input power levels
        self.output_power = {}  # dict of OpticalSignal to output power levels
        self.output_power_qot = {}  # dict of OpticalSignal to output power levels
        self.ase_noise = {}
        self.ase_noise_qot = {}
        self.bandwidth = bandwidth
        self.wdgfunc = None
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

        self.wavelength_dependent_gain_qot = (self.load_wavelength_dependent_gain_qot())

        self.power_excursions_flag_1 = False  # When both are True system gain balancing is complete
        self.power_excursions_flag_2 = False

        self.power_excursions_flag_1_qot = False  # When both are True system gain balancing is complete
        self.power_excursions_flag_2_qot = False

        self.boost = boost
        self.nonlinear_noise = {}  # accumulated NLI noise to be used only in boost = True
        self.nonlinear_noise_qot = {}  # accumulated NLI noise to be used only in boost = True

        self.tmp_qot_id = tmp_qot_id
        self.monitor_flag = False
        self.monitor_unit = 14

    def power_excursions_flags_off(self):
        self.power_excursions_flag_1 = False
        self.power_excursions_flag_2 = False
        self.power_excursions_flag_1_qot = False
        self.power_excursions_flag_2_qot = False

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

    @staticmethod
    def load_wavelength_dependent_gain_qot():
        """
        :return: Return wavelength dependent gain array
        """
        with open(description_files_dir + 'linear.txt', "r") as f:
            return [float(line) for line in f]

    def get_wavelength_dependent_gain(self, signal_index):
        """
        Retrieve WDG by signal index
        :param signal_index:
        :return: WDG of signal
        """
        return self.wavelength_dependent_gain[signal_index - 1]

    def get_wavelength_dependent_gain_qot(self, signal_index):
        """
        Retrieve WDG by signal index
        :param signal_index:
        :return: WDG of signal
        """
        return self.wavelength_dependent_gain_qot[signal_index - 1]

    def active_wavelength_dependent_gain(self):
        """
        Retrieve in a list the WDG of the active channels
        :return: list active channels in amplifier
        """
        list_wdg = []
        for optical_signal, _power in self.output_power.items():
            list_wdg.append(self.get_wavelength_dependent_gain(optical_signal.index))
        return list_wdg

    def active_wavelength_dependent_gain_qot(self):
        """
        Retrieve in a list the WDG of the active channels
        :return: list active channels in amplifier
        """
        list_wdg = []
        for optical_signal, _power in self.output_power_qot.items():
            list_wdg.append(self.get_wavelength_dependent_gain_qot(optical_signal.index))
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

    def output_amplified_power(self, signal, in_power):
        """
        Compute the output power levels of each signal after amplification
        :param signal: signal object
        :param in_power: input signal power linear (mW)
        """
        system_gain = self.system_gain
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(signal.index)
        # Conversion from dB to linear
        system_gain_linear = db_to_abs(system_gain)
        wavelength_dependent_gain_linear = db_to_abs(wavelength_dependent_gain)
        output_power = in_power * system_gain_linear * wavelength_dependent_gain_linear
        self.output_power[signal] = output_power
        return output_power

    def output_amplified_power_qot(self, signal, in_power):
        """
        Compute the output power levels of each signal after amplification
        :param signal: signal object
        :param in_power: input signal power linear (mW)
        """
        # if self.tmp_qot_id % self.monitor_unit is 0 and self.monitor_flag:
        #     self.output_power_qot[signal] = self.output_power[signal]
        #     return self.output_power_qot[signal]
        # else:
        system_gain_qot = self.system_gain_qot
        wavelength_dependent_gain_qot = self.get_wavelength_dependent_gain_qot(signal.index)
        # Conversion from dB to linear
        system_gain_linear_qot = db_to_abs(system_gain_qot)
        wavelength_dependent_gain_linear_qot = db_to_abs(wavelength_dependent_gain_qot)

        output_power_qot = in_power * system_gain_linear_qot * wavelength_dependent_gain_linear_qot
        self.output_power_qot[signal] = output_power_qot
        return output_power_qot

    def stage_amplified_spontaneous_emission_noise(self, optical_signal, in_power, accumulated_noise=None):
        """
        :return:
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """
        if accumulated_noise:
            self.ase_noise[optical_signal] = accumulated_noise[optical_signal]

        # Set parameters needed for ASE model
        noise_figure_linear = db_to_abs(self.noise_figure[optical_signal.index])
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(optical_signal.index)
        system_gain = self.system_gain

        if optical_signal not in self.ase_noise:
            # set initial noise 50 dB below signal power
            init_noise = in_power / db_to_abs(50)
            self.ase_noise[optical_signal] = init_noise
        # Conversion from dB to linear
        gain_linear = db_to_abs(system_gain) * db_to_abs(wavelength_dependent_gain)
        ase_noise = self.ase_noise[optical_signal] * gain_linear + (noise_figure_linear * sc.h *
                                                                    optical_signal.frequency *
                                                                    self.bandwidth * (gain_linear - 1) * 1000)
        self.ase_noise[optical_signal] = ase_noise

    def stage_amplified_spontaneous_emission_noise_qot(self, optical_signal, in_power,
                                                       accumulated_noise=None):
        """
        :return:
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """
        # if self.tmp_qot_id % self.monitor_unit is 0 and self.monitor_flag:
        #     self.ase_noise_qot[optical_signal] = self.ase_noise[optical_signal]
        # else:
        if accumulated_noise:
            self.ase_noise_qot[optical_signal] = accumulated_noise[optical_signal]

        # Set parameters needed for ASE model
        noise_figure_linear = db_to_abs(self.noise_figure[optical_signal.index])
        wavelength_dependent_gain_qot = self.get_wavelength_dependent_gain_qot(optical_signal.index)
        system_gain_qot = self.system_gain_qot

        if optical_signal not in self.ase_noise_qot:
            # set initial noise 50 dB below signal power
            init_noise = in_power / db_to_abs(50)
            self.ase_noise_qot[optical_signal] = init_noise
        # Conversion from dB to linear
        gain_linear_qot = db_to_abs(system_gain_qot) * db_to_abs(wavelength_dependent_gain_qot)

        ase_noise = self.ase_noise_qot[optical_signal] * gain_linear_qot + (noise_figure_linear * sc.h *
                                                                            optical_signal.frequency *
                                                                            self.bandwidth *
                                                                            (gain_linear_qot - 1) * 1000)

        self.ase_noise_qot[optical_signal] = ase_noise

    def compute_power_excursions(self):
        """
        Balance system gain with respect with the mean
        gain of the signals in the amplifier: power excursions
        :return:
        """
        # Convert power levels from linear to dBm
        output_power_dBm = [abs_to_db(p) for p in self.output_power.values()]
        input_power_dBm = [abs_to_db(p) for p in self.input_power.values()]

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
        return self.output_power.copy(), self.input_power.copy(), out_in_difference

    def compute_power_excursions_qot(self):
        """
        Balance system gain with respect with the mean
        gain of the signals in the amplifier
        :return:
        """
        # if self.tmp_qot_id % self.monitor_unit is 0 and self.monitor_flag:
        #     self.system_gain_qot = self.system_gain
        # else:
        # Convert power levels from linear to dBm
        output_power_dBm = [abs_to_db(p) for p in self.output_power_qot.values()]
        input_power_dBm = [abs_to_db(p) for p in self.input_power_qot.values()]

        # Mean difference between output and input power levels
        out_in_difference = np.mean(output_power_dBm) - np.mean(input_power_dBm)
        # Compute the balanced system gain
        gain_difference = out_in_difference - self.target_gain
        system_gain_balance = self.system_gain_qot - gain_difference
        self.system_gain_qot = system_gain_balance
        # Flag check for enabling the repeated computation of balancing
        if self.power_excursions_flag_1_qot and (not self.power_excursions_flag_2_qot):
            self.power_excursions_flag_2_qot = True
        if not (self.power_excursions_flag_1_qot and self.power_excursions_flag_2_qot):
            self.power_excursions_flag_1_qot = True
        return self.output_power_qot.copy(), self.input_power_qot.copy(), out_in_difference

    def nli_compensation(self, accumulated_NLI_noise):
        """
        As the signal power and ASE noise suffer the impact from the
        amplification, the NLI noise also gets amplified.
        """
        for optical_signal, nli_noise in accumulated_NLI_noise.items():
            wavelength_dependent_gain = db_to_abs(self.get_wavelength_dependent_gain(optical_signal.index))
            accumulated_NLI_noise[optical_signal] = \
                nli_noise * db_to_abs(self.system_gain) * wavelength_dependent_gain
        self.nonlinear_noise.update(accumulated_NLI_noise)

    def nli_compensation_qot(self, accumulated_NLI_noise):
        for optical_signal, nli_noise in accumulated_NLI_noise.items():
            accumulated_NLI_noise[optical_signal] = nli_noise * db_to_abs(self.system_gain)
        self.nonlinear_noise_qot.update(accumulated_NLI_noise)

    def clean_optical_signals(self, optical_signals):
        for optical_signal in optical_signals:
            del self.input_power[optical_signal]
            del self.output_power[optical_signal]
            del self.ase_noise[optical_signal]
            if optical_signal in self.nonlinear_noise.keys():
                del self.nonlinear_noise[optical_signal]


class Monitor(Node):
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
    def order_signals(signals):
        signal_by_index = {signal.index: signal for signal in signals}
        indices = [signal.index for signal in signals]
        ordered_signals_by_index = sorted(indices)
        ordered_signals = [signal_by_index[i] for i in ordered_signals_by_index]
        return ordered_signals

    def get_list_gosnr(self):
        """
        Get the gOSNR values at this OPM as a list
        :return: gOSNR values at this OPM as a list
        """
        # print("Monitor.get_list_gosnr.%s" % self.name)
        optical_signals = self.amplifier.output_power.keys()
        optical_signals_list = []
        for optical_signal in optical_signals:
            optical_signals_list.append(self.get_gosnr(optical_signal))
        return optical_signals_list

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
        if self.amplifier.boost:
            if self.amplifier.tmp_qot_id is 1:
                nli_noise = 0.0
            else:
                nli_noise = self.amplifier.nonlinear_noise[optical_signal]
        else:
            nli_noise = self.link.nonlinear_interference_noise[self.span][optical_signal]
        gosnr_linear = output_power / (ase_noise + nli_noise * 1.0e0)
        gosnr = abs_to_db(gosnr_linear)
        return gosnr

    def monitor_gosnr(self, optical_signal):
        """
        Compute gOSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :return: gOSNR (mW)
        """
        output_power = self.amplifier.output_power[optical_signal]
        ase_noise = self.amplifier.ase_noise[optical_signal]
        nli_noise = self.link.nonlinear_interference_noise[self.span][optical_signal]
        gosnr = output_power / (ase_noise + nli_noise)
        return gosnr

    ########################### QOT ESTIMATION BEGINS ######################################
    def get_list_osnr_qot(self):
        """
        Get the OSNR values at this OPM as a list
        :return: OSNR values at this OPM as a list
        """
        optical_signals = self.amplifier.output_power_qot.keys()
        signals_list = []
        ordered_signals = self.order_signals(optical_signals)
        for optical_signal in ordered_signals:
            signals_list.append(self.get_osnr_qot(optical_signal))
        return signals_list

    def get_list_gosnr_qot(self):
        """
        Get the gOSNR values at this OPM as a list
        :return: gOSNR values at this OPM as a list
        """
        # print("Monitor.get_list_gosnr.%s" % self.name)
        optical_signals = self.amplifier.output_power_qot.keys()
        optical_signals_list = []
        for optical_signal in optical_signals:
            optical_signals_list.append(self.get_gosnr_qot(optical_signal))
        return optical_signals_list

    def get_osnr_qot(self, optical_signal):
        """
        Compute OSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :return: OSNR (linear)
        """
        output_power = self.amplifier.output_power_qot[optical_signal]
        ase_noise = self.amplifier.ase_noise_qot[optical_signal]
        osnr_linear = output_power / ase_noise
        osnr = abs_to_db(osnr_linear)
        return osnr

    def get_gosnr_qot(self, optical_signal):
        """
        Compute gOSNR levels of the signal
        :param optical_signal: OpticalSignal object
        :return: gOSNR (linear)
        """
        output_power = self.amplifier.output_power_qot[optical_signal]
        ase_noise = self.amplifier.ase_noise_qot[optical_signal]
        if self.amplifier.boost:
            if self.amplifier.tmp_qot_id is 1:
                nli_noise = 0.0
            else:
                nli_noise = self.amplifier.nonlinear_noise_qot[optical_signal]
        else:
            nli_noise = self.link.nonlinear_interference_noise_qot[self.span][optical_signal]
        gosnr_linear = output_power / (ase_noise + (nli_noise * 1.0e0))
        gosnr = abs_to_db(gosnr_linear)
        return gosnr
    ########################### QOT ESTIMATION ENDS ######################################

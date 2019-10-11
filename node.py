import units as unit
from pprint import pprint
import numpy as np
import scipy.constants as sc


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


class Node(object):

    input_port_base = 0
    output_port_base = 100  # higher value to ease debugging, might need to rethink its scalability

    def __init__(self, name):
        self.name = name
        self.ports_in = []
        self.ports_out = []
        self.port_to_node_in = {}  # dict of port no. to ingress connecting nodes
        self.port_to_node_out = {}  # dict of port no. to egress connecting nodes
        self.port_to_signal_in = {}  # dict of ports to input signals
        self.port_to_signal_out = {}  # dict of ports to output signals
        self.port_to_signal_power_in = {}  # dict of ports to input signals and power levels
        self.port_to_signal_power_out = {}  # dict of ports to output signals and power levels

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
        self.port_to_signal_out[new_output_port] = []
        # Enable monitoring of signal power levels at output port
        self.port_to_signal_power_out[new_output_port] = {}
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
        self.port_to_signal_in[new_input_port] = []
        # Enable monitoring of signal power levels at input port
        self.port_to_signal_power_in[new_input_port] = {}
        return new_input_port

    def describe(self):
        pprint(vars(self))


class OpticalLineSystem(Node):

    def __init__(self, name):
        Node.__init__(self, name)
        self.wss_attenuation = db_to_abs(6)  # Might want to enable this for dynamic allocation
        self.transceivers = []
        self.name_to_transceivers = {}  # dict of name of transceiver to transceiver objects
        self.transceiver_to_signals = {}  # dict of transceivers name to list of optical signal objects
        self.operation_power = db_to_abs(-2)  # operation power input in dBm to convert to linear

        self.wavelengths = {k: 'off' for k in range(1, 91)}  # only supporting 90 channels per OLS

        self.traffic = []  # list of traffic objects at nodes

        self.tmp_e2e = 0  # number of invocation of a Node

    def add_transceiver(self, transceiver_name, spectrum_band):
        """
        Add a new transceiver to the OLT
        :param transceiver_name: name of transceiver to add
        :param spectrum_band: spectrum band to function
        :return: added transceiver
        """
        if transceiver_name in self.name_to_transceivers:
            raise ValueError("Node.OpticalLineSystem.add_transceiver: Transceiver with this name already exist!")
        new_transceiver = Transceiver(transceiver_name, spectrum_band)
        self.name_to_transceivers[transceiver_name] = new_transceiver
        self.transceiver_to_signals[new_transceiver] = []
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
            raise ValueError("Node.OpticalLineSystem.delete_transceiver: transceiver does not exist!")
        transceiver = self.name_to_transceivers[transceiver_name]
        self.transceivers.remove(transceiver)
        del self.name_to_transceivers[transceiver_name]
        del self.transceiver_to_signals[transceiver_name]

    def add_channel_receiver(self, traffic, in_port, link):
        self.port_to_signal_power_in[in_port].update(link.signal_power_out)
        for channel, _power in self.port_to_signal_power_in[in_port].items():
            self.wavelengths[channel.index] = traffic
            self.port_to_signal_in[in_port].append(channel)
        self.tmp_e2e += 1

    def update_channel_receiver(self, traffic, in_port):
        for signal in traffic.signals:
            self.wavelengths[signal.index] = 'off'
            self.port_to_signal_in[in_port].remove(signal)
            del self.port_to_signal_power_in[in_port][signal]

    def add_channel_transmitter(self, traffic, transceiver, out_port, channels):
        """
        Add a reference to an optical signal from a transceiver
        Compute output power levels at port where channel is added
        Propagate transmission through the link passing the info of the node
        :param traffic
        :param transceiver:
        :param out_port:
        :param channels:
        :return:
        """
        # Save traffic instance to list for easy access
        self.traffic.append(traffic)
        # Retrieve transmission specifications to pass
        # to the signals to be installed
        spectrum_band = transceiver.spectrum_band
        channel_spacing = transceiver.channel_spacing
        symbol_rate = transceiver.symbol_rate
        bits_per_symbol = transceiver.bits_per_symbol
        # list containing the new signals
        signals = []
        for channel in channels:
            new_signal = OpticalSignal(channel, spectrum_band, channel_spacing, symbol_rate, bits_per_symbol)
            signals.append(new_signal)
            # Turn on wavelengths for this traffic instance
            self.wavelengths[channel] = traffic
            # Associate signals to a transceiver/modulator
            self.transceiver_to_signals[transceiver].append(new_signal)
        # Compute output power levels at output port
        self.compute_output_power_levels(out_port)
        # associate the signal objects to the traffic
        traffic.signals = signals
        # Pass transmission to traffic handler
        traffic.next_link_in_route(self)

    def reset(self, traffic, transceiver, out_port, rule_id):
        """
        Remove the traces of this traffic in this node
        :param traffic: traffic being removed
        :param transceiver: tx-transceiver from traffic
        :param out_port: output port for transmission
        :param rule_id: rule associated with traffic
        :return:
        """
        for signal in traffic.signals:
            self.wavelengths[signal.index] = 'off'
            self.transceiver_to_signals[transceiver].remove(signal)
            self.port_to_signal_out[out_port].remove(signal)
            del self.port_to_signal_power_out[out_port][signal]
        self.traffic.remove(traffic)
        traffic.next_link_in_route_rule_update(self, rule_id)

    def delete_channel(self, transceiver_name, optical_signal):
        """
        Delete signal reference attributed to a transceiver
        :param transceiver_name: name of transceiver containing the signal
        :param optical_signal: optical signal object to be deleted
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.OpticalLineSystem.delete_signal: transceiver does not exist!")
        self.transceiver_to_signals[transceiver_name].remove(optical_signal)

    def available_wavelengths(self):
        """
        Check for wavelengths 'off'
        :return: wavelength indexes where 'off'
        """
        return [key for key, value in self.wavelengths.items() if value is 'off']

    def compute_output_power_levels(self, out_port):
        # Check all transceiver - Maybe this is not correct...
        for transceiver in self.transceivers:
            if len(self.transceiver_to_signals[transceiver]) > 0:
                for channel in self.transceiver_to_signals[transceiver]:
                    output_power = self.operation_power / self.wss_attenuation
                    channel.power_at_output_interface[self] = output_power
                    self.port_to_signal_power_out[out_port][channel] = output_power
                    self.port_to_signal_out[out_port].append(channel)


class Transceiver(object):
    def __init__(self, name, spectrum_band='C', optical_carrier=1550.0,
                 channel_spacing=0.4*1e-9, bandwidth=2.99792458*1e9, modulation_format='PM-QPSK',
                 bits_per_symbol=2.0, symbol_rate=0.025 * 1e12):
        """
        :param channel_spacing: channel spacing in nanometers - float
        :param bandwidth: channel bandwidth in GHz - float
        :param modulation_format: modulation format name - string
        :param bits_per_symbol: bits per symbol according to modulation format = float
        :param symbol_rate: symbol rate in GBaud - float
        """
        self.id = id(self)
        self.name = name
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


class Roadm(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """

    def __init__(self, name, attenuation=18):
        """

        :param name:
        :param attenuation: total attenuation at the node. Default
        set to 18 dB since we are considering 9 dB per WSS, and 2 WSSs
        per task needed (Add/Drop/Pass-through).
        """
        Node.__init__(self, name)
        self.node_id = id(self)
        self.attenuation = attenuation

        self.traffic = []
        self.traffic_to_out_port = {}

        self.switch_table = {}

    def install_switch_rule(self, rule_id, in_port, out_port, signals):
        """
        Switching rule installation, accessible from a Control System
        :param rule_id: ID of rule (similar to VLAN id)
        :param in_port: input port for incoming signals
        :param out_port: switching/output port for incoming signals
        :param signals: signals involved in switching procedure
        :return:
        """
        self.switch_table[rule_id] = {'in_port': in_port,
                                      'out_port': out_port,
                                      'signals': signals}
        for signal in signals:
            self.port_to_signal_in[in_port].append(signal)
            self.port_to_signal_out[out_port].append(signal)

    def update_switch_rule(self, prev_rule_id, new_rule_id, in_port, out_port, signals, traffic_of_rule):
        """
        Update/create a new rule for switching
        :param prev_rule_id: previous rule ID
        :param new_rule_id: new rule ID
        :param in_port: input port for new rule (same as in prev rule)
        :param out_port: output port for new rule
        :param signals: signals to be switched (same as in prev rule)
        :param traffic_of_rule: traffic associated with previous rule
        :return:
        """
        # Change the rule in the current ROADM
        self.switch_table[new_rule_id] = {'in_port': in_port,
                                          'out_port': out_port,
                                          'signals': signals}

        prev_out_port = self.switch_table[prev_rule_id]['out_port']
        traffic_of_rule.reset(prev_out_port, prev_rule_id)

    def get_traffic_from_rule(self, rule_id, signals):
        """
        Given a rule, find the associated traffic to the
        output port and the signals
        :param rule_id: ID of the rule
        :param signals: signals attributed to both traffic and rule
        :return: traffic object
        """
        # Get the output for the given rule
        out_port = self.switch_table[rule_id]['out_port']
        for t, port in self.traffic_to_out_port.items():
            if port is out_port and t.signals is signals:
                return t
        return None

    def delete_switch_rule(self, rule_id):
        """
        Switching rule deletion from Control System
        :param rule_id: ID of rule
        :return:
        """
        in_port = self.switch_table[rule_id]['in_port']
        out_port = self.switch_table[rule_id]['out_port']
        signals = self.switch_table[rule_id]['signals']

        for signal in signals:
            list(filter(signal.__ne__,self.port_to_signal_in[in_port]))
            list(filter(signal.__ne__,self.port_to_signal_out[out_port]))

            del self.port_to_signal_power_in[in_port][signal]
            del self.port_to_signal_power_out[out_port][signal]

        del self.switch_table[rule_id]

    def add_channel_roadm(self, traffic, in_port, out_port):
        """
        Simulation of physical effects of signals traversing
        a ROADM node with two WSSs (attenuation) values
        :param traffic:
        :param in_port:
        :param out_port:
        :return:
        """
        # First check if there is switching rule
        if self.switching_rule(traffic, in_port, out_port):
            self.traffic.append(traffic)
            # Create a relation between the current traffic
            # and the output port that it will follow
            self.traffic_to_out_port[traffic] = out_port
            for signal, in_power in self.port_to_signal_power_in[in_port].items():
                if signal in traffic.signals:
                    # Inflict the ROADM (2xWSS) attenuation to the signals
                    self.port_to_signal_power_out[out_port][signal] = in_power / db_to_abs(self.attenuation)
            if len(self.traffic) > 1:
                # Keep track of the other traffic instances that
                # will get altered because of this new addition
                for t in self.traffic:
                    # Don't add if traffic follows same port, because
                    # the computation of the phy-effects is automated
                    if (t not in traffic.altered_traffic) and (self.traffic_to_out_port[t] != out_port):
                        # update the altered_traffic attribute in
                        # the Traffic object
                        traffic.altered_traffic[t] = self
            # Relay next action to the traffic object
            traffic.next_link_in_route(self)
        else:
            print("Node.Roadm.add_channel_roadm: There is no rule in %s to handle traffic." % self.name)
            return

    def switching_rule(self, traffic, in_port, out_port):
        """
        Check if there is a rule with the values from
        the parameters
        :param traffic: traffic object to check
        :param in_port: input port in rule
        :param out_port: output port in rule
        :return: True|False if found
        """
        found = False
        for rule, items in self.switch_table.items():
            if (items['in_port'] is in_port)\
                    and (items['out_port'] is out_port)\
                    and (items['signals'] is traffic.wavelength_indexes):
                found = True
                return found
        return found

    def update_channel_roadm(self, traffic, rule_id):
        """
        Simulation
        A switching rule changed in a previous ROADM,
        hence, we need to remove the instances of the previous
        traffic still allocated at this node.
        :return:
        """
        in_port = self.switch_table[rule_id]['in_port']
        out_port = self.switch_table[rule_id]['out_port']
        signals = self.switch_table[rule_id]['signals']

        for signal in traffic.signals:
            self.port_to_signal_in[in_port].remove(signal.index)
            self.port_to_signal_out[out_port].remove(signal.index)
            del self.port_to_signal_power_in[in_port][signal]
            del self.port_to_signal_power_out[out_port][signal]
        del self.traffic_to_out_port[traffic]
        self.traffic.remove(traffic)

        traffic.next_link_in_route_rule_update(self, rule_id)


description_files_dir = 'description-files/'
description_files = {'wdg1': 'wdg1.txt', 'wdg2': 'wdg2.txt'}


class Amplifier(Node):

    def __init__(self, name, amplifier_type='EDFA', target_gain=18.0,
                 noise_figure=(6.0, 90), noise_figure_function=None,
                 bandwidth=12.5e9, wavelength_dependent_gain_id='wdg1'):
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
        self.input_power = {}  # dict of signal to input power levels
        self.output_power = {}  # dict of signal to output power levels
        self.ase_noise = {}
        self.bandwidth = bandwidth
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

        self.balancing_flag_1 = False  # When both are True system gain balancing is complete
        self.balancing_flag_2 = False

        self.osnr = {}  # dict signal to osnr (temporal for debugging purposes)

    def balancing_flags_off(self):
        self.balancing_flag_1 = False
        self.balancing_flag_2 = False

    @staticmethod
    def load_wavelength_dependent_gain(wavelength_dependent_gain_id):
        """
        :param wavelength_dependent_gain_id: file name id (see top of script) - string
        :return: Return wavelength dependent gain array
        """
        wdg_file = description_files[wavelength_dependent_gain_id]
        with open(description_files_dir + wdg_file, "r") as f:
            return [float(line) for line in f]

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
        for signal, _power in self.output_power.items():
            list_wdg.append(self.get_wavelength_dependent_gain(signal.index))
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

    def stage_amplified_spontaneous_emission_noise(self, signal, in_power):
        """
        :return:
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """
        if signal not in self.ase_noise:
            # set initial noise 50 dB below signal power
            init_noise = in_power / db_to_abs(40)
            self.ase_noise[signal] = init_noise

        # Set parameters needed for ASE model
        noise_figure = self.noise_figure[signal.index]
        system_gain = self.system_gain - 1

        # Conversion from dB to linear
        system_gain_linear = db_to_abs(system_gain)

        ase_noise = (self.ase_noise[signal] * system_gain) +\
                    (noise_figure * sc.h * system_gain_linear * signal.frequency * self.bandwidth * 1000)

        self.ase_noise[signal] = ase_noise

    def balance_system_gain(self):
        """
        Balance system gain with respect with the mean
        gain of the signals in the amplifier
        :return:
        """
        # Convert power levels from linear to dBm
        output_power_dBm = [abs_to_db(p) for p in self.output_power.values()]
        input_power_dBm = [abs_to_db(p) for p in self.input_power.values()]
        # Mean difference between output and input power levels
        out_in_difference = np.mean(output_power_dBm) - np.mean(input_power_dBm)
        # Compute the balanced system gain
        system_gain_balance = self.system_gain + (self.target_gain - out_in_difference)
        self.system_gain = system_gain_balance
        # Flag check for enabling the repeated computation of balancing
        if self.balancing_flag_1 and (not self.balancing_flag_2):
            self.balancing_flag_2 = True
        if not(self.balancing_flag_1 and self.balancing_flag_2):
            self.balancing_flag_1 = True

    def set_osnr(self, signal):
        """
        Compute OSNR for debugging purposes.
        Must be relayed to a monitoring procedure/object
        :param signal:
        :return:
        """
        osnr_linear = self.output_power[signal] / self.ase_noise[signal]
        osnr = abs_to_db(osnr_linear)
        self.osnr[signal] = osnr

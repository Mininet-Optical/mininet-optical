import units as unit
from pprint import pprint
import numpy as np
import scipy.constants as sc
import random


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
        self.port_to_signal_in = {}  # dict of ports to input signals
        self.port_to_signal_out = {}  # dict of ports to output signals
        self.port_to_signal_power_in = {}  # dict of ports to input signals and power levels
        self.port_to_signal_power_out = {}  # dict of ports to output signals and power levels
        self.out_port_to_link = {}

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


class LineTerminal(Node):

    def __init__(self, name, transceivers=None):
        Node.__init__(self, name)
        self.transceivers = []
        self.name_to_transceivers = {}  # dict of name of transceiver to transceiver objects
        self.transceiver_to_signals = {}  # dict of transceivers name to list of optical signal objects

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
            raise ValueError("Node.LineTerminal.delete_transceiver: transceiver does not exist!")
        transceiver = self.name_to_transceivers[transceiver_name]
        self.transceivers.remove(transceiver)
        del self.name_to_transceivers[transceiver_name]
        del self.transceiver_to_signals[transceiver_name]

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
            new_signal = OpticalSignal(channel, spectrum_band, channel_spacing, symbol_rate, bits_per_symbol)
            signals.append(new_signal)
            # Associate signals to a transceiver/modulator
            self.transceiver_to_signals[transceiver].append(new_signal)
        # Start transmission
        self.start(transceiver, out_port)
        link = self.out_port_to_link[out_port]
        link.propagate(self.port_to_signal_power_out[out_port], accumulated_ASE_noise=None, accumulated_NLI_noise=None)

    def receiver(self, in_port, signal_power):
        self.port_to_signal_power_in[in_port].update(signal_power)
        print("%s.receiver.%s: Success!" % (self.__class__.__name__, self.name))

    def delete_channel(self, transceiver_name, optical_signal):
        """
        Delete signal reference attributed to a transceiver
        :param transceiver_name: name of transceiver containing the signal
        :param optical_signal: optical signal object to be deleted
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.LineTerminal.delete_signal: transceiver does not exist!")
        self.transceiver_to_signals[transceiver_name].remove(optical_signal)

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
        for channel in self.transceiver_to_signals[transceiver]:
            output_power = transceiver.operation_power
            channel.power_at_output_interface[self] = output_power
            self.port_to_signal_power_out[out_port][channel] = output_power
            self.port_to_signal_out[out_port].append(channel)


class Transceiver(object):
    def __init__(self, name, operation_power=-2, spectrum_band='C', optical_carrier=1550.0,
                 channel_spacing=0.4 * 1e-9, bandwidth=2.99792458 * 1e9, modulation_format='PM-QPSK',
                 bits_per_symbol=2.0, symbol_rate=0.025e12):
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


class Roadm(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """

    def __init__(self, name, attenuation=6):
        """

        :param name:
        :param attenuation: total attenuation at the node. Default
        set to 6 dB per task needed (Add/Drop/Pass-through).
        """
        Node.__init__(self, name)
        self.node_id = id(self)
        self.attenuation = attenuation

        self.switch_table = {}  # dict of rule id to dict with keys in_port, out_port and signal_indexes
        self.signal_to_out_port = {}  # dict OpticalSignal to output port in ROADM

        self.port_to_signal_ase_noise_out = {}  # dict out port to OpticalSignal and ASE noise
        self.port_to_signal_nli_noise_out = {}  # dict out port to OpticalSignal and NLI noise

    def install_switch_rule(self, rule_id, in_port, out_port, signals):
        """
        Switching rule installation, accessible from a Control System
        :param rule_id: ID of rule (similar to VLAN id)
        :param in_port: input port for incoming signals
        :param out_port: switching/output port for incoming signals
        :param signals: signals involved in switching procedure
        :return:
        """
        # arbitrary rule identifier
        self.switch_table[rule_id] = {'in_port': in_port,
                                      'out_port': out_port,
                                      'signals': signals}
        for signal in signals:
            self.signal_to_out_port[signal] = out_port

    def update_switch_rule(self, rule_id, new_out_port):
        """
        Update/create a new rule for switching
        :param rule_id: rule ID
        :param new_out_port: new output port for rule
        :return:
        """
        in_port = self.switch_table[rule_id]['in_port']
        prev_out_port = self.switch_table[rule_id]['out_port']
        signals = self.switch_table[rule_id]['signals']

        self.switch_table[rule_id]['out_port'] = new_out_port

        for signal in signals:
            self.signal_to_out_port[signal] = new_out_port

        # Clean the output port instances of the signals
        optical_signals = []
        for optical_signal, _power in self.port_to_signal_power_out[prev_out_port].items():
            if optical_signal.index in signals:
                optical_signals.append(optical_signal)

        # Clean and prevent signals from link propagation
        link = self.out_port_to_link[prev_out_port]
        link.clean_signals(optical_signals)

        for optical_signal in optical_signals:
            # Delete from structures in ROADM node
            del self.port_to_signal_power_out[prev_out_port][optical_signal]

            if prev_out_port in self.port_to_signal_ase_noise_out.keys() and \
                    prev_out_port in self.port_to_signal_nli_noise_out.keys():
                del self.port_to_signal_ase_noise_out[prev_out_port][optical_signal]
                del self.port_to_signal_nli_noise_out[prev_out_port][optical_signal]

        if prev_out_port in self.port_to_signal_ase_noise_out.keys() and \
                prev_out_port in self.port_to_signal_nli_noise_out.keys():
            ase = self.port_to_signal_ase_noise_out[prev_out_port].copy()
            nli = self.port_to_signal_nli_noise_out[prev_out_port].copy()
        else:
            ase = {}
            nli = {}

        # Propagate the changes in the switch by switching
        self.switch(in_port, self.port_to_signal_power_in[in_port], ase, nli)

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
            # Delete rule indication of output port
            del self.signal_to_out_port[signal]

        optical_signals = []
        # get the signal objects to be removed
        for signal in self.port_to_signal_power_out[out_port]:
            if signal.index in signals:
                optical_signals.append(signal)

        for signal in optical_signals:
            # delete signals from structures in the switch
            list(filter(signal.__ne__, self.port_to_signal_in[in_port]))
            list(filter(signal.__ne__, self.port_to_signal_out[out_port]))

            del self.port_to_signal_power_in[in_port][signal]
            del self.port_to_signal_power_out[out_port][signal]

            if out_port in self.port_to_signal_ase_noise_out.keys() and \
                    out_port in self.port_to_signal_nli_noise_out.keys():
                del self.port_to_signal_ase_noise_out[out_port][signal]
                del self.port_to_signal_nli_noise_out[out_port][signal]

        del self.switch_table[rule_id]

        # Clean signals from link propagation
        link = self.out_port_to_link[out_port]
        link.clean_signals(optical_signals)

    def switch(self, in_port, link_signals, accumulated_ASE_noise, accumulated_NLI_noise):
        """
        Switch the input signals to the appropriate output ports as established
        by the switching rules in the switch table (if any).
        :param in_port: input port where signals are being transmitted
        :param link_signals: the signals being transmitted
        :param accumulated_ASE_noise: ASE noise (if any)
        :param accumulated_NLI_noise: NLI noise (if any)
        :return:
        """
        # Keep track of in which ports there are signals
        out_ports_to_links = {}
        # Update input port structure for monitoring purposes
        self.port_to_signal_power_in[in_port].update(link_signals)
        for signal, in_power in self.port_to_signal_power_in[in_port].items():
            # Iterate through all signals since they all might have changed
            if signal.index in self.signal_to_out_port:
                # Find the output port as established when installing a rule
                out_port = self.signal_to_out_port[signal.index]
                # Attenuate signals power
                self.port_to_signal_power_out[out_port][signal] = in_power / db_to_abs(self.attenuation)
                if accumulated_ASE_noise:
                    # Attenuate signals noise power
                    accumulated_ASE_noise[signal] /= db_to_abs(self.attenuation)

                    if out_port not in self.port_to_signal_ase_noise_out.keys():
                        # Create an entry for the output port
                        self.port_to_signal_ase_noise_out[out_port] = {}
                    # Update structure
                    self.port_to_signal_ase_noise_out[out_port].update(accumulated_ASE_noise)

                if accumulated_NLI_noise:
                    if out_port not in self.port_to_signal_nli_noise_out.keys():
                        # Create an entry for the output port
                        self.port_to_signal_nli_noise_out[out_port] = {}
                    # Update structure
                    self.port_to_signal_nli_noise_out[out_port].update(accumulated_NLI_noise)

                if out_port not in out_ports_to_links.keys():
                    # keep track of the ports where signals will passed through
                    out_ports_to_links[out_port] = self.out_port_to_link[out_port]
            else:
                # We can trigger an Exception, but the signals wouldn't be propagated anyway
                print("%s.%s.switch unable to find rule for signal %s" % (self.__class__.__name__,
                                                                          self.name, signal.index))

        for op, link in out_ports_to_links.items():
            # Pass only the signals corresponding to the output port
            pass_through_signals = self.port_to_signal_power_out[op]
            if op in self.port_to_signal_ase_noise_out.keys():
                ase = self.port_to_signal_ase_noise_out[op].copy()
            else:
                ase = accumulated_ASE_noise.copy()

            if op in self.port_to_signal_nli_noise_out.keys():
                nli = self.port_to_signal_nli_noise_out[op].copy()
            else:
                nli = accumulated_NLI_noise.copy()
            # Propagate signals through link
            link.propagate(pass_through_signals, ase, nli)


description_files_dir = 'description-files/'
# description_files = {'linear': 'linear.txt'}
description_files = {'wdg1': 'wdg1.txt',
                     'wdg2': 'wdg2.txt',
                     'wdg1_yj': 'wdg1_yeo_johnson.txt',
                     'wdg2_yj': 'wdg2_yeo_johnson.txt'}


class Amplifier(Node):

    def __init__(self, name, amplifier_type='EDFA', target_gain=18.0,
                 noise_figure=(5.5, 90), noise_figure_function=None,
                 bandwidth=12.5e9, wavelength_dependent_gain_id=None,
                 boost=False):
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
        self.wdgfunc = None
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

        self.balancing_flag_1 = False  # When both are True system gain balancing is complete
        self.balancing_flag_2 = False

        self.boost = boost
        self.nonlinear_noise = {}  # accumulated NLI noise to be used only in boost = True

    def balancing_flags_off(self):
        self.balancing_flag_1 = False
        self.balancing_flag_2 = False

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

    def stage_amplified_spontaneous_emission_noise(self, signal, in_power, accumulated_noise=None):
        """
        :return:
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """
        if accumulated_noise:
            self.ase_noise[signal] = accumulated_noise[signal]

        # Set parameters needed for ASE model
        noise_figure_linear = db_to_abs(self.noise_figure[signal.index])
        wavelength_dependent_gain = self.get_wavelength_dependent_gain(signal.index)
        system_gain = self.system_gain

        if signal not in self.ase_noise:
            # set initial noise 50 dB below signal power
            init_noise = in_power / db_to_abs(50)
            self.ase_noise[signal] = init_noise
        # Conversion from dB to linear
        gain_linear = db_to_abs(system_gain) * db_to_abs(wavelength_dependent_gain)
        ase_noise = self.ase_noise[signal] * gain_linear + (noise_figure_linear * sc.h * signal.frequency *
                                                            self.bandwidth * (gain_linear-1) * 1000)
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
        # print(self.name + " output_power_dBm: %s" % str(output_power_dBm))
        # print(self.name + " input_power_dBm: %s" % str(input_power_dBm))

        # Mean difference between output and input power levels
        out_in_difference = np.mean(output_power_dBm) - np.mean(input_power_dBm)
        # Compute the balanced system gain
        gain_difference = out_in_difference - self.target_gain
        system_gain_balance = self.system_gain - gain_difference
        # print(self.name + " system_gain_balance: %s" % str(system_gain_balance))
        # print()
        self.system_gain = system_gain_balance
        # Flag check for enabling the repeated computation of balancing
        if self.balancing_flag_1 and (not self.balancing_flag_2):
            self.balancing_flag_2 = True
        if not (self.balancing_flag_1 and self.balancing_flag_2):
            self.balancing_flag_1 = True

    def clean_signals(self, signals):
        for signal in signals:
            del self.input_power[signal]
            del self.output_power[signal]
            del self.ase_noise[signal]
            if signal in self.nonlinear_noise.keys():
                del self.nonlinear_noise[signal]


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
        for signal in optical_signals:
            signals_list.append(self.get_osnr(signal))
        return signals_list

    def get_list_gosnr(self):
        """
        Get the gOSNR values at this OPM as a list
        :return: gOSNR values at this OPM as a list
        """
        # print("Monitor.get_list_gosnr.%s" % self.name)
        optical_signals = self.amplifier.output_power.keys()
        signals_list = []
        for signal in optical_signals:
            signals_list.append(self.get_gosnr(signal))
        return signals_list

    def get_osnr(self, signal):
        """
        Compute OSNR levels of the signal
        :param signal: OpticalSignal object
        :return: OSNR (linear)
        """
        output_power = self.amplifier.output_power[signal]
        ase_noise = self.amplifier.ase_noise[signal]
        osnr_linear = output_power / ase_noise
        osnr = abs_to_db(osnr_linear)
        return osnr

    def get_gosnr(self, signal):
        """
        Compute gOSNR levels of the signal
        :param signal: OpticalSignal object
        :return: gOSNR (linear)
        """
        output_power = self.amplifier.output_power[signal]
        ase_noise = self.amplifier.ase_noise[signal]
        if self.amplifier.boost:
            nli_noise = self.amplifier.nonlinear_noise[signal]
        else:
            nli_noise = self.link.nonlinear_interference_noise[self.span][signal]
        # print("%s.get_osnr span: %s ; power: %s ase_noise: %s nli_noise: %s" % (self.__class__.__name__,
        #                                                                         self.span, str(output_power),
        #                                                                         str(ase_noise),
        #                                                                         str(nli_noise * 1.0e0)))
        gosnr_linear = output_power / (ase_noise + (nli_noise * 1.0e0))
        gosnr = abs_to_db(gosnr_linear)
        return gosnr

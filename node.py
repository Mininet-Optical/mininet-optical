import units as unit


class Node(object):

    input_port_base = 0
    output_port_base = 100  # higher value to ease debugging

    def __init__(self, name):
        self.name = name
        self.dummy_interface = None
        self.ports = {}
        self.input_ports = {}  # dict of port no. to ingress connecting nodes
        self.output_ports = {}  # dict of port no. to egress connecting nodes

    def new_connection_ports(self, connected_node):
        """
        Create new connection ports between the object node and another one
        :param connected_node: node to establish connection with
        :return: created input and output ports
        """
        if len(self.input_ports) > 0:
            new_input_port = max(self.input_ports.keys()) + 1
        else:
            new_input_port = self.input_port_base
        self.input_ports[new_input_port] = connected_node

        if len(self.output_ports) > 0:
            new_output_port = max(self.output_ports.keys()) + 1
        else:
            new_output_port = self.output_port_base
        self.output_ports[new_output_port] = connected_node

        return new_input_port, new_output_port


class OpticalLineTerminal(Node):

    def __init__(self, name):
        Node.__init__(self, name)
        self.transceivers = []
        self.name_to_transceivers = {}  # dict of name of transceiver to transceiver objects
        self.transceiver_to_signals = {}  # dict of transceivers name to list of optical signal objects

    def add_transceiver(self, transceiver_name, spectrum_band):
        """
        Add a new transceiver to the OLT
        :param transceiver_name: name of transceiver to add
        :param spectrum_band: spectrum band to function
        :return: added transceiver
        """
        name = self.name + '-' + transceiver_name
        if name in self.name_to_transceivers:
            raise ValueError("Node.OpticalLineTerminal.add_transceiver: Transceiver with this name already exist!")
        new_transceiver = Transceiver(name, spectrum_band)
        self.name_to_transceivers[name] = new_transceiver
        self.transceivers.append(new_transceiver)
        return new_transceiver

    def update_transceiver(self, transceiver_name, **kwargs):
        transceiver = self.name_to_transceivers[transceiver_name]
        if 'operation_power' in kwargs:
            transceiver.operation_power = kwargs.get('operation_power')
        if 'spectrum_band' in kwargs:
            transceiver.spectrum_band = kwargs.get('spectrum_band')

    def delete_transceiver(self, transceiver_name):
        """
        Delete transceiver from OLT
        :param transceiver_name: name of transceiver to be deleted
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.OpticalLineTerminal.delete_transceiver: transceiver does not exist!")
        transceiver = self.name_to_transceivers[transceiver_name]
        self.transceivers.remove(transceiver)
        del self.name_to_transceivers[transceiver_name]
        del self.transceiver_to_signals[transceiver_name]

    def add_signal(self, transceiver_name, optical_signal):
        """
        Add a reference to an optical signal from a transceiver
        :param transceiver_name:
        :param optical_signal:
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.OpticalLineTerminal.add_signal: transceiver does not exist!")
        if transceiver_name not in self.transceiver_to_signals:
            self.transceiver_to_signals[transceiver_name] = []
        self.transceiver_to_signals[transceiver_name].append(optical_signal)

    def delete_signal(self, transceiver_name, optical_signal):
        """
        Delete signal reference attributed to a transceiver
        :param transceiver_name: name of transceiver containing the signal
        :param optical_signal: optical signal object to be deleted
        :return:
        """
        if transceiver_name not in self.name_to_transceivers:
            raise ValueError("Node.OpticalLineTerminal.delete_signal: transceiver does not exist!")
        self.transceiver_to_signals[transceiver_name].remove(optical_signal)


class Transceiver(object):
    def __init__(self, name, operation_power=-2, spectrum_band='C'):
        self.id = id(self)
        self.name = name
        self.operation_power = operation_power
        self.spectrum_band = spectrum_band

"""
The signal probably don't need to be here once physical effects simulation is distributed.
"""
class OpticalSignal(object):

    def __init__(self, index, channel_spacing=0.4*1e-9, launch_power=-2.0,
                 bandwidth=2.99792458*1e9, modulation_format="16QAM",
                 bits_per_symbol=4.0, symbol_rate=0.032*1e12):
        """
        :param index: signal index starting from 1 - int
        :param channel_spacing: channel spacing in nanometers - float
        :param launch_power: launch power in dBm - float
        :param bandwidth: channel bandwidth in GHz - float
        :param modulation_format: modulation format name - string
        :param bits_per_symbol: bits per symbol according to modulation format = float
        :param symbol_rate: symbol rate in GBaud - float
        """
        self.index = index
        self.wavelength = 1529.2 * unit.nm + index * channel_spacing
        self.frequency = unit.c / self.wavelength
        self.channel_spacing = channel_spacing
        self.launch_power = launch_power
        self.bandwidth = bandwidth
        self.modulation_format = modulation_format
        self.bits_per_symbol = bits_per_symbol
        self.symbol_rate = symbol_rate


class Roadm(Node):
    """
    This implementation of Reconfigurable Optical Add/Drop Multiplexing nodes considers
    only common ports. That is, not including the internal connections between reconfiguration
    components (i.e., WSSs).
    """
    port_base = 1

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


description_files_dir = 'description-files/'
description_files = {'wdg1': 'wdg1.txt', 'wdg2': 'wdg2.txt'}


class Amplifier(Node):

    def __init__(self, name, amplifier_type='EDFA', target_gain=18.0, noise_figure=(6.0, 90), noise_figure_function=None,
                 bandwidth=12.5e9, wavelength_dependent_gain_id='wdg1'):
        """
        :param target_gain: units: dB - float
        :param noise_figure: tuple with NF value in dB and number of channels (def. 90)
        :param noise_figure_function: custom NF function with values in dB
        :param bandwidth: measurement optical bandwidth units: GHz - float
        :param wavelength_dependent_gain_id: file name id (see top of script) units: dB - string
        """
        Node.__init__(self, name)
        self.amplifier_id = id(self)
        self.target_gain = target_gain
        self.system_gain = target_gain
        self.noise_figure = self.get_noise_figure(noise_figure, noise_figure_function)
        self.input_power = {}  # dict of port to input power levels
        self.output_power = {}  # dict of port to output power levels
        self.bandwidth = bandwidth
        self.wavelength_dependent_gain = (
            self.load_wavelength_dependent_gain(wavelength_dependent_gain_id))

    @staticmethod
    def load_wavelength_dependent_gain(wavelength_dependent_gain_id):
        """
        :param wavelength_dependent_gain_id: file name id (see top of script) - string
        :return: Return wavelength dependent gain array
        """
        wdg_file = description_files[wavelength_dependent_gain_id]
        with open(description_files_dir + wdg_file, "r") as f:
            return [float(line) for line in f]

    @staticmethod
    def get_noise_figure(noise_figure, noise_figure_function):
        """
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

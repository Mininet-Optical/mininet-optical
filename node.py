from units import *
from pprint import pprint
import random
from collections import namedtuple


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

    def include_optical_signal_in(self, optical_signal_tuple, power=None, ase_noise=None,
                                  nli_noise=None, in_port=None, src_node=None):
        """
        :param optical_signal_tuple: OpticalSignal object, OpticalSignal uid
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param in_port: input port of node (optional)
        :param src_node: src node (optional)
        """
        optical_signal = optical_signal_tuple[0]

        # update structures with the input ports of the current node
        if in_port is not None or in_port == 0:
            self.port_to_optical_signal_in.setdefault(in_port, [])
            if optical_signal_tuple not in self.port_to_optical_signal_in[in_port]:
                # a port can carry multiple signals
                self.port_to_optical_signal_in[in_port].append((optical_signal, optical_signal.uid))
                # for symmetry:
                self.optical_signal_to_port_in[optical_signal, optical_signal.uid] = in_port

        # update the structures with the source nodes (where signals are coming from)
        if src_node is not None:
            self.node_to_optical_signal_in.setdefault(src_node, [])
            if optical_signal_tuple not in self.node_to_optical_signal_in[src_node]:
                self.node_to_optical_signal_in[src_node].append((optical_signal, optical_signal.uid))
                self.optical_signal_to_node_in[(optical_signal, optical_signal.uid)] = src_node

        # but we need to associate a component with the state of the signal
        optical_signal.assoc_loc_in(self, power, ase_noise, nli_noise)

    def include_optical_signal_out(self, optical_signal_tuple, power=None, ase_noise=None,
                                   nli_noise=None, out_port=None, dst_node=None):
        """
        :param optical_signal_tuple: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param out_port: output port of node (optional)
        :param dst_node: dst node (optional)
        """
        optical_signal = optical_signal_tuple[0]

        if out_port is not None or out_port == 0:
            self.port_to_optical_signal_out.setdefault(out_port, [])
            if optical_signal_tuple not in self.port_to_optical_signal_out[out_port]:
                self.port_to_optical_signal_out[out_port].append(optical_signal_tuple)
                self.optical_signal_to_port_out[optical_signal, optical_signal.uid] = out_port

        if dst_node is not None:
            self.node_to_optical_signal_out.setdefault(dst_node, [])
            if optical_signal_tuple not in self.node_to_optical_signal_out[dst_node]:
                self.node_to_optical_signal_out[dst_node].append(optical_signal_tuple)
                self.optical_signal_to_node_out[optical_signal, optical_signal.uid] = dst_node

        optical_signal.assoc_loc_out(self, power, ase_noise, nli_noise)

    def remove_optical_signal(self, optical_signal_tuple):
        optical_signal = optical_signal_tuple[0]
        print("*** %s - %s removing signal: %s-%s" % (self.__class__.__name__,
                                                      self.name, optical_signal, optical_signal.uid))

        if (optical_signal, optical_signal.uid) in self.optical_signal_to_node_in:
            src_node = self.optical_signal_to_node_in[(optical_signal, optical_signal.uid)]
            if (optical_signal, optical_signal.uid) in self.node_to_optical_signal_in[src_node]:
                self.node_to_optical_signal_in[src_node].remove((optical_signal, optical_signal.uid))
            del self.optical_signal_to_node_in[(optical_signal, optical_signal.uid)]

        if (optical_signal, optical_signal.uid) in self.optical_signal_to_node_out:
            dst_node = self.optical_signal_to_node_out[(optical_signal, optical_signal.uid)]
            if (optical_signal, optical_signal.uid) in self.node_to_optical_signal_out[dst_node]:
                self.node_to_optical_signal_out[dst_node].remove((optical_signal, optical_signal.uid))
            del self.optical_signal_to_node_out[(optical_signal, optical_signal.uid)]

        if (optical_signal, optical_signal.uid) in self.optical_signal_to_port_in:
            port_in = self.optical_signal_to_port_in[optical_signal, optical_signal.uid]
            self.port_to_optical_signal_in[port_in].remove((optical_signal, optical_signal.uid))

            del self.optical_signal_to_port_in[optical_signal, optical_signal.uid]

        if (optical_signal, optical_signal.uid) in self.optical_signal_to_port_out:
            port_out = self.optical_signal_to_port_out[optical_signal, optical_signal.uid]
            self.port_to_optical_signal_out[port_out].remove((optical_signal, optical_signal.uid))
            del self.optical_signal_to_port_out[optical_signal, optical_signal.uid]
            link = self.port_to_link_out[port_out]
            link.remove_optical_signal((optical_signal, optical_signal.uid))

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        """Human-readable representation"""
        return '%s' % self.name


class LineTerminal(Node):

    def __init__(self, name, transceivers=None, receiver_threshold=20, monitor_mode='out'):
        Node.__init__(self, name)
        # list of transceivers in LineTerminal
        self.transceivers = []
        # dict of name of transceiver to transceiver objects
        self.name_to_transceivers = {}
        self.signal_info_dict_transceiver = {}  # what is this? used in receiver, but, is it needed?

        if monitor_mode:
            self.monitor = Monitor(name + "-monitor", component=self, mode=monitor_mode)

        if transceivers:
            self.add_transceivers(transceivers)

        self.rx_threshold_dB = receiver_threshold

    def monitor_query(self):
        if self.monitor:
            # start monitor
            self.monitor.start()
            return self.monitor

    def reset(self):
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
        transceiver_id = len(self.transceivers)
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

    def update_rx_threshold(self, new_rx_threshold):
        self.rx_threshold_dB = new_rx_threshold

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

    def configure_terminal(self, transceiver, channel, in_port=-1, lp_descriptor={}):
        """
        Program the channels that will be launched at transceivers
        :param transceiver: transceiver to use for transmission
        :param channel: the channels to be transmitted
        :param in_port: input port to terminal, 0 if none.
        :return:
        """
        # instantiate OpticalSignal object
        ase_noise, nli_noise = self.init_noise_structs(transceiver.operation_power)
        optical_signal = OpticalSignal(channel, transceiver.spectrum_band,
                                       transceiver.channel_spacing_H, transceiver.channel_spacing_nm,
                                       transceiver.symbol_rate, transceiver.bits_per_symbol,
                                       power=transceiver.operation_power, ase_noise=ase_noise, nli_noise=nli_noise,
                                       lp_descriptor=lp_descriptor)

        # include optical signal in LineTerminal list
        self.include_optical_signal_in((optical_signal, optical_signal.uid), in_port=in_port, src_node=self)

        # associate transceiver to optical_signal
        transceiver.assoc_optical_signal(optical_signal)

        # associate an output port to the signal
        self.include_optical_signal_out((optical_signal, optical_signal.uid), out_port=transceiver.id)

    def turn_on(self):
        self.propagate()

    def propagate(self):
        """
        Propagate must indicate a direction!
        """
        ports_out = []
        # check which output ports are launching signals
        for out_port, optical_signals in self.port_to_optical_signal_out.items():
            if len(optical_signals) > 0:
                ports_out.append(out_port)

        # if there are active ports
        # make a copy of the active ports
        pop_ports_out = ports_out.copy()
        for port_out in ports_out:
            # ports and signals for LTs are 1:1 match
            optical_signal_tuple = self.port_to_optical_signal_out[port_out][0]
            optical_signal = optical_signal_tuple[0]
            # init optical signal structs
            optical_signal.reset()

            # pass signal info to link
            link = self.port_to_link_out[port_out]
            # the inport of the link is the outport of the node
            link.include_optical_signal_in((optical_signal, optical_signal.uid), in_port=port_out)

            pop_ports_out.pop()
            if len(pop_ports_out) < 1:
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
            self.remove_optical_signal((optical_signal, optical_signal.uid))
        # call propagation with left-over signals (if any)
        self.propagate()

    @staticmethod
    def init_noise_structs(operation_power):
        noise = operation_power / db_to_abs(90)
        return noise, noise

    @staticmethod
    def osnr(power, ase_noise):
        return abs_to_db(power / ase_noise)

    @staticmethod
    def gosnr(power, ase_noise, nli_noise):
        return abs_to_db(power / (ase_noise + nli_noise* (12.5e9 / 32.0e9)))

    def receiver(self, src_node):
        # print("*** %s.receiver from %s:" % (self, src_node))

        signalInfoDict = {}
        for optical_signal_tuple in self.node_to_optical_signal_in[src_node]:
            optical_signal = optical_signal_tuple[0]
            in_port = self.optical_signal_to_port_in[optical_signal_tuple]

            if in_port < 0:
                continue

            signalInfoDict[optical_signal] = {'osnr': None, 'gosnr': None,
                                              'ber': None, 'success': False}

            # Get signal info
            power = optical_signal.loc_in_to_state[self]['power']
            ase_noise = optical_signal.loc_in_to_state[self]['ase_noise']
            nli_noise = optical_signal.loc_in_to_state[self]['nli_noise']

            # Compute OSNR and gOSNR
            osnr = self.osnr(power, ase_noise)
            gosnr = self.gosnr(power, ase_noise, nli_noise)

            signalInfoDict[optical_signal]['osnr'] = osnr
            signalInfoDict[optical_signal]['gosnr'] = gosnr

            if gosnr < self.rx_threshold_dB:
                # print("*** %s-%s - %s.receiver.%s: Failure!\ngOSNR: %f dB - rx-thd:%s dB" %
                #      (optical_signal, optical_signal.uid, self.__class__.__name__,
                #       self.name, gosnr, self.rx_threshold_dB))

                signalInfoDict[optical_signal]['success'] = False
                self.signal_info_dict_transceiver[in_port] = signalInfoDict
                self.receiver_callback(in_port, signalInfoDict)
            else:

                # print("*** %s-%s - %s.receiver.%s: Success!\ngOSNR: %f dB" %
                #      (optical_signal, optical_signal.uid, self.__class__.__name__, self.name, gosnr))

                signalInfoDict[optical_signal]['success'] = True
                self.signal_info_dict_transceiver[in_port] = signalInfoDict
                self.receiver_callback(in_port, signalInfoDict)

    def receiver_callback(self, in_port, signalDictInfo):
        return


class Transceiver(object):
    def __init__(self, transceiver_id, name, operation_power=0, spectrum_band='C', optical_carrier=1550.0,
                 channel_spacing_nm=0.4 * 1e-9, channel_spacing_H=50e9,
                 bandwidth=2.99792458 * 1e9, modulation_format='16-QAM',
                 bits_per_symbol=4.0, symbol_rate=32e9):
        """
        :param name: human readable ID
        :param transceiver_id: int, ID
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
        self.id = transceiver_id
        # operation power input in dBm to convert to linear
        # self.operation_power = db_to_abs(operation_power)
        self.operation_power = db_to_abs(operation_power) * 1e-3  # in Watts
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

    def remove_optical_signal(self):
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
                 power=None, ase_noise=None, nli_noise=None, data=None,
                 lp_descriptor={}):
        self.uid = id(self)
        # configuration attributes
        self.index = index
        self.frequency = self.spectrum_band_init_H[spectrum_band] + (channel_spacing_H * int(index))
        self.wavelength = c / self.frequency
        self.wavelength2 = self.spectrum_band_init_nm[spectrum_band] * nm + index * channel_spacing_nm
        self.data = data
        self.symbol_rate = symbol_rate
        self.bits_per_symbol = bits_per_symbol

        self.visited_elements = []

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

        # LP descriptor contains:
        # src_node, dst_node, src_visit
        if len(lp_descriptor) > 0:
            self.lp_descriptor = {'src_visit': 0, 'dst_visit': 0}
            self.lp_descriptor.update(lp_descriptor)
        else:
            self.lp_descriptor = None

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

        if loc not in self.visited_elements:
            self.visited_elements.append(loc)

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

        if loc not in self.visited_elements:
            self.visited_elements.append(loc)

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

    def __init__(self, name, wss_dict=None, equalization_function='flatten',
                 equalization_target_out_power=0, monitor_mode=None):

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
        self.equalization_target_out_power = {}
        self.equalization_compensation = True
        #\
        #    self.equalization_safety_check(equalization_function, equalization_target_out_power)
        # dict of rule id to dict with keys in_port, out_port and signal_indices
        self.switch_table = {}
        # initialized for dynamic performance
        self.port_to_optical_signal_in_roadm = {-1: []}
        self.optical_signal_to_port_in_roadm = {-1: []}
        self.node_to_optical_signal_in_roadm = {-1: []}
        self.optical_signal_to_node_in_roadm = {-1: []}

        self.node_to_rule_id_in = {-1: []}
        self.rule_id_to_node_in = {-1: []}

        if monitor_mode:
            self.monitor = Monitor(name + "-monitor", component=self, mode=monitor_mode)

        # GNPy additions
        self.target_output_power_dB = -17
        self.effective_output_power_dB = 0
        self.reference_power = 0

    def monitor_query(self):
        if self.monitor:
            # start monitor
            self.monitor.start()
            return self.monitor

    def configure_voa(self, channel_id, output_port, operational_power_dB):
        self.equalization_target_out_power[(channel_id, output_port)] = db_to_abs(operational_power_dB) * 1e-3

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

    def include_optical_signal_in_roadm(self, optical_signal_tuple, in_port):
        """
        Register the optical_signals that are coming in, in the event of interest
        and from which port are they entering
        :param optical_signal_tuple: OpticalSignal object
        :param in_port: input port of node (optional)
        """
        src_node = self.port_to_node_in[in_port]

        # If the key exist, this parameter has no effect.
        # If the key does not exist, this value becomes the key's value
        self.port_to_optical_signal_in_roadm.setdefault(in_port, [])
        if optical_signal_tuple not in self.port_to_optical_signal_in_roadm[in_port]:
            optical_signal = optical_signal_tuple[0]
            self.port_to_optical_signal_in_roadm[in_port].append((optical_signal, optical_signal.uid))

        self.node_to_optical_signal_in_roadm.setdefault(src_node, [])
        if optical_signal_tuple not in self.node_to_optical_signal_in_roadm[src_node]:
            optical_signal = optical_signal_tuple[0]
            self.node_to_optical_signal_in_roadm[src_node].append((optical_signal, optical_signal.uid))

    def install_switch_rule(self, rule_id, in_port, out_port, signal_indices, src_node=None):
        """
        Switching rule installation, accessible from a Control System
        :param rule_id: ID of rule (similar to VLAN id)
        :param in_port: input port for incoming signals
        :param out_port: switching/output port for incoming signals
        :param signal_indices: signal indices involved in switching procedure
        :param src_node: source node
        :return:
        """
        # arbitrary rule identifier
        for signal_index in signal_indices:
            self.switch_table[rule_id, in_port, signal_index] = out_port

        self.node_to_rule_id_in.setdefault(src_node, [])
        self.node_to_rule_id_in[src_node].append(rule_id)
        self.rule_id_to_node_in[rule_id] = src_node

    def update_switch_rule(self, rule_id, new_port_out):
        """
        Update/create a new rule for switching
        :param rule_id: rule ID
        :param new_port_out: new output port for rule
        :return:
        """
        # self.switch_table[rule_id, in_port, signal_index]
        switch_rules = self.get_switch_rules_id(rule_id)
        for switch_rule in switch_rules:
            in_port = switch_rule[1]
            signal_index = switch_rule[2]
            prev_port_out = self.switch_table[switch_rule]

            for optical_signal_tuple in self.port_to_optical_signal_out[prev_port_out]:
                optical_signal = optical_signal_tuple[0]
                if optical_signal.index == signal_index:
                    self.optical_signal_to_port_out[optical_signal, optical_signal.uid] = new_port_out
                    self.port_to_optical_signal_out[prev_port_out].remove((optical_signal, optical_signal.uid))
                    self.switch_table[rule_id, in_port, signal_index] = new_port_out  # replacement of rule

                    del self.equalization_target_out_power[optical_signal.index, prev_port_out]

                    link = self.port_to_link_out[prev_port_out]
                    link.remove_optical_signal((optical_signal, optical_signal.uid))

        src_node = self.rule_id_to_node_in[rule_id]
        self.switch(src_node)

    def get_switch_rules_id(self, rule_id):
        switch_rules = []
        for switch_rule in self.switch_table.keys():
            if switch_rule[0] == rule_id:
                switch_rules.append(switch_rule)
        return switch_rules

    def delete_switch_rule(self, rule_id):
        """
        Switching rule deletion from Control System
        :param rule_id: ID of rule
        :return:
        """
        # self.switch_table[rule_id, in_port, signal_index]
        switch_rules = self.get_switch_rules_id(rule_id)
        for switch_rule in switch_rules:
            in_port = switch_rule[1]
            signal_index = switch_rule[2]
            out_port = self.switch_table[switch_rule]
            # clean output port from signal
            for optical_signal in self.port_to_optical_signal_out[out_port]:
                if optical_signal.index == signal_index:
                    self.port_to_optical_signal_out[out_port].remove(optical_signal)

                    # clean register of signal in dst_node
                    dst_node = self.optical_signal_to_node_out[optical_signal, optical_signal.uid]
                    self.node_to_optical_signal_out[dst_node].remove(optical_signal)

                    del self.optical_signal_to_port_out[optical_signal, optical_signal.uid]
                    del self.optical_signal_to_node_out[optical_signal, optical_signal.uid]

                    del self.equalization_target_out_power[optical_signal.index, out_port]

                    # propagate clean-up across links and nodes
                    link = self.port_to_link_out[out_port]
                    link.remove_optical_signal(optical_signal)

            del self.switch_table[switch_rule]

            src_node = self.port_to_node_in[in_port]
            self.switch(src_node)

    def delete_switch_rules(self):
        """Delete all switching rules"""
        for ruleId in list(self.switch_table):
            self.delete_switch_rule(ruleId)

    def get_switch_rules(self, src_node):
        optical_signals = self.node_to_optical_signal_in[src_node]

        switch_rules = []
        for optical_signal, optical_signal.uid in optical_signals:
            if (optical_signal, optical_signal.uid) in self.optical_signal_to_port_in:
                in_port = self.optical_signal_to_port_in[optical_signal, optical_signal.uid]
                # then we search the switch table for a matching rule
                for switch_rule in self.switch_table.keys():
                    # self.switch_table[rule_id, in_port, signal_index]
                    if switch_rule[1] == in_port and switch_rule[2] == optical_signal.index:
                        switch_rules.append(switch_rule)

        return switch_rules

    def get_switch_rule(self, in_port, signal_index):
        # self.switch_table[rule_id, in_port, signal_index]
        for switch_rule, out_port in self.switch_table.items():
            if switch_rule[1] == in_port and switch_rule[2] == signal_index:
                return switch_rule

    def get_ports_and_signals_in(self):
        port_to_signal_in = {}
        for port_in, optical_signal in self.port_to_optical_signal_in_roadm.items():
            if port_in >= 0:
                port_to_signal_in[port_in] = optical_signal[0]
        return port_to_signal_in

    def can_propagate(self):
        for optical_signal_tuple in self.optical_signal_to_port_in:
            optical_signal = optical_signal_tuple[0]

            if optical_signal.lp_descriptor is None:
                # Not checking for loops, but not stopping transmission
                return True
            # Check the propagation of the signals across ROADMs
            if optical_signal.lp_descriptor['src_roadm'] is self:
                optical_signal.lp_descriptor['src_visit'] += 1
            elif optical_signal.lp_descriptor['dst_roadm'] is self:
                optical_signal.lp_descriptor['dst_visit'] += 1

        list_src_visits = []

        for optical_signal_tuple in self.optical_signal_to_port_in:
            optical_signal = optical_signal_tuple[0]
            list_src_visits.append(optical_signal.lp_descriptor['src_visit'])

        mean_src_visits = np.mean(list_src_visits)
        if mean_src_visits >= 30:  # AD: How to dynamically configure this parameter?
            return False
        return True

    def switch(self, src_node, att_flag=True):
        if not self.can_propagate():
            print('RoadmWarning:', self, "loop detected. Stopping propagation.")
            return

        # get switch rules from signals
        # coming from src_node
        switch_rules = self.get_switch_rules(src_node)

        if len(switch_rules) == 0:
            # We can trigger an Exception, but the signals wouldn't be propagated anyway
            print("*** %s unable to find rules for signals %s" % (
                self, self.optical_signal_to_node_in.keys()))
        else:
            # simulate PHY-propagation
            self.propagate_simulation(src_node)

            dst_nodes = []
            for optical_signal_tuple in self.node_to_optical_signal_in[src_node]:
                optical_signal = optical_signal_tuple[0]
                in_port = self.optical_signal_to_port_in[optical_signal, optical_signal.uid]
                if in_port < 0:
                    continue

                # find the port where signals should be switch towards
                switch_rule = self.get_switch_rule(in_port, optical_signal.index)

                if switch_rule is None:
                    print("*** %s unable to find rules for signal %s" % (
                        self, optical_signal))
                else:
                    # find output port from switch table
                    out_port = self.switch_table[switch_rule]

                    if out_port is not None or out_port == 0:
                        # get the destination node with the output port
                        dst_node = self.port_to_node_out[out_port]
                        if dst_node is not src_node:
                            if dst_node not in dst_nodes:
                                # build up the list of destinations
                                dst_nodes.append(dst_node)
                            # update the structures for the direction
                            self.include_optical_signal_out((optical_signal, optical_signal.uid),
                                                            out_port=out_port, dst_node=dst_node)

                            # pass signal to the respective link
                            link = self.port_to_link_out[out_port]
                            link.include_optical_signal_in((optical_signal, optical_signal.uid), in_port=out_port)

            # now we check if we have multiple destinations
            for dst_node in dst_nodes:
                # we get all optical signals going towards dst_node
                optical_signal_list = self.node_to_optical_signal_out[dst_node]
                output_ports = []
                for optical_signal_tuple in optical_signal_list:
                    optical_signal = optical_signal_tuple[0]
                    # we detect which signal is at which output port
                    if (optical_signal, optical_signal.uid) in self.optical_signal_to_port_out:
                        out_port = self.optical_signal_to_port_out[optical_signal, optical_signal.uid]
                        if out_port not in output_ports and out_port is not None:
                            # and we register these active output ports
                            output_ports.append(out_port)

                if len(output_ports) > 0:
                    # make a copy of active ports
                    pop_output_ports = output_ports.copy()
                    for out_port in output_ports:
                        link = self.port_to_link_out[out_port]
                        pop_output_ports.remove(out_port)
                        # if it's the last of our ports going towards that dst_node
                        # then is_last_port is True
                        if len(pop_output_ports) < 1:
                            link.propagate(equalization=self.equalization_compensation, is_last_port=True)
                        else:
                            link.propagate(equalization=self.equalization_compensation)

    def propagate_simulation(self, src_node):
        self.effective_output_power_dB = min(self.reference_power, self.target_output_power_dB)
        self.effective_loss = self.reference_power - self.target_output_power_dB
        carriers_power = []
        for optical_signal_tuple in self.node_to_optical_signal_in[src_node]:
            optical_signal = optical_signal_tuple[0]
            power_in = optical_signal.loc_in_to_state[self]['power']
            ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
            nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']

            total_power = power_in + ase_noise_in + nli_noise_in
            carriers_power.append(total_power)

        carriers_att = list(map(lambda x: abs_to_db(x * 1e3) - self.target_output_power_dB, carriers_power))
        exceeding_att = -min(list(filter(lambda x: x < 0, carriers_att)), default=0)
        carriers_att = list(map(lambda x: db_to_abs(x + exceeding_att), carriers_att))

        for optical_signal_tuple, carrier_att in zip(self.node_to_optical_signal_in[src_node], carriers_att):
            optical_signal = optical_signal_tuple[0]
            in_port = self.optical_signal_to_port_in[optical_signal, optical_signal.uid]
            if in_port < 0:
                continue

            # attenuate signal power
            power_in = optical_signal.loc_in_to_state[self]['power']
            ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
            nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']

            # retrieve the WSS wavelength-dependent attenuation (AD: probably obsolete).
            node_attenuation = self.get_node_attenuation(in_port)
            # retrieve the equalization attenuation function at the output ports (AD: to be updated).
            equalization_attenuation = self.equalization_attenuation

            power_out = power_in / carrier_att  # node_attenuation[optical_signal] / equalization_attenuation
            ase_noise_out = ase_noise_in / carrier_att  # node_attenuation[optical_signal] / equalization_attenuation
            nli_noise_out = nli_noise_in / carrier_att  # node_attenuation[optical_signal] / equalization_attenuation

            # update the structures for the direction
            self.include_optical_signal_out((optical_signal, optical_signal.uid), power=power_out,
                                            ase_noise=ase_noise_out, nli_noise=nli_noise_out)

    def get_node_attenuation(self, in_port):
        """
        When switching, it computes the total node attenuation only
        for the signals passing through
        """
        node_attenuation = {}
        for optical_signal_tuple in self.port_to_optical_signal_in[in_port]:
            optical_signal = optical_signal_tuple[0]
            wss_attenuation = 0.0
            wss_wd_attenuation = 0.0
            for wss_id, attenuation_tuple in self.wss_dict.items():
                wss_attenuation += attenuation_tuple[0]
                wss_wd_attenuation += attenuation_tuple[1][optical_signal.index - 1]
            total_attenuation = db_to_abs(wss_attenuation + wss_wd_attenuation)
            node_attenuation[optical_signal] = total_attenuation
        return node_attenuation

    def equalization_reconf(self, link, output_power_dict, node_out_port):
        """
        wavelength dependent attenuation
        """

        if self.equalization_function == 'flatten':
            # compute equalization compensation and re-propagate only if there is a function
            out_difference = {}
            for optical_signal, out_power in output_power_dict.items():
                if (optical_signal.index, node_out_port) not in self.equalization_target_out_power:
                    raise Exception("%s couldn't find equalization configuration for "
                                    "channel-index %s" % (self, optical_signal.index))
                # From the boost-amp, compute the difference between output power levels
                # and the target output power. Set this as the compensation function.
                delta = self.equalization_target_out_power[(optical_signal.index, node_out_port)] / out_power
                out_difference[optical_signal] = delta

            for optical_signal, equalization_att in out_difference.items():
                # attenuate signal power
                power_out = optical_signal.loc_out_to_state[self]['power']
                ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise']
                nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise']

                # WSS attenuation and fixed equalization attenuation was inflicted at switching time,
                # hence, only inflict now the additional equalization attenuation to compensate
                # for the excursions generated at the boost-amp.
                power = power_out * equalization_att
                ase_noise = ase_noise_out * equalization_att
                nli_noise = nli_noise_out * equalization_att

                self.include_optical_signal_out((optical_signal, optical_signal.uid),
                                                power=power, ase_noise=ase_noise, nli_noise=nli_noise)
                link.include_optical_signal_in((optical_signal, optical_signal.uid),
                                                power=power, ase_noise=ase_noise, nli_noise=nli_noise)

        link.propagate(equalization=False, is_last_port=True)


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
description_files = {'wdg1': 'linear.txt',
                     'wdg2': 'linear.txt'}


# 'wdg1_yj': 'wdg1_yeo_johnson.txt',
# 'wdg2_yj': 'wdg2_yeo_johnson.txt'}


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

        # GNPy params to be included
        self.interpol_dgt = None  # interpolated dynamic gain tilt
        self.interpol_gain_ripple = None  # gain ripple
        self.interpol_nf_ripple = None  # nf_ripple
        self.channel_freq = None  # SI channel frequencies
        # nf, gprofile, pin and pout attributes are set by interpol_params
        self.nf = None  # dB edfa nf at operational.gain_target
        self.gprofile = None
        self.pin_db = None
        self.nch = None
        self.pout_db = None
        self.target_pch_out_db = None
        self.effective_pch_out_db = None
        self.passive = False
        self.att_in = None
        self.carriers_in = None
        self.carriers_out = None
        # self.effective_gain = self.operational.gain_target
        # self.delta_p = self.operational.delta_p  # delta P with Pref (power swwep) in power mode
        # self.tilt_target = self.operational.tilt_target
        # self.out_voa = self.operational.out_voa


    def monitor_query(self):
        if self.monitor:
            # start monitor
            self.monitor.start()
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
        AD: TO BE UPDATED
        wavelength dependent attenuation
        """

        if self.equalization_function == 'flatten':
            # compute equalization compensation and re-propagate only if there is a function
            out_difference = {}
            for k, out_power in output_power_dict.items():
                # From the boost-amp, compute the difference between output power levels
                # and the target output power. Set this as the compensation function.
                delta = self.equalization_target_out_power / out_power
                out_difference[k] = delta

            for optical_signal, equalization_att in out_difference.items():
                power = optical_signal.loc_in_to_state[self]['power'] * equalization_att
                ase_noise = optical_signal.loc_in_to_state[self]['ase_noise'] * equalization_att
                nli_noise = optical_signal.loc_in_to_state[self]['nli_noise'] * equalization_att
                self.include_optical_signal_in((optical_signal, optical_signal.uid), power=power,
                                               ase_noise=ase_noise, nli_noise=nli_noise)

                # self.include_optical_signal_in(optical_signal)
        # self.equalization_flag_1=False
        # link.propagate_simulation(equalization=False, is_last_port=True)

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
        self.include_optical_signal_out((optical_signal, optical_signal.uid), power=output_power,
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

        #print("attempt to update at amplifier with nli noise", nli_noise_out)
        self.include_optical_signal_out((optical_signal, optical_signal.uid),
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
                                                      self.bandwidth * (gain_linear - 1))  # * 1000)
        # associate amp to optical signal at output interface
        # and update the optical signal state (power)
        self.include_optical_signal_out((optical_signal, optical_signal.uid),
                                        ase_noise=ase_noise_out, out_port=0, dst_node=dst_node)

    def compute_power_excursions(self):
        """
        NOT WORKING
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
        self.optical_signals = None

    def modify_mode(self, mode='out'):
        self.mode = mode

    def start(self):
        self.optical_signals = self.extract_optical_signal()

    def extract_optical_signal(self):
        """
        :return power: Returns Optical signals for the required objects
        """
        if self.mode == 'in':
            in_signals = []
            for _list in list(self.component.port_to_optical_signal_in.values()):
                if len(_list) > 0:
                    for optical_signal in _list:
                        in_signals.append(optical_signal)
            return in_signals
        else:
            out_signals = []
            for _list in list(self.component.port_to_optical_signal_out.values()):
                if len(_list) > 0:
                    for optical_signal in _list:
                        out_signals.append(optical_signal)
            return out_signals

    def get_list_osnr(self):
        """
        Get the OSNR values at this OPM as a list/dictionary
        :return: OSNR values at this OPM as a list/dictionary
        """
        optical_signals = self.extract_optical_signal()
        signals_list = []
        ordered_signals = self.order_signals(optical_signals)
        for optical_signal in ordered_signals:
            signals_list.append((optical_signal[0], self.get_osnr(optical_signal)))
        return signals_list

    def get_dict_osnr(self):
        """
        Get the OSNR values at this OPM as a dict
        :return: OSNR values at this OPM as a dict
        """
        return { sigtuple[0]: self.get_osnr(sigtuple)
                 for sigtuple in self.extract_optical_signal() }

    @staticmethod
    def order_signals(optical_signal_tuples):
        """
        Sort OpticalSignal tuples (!) by index
        :param optical_signals: list[(OpticalSignal,), ]
        :return: sorted list[(OpticalSignal,), ]
        """
        return sorted(optical_signal_tuples, key=lambda s:s[0].index)

    def get_list_gosnr(self):
        """
        Get the gOSNR values at this OPM as a list
        :return: gOSNR values at this OPM as a list
        """
        optical_signals = self.extract_optical_signal()
        signals_list = []
        ordered_signals = self.order_signals(optical_signals)
        for optical_signal in ordered_signals:
            signals_list.append((optical_signal[0], self.get_gosnr(optical_signal)))
        return signals_list

    def get_dict_gosnr(self):
        """
        Get the gOSNR values at this OPM as a dict
        :return: gOSNR values at this OPM as a dict
        """
        return { sigtuple[0]: self.get_gosnr(sigtuple)
                 for sigtuple in self.extract_optical_signal() }
    
    def get_power(self, optical_signal_tuple):
        optical_signal = optical_signal_tuple[0]
        if self.mode == 'out':
            power = optical_signal.loc_out_to_state[self.component]['power']
        else:
            power = optical_signal.loc_in_to_state[self.component]['power']
        return power
        
    def get_dict_power(self):
        """
        Get the power values at this OPM as a dict
        :return: power values at this OPM as a dict
        """
        return { sigtuple[0]: self.get_power(sigtuple)
                 for sigtuple in self.extract_optical_signal() }

    def get_ase_noise(self, optical_signal_tuple):
        optical_signal = optical_signal_tuple[0]
        if self.mode == 'out':
            ase_noise = optical_signal.loc_out_to_state[self.component]['ase_noise']
        else:
            ase_noise = optical_signal.loc_in_to_state[self.component]['ase_noise']
        return ase_noise

    def get_nli_noise(self, optical_signal_tuple):
        optical_signal = optical_signal_tuple[0]
        if self.mode == 'out':
            nli_noise = optical_signal.loc_out_to_state[self.component]['nli_noise']
        else:
            nli_noise = optical_signal.loc_in_to_state[self.component]['nli_noise']
        return nli_noise

    def get_osnr(self, optical_signal_tuple):
        """
        Compute OSNR levels of the signal
        :param optical_signal_tuple: OpticalSignal object
        :return: OSNR (linear)
        """
        optical_signal = optical_signal_tuple[0]
        if self.mode == 'out':
            power = optical_signal.loc_out_to_state[self.component]['power']
            ase_noise = optical_signal.loc_out_to_state[self.component]['ase_noise']
        else:
            power = optical_signal.loc_in_to_state[self.component]['power']
            ase_noise = optical_signal.loc_in_to_state[self.component]['ase_noise']
        osnr_linear = power / ase_noise
        osnr = abs_to_db(osnr_linear)
        return osnr

    def get_gosnr(self, optical_signal_tuple):
        """
        Compute gOSNR levels of the signal
        :param optical_signal_tuple: OpticalSignal object
        :return: gOSNR (linear)
        """
        optical_signal = optical_signal_tuple[0]
        if self.mode == 'out':
            output_power = optical_signal.loc_out_to_state[self.component]['power']
            ase_noise = optical_signal.loc_out_to_state[self.component]['ase_noise']
            nli_noise = optical_signal.loc_out_to_state[self.component]['nli_noise']
        else:
            output_power = optical_signal.loc_in_to_state[self.component]['power']
            ase_noise = optical_signal.loc_in_to_state[self.component]['ase_noise']
            nli_noise = optical_signal.loc_in_to_state[self.component]['nli_noise']

        gosnr_linear = output_power / (ase_noise + nli_noise) * (32e9/12.5e9)
        gosnr = abs_to_db(gosnr_linear)
        return gosnr

    def __repr__(self):
        return "<name: %s, component: %s,>" % (self.name, self.component)

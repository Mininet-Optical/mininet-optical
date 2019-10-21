from collections import namedtuple
import math
import units as unit
from pprint import pprint
import numpy as np


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


SpanTuple = namedtuple('Span', 'span amplifier')


class Link(object):
    """
    A Link refers to the connection between two network nodes (i.e., transceiver-ROADM or
    ROADM-ROADM). In the future we must enable network-element-node to controller-node
    connectivity.
    """

    def __init__(self, node1, node2,
                 output_port_node1, input_port_node2,
                 boost_amp):
        """

        :param node1: source Node object
        :param node2: destination Node object
        """
        if node1 == node2:
            raise ValueError("link.__init__ src_node must be different from dst_node!")

        self.id = id(self)
        self.node1 = node1
        self.node2 = node2
        self.output_port_node1 = output_port_node1
        self.input_port_node2 = input_port_node2
        self.boost_amp = boost_amp

        self.signal_power_in = {}  # dict of signals and power levels
        self.signal_power_out = {}  # dict of signals and power levels

        self.nonlinear_interference_noise = {}  # dict of spans to signals to nonlinear noise
        self.aggregated_ASE_noise = {}

        self.spans = []

        self.traffic = []

    def add_span(self, span, amplifier):
        """
        :param span: Span() object
        :param amplifier: Amplifier() object
        :return: appends a SpanTuple to the spans attribute
        """
        self.spans.append(SpanTuple(span, amplifier))

    def length(self):
        """
        :return: link length adding up span lengths in spans attribute
        """
        if len(self.spans) > 0:
            return sum(span.span.length for span in self.spans)
        return 0

    def describe(self):
        pprint(vars(self))

    def link_updated_rule(self, traffic, rule_id):
        """
        Update structures and invoke propagate_simulation()
        if there are signals affected
        :param traffic: Traffic object associated with this transmission
        :param rule_id: the Rule ID associated with this transmission
        :return:
        """
        for signal in traffic.signals:
            del self.signal_power_in[signal]
            del self.signal_power_out[signal]
        for span in self.spans:
            for signal in traffic.signals:
                del self.nonlinear_interference_noise[span][signal]
        self.traffic.remove(traffic)

        if len(self.signal_power_in) > 0:
            # print("Link entering")
            self.propagate_simulation()
        traffic.next_node_in_route_update(self, rule_id)

    def incoming_transmission(self, traffic, node, aggregated_ASE_noise):
        """
        Update structures and invoke propagate_simulation(
        :param traffic: Traffic object associated to transmission
        :param node: node where signals are coming from
        :param aggregated_ASE_noise: carried ASE noise until this point
        :return: traffic.next_node_in_route()
        """
        # Save traffic instance to list for easy access
        self.traffic.append(traffic)
        # Set output signals from node to input of the link
        for signal, power in node.port_to_signal_power_out[self.output_port_node1].items():
            self.signal_power_in[signal] = power

        self.propagate_simulation(aggregated_ASE_noise)
        # Relay to next node in transmission
        traffic.next_node_in_route(self)

    def propagate_simulation(self, aggregated_ASE_noise=None):
        """
        Compute the propagation of signals over this link
        :return:
        """
        # keep track of the signal power in link
        signal_power_progress = self.signal_power_in.copy()
        # aggregated_ASE_noise = None
        # If there is an amplifier compensating for the node
        # attenuation, compute the physical effects
        if self.boost_amp:
            # Enabling amplifier system gain balancing check
            while not (self.boost_amp.balancing_flag_1 and self.boost_amp.balancing_flag_2):
                for signal, in_power in self.signal_power_in.items():
                    self.boost_amp.input_power[signal] = in_power
                    output_power = self.boost_amp.output_amplified_power(signal, in_power)
                    # Update status of signal power in link
                    signal_power_progress[signal] = output_power
                self.boost_amp.balance_system_gain()
            # Reset balancing flags to original settings
            self.boost_amp.balancing_flags_off()
            # Compute ASE noise
            for signal, in_power in self.signal_power_in.items():
                self.boost_amp.stage_amplified_spontaneous_emission_noise(signal,
                                                                          in_power,
                                                                          aggregated_noise=aggregated_ASE_noise)
            aggregated_ASE_noise = self.boost_amp.ase_noise.copy()

        # Needed for the subsequent computations
        prev_amp = self.boost_amp
        nonlinear_interference_noise = {}
        nonlinear_noise = self.init_nonlinear_noise()
        for span, amplifier in self.spans:
            span.input_power = signal_power_progress
            # Compute linear effects from the fibre
            for signal, power in signal_power_progress.items():
                signal_power_progress[signal] = power / span.attenuation()

            # Compute nonlinear effects from the fibre
            signals_list = list(signal_power_progress.keys())
            if len(signal_power_progress) > 1 and prev_amp:
                signal_power_progress = self.zirngibl_srs(signals_list, signal_power_progress, span)

                # Store not normalized power and noise levels
                # to be considered in the power excursion calculation

                not_normalized_power = signal_power_progress
                not_normalized_noise = prev_amp.ase_noise

                normalized_power, normalized_noise = self.normalize_channel_levels(
                    signal_power_progress,
                    prev_amp.ase_noise,
                    prev_amp.active_wavelength_dependent_gain())
                # Consider power excursion and propagation per-span
                signal_power_progress = self.power_excursion_propagation(
                    normalized_power, normalized_noise,
                    not_normalized_power, not_normalized_noise)

            if len(signal_power_progress) > 2 and prev_amp:
                # Compute nonlinear interference noise, passing the node_amplifier
                # because its amplification gain impacts negatively the nonlinear
                # interference.
                nonlinear_interference_noise[span] = self.output_nonlinear_noise(
                    nonlinear_noise,
                    signals_list,
                    span,
                    prev_amp)
                self.nonlinear_interference_noise[span] = nonlinear_interference_noise[span]
                nonlinear_noise = nonlinear_interference_noise[span]
                """
                pprint("nonlinear_interference_noise")
                pprint(nonlinear_interference_noise)
                print("¢¢¢")
                """
            # Compute amplifier compensation
            if amplifier:
                # Enabling balancing check
                while not (amplifier.balancing_flag_1 and amplifier.balancing_flag_2):
                    for signal, in_power in signal_power_progress.items():
                        amplifier.input_power[signal] = in_power
                        output_power = amplifier.output_amplified_power(signal, in_power)
                        # Update status of signal power in link
                        self.signal_power_out[signal] = output_power
                    amplifier.balance_system_gain()
                # Reset balancing flags to original settings
                amplifier.balancing_flags_off()
                signal_power_progress = self.signal_power_out.copy()

                # Compute ASE noise
                for signal, in_power in self.signal_power_in.items():
                    amplifier.stage_amplified_spontaneous_emission_noise(signal,
                                                                         in_power,
                                                                         aggregated_noise=aggregated_ASE_noise)
                    nonlinear_noise[signal] = nonlinear_noise[signal] * amplifier.system_gain
                aggregated_ASE_noise.update(amplifier.ase_noise)
            else:
                for signal, in_power in signal_power_progress.items():
                    # Update status of signal power in link
                    self.signal_power_out[signal] = in_power

            prev_amp = amplifier
            if aggregated_ASE_noise:
                self.aggregated_ASE_noise.update(aggregated_ASE_noise)

    @staticmethod
    def zirngibl_srs(signals, active_channels, span):
        """
        Computation taken from : M. Zirngibl Analytical model of Raman gain effects in massive
        wavelength division multiplexed transmission systems, 1998. - Equations 7,8.
        :param signals: signals interacting at given transmission - list[Signal() object]
        :param active_channels: power levels at the end of span - dict{signal_index: power levels}
        :param span: Span() object
        :return:
        """
        min_wavelength_index = 90
        max_wavelength_index = 0
        min_signal = None
        max_signal = None
        for signal in signals:
            if signal.index < min_wavelength_index:
                min_signal = signal
                min_wavelength_index = signal.index
            if signal.index > max_wavelength_index:
                max_signal = signal
                max_wavelength_index = signal.index
        frequency_min = min_signal.frequency  # minimum frequency of longest wavelength
        frequency_max = max_signal.frequency  # maximum frequency of shortest wavelength

        effective_length = span.effective_length  # SMF effective distance
        beta = span.raman_coefficient

        total_power = 0  # Total input power calculated by following loop
        for channel, power_per_channel in active_channels.items():
            total_power += power_per_channel * unit.mW

        # Calculate delta P for each channel
        for signal in signals:
            frequency = signal.frequency
            r1 = beta * total_power * effective_length * (frequency_max - frequency_min) * math.e ** (
                    beta * total_power * effective_length * (frequency_max - frequency))  # term 1
            r2 = math.e ** (beta * total_power * effective_length * (frequency_max - frequency_min)) - 1  # term 2

            delta_p = float(r1 / r2)  # Does the arithmetic in mW
            active_channels[signal] *= delta_p

        return active_channels

    @staticmethod
    def normalize_channel_levels(power_levels, noise_levels, wavelength_dependent_gains):
        """
        :param power_levels: units: mW - list[float,]
        :param noise_levels: units: linear - list[float,]
        :param wavelength_dependent_gains: units: dB list[float,]
        :return: dictionary of normalized power and noise - dict{signal_index: power/noise}
        """
        # Sum amplifier attenuation for each channel
        # Calculate the main system gain of the loaded channels
        # (i.e. mean wavelength gain)
        loaded_gains_db = wavelength_dependent_gains
        total_system_gain_db = sum(loaded_gains_db)
        channel_count = len(wavelength_dependent_gains)
        mean_system_gain_db = total_system_gain_db / float(channel_count)
        mean_system_gain_abs = db_to_abs(mean_system_gain_db)

        # Affect the power and noise with the mean of wavelength gain
        normalized_power = {k: abs(x / mean_system_gain_abs) for k, x in power_levels.items()}
        normalized_noise = {k: abs(x / mean_system_gain_abs) for k, x in noise_levels.items()}

        return normalized_power, normalized_noise

    @staticmethod
    def power_excursion_propagation(normalized_power, normalized_noise,
                                    not_normalized_power, not_normalized_noise):
        """
        :param normalized_power: dict{signal_index: power - float}
        :param normalized_noise: dict{signal_index: noise - float}
        :param not_normalized_power: dict{signal_index: power - float}
        :param not_normalized_noise: dict{signal_index: noise - float}
        :return: dictionary with the power excursion propagated in the signal power levels
        """
        # Calculate total power values given by the form: P*N
        total_power = {}
        for k in normalized_power.keys():
            power = normalized_power[k]
            noise = normalized_noise[k]
            total_power[k] = abs(power * noise + power)
        total_power_old = {}
        for k in normalized_power.keys():
            power = not_normalized_power[k]
            noise = not_normalized_noise[k]
            total_power_old[k] = abs(power * noise + power)

        # Calculate excursion
        excursion = max(p / op for p, op in zip(total_power.values(), total_power_old.values()))

        # Propagate power excursion
        power_excursion_prop = {k: p * excursion for k, p in total_power.items()}  # new

        # update current power levels with the excursion propagation
        return power_excursion_prop

    def init_nonlinear_noise(self):
        nonlinear_noise = {}
        for signal, in_power in self.signal_power_in.items():
            nonlinear_noise[signal] = in_power / db_to_abs(50)
        return nonlinear_noise

    def output_nonlinear_noise(self, nonlinear_noise, signals, span, amplifier):
        """
        :param nonlinear_noise:
        :param signals: signals interacting at given transmission - list[Signal() object]
        :param span: Span() object
        :param amplifier: Amplifier() object at beginning of span
        :return: dict{signal_index: accumulated NLI noise levels}
        """
        amplifier_gain = db_to_abs(amplifier.system_gain)
        nonlinear_noise_new = self.nonlinear_noise(signals, span, amplifier_gain)
        out_noise = {}
        for signal, value in nonlinear_noise.items():
            # pprint("Adding %s with %s" % (nonlinear_noise[signal], nonlinear_noise_new[signal]))
            out_noise[signal] = nonlinear_noise[signal] + nonlinear_noise_new[signal]
        return out_noise

    def nonlinear_noise(self, signals, span, lump_gain):
        """
        Computation taken from: Poggiolini, P., et al. "Accurate Non-Linearity Fully-Closed-Form Formula
        based on the GN/EGN Model and Large-Data-Set Fitting." Optical Fiber Communication Conference.
        Optical Society of America, 2019. Equations 1-4
        :param signals: signals interacting at given transmission - list[Signal() object]
        :param span: Span() object
        :param lump_gain: EDFA target gain + wavelength dependent gain - float
        :return: Nonlinear Interference noise - dictionary{signal_index: NLI}
        """
        nonlinear_noise_struct = {}
        channels_index = []
        index_to_signal = {}
        for channel in signals:
            nonlinear_noise_struct[channel] = None
            channels_index.append(channel.index)
            index_to_signal[channel.index] = channel
        sorted(channels_index)
        channel_center = channels_index[int(math.floor(len(self.signal_power_in.keys()) / 2))]
        frequency_center = index_to_signal[channel_center].frequency

        # Retrieve fiber properties from span
        b2 = span.dispersion_coefficient
        b3 = span.dispersion_slope
        alpha = span.loss_coefficient
        gamma = span.non_linear_coefficient
        span_length = span.length

        for signal in signals:
            channel_under_test = signal.index
            frequency_cut = signal.frequency
            symbol_rate_cut = signal.symbol_rate
            bits_per_symbol_cut = signal.bits_per_symbol
            gross_bit_rate_cut = symbol_rate_cut * np.log2(bits_per_symbol_cut)
            bw_cut = gross_bit_rate_cut / (2 * np.log2(4))  # full bandwidth of the nth channel (THz).
            pwr_cut = self.signal_power_in[signal]
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            nonlinear_noise_term2 = 0

            for ch in signals:
                # omit channel under test
                if ch == channel_under_test:
                    continue

                frequency_ch = ch.frequency
                symbol_rate_ch = signal.symbol_rate
                bits_per_symbol_ch = signal.bits_per_symbol
                gross_bit_rate_ch = symbol_rate_ch * np.log2(bits_per_symbol_ch)
                bw_ch = gross_bit_rate_ch / (2 * np.log2(4))  # full bandwidth of the nth channel (THz).
                pwr_ch = self.signal_power_in[ch]
                g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)

                b2_eff_nch = b2 + unit.pi * b3 * (
                        frequency_ch + frequency_cut - 2 * frequency_center)  # FWM-factor - [1], Eq. (5)
                b2_eff_ncut = b2 + unit.pi * b3 * (
                        2 * frequency_cut - 2 * frequency_center)  # FWM-factor - [1], Eq. (6)

                nch_dividend1 = math.asinh(
                    (unit.pi ** 2 / 2) * abs(b2_eff_nch / alpha) *
                    (frequency_ch - frequency_cut + (bw_ch / 2)) * bw_cut)
                nch_divisor1 = 8 * unit.pi * abs(b2_eff_nch) * alpha

                nch_dividend2 = math.asinh(
                    (unit.pi ** 2 / 2) * abs(b2_eff_nch / alpha) *
                    (frequency_ch - frequency_cut - (bw_ch / 2)) * bw_cut)
                nch_divisor2 = 8 * unit.pi * abs(b2_eff_nch) * alpha

                _nch = (nch_dividend1 / float(nch_divisor1)) - (
                        nch_dividend2 / float(nch_divisor2))  # [1], Eq. (3)

                cut_dividend = math.asinh((unit.pi ** 2 / 2) * abs(b2_eff_ncut / (2 * alpha)) * bw_cut ** 2)
                cut_divisor = 4 * unit.pi * abs(b2_eff_ncut) * alpha
                _cut = cut_dividend / float(cut_divisor)  # [1], Eq. (4)

                nonlinear_noise_term2 += (2 * g_ch ** 2 * _nch + g_cut ** 2 * _cut)

            nonlinear_noise_term1 = 16 / 27.0 * gamma ** 2 * lump_gain * math.e ** (-2 * alpha * span_length) * g_cut
            # Justify the multiplication by 10 below:
            # balancing units
            nonlinear_noise = nonlinear_noise_term1 * nonlinear_noise_term2
            signal_under_test = index_to_signal[channel_under_test]
            nonlinear_noise_struct[signal_under_test] = abs(nonlinear_noise)
        return nonlinear_noise_struct


class Span(object):

    def __init__(self, fibre_type='SMF', length=20.0):
        """
        :param length: optical fiber span length in km - float
        :param fibre_type: optical fiber type - string
        """
        self.span_id = id(self)
        self.fibre_type = fibre_type
        self.length = length * unit.km
        self.fibre_attenuation = 0.22 / unit.km  # fiber attenuation in decibels/km
        self.loss_coefficient = 1 - 10 ** (self.fibre_attenuation / 10.0)
        self.effective_length = (1 - math.e ** (-self.loss_coefficient * self.length)) / self.loss_coefficient
        self.non_linear_coefficient = 1.3 / unit.km  # gamma fiber non-linearity coefficient [W^-1 km^-1]
        self.dispersion_coefficient = -21 * (unit.ps ** 2 / unit.km)  # B_2 dispersion coefficient [ps^2 km^-1]
        self.dispersion_slope = 0.1452 * (unit.ps ** 3 / unit.km)  # B_3 dispersion slope in (ps^3 km^-1)
        self.effective_area = 80 * unit.um * unit.um  # Aeff - SMF effective area
        self.raman_gain = 7.0*1e-12 * unit.cm / unit.W  # r - Raman Gain in SMF
        self.raman_amplification_band = 15 * unit.THz  # Raman amplification band ~15THz
        # Raman coefficient
        self.raman_coefficient = self.raman_gain / (2 * self.effective_area * self.raman_amplification_band)

        self.input_power = {}  # dict signal to input power
        self.output_power = {}  # dict signal to output power

    def describe(self):
        pprint(vars(self))

    def attenuation(self):
        return db_to_abs(self.fibre_attenuation * self.length)

from collections import namedtuple
import math
import units as unit
from pprint import pprint
import numpy as np
import warnings
import json
import sys

warnings.filterwarnings('error')

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


SpanTuple = namedtuple('Span', 'span amplifier')


class Link(object):
    """
    A Link refers to the connection between two network nodes (i.e., transceiver-ROADM or
    ROADM-ROADM). In the future we must enable network-element-node to controller-node
    connectivity.
    """

    def __init__(self, node1, node2,
                 output_port_node1, input_port_node2,
                 boost_amp, spans=None):
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

        self.optical_signal_power_in = {}  # dict of signals and power levels
        self.optical_signal_power_out = {}  # dict of signals and power levels

        self.optical_signal_power_in_qot = {}  # dict of signals and power levels
        self.optical_signal_power_out_qot = {}  # dict of signals and power levels

        self.nonlinear_interference_noise = {}  # dict of spans to signals to nonlinear noise
        self.nonlinear_interference_noise_qot = {}  # dict of spans to signals to nonlinear noise
        self.nli_id = 1  # For debugging purposes of NLI noise aggregation
        self.accumulated_ASE_noise = {}
        self.accumulated_ASE_noise_qot = {}
        self.accumulated_NLI_noise = {}
        self.accumulated_NLI_noise_qot = {}

        self.spans = spans or []

        self.traffic = []
        self.monitor_flag = False
        self.monitor_unit = 14.0

        self.srs_effect = True

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

    def clean_optical_signals(self, optical_signals):
        """
        A rule deletion or update has been called. Hence, remove the
        instances of signals in the link structure where the previously
        used signals in those ports were.
        :param optical_signals: signals to be removed on this link
        :return:
        """
        for optical_signal in optical_signals:
            del self.optical_signal_power_in[optical_signal]
            del self.optical_signal_power_out[optical_signal]
            if optical_signal in self.accumulated_ASE_noise.keys() and \
                    optical_signal in self.accumulated_NLI_noise.keys():
                del self.accumulated_ASE_noise[optical_signal]
                del self.accumulated_NLI_noise[optical_signal]

        if self.boost_amp:
            self.boost_amp.clean_optical_signals(optical_signals)

        for span, amplifier in self.spans:
            for optical_signal in optical_signals:
                if span in self.nonlinear_interference_noise.keys():
                    if optical_signal in self.nonlinear_interference_noise[span].keys():
                        del self.nonlinear_interference_noise[span][optical_signal]
            if amplifier:
                amplifier.clean_optical_signals(optical_signals)

    def propagate(self, pass_through_signals, pass_through_signals_qot,
                  accumulated_ASE_noise, accumulated_NLI_noise,
                  accumulated_ASE_noise_qot, accumulated_NLI_noise_qot,
                  voa_compensation=False):
        """
        Propagate the signals across the link
        :param pass_through_signals:
        :param accumulated_ASE_noise:
        :param accumulated_NLI_noise:
        :return:
        """
        # Set output signals from node to input of the link
        for optical_signal, power in pass_through_signals.items():
            self.optical_signal_power_in[optical_signal] = power
        for optical_signal, power in pass_through_signals_qot.items():
            self.optical_signal_power_in_qot[optical_signal] = power

        if self.propagate_simulation(accumulated_ASE_noise, accumulated_NLI_noise,
                                     accumulated_ASE_noise_qot, accumulated_NLI_noise_qot, voa_compensation):

            # use is instance instead of checking the class
            if self.node2.__class__.__name__ is 'LineTerminal':
                self.node2.receiver(self.input_port_node2, self.optical_signal_power_out,
                                    self.optical_signal_power_out_qot)
            else:
                self.node2.insert_signals(self.input_port_node2,
                                          self.optical_signal_power_out.copy(), self.optical_signal_power_out_qot.copy(),
                                          self.accumulated_ASE_noise.copy(), self.accumulated_NLI_noise.copy(),
                                          self.accumulated_ASE_noise_qot.copy(), self.accumulated_NLI_noise_qot.copy())
                self.node2.switch(self.input_port_node2)

    def propagate_simulation(self, accumulated_ASE_noise, accumulated_NLI_noise,
                             accumulated_ASE_noise_qot, accumulated_NLI_noise_qot, voa_compensation):
        """
        Compute the propagation of signals over this link
        :return:
        """
        # keep track of the signal power in link
        signal_power_progress = self.optical_signal_power_in.copy()
        signal_power_progress_qot = self.optical_signal_power_in_qot.copy()
        # If there is an amplifier compensating for the node
        # attenuation, compute the physical effects
        if self.boost_amp:
            output_power_dict, input_power_dict, out_in_difference = None, None, None
            tmp = {}
            output_power_dict_qot, input_power_dict_qot, out_in_difference_qot = None, None, None
            # Enabling amplifier system gain balancing check
            signal_keys = list(self.optical_signal_power_in)
            while not (self.boost_amp.power_excursions_flag_1 and self.boost_amp.power_excursions_flag_2):
                for optical_signal in signal_keys:
                    in_power = self.optical_signal_power_in[optical_signal]
                    self.boost_amp.input_power[optical_signal] = in_power
                    out_p = self.boost_amp.output_amplified_power(optical_signal, in_power, p_exc=True)
                    tmp[optical_signal] = out_p

                    # in_power_qot = self.optical_signal_power_in_qot[optical_signal]
                    # self.boost_amp.input_power_qot[optical_signal] = in_power_qot
                    # self.boost_amp.output_amplified_power_qot(optical_signal, in_power_qot)
                output_power_dict, input_power_dict, out_in_difference = self.boost_amp.compute_power_excursions()
                # output_power_dict_qot, input_power_dict_qot, out_in_difference_qot = \
                #     self.boost_amp.compute_power_excursions_qot()

            # Reset balancing flags to original settings
            self.boost_amp.power_excursions_flags_off()

            if voa_compensation:

                # procedure for VOA reconfiguration
                prev_roadm = self.node1
                prev_roadm.voa_reconf(self, tmp, self.output_port_node1)
                # return to avoid propagation of effects
                return False

            # Compute for the power and ASE noise
            tmp_ = [abs_to_db(x) for x in list(self.optical_signal_power_in.values())]
            # tmp_ = [abs_to_db(x) for x in list(accumulated_ASE_noise.values())]
            for optical_signal in signal_keys:
                in_power = self.optical_signal_power_in[optical_signal]
                self.boost_amp.input_power[optical_signal] = in_power
                output_power = self.boost_amp.output_amplified_power(optical_signal, in_power)

                in_power_qot = self.optical_signal_power_in_qot[optical_signal]
                self.boost_amp.input_power_qot[optical_signal] = in_power_qot
                output_power_qot = self.boost_amp.output_amplified_power_qot(optical_signal, in_power_qot)

                # Update status of signal power in link
                signal_power_progress[optical_signal] = output_power
                # Update status of signal power in link QoT
                signal_power_progress_qot[optical_signal] = output_power_qot

                self.boost_amp.stage_amplified_spontaneous_emission_noise(optical_signal,
                                                                          accumulated_noise=accumulated_ASE_noise)
                self.boost_amp.stage_amplified_spontaneous_emission_noise_qot(optical_signal,
                                                                              accumulated_noise=accumulated_ASE_noise_qot)

            tmp_pow = [abs_to_db(x) for x in list(signal_power_progress.values())]
            # Update accumulated ASE noise structure with respect to
            # the boost amplifier generated noise
            accumulated_ASE_noise.update(self.boost_amp.ase_noise)
            accumulated_ASE_noise_qot.update(self.boost_amp.ase_noise_qot)

            # tmp_ = [abs_to_db(x) for x in list(accumulated_ASE_noise.values())]

            # Compensate for the ROADM attenuation
            self.boost_amp.nli_compensation(accumulated_NLI_noise)
            if self.boost_amp.tmp_qot_id % self.monitor_unit == 0.0 and self.monitor_flag:
                self.boost_amp.nli_compensation_qot(accumulated_NLI_noise)
            else:
                self.boost_amp.nli_compensation_qot(accumulated_NLI_noise_qot)
            accumulated_NLI_noise.update(self.boost_amp.nonlinear_noise)
            accumulated_NLI_noise_qot.update(self.boost_amp.nonlinear_noise_qot)

        # Needed for the subsequent computations
        prev_amp = self.boost_amp
        nonlinear_interference_noise = {}
        nonlinear_interference_noise_qot = {}
        for span, amplifier in self.spans:
            signals_list = list(signal_power_progress.keys())
            signals_list_qot = list(signal_power_progress_qot.keys())

            if amplifier:
                # Compute nonlinear interference noise, passing the node_amplifier
                # because its amplification gain impacts negatively the nonlinear
                # interference.
                nonlinear_interference_noise[span] = self.output_nonlinear_noise(
                    accumulated_NLI_noise,
                    signal_power_progress,
                    signals_list,
                    span,
                    amplifier)
                self.nonlinear_interference_noise[span] = nonlinear_interference_noise[span]
                accumulated_NLI_noise.update(nonlinear_interference_noise[span])
                self.accumulated_NLI_noise.update(nonlinear_interference_noise[span])

                nonlinear_interference_noise_qot[span] = self.output_nonlinear_noise_qot(
                    accumulated_NLI_noise_qot,
                    signal_power_progress_qot,
                    signals_list_qot,
                    span,
                    amplifier)
                self.nonlinear_interference_noise_qot[span] = nonlinear_interference_noise_qot[span]
                accumulated_NLI_noise_qot.update(nonlinear_interference_noise_qot[span])
                self.accumulated_NLI_noise_qot.update(nonlinear_interference_noise_qot[span])

            if self.srs_effect:
                # Compute nonlinear effects from the fibre
                if len(signal_power_progress) > 1 and prev_amp:
                    signal_power_progress, accumulated_ASE_noise, accumulated_NLI_noise = \
                        self.zirngibl_srs(signals_list, signal_power_progress, accumulated_ASE_noise,
                                          accumulated_NLI_noise, span)
                    # signal_power_progress_qot, accumulated_ASE_noise_qot, accumulated_NLI_noise_qot = \
                    #     self.zirngibl_srs(signals_list_qot, signal_power_progress_qot, accumulated_ASE_noise_qot,
                    #                       accumulated_NLI_noise_qot, span, flag=False)

            # Compute linear effects from the fibre
            for optical_signal, power in signal_power_progress.items():
                signal_power_progress[optical_signal] = power / span.attenuation()
                accumulated_ASE_noise[optical_signal] /= span.attenuation()
                accumulated_NLI_noise[optical_signal] /= span.attenuation()
            for optical_signal, power in signal_power_progress_qot.items():
                signal_power_progress_qot[optical_signal] = power / span.attenuation()
                accumulated_ASE_noise_qot[optical_signal] /= span.attenuation()
                accumulated_NLI_noise_qot[optical_signal] /= span.attenuation()

            # Compute amplifier compensation
            if amplifier:
                signal_keys = list(signal_power_progress)
                # Enabling balancing check
                while not (amplifier.power_excursions_flag_1 and amplifier.power_excursions_flag_2):
                    for optical_signal in signal_keys:
                        in_power = signal_power_progress[optical_signal]
                        amplifier.input_power[optical_signal] = in_power
                        amplifier.output_amplified_power(optical_signal, in_power)

                        # in_power_qot = signal_power_progress_qot[optical_signal]
                        # amplifier.input_power_qot[optical_signal] = in_power_qot
                        # amplifier.output_amplified_power_qot(optical_signal, in_power_qot)
                    amplifier.compute_power_excursions()
                    # amplifier.compute_power_excursions_qot()

                amplifier.power_excursions_flags_off()

                # Compute for the power
                for optical_signal in signal_keys:
                    in_power = signal_power_progress[optical_signal]
                    amplifier.input_power[optical_signal] = in_power
                    output_power = amplifier.output_amplified_power(optical_signal, in_power)

                    in_power_qot = signal_power_progress_qot[optical_signal]
                    amplifier.input_power_qot[optical_signal] = in_power_qot
                    output_power_qot = amplifier.output_amplified_power_qot(optical_signal, in_power_qot)

                    self.optical_signal_power_out[optical_signal] = output_power
                    self.optical_signal_power_out_qot[optical_signal] = output_power_qot

                    amplifier.stage_amplified_spontaneous_emission_noise(optical_signal,
                                                                         accumulated_noise=accumulated_ASE_noise)
                    amplifier.stage_amplified_spontaneous_emission_noise_qot(optical_signal,
                                                                             accumulated_noise=accumulated_ASE_noise_qot)

                accumulated_ASE_noise.update(amplifier.ase_noise)
                signal_power_progress.update(self.optical_signal_power_out.copy())
                accumulated_ASE_noise_qot.update(amplifier.ase_noise_qot)
                signal_power_progress_qot.update(self.optical_signal_power_out_qot.copy())

                amplifier.nli_compensation(accumulated_NLI_noise)
                if self.boost_amp.tmp_qot_id % self.monitor_unit == 0.0 and self.monitor_flag:
                    amplifier.nli_compensation_qot(accumulated_NLI_noise)
                else:
                    amplifier.nli_compensation_qot(accumulated_NLI_noise_qot)
                accumulated_NLI_noise.update(amplifier.nonlinear_noise)
                accumulated_NLI_noise_qot.update(amplifier.nonlinear_noise_qot)
            else:
                for optical_signal, in_power in signal_power_progress.items():
                    # Update status of signal power in link
                    self.optical_signal_power_out[optical_signal] = in_power

                for optical_signal, in_power in signal_power_progress_qot.items():
                    # Update status of signal power in link
                    self.optical_signal_power_out_qot[optical_signal] = in_power

            prev_amp = amplifier
            self.accumulated_ASE_noise.update(accumulated_ASE_noise)
            self.accumulated_NLI_noise.update(accumulated_NLI_noise)
            self.accumulated_ASE_noise_qot.update(accumulated_ASE_noise_qot)
            self.accumulated_NLI_noise_qot.update(accumulated_NLI_noise_qot)

            tmp_pow = [abs_to_db(x) for x in list(signal_power_progress.values())]

        return True

    @staticmethod
    def zirngibl_srs(optical_signals, active_channels, accumulated_ASE_noise, accumulated_NLI_noise, span, flag=True):
        """
        Computation taken from : M. Zirngibl Analytical model of Raman gain effects in massive
        wavelength division multiplexed transmission systems, 1998. - Equations 7,8.
        :param optical_signals: signals interacting at given transmission - list[Signal() object]
        :param active_channels: power levels at the end of span - dict{signal_index: power levels}
        :param accumulated_ASE_noise: ASE levels at the end of span - dict{signal_index: ASE levels}
        :param accumulated_NLI_noise: NLI levels at the end of span - dict{signal_index: NLI levels}
        :param span: Span() object
        :return:
        """
        min_wavelength_index = 90
        max_wavelength_index = 0
        min_signal = None
        max_signal = None
        for optical_signal in optical_signals:
            if optical_signal.index < min_wavelength_index:
                min_signal = optical_signal
                min_wavelength_index = optical_signal.index
            if optical_signal.index > max_wavelength_index:
                max_signal = optical_signal
                max_wavelength_index = optical_signal.index
        frequency_min = min_signal.frequency  # minimum frequency of longest wavelength
        frequency_max = max_signal.frequency  # maximum frequency of shortest wavelength

        effective_length = span.effective_length_  # SMF effective distance
        beta = span.raman_coefficient

        total_power = 0  # Total input power calculated by following loop
        for channel, power_per_channel in active_channels.items():
            total_power += power_per_channel * unit.mW

        # Calculate delta P for each channel
        for optical_signal in optical_signals:
            frequency = optical_signal.frequency
            r1 = beta * total_power * effective_length * (frequency_max - frequency_min) * math.e ** (
                    # beta * total_power * effective_length * (frequency_max - frequency))  # term 1
                    beta * total_power * effective_length * (frequency - frequency_min))  # term 1

            r2 = math.e ** (beta * total_power * effective_length * (frequency_max - frequency_min)) - 1  # term 2

            delta_p = float(r1 / r2)  # Does the arithmetic in mW
            active_channels[optical_signal] *= delta_p
            accumulated_ASE_noise[optical_signal] *= delta_p
            accumulated_NLI_noise[optical_signal] *= delta_p
        # if flag:
        #     min_p = str(round(abs_to_db(min(list(active_channels.values()))), 2))
        #     max_p = str(round(abs_to_db(max(list(active_channels.values()))), 2))
        #     diff_p_lin = abs_to_db(max(list(active_channels.values()))) - abs_to_db(min(list(active_channels.values())))
        #     diff_p = str(round(diff_p_lin, 2))
            # print("(link.py line:392) Min p: %s dB --- Max p: %s dB --- Diff: %s dB" % (min_p, max_p, diff_p))

        return active_channels, accumulated_ASE_noise, accumulated_NLI_noise

    def output_nonlinear_noise(self, _nonlinear_noise, signal_power_progress, signals, span, amplifier):
        """
        :param _nonlinear_noise:
        :param signal_power_progress:
        :param signals: signals interacting at given transmission - list[Signal() object]
        :param span: Span() object
        :param amplifier: Amplifier() object at beginning of span
        :return: dict{signal_index: accumulated NLI noise levels}
        """
        # amplifier_gain = db_to_abs(amplifier.system_gain)
        nonlinear_noise_new = self.gn_analytic(signals, signal_power_progress, span)
        # nonlinear_noise_new = self.nonlinear_noise(signals, signal_power_progress, span, amplifier_gain)

        out_noise = {}
        for signal, value in _nonlinear_noise.items():
            wdg_linear = db_to_abs(amplifier.get_wavelength_dependent_gain(signal.index))
            out_noise[signal] = value + nonlinear_noise_new[signal] #* wdg_linear

        # # Looking at the recently accumulated nonlinear noise
        # json_struct = {'tests': []}
        # nli_id = 'nli_' + str(self.nli_id)
        # json_struct['tests'].append({nli_id: list(out_noise.values())})
        # json_file_name = '../../monitoring-nli-noise/' + str(self.id) + '_' + nli_id + '.json'
        # with open(json_file_name, 'w+') as outfile:
        #     json.dump(json_struct, outfile)
        # self.nli_id += 1
        return out_noise

    def output_nonlinear_noise_qot(self, _nonlinear_noise, signal_power_progress, signals, span, amplifier):
        """
        :param _nonlinear_noise:
        :param signal_power_progress:
        :param signals: signals interacting at given transmission - list[Signal() object]
        :param span: Span() object
        :param amplifier: Amplifier() object at beginning of span
        :return: dict{signal_index: accumulated NLI noise levels}
        """

        if amplifier.tmp_qot_id % self.monitor_unit == 0.0 and self.monitor_flag:
            tmp = self.nonlinear_interference_noise[span].copy()
            out_noise = tmp
        else:
            nonlinear_noise_new = self.gn_analytic(signals, signal_power_progress, span)
            out_noise = {}
            for signal, value in _nonlinear_noise.items():
                out_noise[signal] = value + nonlinear_noise_new[signal]
        return out_noise

    def nonlinear_noise(self, signals, signal_power_progress, span, lump_gain):
        """
        Computation taken from: Poggiolini, P., et al. "Accurate Non-Linearity Fully-Closed-Form Formula
        based on the GN/EGN Model and Large-Data-Set Fitting." Optical Fiber Communication Conference.
        Optical Society of America, 2019. Equations 1-4
        :param signals: signals interacting at given transmission - list[Signal() object]
        :param span: Span() object
        :param lump_gain: EDFA target gain + wavelength dependent gain - float
        :return: Nonlinear Interference noise - dictionary{signal_index: NLI}

        not correct! Nov. 28th 2019
        """
        nonlinear_noise_struct = {}
        channels_index = []
        index_to_signal = {}
        for channel in signals:
            nonlinear_noise_struct[channel] = None
            channels_index.append(channel.index)
            index_to_signal[channel.index] = channel
        sorted(channels_index)
        channel_center = channels_index[int(math.floor(len(signal_power_progress.keys()) / 2))]
        frequency_center = index_to_signal[channel_center].frequency

        # Retrieve fiber properties from span
        b2 = span.dispersion_coefficient
        b3 = span.dispersion_slope
        alpha = span.fibre_attenuation
        gamma = span.non_linear_coefficient
        span_length = span.length

        for signal in signals:
            channel_under_test = signal.index
            frequency_cut = signal.frequency
            symbol_rate_cut = signal.symbol_rate
            bits_per_symbol_cut = signal.bits_per_symbol
            gross_bit_rate_cut = symbol_rate_cut * np.log2(bits_per_symbol_cut)
            # bw_cut = gross_bit_rate_cut / (2 * np.log2(4))  # full bandwidth of the nth channel (THz).
            bw_cut = symbol_rate_cut
            pwr_cut = signal_power_progress[signal] * unit.mW
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            nonlinear_noise_term2 = 0

            for ch in signals:

                frequency_ch = ch.frequency
                symbol_rate_ch = ch.symbol_rate
                bits_per_symbol_ch = ch.bits_per_symbol
                gross_bit_rate_ch = symbol_rate_ch * np.log2(bits_per_symbol_ch)
                # bw_ch = gross_bit_rate_ch / (2 * np.log2(4))  # full bandwidth of the nth channel (THz).
                bw_ch = symbol_rate_ch
                pwr_ch = signal_power_progress[ch] * unit.mW
                g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)

                if ch == channel_under_test:
                    continue
                else:

                    b2_eff_nch = b2 + unit.pi * b3 * (
                            frequency_ch + frequency_cut - 2 * frequency_center)  # FWM-factor - [1], Eq. (5)
                    b2_eff_ncut = b2 + unit.pi * b3 * (
                            2 * frequency_cut - 2 * frequency_center)  # FWM-factor - [1], Eq. (6)

                    nch_dividend1 = math.asinh(
                        (unit.pi ** 2 / 2) * abs(b2_eff_nch / alpha) *
                        (frequency_ch - frequency_cut + (bw_ch / 2)) * bw_cut)
                    nch_divisor1 = 8 * unit.pi * abs(b2_eff_nch) * alpha

                    nch_dividend2 = np.arcsinh(
                        (unit.pi ** 2 / 2) * abs(b2_eff_nch / alpha) *
                        (frequency_ch - frequency_cut - (bw_ch / 2)) * bw_cut)
                    nch_divisor2 = 8 * unit.pi * abs(b2_eff_nch) * alpha

                    _nch = (nch_dividend1 / float(nch_divisor1)) - (
                            nch_dividend2 / float(nch_divisor2))  # [1], Eq. (3)

                    cut_dividend = np.arcsinh((unit.pi ** 2 / 2) * abs(b2_eff_ncut / (2 * alpha)) * bw_cut ** 2)
                    cut_divisor = 4 * unit.pi * abs(b2_eff_ncut) * alpha
                    _cut = cut_dividend / float(cut_divisor)  # [1], Eq. (4)

                    nonlinear_noise_term2 += (2 * g_ch ** 2 * _nch + g_cut ** 2 * _cut)

            nonlinear_noise_term1 = 16 / 27.0 * gamma ** 2 * lump_gain * \
                                    math.e ** (-2 * alpha * span_length) * g_cut
            nonlinear_noise = nonlinear_noise_term1 * nonlinear_noise_term2
            signal_under_test = index_to_signal[channel_under_test]
            nonlinear_noise_struct[signal_under_test] = nonlinear_noise * bw_cut
        return nonlinear_noise_struct

    def gn_model(self, optical_signals, signal_power_progress, span):
        """ Calculates Eq. 7.32 from
        Poggiolini, P., Jiang, Y., Carena, A. and Forghieri, F., 2016. Analytical modeling
        of the impact of fiber non-linear propagation on coherent systems and networks.
        Enabling Technologies for High Spectral-Efficiency Coherent Optical Communication
        Networks.
        :param optical_signals:
        :param signal_power_progress:
        :param span:
        :return: carrier_nli: the amount of nonlinear interference in W on the carrier under analysis
        """
        nonlinear_noise_struct = {}
        channels_index = []
        index_to_signal = {}
        for channel in optical_signals:
            nonlinear_noise_struct[channel] = None
            channels_index.append(channel.index)
            index_to_signal[channel.index] = channel

        alpha = span.alpha
        beta2 = span.dispersion_coefficient
        gamma = span.non_linear_coefficient
        length = span.length
        effective_length = span.effective_length

        for optical_signal in optical_signals:
            channel_under_test = optical_signal.index
            symbol_rate_cut = optical_signal.symbol_rate
            bw_cut = symbol_rate_cut
            pwr_cut = signal_power_progress[optical_signal] * 1e-3
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            g_nli = 0
            for ch in optical_signals:
                symbol_rate_ch = ch.symbol_rate
                bw_ch = symbol_rate_ch
                pwr_ch = signal_power_progress[ch] * 1e-3
                g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)

                g_nli += (g_ch ** 2) * self.psi_factor(optical_signal, ch, alpha,
                                                             beta2, length, effective_length)
            g_nli *= (8.0 / (27.0 * unit.pi)) * g_cut * ((gamma ** 2) * effective_length) / beta2
            signal_under_test = index_to_signal[channel_under_test]
            nonlinear_noise_struct[signal_under_test] = g_nli * bw_cut

        return nonlinear_noise_struct

    @staticmethod
    def psi_factor(carrier, interfering_carrier, alpha, beta2, length, effective_length):
        symbol_rate_cut = carrier.symbol_rate
        bw_cut = symbol_rate_cut

        symbol_rate_ch = interfering_carrier.symbol_rate
        bw_ch = symbol_rate_ch

        if carrier.index == interfering_carrier.index:  # SCI, SPM
            psi = np.arcsinh(((unit.pi ** 2) * abs(beta2) / (4.0 * alpha)) * bw_cut ** 2)
        else:  # XCI, XPM
            delta_f = interfering_carrier.frequency - carrier.frequency
            div = 1 / (2.0 * alpha)
            psi = np.arcsinh((unit.pi ** 2 * abs(beta2) * div) * (delta_f + bw_ch * 0.5) * bw_cut)
            psi -= np.arcsinh((unit.pi ** 2 * abs(beta2) * div) * (delta_f - bw_ch * 0.5) * bw_cut)
            psi -= 1 * (bw_cut / delta_f) * (5.0 / 3.0) * (effective_length / length)
        return psi

    def gn_analytic(self, optical_signals, signal_power_progress, span):
        """ Computes the nonlinear interference power on a single carrier.
        Translated from the GNPy project source code
        The method uses eq. 120 from arXiv:1209.0394.
        :param optical_signals:
        :param signal_power_progress:
        :param span:
        :return: carrier_nli: the amount of nonlinear interference in W on the carrier under analysis
        """

        nonlinear_noise_struct = {}
        channels_index = []
        index_to_signal = {}
        for channel in optical_signals:
            nonlinear_noise_struct[channel] = None
            channels_index.append(channel.index)
            index_to_signal[channel.index] = channel
        # alpha_ = span.alpha
        alpha = span.alpha_
        beta2 = span.dispersion_coefficient
        gamma = span.non_linear_coefficient
        # effective_length_ = span.effective_length
        effective_length = span.effective_length_
        # asymptotic_length_ = 1 / alpha
        asymptotic_length = 1 / (2 * alpha)

        for optical_signal in optical_signals:
            channel_under_test = optical_signal.index
            symbol_rate_cut = optical_signal.symbol_rate
            bw_cut = symbol_rate_cut
            pwr_cut = signal_power_progress[optical_signal] * 1e-3
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            g_nli = 0
            for ch in optical_signals:
                symbol_rate_ch = ch.symbol_rate
                bw_ch = symbol_rate_ch
                pwr_ch = signal_power_progress[ch] * 1e-3
                g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)
                delta_factor = 1 if ch.frequency == optical_signal.frequency else 2
                psi = self._psi_gnpy(optical_signal, ch, beta2=beta2,
                                     asymptotic_length=asymptotic_length)
                g_nli += g_ch ** 2 * g_cut * psi
                tmp = 0

            g_nli *= (16.0 / 27.0) * (gamma * effective_length) ** 2 \
                     / (2 * np.pi * abs(beta2) * asymptotic_length)
            tmp = 0
            signal_under_test = index_to_signal[channel_under_test]
            nonlinear_noise_struct[signal_under_test] = g_nli * bw_cut * 1e3
        return nonlinear_noise_struct

    @staticmethod
    def _psi(carrier, interfering_carrier, beta2, asymptotic_length):
        """Calculates eq. 123 from `arXiv:1209.0394 <https://arxiv.org/abs/1209.0394>`__
        Translated from the GNPy project source code
        """
        symbol_rate_cut = carrier.symbol_rate
        bw_cut = symbol_rate_cut

        symbol_rate_ch = interfering_carrier.symbol_rate
        bw_ch = symbol_rate_ch

        if carrier.index == interfering_carrier.index:  # SCI, SPM
            psi = np.arcsinh(0.5 * (unit.pi ** 2) * asymptotic_length * abs(beta2) * (bw_cut ** 2)) /\
                  (2 * unit.pi * asymptotic_length * abs(beta2))
        else:  # XCI, XPM
            delta_f = carrier.frequency - interfering_carrier.frequency
            psi1 = np.arcsinh((unit.pi ** 2) * asymptotic_length * abs(beta2) *
                              bw_cut * (delta_f + 0.5 * bw_ch)) / (4 * unit.pi * asymptotic_length * abs(beta2))
            psi2 = np.arcsinh((unit.pi ** 2) * asymptotic_length * abs(beta2) *
                              bw_cut * (delta_f - 0.5 * bw_ch)) / (4 * unit.pi * asymptotic_length * abs(beta2))
            psi = psi1 - psi2
        return psi

    @staticmethod
    def _psi_gnpy(carrier, interfering_carrier, beta2, asymptotic_length):
        """Calculates eq. 123 from `arXiv:1209.0394 <https://arxiv.org/abs/1209.0394>`__
        Translated from the GNPy project source code
        """
        symbol_rate_cut = carrier.symbol_rate
        bw_cut = symbol_rate_cut

        symbol_rate_ch = interfering_carrier.symbol_rate
        bw_ch = symbol_rate_ch

        if carrier.index == interfering_carrier.index:  # SCI, SPM
            psi = np.arcsinh(0.5 * unit.pi ** 2 * asymptotic_length * abs(beta2) * bw_cut ** 2)
            tmp = 0
        else:  # XCI, XPM
            delta_f = carrier.frequency - interfering_carrier.frequency
            psi = np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                              bw_cut * (delta_f + 0.5 * bw_ch))
            psi -= np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                              bw_cut * (delta_f - 0.5 * bw_ch))
            tmp = 0
        return psi

    # ADDITIONS FOR OFC DEMO USE-CASES
    def reset_propagation_struct(self):
        # Link structures
        self.optical_signal_power_in = {}
        self.optical_signal_power_out = {}
        self.nonlinear_interference_noise = {}
        self.accumulated_ASE_noise = {}
        self.accumulated_NLI_noise = {}

        self.optical_signal_power_in_qot = {}
        self.optical_signal_power_out_qot = {}
        self.nonlinear_interference_noise_qot = {}
        self.accumulated_ASE_noise_qot = {}
        self.accumulated_NLI_noise_qot = {}

        # Amplifiers' structures
        if self.boost_amp:
            self.boost_amp.input_power = {}  # dict of OpticalSignal to input power levels
            self.boost_amp.output_power = {}
            self.boost_amp.ase_noise = {}
            self.boost_amp.nonlinear_noise = {}
            self.boost_amp.system_gain = self.boost_amp.target_gain

            self.boost_amp.input_power_qot = {}  # dict of OpticalSignal to input power levels
            self.boost_amp.output_power_qot = {}
            self.boost_amp.ase_noise_qot = {}
            self.boost_amp.nonlinear_noise_qot = {}
            self.boost_amp.system_gain_qot = self.boost_amp.target_gain
        for span, amplifier in self.spans:
            if amplifier:
                amplifier.input_power = {}
                amplifier.output_power = {}
                amplifier.ase_noise = {}
                amplifier.nonlinear_noise = {}
                amplifier.system_gain = amplifier.target_gain

                amplifier.input_power_qot = {}
                amplifier.output_power_qot = {}
                amplifier.ase_noise_qot = {}
                amplifier.nonlinear_noise_qot = {}
                amplifier.system_gain_qot = amplifier.target_gain


class Span(object):

    ids = 1

    def __init__(self, fibre_type='SMF', length=20.0):
        """
        :param length: optical fiber span length in km - float
        :param fibre_type: optical fiber type - string
        """
        self.span_id = Span.ids  # was id(self)
        Span.ids += 1
        self.fibre_type = fibre_type
        self.length = length * unit.km
        self.fibre_attenuation = 0.22 / unit.km  # fiber attenuation in decibels/km
        self.alpha = self.fibre_attenuation * 0.23  # linear value fibre attenuation
        self.alpha_ = self.fibre_attenuation / (20 * np.log10(np.e))  # linear value fibre attenuation
        self.effective_length = (1 - np.exp(-self.alpha * self.length)) / self.alpha
        self.effective_length_ = (1 - np.exp(-2 * self.alpha_ * self.length)) / (2 * self.alpha_)
        self.non_linear_coefficient = 0.78 / unit.km  # gamma fiber non-linearity coefficient [W^-1 km^-1]
        self.dispersion = 2.1e-05
        self.dispersion_coefficient_ = -21.0 * (unit.ps ** 2 / unit.km)  # B_2 dispersion coefficient [ps^2 km^-1]
        self.dispersion_coefficient = self.beta2()  # B_2 dispersion coefficient [ps^2 km^-1]
        self.dispersion_slope = 0.1452 * (unit.ps ** 3 / unit.km)  # B_3 dispersion slope in (ps^3 km^-1)
        self.effective_area = 80 * unit.um * unit.um  # Aeff - SMF effective area
        self.raman_gain = 7.0 * 1e-12 * unit.cm / unit.W  # r - Raman Gain in SMF
        self.raman_amplification_band = 15 * unit.THz  # Raman amplification band ~15THz
        # Raman coefficient
        self.raman_coefficient = self.raman_gain / (2 * self.effective_area * self.raman_amplification_band)

        self.input_power = {}  # dict signal to input power
        self.output_power = {}  # dict signal to output power

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        "String representation"
        return '<%d %.1fkm>' % (self.span_id, self.length/unit.km)

    def attenuation(self):
        return db_to_abs(self.fibre_attenuation * self.length)

    def beta2(self, ref_wavelength=1550e-9):
        """Returns beta2 from dispersion parameter.
        Dispersion is entered in ps/nm/km.
        Disperion can be a numpy array or a single value.

        :param ref_wavelength: can be a numpy array; default: 1550nm
        """
        D = abs(self.dispersion)
        b2 = (ref_wavelength ** 2) * D / (2 * unit.pi * unit.c)  # 10^21 scales [ps^2/km]
        return b2  # s/Hz/m

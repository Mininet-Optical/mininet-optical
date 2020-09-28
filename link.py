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
                 output_port_node1=None, input_port_node2=None,
                 boost_amp=None, srs_effect=True, spans=None):
        """
        :param node1: source Node object
        :param node2: destination Node object
        """
        if node1 == node2:
            raise ValueError("link.__init__ src_node must be different from dst_node!")

        self.id = id(self)
        self.node1 = node1
        self.node2 = node2
        output_port_node1 = node1.new_output_port(node2, portnum=output_port_node1)
        input_port_node2 = node2.new_input_port(node1, portnum=input_port_node2)
        node1.out_port_to_link[output_port_node1] = self
        self.output_port_node1 = output_port_node1
        self.input_port_node2 = input_port_node2
        self.boost_amp = boost_amp
        self.srs_effect = srs_effect

        self.optical_signal_power_in = {}  # dict of signals and power levels
        self.optical_signal_power_out = {}  # dict of signals and power levels

        self.nonlinear_interference_noise = {}  # dict of spans to signals to nonlinear noise
        self.accumulated_ASE_noise = {}
        self.accumulated_NLI_noise = {}

        self.spans = spans or []

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

    def print_signals(self):
        "Debugging: print signals"
        print(self, 'power in:')
        for signal, power in self.optical_signal_power_in.items():
            print('%s@%.1fdBm' % (signal, abs_to_db(power)))
        print(self, 'power out:')
        for signal, power in self.optical_signal_power_out.items():
            print('%s@%.1fdBm' % (signal, abs_to_db(power)))

    def __repr__(self):
        "String representation"
        return "(%s->%s)" % (self.node1, self.node2)

    def clean_optical_signals(self, optical_signals):
        """
        THIS MIGHT BE OBSOLETE
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


    def propagate(self, pass_through_signals, accumulated_ASE_noise, accumulated_NLI_noise, Modulation_Format,
                  voa_compensation=False, is_last_port=False):

        """
        Propagate the signals across the link
        :param pass_through_signals:
        :param accumulated_ASE_noise:
        :param accumulated_NLI_noise:
        :param voa_compensation:
        :param is_last_port:
        :return:
        """
        accumulated_ASE_noise = accumulated_ASE_noise or {}
        accumulated_NLI_noise = accumulated_NLI_noise or {}
        # Set output signals from node to input of the link
        for optical_signal, power in pass_through_signals.items():
            self.optical_signal_power_in[optical_signal] = power

        if self.propagate_simulation(accumulated_ASE_noise, accumulated_NLI_noise, voa_compensation):
            # use is instance instead of checking the class
            if self.node2.__class__.__name__ is 'LineTerminal':
                self.node2.receiver(self.input_port_node2, self.optical_signal_power_out,
                                    self.accumulated_ASE_noise.copy(), self.accumulated_NLI_noise.copy(),
                                    Modulation_Format=Modulation_Format)
            else:
                self.node2.insert_signals(self.input_port_node2, self.optical_signal_power_out.copy(),
                                          accumulated_ASE_noise=self.accumulated_ASE_noise.copy(),
                                          accumulated_NLI_noise=self.accumulated_NLI_noise.copy(),
                                          Modulation_Format=Modulation_Format)

                if is_last_port:
                    self.node2.switch()


    def propagate_simulation(self, accumulated_ASE_noise, accumulated_NLI_noise, voa_compensation):
        """
        Compute the propagation of signals over this link
        :return:
        """
        # keep track of the signal power in link
        signal_power_progress = self.optical_signal_power_in.copy()
        # get the output power of the signals at output boost port
        output_power_dict = {}
        # If there is an amplifier compensating for the node
        # attenuation, compute the physical effects
        if self.boost_amp:
            # Enabling amplifier system gain balancing check
            while not (self.boost_amp.power_excursions_flag_1 and self.boost_amp.power_excursions_flag_2):
                for optical_signal, in_power in self.optical_signal_power_in.items():
                    self.boost_amp.input_power[optical_signal] = in_power
                    output_power_dict[optical_signal] = \
                        self.boost_amp.output_amplified_power(optical_signal, in_power, p_exc=True)
                self.boost_amp.compute_power_excursions()

            # Reset balancing flags to original settings
            self.boost_amp.power_excursions_flags_off()

            if voa_compensation:
                # procedure for VOA reconfiguration
                prev_roadm = self.node1
                prev_roadm.voa_reconf(self, output_power_dict, self.output_port_node1)
                # return to avoid propagation of effects
                return False

            # Compute for the power
            for optical_signal, in_power in self.optical_signal_power_in.items():
                self.boost_amp.input_power[optical_signal] = in_power
                output_power = self.boost_amp.output_amplified_power(optical_signal, in_power)
                # Update status of signal power in link
                signal_power_progress[optical_signal] = output_power
                # Compute ASE noise generation
                self.boost_amp.stage_amplified_spontaneous_emission_noise(optical_signal,
                                                                          accumulated_noise=accumulated_ASE_noise)
            # Update accumulated ASE noise structure with respect to
            # the boost amplifier generated noise
            accumulated_ASE_noise.update(self.boost_amp.ase_noise)

            # Compensate for the ROADM attenuation
            self.boost_amp.nli_compensation(accumulated_NLI_noise)
            accumulated_NLI_noise.update(self.boost_amp.nonlinear_noise)

        # Needed for the subsequent computations
        prev_amp = self.boost_amp
        nonlinear_interference_noise = {}
        for span, amplifier in self.spans:
            signals_list = list(signal_power_progress.keys())
            if amplifier:
                # Compute the nonlinear noise with the GN model
                nonlinear_interference_noise[span] = self.output_nonlinear_noise(
                    accumulated_NLI_noise,
                    signal_power_progress,
                    signals_list,
                    span)
                self.nonlinear_interference_noise[span] = nonlinear_interference_noise[span]
                accumulated_NLI_noise.update(nonlinear_interference_noise[span])
                self.accumulated_NLI_noise.update(nonlinear_interference_noise[span])

            # Compute SRS effects from the fibre
            if self.srs_effect:
                if len(signal_power_progress) > 1 and prev_amp:
                    signal_power_progress, accumulated_ASE_noise, accumulated_NLI_noise = \
                        self.zirngibl_srs(signals_list, signal_power_progress, accumulated_ASE_noise,
                                          accumulated_NLI_noise, span)

            # Compute linear effects from the fibre
            for optical_signal, power in signal_power_progress.items():
                signal_power_progress[optical_signal] = power / span.attenuation()
                accumulated_ASE_noise[optical_signal] /= span.attenuation()
                accumulated_NLI_noise[optical_signal] /= span.attenuation()

            # Compute amplifier compensation
            if amplifier:
                # Enabling balancing check
                while not (amplifier.power_excursions_flag_1 and amplifier.power_excursions_flag_2):
                    for optical_signal, in_power in signal_power_progress.items():
                        amplifier.input_power[optical_signal] = in_power
                        amplifier.output_amplified_power(optical_signal, in_power)
                    amplifier.compute_power_excursions()
                # Reset balancing flags to original settings
                amplifier.power_excursions_flags_off()

                # Compute for the power
                for optical_signal, in_power in signal_power_progress.items():
                    amplifier.input_power[optical_signal] = in_power
                    output_power = amplifier.output_amplified_power(optical_signal, in_power)
                    # Update status of signal power in link
                    self.optical_signal_power_out[optical_signal] = output_power
                    # Compute ASE noise
                    amplifier.stage_amplified_spontaneous_emission_noise(optical_signal,
                                                                         accumulated_noise=accumulated_ASE_noise)
                accumulated_ASE_noise.update(amplifier.ase_noise)
                signal_power_progress.update(self.optical_signal_power_out)

                amplifier.nli_compensation(accumulated_NLI_noise)
                accumulated_NLI_noise.update(amplifier.nonlinear_noise)

            else:
                for optical_signal, in_power in signal_power_progress.items():
                    # Update status of signal power in link
                    self.optical_signal_power_out[optical_signal] = in_power

            prev_amp = amplifier
            self.accumulated_ASE_noise.update(accumulated_ASE_noise)
            self.accumulated_NLI_noise.update(accumulated_NLI_noise)

        return True

    @staticmethod
    def zirngibl_srs(optical_signals, active_channels, accumulated_ASE_noise, accumulated_NLI_noise, span):
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

        effective_length = span.effective_length  # SMF effective distance
        beta = span.raman_coefficient

        total_power = 0  # Total input power calculated by following loop
        for channel, power_per_channel in active_channels.items():
            total_power += power_per_channel * unit.mW

        # Calculate delta P for each channel
        for optical_signal in optical_signals:
            frequency = optical_signal.frequency
            r1 = beta * total_power * effective_length * (frequency_max - frequency_min) * math.e ** (
                    beta * total_power * effective_length * (frequency - frequency_min))  # term 1
            r2 = math.e ** (beta * total_power * effective_length * (frequency_max - frequency_min)) - 1  # term 2

            delta_p = float(r1 / r2)  # Does the arithmetic in mW
            active_channels[optical_signal] *= delta_p
            accumulated_ASE_noise[optical_signal] *= delta_p
            accumulated_NLI_noise[optical_signal] *= delta_p

        return active_channels, accumulated_ASE_noise, accumulated_NLI_noise

    def output_nonlinear_noise(self, _nonlinear_noise, signal_power_progress, signals, span):
        """
        :param _nonlinear_noise:
        :param signal_power_progress:
        :param signals: signals interacting at given transmission - list[Signal() object]
        :param span: Span() object
        :return: dict{signal_index: accumulated NLI noise levels}
        """

        nonlinear_noise_new = self.gn_model(signals, signal_power_progress, span)

        out_noise = {}
        for optical_signal, value in _nonlinear_noise.items():
            out_noise[optical_signal] = value + nonlinear_noise_new[optical_signal]
        return out_noise

    def gn_model(self, optical_signals, signal_power_progress, span):
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
        alpha = span.alpha
        beta2 = span.dispersion_coefficient
        gamma = span.non_linear_coefficient
        effective_length = span.effective_length
        asymptotic_length = 1 / (2 * alpha)

        for optical_signal in optical_signals:
            channel_under_test = optical_signal.index
            symbol_rate_cut = optical_signal.symbol_rate
            bw_cut = symbol_rate_cut
            pwr_cut = round(signal_power_progress[optical_signal], 2) * 1e-3
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            g_nli = 0
            for ch in optical_signals:
                symbol_rate_ch = ch.symbol_rate
                bw_ch = symbol_rate_ch
                pwr_ch = round(signal_power_progress[ch], 2) * 1e-3
                g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)
                psi = self.psi_factor(optical_signal, ch, beta2=beta2, asymptotic_length=asymptotic_length)
                g_nli += g_ch ** 2 * g_cut * psi

            g_nli *= (16.0 / 27.0) * (gamma * effective_length) ** 2 \
                     / (2 * np.pi * abs(beta2) * asymptotic_length)
            signal_under_test = index_to_signal[channel_under_test]
            nonlinear_noise_struct[signal_under_test] = g_nli * bw_cut * 1e3
        return nonlinear_noise_struct

    @staticmethod
    def psi_factor(carrier, interfering_carrier, beta2, asymptotic_length):
        """Calculates eq. 123 from `arXiv:1209.0394 <https://arxiv.org/abs/1209.0394>`__
        Translated from the GNPy project source code
        """
        symbol_rate_cut = carrier.symbol_rate
        bw_cut = symbol_rate_cut

        symbol_rate_ch = interfering_carrier.symbol_rate
        bw_ch = symbol_rate_ch

        if carrier.index == interfering_carrier.index:  # SCI, SPM
            psi = np.arcsinh(0.5 * unit.pi ** 2 * asymptotic_length * abs(beta2) * bw_cut ** 2)
        else:  # XCI, XPM
            delta_f = carrier.frequency - interfering_carrier.frequency
            psi = np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                             bw_cut * (delta_f + 0.5 * bw_ch))
            psi -= np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                              bw_cut * (delta_f - 0.5 * bw_ch))
        return psi

    # ADDITIONS FOR OFC DEMO USE-CASES
    def reset_propagation_struct(self):
        # Link structures
        self.optical_signal_power_in = {}
        self.optical_signal_power_out = {}
        self.accumulated_ASE_noise = {}
        self.accumulated_NLI_noise = {}
        self.nonlinear_interference_noise = {}

        # Amplifiers' structures
        if self.boost_amp:
            self.boost_amp.input_power = {}  # dict of OpticalSignal to input power levels
            self.boost_amp.output_power = {}
            self.boost_amp.ase_noise = {}
            self.boost_amp.nonlinear_noise = {}
            self.boost_amp.system_gain = self.boost_amp.target_gain
        for span, amplifier in self.spans:
            if amplifier:
                amplifier.input_power = {}
                amplifier.output_power = {}
                amplifier.ase_noise = {}
                amplifier.nonlinear_noise = {}
                amplifier.system_gain = amplifier.target_gain


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
        self.alpha = self.fibre_attenuation / (20 * np.log10(np.e))  # linear value fibre attenuation
        self.effective_length = (1 - np.exp(-2 * self.alpha * self.length)) / (2 * self.alpha)
        self.non_linear_coefficient = 0.78 / unit.km  # gamma fiber non-linearity coefficient [W^-1 km^-1]
        self.dispersion = 2.1e-05
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
        Translated from the GNPy project source code
        :param ref_wavelength: can be a numpy array; default: 1550nm
        """
        D = abs(self.dispersion)
        b2 = (ref_wavelength ** 2) * D / (2 * unit.pi * unit.c)  # 10^21 scales [ps^2/km]
        return b2  # s/Hz/m

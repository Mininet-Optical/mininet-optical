from collections import namedtuple
from units import *
from pprint import pprint
from numpy import errstate
from node import LineTerminal, Roadm, Amplifier


SpanTuple = namedtuple('Span', 'span amplifier')


class Link(object):
    """
    A Link refers to the connection between two network nodes (i.e., transceiver-ROADM or
    ROADM-ROADM). In the future we must enable network-element-node to controller-node
    connectivity.
    """

    def __init__(self, src_node, dst_node, src_out_port=-1, dst_in_port=-1,
                 boost_amp=None, srs_effect=False, spans=None, debugger=False):
        """
        :param src_node: Node, source Node
        :param dst_node: Node, destination Node
        :param src_out_port: int, output port of src node
        :param dst_in_port: int, input port of dst node
        :param boost_amp: Amplifier, booster
        :param srs_effect: boolean, enabling/disabling SRS effect
        :param spans: list, list of Span objects
        :param debugger: boolean, debugging flag
        """
        if src_node == dst_node:
            raise ValueError("link.__init__ src_node must be different from dst_node!")
        self.debugger = debugger
        # configuration attributes
        self.src_node = src_node
        self.dst_node = dst_node
        self.boost_amp = boost_amp
        self.srs_effect = srs_effect
        self.spans = spans or []

        self.optical_signals = []

        # set connection ports for amps and the link
        if boost_amp:
            self.boost_amp.set_input_port(self.src_node, self, input_port=0)
            self.boost_amp.set_output_port(spans[0][0], self, output_port=0)
            self.boost_amp.prev_component = src_node
            self.boost_amp.next_component = spans[0][0]

        prev_amp = None
        for i, span in enumerate(spans):
            prev_span = span[0]
            prev_span.link = self
            amplifier = span[1]

            if i == 0:
                prev_span.prev_component = src_node
            else:
                prev_span.prev_component = prev_amp

            if amplifier:
                amplifier.link = self
                amplifier.set_input_port(prev_span, self, input_port=0)

                amplifier.prev_component = prev_span
                if i + 1 < len(spans):
                    next_span = spans[i + 1][0]
                    amplifier.set_output_port(next_span, self, output_port=0)
                    amplifier.next_component = next_span
                else:
                    amplifier.set_output_port(dst_node, self, output_port=0)
                    amplifier.next_component = dst_node

                prev_amp = amplifier
                prev_span.next_component = amplifier
            else:
                prev_span.next_component = dst_node

        self.src_node.set_output_port(self.dst_node, self, output_port=src_out_port)
        self.dst_node.set_input_port(self.src_node, self, input_port=dst_in_port)

    def length(self):
        """
        :return: link length adding up span lengths in spans attribute
        """
        if len(self.spans) > 0:
            return sum(span.span.length for span in self.spans)
        return 0

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        """String representation"""
        return "(%s->%s)" % (self.src_node, self.dst_node)

    def reset(self):
        """
        Remove all optical signals from Link
        """
        print("*** resetting link", self)
        if len(self.optical_signals) > 0:
            self.optical_signals = []
            for span_tuple in self.spans:
                span = span_tuple[0]
                span.reset()

                amplifier = span_tuple[1]
                if amplifier:
                    amplifier.reset()

            if self.dst_node is not None:
                self.dst_node.reset()

    def remove_optical_signal(self, optical_signal):
        if self.debugger:
            print("*** %s removing: %s" % (self, optical_signal))
        if optical_signal in self.optical_signals:
            self.optical_signals.remove(optical_signal)

        for span, amplifier in self.spans:
            span.remove_optical_signal(optical_signal)
            if amplifier:
                amplifier.remove_optical_signal(optical_signal)

        if self.dst_node is not None:
            self.dst_node.remove_optical_signal(optical_signal)

    def include_optical_signal_in(self, optical_signal, power=None,
                                  ase_noise=None, nli_noise=None, tup_key=None):
        """
        Include optical signal in optical_signals
        :param optical_signal: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param tup_key: tuple key composed of (Link, Span)
        """
        if optical_signal not in self.optical_signals:
            self.optical_signals.append(optical_signal)
        optical_signal.assoc_loc_in(self, power, ase_noise, nli_noise)

    def include_optical_signal_out(self, optical_signal, power=None, ase_noise=None, nli_noise=None):
        """
        Include optical signal in optical_signals_out
        :param optical_signal: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param tup_key: tuple key composed of (Link, Span)
        """
        optical_signal.assoc_loc_out(self, power, ase_noise, nli_noise)

    def propagate(self, is_last_port=False, safe_switch=False):
        """
        Propagate the signals across the link
        :param is_last_port: boolean, needed for propagation algorithm
        :param safe_switch: boolean, needed for propagation algorithm
        :return:
        """
        if self.boost_amp:
            for optical_signal in self.optical_signals:
                # associate boost_amp to optical signal at input interface
                self.boost_amp.include_optical_signal_in(optical_signal,
                                                         in_port=0)
            self.boost_amp.propagate(self.optical_signals,
                                     is_last_port=is_last_port,
                                     safe_switch=safe_switch)
        else:
            first_span = self.spans[0][0]
            for optical_signal in self.optical_signals:
                first_span.include_optical_signal_in(optical_signal)
            first_span.propagate(is_last_port=is_last_port,
                                 safe_switch=safe_switch)

class Span(object):

    ids = 1

    def __init__(self, fibre_type='SMF', length=20.0, debugger=False):
        """
        :param length: optical fiber span length in km - float
        :param fibre_type: optical fiber type - string
        """
        self.debugger = debugger
        self.span_id = Span.ids
        Span.ids += 1
        self.fibre_type = fibre_type
        self.length = length * km
        self.fibre_attenuation = 0.22 / km  # fiber attenuation in decibels/km
        self.alpha = self.fibre_attenuation / (20 * np.log10(np.e))  # linear value fibre attenuation
        self.effective_length = (1 - np.exp(-2 * self.alpha * self.length)) / (2 * self.alpha)
        self.non_linear_coefficient = 0.78 / km  # gamma fiber non-linearity coefficient [W^-1 km^-1]
        self.dispersion = 2.1e-05
        self.dispersion_coefficient = self.beta2()  # B_2 dispersion coefficient [ps^2 km^-1]
        self.dispersion_slope = 0.1452 * (ps ** 3 / km)  # B_3 dispersion slope in (ps^3 km^-1)
        self.effective_area = 80 * um * um  # Aeff - SMF effective area
        self.raman_gain = 7.0 * 1e-12 * cm / W  # r - Raman Gain in SMF
        self.raman_amplification_band = 15 * THz  # Raman amplification band ~15THz
        # Raman coefficient
        self.raman_coefficient = self.raman_gain / (2 * self.effective_area * self.raman_amplification_band)

        self.optical_signals = []
        self.link = None
        self.prev_component = None
        self.next_component = None

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        """String representation"""
        return '<%d %.1fkm>' % (self.span_id, self.length/km)

    def reset(self):
        self.optical_signals = []

    def attenuation(self):
        return db_to_abs(self.fibre_attenuation * self.length)

    def beta2(self, ref_wavelength=1550e-9):
        """Returns beta2 from dispersion parameter.
        Dispersion is entered in ps/nm/km.
        Translated from the GNPy project source code
        :param ref_wavelength: can be a numpy array; default: 1550nm
        """
        D = abs(self.dispersion)
        b2 = (ref_wavelength ** 2) * D / (2 * pi * c)  # 10^21 scales [ps^2/km]
        return b2  # s/Hz/m

    def remove_optical_signal(self, optical_signal):
        if self.debugger:
            print("*** %s removing: %s" % (self, optical_signal))
        if optical_signal in self.optical_signals:
            self.optical_signals.remove(optical_signal)

    def include_optical_signal_in(self, optical_signal, power=None,
                                  ase_noise=None, nli_noise=None):
        """
        Include optical signal in optical_signals
        :param optical_signal: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        """
        if optical_signal not in self.optical_signals:
            self.optical_signals.append(optical_signal)
        optical_signal.assoc_loc_in(self, power, ase_noise, nli_noise)

    def include_optical_signal_out(self, optical_signal, power=None,
                                   ase_noise=None, nli_noise=None):
        """
        Include optical signal in optical_signals_out
        :param optical_signal: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        """
        optical_signal.assoc_loc_out(self, power, ase_noise, nli_noise)

    def propagate(self, is_last_port=False, safe_switch=False):
        for optical_signal in self.optical_signals:
            power_in = optical_signal.loc_in_to_state[self]['power']
            ase_noise_in = optical_signal.loc_in_to_state[self]['ase_noise']
            nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']

            self.include_optical_signal_out(optical_signal, power=power_in,
                                            ase_noise=ase_noise_in, nli_noise=nli_noise_in)
            self.link.include_optical_signal_out(optical_signal, power=power_in,
                                            ase_noise=ase_noise_in, nli_noise=nli_noise_in)

        if not isinstance(self.prev_component, LineTerminal):
            # Compute the nonlinear noise with the GN model
            self.output_nonlinear_noise()
            # Compute SRS effects from the fibre
            if self.link.srs_effect:
                if len(self.optical_signals) > 1:
                    self.zirngibl_srs()

            for optical_signal in self.optical_signals:
                power_out = optical_signal.loc_out_to_state[self]['power'] / self.attenuation()
                ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise'] / self.attenuation()
                nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise'] / self.attenuation()

                self.include_optical_signal_out(optical_signal, power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out)

        for optical_signal in self.optical_signals:
            in_port = self.next_component.link_to_port_in[self.link]
            if isinstance(self.next_component, LineTerminal):
                self.next_component.include_optical_signal_in(
                    optical_signal,
                    power=optical_signal.loc_out_to_state[self]['power'],
                    ase_noise=optical_signal.loc_out_to_state[self]['ase_noise'],
                    nli_noise=optical_signal.loc_out_to_state[self]['nli_noise'],
                    in_port=in_port)
                self.next_component.receiver(optical_signal, in_port)
            elif isinstance(self.next_component, Roadm):
                self.next_component.include_optical_signal_in_roadm(
                    optical_signal,
                    power=optical_signal.loc_out_to_state[self]['power'],
                    ase_noise=optical_signal.loc_out_to_state[self]['ase_noise'],
                    nli_noise=optical_signal.loc_out_to_state[self]['nli_noise'],
                    in_port=in_port)
            elif isinstance(self.next_component, Amplifier):
                self.next_component.include_optical_signal_in(
                    optical_signal,
                    power=optical_signal.loc_out_to_state[self]['power'],
                    ase_noise=optical_signal.loc_out_to_state[self]['ase_noise'],
                    nli_noise=optical_signal.loc_out_to_state[self]['nli_noise'],
                    in_port=0)

        if isinstance(self.next_component, Amplifier):
            self.next_component.propagate(self.optical_signals, is_last_port=is_last_port, safe_switch=safe_switch)
        elif isinstance(self.next_component, Roadm) and is_last_port:
            in_port = self.next_component.link_to_port_in[self.link]
            self.next_component.switch(in_port, self.link.src_node, safe_switch=safe_switch)

    def zirngibl_srs(self):
        """
        Computation taken from : M. Zirngibl Analytical model of Raman gain effects in massive
        wavelength division multiplexed transmission systems, 1998. - Equations 7,8.
        :return:
        """
        min_wavelength_index = 90
        max_wavelength_index = 0
        min_signal = None
        max_signal = None
        for optical_signal in self.optical_signals:
            if optical_signal.index < min_wavelength_index:
                min_signal = optical_signal
                min_wavelength_index = optical_signal.index
            if optical_signal.index > max_wavelength_index:
                max_signal = optical_signal
                max_wavelength_index = optical_signal.index
        frequency_min = min_signal.frequency  # minimum frequency of longest wavelength
        frequency_max = max_signal.frequency  # maximum frequency of shortest wavelength

        effective_length = self.effective_length  # SMF effective distance
        beta = self.raman_coefficient

        total_power = 0  # Total input power calculated by following loop
        for optical_signal in self.optical_signals:
            total_power += optical_signal.loc_out_to_state[self]['power']

        # Calculate delta P for each channel
        for optical_signal in self.optical_signals:
            frequency = optical_signal.frequency
            with errstate(divide='ignore'):
                r1 = beta * total_power * effective_length * (frequency_max - frequency_min) * math.e ** (
                        beta * total_power * effective_length * (frequency - frequency_min))  # term 1
                r2 = math.e ** (beta * total_power * effective_length * (frequency_max - frequency_min)) - 1  # term 2

                delta_p = float(r1 / r2)
                power_out = optical_signal.loc_out_to_state[self]['power'] * delta_p
                ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise'] * delta_p
                nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise'] * delta_p
                self.include_optical_signal_out(optical_signal, power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out)

    def output_nonlinear_noise(self):
        """
        Compute GN model and updates state data structures
        """
        nonlinear_noise = self.gn_model()
        for optical_signal in self.optical_signals:
            nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']
            if nonlinear_noise[optical_signal] == 'NoneType': nonlinear_noise[optical_signal] = 0
            nli_noise_out = float(nli_noise_in) + nonlinear_noise[optical_signal]
            self.include_optical_signal_out(optical_signal, nli_noise=nli_noise_out)

    def gn_model(self):
        """ Computes the nonlinear interference power on a single carrier.
        Translated from the GNPy project source code
        The method uses eq. 120 from arXiv:1209.0394.
        :return: carrier_nli: the amount of nonlinear interference in W on the carrier under analysis
        """
        nonlinear_noise_struct = {}
        channels_index = []
        index_to_signal = {}
        for channel in self.optical_signals:
            nonlinear_noise_struct[channel] = None
            channels_index.append(channel.index)
            index_to_signal[channel.index] = channel
        alpha = self.alpha
        beta2 = self.dispersion_coefficient
        gamma = self.non_linear_coefficient
        effective_length = self.effective_length
        asymptotic_length = 1 / (2 * alpha)

        for optical_signal in self.optical_signals:
            channel_under_test = optical_signal.index
            symbol_rate_cut = optical_signal.symbol_rate
            bw_cut = symbol_rate_cut
            pwr_cut = optical_signal.loc_out_to_state[self]['power']
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            g_nli = 0
            for ch in self.optical_signals:
                symbol_rate_ch = ch.symbol_rate
                bw_ch = symbol_rate_ch
                pwr_ch = ch.loc_out_to_state[self]['power']
                g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)
                psi = self.psi_factor(optical_signal, ch, beta2=beta2, asymptotic_length=asymptotic_length)
                g_nli += g_ch ** 2 * g_cut * psi

            with errstate(divide='ignore'):
                g_nli *= (16.0 / 27.0) * (gamma * effective_length) ** 2 / (2 * np.pi * abs(beta2) * asymptotic_length)

            signal_under_test = index_to_signal[channel_under_test]
            nonlinear_noise_struct[signal_under_test] = g_nli * bw_cut
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
            psi = np.arcsinh(0.5 * np.pi ** 2 * asymptotic_length * abs(beta2) * bw_cut ** 2)
        else:  # XCI, XPM
            delta_f = carrier.frequency - interfering_carrier.frequency
            psi = np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                             bw_cut * (delta_f + 0.5 * bw_ch))
            psi -= np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                              bw_cut * (delta_f - 0.5 * bw_ch))
        return psi

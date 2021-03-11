from collections import namedtuple
from units import *
from pprint import pprint


SpanTuple = namedtuple('Span', 'span amplifier')


class Link(object):
    """
    A Link refers to the connection between two network nodes (i.e., transceiver-ROADM or
    ROADM-ROADM). In the future we must enable network-element-node to controller-node
    connectivity.
    """

    def __init__(self, src_node, dst_node, src_out_port=-1, dst_in_port=-1,
                 boost_amp=None, srs_effect=False, spans=None):
        """
        :param src_node: source Node object
        :param dst_node: destination Node object
        """
        if src_node == dst_node:
            raise ValueError("link.__init__ src_node must be different from dst_node!")
        # configuration attributes
        self.id = id(self)
        self.src_node = src_node
        self.dst_node = dst_node
        self.boost_amp = boost_amp
        self.srs_effect = srs_effect
        self.spans = spans or []

        self.optical_signals = []

        # set connection ports for amps and the link
        if boost_amp:
            boost_amp.set_output_port(self.dst_node, self, output_port=0)
            boost_amp.set_input_port(self.src_node, self, input_port=0)
        for span, amplifier in spans:
            if amplifier:
                amplifier.set_output_port(self.dst_node, self, output_port=0)
                amplifier.set_input_port(self.src_node, self, input_port=0)
        self.src_node.set_output_port(self.dst_node, self, output_port=src_out_port)
        self.dst_node.set_input_port(self.src_node, self, input_port=dst_in_port)

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

    def __repr__(self):
        """String representation"""
        return "(%s->%s)" % (self.src_node, self.dst_node)

    def remove_optical_signal(self, optical_signal_tuple):
        optical_signal = optical_signal_tuple[0]
        print("%s - %s removing signal: %s-%s" % (self.__class__.__name__, self, optical_signal, optical_signal.uid))
        if optical_signal in self.optical_signals:
            self.optical_signals.remove(optical_signal)

        for span, amplifier in self.spans:
            if amplifier:
                amplifier.remove_optical_signal(optical_signal_tuple)

        if self.dst_node is not None:
            self.dst_node.remove_optical_signal((optical_signal, optical_signal.uid))

    def include_optical_signal_in(self, optical_signal_tuple, in_port=None, power=None,
                                  ase_noise=None, nli_noise=None, tup_key=None):
        """
        Include optical signal in optical_signals
        :param optical_signal_tuple: OpticalSignal object
        :param in_port: output port from Node
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param tup_key: tuple key composed of (Link, Span)
        """
        optical_signal = optical_signal_tuple[0]
        if optical_signal not in self.optical_signals:
            self.optical_signals.append(optical_signal)

        if tup_key:
            optical_signal.assoc_loc_in(tup_key, power, ase_noise, nli_noise)
        else:
            optical_signal.assoc_loc_in(self, power, ase_noise, nli_noise)

    def include_optical_signal_out(self, optical_signal_tuple, power=None, ase_noise=None, nli_noise=None, tup_key=None):
        """
        Include optical signal in optical_signals_out
        :param optical_signal_tuple: OpticalSignal object
        :param power: power level of OpticalSignal
        :param ase_noise: ase noise level of OpticalSignal
        :param nli_noise: nli noise  level of OpticalSignal
        :param tup_key: tuple key composed of (Link, Span)
        """
        optical_signal = optical_signal_tuple[0]
        if tup_key:
            optical_signal.assoc_loc_out(tup_key, power, ase_noise, nli_noise)
        else:
            optical_signal.assoc_loc_out(self, power, ase_noise, nli_noise)

    def propagate(self, equalization=False, is_last_port=False):
        """
        Propagate the signals across the link
        :param equalization:
        :param is_last_port:
        :return:
        """
        if self.propagate_simulation(equalization):
            # use is instance instead of checking the class
            if self.dst_node.__class__.__name__ is 'LineTerminal':
                # we need to pass the signals individually and indicate
                # what port should match what signal
                for optical_signal in self.optical_signals:
                    in_port = self.dst_node.link_to_port_in[self]
                    self.dst_node.include_optical_signal_in((optical_signal, optical_signal.uid),
                                                            in_port=in_port, src_node=self.src_node)
                if is_last_port:
                    self.dst_node.receiver(self.src_node)
            else:
                for optical_signal in self.optical_signals:
                    # if it's just one signal this enters just once.
                    # a single link could have multiple optical signals
                    # and the link only has an input port of reference for
                    # the dst_node
                    in_port = self.dst_node.link_to_port_in[self]
                    self.dst_node.include_optical_signal_in((optical_signal, optical_signal.uid),
                                                            in_port=in_port, src_node=self.src_node)

                if is_last_port:
                    self.dst_node.switch(self.src_node)

    def propagate_simulation(self, equalization):
        """
        Compute the propagation of signals over this link
        :return:
        """
        # get the output power of the signals at output boost port
        output_power_dict = {}
        # If there is an amplifier compensating for the node
        # attenuation, compute the physical effects
        if self.boost_amp:  # Implementing boost as part of ROADM? Probably yes.
            for optical_signal in self.optical_signals:
                # associate boost_amp to optical signal at input interface
                self.boost_amp.include_optical_signal_in((optical_signal, optical_signal.uid),
                                                         in_port=0, src_node=self.src_node)
            # Enabling amplifier system gain balancing check
            # print(self.boost_amp)
            while not (self.boost_amp.power_excursions_flag_1 and self.boost_amp.power_excursions_flag_2):
                for optical_signal in self.optical_signals:
                    output_power_dict[optical_signal] = \
                        self.boost_amp.output_amplified_power(optical_signal, dst_node=self.dst_node)
                self.boost_amp.compute_power_excursions()
            self.boost_amp.power_excursions_flags_off()

            if equalization:
                # procedure for VOA reconfiguration (equalization)
                src_node_out_port = self.src_node.link_to_port_out[self]
                self.src_node.equalization_reconf(self, output_power_dict, src_node_out_port)
                # return False to avoid propagation of effects
                return False

            for optical_signal in self.optical_signals:
                self.boost_amp.nli_compensation(optical_signal, dst_node=self.dst_node)
                # Compute ASE noise generation
                self.boost_amp.stage_amplified_spontaneous_emission_noise(optical_signal)

        # Needed for the subsequent computations
        prev_amp = self.boost_amp
        for span, amplifier in self.spans:
            for optical_signal in self.optical_signals:
                # associate (Link, Span) to optical signal at input interface
                self.include_optical_signal_in((optical_signal, optical_signal.uid), tup_key=(self, span))
                # this will initialize the output state of the signal
                # that will enable the subsequent computations
                self.include_optical_signal_out((optical_signal, optical_signal.uid), tup_key=(self, span))


            conn_loss_in = db_to_abs(span.conn_loss_in + span.att_in)
            for optical_signal in self.optical_signals:
                power_out = optical_signal.loc_out_to_state[(self, span)]['power'] / conn_loss_in
                ase_noise_out = optical_signal.loc_out_to_state[(self, span)]['ase_noise'] / conn_loss_in
                nli_noise_out = optical_signal.loc_out_to_state[(self, span)]['nli_noise'] / conn_loss_in

                self.include_optical_signal_out((optical_signal, optical_signal.uid), power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                                                tup_key=(self, span))

            if amplifier:
                # Compute the nonlinear noise with the GN model
                self.output_nonlinear_noise(span)

            # Compute SRS effects from the fibre
            if self.srs_effect:
                if len(self.optical_signals) > 1 and prev_amp:
                    self.zirngibl_srs(span)

            # Compute linear effects from the fibre
            span_attenuation = db_to_abs(span.length * span.fibre_attenuation)
            for optical_signal in self.optical_signals:
                power_out = optical_signal.loc_out_to_state[(self, span)]['power'] / span_attenuation
                ase_noise_out = optical_signal.loc_out_to_state[(self, span)]['ase_noise'] / span_attenuation
                nli_noise_out = optical_signal.loc_out_to_state[(self, span)]['nli_noise'] / span_attenuation

                self.include_optical_signal_out((optical_signal, optical_signal.uid), power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                                                tup_key=(self, span))

            # Compute amplifier compensation
            if amplifier:
                for optical_signal in self.optical_signals:
                    # associate amp to optical signal at input interface
                    amplifier.include_optical_signal_in((optical_signal, optical_signal.uid),
                                                        in_port=0, src_node=self.src_node)
                # Enabling balancing check
                while not (amplifier.power_excursions_flag_1 and amplifier.power_excursions_flag_2):
                    for optical_signal in self.optical_signals:
                        amplifier.output_amplified_power(optical_signal, dst_node=self.dst_node)
                    amplifier.compute_power_excursions()
                # Reset balancing flags to original settings
                amplifier.power_excursions_flags_off()

                # Compute for the power
                for optical_signal in self.optical_signals:
                    amplifier.nli_compensation(optical_signal, dst_node=self.dst_node)
                    # Compute ASE noise generation
                    amplifier.stage_amplified_spontaneous_emission_noise(optical_signal, dst_node=self.dst_node)

                    power_out = optical_signal.loc_out_to_state[amplifier]['power']
                    ase_noise_out = optical_signal.loc_out_to_state[amplifier]['ase_noise']
                    nli_noise_out = optical_signal.loc_out_to_state[amplifier]['nli_noise']
                    self.include_optical_signal_in((optical_signal, optical_signal.uid), power=power_out,
                                                    ase_noise=ase_noise_out, nli_noise=nli_noise_out)

            prev_amp = amplifier
        return True

    def zirngibl_srs(self, span):
        """
        Computation taken from : M. Zirngibl Analytical model of Raman gain effects in massive
        wavelength division multiplexed transmission systems, 1998. - Equations 7,8.
        :param span: Span() object
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

        effective_length = span.effective_length  # SMF effective distance
        beta = span.raman_coefficient

        total_power = 0  # Total input power calculated by following loop
        for optical_signal in self.optical_signals:
            total_power += optical_signal.loc_out_to_state[(self, span)]['power'] * mW

        # Calculate delta P for each channel
        for optical_signal in self.optical_signals:
            frequency = optical_signal.frequency
            r1 = beta * total_power * effective_length * (frequency_max - frequency_min) * math.e ** (
                    beta * total_power * effective_length * (frequency - frequency_min))  # term 1
            r2 = math.e ** (beta * total_power * effective_length * (frequency_max - frequency_min)) - 1  # term 2

            delta_p = float(r1 / r2)  # Does the arithmetic in mW
            power_out = optical_signal.loc_out_to_state[(self, span)]['power'] * delta_p
            ase_noise_out = optical_signal.loc_out_to_state[(self, span)]['ase_noise'] * delta_p
            nli_noise_out = optical_signal.loc_out_to_state[(self, span)]['nli_noise'] * delta_p
            self.include_optical_signal_out((optical_signal, optical_signal.uid), power=power_out,
                                            ase_noise=ase_noise_out, nli_noise=nli_noise_out,
                                            tup_key=(self, span))

    def output_nonlinear_noise(self, span):
        """
        :param span: Span() object
        :return: dict{signal_index: accumulated NLI noise levels}
        """
        nonlinear_noise_new = self.gn_model(span)

        for optical_signal in self.optical_signals:
            nli_noise_in = optical_signal.loc_in_to_state[(self, span)]['nli_noise']
            nli_noise_out = nli_noise_in + nonlinear_noise_new[optical_signal]
            # nli_noise_out = nonlinear_noise_new[optical_signal]
            self.include_optical_signal_out((optical_signal, optical_signal.uid), nli_noise=nli_noise_out, tup_key=(self, span))

    def gn_model(self, span):
        """ Computes the nonlinear interference power on a single carrier.
        Translated from the GNPy project source code
        The method uses eq. 120 from arXiv:1209.0394.
        :param span:
        :return: carrier_nli: the amount of nonlinear interference in W on the carrier under analysis
        """

        nonlinear_noise_struct = {}
        channels_index = []
        index_to_signal = {}
        for channel in self.optical_signals:
            nonlinear_noise_struct[channel] = None
            channels_index.append(channel.index)
            index_to_signal[channel.index] = channel
        alpha = span.alpha
        beta2 = span.dispersion_coefficient
        gamma = span.non_linear_coefficient
        effective_length = span.effective_length
        asymptotic_length = 1 / (2 * alpha)

        for optical_signal in self.optical_signals:
            channel_under_test = optical_signal.index
            symbol_rate_cut = optical_signal.symbol_rate
            bw_cut = symbol_rate_cut
            # pwr_cut = round(optical_signal.loc_out_to_state[(self, span)]['power'], 2) * 1e-3
            pwr_cut = optical_signal.loc_out_to_state[(self, span)]['power'] * 1e-3
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            g_nli = 0
            for ch in self.optical_signals:
                symbol_rate_ch = ch.symbol_rate
                bw_ch = symbol_rate_ch
                pwr_ch = ch.loc_out_to_state[(self, span)]['power'] * 1e-3
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
            psi = np.arcsinh(0.5 * np.pi ** 2 * asymptotic_length * abs(beta2) * bw_cut ** 2)
        else:  # XCI, XPM
            delta_f = carrier.frequency - interfering_carrier.frequency
            psi = np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                             bw_cut * (delta_f + 0.5 * bw_ch))
            psi -= np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                              bw_cut * (delta_f - 0.5 * bw_ch))
        return psi


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

        self.input_power = {}  # dict signal to input power
        self.output_power = {}  # dict signal to output power

        # Parameters to add:
        self.att_in = 0
        self.conn_loss_in = 0
        self.conn_loss_out = 0
        self.padding = 0

    def describe(self):
        pprint(vars(self))

    def __repr__(self):
        """String representation"""
        return '<%d %.1fkm>' % (self.span_id, self.length/km)

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

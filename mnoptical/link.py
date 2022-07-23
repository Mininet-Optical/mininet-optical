from collections import namedtuple
from mnoptical.units import *
from pprint import pprint
from numpy import errstate
from mnoptical.node import LineTerminal, Roadm, Amplifier
from mnoptical.edfa_params import fibre_spectral_attenuation
import math


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
        FIXME: Using a different file for the physical effects
        """
        self.debugger = debugger
        self.span_id = Span.ids
        Span.ids += 1
        self.fibre_type = fibre_type
        self.length = length * km
        self.fibre_attenuation = (self.get_fibre_spectral_attenuation())[::-1]
        self.alpha = (self.fibre_attenuation) / (20 * np.log10(np.e))  # fibre attenuation
        self.effective_length = (1 - np.exp(-2 * self.alpha * self.length)) / (2 * self.alpha)
        self.non_linear_coefficient = 1.2 / km  # gamma fiber non-linearity coefficient [W^-1 km^-1]
        self.dispersion = 1.67e-05
        self.dispersion_coefficient = self.beta2()  # B_2 dispersion coefficient [ps^2 km^-1]
        self.dispersion_slope = 0.1452 * (ps ** 3 / km)  # B_3 dispersion slope in (ps^3 km^-1)
        self.effective_area = 80 * um * um  # Aeff - SMF effective area
        self.raman_gain = 7.0 * 1e-12 * cm / W  # r - Raman Gain in SMF
        self.raman_amplification_band = 15 * THz  # Raman amplification band ~15THz
        # Raman coefficient
        self.raman_coefficient = self.raman_gain / (2 * self.effective_area * self.raman_amplification_band)
        #self.raman_coefficient = (8.2e-17 / 2) or (7.87e-17 / 2) for 50 or 25 km spans
         
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

    def get_fibre_spectral_attenuation(self):
        """
        Retrieve the WDL of the single mode fibre
        :return: WDL of the SMF
        """
        self.attenuation_values = list(fibre_spectral_attenuation['SMF'])

        for i in range(0, len(self.attenuation_values)):
            self.attenuation_values[i] = self.attenuation_values[i] / km
            # self.attenuation_values[i] = 0.22 / km   # for linear attenuation

        return self.attenuation_values

    def attenuation(self, signal_index=1):
        """
        Returns the attenuation value for each wavelength by the signal's index
        :param signal_index:
        """
        self.attenuation_values = self.get_fibre_spectral_attenuation()
        self.fibre_attenuation = self.attenuation_values[92 - signal_index]
        return db_to_abs(self.fibre_attenuation * self.length)

    def beta2(self, ref_wavelength=1550e-9):
        """Returns beta2 from dispersion parameter.
        Dispersion is entered in ps/nm/km.
        Translated from the GNPy project source code
        :param ref_wavelength: can be a numpy array; default: 1550nm
        """
        D = abs(self.dispersion)
        b2 = -(ref_wavelength ** 2) * D / (2 * pi * c)  # 10^21 scales [ps^2/km]
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
                    self.srs_effect_model()
                    # self.Zirngibl_General_Method()
                    # self.Sylvestre_SRS_model()
                    # self.Bigo_SRS_model()
                    # self.capacity_length_product()

            for optical_signal in self.optical_signals:
                power_out = optical_signal.loc_out_to_state[self]['power'] / self.attenuation(optical_signal.index)
                ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise'] / self.attenuation(optical_signal.index)
                nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise'] / self.attenuation(optical_signal.index)

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

    def srs_effect_model(self):
        """
        Computation taken from : M. Zirngibl Analytical model of Raman gain effects in massive
        wavelength division multiplexed transmission systems, 1998. - Equation 10.
        - Most accurate for uniform loading cases.
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
        i = 0
        # Calculate delta P for each channel
        for optical_signal in self.optical_signals:
            frequency = optical_signal.frequency

            with errstate(divide='ignore'):
                i = i+1
                r1 = beta * total_power * effective_length[i] * (frequency_max - frequency_min) * math.e ** (
                        beta * total_power * effective_length[i] * (frequency - frequency_min))  # term 1
                r2 = math.e ** (beta * total_power * effective_length[i] * (frequency_max - frequency_min)) - 1  # term 2
                delta_p = float(r1 / r2)
                power_out = optical_signal.loc_out_to_state[self]['power'] / delta_p
                ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise'] / delta_p
                nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise'] / delta_p
                self.include_optical_signal_out(optical_signal, power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out)

    def Zirngibl_General_Method(self):
        """
        The general form of the SRS model as proposed by M. Zirngibl in
        Analytical model of Raman gain effects in massive wavelength division
        multiplexed transmission systems, 1998." - Equation 7
        - Most accurate for non-uniform loading cases.
        """
	
        beta = self.raman_coefficient  # (mWHz)^-1
        effective_length = self.effective_length  # SMF effective length (km)
        alpha = self.alpha  # fibre attenuation in dB/km

        power_array = []  # to store the power level of each channel
        channels_frequency = []  # to store the frequency of each channel
        total_power = 0
        i = 0
        counter = 1

        # Iterate through all the signals
        for optical_signal in self.optical_signals:
            current_ch_power = optical_signal.loc_out_to_state[self]['power']
            # Sum the power across the channels
            total_power += current_ch_power
            power_array.append(current_ch_power)

            # Store each channel's frequency
            frequency = (optical_signal.frequency)
            channels_frequency.append(frequency)

        # Calculate delta P for each channel
        for optical_signal in self.optical_signals:
            num = power_array[i] * (total_power) * math.e ** (- alpha[i] * (self.length))
            den = 0
            for j in range(0, len(power_array)):
                den = power_array[j] * math.e ** (beta * total_power * effective_length[i] * (channels_frequency[j] - channels_frequency[i]))
                den_sum += den
            i += 1

            with errstate(divide='ignore'):
                delta_p = float(num / den_sum)

            counter += 1

            # Update the current values
            power_out = optical_signal.loc_out_to_state[self]['power'] / delta_p
            ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise'] / delta_p
            nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise'] / delta_p
            self.include_optical_signal_out(optical_signal, power=power_out,
                                                ase_noise=ase_noise_out, nli_noise=nli_noise_out)

    def capacity_length_product(self, system_capacity=4450e9, amplifier_spacing=50e3):
        """
        CLP analytical model by Hyun Deok Kim and Chang-Hee Lee in
        Capacities of WDM Transmission Systems and Networks Limited by
        Stimulated Raman Scattering, 2001. - Equations 1 and 2
        """
        max_wavelength_index = 0

        # get the frequency of the shortest wavelength
        max_signal = None
        no_of_signals = 0
        for optical_signal in self.optical_signals:
            if optical_signal.index > max_wavelength_index:
                max_signal = optical_signal
                max_wavelength_index = optical_signal.index
            no_of_signals += 1
        frequency_max = max_signal.frequency  # shortest wavelength

        # calculate K
        NF = 5.6  # dB
        plank_constant = 6.62607015e-34  # (Joule second)
        photon_energy = (plank_constant * frequency_max)  # shortest wavelength
        fibre_attenuation = 0.22 / 1000  # dB/km
        optical_resolution_bandwidth = 12.5e9  # Hz
        amplifier_spacing = 50e3  # m
        exp_val = np.exp(fibre_attenuation * amplifier_spacing) - 1
        # K is a constant for the defined expression
        K = (NF * photon_energy * optical_resolution_bandwidth * exp_val)
        K = np.power(K, -1)
        effective_area = 72e-6  # um

        # transmission_length, L -> No of spans * length of each span
        length = self.length * 2
        fibre_attenuation = 0.22 / 1000
        alpha = fibre_attenuation / (20 * np.log10(np.e))  # linear attenuation
        effective_length = (1 - np.exp(- alpha * length)) / (alpha)
        channel_spacing = 50e9  # Hz
        transmission_bandwidth = channel_spacing * (no_of_signals - 1)
        raman_gain_coef = 5.9e-27  # slope of the Raman gain profile
        bit_rate = 10e9  # bps
        CLPs = []
        OSNR_values = [10, 20, 30, 40, 50, 60, 70]
        for OSNR in OSNR_values:
            n1 = (2.6 * effective_area) / (raman_gain_coef * effective_length)
            n2 = bit_rate / OSNR
            n3 = system_capacity / transmission_bandwidth
            CLP = amplifier_spacing * np.sqrt(K * n1 * n2 * n3)
            CLPs.append(CLP)

    def Sylvestre_SRS_model(self):
        """
        SRS model proposed in 'Raman-Induced Power Tilt in Arbitrarily 
        Large Wavelength-Division-MUltiplexed Systems' by T. Sylvestre et al., 2005
        - Equation 6
        """
        F_j = [-1.5690, 5.6979, -6.5340, 4.7408, -2.0005, 0.1426, 5.9511, -3.2483, -2.4842, 0.4010]
        omega_j = [0.0532, 4.1560, 5.2066, 6.4445, 7.2368, 14.9782, 15.7841, 16.3591, 18.2431, 24.4251]
        delta_j = [1.2745, 7.4252, 5.2615, 4.8111, 3.7719, 0.6586, 4.2635, 2.2120, 5.4013, 1.3313]

        for i in range(0, len(F_j)):
            omega_j[i] = omega_j[i] * (2 * math.pi)
            delta_j[i] = delta_j[i] * (2 * math.pi)

        channel_spacing = 0.05  # THz
        delta_w = 2 * math.pi * channel_spacing

        length = self.length / km
        total_power = 0  # Total input power calculated by following loop
        no_of_channels = 0
        for optical_signal in self.optical_signals:
            total_power += optical_signal.loc_out_to_state[self]['power']
            no_of_channels += 1
        average_input_power = total_power / no_of_channels

        f_R = 0.18  # f_R raman_polarisation
        non_linearity = 0.78  # W^-1 km^-1 at 1550nm
        effective_length = self.effective_length  # SMF effective distance
        n_R = 10
        ind = 0

        # Calculate delta P for each channel
        for optical_signal in self.optical_signals:
            total_sum = 0
            # change no_of_channels to the signal.index
            # repeat iteratively for each individual channel
            for k in range(1, optical_signal.index - 1):
                for j in range(1, n_R):
                    numerator = k * delta_w * F_j[j] * omega_j[j] * (delta_j[j]**2)
                    denominator1 = ((delta_j[j] ** 2) + (omega_j[j] ** 2))**2
                    denominator2 = (k * delta_w) ** 2
                    denominator3 = ((k * delta_w) ** 2) + (2 * (delta_j[j] ** 2)) - (2 * (omega_j[j] ** 2))

                denominator = denominator1 + (denominator2 * denominator3)
                div = numerator / denominator
                total_sum += div
            delta_p = 34.74 * average_input_power * effective_length[ind] * non_linearity * f_R * total_sum
            ind += 1
            delta_p_linear = db_to_abs(delta_p)  # convert to linear

            # Update the current values
            power_out = optical_signal.loc_out_to_state[self]['power'] / delta_p_linear
            ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise'] * delta_p_linear
            nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise'] * delta_p_linear
            self.include_optical_signal_out(optical_signal, power=power_out,
                                                    ase_noise=ase_noise_out, nli_noise=nli_noise_out)

    def Bigo_SRS_model(self):
        """
        SRS model proposed in the paper tilted:
        'Experimental Investigation of Stimulated Raman Scattering
        Limitation on WDM Transmission Over Various Types of Fiber
        Infrastructures' by S.Bigo et al., 1999 - Equation 1
        - Simplified form of the srs_effect_model() function
        """

        channel_spacing = 50e9
        total_power = 0
        no_of_channels = 0
        for optical_signal in self.optical_signals:
            # sum the total power across the channels
            total_power += optical_signal.loc_out_to_state[self]['power']
            no_of_channels += 1

        average_input_power = total_power / no_of_channels  # average channel power
        g_Aeff = 8.2e-17  # estimated Raman gain coefficient for a 50 km span in COSMOS
        #g_Aeff = 7.87e-17  # estimated Raman gain coefficient for a 25 km span in COSMOS
	
        # Calculate delta P for each channel using the model
        for optical_signal in self.optical_signals:

            delta_p = 2.17 * (g_Aeff) * average_input_power * no_of_channels * (optical_signal.index - 1) * self.effective_length[optical_signal.index] * channel_spacing
            delta_p_linear = db_to_abs(delta_p)  # convert to linear

            # Update the current values
            power_out = optical_signal.loc_out_to_state[self]['power'] / delta_p_linear
            ase_noise_out = optical_signal.loc_out_to_state[self]['ase_noise'] / delta_p_linear
            nli_noise_out = optical_signal.loc_out_to_state[self]['nli_noise'] / delta_p_linear
            self.include_optical_signal_out(optical_signal, power=power_out,
                                                    ase_noise=ase_noise_out, nli_noise=nli_noise_out)

    def output_nonlinear_noise(self):
        """
        Compute GN model and updates state data structures
        """
        nonlinear_noise = self.gn_model()
        for optical_signal in self.optical_signals:
            nli_noise_in = optical_signal.loc_in_to_state[self]['nli_noise']
            nli_noise_out = nli_noise_in + nonlinear_noise[optical_signal]
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
        beta2 = self.beta2()
        gamma = self.non_linear_coefficient
        effective_length = self.effective_length
        asymptotic_length = 1 / (2 * alpha)

        index = 0
        for optical_signal in self.optical_signals:
            channel_under_test = optical_signal.index
            symbol_rate_cut = optical_signal.symbol_rate
            bw_cut = symbol_rate_cut
            pwr_cut = optical_signal.loc_out_to_state[self]['power']
            g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

            g_nli = 0
            i = 0
            for ch in self.optical_signals:

                symbol_rate_ch = ch.symbol_rate
                bw_ch = symbol_rate_ch
                pwr_ch = ch.loc_out_to_state[self]['power']
                g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)
                psi = self.psi_factor(optical_signal, ch, beta2=beta2, asymptotic_length=asymptotic_length[i])
                g_nli += g_ch ** 2 * g_cut * psi

                i += 1
            with errstate(divide='ignore'):
                g_nli *= (16.0 / 27.0) * (gamma * effective_length[index]) ** 2 / (2 * np.pi * abs(beta2) * asymptotic_length[index])
                index = index + 1

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


from collections import namedtuple
import math
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


SpanTuple = namedtuple('Span', 'span amplifier')


class Link(object):
    """
    A Link refers to the connection between two network nodes (i.e., transceiver-ROADM or
    ROADM-ROADM). In the future we must enable network-element-node to controller-node
    connectivity.
    """

    def __init__(self, node1, node2, new_input_port1,
                 new_output_port1, new_input_port2, new_output_port2,
                 preamp):
        """

        :param node1: source Node object
        :param node2: destination Node object
        """
        if node1 == node2:
            raise ValueError("link.__init__ src_node must be different from dst_node!")

        self.id = id(self)
        self.node1 = node1
        self.node2 = node2
        self.input_port1 = new_input_port1
        self.output_port1 = new_output_port1
        self.input_port2 = new_input_port2
        self.output_port2 = new_output_port2
        self.preamp = preamp

        self.signal_power_in = {}  # dict of ports to signals and power levels
        self.signal_power_out = {}  # dict of ports to signals and power levels

        self.spans = []

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

    def incoming_transmission(self, node):
        """
        INCOMPLETE FUNCTION OCT. 6TH, 2019
        :param node:
        :return:
        """
        self.signal_power_in.update(node.port_to_signal_power_out[self.output_port1])
        if self.preamp:
            for signal, in_power in self.signal_power_in.items():
                preamp_power = 0
        self.describe()
        for span, amplifier in self.spans:
            pass

    @staticmethod
    def output_amplified_power(signal_power, target_gain, mode, launch_power, amplifier_wavelength_dependent_gain):
        """
        :param signal_power: units: mW - float
        :param target_gain: units mW (absolute value) - float
        :param mode: amplifier mode - string
        :param launch_power: units: mW, only used if mode=AGC - float
        :param amplifier_wavelength_dependent_gain: units: mW - float
        :param amplifier_wavelength_dependent_gain: units: mW - float
        :return: amplification-compensated power levels - float
        """
        if mode == 'AGC':
            # Adjust the gain to keep signal power constant
            target_gain = db_to_abs(abs(abs_to_db(signal_power) - launch_power))
        # Conversion from dB to linear
        target_gain_linear = db_to_abs(target_gain)
        wavelength_dependent_gain_linear = db_to_abs(amplifier_wavelength_dependent_gain)
        return signal_power * target_gain_linear * wavelength_dependent_gain_linear

    @staticmethod
    def stage_amplified_spontaneous_emission_noise(signal_frequency, amplifier_target_gain,
                                                   amplifier_wavelength_dependent_gain,
                                                   amplifier_noise_figure, amplifier_bandwidth):
        """
        :param signal_frequency: units: THz
        :param amplifier_target_gain: units: dB
        :param amplifier_wavelength_dependent_gain: units: dB
        :param amplifier_noise_figure: units: dB
        :param amplifier_bandwidth: units: GHz
        :return: ASE noise in linear form
        Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
        """

        # Compute parameters needed for ASE model
        population_inversion = 0.5 * 10 ** (amplifier_noise_figure / 10.0)
        amplifier_gain = amplifier_target_gain - 1

        # Conversion from dB to linear
        gain_linear = db_to_abs(amplifier_gain)
        wavelength_dependent_gain_linear = db_to_abs(amplifier_wavelength_dependent_gain)

        # Calculation of the amplified spontaneous emission (ASE) noise.
        # Simpler formula
        # ase_noise = db_to_abs(amplifier_noise_figure) * sc.h * signal_frequency * amplifier_bandwidth
        ase_noise = 2 * population_inversion * (gain_linear * wavelength_dependent_gain_linear) * \
                    sc.h * signal_frequency * amplifier_bandwidth
        return ase_noise


class Span(object):

    def __init__(self, fibre_type='SMF', length=20.0):
        """
        :param length: optical fiber span length in km - float
        :param fibre_type: optical fiber type - string
        """
        self.span_id = id(self)
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

    def describe(self):
        pprint(vars(self))

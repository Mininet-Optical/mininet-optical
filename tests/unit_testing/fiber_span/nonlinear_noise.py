import numpy as np
import units as unit
from pprint import pprint
import matplotlib.pyplot as plt


def order_signals(signals):
    signal_by_index = {signal.index: signal for signal in signals}
    indices = [signal.index for signal in signals]
    ordered_signals_by_index = sorted(indices)
    ordered_signals = [signal_by_index[i] for i in ordered_signals_by_index]
    return ordered_signals


def plot_list_osnr(_list):
    fig_count = 1
    for element in _list:
        plt.figure(fig_count)
        plt.xlabel("Channel index")
        plt.ylabel("G_NLI")
        plt.plot(element, linestyle='None', linewidth=4, color='g', marker='D', markersize=8, markerfacecolor='None', )
        fig_count += 1
    plt.show()


def plot_list_osnr_sf(_list):
    plt.xlabel("Channel index")
    plt.ylabel("G_NLI")
    for element in _list:
        plt.plot(element, linestyle='None', linewidth=4, marker='D', markersize=8, markerfacecolor='None', )
    plt.show()


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


def init_nonlinear_noise(signals_dict):
    nonlinear_noise = {}
    for ch, in_pwr in signals_dict.items():
        nonlinear_noise[ch] = in_pwr / db_to_abs(50)
    return nonlinear_noise


def output_nonlinear_noise(_nonlinear_noise, signal_power_progress, signals, span):
    """
    :param _nonlinear_noise:
    :param signal_power_progress:
    :param signals: signals interacting at given transmission - list[Signal() object]
    :param span: Span() object
    :return: dict{signal_index: accumulated NLI noise levels}
    """
    nonlinear_noise_new = gn_analytic(signals, signal_power_progress, span)

    out_noise = {}
    for signal, value in _nonlinear_noise.items():
        out_noise[signal] = value + nonlinear_noise_new[signal]
    return out_noise


def gn_analytic(optical_signals, signal_power_progress, span):
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

    alpha = span.fibre_attenuation
    beta2 = span.dispersion_coefficient
    gamma = span.non_linear_coefficient
    effective_length = span.effective_length
    asymptotic_length = 1 / (2 * alpha)

    for optical_signal in optical_signals:
        channel_under_test = optical_signal.index
        symbol_rate_cut = optical_signal.symbol_rate
        bw_cut = symbol_rate_cut
        pwr_cut = signal_power_progress[optical_signal]
        g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

        g_nli = 0
        for ch in optical_signals:
            symbol_rate_ch = ch.symbol_rate
            bw_ch = symbol_rate_ch
            pwr_ch = signal_power_progress[ch]
            g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)

            g_nli += g_ch ** 2 * g_cut * my_psi(optical_signal, ch, beta2=beta2, asymptotic_length=asymptotic_length)

        g_nli *= (16.0 / 27.0) * ((gamma * effective_length) ** 2)
        signal_under_test = index_to_signal[channel_under_test]
        nonlinear_noise_struct[signal_under_test] = bw_cut * g_nli

    return nonlinear_noise_struct


def _psi(carrier, interfering_carrier, beta2, asymptotic_length):
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
        psi = np.arcsinh(unit.pi ** 2 * asymptotic_length * abs(beta2) *
                         bw_cut * (delta_f + 0.5 * bw_ch))
        psi -= np.arcsinh(unit.pi ** 2 * asymptotic_length * abs(beta2) *
                          bw_cut * (delta_f - 0.5 * bw_ch)) / (4 * unit.pi * abs(beta2) * asymptotic_length)
    return psi


def my_psi(carrier, interfering_carrier, beta2, asymptotic_length):
    """Calculates eq. 123 from `arXiv:1209.0394 <https://arxiv.org/abs/1209.0394>`__
    Translated from the GNPy project source code
    """
    symbol_rate_cut = carrier.symbol_rate
    bw_cut = symbol_rate_cut

    symbol_rate_ch = interfering_carrier.symbol_rate
    bw_ch = symbol_rate_ch

    if carrier.index == interfering_carrier.index:  # SCI, SPM
        psi = np.arcsinh(0.5 * unit.pi ** 2 * asymptotic_length * abs(beta2) * bw_cut ** 2) / \
              (2 * unit.pi * abs(beta2) * asymptotic_length)
    else:  # XCI, XPM
        delta_f = carrier.frequency - interfering_carrier.frequency
        div = 4 * unit.pi * abs(beta2) * asymptotic_length
        psi = np.arcsinh(unit.pi ** 2 * asymptotic_length * abs(beta2) * (delta_f + bw_ch / 2) * bw_ch) / div
        psi -= np.arcsinh(unit.pi ** 2 * asymptotic_length * abs(beta2) * (delta_f - bw_ch / 2) * bw_ch) / div
    return psi


class Span:

    def __init__(self, fibre_type='SMF', length=20.0):
        """
        :param length: optical fiber span length in km - float
        :param fibre_type: optical fiber type - string
        """
        self.span_id = id(self)
        self.fibre_type = fibre_type
        self.length = length * unit.km
        self.fibre_attenuation = 0.22 / unit.km  # fiber attenuation in decibels/km
        # loss_coefficient = math.e ** (-2 * fibre_attenuation * length)
        self.effective_length = (1 - np.exp(-2 * self.fibre_attenuation * length)) / 2 * self.fibre_attenuation
        self.non_linear_coefficient = 1.3 / unit.km  # gamma fiber non-linearity coefficient [W^-1 km^-1]
        self.dispersion_coefficient = 20.7 * (unit.ps ** 2 / unit.km)  # B_2 dispersion coefficient [ps^2 km^-1]
        self.dispersion_slope = 0.1452 * (unit.ps ** 3 / unit.km)  # B_3 dispersion slope in (ps^3 km^-1)
        # self.effective_area = 80 * unit.um * unit.um  # Aeff - SMF effective area
        # self.raman_gain = 7.0 * 1e-12 * unit.cm / unit.W  # r - Raman Gain in SMF
        # self.raman_amplification_band = 15 * unit.THz  # Raman amplification band ~15THz
        # # Raman coefficient
        # self.raman_coefficient = self.raman_gain / (2 * self.effective_area * self.raman_amplification_band)


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

    def __repr__(self):
        if self.index < 10:
            return '<0%d>' % self.index
        return '<%d>' % self.index


if __name__ == '__main__':
    # Initial launch power for ALL signals
    in_power = db_to_abs(0)
    # Signals to be used - by index
    channel_indices = list(range(1, 12))
    spectrum_band = 'C'
    channel_spacing = 0.4 * 1e-9
    modulation_format = '16-QAM'
    bits_per_symbol = 4.0
    symbol_rate = 32e9

    signal_to_power = {OpticalSignal(i, spectrum_band, channel_spacing, symbol_rate, bits_per_symbol):
                                in_power for i in channel_indices}
    signals = signal_to_power.keys()

    # single span declaration
    spanx = Span('SMF', length=100.0)
    amp_compensation = db_to_abs(100*0.22)
    # initial nonlinear interference noise
    nli = init_nonlinear_noise(signal_to_power)
    _nli = 0
    nli0 = nli
    nli_list = [nli]
    for i in range(10):
        _nli = output_nonlinear_noise(nli, signal_to_power, signals, spanx)
        nli = _nli
        nli_list.append(nli)
    ordered_indices = order_signals(nli)

    ord_nli_list = []
    for _l in nli_list:
        nn = [_l[i] * amp_compensation for i in ordered_indices]
        ord_nli_list.append(nn)
    # plot_list_osnr_sf([new_nli])
    plot_list_osnr_sf(ord_nli_list)

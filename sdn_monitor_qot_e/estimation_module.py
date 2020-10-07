import numpy as np
import scipy.constants as sc
import math
import json
import os
import subprocess


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


def estimation_module(load, load_id, test_id, signal_ids=None):
    keys, s_p, s_a, s_n = build_struct(load, signal_ids=signal_ids)
    estimation_osnr_log = []
    estimation_gosnr_log = []
    roadms = 15
    spans = 6
    for roadm in range(roadms - 1):
        # process roadm attenuation
        s_p, s_a, s_n = process_roadm(keys, s_p, s_a, s_n)
        s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=True)
        estimation_osnr_log.append(osnr(keys, s_p, s_a))
        estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
        for span in range(spans):
            # process span attenuation
            s_p, s_a, s_n = process_span(keys, s_p, s_a, s_n)
            s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=False)
            estimation_osnr_log.append(osnr(keys, s_p, s_a))
            estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
    write_files(estimation_osnr_log, estimation_gosnr_log, test_id, load_id)
    return estimation_osnr_log, estimation_gosnr_log


def estimation_module_dyn(main_struct, m):
    keys, s_p, s_a, s_n = main_struct
    estimation_osnr_log = []
    estimation_gosnr_log = []
    roadms = m
    spans = 6
    for roadm in range(roadms):
        # process roadm attenuation
        s_p, s_a, s_n = process_roadm(keys, s_p, s_a, s_n)
        s_p, s_a, s_n = leveling(keys, s_p, s_a, s_n)
        s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=True)
        estimation_osnr_log.append(osnr(keys, s_p, s_a))
        estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
        for span in range(spans):
            # process span attenuation
            s_p, s_a, s_n = process_span(keys, s_p, s_a, s_n)
            s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=False)
            estimation_osnr_log.append(osnr(keys, s_p, s_a))
            estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
    return estimation_osnr_log, estimation_gosnr_log


def estimation_module_approx(main_struct, m):
    keys, s_p, s_a, s_n = main_struct
    estimation_osnr_log = []
    estimation_gosnr_log = []
    roadms = m
    spans = 6
    for roadm in range(roadms):
        # process roadm attenuation
        s_p, s_a, s_n = process_roadm(keys, s_p, s_a, s_n)
        s_p, s_a, s_n = leveling(keys, s_p, s_a, s_n)
        s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=True)
        estimation_osnr_log.append(osnr(keys, s_p, s_a))
        estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
        for span in range(spans):
            # process span attenuation
            s_p, s_a, s_n = process_span(keys, s_p, s_a, s_n)
            s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=False)
            estimation_osnr_log.append(osnr(keys, s_p, s_a))
            estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
    return estimation_osnr_log, estimation_gosnr_log, s_p, s_a, s_n


def estimation_module_simpledemo(main_struct, spans, link_dir, last=True):
    keys, s_p, s_a, s_n = main_struct
    estimation_osnr_log = []
    estimation_gosnr_log = []
    estimation_power_log = []
    estimation_ase_log = []
    estimation_nli_log = []

    # process roadm attenuation
    s_p, s_a, s_n = process_roadm(keys, s_p, s_a, s_n)
    s_p, s_a, s_n = leveling(keys, s_p, s_a, s_n)
    s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=True)
    estimation_osnr_log.append(osnr(keys, s_p, s_a))
    estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
    estimation_power_log.append(s_p)
    estimation_ase_log.append(s_a)
    estimation_nli_log.append(s_n)
    for span in spans:
        # process span attenuation
        s_p, s_a, s_n = process_span_dyn(keys, s_p, s_a, s_n, span)
        s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=False)
        estimation_osnr_log.append(osnr(keys, s_p, s_a))
        estimation_gosnr_log.append(gosnr(keys, s_p, s_a, s_n))
        estimation_power_log.append(s_p)
        estimation_ase_log.append(s_a)
        estimation_nli_log.append(s_n)
    write_files_simpledemo(estimation_osnr_log, estimation_gosnr_log, estimation_power_log,
                           estimation_ase_log, estimation_nli_log, link_dir)

    if last:
        return estimation_osnr_log, estimation_gosnr_log
    else:
        return keys, s_p, s_a, s_n


def estimation_module_simpledemo_correct(main_struct, span, first=False):
    keys, s_p, s_a, s_n = main_struct
    if first:
        # process roadm attenuation
        s_p, s_a, s_n = process_roadm(keys, s_p, s_a, s_n)
        s_p, s_a, s_n = leveling(keys, s_p, s_a, s_n)
        s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=True)
        _osnr = osnr(keys, s_p, s_a)
        _gosnr = gosnr(keys, s_p, s_a, s_n)
        return _osnr, _gosnr, s_p, s_a, s_n
    # process span attenuation
    s_p, s_a, s_n = process_span_dyn(keys, s_p, s_a, s_n, span)
    s_p, s_a, s_n = process_amp(keys, s_p, s_a, s_n, boost=False)
    _osnr = osnr(keys, s_p, s_a)
    _gosnr = gosnr(keys, s_p, s_a, s_n)
    return _osnr, _gosnr, s_p, s_a, s_n


def build_struct(load, signal_ids=None):
    s_p, s_a, s_n = {}, {}, {}
    if signal_ids:
        keys = signal_ids
    else:
        keys = range(1, load + 1)
    for key in keys:
        s_p[key] = db_to_abs(0)
        s_a[key] = db_to_abs(0) / db_to_abs(50)
        s_n[key] = db_to_abs(0) / db_to_abs(50)
    return keys, s_p, s_a, s_n


def osnr(keys, s_p, s_a):
    osnrs = {}
    for ch in keys:
        osnr = s_p[ch] / s_a[ch]
        osnrs[ch] = abs_to_db(osnr)
    return osnrs


def gosnr(keys, s_p, s_a, s_n):
    gosnrs = {}
    for ch in keys:
        gosnr = s_p[ch] / (s_a[ch] + s_n[ch] * (12.5e9/32.0e9))
        gosnrs[ch] = abs_to_db(gosnr)
    return gosnrs


def process_roadm(keys, s_p, s_a, s_n):
    attenuation = db_to_abs(17.0)
    for ch in keys:
        s_p[ch] /= attenuation
        s_a[ch] /= attenuation
        s_n[ch] /= attenuation
    return s_p, s_a, s_n


def leveling(keys, s_p, s_a, s_n):
    op = db_to_abs(-17.0)
    delta = {}
    for ch in keys:
        delta[ch] = op / s_p[ch]
    for ch in keys:
        s_p[ch] *= delta[ch]
        s_a[ch] *= delta[ch]
        s_n[ch] *= delta[ch]
    return s_p, s_a, s_n


def process_amp(keys, s_p, s_a, s_n, boost=False):
    boost_gain = db_to_abs(17.0)
    amp_gain = db_to_abs(11)
    for ch in keys:
        if boost:
            gain = boost_gain
        else:
            gain = amp_gain
        s_p[ch] *= gain

        s_a[ch] = stage_amplified_spontaneous_emission_noise(ch, s_a[ch], gain)

        s_n[ch] *= gain

    return s_p, s_a, s_n


def process_span(keys, s_p, s_a, s_n):
    attenuation = db_to_abs(80 * 0.22)

    s_n = nonlinear_noise(s_n, s_p, keys)

    # s_p, s_a, s_n = zirngibl_srs(keys, s_p, s_a, s_n)

    for ch in keys:
        s_p[ch] /= attenuation
        s_a[ch] /= attenuation
        s_n[ch] /= attenuation

    return s_p, s_a, s_n


def process_span_dyn(keys, s_p, s_a, s_n, _len):
    attenuation = db_to_abs(_len * 0.22)

    s_n = nonlinear_noise(s_n, s_p, keys)

    # s_p, s_a, s_n = zirngibl_srs(keys, s_p, s_a, s_n)

    for ch in keys:
        s_p[ch] /= attenuation
        s_a[ch] /= attenuation
        s_n[ch] /= attenuation

    return s_p, s_a, s_n

  
def stage_amplified_spontaneous_emission_noise(index, ase_noise_acc,
                                               system_gain):
    """
    :return:
    Ch.5 Eqs. 4-16,18 in: Gumaste A, Antony T. DWDM network designs and engineering solutions. Cisco Press; 2003.
    """

    # Set parameters needed for ASE model
    noise_figure_linear = db_to_abs(5.5)
    bandwidth = 12.5e9
    channel_spacing_H = 50e9
    frequency = 191.3e12 + (channel_spacing_H * index)

    # Conversion from dB to linear
    ase_noise = ase_noise_acc * system_gain + (noise_figure_linear * sc.h *
                                               frequency * bandwidth * (system_gain - 1) * 1000)
    return ase_noise


def nonlinear_noise(s_n, s_p, keys):
    new_nli = gn_model(s_p, keys)
    for ch in keys:
        s_n[ch] += new_nli[ch]
    return s_n


def gn_model(s_p, keys):
    """ Computes the nonlinear interference power on a single carrier.
    Translated from the GNPy project source code
    The method uses eq. 120 from arXiv:1209.0394.
    """

    nonlinear_noise_struct = {}
    for channel in keys:
        nonlinear_noise_struct[channel] = None

    length = 80.0 * 1.0e3
    fibre_attenuation = 0.22 / 1.0e3
    alpha = fibre_attenuation / (20 * np.log10(np.e))  # linear value fibre attenuation
    beta2 = get_beta2()
    gamma = 0.78 / 1.0e3  # gamma fiber non-linearity coefficient [W^-1 km^-1]
    effective_length = (1 - np.exp(-2 * alpha * length)) / (2 * alpha)
    asymptotic_length = 1 / (2 * alpha)

    for optical_signal in keys:
        symbol_rate_cut = 32e9
        bw_cut = symbol_rate_cut
        pwr_cut = round(s_p[optical_signal], 2) * 1e-3
        g_cut = pwr_cut / bw_cut  # G is the flat PSD per channel power (per polarization)

        g_nli = 0
        for ch in keys:
            bw_ch = 32e9
            pwr_ch = round(s_p[ch], 2) * 1e-3
            g_ch = pwr_ch / bw_ch  # G is the flat PSD per channel power (per polarization)
            psi = psi_factor(optical_signal, ch, beta2=beta2, asymptotic_length=asymptotic_length)
            g_nli += g_ch ** 2 * g_cut * psi

        g_nli *= (16.0 / 27.0) * (gamma * effective_length) ** 2 \
                 / (2 * np.pi * abs(beta2) * asymptotic_length)
        nonlinear_noise_struct[optical_signal] = g_nli * bw_cut * 1e3
    return nonlinear_noise_struct


def get_beta2():
    """Returns beta2 from dispersion parameter.
    Dispersion is entered in ps/nm/km.
    Translated from the GNPy project source code
    :param ref_wavelength: can be a numpy array; default: 1550nm
    """
    ref_wavelength = 1550e-9
    D = abs(2.1e-05)
    b2 = (ref_wavelength ** 2) * D / (2 * math.pi * 299792458.0)  # 10^21 scales [ps^2/km]
    return b2  # s/Hz/m


def psi_factor(carrier, interfering_carrier, beta2, asymptotic_length):
    """Calculates eq. 123 from `arXiv:1209.0394 <https://arxiv.org/abs/1209.0394>`__
    Translated from the GNPy project source code
    """
    bw_cut = 32e9
    bw_ch = 32e9

    if carrier == interfering_carrier:  # SCI, SPM
        psi = np.arcsinh(0.5 * math.pi ** 2 * asymptotic_length * abs(beta2) * bw_cut ** 2)
    else:  # XCI, XPM
        carrier_f = 191.3e12 + (50e9 * carrier)
        interfering_carrier_f = 191.3e12 + (50e9 * interfering_carrier)
        delta_f = carrier_f - interfering_carrier_f
        psi = np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                         bw_cut * (delta_f + 0.5 * bw_ch))
        psi -= np.arcsinh(np.pi ** 2 * asymptotic_length * abs(beta2) *
                          bw_cut * (delta_f - 0.5 * bw_ch))
    return psi


def zirngibl_srs(keys, s_p, s_a, s_n):
    """
    Computation taken from : M. Zirngibl Analytical model of Raman gain effects in massive
    wavelength division multiplexed transmission systems, 1998. - Equations 7,8.
    """
    min_signal = min(keys)
    max_signal = max(keys)
    channel_spacing_H = 50e9
    frequency_min = 191.3e12 + (channel_spacing_H * min_signal)  # minimum frequency of longest wavelength
    frequency_max = 191.3e12 + (channel_spacing_H * max_signal)  # maximum frequency of shortest wavelength

    length = 80 * 1e3
    fibre_attenuation = 0.22 / 1e3
    alpha = fibre_attenuation / (20 * np.log10(np.e))  # linear value fibre attenuation
    effective_length = (1 - np.exp(-2 * alpha * length)) / (2 * alpha)
    effective_area = 80 * 1.0e-6 * 1.0e-6  # Aeff - SMF effective area
    raman_gain = 7.0 * 1e-12 * 1.0e-2 / 1.0  # r - Raman Gain in SMF
    raman_amplification_band = 15 * 1.0e12  # Raman amplification band ~15THz
    # Raman coefficient
    raman_coefficient = raman_gain / (2 * effective_area * raman_amplification_band)
    beta = raman_coefficient

    total_power = 0  # Total input power calculated by following loop
    for ch in keys:
        total_power += s_p[ch] * 1.0e-3

    # Calculate delta P for each channel
    for optical_signal in keys:
        frequency = 191.3e12 + (channel_spacing_H * optical_signal)
        r1 = beta * total_power * effective_length * (frequency_max - frequency_min) * math.e ** (
                beta * total_power * effective_length * (frequency - frequency_min))  # term 1
        r2 = math.e ** (beta * total_power * effective_length * (frequency_max - frequency_min)) - 1  # term 2

        delta_p = float(r1 / r2)  # Does the arithmetic in mW
        s_p[optical_signal] *= delta_p
        s_a[optical_signal] *= delta_p
        s_n[optical_signal] *= delta_p

    return s_p, s_a, s_n


def write_files(estimation_osnr_log, estimation_gosnr_log, test_id, load_id):
    """
    Write a file with osnr and gosnr information from a given OPM node
    """
    monitor_keys = [
        'r1-r2-boost-monitor', 'r1-r2-amp1-monitor', 'r1-r2-amp2-monitor', 'r1-r2-amp3-monitor', 'r1-r2-amp4-monitor',
        'r1-r2-amp5-monitor', 'r1-r2-amp6-monitor', 'r2-r3-boost-monitor', 'r2-r3-amp1-monitor', 'r2-r3-amp2-monitor',
        'r2-r3-amp3-monitor', 'r2-r3-amp4-monitor', 'r2-r3-amp5-monitor', 'r2-r3-amp6-monitor', 'r3-r4-boost-monitor',
        'r3-r4-amp1-monitor', 'r3-r4-amp2-monitor', 'r3-r4-amp3-monitor', 'r3-r4-amp4-monitor', 'r3-r4-amp5-monitor',
        'r3-r4-amp6-monitor', 'r4-r5-boost-monitor', 'r4-r5-amp1-monitor', 'r4-r5-amp2-monitor', 'r4-r5-amp3-monitor',
        'r4-r5-amp4-monitor', 'r4-r5-amp5-monitor', 'r4-r5-amp6-monitor', 'r5-r6-boost-monitor', 'r5-r6-amp1-monitor',
        'r5-r6-amp2-monitor', 'r5-r6-amp3-monitor', 'r5-r6-amp4-monitor', 'r5-r6-amp5-monitor', 'r5-r6-amp6-monitor',
        'r6-r7-boost-monitor', 'r6-r7-amp1-monitor', 'r6-r7-amp2-monitor', 'r6-r7-amp3-monitor', 'r6-r7-amp4-monitor',
        'r6-r7-amp5-monitor', 'r6-r7-amp6-monitor', 'r7-r8-boost-monitor', 'r7-r8-amp1-monitor', 'r7-r8-amp2-monitor',
        'r7-r8-amp3-monitor', 'r7-r8-amp4-monitor', 'r7-r8-amp5-monitor', 'r7-r8-amp6-monitor', 'r8-r9-boost-monitor',
        'r8-r9-amp1-monitor', 'r8-r9-amp2-monitor', 'r8-r9-amp3-monitor', 'r8-r9-amp4-monitor', 'r8-r9-amp5-monitor',
        'r8-r9-amp6-monitor', 'r9-r10-boost-monitor', 'r9-r10-amp1-monitor', 'r9-r10-amp2-monitor', 'r9-r10-amp3-monitor',
        'r9-r10-amp4-monitor', 'r9-r10-amp5-monitor', 'r9-r10-amp6-monitor', 'r10-r11-boost-monitor', 'r10-r11-amp1-monitor',
        'r10-r11-amp2-monitor', 'r10-r11-amp3-monitor', 'r10-r11-amp4-monitor', 'r10-r11-amp5-monitor',
        'r10-r11-amp6-monitor', 'r11-r12-boost-monitor', 'r11-r12-amp1-monitor', 'r11-r12-amp2-monitor',
        'r11-r12-amp3-monitor', 'r11-r12-amp4-monitor', 'r11-r12-amp5-monitor', 'r11-r12-amp6-monitor',
        'r12-r13-boost-monitor', 'r12-r13-amp1-monitor', 'r12-r13-amp2-monitor', 'r12-r13-amp3-monitor',
        'r12-r13-amp4-monitor', 'r12-r13-amp5-monitor', 'r12-r13-amp6-monitor', 'r13-r14-boost-monitor',
        'r13-r14-amp1-monitor', 'r13-r14-amp2-monitor', 'r13-r14-amp3-monitor', 'r13-r14-amp4-monitor',
        'r13-r14-amp5-monitor', 'r13-r14-amp6-monitor', 'r14-r15-boost-monitor', 'r14-r15-amp1-monitor',
        'r14-r15-amp2-monitor', 'r14-r15-amp3-monitor', 'r14-r15-amp4-monitor', 'r14-r15-amp5-monitor',
        'r14-r15-amp6-monitor'
    ]

    _osnr_id = 'osnr_load_' + load_id
    _gosnr_id = 'gosnr_load_' + load_id

    test = 'metrics-monitor/'

    for index, monitor_key in enumerate(monitor_keys):
        json_struct = {'tests': []}
        json_struct['tests'].append({_osnr_id: estimation_osnr_log[index]})
        json_struct['tests'].append({_gosnr_id: estimation_gosnr_log[index]})
        dir_ = test + 'estimation-module/' + monitor_key

        if not os.path.exists(dir_):
            os.makedirs(dir_)
        json_file_name = dir_ + '/' + test_id + '_' + str(load_id) + '.json'
        with open(json_file_name, 'w+') as outfile:
            json.dump(json_struct, outfile)
        # process_file(json_file_name, monitor_key)


def write_files_simpledemo(estimation_osnr_log, estimation_gosnr_log, s_p, s_a, s_n, link_dir):
    monitors = None
    if link_dir == 'r_london-r_copenhagen/':
        # build the monitors list
        monitors = ['r_london-r_copenhagen-amp%s' % str(i) for i in range(1, 21)]
        # insert booster monitor at the beginning
        monitors.insert(0, 'r_london-r_copenhagen-boost')
    elif link_dir == 'r_copenhagen-r_berlin/':
        monitors = ['r_copenhagen-r_berlin-amp%s' % str(i) for i in range(1, 9)]
        monitors.insert(0, 'r_copenhagen-r_berlin-boost')
    elif link_dir == 'r_paris-r_berlin/':
        monitors = ['r_paris-r_berlin-amp%s' % str(i) for i in range(1, 19)]
        monitors.insert(0, 'r_paris-r_berlin-boost')
    elif link_dir == 'r_prague-r_vienna/':
        monitors = ['r_prague-r_vienna-amp%s' % str(i) for i in range(1, 8)]
        monitors.insert(0, 'r_prague-r_vienna-boost')

    _osnr_id = 'osnr'
    _gosnr_id = 'gosnr'
    _power_id = 'power'
    _ase_id = 'ase'
    _nli_id = 'nli'

    for index, monitor_key in enumerate(monitors):
        json_struct = {'tests': []}
        json_struct['tests'].append({_osnr_id: estimation_osnr_log[index]})
        json_struct['tests'].append({_gosnr_id: estimation_gosnr_log[index]})
        json_struct['tests'].append({_power_id: s_p[index]})
        json_struct['tests'].append({_ase_id: s_a[index]})
        json_struct['tests'].append({_nli_id: s_n[index]})

        dir_ = 'cost239-monitor/estimation-module-new/' + link_dir + monitor_key

        if not os.path.exists(dir_):
            os.makedirs(dir_)
        json_file_name = dir_ + '/log_data.json'
        with open(json_file_name, 'w+') as outfile:
            json.dump(json_struct, outfile)


def process_file(outfile, monitor_key):
    """
    To avoid memory exhaustion in VM, transfer recently created
    file to a remote location (flash drive) and remove them
    from local (VM).
    """
    # send file to flash drive
    # print("processing file: ", outfile)
    dest_file = '../tmp/'
    cmd1 = ['rsync', '-r', outfile, dest_file]
    # delete file
    cmd2 = ['rm', outfile]
    subprocess.call(cmd1)
    subprocess.call(cmd2)

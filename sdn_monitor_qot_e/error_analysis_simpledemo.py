import json
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager
from sdn_monitor_qot_e.correction_procedure import *


def compute_errors(y, z):
    _errors = []
    keys = z.keys()
    print("uno", y)
    print("dos", z)
    for k in keys:
        e = abs(y[k] - z[k])
        _errors.append(e)
    return max(_errors)


def get_sorted_files(unsorted_files):
    sorted_files = sorted(unsorted_files)
    new_files = [sorted_files[-1]]
    for x in sorted_files[:-1]:
        new_files.append(x)
    return new_files


def get_monitors(link_dir):
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
    return monitors


def build_mon_est(links_dir):
    _dict = {'r_london-r_copenhagen': {}, 'r_copenhagen-r_berlin': {},
             'r_paris-r_berlin': {}, 'r_prague-r_vienna': {}}

    for link_dir in links_dir:
        monitors = get_monitors(link_dir)
        key = link_dir[:-1]
        for monitor in monitors:
            _dict[key][monitor] = {}

    return _dict


def build_mon_corr(links_dir):
    # _dict = {10: {}, 30: {}, 60: {}}
    _dict = {10: {}, 20: {}, 30: {}, 40: {}, 50: {}, 60: {}, 70: {}, 80: {}}
    densities = _dict.keys()
    for key in densities:
        new_dict = {'r_london-r_copenhagen': {}, 'r_copenhagen-r_berlin': {},
                    'r_paris-r_berlin': {}, 'r_prague-r_vienna': {}}
        _dict[key] = new_dict
    for link_dir in links_dir:
        monitors = get_monitors(link_dir)
        link_key = link_dir[:-1]
        for density in densities:
            _dict[density][link_key] = {}
            for monitor in monitors:
                _dict[density][link_key][monitor] = {}
    return _dict


def get_monitor_deploy(link_key, density=10, first_last='first'):
    """
    net: network object
    density: density percentage (10 = 10%, 30 = 30%, etc)
    first_last: when 1 OPM is to be used, decide whether using
    the first one (boost-monitor) or last one (pre-amp-monitor) in the link
    """
    if link_key == 'r_london-r_copenhagen':
        # build the monitors list
        mon_ldn_cph = ['r_london-r_copenhagen-amp%s' % str(i) for i in range(1, 21)]
        # insert booster monitor at the beginning
        mon_ldn_cph.insert(0, 'r_london-r_copenhagen-boost')
        # consider only the number of monitors given by the density %
        mon_ldn_cph = monitor_deployment(mon_ldn_cph, density=density, first_last=first_last)
        return mon_ldn_cph

    elif link_key == 'r_copenhagen-r_berlin':
        mon_cph_ber = ['r_copenhagen-r_berlin-amp%s' % str(i) for i in range(1, 9)]
        mon_cph_ber.insert(0, 'r_copenhagen-r_berlin-boost')
        mon_cph_ber = monitor_deployment(mon_cph_ber, density=density, first_last=first_last)
        return mon_cph_ber

    elif link_key == 'r_paris-r_berlin':
        mon_par_ber = ['r_paris-r_berlin-amp%s' % str(i) for i in range(1, 19)]
        mon_par_ber.insert(0, 'r_paris-r_berlin-boost')
        mon_par_ber = monitor_deployment(mon_par_ber, density=density, first_last=first_last)
        return mon_par_ber

    elif link_key == 'r_prague-r_vienna':
        mon_pra_vie = ['r_prague-r_vienna-amp%s' % str(i) for i in range(1, 8)]
        mon_pra_vie.insert(0, 'r_prague-r_vienna-boost')
        mon_pra_vie = monitor_deployment(mon_pra_vie, density=density, first_last=first_last)
        return mon_pra_vie


def monitor_deployment(monitor_link, density=10, first_last='first'):
    # if using 100% OPM density
    # if density == 100:
    #     return monitor_link

    # compute number of OPMs given the density
    monitor_no = int(len(monitor_link) * density*1e-2)
    # list with the monitors to be used
    monitors = []

    if monitor_no <= 1:
        # if monitor_no is 0 or 1, use either the
        # first one (boost) or last one (pre-amp)
        if first_last == 'first':
            monitors.append(monitor_link[0])
        else:
            monitors.append(monitor_link[-1])
    else:
        # if monitor_no >= 2, select monitors in an even manner
        monitors = monitor_select(monitor_link, monitor_no)
    return monitors


def monitor_select(monitor_link, monitor_no):
    n = len(monitor_link)
    # select indices from even_select algorithm
    indices = even_select(n, monitor_no)
    monitors = []
    for i, k in enumerate(indices):
        if k == 0:
            monitors.append(monitor_link[i])
    return monitors


def even_select(n, m):
    """
    n: number of OPMs in link
    m: number of OPMs required
    return: list [0,1] with location of OPMs
    to be considered (0) and ignored (1) as per
    their location in the link
    """
    if m > n/2:
        cut = np.zeros(n, dtype=int)
        q, r = divmod(n, n-m)
        indices = [q*i + min(i, r) for i in range(n-m)]
        cut[indices] = True
    else:
        cut = np.ones(n, dtype=int)
        q, r = divmod(n, m)
        indices = [q*i + min(i, r) for i in range(m)]
        cut[indices] = False
    return cut


def get_opm_struct(link_dir, monitors):
    # locations of the json files
    _opm_path = 'cost239-monitor/monitor-module-new/' + link_dir

    osnr_opm_dict = dict.fromkeys(monitors)
    gosnr_opm_dict = dict.fromkeys(monitors)

    files = os.listdir(_opm_path)

    for filename in files:
        if filename.endswith(".json"):
            file_path = _opm_path + filename
            monitor_name = filename.split('.')[0]

            osnr_label = 'osnr'
            gosnr_label = 'gosnr'

            with open(file_path) as json_file:
                f = json.load(json_file)
            json_items = list(f.items())
            metric_items = json_items[0][1]
            osnr_dict = metric_items[0]
            gosnr_dict = metric_items[1]

            osnr_opm = osnr_dict[osnr_label]
            gosnr_opm = gosnr_dict[gosnr_label]
            # record gosnr estimation per load
            osnr_opm_dict[monitor_name] = osnr_opm
            gosnr_opm_dict[monitor_name] = gosnr_opm

    return osnr_opm_dict, gosnr_opm_dict


def plot_error_to_density(l_id, e_o, e_c):
    """
    Function to plot the max error vs. the density
    l_id: Link ID (i.e., r_london-r_copenhagen)
    e_o: Error_Orig dict
    e_c: Error_Corr dict
    """
    ds = np.arange(10, 90, 10)
    max_eo = []
    max_ec = []
    for d in ds:
        max_eo.append(e_o[l_id][d][-1])
        max_ec.append(e_c[l_id][d][-1])

    plt.plot(ds, max_ec, 'darkblue', label='pra-vie-err-correction')
    plt.plot(ds, max_eo, 'r', label='pra-vie-err-original')
    plt.legend()
    plt.xlabel('OPM density [%]')
    plt.ylabel('QoT-E max error [dB]')
    # plt.show()
    fig_name = '/Users/adiaz/Documents/Trinity-College/Research/OFC2021/images/tests/pra_vie_e2d_end.png'
    plt.savefig(fig_name, format='png', bbox_inches='tight', pad_inches=0)


# dummy boolean
tmp_bool = True
if tmp_bool:

    root_dir = 'cost239-monitor/estimation-module-new/'
    links_dir = ['r_london-r_copenhagen/', 'r_copenhagen-r_berlin/', 'r_paris-r_berlin/', 'r_prague-r_vienna/']
    densities_dir = ['density_10/', 'density_30/', 'density_60/']

    mon_est = build_mon_est(links_dir)

    for link_dir in links_dir:
        link_key = link_dir[:-1]
        monitors = get_monitors(link_dir)
        for monitor in monitors:
            current_path = root_dir + link_dir + monitor + '/'
            files = get_sorted_files(os.listdir(current_path))
            print("Looking at: ", current_path)
            for filename in files:
                if filename.endswith(".json"):
                    file_path = current_path + '/' + filename

                    # process file
                    with open(file_path) as json_file:
                        f = json.load(json_file)
                    json_items = list(f.items())
                    metric_items = json_items[0][1]
                    osnr_dict = metric_items[0]
                    gosnr_dict = metric_items[1]

                    osnr = osnr_dict['osnr']
                    gosnr = gosnr_dict['gosnr']

                    mon_est[link_key][monitor]['osnr'] = osnr
                    mon_est[link_key][monitor]['gosnr'] = gosnr

    link_keys = [('r_london-r_copenhagen', 'r_copenhagen-r_berlin'), 'r_paris-r_berlin', 'r_prague-r_vienna']
    # channels_list = [range(1, 16), range(16, 31), range(31, 46)]
    channels_list = [range(1, 16), range(16, 31), range(75, 91)]
    mon_corr = build_mon_corr(links_dir)
    # densities = [10, 30, 60]
    densities = [10, 20, 30, 40, 50, 60, 70, 80]
    for density in densities:
        for link_key, channels in zip(link_keys, channels_list):
            main_struct = build_struct(15, signal_ids=channels)
            if type(link_key) is tuple:
                for i, e in enumerate(link_key, start=1):
                    link_dir = e + '/'
                    monitors = get_monitors(link_dir)
                    monitors_by_density = get_monitor_deploy(e, density=density)
                    if i == len(link_key):
                        _, mon_corr[density][e] = get_corrected_struct_simpledemo(e, monitors, monitors_by_density,
                                                                                  main_struct=main_struct)
                    else:
                        main_struct, mon_corr[density][e] = get_corrected_struct_simpledemo(e, monitors,
                                                                                            monitors_by_density,
                                                                                            main_struct=main_struct)
            else:
                link_dir = link_key + '/'
                monitors = get_monitors(link_dir)
                monitors_by_density = get_monitor_deploy(link_key, density=density)
                _, mon_corr[density][link_key] = get_corrected_struct_simpledemo(link_key, monitors,
                                                                                 monitors_by_density,
                                                                                 main_struct=main_struct)

    error_link_orig = {}
    error_link_corr = {}

    for link_dir in links_dir:
        # errors_orig = {10: [], 30: [], 60: []}
        errors_orig = {10: [], 20: [], 30: [], 40: [], 50: [], 60: [], 70: [], 80: []}
        # errors_corr = {10: [], 30: [], 60: []}
        errors_corr = {10: [], 20: [], 30: [], 40: [], 50: [], 60: [], 70: [], 80: []}
        link_key = link_dir[:-1]
        monitors = get_monitors(link_dir)
        osnr_opm_dict, gosnr_opm_dict = get_opm_struct(link_dir, monitors)
        for density in densities:
            for monitor in monitors:
                gosnr_opm = gosnr_opm_dict[monitor]
                gosnr_est = mon_est[link_key][monitor]['gosnr']
                gosnr_corr = mon_corr[density][link_key][monitor]
                # Compute errors for the above
                error = compute_errors(gosnr_opm, gosnr_est)

                errors_orig[density].append(error)

                # Compute errors for OPM and QoT-E corrected
                error_c = compute_errors(gosnr_opm, gosnr_corr)
                errors_corr[density].append(error_c)

        error_link_orig[link_key] = errors_orig
        error_link_corr[link_key] = errors_corr

    # plot_error_to_density('r_prague-r_vienna', error_link_orig, error_link_corr)

    # ['r_london-r_copenhagen/', 'r_copenhagen-r_berlin/', 'r_paris-r_berlin/', 'r_prague-r_vienna/']
    links_dir = ['r_london-r_copenhagen/']
    for link_dir in links_dir:
        link_key = link_dir[:-1]

        error_orig = error_link_orig[link_key]
        error_corr = error_link_corr[link_key]

        colors = ['c', 'm', 'y', 'k', 'g', 'darkblue', 'r', 'lightblue']
        markers = ['1', '2', '3', '.', 'h', 'D', 'v', '^']
        bl = True
        for density in densities:
            eo = error_orig[density]
            ec = error_corr[density]

            if bl:
                bl = False
                label_eo = 'original error-' + link_key
                plt.plot(eo, color='g', label=label_eo)

            label_ec = 'c-' + link_key + '-' + str(density)
            plt.plot(ec, color=colors.pop(), label=label_ec, marker=markers.pop())

    plt.legend()
    plt.xlabel('Monitoring locations')
    plt.ylabel('QoT-E max error [dB]')

    fig_name = '/Users/adiaz/Documents/Trinity-College/Research/OFC2021/images/tests/ldn_cph_algo2t.png'
    # plt.savefig(fig_name, format='png', bbox_inches='tight', pad_inches=0)
    plt.show()

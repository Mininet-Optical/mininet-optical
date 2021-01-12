import json
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import figure
import matplotlib.font_manager
import statistics
from sdn_monitor_qot_e.correction_procedure import *


def compute_errors(y, z):
    _errors = []
    keys = z.keys()

    #print("uno", y)
    #print("dos", z)
    for k in keys:
        e = abs(y[k] - z[k])
        _errors.append(e)

    _errors.sort()
    #return (statistics.median(_errors))
    return max(_errors)


def get_sorted_files(unsorted_files):
    sorted_files = sorted(unsorted_files)
    new_files = [sorted_files[-1]]
    for x in sorted_files[:-1]:
        new_files.append(x)
    return new_files


def get_monitors(link_dir):
    dist_dict = {('amsterdam', 'london'): 390, ('london', 'amsterdam'): 390, ('amsterdam', 'brussels'): 200,
                 ('brussels', 'amsterdam'): 200, ('amsterdam', 'luxembourg'): 310, ('luxembourg', 'amsterdam'): 310,
                 ('amsterdam', 'berlin'): 600, ('berlin', 'amsterdam'): 600, ('amsterdam', 'copenhagen'): 750,
                 ('copenhagen', 'amsterdam'): 750, ('berlin', 'copenhagen'): 400, ('copenhagen', 'berlin'): 400,
                 ('berlin', 'paris'): 900, ('paris', 'berlin'): 900, ('berlin', 'prague'): 320,
                 ('prague', 'berlin'): 320,
                 ('berlin', 'vienna'): 710, ('vienna', 'berlin'): 710, ('brussels', 'london'): 340,
                 ('london', 'brussels'): 340,
                 ('brussels', 'paris'): 270, ('paris', 'brussels'): 270, ('brussels', 'milan'): 850,
                 ('milan', 'brussels'): 850,
                 ('brussels', 'luxembourg'): 100, ('luxembourg', 'brussels'): 100, ('copenhagen', 'london'): 1000,
                 ('london', 'copenhagen'): 1000, ('copenhagen', 'prague'): 760, ('prague', 'copenhagen'): 760,
                 ('london', 'paris'): 410, ('paris', 'london'): 410, ('luxembourg', 'paris'): 370,
                 ('paris', 'luxembourg'): 370,
                 ('luxembourg', 'zurich'): 440, ('zurich', 'luxembourg'): 440, ('luxembourg', 'prague'): 900,
                 ('prague', 'luxembourg'): 900, ('milan', 'paris'): 810, ('paris', 'milan'): 810,
                 ('milan', 'zurich'): 100,
                 ('zurich', 'milan'): 100, ('milan', 'vienna'): 720, ('vienna', 'milan'): 720, ('paris', 'zurich'): 590,
                 ('zurich', 'paris'): 590, ('prague', 'zurich'): 100, ('zurich', 'prague'): 100,
                 ('prague', 'vienna'): 350,
                 ('vienna', 'prague'): 350, ('vienna', 'zurich'): 710, ('zurich', 'vienna'): 710}
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
    else:
        step = 50
        stripped_name = link_dir.strip('/')
        node_list = stripped_name.split('-')
        node_list = [node_list[i].strip('r_') for i in range(0, len(node_list))]
        no_monitors = round(dist_dict[(node_list[0], node_list[1])] / step)
        monitors = [stripped_name + '-amp' + str(i)  for i in
                    range(1, no_monitors + 1)]
        monitors.insert(0, stripped_name + '-boost')
        return monitors
    return monitors


def build_mon_est(links_dir):
    _dict =  {'r_london-r_copenhagen': {}, 'r_copenhagen-r_berlin': {}, 'r_paris-r_berlin': {},
                  'r_prague-r_vienna': {}}

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
    dist_dict = {('amsterdam', 'london'): 390, ('london', 'amsterdam'): 390, ('amsterdam', 'brussels'): 200,
                 ('brussels', 'amsterdam'): 200, ('amsterdam', 'luxembourg'): 310, ('luxembourg', 'amsterdam'): 310,
                 ('amsterdam', 'berlin'): 600, ('berlin', 'amsterdam'): 600, ('amsterdam', 'copenhagen'): 750,
                 ('copenhagen', 'amsterdam'): 750, ('berlin', 'copenhagen'): 400, ('copenhagen', 'berlin'): 400,
                 ('berlin', 'paris'): 900, ('paris', 'berlin'): 900, ('berlin', 'prague'): 320,
                 ('prague', 'berlin'): 320,
                 ('berlin', 'vienna'): 710, ('vienna', 'berlin'): 710, ('brussels', 'london'): 340,
                 ('london', 'brussels'): 340,
                 ('brussels', 'paris'): 270, ('paris', 'brussels'): 270, ('brussels', 'milan'): 850,
                 ('milan', 'brussels'): 850,
                 ('brussels', 'luxembourg'): 100, ('luxembourg', 'brussels'): 100, ('copenhagen', 'london'): 1000,
                 ('london', 'copenhagen'): 1000, ('copenhagen', 'prague'): 760, ('prague', 'copenhagen'): 760,
                 ('london', 'paris'): 410, ('paris', 'london'): 410, ('luxembourg', 'paris'): 370,
                 ('paris', 'luxembourg'): 370,
                 ('luxembourg', 'zurich'): 440, ('zurich', 'luxembourg'): 440, ('luxembourg', 'prague'): 900,
                 ('prague', 'luxembourg'): 900, ('milan', 'paris'): 810, ('paris', 'milan'): 810,
                 ('milan', 'zurich'): 100,
                 ('zurich', 'milan'): 100, ('milan', 'vienna'): 720, ('vienna', 'milan'): 720, ('paris', 'zurich'): 590,
                 ('zurich', 'paris'): 590, ('prague', 'zurich'): 100, ('zurich', 'prague'): 100,
                 ('prague', 'vienna'): 350,
                 ('vienna', 'prague'): 350, ('vienna', 'zurich'): 710, ('zurich', 'vienna'): 710}
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
    else:
        step = 50
        stripped_name = link_key
        node_list = link_key.split('-')
        node_list=[node_list[i].strip('r_') for i in range(0,len(node_list))]
        no_monitors = round(dist_dict[(node_list[0], node_list[1])] / step)
        monitors = [stripped_name + '-amp' + str(i) + '-monitor' for i in
                    range(1, no_monitors + 1)]
        monitors.insert(0, stripped_name + '-boost-monitor')
        monitors = monitor_deployment_info(monitors, density=density, first_last=first_last)
        return monitors

def get_monitor_deploy_info(link_key, density=10, first_last='first'):
    """
    net: network object
    density: density percentage (10 = 10%, 30 = 30%, etc)
    first_last: when 1 OPM is to be used, decide whether using
    the first one (boost-monitor) or last one (pre-amp-monitor) in the link
    """
    dist_dict={('amsterdam', 'london'): 390, ('london', 'amsterdam'): 390, ('amsterdam', 'brussels'): 200,
     ('brussels', 'amsterdam'): 200, ('amsterdam', 'luxembourg'): 310, ('luxembourg', 'amsterdam'): 310,
     ('amsterdam', 'berlin'): 600, ('berlin', 'amsterdam'): 600, ('amsterdam', 'copenhagen'): 750,
     ('copenhagen', 'amsterdam'): 750, ('berlin', 'copenhagen'): 400, ('copenhagen', 'berlin'): 400,
     ('berlin', 'paris'): 900, ('paris', 'berlin'): 900, ('berlin', 'prague'): 320, ('prague', 'berlin'): 320,
     ('berlin', 'vienna'): 710, ('vienna', 'berlin'): 710, ('brussels', 'london'): 340, ('london', 'brussels'): 340,
     ('brussels', 'paris'): 270, ('paris', 'brussels'): 270, ('brussels', 'milan'): 850, ('milan', 'brussels'): 850,
     ('brussels', 'luxembourg'): 100, ('luxembourg', 'brussels'): 100, ('copenhagen', 'london'): 1000,
     ('london', 'copenhagen'): 1000, ('copenhagen', 'prague'): 760, ('prague', 'copenhagen'): 760,
     ('london', 'paris'): 410, ('paris', 'london'): 410, ('luxembourg', 'paris'): 370, ('paris', 'luxembourg'): 370,
     ('luxembourg', 'zurich'): 440, ('zurich', 'luxembourg'): 440, ('luxembourg', 'prague'): 900,
     ('prague', 'luxembourg'): 900, ('milan', 'paris'): 810, ('paris', 'milan'): 810, ('milan', 'zurich'): 100,
     ('zurich', 'milan'): 100, ('milan', 'vienna'): 720, ('vienna', 'milan'): 720, ('paris', 'zurich'): 590,
     ('zurich', 'paris'): 590, ('prague', 'zurich'): 100, ('zurich', 'prague'): 100, ('prague', 'vienna'): 350,
     ('vienna', 'prague'): 350, ('vienna', 'zurich'): 710, ('zurich', 'vienna'): 710}



    if link_key == 'r_london-r_copenhagen':
        # build the monitors list
        mon_ldn_cph = ['r_london-r_copenhagen-amp%s' % str(i) for i in range(1, 21)]
        # insert booster monitor at the beginning
        mon_ldn_cph.insert(0, 'r_london-r_copenhagen-boost')
        # consider only the number of monitors given by the density %
        mon_ldn_cph = monitor_deployment_info(mon_ldn_cph, density=density, first_last=first_last)
        return mon_ldn_cph

    elif link_key == 'r_copenhagen-r_berlin':
        mon_cph_ber = ['r_copenhagen-r_berlin-amp%s' % str(i) for i in range(1, 9)]
        mon_cph_ber.insert(0, 'r_copenhagen-r_berlin-boost')
        mon_cph_ber = monitor_deployment_info(mon_cph_ber, density=density, first_last=first_last)
        return mon_cph_ber

    elif link_key == 'r_paris-r_berlin':
        mon_par_ber = ['r_paris-r_berlin-amp%s' % str(i) for i in range(1, 19)]
        mon_par_ber.insert(0, 'r_paris-r_berlin-boost')
        mon_par_ber = monitor_deployment_info(mon_par_ber, density=density, first_last=first_last)
        return mon_par_ber

    elif link_key == 'r_prague-r_vienna':
        mon_pra_vie = ['r_prague-r_vienna-amp%s' % str(i) for i in range(1, 8)]
        mon_pra_vie.insert(0, 'r_prague-r_vienna-boost')
        mon_pra_vie = monitor_deployment_info(mon_pra_vie, density=density, first_last=first_last)
        return mon_pra_vie
    else:
        step = 50
        stripped_name = link_key
        node_list = link_key.split('-')
        node_list=[node_list[i].strip('r_') for i in range(0,len(node_list))]
        no_monitors = round(dist_dict[(node_list[0], node_list[1])] / step)
        monitors = [stripped_name + '-amp' + str(i) + '-monitor' for i in
                    range(1, no_monitors + 1)]
        monitors.insert(0, stripped_name + '-boost-monitor')
        monitors = monitor_deployment_info(monitors, density=density, first_last=first_last)
        return monitors


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

def monitor_deployment_info(monitor_link, density=10, first_last='first'):
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
            monitors.append(0)
        else:
            monitors.append(monitor_no-1)
    else:
        # if monitor_no >= 2, select monitors in an even manner
        monitors = monitor_select_info(monitor_link, monitor_no)
    return monitors


def monitor_select_info(monitor_link, monitor_no):
    n = len(monitor_link)
    # select indices from even_select algorithm
    indices = even_select(n, monitor_no)
    monitors = []
    for i, k in enumerate(indices):
        if k == 0:
            monitors.append(i)
    return monitors


def even_select(n, m):
    """
    n: number of OPMs in link
    m: number of OPMs required
    return: list [0,1] with location of OPMs
    to be considered (0) and ignored (1) as per
    their location in the link
    """

    span_equalizers=[8,16]
    #span_equalizers=[4,8,12,16]
    if m > n/2:
        cut = np.zeros(n, dtype=int)
        q, r = divmod(n, n-m)
        indices = [q*i + min(i, r) for i in range(n-m)]
        """for i in span_equalizers:
            if i in indices and i+1<n:
                if i+1 not in indices:
                    indices[indices.index(i)] = i + 1
            if i-1 in indices and i+1<n:
                if i+1 not in indices:
                    indices[indices.index(i - 1)] = i + 1
                elif i not in indices:
                    indices[indices.index(i-1)] = i"""


            #if i - 1 in indices and i + 1 > n:
             #   indices[indices.index(i - 1)] = i

            #if i-2 in indices and i+1<n:
             #   indices[indices.index(i-2)] = i+1
            #if i-1 in indices and i+2<n:
             #   indices[indices.index(i-1)]=i+2
        #if 0 in indices:
        #indices[0]=1
        #print(indices)
        cut[indices] = True
        if (n==21):
            print("no of opms requested : " + str(m))
            print(cut)


    else:
        cut = np.ones(n, dtype=int)
        q, r = divmod(n, m)
        indices = [q*i + min(i, r) for i in range(m)]
        """for i in span_equalizers:
            if i in indices and i + 1 < n:
                if (i+1) not in indices:
                   indices[indices.index(i)] = i + 1
            if i-1 in indices and i+1<n:
                if (i + 1) not in indices:
                    indices[indices.index(i - 1)] = i + 1
                elif i not in indices and i<n:
                    indices[indices.index(i-1)] = i"""


            #if i - 1 in indices and i + 1 > n:
             #   indices[indices.index(i - 1)] = i

            #if i-2 in indices and i+1<n:
             #   indices[indices.index(i-2)] = i+1
            #if i-1 in indices and i + 2 < n:
             #   indices[indices.index(i -1)] = i+2
        #if 0 in indices:
        #indices[0] = 1



        cut[indices] = False
        if (n == 21):
            #print("no of opms : " + str(n))
            print("no of opms requested : " + str(m))
            print(cut)
    """cut = np.ones(n, dtype=int)
    if(n<=8):
        cut[0] = 0
    if (n >7):
        cut[7] = 0

    if(n>15):
        cut[15] = 0
    print("cut"+str(cut))"""
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
    fig_name = '/home/ayush/Desktop/Arizona_work/pra_vie_e2d_end.png'
    plt.savefig(fig_name, format='png', bbox_inches='tight', pad_inches=0)



# dummy boolean
def run_analysis(monitored_nli=False):
    tmp_bool = True
    if tmp_bool:

        root_dir = 'cost239-monitor/estimation-module-new/'
        links_dir = ['r_london-r_copenhagen/', 'r_copenhagen-r_berlin/', 'r_paris-r_berlin/', 'r_prague-r_vienna/']
        # [['london', 'amsterdam'], ['london', 'paris', 'luxembourg', 'zurich']]
        # links_dir = ['r_london-r_amsterdam/', 'r_london-r_paris/', 'r_paris-r_luxembourg/', 'r_luxembourg-r_zurich/']
        densities_dir = ['density_10/', 'density_30/', 'density_60/']
        link_dict = {}
        for link in links_dir:
            link_dict[link.strip('/')] = {}

        mon_est = build_mon_est(links_dir)  # change automated

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

        # ['london', 'brussels', 'luxembourg', 'amsterdam'], ['london', 'brussels', 'paris', 'zurich']
        # [['london', 'amsterdam'], ['london', 'paris', 'luxembourg', 'zurich']]
        # link_keys=['r_london-r_amsterdam',('r_london-r_paris', 'r_paris-r_luxembourg', 'r_luxembourg-r_zurich')]
        link_keys = [('r_london-r_copenhagen', 'r_copenhagen-r_berlin'), 'r_paris-r_berlin', 'r_prague-r_vienna']
        # channels_list = [range(1, 16), range(16, 31), range(31, 46)]

        channelsa_list = [
            59, 25, 71, 79, 10, 34, 57, 15, 40, 23, 39, 66, 46, 17, 53, 67, 61, 55, 26, 76, 24, 11, 28, 60, 47, 62, 50,
            86,
            19, 6, 73, 69, 3, 89, 14, 27, 84, 35, 68, 16, 72, 80, 51, 7, 21, 85, 41, 45, 38, 5, 77, 8, 42, 81, 52, 64,
            43,
            2, 87, 88, 65, 36, 30, 78, 70, 18, 37, 29, 63, 74, 56, 4, 20, 83, 1, 12, 9, 58, 44, 49, 54]

        channels_list = [[1, 2, 3, 4, 5, 6, 7, 8, 73, 74, 75, 85, 86], channelsa_list[16:30], range(75, 91)]
        # channels_list = [ range(16,31), channelsa_list[16:30], range(75, 91)]
        mon_corr = build_mon_corr(links_dir)  # change automated
        mon_info = {}
        mon_info_stat = {}
        per_link_mon = {10: [], 20: [], 30: [], 40: [], 50: [], 60: [], 70: [], 80: []}
        for link_key in link_keys:
            for density in per_link_mon.keys():
                if type(link_key) is tuple:
                    for i, e in enumerate(link_key, start=1):
                        link_dir = e + '/'
                        monitors = get_monitors(link_dir)
                        monitors_by_density = get_monitor_deploy_info(e, density=density)
                        if (link_dir not in mon_info_stat.keys()):
                            mon_info_stat[link_dir] = {10: [], 20: [], 30: [], 40: [], 50: [], 60: [], 70: [], 80: []}
                            mon_info_stat[link_dir][density] = monitors_by_density
                        else:
                            mon_info_stat[link_dir][density] = monitors_by_density
                else:
                    link_dir = link_key + '/'
                    monitors = get_monitors(link_dir)
                    monitors_by_density = get_monitor_deploy_info(link_key, density=density)
                    if (link_dir not in mon_info_stat.keys()):
                        mon_info_stat[link_dir] = {10: [], 20: [], 30: [], 40: [], 50: [], 60: [], 70: [], 80: []}
                        mon_info_stat[link_dir][density] = monitors_by_density
                    else:
                        mon_info_stat[link_dir][density] = monitors_by_density

        # densities = [10]
        densities = [10, 20, 30, 40, 50, 60, 70, 80]
        for density in densities:
            print("Densities : " + str(density))
            for link_key, channels in zip(link_keys, channels_list):
                main_struct = build_struct(15, signal_ids=channels)
                if type(link_key) is tuple:
                    for i, e in enumerate(link_key, start=1):
                        link_dir = e + '/'
                        monitors = get_monitors(link_dir)
                        monitors_by_density = get_monitor_deploy(e, density=density)
                        if i == len(link_key):
                            tmp, mon_corr[density][e] = get_corrected_struct_simpledemo(e, monitors,
                                                                                        monitors_by_density,
                                                                                        main_struct=main_struct,monitored_nli=monitored_nli)
                            print(tmp)
                        else:
                            main_struct, mon_corr[density][e] = get_corrected_struct_simpledemo(e, monitors,
                                                                                                monitors_by_density,
                                                                                                main_struct=main_struct,monitored_nli=monitored_nli)
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
            monitor_count = 0
            for density in densities:
                for monitor in monitors:
                    gosnr_opm = gosnr_opm_dict[monitor]
                    gosnr_est = mon_est[link_key][monitor]['gosnr']
                    gosnr_corr = mon_corr[density][link_key][monitor]
                    # Compute errors for the above
                    error = compute_errors(gosnr_opm, gosnr_est)
                    """
                    if link_key=='' and density ==20 :
                        if monitor_count<16:
                            fig = plt.figure()
                            plt.plot(list(nli.keys()), list(nli.values()), '--', markeredgewidth=3, markersize=9,
                                      markerfacecolor='None',
                                      color='r', marker='o',label="Corrected-ASE")
                             #plt.ylabel("Corrected NLI Value")
                            plt.plot(list(nli.keys()), list(keys_to_int(nli_opm_dict[monitor]).values()), '--', markeredgewidth=3,
                                      markersize=9, markerfacecolor='None',
                                      color='b', marker='x',label="Monitored-ASE")
                            plt.plot(list(gosnr_opm.keys()), list(gosnr_opm.values()), '--', markeredgewidth=3,
                                     markersize=9,
                                     markerfacecolor='None',
                                     color='r', marker='o', label="Monitored GOSNR")
                            plt.plot(list(gosnr_est.keys()), list(gosnr_est.values()), '--', markeredgewidth=3,
                                     markersize=9,
                                     markerfacecolor='None',
                                     color='g', marker='o', label="Estimated GOSNR")
                            # plt.ylabel("Corrected NLI Value")
                            plt.plot(list(gosnr_corr.keys()), list(gosnr_corr.values()), '--',
                                     markeredgewidth=3,
                                     markersize=9, markerfacecolor='None',
                                     color='b', marker='x', label="Corrected-GOSNR")

                            plt.ylabel("GOSNR (dB)")
                            plt.xlabel("Channels")
                            plt.title(str(monitor))
                            plt.grid(True)
                            plt.legend()
                            monitor_count = monitor_count + 1
                            pass"""

                    errors_orig[density].append(error)

                    # Compute errors for OPM and QoT-E corrected
                    error_c = compute_errors(gosnr_opm, gosnr_corr)
                    errors_corr[density].append(error_c)

            error_link_orig[link_key] = errors_orig
            error_link_corr[link_key] = errors_corr

        # plot_error_to_density('r_prague-r_vienna', error_link_orig, error_link_corr)

        # ['r_london-r_copenhagen/', 'r_copenhagen-r_berlin/', 'r_paris-r_berlin/', 'r_prague-r_vienna/']

        links_dir = [ 'r_copenhagen-r_berlin/']
        link_dir_global.append(links_dir[0])
        plt.rc('axes', labelsize=14)
        plt.rc('legend', fontsize=12)
        for link_dir in links_dir:
            fig = plt.figure()
            link_key = link_dir[:-1]

            error_orig = error_link_orig[link_key]
            error_corr = error_link_corr[link_key]

            colors = ['c', 'm', 'y', 'k', 'g', 'darkblue', 'r', 'lightblue']
            markers = ['X', 'H', 's', '.', 'h', 'D', 'v', '^']
            bl = True
            for density in densities:
                eo = error_orig[density]
                ec = error_corr[density]

                if bl:
                    bl = False
                    label_eo = 'original error-' + link_key
                    error_plot['original']=eo
                    plt.plot(eo, color='g', label=label_eo)

                mon_point_values = [ec[i] for i in mon_info_stat[link_dir][density]]

                label_ec = 'c-' + link_key + '-' + str(density)
                color = colors.pop()
                marker = markers.pop()

                if(monitored_nli):
                    error_plot["monitored-nli"][density] =ec
                else:
                    error_plot["estimated-nli"][density]= ec





                plt.plot(ec, color=color, label=label_ec, marker=marker)
                plt.plot(mon_info_stat[link_dir][density], mon_point_values, color=color, marker=marker,
                         linestyle='None', markersize=12)

            plt.legend()
            plt.grid(True)
            plt.xlabel('Monitoring locations')
            plt.ylabel('QoT-E max error [dB]')

        name_png = link_dir[:-1] + '_algo2t_6spanequalizer.png'

        fig_name = '/home/ayush/Desktop/Arizona_work/' + name_png
        # plt.savefig(fig_name, format='png', bbox_inches='tight', pad_inches=0)
        plt.show()

error_plot={"monitored-nli":{},"estimated-nli":{}}
link_dir_global=[]
run_analysis()
run_analysis(monitored_nli=True)

fig = plt.figure()
colors = ['c', 'm','c', 'm', 'y', 'k', 'g', 'darkblue', 'r', 'lightblue','r', 'lightblue']
markers = ['X', 'H', 'X', 'H','s', '.', 'h', 'D', 'v', '^','v', '^']
densities=[10,80]
plt.rc('axes', labelsize=14)
plt.rc('legend', fontsize=12)
for type in error_plot.keys():
    if(type=='original'):

        #plt.plot(error_plot['original'], color='g', label=str(link_dir_global[0])+" original error")
        plt.plot(error_plot['original'], color='g', label="copenhagen-berlin original error")
        continue

    for density in error_plot[type].keys():
        if density in densities:
            color = colors.pop()
            marker = markers.pop()
            if(type=="monitored-nli"):
                plt.plot(error_plot[type][density], color=color, linestyle='--', label="algorithm1 - " + str(density)+" %",
                         marker=marker)
            else:
                plt.plot(error_plot[type][density], color=color,
                         label="algorithm2 - " + str(density)+" %",
                         marker=marker)




plt.legend()
plt.grid(True)
plt.xlabel('Monitoring locations')
plt.ylabel('QoT-E max error [dB]')
plt.show()

print(error_plot)
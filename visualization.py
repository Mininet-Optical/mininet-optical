from node import abs_to_dbm, Monitor
from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR, fetchRules )

import matplotlib.pyplot as plt
import time


def plot_power_vs_wavelength(net, monitor_name, port=None, monitor_mode=None):
    frequency_list=[]
    power_list=[]
    plt.ion()
    figure, ax = plt.subplots(figsize=(8,8))
    plt.plot(frequency_list, power_list,'bo', label='node %s'%(monitor_name))
    plt.xlabel('Frequency [THz]')
    plt.ylabel('Power [dBm]')
    plt.legend(bbox_to_anchor=(0,1.05,1,0.2), loc="lower left",
               mode="expand", borderaxespad=0)
    plt.savefig('PlotMonitor.png')

    while True:
        frequency_list=[]
        power_list=[]
        plt.xlabel('Frequency [THz]')
        plt.ylabel('Power [dBm]')
        response = net.get( 'monitor', params=dict( node=monitor_name, port=port, mode=monitor_mode ) )
        monidata = response.json()[ 'osnr' ]
        for channel, data in monidata.items():
            THz = float( data['freq'] )/1e12
            frequency_list.append(THz)
            power_abs = data['power']
            power_dbm=abs_to_dbm(power_abs)
            power_list.append(power_dbm)
        # print('frequency_list= ', frequency_list)
        # print('power_list= ', power_list)
        plt.plot(frequency_list, power_list,'bo', label='node %s'%(monitor_name))
        plt.legend(bbox_to_anchor=(0,1.05,1,0.2), loc="lower left",
                   mode="expand", borderaxespad=0)
        # Uncomment to have the power value above the points:
        #for x,y in zip(frequency_list,power_list):
        #    label = "{:.2f}".format(y)
        #    plt.annotate(label, # text
        #                (x,y), # point to label
        #                textcoords="offset points", # position of the text
        #                xytext=(0,10), # distance from text to points (x,y)
        #                ha='center') # horizontal alignment (left, right or center)
        # plt.ylim([-20, -10])
        figure.canvas.draw()
        figure.canvas.flush_events()
        time.sleep(1) # updated each second
        figure.clear(True)
    return None


if __name__ == '__main__':

    net=RESTProxy()
    plot_power_vs_wavelength(net, 'r4-monitor', port=None, monitor_mode='out')

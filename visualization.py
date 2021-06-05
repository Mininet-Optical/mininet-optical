from node import abs_to_dbm
from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR, fetchRules )

import matplotlib.pyplot as plt
import time


def plot_power_vs_wavelength(net, monitor_name):
    frequency_list=[]
    power_list=[]
    plt.ion()
    figure, ax = plt.subplots(figsize=(8,8))
    plt.plot(frequency_list, power_list,'bo', label='node %s'%(monitor_name))
    plt.xlabel('Frequency [THz]', size = 20)
    plt.ylabel('Power [dBm]', size = 20)
    plt.legend(bbox_to_anchor=(0,1.05,1,0.2), loc="lower left",
               mode="expand", borderaxespad=0)
    plt.savefig('PlotMonitor.png')
    bbox_args = dict(boxstyle="round", fc="0.8")
    arrow_args = dict(facecolor='black', shrink=0.02) # or arrowstyle="->",
    while True:
        frequency_list=[]
        power_list=[]
        plt.xlabel('Frequency [THz]', size = 20)
        plt.ylabel('Power [dBm]', size = 20)
        plt.grid()
        response = net.get( 'monitor', params=dict( monitor=monitor_name ) )
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
        # Power value above every 6 points:
        i=1
        for x,y in zip(frequency_list,power_list):
            if (i%6 == 0):
                label = '(%.1f, %.4f)'%(x, y)
                plt.annotate(label, # text
                            (x,y), # point to label
                            textcoords="offset points", # position of the text
                            xytext=(0,60), # distance from text to points (x,y)
                            ha='center', # horizontal alignment (left, right or center)
                            va="bottom",
                            bbox=bbox_args,
                            size= 15,
                            arrowprops=arrow_args)
            i+=1
        plt.ylim([-20, 0])
        figure.canvas.draw()
        figure.canvas.flush_events()
        time.sleep(1) # updated each second
        figure.clear(True)
    return None


if __name__ == '__main__':

    net=RESTProxy()
    plot_power_vs_wavelength(net, 'r2-monitor')

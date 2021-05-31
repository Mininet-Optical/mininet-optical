import rest
from dataplane import SwitchBase, Terminal, ROADM, OpticalLink, Monitor
from mininet.node import Switch
from node import db_to_abs, abs_to_db, abs_to_dbm
import node
from rest import (monitors, links, nodes, extract_power)
from dataplane import (Terminal, ROADM, OpticalLink,
                       OpticalNet as Mininet, km, m, dB, dBm)
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.log import setLogLevel, warning
from mininet.clean import cleanup
from sixnodestopo import SixROADMTopo
from wsgiref.simple_server import make_server, WSGIRequestHandler
from bottle import route, get, post, request, default_app, abort
from threading import Thread

from dataplane import Monitor, SwitchBase, Terminal, ROADM, OpticalLink
from mininet.node import Switch
from sixnodestopo import SixROADMTopo
from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR, fetchRules )

def extract_power(node_name):

    monitor = node_name.model
    #monitor = lookUpNode( monitor )
    signals = monitor.get_optical_signals()
    signals = sorted(signals, key=lambda s:s.index)
    frequency_list = []
    power_list = []
    for signal in signals:
        freq=signal.frequency
        freq_thz=freq*1e-12
        frequency_list.append(freq_thz)
        power_abs=monitor.get_power( signal )
        power_dbm=abs_to_dbm(power_abs)
        power_list.append(power_dbm)

    return frequency_list, power_list


def plotMonitor(node_name):
    monitor = node_name.model
    frequency_list, power_list = extract_power(monitor)
    plt.figure(figsize=(8,8))
    plt.plot(frequency_list, power_list,'o', label='node %s'%(node_name))
    plt.xlabel('Frequency [THz]')
    plt.ylabel('Power [dBm]')
    #plt.ylim([-50, -30])
    plt.legend(bbox_to_anchor=(0,1.05,1,0.2), loc="lower left",
               mode="expand", borderaxespad=0) #, ncol=3
    for x,y in zip(frequency_list,power_list):
        label = "{:.2f}".format(y)
        plt.annotate(label, # this is the text
                     (x,y), # this is the point to label
                     textcoords="offset points", # how to position the text
                     xytext=(0,10), # distance from text to points (x,y)
                     ha='center') # horizontal alignment can be left, right or center
    #plt.tight_layout()
    plt.savefig('PlotMonitor.png')
    return None

if __name__ == '__main__':
    #topo = SixROADMTopo()
    net=RESTProxy()

    linksvar = net.get( 'links' ).json()['links']
    #print(linksvar)
    nodesvar = net.get( 'nodes' ).json()['nodes']
    key_node=list(nodesvar.keys())
    print(nodesvar)
    monitorsvar = net.get( 'monitors' ).json()#['monitors']
    print(monitorsvar)
    r = net.get( 'links/roadms' ).json()['links']
    print(r)
    net.allNodes = fetchNodes( net )
    print(net.allNodes)
    net.switches = sorted( node for node, cls in net.allNodes.items()
                           if cls == 'OVSSwitch' )
    net.terminals = sorted( node for node, cls in net.allNodes.items()
                            if cls == 'Terminal' )
    net.roadms =  sorted( node for node, cls in net.allNodes.items()
                          if cls == 'ROADM' )
    net.nodes = net.terminals + net.roadms
    print(net.roadms)
    #fetchRules(r6)
    monitors = net.get( 'monitors' ).json()['monitors']
    print("monitor: ", monitors)
    fetchOSNR(net)
    #print(rest.nodes())
    plotMonitor(r6-monitor)
    #print(links())
    #moninode=t4
    #moninode.plotMonitor()
    #plotMonitor(r6)

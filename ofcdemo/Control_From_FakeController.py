import fakecontroller as fk
import requests

class Mininet_Control_REST(object):
    def __init__(self):
        self.net = fk.RESTProxy()
        self.net.AllNodes = fk.fetchNodes(self.net)
        self.net.roadms = sorted(node for node, cls in self.net.AllNodes.items()
                                 if cls == 'ROADM')
        self.net.terminals = sorted(node for node, cls in self.net.AllNodes.items()
                                 if cls == 'Terminal')
        self.net.monitors = sorted(node for node, cls in self.net.AllNodes.items()
                                 if cls == 'Monitor')
        self.net.switches = sorted(node for node, cls in self.net.AllNodes.items()
                                   if cls == 'OVSSwitch')

        self.net.nodes = self.net.terminals + self.net.roadms

        # Fetch links
        self.net.allLinks, self.net.roadmLinks, self.net.terminalLinks = fk.fetchLinks(self.net)

        # Create adjacency dict
        self.net.graph = self.buildGraph(self.net.allLinks)

        # Fetch ports
        self.net.ports = fk.fetchPorts(self.net, self.net.roadms + self.net.terminals + self.net.switches)

        # Calculate inter-pop routes
        self.net.routes = {node: self.route(node, self.net.graph, self.net.terminals)
                           for node in self.net.terminals}

    def monitorOSNRbyKey(self):

        monitors = self.net.get('monitors').json()['monitors']
        for key in sorted(monitors):
            response = self.net.get('monitor', params=dict(monitor=key))
            osnrdata = response.json()['osnr']

            #THz = float(osnrdata[str(channel)]['freq']) / 1e12
            #osnr, gosnr = osnrdata[str(channel)]['osnr'], osnrdata[str(channel)]['gosnr']
            return osnrdata


    def monitorOutputs(self):
        for monitor in self.net.monitors:
            print(monitor)
            print(self.net.get('monitor'))
            response = self.net.get('monitor')
            #fk.fetchOSNR(monitor)
            osnrdata = response.json()['osnr']
            print(osnrdata)
            return osnrdata.keys()



def test():
    control = Mininet_Control_REST()
    net = control.net
    print(net.AllNodes)
    print(net.monitors)
    #control.monitorOutputs()
    print(control.monitorOSNRbyKey())
test()






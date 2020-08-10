from dataplane import Mininet, disableIPv6
from sdn_monitor_qot_e.demolib import LinearRoadmTopo, CLI
from rest import RestServer

from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController


if __name__ == '__main__':
    # Test our demo topology
    cleanup()
    setLogLevel('info')
    topo1 = LinearRoadmTopo(n=5, txCount=5)
    # topo2 = LinearRoadmTopo(n=15, txCount=9)
    info('*** Creating PTL-Demo Topology \n')
    net = Mininet(topo=topo1, autoSetMacs=True,
                  controller=RemoteController)
    disableIPv6(net)
    restServer = RestServer(net)
    net.start()
    restServer.start()
    CLI(net)
    restServer.stop()
    net.stop()
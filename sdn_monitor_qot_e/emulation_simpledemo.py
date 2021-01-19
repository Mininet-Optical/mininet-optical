from dataplane import Mininet, disableIPv6

from emulation_demolib import Cost239Topo, CLI
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from mininet.node import RemoteController
from rest import RestServer


if __name__ == '__main__':
    # Test our demo topology
    cleanup()
    setLogLevel('info')
    net = Mininet(topo=Cost239Topo(txCount=30), autoSetMacs=True,
                      controller=RemoteController)
    disableIPv6(net)
    restServer = RestServer(net)
    net.start()
    restServer.start()
    CLI(net)
    restServer.stop()
    net.stop()

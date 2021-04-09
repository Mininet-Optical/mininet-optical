from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy,
                                    OFSwitchProxy, TerminalProxy,
                                    fetchNodes)


def install_paths(nodes, channels, line_terminals):
    for i, node in enumerate(nodes):
        if i == len(nodes) - 1:
            return
        elif i == 0:
            in_port = 1
            out_port = 11
        else:
            in_port = channels[0]
            out_port = 12
        ROADMProxy(node).connect(port1=in_port, port2=out_port, channels=channels)


def run(net):
    net.allNodes = fetchNodes(net)
    line_terminals = net.terminals = sorted(node for node, cls in net.allNodes.items()
                           if cls == 'Terminal')
    roadms = net.roadms = sorted(node for node, cls in net.allNodes.items()
                        if cls == 'ROADM')

    channels = [1]
    for i, (r, lt_tx) in enumerate(zip(roadms, line_terminals)):
        if i == 0:
            lt_rx = line_terminals[-1]
        else:
            lt_rx = line_terminals[i - 1]
            # rx_transceiver = lt_rx.rx_transceivers[c]
            # lt_rx.assoc_rx_to_channel(rx_transceiver, c)
        # configure line terminal
        for c in channels:
            print("enter enter", lt_tx)
            TerminalProxy(lt_tx).connect(ethPort=c, wdmPort=11, channel=c)

        # build paths from r_i to r_n
        path = [r] + roadms[i + 1:]
        if len(path) < len(roadms):
            path += roadms[:i]
        path.append(lt_rx)

        # install switch rules into the ROADMs
        install_paths(path, channels, line_terminals)

        print("*** Turning on:", lt_tx)
        TerminalProxy(lt_tx).turn_on()

        ch = channels[0] + 1
        channels[0] = ch



        # # When setting wdmPort we refer to the transceiver
        # TerminalProxy('t1').connect(ethPort=1, wdmPort=11, channel=1)
        #
        # ch = [1]
        # ROADMProxy('r1').connect(port1=1, port2=11, channels=ch)
        #
        # ROADMProxy('r2').connect(port1=11, port2=12, channels=ch)
        #
        # ROADMProxy('r3').connect(port1=11, port2=1, channels=ch)
        # print("*** t1 turning on!")
        # TerminalProxy('t1').turn_on()


if __name__ == '__main__':
    net = RESTProxy()
    run(net)

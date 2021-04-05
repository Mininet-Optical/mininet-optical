from ofcdemo.fakecontroller import (RESTProxy, ROADMProxy,
                                    OFSwitchProxy, TerminalProxy,
                                    fetchNodes)
import network
from link import Span as Fiber, SpanTuple as Segment
from node import Transceiver


def run(net):
    net.roadms = sorted(node for node, cls in net.allNodes.items()
                        if cls == 'ROADM')

    print(net.roadms)

    # ch_no = 1
    # channels = range(1, ch_no + 1)
    # channels = [1]
    # for i, (r, lt_tx) in enumerate(zip(roadms, line_terminals)):
    #     if i == 0:
    #         lt_rx = line_terminals[-1]
    #     else:
    #         lt_rx = line_terminals[i - 1]
    #
    #     # configure line terminal
    #     for c in channels:
    #         tx_transceiver = lt_tx.tx_transceivers[c]
    #         lt_tx.assoc_tx_to_channel(tx_transceiver, c, c)
    #
    #         rx_transceiver = lt_rx.rx_transceivers[c]
    #         lt_rx.assoc_rx_to_channel(rx_transceiver, c)
    #
    #     # build paths from r_i to r_n
    #     path = [r] + roadms[i + 1:]
    #     if len(path) < len(roadms):
    #         path += roadms[:i]
    #     path.append(lt_rx)
    #
    #     # install switch rules into the ROADMs
    #     install_paths(path, channels, line_terminals)

    # print("*** Turning on:", lt_tx)
    # lt_tx.turn_on()
    #
    # ch = channels[0]
    # ch += 1
    # channels[0] = ch
    # channels = range(ch_no + 1, ch_no + ch_no + 1)
    # ch_no += ch_no


def install_paths(nodes, channels, line_terminals):
    for i, node in enumerate(nodes):
        if i == len(nodes) - 1:
            return
        out_port = net.find_link_and_out_port_from_nodes(node, nodes[i + 1])
        if i == 0:
            src_node = line_terminals[i]
            for c in channels:
                node.install_switch_rule(1, c, out_port, [c], src_node=src_node)
        else:
            in_port = net.find_link_and_in_port_from_nodes(nodes[i - 1], node)
            node.install_switch_rule(1, in_port, out_port, channels, src_node=nodes[i - 1])

if __name__ == '__main__':
    net = RESTProxy()
    run(net)

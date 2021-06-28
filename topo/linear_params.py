import network
from link import Span as Fiber, SpanTuple as Segment
import numpy as np
from node import Transceiver
from topo.helper_funcs import *


class LinearTopology:

    @staticmethod
    def build(power_dBm=0, span_length_km=3, span_no=1, hop_no=1, signal_no=10, debugger=True):
        """
        :param op: operational power in dBm
        :param non: number of nodes (integer)
        :return: Network object
        """
        # Create an optical-network object
        net = network.Network()

        # Create LineTerminal objects
        tr_labels = ['tr%s' % str(x) for x in range(1, signal_no + 1)]
        # Transmitter terminal
        transceivers = [Transceiver(id, tr, operation_power=power_dBm)
                        for id, tr in enumerate(tr_labels, start=1)]
        tx = net.add_lt('tx', transceivers=transceivers)
        # Receiver terminal
        transceivers = [Transceiver(id, tr, operation_power=power_dBm)
                        for id, tr in enumerate(tr_labels, start=1)]
        rx = net.add_lt('rx', transceivers=transceivers, monitor_mode='in', debugger=debugger)

        # Create ROADM objects
        roadms = [net.add_roadm('r%s' % (i + 1),
                                insertion_loss_dB=17,
                                reference_power_dBm=power_dBm,
                                preamp=add_amp(net, node_name='r%s' % (i + 1),
                                               type='preamp', gain_dB=17.6, debugger=debugger),
                                boost=add_amp(net, node_name='r%s' % (i + 1),
                                              type='boost', gain_dB=17.0, debugger=debugger),
                                debugger=debugger)
                  for i in range(hop_no)]
        name_to_roadm = {roadm.name: roadm for roadm in roadms}

        first_roadm = roadms[0]
        last_roadm = roadms[-1]

        for port_no, tr in enumerate(tx.transceivers, start=1):
            net.add_link(tx, first_roadm, src_out_port=tr.id, dst_in_port=port_no, spans=[Span(0 * m)])
        for port_no, tr in enumerate(rx.transceivers, start=1):
            net.add_link(last_roadm, rx, src_out_port=port_no, dst_in_port=tr.id, spans=[Span(0 * m)])

        for i in range(hop_no-1):
            # Iterate through the number of nodes linearly connected
            r1 = name_to_roadm['r' + str(i + 1)]
            r2 = name_to_roadm['r' + str(i + 2)]
            build_link(net, r1, r2, span_no, span_length_km)

        return net

import network
from link import Span as Fiber, SpanTuple as Segment
import numpy as np
from node import Transceiver
from topo.helper_funcs import *


class LinearTopology:

    @staticmethod
    def build(power_dBm=0, span_length_km=50, span_no=1, hop_no=4, signal_no=3, debugger=False):
        """
        :param op: operational power in dBm
        :param non: number of nodes (integer)
        :return: Network object
        """
        # Create an optical-network object
        net = network.Network()

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

        for i, r in enumerate(roadms, start=1):
            # Create LineTerminal objects
            tr_labels = ['tr%s' % str(x) for x in range(1, signal_no + 1)]
            # Transmitter terminal
            transceivers = [Transceiver(id, tr, operation_power=power_dBm)
                            for id, tr in enumerate(tr_labels, start=1)]
            lt = net.add_lt(name='lt' + str(i), transceivers=transceivers, debugger=debugger)

            for port_no, tr in enumerate(lt.transceivers, start=1):
                net.add_link(lt, r, src_out_port=tr.id, dst_in_port=port_no, spans=[Span(0 * m)])
                net.add_link(r, lt, src_out_port=port_no, dst_in_port=tr.id, spans=[Span(0 * m)])

        for i in range(hop_no-1):
            # Iterate through the number of nodes linearly connected
            r1 = name_to_roadm['r' + str(i + 1)]
            r2 = name_to_roadm['r' + str(i + 2)]
            build_link(net, r1, r2, span_no, span_length_km)
            build_link(net, r2, r1, span_no, span_length_km)

        return net

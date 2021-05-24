from network import Network
from link import Span as Fiber, SpanTuple as Segment
from Simulation_API import Mininet_Optical_Simu_API
from lumentum_NETCONF_API import Lumentum_NETCONF
from node import Transceiver
from units import *
from collections import defaultdict
import random
from collections import defaultdict
import numpy as np
from ofcdemo.fakecontroller import (
    RESTProxy, TerminalProxy, ROADMProxy, OFSwitchProxy,
    fetchNodes, fetchLinks, fetchPorts, fetchOSNR )


from dataplane import (Terminal, ROADM, OpticalLink,
                       OpticalNet as Mininet, km, m, dB, dBm)
from rest import RestServer
from ofcdemo.demolib import OpticalCLI as CLI

from mininet.node import OVSBridge, Host
from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.clean import cleanup

from os.path import dirname, realpath, join
from subprocess import run
from sys import argv


km = dB = dBm = 1.0
m = .001

# Parameters

NUM_WAV = 40
LINE_IN, LINE_OUT = NUM_WAV, NUM_WAV + 1
NUM_NODE = 5
THRUPORT = 4
ADD_DROP = 1


#################### Lumentum Database ##########################
#
# Two Lumentum nodes form a ROADM node, West Lumemtum + East Lumentum
#
#                           ROADM Node
#   ========================================================
#  ||                                                       ||
#  ||      West  Lumentum              East Lumentum        ||
#  ||                                                       ||
#  ||                  /    add/drop1   \                   ||
#  ||   line in/out -----   add/drop2  -----  line in/out   ||
#  ||                  \    _______     /                   ||
#  ||                       ThruPort                        ||
#  ||                                                       ||
#   =========================================================

#  module 1 MUX, add 4101-4120, line out 4201
#  module 1 DEMUX, line in 5101, drop 5201-5220,
#
#
# ---------- network topology ---------
#
#  ROADM1   ROADM2      ROADM3     ROADM4
#   L1 ==== L2-L3 ===== L4-L5 ===== L6
#
# -------------------------------------
##
Lumentum_NETCONF_Agent = Lumentum_NETCONF()

NodeLink_to_LumentumLink = {}
NodeLink_to_LumentumLink['r1', 'r2'],NodeLink_to_LumentumLink['r2', 'r1'],\
NodeLink_to_LumentumLink['r2', 'r3'],NodeLink_to_LumentumLink['r3', 'r2'],\
NodeLink_to_LumentumLink['r3', 'r4'],NodeLink_to_LumentumLink['r4', 'r3'] \
    = ('L1', 'L2'),('L2', 'L1'),('L3', 'L4'),('L4', 'L3'),('L5', 'L6'),('L6', 'L5')


LumentumName_to_IP = {}
LumentumName_to_IP['L1'], LumentumName_to_IP['L2'], \
LumentumName_to_IP['L3'], LumentumName_to_IP['L4'], \
LumentumName_to_IP['L5'], LumentumName_to_IP['L6'] \
    = '10.104.1','10.104.2','10.104.3','10.104.4','10.104.5','10.104.6'



####################### Lumentum END ############################



class Lumentum_Control_NETCONF(object):

    def installPath(self, path, ruleID, channel):
        "intall switch rules on roadms along a lightpath with a signal channel"

        half_channel_width = 25  # in GHz
        start_center_frequency = 191350.0  # in GHz
        center_frequency = start_center_frequency + channel * 50
        start_freq = str(center_frequency - half_channel_width)
        end_freq = str(center_frequency + half_channel_width)

        # Two Lumentum nodes form a ROADM node, two WSSs forms a Lumentum node, module 1 is MUX WSS, module 2 is DEMUX WSS
        # ingress and egress nodes only use MUX and DEMUX respectively. Intermediate nodes use DEMUX -> MUX.
        for i in range(len(path)):
            # intermediate ROADM nodes using 2 Lumentum nodes (4 WSSs)
            if i != 0 or i != len(path)-1:
                Lumentum_this_out, Lumentum_next = NodeLink_to_LumentumLink[path[i], path[i + 1]]
                Lumentum_previous, Lumentum_this_in = NodeLink_to_LumentumLink[path[i - 1], path[i]]
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_in], status='add', conn_id=ruleID,
                                                  module_id=1, input_port=4100+THRUPORT, output_port=4201,
                                                  start_freq=start_freq, end_freq=end_freq, attenuation=0,
                                                  block=False, name='CH' + str(channel))
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_in], status='add', conn_id=ruleID,
                                                  module_id=2, input_port=5101, output_port=5200+THRUPORT,
                                                  start_freq=start_freq, end_freq=end_freq, attenuation=0,
                                                  block=False, name='CH' + str(channel))
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_out], status='add', conn_id=ruleID,
                                                  module_id=1, input_port=4100 + THRUPORT, output_port=4201,
                                                  start_freq=start_freq, end_freq=end_freq, attenuation=0,
                                                  block=False, name='CH' + str(channel))
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_out], status='add', conn_id=ruleID,
                                                  module_id=2, input_port=5101, output_port=5200 + THRUPORT,
                                                  start_freq=start_freq, end_freq=end_freq, attenuation=0,
                                                  block=False, name='CH' + str(channel))
            # Add/drop using Lumentum WSSs
            if i == 0 or i == len(path)-1:
                if i == 0:
                    Lumentum_this_add_drop, Lumentum_next = NodeLink_to_LumentumLink[path[i], path[i+1]]
                else:
                    Lumentum_previous, Lumentum_this_add_drop = NodeLink_to_LumentumLink[path[i-1], path[i]]
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_add_drop], status='add', conn_id=ruleID,
                                                  module_id=1, input_port=4100 + ADD_DROP, output_port=4201,
                                                  start_freq=start_freq, end_freq=end_freq, attenuation=0,
                                                  block=False, name='CH' + str(channel))
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_add_drop], status='add', conn_id=ruleID,
                                                  module_id=2, input_port=5101, output_port=5200 + ADD_DROP,
                                                  start_freq=start_freq, end_freq=end_freq, attenuation=0,
                                                  block=False, name='CH' + str(channel))


    def uninstallPath(self, path, ruleID):
        "delete switch rules on roadms along a lightpath for some signal channels"


        for i in range(len(path)):
            # del intermediate ROADM nodes using West+East Lumentum nodes (4 WSSs)
            if i != 0 or i != len(path) - 1:
                Lumentum_this_out, Lumentum_next = NodeLink_to_LumentumLink[path[i], path[i + 1]]
                Lumentum_previous, Lumentum_this_in = NodeLink_to_LumentumLink[path[i - 1], path[i]]
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_in], status='del', conn_id=ruleID,
                                                  module_id=1)
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_in], status='del', conn_id=ruleID,
                                                  module_id=2)
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_out], status='del', conn_id=ruleID,
                                                  module_id=1)
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_out], status='del', conn_id=ruleID,
                                                  module_id=2)
            # del Add/Drop using East Lumentum (two WSSs)
            if i == 0 or i == len(path)-1:
                if i == 0:
                    Lumentum_this_add_drop, Lumentum_next = NodeLink_to_LumentumLink[path[i], path[i+1]]
                else:
                    Lumentum_previous, Lumentum_this_add_drop = NodeLink_to_LumentumLink[path[i-1], path[i]]
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_add_drop], status='del', conn_id=ruleID,
                                                  module_id=1)
                Lumentum_NETCONF_Agent._ConfigWSS(node_ip=LumentumName_to_IP[Lumentum_this_add_drop], status='del', conn_id=ruleID,
                                                  module_id=2)

    def channel_monitor(self, path, ruleID):
        Lumentum_Source, Lumentum_next = NodeLink_to_LumentumLink[path[0], path[1]]
        Lumentum_previous, Lumentum_Desination = NodeLink_to_LumentumLink[path[-2], path[-1]]
        S_WSS_info = Lumentum_NETCONF_Agent._WSSMonitor(LumentumName_to_IP[Lumentum_Source])
        D_WSS_info = Lumentum_NETCONF_Agent._WSSMonitor(LumentumName_to_IP[Lumentum_Desination])
        print(S_WSS_info['MUX'][ruleID], S_WSS_info['DEMUX'][ruleID])
        print(D_WSS_info['MUX'][ruleID], D_WSS_info['DEMUX'][ruleID])


def Control_Test():
    " set up a lightpath from r4 to r1 bidirectionally with channel 5"

    ####### Lumentum Test ########
    path = ['r4', 'r3', 'r2', 'r1']
    Controller = Lumentum_Control_NETCONF()
    Controller.installPath(path=path, channel=5, ruleID=1)
    Controller.channel_monitor(path=path, ruleID=1)
    #Controller.uninstallPath(path=path, ruleID=1)


Control_Test()
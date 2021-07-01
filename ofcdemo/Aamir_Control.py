from fakecontroller import ListenPortBase
from Aamir_REST import Mininet_Control_Rest

Controller_Mininet = Mininet_Control_Rest


km = db = dbm = 1.0
m = 0.001

#Mininet variables


NUM_NODE = 4
TERMINAL_ID ={}
for i in range(NUM_NODE):
    TERMINAL_ID['t%d'%(i+1)] = (i+1)
def NetworkTopo():
    """
    Basic Roadm Topology
     t1   t2   t3   t4
     |    |    |    |
    r1 - r2 - r3 - r4
    """
    for k in range (1,NUM_NODE):
        print(k)

def Mininet_InstallPath(lightpath_id, path, channel, power):
    src, dst = path[0], path[-1]
    src_id, dst_id = TERMINAL_ID[src], TERMINAL_ID[dst]
    Controller_Mininet.installPath(path, channel)





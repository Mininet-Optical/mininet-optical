#!/usr/bin/python3



"""
UNIT TESTS

These are extremely simple and small tests
of individual component models in Mininet-Optical

"""


from simfunctions import createSignals, fiberOutput
from mnoptical.node import LineTerminal
from mnoptical.network import Network

# Constants
dBm = 1

# Parameters
LINEIN, LINEOUT = 0, 1
TxCount = 1

### SIMPLE FIBER TEST

def basicfibertest(length_km=50):
    "Basic propagation test through length of fiber"

    # Functional version
    channels = {ch:0*dBm for ch in range(1, TxCount+1)}
    s0 = createSignals(channels)
    s1 = fiberOutput(s0, length_km, srs=None)

    # Mininet-Optical version
    net = Network()
    c1 = CombSource('c1', channels)
    a1 = net.add_amplifier('a1', monitor_mode='in')
    span = Segment(Fiber(length_km), None)
    net.add_link(c1, a1, LINEOUT, LINEIN, spans=[span])
    c1.turn_on()
    m2 = mntosigstate('a1')


### This should be in mnoptical.node

class CombSource(LineTerminal):
    "Comb Source with multiple simulated output signals"
    def __init__(self, name, *args, power={1: 0*dBm}, **kwargs):
        """power: in form of dict {ch: power} where
           ch: channels to transmit
           power: tx power"""
        super().__init__(name, *args, **kwargs)
        for i, (ch, power) in enumerate(self.power.items(), start=1):
            tx = Transceiver(i, f'tx{ch}', power)
            self.add_transceiver(tx)
            self.assoc_tx_to_channel(tx, ch, LINEOUT)


### Helper functions

def makespan(net, length, aname='', *args, **params):
    "Return fiber span for net with optional compensating amp"
    amp = net.add_amplifier(aname, *args, **params) if aname else None
    return Segment(span=Fiber(length=length), amplifier=amp)

def mntosigstate(node, mode=None):
    """Convert mn-optical signal list to Sigstate dict
       node: mnoptical.node.Node with attached monitor
       mode: direction: None (node default) | 'in' | 'out'"""
    mon = node.monitor
    if mode: mon.modify_mode(mode)
    return {s.index: Sigstate(pwr=mon.get_power(s),
                              ase=mon.get_ase_noise(s),
                              nli=mon.get_nli_noise(s))
            for s in mon.get_optical_signals()}



if __name__ == '__main__':
    basicfibertest()

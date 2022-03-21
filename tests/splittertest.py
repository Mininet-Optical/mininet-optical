#!/usr/bin/python3
"""
splittertest.py: test splitter element

We create a 99/1 power split and verify that it
is working as expected.
"""

from mnoptical.network import Network
# Note: Segment() is a (Fiber(), Amplifier()) tuple
from mnoptical.link import Span as Fiber, SpanTuple as Segment
from mnoptical.node import Transceiver, Roadm, LineTerminal, Splitter, Amplifier
from mnoptical.units import abs_to_db

# Units
km = dB = dBm = 1.0
m = .001

# Terminal TX/RX port numbers (arbitrary for simulation)
TX, RX = 100, 200

# Splitter input and output ports
IN0, OUT1, OUT2 = 0, 1, 2

# Roadm line in/out and add/drop base
LINEIN, LINEOUT, ADD, DROP = 0, 1, RX, TX

# Number of transceivers
txcount = 3

# Network topology
def createnetwork():
    """Simple test network t1 -> r1 -> splitter(99/1) -> r3 -> t3
                                        -> r2 -> t2  """
    net = Network()
    
    def span(length, amp='', **params):
        "Span helper function"
        if amp: amp = net.add_amplifier(ampname, **params)
        return Segment(span=Fiber(length=length), amplifier=amp)

    # Terminals and Roadms
    for i in 1, 2, 3:
        transceivers = [Transceiver(i,f'tx{i}',0*dBm)
                        for i in range(1, txcount+1)]
        net.add_lt(f't{i}', transceivers=transceivers,
                   monitor_mode='in')
        net.add_roadm(f'r{i}')
    t1, t2, t3 = net.line_terminals
    r1, r2, r3 = net.roadms
        
    # 99/1 Splitter
    sp1 = net.add_node('sp1', cls=Splitter, split={OUT1:99, OUT2:1})

    # Local uplinks and downlinks
    L = net.add_link
    for ch in range(1, txcount+1):
        L(t1, r1, spans=[span(1*m)],
          src_out_port=TX+ch, dst_in_port=ADD+ch)
        L(r2, t2, spans=[span(1*m)],
          src_out_port=DROP+ch, dst_in_port=RX+ch)
        L(r3, t3, spans=[span(1*m)],
          src_out_port=DROP+ch, dst_in_port=RX+ch)

    # Long link before splitter
    net.add_link(
        r1, sp1, boost_amp=net.add_amplifier('boost1', target_gain=0.0),
        spans=[span(25*km)], src_out_port=LINEOUT, dst_in_port=IN0)

    # Short links from splitter
    net.add_link(sp1, r2, spans=[span(1*m)],
                 src_out_port=OUT1, dst_in_port=LINEIN)
    net.add_link(sp1, r3, spans=[span(1*m)],
                 src_out_port=OUT2, dst_in_port=LINEIN)
    
    return net

# Monitoring helper functions
def getsignalwatts(node, port=None):
    "Return monitored signal, ase noise, and nli noise power in watts"
    monitor = node.monitor
    return {s.index: {'pwrW': monitor.get_power(s),
                      'aseW': monitor.get_ase_noise(s),
                      'nliW': monitor.get_nli_noise(s)}
            for s in monitor.get_optical_signals(port)}

def wtodbm(W):
    "Return watts as dBm"
    return abs_to_db(W*1000.0) if W != 0 else float('-inf')

def printdbm(sigwatts, fn=wtodbm, units='dBm'):
    "Print signal watts as dBm"
    for ch, entries in sigwatts.items():
        pdbm = fn(entries['pwrW'])
        adbm = fn(entries['aseW'])
        ndbm = fn(entries['nliW'])
        print(f'ch{ch}: pwr {pdbm:.2e}{units} '
              f'ase {adbm:.2e}{units} nli {ndbm:.2e}{units}')

def printmw(sigwatts):
    "Print signal watts as watts"
    printdbm(sigwatts, fn=lambda W: W*1e3, units='mW')

# Configuration

def configroadms(net):
    "Configure ROADMs (as mux or demux)"
    r1, r2, r3 = net.roadms
    for ch in range(1, txcount+1):
        r1.install_switch_rule(ADD+ch, LINEOUT, ch)
        r2.install_switch_rule(LINEIN, DROP+ch, ch)
        r3.install_switch_rule(LINEIN, DROP+ch, ch)

def configterms(net):
    "Configure terminals"
    t1, t2, t3 = net.line_terminals
    # Set TX and RX channels
    for t in range(1, txcount+1):
        ch = t  # channel number == transceiver number
        tx1 = t1.id_to_transceivers[t]
        rx2 = t2.id_to_transceivers[t]
        rx3 = t3.id_to_transceivers[t]
        t1.assoc_tx_to_channel(tx1, ch, out_port=TX+ch)
        t2.assoc_rx_to_channel(rx2, ch, in_port=RX+ch)
        t3.assoc_rx_to_channel(rx3, ch, in_port=RX+ch)
    # Start transmission
    for term in t1, t2, t3:
        term.turn_on()

def ratio(a, b):
    "Return percent ratio of a to b"
    total = a+b
    apct = int(100.0 * a/total + .5)
    bpct = int(100.0 * b/total + .5)
    return apct, bpct

def test():
    "Verify that a 99/1 split works as expected"
    # Create and configure network
    net = createnetwork()
    configroadms(net)
    configterms(net)
    # Check power
    t1, t2, t3 = net.line_terminals
    print(f"*** {t2} power")
    t2watts = getsignalwatts(t2)
    printmw(t2watts)
    print(f"*** {t3} power")
    t3watts = getsignalwatts(t3)    
    printmw(t3watts)
    print(f"*** Checking split ratios")
    errors = 0
    for ch in range(1,4):
        for f in 'pwr', 'ase':
            w = f'{f}W'
            a, b = ratio(t2watts[ch][w], t3watts[ch][w])
            print(f"ch{ch} {f} split is {a}/{b}")
            if (a,b) != (99,1):
                print(f'Expected 99/1 split but got {a}/{b}')
    print(f"*** Completed with {errors} errors.")
    return errors
                
if __name__ == '__main__':
    result = test()
    exit(result)


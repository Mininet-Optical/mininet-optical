#!/usr/bin/env python3

"""

simpleverify.py:

We really want to verify Mininet-Optical's simulation
by comparing it with the output from our functions.

Ideally if we use the same parameters then the output
values should match as well

Note that this could potentially be done against
GNpy as well.

"""


# Functional model imports
from tests.simfunctions import (
    Sigstate, createSignals, fiberOutput, edfaAdjustedOutput,
    roadmOutput, flatWDG,
    plotChannelPower, pwr, ase, nli, tpwr, ddelta,
    wattstodbm, dbmtowatts,
    dB, dBm, cm, m, wdg1 )

# Mininet-Optical imports
from mnoptical.network import Network
from mnoptical.link import Span as Fiber, SpanTuple as Segment
from mnoptical.node import Transceiver as Tx, Roadm, LineTerminal, Node

# Standard imports
from functools import partial


### Validation tests: functional model vs. Mininet-Optical

TXCOUNT = 1 # number of channels to transmit


### 1. Single span with add and drop ROADMs

def singlespantest():
    """Single span topology:
       channels -> roadm -> fiber -> amp -> roadm """

    # Functional version
    channels = set(range(1,TXCOUNT+1))
    s0 = createSignals({ch:0*dBm for ch in channels})
    s1, _drop = roadmOutput(
        mux={'add':s0, 'loss':4.5, 'levelto': None},
        demux={'loss':0.0},
        boost={'gtarg':4.5, 'wdg':flatWDG})
    s2 = fiberOutput(s1, 75, srs=None)
    s3 = edfaAdjustedOutput(s2, gtarg=75*.22*dB, wdg=wdg1)
    _lineout, s4 = roadmOutput(s3, demux={'drop':channels})

    # Mininet-Optical simulated version
    net = net1()
    mnin, mnout = run1(net)
    m1 = mnout['r1']
    m2 = mnin['amp1']
    m3 = mnout['amp1']
    m4 = mnout['t1']
    nodes = net.name_to_node
    amp1 = nodes['amp1']
    print(amp1, amp1.system_gain)

    # Comparison
    dmax = max(abs(s1[ch].ase - m1[ch].ase)
               for ch in s1)
    print("ROADM/BOOST OUTPUT")
    print("FUNCTIONAL", s1)
    print("MNO", m1)
    print('DMAX', dmax)
    exit(0)
    plotChannelPower({
        #'r1 output ase (fn)': ase(s1),
        #'r1 output ase (mn)': ase(m1),
        'r1 ase delta': ddelta(ase(s1), ase(m1)),
        #'amp1 in pwr(fn)': pwr(s2),
        #'amp1 in pwr(mn)': pwr(m2),
        #'amp1 out pwr(fn)': pwr(s3),
        #'amp1 out pwr(mn)': pwr(m3),
        #'amp1 out ase(fn)': ase(s3),
        #'amp1 out ase(mn)': ase(m3),
        #'amp1 out nli(fn)': nli(s3),
        #'amp1 out nli(mn)': nli(m3),
        #'r2 drop(fn)': pwr(s4),
        #'r2 drop(mn)': pwr(m4)
        }, 'Single Span Test')


### 2. Dual spans with intermediate passthrough ROADM

def dualspantest():
    """Simple signal path:
       channels -> r1 -75km/amp-> r2 -75km/amp-> r3 """

    # Functional version
    channels = set(range(1,90))
    s0 = createSignals({ch:-9.0*dBm for ch in channels})
    # ROADM1
    s1, _drop = roadmOutput(
        mux={'add':s0, 'levelto': None},
        boost={'gtarg':4.5*dB, 'wdg':flatWDG})
    # Span1 + Amp1
    s2 = fiberOutput(s1, 75)
    s3 = edfaAdjustedOutput(s2, gtarg=75*.22*dB, wdg=wdg1)
    # ROADM2
    s4, _drop = roadmOutput(
        s3, demux={'through':channels},
        mux={'levelto': -4.5*dBm, 'headroom':1.0*dB},
        boost={'gtarg':9.0*dB, 'wdg':flatWDG})
    # Span2 + amp2
    s5 = fiberOutput(s4, 75)
    s6 = edfaAdjustedOutput(s5, gtarg=75*.22*dB, wdg=wdg1)
    # ROADM3
    _lineout, s7 = roadmOutput(s6, demux={'drop':channels})

    # Mininet-Optical simulated version
    msignals = run2(net2())
    m1 = msignals['r1']
    m3 = msignals['amp1']
    m4 = msignals['r2']
    m6 = msignals['amp2']
    m7 = msignals['r3']

    # Comparison
    plotChannelPower({
        'r1 output(fn)': pwr(s1),
        'r1 output(mn)': pwr(m1),
        'amp1 out/r2 in(fn)': pwr(s3),
        'amp1 out/r2 in(mn)': pwr(m3),
        'r2 output(fn)': pwr(s4),
        'r2 output(mn)': pwr(m4),
        #'amp2 output(fn)': pwr(s6),
        #'r3 output(fn)': pwr(s7),
        #'r3 ase(fn)': ase(s7),
        }, 'Dual span test')


###  Mininet-Optical network topologies (simulation mode)

# Port numbers for Mininet-Optical
LINEIN, LINEOUT = 0, 1
ADD, DROP, RX, TX = 100, 200, 300, 400

def net1():
    "net1: single span mininet-optical network"

    net = Network()

    channels = set(range(1,TXCOUNT+1))

    # Helpful shortcuts used below
    term, roadm, amp = (net.add_lt, net.add_roadm, net.add_amplifier)
    L, span  = net.add_link, partial(makespan, net)
    outm, inm = {'monitor_mode':'out'}, {'monitor_mode':'in'}
    aconf = {'monitor_mode':'out', 'wdg_id':'wdg1'}

    # Nodes: t1, r1, r2
    t1 = term('t1', [Tx(i, f'tx{i}', 0*dBm) for i in channels])
    t2 = term('t2', [Tx(i, f'tx{i}', 0*dBm) for i in channels], **inm)
    r1 = roadm('r1',
               reference_power_dBm=0.0*dBm,
               boost=amp('b1', target_gain=4.5*dB, wdg_id='linear'),
               insertion_loss_dB=4.5*dB, **outm)
    r2 = roadm('r2', preamp=None, boost=None, **outm)

    # Uplinks and downlinks
    for ch in channels:
        L(t1, r1, TX+ch, ADD+ch, spans=[span(.001)])
        L(r2, t2, DROP+ch, RX+ch, spans=[span(.001)])

    # Fiber span and compensating amplifier
    length = 75  # km !!!
    spans = [span(length, 'amp1', target_gain=length*.22*dB, **aconf)]
    L(r1, r2, LINEOUT, LINEIN, spans=spans)

    return net


def run1(net):
    """Configure and run net1, returning input and output signals
       for all nodes with attached monitors"""

    # ROADMs: r1 adds channels; r2 drops them
    r1, r2 = net.roadms
    for ch in range(1,TXCOUNT+1):
        r1.install_switch_rule(ADD+ch, LINEOUT, [ch])
        r2.install_switch_rule(LINEIN, DROP+ch, [ch])

    # Terminals: t1 is uplink; t2 is downlink
    t1, t2 = net.line_terminals
    for ch in range(1, TXCOUNT+1):
        t1.assoc_tx_to_channel(
            t1.id_to_transceivers[ch], ch, out_port=TX+ch)
        t2.assoc_rx_to_channel(
            t2.id_to_transceivers[1], ch, in_port=RX+ch)

    # Turn on terminals/transceivers
    for t in t1, t2:
        t.turn_on()

    # Return input and output signals in SigState format
    return [{node.name: mntosigstate(node, mode)
            for node in net.name_to_node.values()
                 if hasattr(node, 'monitor')}
            for mode in ('in', 'out')]



def net2():
    "net2: dual span/3-ROADM mininet-optical network"

    net = Network()

    channels = set(range(1,91))

    # Helpful shortcuts used below
    term, roadm, amp = (net.add_lt, net.add_roadm, net.add_amplifier)
    L, span  = net.add_link, partial(makespan, net)
    outm, inm = {'monitor_mode':'out'}, {'monitor_mode':'in'}
    aconf = {'monitor_mode':'out', 'wdg_id':'linear'}

    # Nodes: t1, r1, r2, r3, t3
    t1 = term('t1', [Tx(i, f'tx{i}', 0*dBm) for i in channels])
    t3 = term('t3', [Tx(i, f'tx{i}', 0*dBm) for i in channels], **inm)
    rparams = {'reference_power_dBm':0*dBm, 'insertion_loss_dB':9*dB}
    for i in range(1, 4):
        roadm(f'r{i}', **rparams,
              boost=amp(f'b{i}', target_gain=9*dB, wdg_id='wdg1'),
              **outm)

    # Uplinks and downlinks
    r1, r2, r3 = net.roadms
    for ch in channels:
        L(t1, r1, TX+ch, ADD+ch, spans=[span(1*m)])
        L(r3, t3, DROP+ch, RX+ch, spans=[span(1*m)])

    # Fiber span and compensating amplifier
    length = 75  # km !!!
    spans1 = [span(length, 'amp1', target_gain=length*.22*dB, **aconf)]
    L(r1, r2, LINEOUT, LINEIN, spans=spans1)
    spans2 = [span(length, 'amp2', target_gain=length*.22*dB, **aconf)]
    L(r2, r3, LINEOUT, LINEIN, spans=spans2)

    return net


def run2(net):
    "Configure and run net1, returning output signals"

    # ROADMs: r1 adds channels; r2 drops them
    r1, r2, r3 = net.roadms
    for ch in range(1,91):
        r1.install_switch_rule(ADD+ch, LINEOUT, [ch])
        r2.install_switch_rule(LINEIN, LINEOUT, [ch])
        r3.install_switch_rule(LINEIN, DROP+ch, [ch])

    # Terminals: t1 is uplink; t3 is downlink
    t1, t3 = net.line_terminals
    for ch in range(1, 91):
        t1.assoc_tx_to_channel(
            t1.id_to_transceivers[ch], ch, out_port=TX+ch)
        t3.assoc_rx_to_channel(
            t3.id_to_transceivers[1], ch, in_port=RX+ch)

    # Turn on terminals/transceivers
    for t in t1, t3:
        t.turn_on()

    # Return output signals in SigState format
    return {node.name: mntosigstate(node)
            for node in net.name_to_node.values()
            if hasattr(node, 'monitor')}



# Helper function for Mininet-Optical simulated topologies

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


### More tests TBD

def multiplespantest():
    "3. Validate multiple spans with compensating amplifiers"

def singleroadmtest():
    "4. validate single roadm through path"

def multiroadmtest():
    "5. validate multiple roadm through path"

def adddroptest():
    "5. validate add/drop paths"

def endtoendtest():
    "7. validate covert comms topology end-to-end"


### Do it

if __name__ == '__main__':

    Node.debugger = False
    singlespantest()

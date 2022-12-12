#!/usr/bin/python3

"""
fibertest.py: simple fiber test

Test Mininet-Optical fiber output vs. expected
output calculated by functional model.

"""

from simfunctions import (
    createSignals, fiberOutput, Sigstate, edfaAdjustedOutput,
    edfaAseNoise, mininetOpticalMeanGain, edfaAseNoiseWrong,
    flatWDG)


from mnoptical.network import Network
from mnoptical.node import LineTerminal, Transceiver as Tx
from mnoptical.link import Span as Fiber, SpanTuple as Segment

from functools import partial

### Constants

dB = dBm = 1.0

LINEIN, LINEOUT = 0, 1
TX, RX = 100, 200
TxCount = 1


### SIMPLE EDFA TEST


"""
Unfortunately it's hard to test fiber in isolation in
Mininet-Optical, but we can test an EDFA with a single
channel and in a ROADM.
"""

def check(ch, mn, fn, name, field, epsilon=1e-16):
    """Check mn vs. fn signals
       mn: minine-optical signals
       fn: functional model signals
       name: name of signal set
       field: signal component to compare
       epsilon: error/accuracy threshold"""
    m = getattr(mn[ch], field)
    f = getattr(fn[ch], field)
    error = abs(m - f)
    assert error < epsilon, (
        f'Mininet-Optical {name} {field} {m} '
        f' diverges from expected {f} by '
        f'{error:.2e} > {epsilon:.2e}')


def edfaSingleWavelengthTest(ch=1, pwr=0*dBm, gain=3*dB,
                             length_km=25):
    "Basic test of a single wavelength through an EDFA"

    # Functional version
    fedfain = createSignals({ch: pwr})
    eparams = dict(wdg=flatWDG, meanfn=mininetOpticalMeanGain,
                   asefn=edfaAseNoiseWrong)
    fedfaout = edfaAdjustedOutput(fedfain, gain, **eparams)
    ffiberin = fedfaout
    ffiberout = fiberOutput(ffiberin, length_km, srs=None)

    # Mininet-Optical simulated version
    # We connect the EDFA directly to the TX port by
    # specifying it as a boost amplifier for the attached
    # link.
    net = Network()
    t1 = net.add_lt(
        't1', transceivers=[Tx(ch, 'tx1', pwr)], monitor_mode='out')
    t2 = net.add_lt(
        't2', transceivers=[Tx(ch, 'tx1', pwr)], monitor_mode='in')
    e1 = net.add_amplifier('e1', target_gain=gain, monitor_mode='out')
    span = Segment(Fiber(length=length_km), amplifier=None)
    net.add_link(t1, t2, TX+ch, RX+ch, boost_amp=e1, spans=[span])
    t1.assoc_tx_to_channel(t1.transceivers[0], ch, out_port=TX+ch)
    t2.assoc_rx_to_channel(t2.transceivers[0], ch, in_port=RX+ch)
    t1.turn_on()

    medfain = mntosigstate(t1)
    medfaout = mntosigstate(e1)
    mfiberin = medfaout
    mfiberout = mntosigstate(t2)

    print(fedfain)
    print(medfain)
    print(fedfaout)
    print(medfaout)
    print(ffiberout)
    print(mfiberout)

    # Cross-check EDFA input and output signal values
    for field in 'pwr', 'ase', 'nli':
        check(ch, medfain, fedfain, 'EDFA input', field)
        check(ch, medfaout, fedfaout, 'EDFA output', field)



### SIMPLE FIBER TEST



def basicfibertest(length_km=50):
    "Basic propagation test through length of fiber"

    # Functional version
    channels = {ch:0*dBm for ch in range(1, TxCount+1)}
    ffiberin = createSignals(channels)
    ffiberout = fiberOutput(ffiberin, length_km, srs=None)

    # Mininet-Optical version
    net = net1()
    run1(net)

    nodes = net.name_to_node
    mfiberin = mntosigstate(nodes['r1'])
    mfiberout = mntosigstate(nodes['amp1'])
    epsilon = 1e-16


    print(mfiberin)
    print(mfiberout)

    # Compare fiber input and output signals
    for ch in channels:
        check(ch, mfiberin, ffiberin, 'fiber input', 'pwr')
        check(ch, mfiberout, ffiberout, 'fiber output', 'pwr')
        check(ch, mfiberin, ffiberin, 'fiber input', 'ase')
        check(ch, mfiberout, ffiberout, 'fiber output', 'ase')
        check(ch, mfiberin, ffiberin, 'fiber input', 'nli')
        check(ch, mfiberout, ffiberout, 'fiber output', 'nli')

# Port numbers for Mininet-Optical
LINEIN, LINEOUT = 0, 1
ADD, DROP, RX, TX = 100, 200, 300, 400

def net1():
    "net1: single span mininet-optical network"

    net = Network()

    channels = set(range(1,TxCount+1))

    # Helpful shortcuts used below
    term, roadm, amp = (net.add_lt, net.add_roadm, net.add_amplifier)
    L, span  = net.add_link, partial(makespan, net)
    outm, inm = {'monitor_mode':'out'}, {'monitor_mode':'in'}
    aconf = {'monitor_mode':'out', 'wdg_id':'wdg1'}

    # Nodes: t1, r1, r2
    t1 = term('t1', [Tx(i, f'tx{i}', 0*dBm) for i in channels])
    t2 = term('t2', [Tx(i, f'tx{i}', 0*dBm) for i in channels], **inm)

    # We're faking out the ROADM here
    r1 = roadm('r1', preamp=None, boost=None,
               reference_power_dBm=0.0*dBm,
               insertion_loss_dB=0.0*dB, **outm)
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
    for ch in range(1,TxCount+1):
        r1.install_switch_rule(ADD+ch, LINEOUT, [ch])
        r2.install_switch_rule(LINEIN, DROP+ch, [ch])

    # Terminals: t1 is uplink; t2 is downlink
    t1, t2 = net.line_terminals
    for ch in range(1, TxCount+1):
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
    edfaSingleWavelengthTest()

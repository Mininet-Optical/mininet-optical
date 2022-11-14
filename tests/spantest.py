#!/usr/bin/env python3

"""
Test propagation across multiple fiber spans

We want to make sure that signals are
propagating properly through all of the segments.
"""

from mnoptical.network import Network
from mnoptical.link import Span, SpanTuple
from mnoptical.node import Amplifier, Transceiver as Tx
from mnoptical.units import abs_to_db

km = dB = dBm = 1.0
m = .001

# Helper functions

ampcount = 0
def span(length, gain=None):
    "Return a fiber segment of the given length with a compensating amp"
    global ampcount, net
    if gain is None: amp = None
    else:
        ampcount += 1
        amp = net.add_amplifier(
            f'amp{ampcount}', target_gain=gain, monitor_mode='out')
    return SpanTuple(Span(length=length, wd_loss='linear'), amp)

def config(t, txnum, ch, inport, outport):
    "Configure tx/rx on LineTerminal t"
    tx = rx = t.transceivers[txnum]
    t.assoc_tx_to_channel(tx, ch, out_port=outport)
    t.assoc_rx_to_channel(rx, ch, in_port=inport)

# Parameters
segcount = 10  # Number of link segments
outport, inport = 0, 1  # Port numbers

# Create network
net = Network()
t1 = net.add_lt('t1', transceivers=[Tx('tx1',0*dBm)])
t2 = net.add_lt('t2', transceivers=[Tx('tx2',0*dBm)])
boost1 = Amplifier('boost1', target_gain=0*dB)
boost2 = Amplifier('boost2', target_gain=0*dB)
spans1 = list(span(1*km) for i in range(segcount))
spans2 = list(span(1*km) for i in reversed(range(segcount)))
net.add_link(t1, t2, outport, inport, boost_amp=boost1, spans=spans1)
net.add_link(t2, t1, outport, inport, boost_amp=boost2, spans=spans2)

# Configure and run
config(t1, txnum=0, ch=1, inport=inport, outport=outport)
config(t2, txnum=0, ch=1, inport=inport, outport=outport)
t1.turn_on()
t2.turn_on()

# Examine span signals
errors = 0
instate, outstate = [], []

for link in net.links:
    for span, amp in link.spans:
        signals = span.optical_signals
        sigcount = len(signals)
        if sigcount != 1:
            print(f'Error: {span}: {sigcount} != 1')
            errors += 1
        sig = signals[0]
        if sig.index != 1:
            print(f'Error: {span}: channel index != 1')
            errors += 1
        # Check attenuation
        inwatts = sig.loc_in_to_state[span]
        outwatts = sig.loc_out_to_state[span]
        indbm = abs_to_db(1e3*inwatts['power'])
        outdbm = abs_to_db(1e3*outwatts['power'])
        loss = indbm - outdbm
        print(f'{span}: power in:{indbm:.2f}dBm out:{outdbm:.2f}dBm'
              f' loss:{loss:.2f}dB')
        if abs(loss - .22) > 1e-6:
            print(f'bad loss {loss} should be .22')
            errors += 1

exit(errors)

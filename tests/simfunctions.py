"""
simfunctions.py:

This is a simple *functional* implementation of the
simulation model used by Mininet-Optical, including
the GN (Gaussian Noise) model and a simple model for
SRS (Stimulated Rama Scattering) effects.

Core idea:

This implementation is purely *functional*. Each component
is modeled as a function that takes input signals (including
control signals) and returns output signals.

Inviolable rules for model functions:

1. Functions may *never* modify their input parameters
   (even when they are mutable Python objects.)

2. Function state may *never* be retained across calls.
"""

from collections import namedtuple
from math import e, pi, exp, log10, asinh
from mnoptical.edfa_params import ripple_functions

### Units

# Note one gotcha is that node.Span takes length in
# km rather than meters; we should probably change
# that lest it lead to errors, although
# there is a risk of breaking existing code and
# tests.

THz = 1e12
GHz = 1e9
dB = dBm = 1.0
um = 1e-6
cm = 1e-2
m = 1
km = 1e3
W = 1.0

### Constants

Planck = 6.62607015e-34  # Planck's constant  (J/Hz?)
C = 299792458.0   # speed of light (m/s)

### Helper functions

def dbtolinear(dbvalue):
    "Convert power dB value to linear factor"
    return 10 ** (dbvalue/10.0)

def lineartodb(linearvalue):
    "Convert linear factor to power dB value"
    if linearvalue == 0: return float('-inf')
    return 10 * log10(linearvalue)

def dbmtowatts(dbmvalue):
    "Convert dBm value to Watts"
    return dbtolinear(dbmvalue) * 1e-3

def wattstodbm(wvalue):
    "Convert watts value to dBm"
    return lineartodb(wvalue*1e3)

def chtofreq(ch):
    """Convert Mininet-Optical/ROADM-20/ITU 50 GHz
       channel grid index to frequency in Hz."""
    # Channel 0 frequency and channel width in GHz
    ch0 = 191300
    width = 50
    return (ch0 + ch*width)*GHz


### Signal state representation

# Signal state Sigstate ('sig') consists of:
# pwr: signal power in watts
# ase: ASE noise in watts
# nli: GN model NLI noise component in watts

Sigstate = namedtuple('sig', 'pwr ase nli')

def createSignals(channels):
    """Return a signal spectrum
       channels: {ch: power in dBm}
       returns: {ch: Sigstate(pwr in watts)}"""
    return {ch: Sigstate(pwr=dbmtowatts(pdbm),ase=0,nli=0)
            for ch, pdbm in channels.items()}

# Signal spectrum helper functions

def adjust(signals, gain):
    "Adjust (amplify/attenuate) signals by gain/loss in dB"
    if gain == 0*dB: return signals  # bypass
    g = dbtolinear(gain)
    return {ch:
            Sigstate(pwr=s.pwr*g, ase=s.ase*g, nli=s.nli*g)
            for ch, s in signals.items()}

def attenuate(signals, loss):
    "Attenuate signals by loss in dB"
    assert loss >= 0
    return adjust(signals, -loss)



# Selector functions (useful for plotting)

def selectdbm(signals, field):
    "Return {ch: field in dBm} for signals"
    return {ch:wattstodbm(getattr(s, field))
            for ch,s in signals.items()}

def pwr(sigs): return selectdbm(sigs, 'pwr')
def ase(sigs): return selectdbm(sigs, 'ase')
def nli(sigs): return selectdbm(sigs, 'nli')


### Fiber span model


# SRS effect model


SmfEffArea = 80 * um * um  # SMF effective area
SmfRamanGain = 7.0 * 1e-12 * cm/W  # SMF Raman gain
RamanAmpBand = 15 * THz  # Raman amplification band
RamanCoeff1 = SmfRamanGain / (2 * SmfEffArea * RamanAmpBand)

def srs_effect_model1(signals, length, beta=RamanCoeff1):
    """SRS model from [Zirngibl98:eq7,8]
       length: effective fiber length in KILOMETERS (!!!)
       beta: raman coefficient
       returns: {ch: linear gain}"""
    chmin, chmax = min(signals, default=0), max(signals, default=1)
    fmin, fmax = chtofreq(chmin), chtofreq(chmax)
    # XXX: do we need to consider noise power?!?!
    tpower = sum((s.pwr for s in signals.values()), 0)
    output = {}
    # Equation
    term1 = beta * tpower * length * (fmax-fmin)
    r2 = exp(term1) - 1  # denominator
    if r2 == 0: return signals
    output = {}
    for ch, s in signals.items():
        f = chtofreq(ch)
        r1 = term1 * exp(beta * tpower * length * (f-fmin))
        r = r1/r2
        output[ch] = Sigstate(pwr=s.pwr*r, ase=s.ase*r, nli=s.nli*r)
    return output



# GN model/NLI compensation factor


### BL NOTES:
###
### 1. I simplified this somewhat from Alan's code by
###    assuming a standard channel bandwidth==symbol rate.
###
### 2. I think we should really verify this against the
###    original GN model equations rather than trusting
###    Alan's interpretation of the GNpy code.

pi2 = pi*pi



def calcbeta2(dispersion=1.67e-05, ref_wavelength=1550e-9):
    """Returns beta2 from dispersion parameter.
    Dispersion is entered in ps/nm/km.
    Translated from the GNPy project source code
    :param ref_wavelength: can be a numpy array; default: 1550nm
    """
    D = abs(dispersion)
    b2 = -(ref_wavelength ** 2) * D / (2 * pi * C)  # 10^21 scales [ps^2/km]
    return b2  # s/Hz/m


def gn_model(signals, nonlinear_coefficient, alpha,
             effective_length, bw):
    """
    Original comment (A.Diaz):
    Computes the nonlinear interference power on a single carrier.
    Translated from the GNPy project source code
    The method uses eq. 120 from arXiv:1209.0394.
    :return: carrier_nli: the amount of nonlinear interference in W on the carrier under analysis
    """
    nli = {}
    gamma = nonlinear_coefficient
    asymptotic_length = 1 / (2 * alpha)
    bw_cut = bw_ch = bw
    beta2 = calcbeta2()
    # cut/sut == channel/signal under test
    for cut, sut in signals.items():
        g_cut = sut.pwr / bw_cut  # G is the flat PSD per channel power (per polarization)
        g_nli = 0
        for ch, sig in signals.items():
            g_ch = sig.pwr / bw  # G is the flat PSD per channel power (per polarization)
            psi = psi_factor(cut, ch, bw_cut, bw_ch, beta2, asymptotic_length)
            g_nli += g_ch*g_ch * g_cut * psi
            g_nli *= ((16/27) * (gamma * effective_length)**2 /
                      (2*pi * abs(beta2) * asymptotic_length))
        nli[cut] = g_nli * bw_cut
    return nli



def psi_factor(carrier, interfering_carrier, bw_cut, bw_ch, beta2, asymptotic_length):
    """
    Original comment (A.Diaz):
    Calculates eq. 123 from `arXiv:1209.0394 <https://arxiv.org/abs/1209.0394>`__
    Translated from the GNPy project source code
    """
    if carrier == interfering_carrier:  # SCI, SPM
        psi = asinh(0.5 * pi2 * asymptotic_length * abs(beta2) * bw_cut*bw_cut)
    else:  # XCI, XPM
        delta_f = chtofreq(carrier) - chtofreq(interfering_carrier)
        psi = asinh(pi2 * asymptotic_length * abs(beta2) *
                    bw_cut * (delta_f + 0.5 * bw_ch))
        psi -= asinh(pi2 * asymptotic_length * abs(beta2) *
                     bw_cut * (delta_f - 0.5 * bw_ch))
    return psi



def fiberOutput(signals, length, srs=srs_effect_model1, bw=32*GHz):
    """Return output signals after passing through fiber span
       signals: fiber span input signals
       length: length of fiber in KILOMETERS (!!)"""
    # NOTE: Length is currently in kilometers as in
    # link.Span; however this has led to the unfortunate
    # situation of multiple km units, so it should probably
    # be changed to meters here and elsewhere.
    length = length * km
    # These values are ported from link.Span
    fiber_attenuation = .22*dB / km
    # alpha: linear value fiber attenuation
    alpha = fiber_attenuation / (20 * log10(e))
    effective_length = ((1 - exp(-2 * alpha * length)) /
                         (2 * alpha))
    # gamma: fiber non-linearity coefficient [W^-1 km^-1]
    nonlinear_coefficient = 1.27 / km


    # SRS effect if any
    if srs: signals = srs(signals, length )

    # GN model NLI compensation
    nli = gn_model(signals, nonlinear_coefficient, alpha=alpha,
                   effective_length=effective_length, bw=bw)


    # Apply fiber attenuation
    attenuationdb = length * fiber_attenuation
    att = dbtolinear(-attenuationdb)
    # WIP - ignore GN model until fixed
    output = {ch: Sigstate(s.pwr*att, s.ase*att, 0*nli[ch]*att)
              for ch, s in signals.items()}

    return output


### EDFA model
### Based on Alan's thesis section 3.3

def EdfaAseNoise(ase, freq, glin, nf, bw):
    """
    Return EDFA Amplified Spontaneous Emission Noise output power (W)
    Equation source: [Diaz21:eq3.7], [Kumar/Deen14:eqA.38]
    ASE: input ASE noise (W)
    glin: system power gain (linear)
    nf: noise/spontaneous emission/population inversion factor (float)
    freq: center frequency of signal
    bw: bandwidth (we use channel bandwidth in our model?)
    """
    return ase * glin + nf * Planck * freq * (glin-1.0) * bw


def flatWDG(ch, signals):
    """Flat (0dB) wavelength dependent gain function
       (NB: input is channel, not wavelength)
       ch: channel
       signals: amplifier input signals
       returns: linear power gain factor (1.0)"""
    return 1.0


def wdg1(ch, signals, profile='wdg1'):
    """Return static WDG from Mininet-Optical's
       'wdg1' ripple function
       profile: WDG profile name ('wdg1')
       returns: linear power gain factor """
    # Assume entry 0 corresponds to channel 1
    return dbtolinear(ripple_functions[profile][ch-1])


def nf55(ch):
    """Default static noise factor 5.5
       used in Mininet-Optical (???)"""
    return 5.5


def edfaOutput(signals, gsys, wdg, nf, bw):
    """Return EDFA output for given input
       signals: {ch: Sigstate} (power, ase noise, nli in watts)
       gsys: system (nominal) gain setting in dB
       wdg: wavelength dependent gain function
            (ch, signals)->linear gain factor
       nf: noise figure array (units???)
       bw: EDFA configured bandwidth in Hz
       returns: {ch: Sigstate}"""
    Glin = dbtolinear(gsys)
    output = {ch:
              Sigstate(
                  pwr = s.pwr * Glin * wdg(ch, signals),
                  ase = EdfaAseNoise(
                      s.ase, chtofreq(ch), Glin, nf(ch), bw),
                  nli = 0  # ignore GN model NLI component for now
              )
              for ch, s in signals.items()}
    return output


def edfaAdjustedGain(signals, gcur, gtarg, **params):
    """
    Perform a single iteration of the EDFA constant
    gain algorithm, and return the new system gain
    (as well as the output signals, so that we don't have
    to recalculate them.)

    The system gain is the nominal gain of the amplifier,
    adjusted to (hopefully) bring the actual mean gain
    closer to the desired target gain.

    gcur: current system/nominal gain setting in dB
    gtarg: desired target gain in dB
    signals: input signals
    params: EDFA parameters
    (channel, signals) -> linear power gain factor

    We return a tuple of:
    ( gnew = gcur + (gtarg - gmean), output signals)

    where gtarg is the target gain and gmean is the gain for
    the approximated total signal + ase power passing through
    the amplifier with the current gain gcur. The total
    power is approximated by adding up the individual channel
    signal and noise power values.

    This follows [Diaz21] as well as the Mininet-Optical code.
    """
    print('signals', signals)
    # Total input power approximation
    Tin = sum(sig.pwr + sig.ase for sig in signals.values())
    print('Tin', Tin)
    # Total output power approximation
    output = edfaOutput(signals, gcur, **params)
    Tout = sum(sig.pwr + sig.ase for sig in output.values())
    # Mean unadjusted power gain approximation (dB)
    if Tin == 0: return gcur, signals  # Avoid division by zero
    gmean = lineartodb(Tout/Tin)
    # System gain is adjusted up or down
    gnew = gcur + (gtarg - gmean)
    return gnew, output


### Question: is the 32 GHz default bandwidth correct for
### this equation?

def edfaAdjustedOutput(signals, gtarg=0*dB, wdg=flatWDG, nf=nf55, bw=32*GHz,
                       iterations=1):
    """Return EDFA output for given input,
       with system gain adjusted by the automatic
       constant gain control algorithm.
       signals: {ch: Sigstate} (power, ase noise, nli in watts)
       gtarg: desired target gain in dB
       wdg: wavelength dependent gain function
            (ch, signals)->linear gain factor
       nf: noise figure array
       bw: EDFA configured bandwidth in THz
       iterations: number of iterations to run
       returns: {ch: Sigstate}"""
    # Start system gain setting at target gain
    gcur = gtarg
    # Run automatic gain control algorithm
    for _ in range(iterations):
        gnew, signals = edfaAdjustedGain(signals, gcur, gtarg,
                                         wdg=wdg, nf=nf, bw=bw)
    return signals


### ROADM and WSS model

# Note: we may want to rethink this to enable n-degree ROADMs...
# However starting with a single line input/output pair is
# simpler

def demuxOutput(signals, through={}, drop={},
                loss=4.5*dB):
    if loss: signals = attenuate(signals, loss)
    passed, dropped = {}, {}
    for ch, sig in signals.items():
        if ch in through: passed[ch] = sig
        elif ch in drop: dropped[ch] = sig
    return passed, dropped


### BL: It turns out that power leveling is kind of
### subtle. I haven't seen a definitive specification
### of the algorithm, so this is my attempt at it.
### Basically we squash the spectrum by up to a certain
### amount and then lower any channel which is above
### the target operating power.
###


def limit(minval, x, maxval):
    "Limit x to the range [minval, maxval] inclusive"
    return max(minval, min(x, maxval))


def squashpower(signals, headroom=0.0*dB):
    """Flatten spectrum by attenuating by up to headroom dB:
       Any signal with power higher than the lowest
       power may be attenuated by anywhere from 0..headroom dB,
       to bring it closer to the lowest signal power;
       this "boosts" the lowest signal closer to the rest."""
    if not headroom or not signals: return signals
    # Compute total channel power in dBm
    chpwr = {ch:wattstodbm(s.pwr + s.ase) for ch, s in signals.items()}
    # If full headroom isn't needed, reduce it
    mindbm = min(chpwr.values())
    maxdelta = max(p-mindbm for p in chpwr.values())
    maxsquash = limit(0, maxdelta, headroom)
    # Squash spectrum
    output = {}
    for ch, p in chpwr.items():
        squash = limit(0, p-mindbm, maxsquash)
        if ch==1:
            print(0, p-mindbm, maxsquash)
        output[ch] = (attenuate({ch:signals[ch]}, squash))[ch]
    return output


def levelpower(signals, levelto=0.0*dBm, headroom=1.0*dB,
                  maxatten=30*dB, channelmap='all'):
    """Channel power leveling algorithm

       signals: input signals
       levelto: target output power dBm
       headroom: "boost" lowest signal by up to this amount
       maxatten: maximum attenuation
       channelmap: channels to consider or 'all'

       returns: power-leveled signals"""
    # Squash spectrum by up to headroom amount
    signals = squashpower(signals, headroom)
    # Attenuate any channels that are above levelto target
    output = {}
    for ch, sig in signals.items():
        if channelmap=='all' or ch in channelmap:
            pdbm = wattstodbm(sig.pwr + sig.ase)
            excess = limit(0, pdbm-levelto, maxatten)
            sig = attenuate({ch:sig}, excess)[ch]
        output[ch] = sig
    return output


def muxOutput(signals, add={}, loss=4.5*dB, levelto=None,
              headroom=0.0*dB):
    """Compute MUX WSS output
       signals: passthrough signals
       add: add signals
       loss: WSS loss in dB
       autolevel: if not None, level output to specified dBm"""
    # Multiplex signals together
    assert not add or set(signals) - set(add) == set(), (
        'MUX line input/add signals must not overlap')
    print('mux add', add.get(1, None))
    output = signals.copy()  # must not change input values
    output.update(add)  # OK since sigstate is immutable
    output = attenuate(output, loss)
    output = levelpower(output, levelto)
    return output


def roadmOutput(lineSignals={}, lineInputLoss=0*dB, preamp={}, mux={},
                passLinkLoss=0*dB, demux={}, boost={},
                lineOutputLoss=0*dB):
    """
    Calculate ROADM output for through path from Line Input
    to Line Output --
      line input -> preamp -> demux -> mux -> line output

    lineInputLoss: input loss (if any) for line input signals
    preamp: preamp parameters, or None of no preamp,
    mux: mux WSS parameters,
    passLinkLoss: loss (if any) between demux and mux
    demux: demux WSS parameters,
    boost: boost amp params, or None if no boost amp
    lineOutputLoss: output loss (if any) for line output signals

    Notes:
    - all gain/loss is in dB
    - add signals are passed as mux={'add':sigs}

    Returns: line output, drop signals
    """
    s = lineSignals
    print('line input', s)
    # Line input loss
    s = attenuate(s, lineInputLoss)
    # Preamp if present
    if preamp is not None: s = edfaAdjustedOutput(s, **preamp)
    # Demux WSS
    s, dropSignals = demuxOutput(s, **demux)
    print('demux output', s, dropSignals)
    # Passthrough coupling loss
    s = attenuate(s, passLinkLoss)
    # Mux WSS
    s = muxOutput(s, **mux)
    # Boost if any
    if boost is not None: s = edfaAdjustedOutput(s, **boost)
    # Line output loss
    s = attenuate(s, lineOutputLoss)
    lineOutput = s
    return lineOutput, dropSignals


### Simple plotting

def plotChannelPower(spectra, title='Channel Power (dBm)'):
    """Simple channel power spectrum plot (dBm)
       spectra: {signame: {ch:dBm...}}"""
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots()
    for name, spectrum in spectra.items():
        ax.scatter(spectrum.keys(), spectrum.values(),
                label=name)
    plt.title(title)
    ax.set_ylabel('dBm')
    ax.set_xlabel('channel')
    ax.legend()
    ax.grid()
    plt.show()

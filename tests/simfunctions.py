"""
simfunctions.py: optical modeling function library

This file is a simple *functional* (re)implementation of the
steady-state optical transmission physics simulation model used by
Mininet-Optical, including the GN-model (Gaussian Noise model) and a
simple model for SRS (Stimulated Raman Scattering) effects.

Optical signal and component models:

Signal state model/representation
- signal power, ASE noise power, NLI effects
- fixed ITU 50 GHz channel grid
- spectrum is {ch: (pwr, ase, nli) in watts}
- frequency <-> channel conversion functions

Fiber (SMF) model:
- fixed attenuation (.22 dB/km across all channels)
- SRS model
- GN-model for nonlinear interference (NLI) effects

Amplifier (EDFA) model:
- basic amplification and noise figure
- ASE noise model
- automatic constant gain control algorithms

Switching (WSS/ROADM) model:
- MUX and DEMUX WSS models
- optional preamp and boost amp
- simple switching model
- power leveling algorithms

Core idea:

This implementation is purely *functional*. Each component
is modeled as a function that calculates output signals as
a function of input signals and control signals, without
side-effects or retention of intermediate state.

The standard input and output signal state is a dict of
the form {ch: Sigstate}.

Inviolable rules for model functions:

1. Functions may *never* modify their input parameters
   (even when they are mutable Python objects.)

2. Function state may *never* be retained across calls.

"""

from mnoptical.edfa_params import ripple_functions

from collections import namedtuple
from math import e, pi, exp, log10, asinh, prod


### Units

# NB: One gotcha is that fiber length is specified in
# km rather than meters, following the GN model.
# Without accounting for proper dimensional analysis
# this is likely to lead to errors.

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
    return 10 ** (dbvalue/10)

def lineartodb(linearvalue):
    "Convert linear factor to power dB value"
    if linearvalue == 0: return float('-inf')
    return 10 * log10(linearvalue)

def dbmtowatts(dbmvalue):
    "Convert dBm value to Watts"
    return dbtolinear(dbmvalue) * .001

def wattstodbm(wvalue):
    "Convert watts value to dBm"
    return lineartodb(wvalue * 1000)

def chtofreq(ch):
    """Convert ITU/ROADM-20/Mininet-Optical fixed 50 GHz
       channel grid index to frequency in Hz."""
    # Channel 0 frequency and channel width in GHz
    ch0 = 191300
    width = 50
    return (ch0 + ch*width)*GHz


### Signal state representation

# Signal state Sigstate ('S') consists of:
# pwr: signal power in watts
# ase: ASE noise in watts
# nli: GN model NLI noise component in watts

Sigstate = namedtuple('S', 'pwr ase nli')
S = Sigstate   # abbreviation

def createSignals(channels):
    """Return a signal spectrum
       channels: {ch: power in dBm}
       returns: {ch: Sigstate(pwr in watts)}"""
    return {ch: S(dbmtowatts(pdbm), ase=0, nli=0)
            for ch, pdbm in channels.items()}

# Signal spectrum helper functions

def adjust(signals, gain):
    "Adjust (amplify/attenuate) signals by gain/loss in dB"
    g = dbtolinear(gain)
    return {ch: S(s.pwr*g, s.ase*g, s.nli*g)
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

def tpwr(signals):
    "Return signal + ase power"
    return {ch:s.pwr+s.ase
            for ch, s in signals.items()}

def ddelta(d1, d2):
    "Dictionary delta {ch: d2[ch]-d1[ch]}"
    result = { ch: d2[ch] - d1[ch]
               for ch in d1}
    return result

### Fiber span model


# SRS effect model


SmfEffArea = 80 * um * um  # SMF effective area
SmfRamanGain = 7.0 * 1e-12 * cm/W  # SMF Raman gain
RamanAmpBand = 15 * THz  # Raman amplification band
RamanCoeff1 = SmfRamanGain / (2 * SmfEffArea * RamanAmpBand)

def srs_effect_model1(signals, length,
                      beta=RamanCoeff1):
    """SRS model from [Zirngibl98:eq7,8]
       length: effective fiber length in KILOMETERS (!!!)
       beta: raman coefficient"""
    chmin, chmax = min(signals, default=0), max(signals, default=1)
    fmin, fmax = chtofreq(chmin), chtofreq(chmax)
    # XXX: do we need to consider noise power?!?!
    # It seems incorrect not to.
    tpower = sum((s.pwr for s in signals.values()), 0)
    output = {}
    # Equation
    # length is in km
    term1 = beta * tpower * length * (fmax-fmin)
    r2 = exp(term1) - 1  # denominator
    if r2 == 0: return signals.copy()
    output = {}
    for ch, s in signals.items():
        f = chtofreq(ch)
        r1 = term1 * exp(beta * tpower * length * (f-fmin))
        r = r1/r2
        output[ch] = S(s.pwr*r, s.ase*r, s.nli*r)
    return output



# GN model/NLI compensation factor


### BL NOTES:
###
### 1. I simplified this somewhat vs. mnoptical.node,
###    assuming a standard channel bandwidth==symbol rate.
###
### 2. I think we should really verify this against the
###    original GN model equations rather than trusting
###    Alan's interpretation of the GNpy code.

pi2 = pi*pi


def gn_model(signals, length_km, fiber_attenuation,
             nonlinear_coefficient=1.27, # /(W*km)
             bw=32*GHz, # ??? is this correct???
             # This should be 16.7 ps/(km*nm) for SMF
             # I don't see why it should be off by 1e6
             dispersion=1.67e-5, # SMF dispersion ps/(km*nm)
             ref_wavelength=1550e-9):
    """
    Original comment (A.Diaz):
    Computes the nonlinear interference power on a single carrier.
    (Originally) modeled on the GNPy project source code
    The method uses eq. 120 from arXiv:1209.0394.
    :return: {ch:nli} per-channel nonlinear interference value
    in W on the carrier under analysis
    """
    # alpha (field loss coefficient)
    # optical power attenuates as exp(-2*alpha*length)
    alpha = fiber_attenuation / (20 * log10(e))
    asymptotic_length = 1 / (2 * alpha)
    # BL: effective length is counterintuitive...
    effective_length = ((1 - exp(-2 * alpha * length_km)) /
                         (2 * alpha))
    print("effective length km", effective_length)
    print("asymptotic length km", asymptotic_length)
    # Note cut/sut == channel/signal under test
    bw_cut = bw_ch = bw
    gamma = nonlinear_coefficient
    # TODO: CHECK UNITS HERE
    D = abs(dispersion)
    beta2 = -(ref_wavelength ** 2) * D / (2 * pi * C) # ps^2/km
    print('beta2', beta2)
    # Constant term outside summation:
    const = ((16/27) * (gamma * effective_length)**2 /
             (2*pi * abs(beta2) * asymptotic_length))
    # Accumulate modeled NLI (pseudo?)power across all channels
    nli = {}
    for cut, sut in signals.items():
        # G is the flat PSD per channel power (per polarization) (??)
        # BL: apparently we are only modeling interference
        # between coherent signals, so we ignore noise power
        g_cut = sut.pwr / bw_cut
        g_nli = 0
        for ch, sig in signals.items():
            g_ch = sig.pwr / bw_ch
            psi = psi_factor(
                cut, ch, bw_cut, bw_ch, beta2, asymptotic_length)
            print("PSI FACTOR", psi)
            g_nli += (g_ch * g_ch) * g_cut * psi
        nli[cut] = const * g_nli * bw_cut
    return nli


def psi_factor(carrier, interfering_carrier, bw_cut, bw_ch,
               beta2, asymptotic_length):
    """
    Original comment (A.Diaz):
    Calculates eq. 123 from
    `arXiv:1209.0394 <https://arxiv.org/abs/1209.0394>`
    Translated from the GNPy project source code
    """
    print('PSI AL DF BW', asymptotic_length, bw_cut)
    # Self channel interference (SCI)
    if carrier == interfering_carrier:
        return asinh(0.5 * pi2 * asymptotic_length * abs(beta2)
                    * bw_cut*bw_cut)
    # Cross channel interference (XCI)
    delta_f = chtofreq(carrier) - chtofreq(interfering_carrier)
    return (asinh(pi2 * asymptotic_length * abs(beta2) *
                  bw_cut * (delta_f + 0.5 * bw_ch))
            - asinh(pi2 * asymptotic_length * abs(beta2) *
                    bw_cut * (delta_f - 0.5 * bw_ch)))


def fiberOutput(signals, length, srs=srs_effect_model1):
    """Return output signals after passing through fiber span
       signals: fiber span input signals
       length: length of fiber in KILOMETERS (!!)"""
    length_km = length
    fiber_attenuation=.22*dB # /km

    # GN model NLI compensation value
    nli = gn_model(signals, length_km, fiber_attenuation)
    # ??? Do we add in the NLI noise value from the GN-model
    # *before* attenuation like Mininet-Optical?!?!
    signals = {ch: S(s.pwr, s.ase, s.nli + nli[ch])
               for ch, s in signals.items()}

    # SRS effect if any
    if srs: signals = srs(signals, length_km )

    # Fiber attenuation
    attenuationdb = length * fiber_attenuation
    output = attenuate(signals, attenuationdb)

    return output


### EDFA model


def edfaAseNoise(ase, freq, glin, nf, bw):
    """
    Return EDFA Amplified Spontaneous Emission Noise output power (W)
    Equation source: [Diaz21:eq3.7], [Kumar/Deen14:eqA.38]
    ase: input ASE noise (W)
    glin: system power gain (linear)
    nf: noise figure in dB: 10^(nf/10) = inversion factor 2*nsp
    freq: center frequency of signal
    bw: bandwidth (we use channel bandwidth in our model?)
    """
    nflin = dbtolinear(nf)
    return ase * glin + nflin * Planck * freq * (glin-1.0) * bw


def edfaAseNoiseWrong(ase, freq, glin, nf, bw):
    """
    Seemingly incorrect version of ASE noise implemented in
    mininet-optical?
    """
    nflin = dbtolinear(nf)
    return ase * glin + nflin * Planck * freq * (glin) * bw


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
       returns: LINEAR power gain factor """
    # Assume entry 0 corresponds to channel 1
    return dbtolinear(ripple_functions[profile][ch-1])


def nf55(ch):
    """Default constant 5.5 dB EDFA noise figure,
       used in Mininet-Optical (and GNpy?)"""
    return 5.5*dB


def edfaOutput(signals, gsys, wdg, nf, bw, asefn):
    """Return EDFA output for given input;
       gsys: system (nominal) gain setting in dB
       wdg: wavelength dependent gain function
            (ch, signals)->linear gain factor
       nf: noise figure array (units???)
       bw: EDFA configured bandwidth in Hz"""
    output = {}
    for ch, s in signals.items():
        glin = dbtolinear(gsys) * wdg(ch, signals)
        output[ch] = S(
            pwr = glin * s.pwr,
            ase = asefn(
                s.ase, chtofreq(ch), glin, nf(ch), bw),
            nli = glin * s.nli
        )
    return output


def totalPowerGain(sigin, sigout):
    """Return total gain from input to output power, in dB
       NB: we *ignore* NLI power as apparently it is a
       compensation factor and not physical power. Real
       NLI is small so it should not make a huge difference."""
    # Total input/output power approximation
    # We sum up the channel powers; presumably this is
    # comparable to integrating the power spectral density
    Tin = sum(s.pwr + s.ase for s in sigin.values())
    Tout = sum(s.pwr + s.ase for s in sigout.values())
    return lineartodb(Tout/Tin) if Tin != 0 else None


def gmean(items):
    "Geometric mean"
    items = tuple(items)
    return prod(items)**(1/len(items))


def mininetOpticalMeanGain(sigin, sigout):
    """Mininet-Optical mean gain algorithm.
       Mininet-Optical calculates the gain as the ratio of the
       geometric mean SIGNAL output power to the geometric mean input power.
       ???: This seems non-physical. And why geometric mean???"""
    Min = gmean(s.pwr for s in sigin.values())
    Mout = gmean(s.pwr for s in sigout.values())
    return lineartodb(Mout/Min) if Min != 0 else None


### Question: is the 32 GHz default bandwidth correct for
### this equation?

def edfaAdjustedOutput(signals, gtarg=0*dB, wdg=flatWDG, nf=nf55,
                       bw=32*GHz, iterations=1,
                       meanfn=totalPowerGain, asefn=edfaAseNoise):
    """Return EDFA output for given input,
       with system gain adjusted by the automatic
       constant gain control algorithm.
       signals: {ch: Sigstate} (power, ase noise, nli in watts)
       gtarg: desired target gain in dB
       wdg: wavelength dependent gain function
            (ch, signals)->linear gain factor
       nf: noise figure function (dB)
       bw: EDFA configured bandwidth in THz
       iterations: number of iterations to run
       meanfn: function to calculate mean power gain
       asefn: ASE noise function"""
    # Start system gain setting at target gain
    gain = gtarg
    # Perform iterations of gain control algorithm
    params = dict(wdg=wdg, nf=nf, bw=bw, asefn=asefn)
    for _ in range(iterations):
        sigout = edfaOutput(signals, gain, **params)
        gmean = meanfn(signals, sigout)
        if gmean is None: break
        gain += gtarg - gmean
    return edfaOutput(signals, gain, **params)


### ROADM and WSS model

# Note: we may want to rethink this to enable n-degree ROADMs...
# However starting with a single line input/output pair is
# simpler.

def demuxOutput(signals, through={}, drop={},
                loss=4.5*dB):
    """Compute demux WSS output
       through: channel indices to pass
       drop: channel indices to drop"""
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
        output[ch] = (attenuate({ch:signals[ch]}, squash))[ch]
    return output


def levelPowerBL(signals, levelto=0.0*dBm, headroom=1.0*dB,
                  maxatten=30*dB, channelmap='all'):
    """My Own Channel power leveling algorithm
       levelto: target output power dBm
       headroom: "boost" lowest signal by *up to* this amount
       maxatten: maximum attenuation
       channelmap: channels to consider or 'all'"""
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


def alcatelLucentLevel(signals, levelto=0.0*dBm, headroom=3.0*dB,
                  maxatten=30*dB, channelmap='all'):
    """Alcatel-Lucent style power leveling algorithm:
       pre-attenuate by 3.0dB and then either increase or
       reduce attenuation to hit target output power.
       levelto: target output power dBm
       headroom: pre-attenuate all signals by this amount
       maxatten: maximum attenuation
       channelmap: channels to consider or 'all'"""
    # Attenuate any channels that are above levelto - headroom
    print("LEVELTO", levelto, "HEADROOM", headroom)
    levelto -= headroom
    output = {}
    for ch, sig in signals.items():
        if channelmap=='all' or ch in channelmap:
            pdbm = wattstodbm(sig.pwr + sig.ase)
            excess = limit(0, pdbm-levelto, maxatten)
            sig = attenuate({ch:sig}, excess)[ch]
        output[ch] = sig
    return output



def muxOutput(signals, add={}, loss=4.5*dB,
              levelpower=alcatelLucentLevel,
              levelto=0.0*dBm, **levelparams):
    """Compute MUX WSS output
       signals: passthrough signals
       add: add signals
       loss: WSS loss in dB
       levelpower: power leveling algorithm (alcatelLucentLevel)
       levelto: target output power in dBm
       **levelparams: other levelpower parameters"""
    # Multiplex signals together
    print('mux input', signals)
    assert not add or set(signals) - set(add) == set(), (
        'MUX line input/add signals must not overlap')
    print('mux add', add.get(1, None))
    output = signals.copy()  # must not change input values
    output.update(add)  # OK since sigstate is immutable
    output = attenuate(output, loss)
    print('attenuated by', loss, '->', output)
    if levelpower and levelto is not None:
        output = levelpower(output, levelto, **levelparams)
    print('leveled to', output)
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
    * all gain/loss is in dB *
    * add signals are passed as mux={'add':sigs} *

    Returns: line output, drop signals
    """
    s = lineSignals
    # Line input loss
    s = attenuate(s, lineInputLoss)
    print('attenuated line input', s)
    # Preamp if present
    if preamp is not None: s = edfaAdjustedOutput(s, **preamp)
    # Demux WSS
    s, dropSignals = demuxOutput(s, **demux)
    # Passthrough coupling loss
    s = attenuate(s, passLinkLoss)
    print('passthrough', s)
    # Mux WSS
    s = muxOutput(s, **mux)
    print('mux output', s)
    # Boost if any
    if boost is not None: s = edfaAdjustedOutput(s, **boost)
    print('boost output', s)
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

#!/usr/bin/python3

"""
pqtest.py:

Test GN model equations using PhysicalQuantities package.

For this example, we use a single wavelength,
so we are just looking at self channel interference.

We make sure that the units are correct, and we
compare against the simulated result from Mininet-Optical.

"""

from math import log10, exp, e, pi, asinh
from PhysicalQuantities import q

# Import individual units as well.
# Use q.{unit} to disambiguate if needed
locals().update({f:getattr(q,f) for f in dir(q)})

# Missing units as needed
Hz = 1/s
GHz = 1e9 * Hz

# Scaling hacks since units aren't canceling for some reason
nm = 1e-9 * m
ps = 1e-12 * s

# Physical Constants
Planck = h = 6.62607015e-34 * J/Hz
C = 299792458.0 * m/s

# Signal parameters
pwr = (.001 * dBm).W

# Other test parameters
length = 25 * km

# SMF constants
fiber_attenuation_db = .22/km
nonlinear_coefficient = 1.27/(W*km)
dispersion = 16.7 * ps/(km*nm)

# Self channel interference so same power for
# channel under test and interfering channel
bw = 32 * GHz  # Is this correct?
pwr_cut = pwr
pwr_ch = pwr_cut
bw_cut = bw
bw_ch = bw

alpha = fiber_attenuation_db / (20*log10(e))
asymptotic_length = 1 / (2*alpha)
effective_length = ((1 - exp(-2 * alpha * length)) /
                    (2 * alpha))
ref_wavelength = 1550 * nm

D = dispersion
gamma = nonlinear_coefficient

beta2 = ref_wavelength**2 * D / (2 * pi * C)

# Constant from GN-model equation
const = ((16/27) * (gamma * effective_length)**2 /
         (2*pi * beta2 * asymptotic_length))

# Self channel interference psi computation
# Note parameter should be unitless
psi = asinh(0.5 * pi*pi * asymptotic_length *
            beta2 * bw_cut*bw_cut)

# G is the flat PSD
g_cut = pwr_cut/bw_cut
g_ch = pwr_ch/bw_ch

g_nli = const * (g_ch*g_ch) * g_cut * psi * bw_cut

print(g_nli.mW)
print(g_nli.mW.dB)

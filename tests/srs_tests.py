from mnoptical.topo.linear_params import LinearTopology
from mnoptical.link import SRS_Effect_Model, Zirngibl_General_Model, Sylvestre_SRS_Model, Bigo_SRS_Model
from scipy.optimize import curve_fit
import numpy as np
import math
import unittest

power_dBm = 0
span_length_km = 50
span_no = 1
hop_no = 2

wdg_id = 'linear'
signal_no = 90

# convert the watts values to dBm
def wattsTodBm(value):
  conv = 10 * np.log10(value) + 30
  return conv


# basis function for end to end tilt
def basisFunction(x, m, b):
  return m * x + b


# calculate the end to end tilt
def computeEndToEndTilt(values):
  data_len = len(values)
  x = np.arange(1, data_len+1, 1)
  y = values
  popt, _ = curve_fit(basisFunction, x, y)
  # summarize the parameter values
  a, b = popt
  x_line = np.arange(min(x), max(x), 1)
  y_line = basisFunction(x_line, a, b)
  tilt = max(y_line) - min(y_line)
  return tilt


def configure_terminals(net):
  tx = net.name_to_node['tx']
  rx = net.name_to_node['rx']
  for p, c in enumerate(range(1, signal_no + 1), start=1):
    # configure transmitter terminal
    tx_transceiver = tx.id_to_transceivers[c]
    tx.assoc_tx_to_channel(tx_transceiver, c, out_port=p)
    # configure receiver terminal
    rx_transceiver = rx.id_to_transceivers[1]
    rx.assoc_rx_to_channel(rx_transceiver, c, in_port=1)


def configure_roadms(net):
  in_port = out_port = 0
  for i, r in enumerate(net.roadms):

    if i == 0:
      # case for first ROADM
      for in_port, c in enumerate(range(1, signal_no + 1), start=1):
        r.install_switch_rule(in_port, out_port, c)
    elif i == len(net.roadms) - 1:
      in_port = 0
      # case for last ROADM
      for out_port, c in enumerate(range(1, signal_no + 1), start=1):
        r.install_switch_rule(in_port, 1, c)
    else:
      # case for intermediate ROADM
      in_port = out_port = 0
      for c in range(1, signal_no + 1):
        r.install_switch_rule(in_port, out_port, c)

  # returns two ROADM objects
  return net.roadms[0], net.roadms[1]


def launch_transmission(net):
  tx = net.name_to_node['tx']
  tx.turn_on()


def get_preamp_tilt(roadms):

  optical_signals = roadms[1].get_optical_signals()

  # declare an array to store the computed values
  preamp_in = []

  # read the monitored values
  for i in range(0, len(optical_signals)):
    for k, v in list(optical_signals[i].loc_in_to_state.items()):
      if str(k) == "<r2-preamp 11.0dB>":  # input of R2's pre-amp
        preamp_in.append(wattsTodBm(v['power']))

  # compute the end-to-end tilt
  preamp_in_dBm_tilt = computeEndToEndTilt(preamp_in)

  # round the value to 2 decimal places
  preamp_in_dBm_tilt = round(preamp_in_dBm_tilt, 2)
  actual_result = preamp_in_dBm_tilt
  print("preamp_in_dBm_tilt: ", preamp_in_dBm_tilt)

  return actual_result


def srs_test(srs_model):

  net = LinearTopology.build(power_dBm=power_dBm, span_length_km=span_length_km,
                             span_no=span_no, hop_no=hop_no, signal_no=signal_no,
                             wdg_id='linear', srs_model=srs_model, wd_loss='SMF')

  configure_terminals(net)
  r = configure_roadms(net)
  launch_transmission(net)
  actual_result = get_preamp_tilt(roadms=r)

  return actual_result


if __name__ == '__main__':
  
  # Test for SRS_Effect_Model
  # M. Zirngibl Analytical model of Raman gain effects in massive wavelength division multiplexed transmission systems
  # Most accurate for uniform loading cases.

  expected_result = 0.62
  srs_model = SRS_Effect_Model
  preamp_tilt = srs_test(srs_model=srs_model)
  assert preamp_tilt == expected_result


  # Test for Zirngibl_General_Model
  # M. Zirngibl Analytical model of Raman gain effects in massive wavelength division multiplexed transmission systems. - Equation 7
  # Most accurate for non-uniform loading cases.

  expected_result = 0.78
  srs_model = Zirngibl_General_Model
  preamp_tilt = srs_test(srs_model=srs_model)
  assert preamp_tilt == expected_result


  # Test for Sylvestre_SRS_Model
  # SRS model proposed in 'Raman-Induced Power Tilt in Arbitrarily Large Wavelength-Division-MUltiplexed Systems' by T. Sylvestre et al., 2005 - Equation 6

  expected_result = 0.57
  srs_model = Sylvestre_SRS_Model
  preamp_tilt = srs_test(srs_model=srs_model)
  assert preamp_tilt == expected_result


  # Test for Bigo_SRS_Model
  # SRS model proposed in 'Raman-Induced Power Tilt in Arbitrarily Large Wavelength-Division-MUltiplexed Systems' by T. Sylvestre et al., 2005 - Equation 6

  expected_result = 1.01
  srs_model = Bigo_SRS_Model
  preamp_tilt = srs_test(srs_model=srs_model)
  assert preamp_tilt == expected_result



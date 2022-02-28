"""

    Read log files and check the statistical differences.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, \
    mean_squared_error


# get GNPy and Mininet-Optical tests data
mo_tests_path = 'mo_tests.csv'
gnpy_tests_path = '../../gnpy-cross-validation/gnpy-mytests/gnpy_tests.csv'

# Files' header:
# test no,frequency,launch power,fibre length,spans,hops,signal no,power,ASE noise,NLI noise,OSNR,GSNR
gnpy_tests_dataset = pd.read_csv(mo_tests_path)
mo_tests_dataset = pd.read_csv(gnpy_tests_path)
metrics_of_interest = ['power', 'ASE noise', 'NLI noise', 'OSNR', 'GSNR']


def error_analysis(x, y, metric, metric_unit):
    """
    Compute mean absolute error (MAE) and mean squared error (MSE)
    for each parameter. The error threshold (error_th) is the maximum
    difference allowed to indicate if the two simulation systems
    operate statistically similar.
    :param x: Series, first sample of comparison
    :param y: Series, second sample of comparison
    :param metric: String, metric label
    :param metric_unit: String, metric unit label
    :return:
    """
    error_th = 0.01
    if mean_absolute_error(x, y) > error_th or \
        mean_squared_error(x, y) > error_th:
        print("Mininet-Optical simulation differs from GNPy, you may want to check the code!")
        print("Metric of interest: %s [%s]" % (metric, metric_unit))
        print("MAE: %f %s" % (mean_absolute_error(x, y), metric_unit))
        print("MSE: %f %s" % (mean_squared_error(x, y), metric_unit))
        print()
    else:
        print("Mininet-Optical simulation complies with GNPy")


def analysis_all():
    """
    Iterate through Mininet-Optical and GNPy data by metric
    and compute the error analysis with error_analysis()
    """
    mo_tests = mo_tests_dataset
    gnpy_tests = gnpy_tests_dataset
    for metric in metrics_of_interest:
        if metric == 'power':
            # convert power to dBm
            m_metric_dBm = 10 * np.log10(mo_tests[metric] * 1e3)
            g_metric_dBm = 10 * np.log10(gnpy_tests[metric] * 1e3)
            error_analysis(m_metric_dBm, g_metric_dBm, metric, 'dBm')
        elif metric == 'NLI noise' or metric == 'ASE noise':
            m_metric_dB = 10 * np.log10(mo_tests[metric])
            g_metric_dB = 10 * np.log10(gnpy_tests[metric])
            error_analysis(m_metric_dB, g_metric_dB, metric, 'dB')
        else:
            m_metric_dB = mo_tests[metric]
            g_metric_dB = gnpy_tests[metric]
            error_analysis(m_metric_dB, g_metric_dB, metric, 'dB')

# Main call
analysis_all()
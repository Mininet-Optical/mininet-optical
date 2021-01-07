import math
import numpy as np
import scipy.constants as sc
import os


# Helper functions

def db_to_abs(db_value):
    """
    :param db_value: list or float
    :return: Convert dB to absolute value
    """
    absolute_value = 10 ** (db_value / float(10))
    return absolute_value


def abs_to_db(absolute_value):
    """
    :param absolute_value: list or float
    :return: Convert absolute value to dB
    """
    db_value = 10 * np.log10(absolute_value)
    return db_value


# Units

c = 299792458.0  # Speed of light
nm = 1.0e-9  # nanometers
cm = 1.0e-2  # centimeters
um = 1.0e-6  # micrometers
km = 1.0e3  # kilometers
THz = 1.0e12  # terahertz
mW = 1.0e-3  # milli-watts
W = 1.0  # watts
ps = 1.0E-12  # picoseconds
pi = math.pi  # pi
h = sc.h  # Planck constant

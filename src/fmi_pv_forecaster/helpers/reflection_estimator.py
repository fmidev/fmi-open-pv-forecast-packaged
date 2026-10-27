"""
This file contains functions for estimating how much of the light reaching the plane of array is lost due to
reflections.

Equations are based on Martin & Ruiz 2001 paper
"Calculation of the PV modules angular losses under field conditions by means of an analytical model"

Author: TimoSalola (Timo Salola).
"""

import math
from datetime import datetime

import numpy
import pandas
import pandas as pd

from fmi_pv_forecaster.helpers import astronomical_calculations

# panel reflectance constant, empirical value. Solar panels with better optical coatings would have a lower value where
# as uncoated panels would have a higher value. Dust on panels increases reflectance_constant.
# 0.159 is given as an average value for polycrystalline silicon module reflectance
# 0.169 is given in the same paper as monocrystalline reflectance
reflectance_constant = 0.169


def components_to_corrected_poa(DNI_component: float, DHI_component: float, GHI_component: float,
                                dt: pandas.DataFrame, latitude, longitude, tilt, azimuth) -> pandas.DataFrame:
    """
    Takes dni, dhi and ghi components of a solar panel projected irradiance and computes how much of the radiation is
    absorbed by the solar panels, in opposed to reflected away.
    :param DNI_component: poa transposed dni value(W)
    :param DHI_component: poa transposed dhi value(W)
    :param GHI_component: poa transposed ghi value(W)
    :param dt: time for estimation. For example, "2023-10-13 19:30:00+00:00"
    :return: absorbed radiation in W
    """

    # direct sunlight reflection variable, has to be computed multiple times.
    dni_reflected = __dni_reflected(dt, latitude, longitude, tilt, azimuth)

    # These values do not have to be recomputed every single time as they are installation-specific, and they do not
    # even take time as an input. This could be optimized if needed.
    dhi_reflected = __dhi_reflected(tilt)
    ghi_reflected = __ghi_reflected(tilt)

    # POA_reflection_corrected or radiation absorbed by the solar panel.
    POA_reflection_corrected = ((1 - dni_reflected) * DNI_component + (1 - dhi_reflected) * DHI_component
                                + (1 - ghi_reflected) * GHI_component)

    return POA_reflection_corrected


def add_reflection_corrected_poa_to_df(df: pandas.DataFrame) -> pandas.DataFrame:
    """
    Adds reflection corrected POA value to dataframe with name "poa_ref_cor"
    :param df:
    :return:
    """

    df["poa_ref_cor"] = df["dni_rc"] + df["dhi_rc"] + df["ghi_rc"]

    # print("Adding reflection corrected POA to dataframe")

    # helper function + apply — structure

    # helper function
    def helper_components_to_corrected_poa(df: pandas.DataFrame) -> pandas.DataFrame:
        return components_to_corrected_poa(df["dni_poa"], df["dhi_poa"], df["ghi_poa"], df["time"])

    # applying helper function to dataset and storing result as a new column
    # df["poa_ref_cor"] = df.apply(helper_components_to_corrected_poa, axis=1)

    # print("Reflection corrected POA values added.")

    return df


def add_reflection_corrected_poa_components_to_df(df: pandas.DataFrame,
                                                  latitude, longitude, tilt, azimuth) -> pandas.DataFrame:
    """
    def helper_add_dni_ref(h_df):
        #  (1-alpha_BN)*BTN
        return math.fabs(1 - __dni_reflected(df["time"], latitude, longitude, tilt, azimuth)) * h_df["dni_poa"]

    def helper_add_dhi_ref(h_df):
        # (1-alpha_d)*DT
        return math.fabs(1 - __dhi_reflected(tilt)) * h_df["dhi_poa"]

    def helper_add_ghi_ref(h_df):
        # (1-alpha_dg)*DTg
        return math.fabs(1 - __ghi_reflected(tilt)) * h_df["ghi_poa"]


    BTN = dni_poa
    DTg = ghi_poa
    DT = dhi_poa
    """

    dhi_reflection_value = __dhi_reflected(tilt)
    ghi_reflection_value = __ghi_reflected(tilt)

    # df["AOI"] = astronomical_calculations.get_solar_angle_of_incidence_fast(df.index)
    df["dni_rc"] = (1 - __dni_reflected(df.index, latitude, longitude, tilt, azimuth)) * df["dni_poa"]
    df["dhi_rc"] = (1 - dhi_reflection_value) * df["dhi_poa"]
    df["ghi_rc"] = (1 - ghi_reflection_value) * df["ghi_poa"]

    # print_full(df)

    return df


def __dni_reflected(dt: datetime, latitude, longitude, tilt, azimuth) -> float:
    """
    Computes a constant in range [0,1] which represents how much of the direct irradiance is reflected from panel
    surfaces.
    :param dt: datetime
    :return: reflected radiation in range [0,1]

    F_B_(alpha) in "Calculation of the PV modules angular losses under field conditions by means of an analytical model"
    """

    a_r = reflectance_constant

    AOI = astronomical_calculations.get_solar_angle_of_incidence_limited(dt, latitude, longitude, tilt, azimuth)

    # upper section of the fraction equation
    upper_fraction = math.e ** (-numpy.cos(numpy.radians(AOI)) / a_r) - math.e ** (-1.0 / a_r)
    # lower section of the fraction equation
    lower_fraction = 1.0 - math.e ** (-1.0 / a_r)

    # fraction or alpha_BN or dni_reflected
    dni_reflected = upper_fraction / lower_fraction

    return dni_reflected


def __ghi_reflected(tilt) -> float:
    """
    Computes a constant in range [0,1] which represents how much of ground reflected irradiation is reflected away from
    solar panel surfaces. Note that this is constant for an installation.
    :return: [0,1] float, 0 no light reflected, 1 no light absorbed by panels.

    F_A(beta) in "Calculation of the PV modules angular losses under field conditions by means of an analytical model"

    """

    if tilt == 0:
        return 1

    # constants, these are from
    c1 = 4.0 / (3.0 * math.pi)

    c2 = -0.074
    a_r = reflectance_constant
    panel_tilt = numpy.radians(tilt)  # theta_T

    # equation parts, part 1 is used 2 times
    part1 = math.sin(panel_tilt) + (panel_tilt - math.sin(panel_tilt)) / (1.0 - math.cos(panel_tilt))

    part2 = c1 * part1 + c2 * (part1 ** 2.0)
    part3 = (-1.0 / a_r) * part2

    ghi_reflected = math.e ** part3

    return ghi_reflected


def __dhi_reflected(tilt) -> float:
    """
    Computes a constant in range [0,1] which represents how much of atmospheric diffuse light is reflected away from
    solar panel surfaces. Constant for an installation. Almost a 1 to 1 copy of __ghi_reflected except
    "pi -" addition to part1 and "1-cos" to "1+cos" replacement in part1 as well.
    :return: [0,1] float, 0 no light reflected, 1 no light absorbed by panels.

    F_D(beta) in "Calculation of the PV modules angular losses under field conditions by means of an analytical model"

    """
    # constants

    c1 = 4.0 / (math.pi * 3.0)
    c2 = -0.074
    a_r = reflectance_constant
    panel_tilt = numpy.radians(tilt)  # theta_T
    pi = math.pi

    # equation parts, part 1 is used 2 times
    part1 = math.sin(panel_tilt) + (pi - panel_tilt - math.sin(panel_tilt)) / (1.0 + math.cos(panel_tilt))

    part2 = c1 * part1 + c2 * (part1 ** 2.0)
    part3 = (-1.0 / a_r) * part2

    dhi_reflected = math.exp(part3)

    return dhi_reflected


def print_full(x: pandas.DataFrame):
    """
    Prints a dataframe without leaving any columns or rows out. Useful for debugging.
    """

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1400)
    pd.set_option('display.float_format', '{:10,.2f}'.format)
    pd.set_option('display.max_colwidth', None)
    print(x)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')

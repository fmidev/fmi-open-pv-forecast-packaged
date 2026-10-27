"""
Irradiance transposition functions. Used for transforming different solar irradiance components to panel
projected irradiance components.

Terminology:
POA: Plane of array irradiance, the total amount of radiation which reaches the panel surface at a given time. This is
the sum of poa projected dhi, dni and ghi.
POA = "dhi_poa" + "dni_poa" + "ghi_poa"

Author: TimoSalola (Timo Salola).
"""

import math
from datetime import datetime

import numpy
import pandas
import pandas as pd
import pvlib.irradiance

import fmi_pv_forecaster.helpers.default_parameters
from fmi_pv_forecaster.helpers import astronomical_calculations


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


def irradiance_df_to_poa_df(irradiance_df: pandas.DataFrame, latitude, longitude, tilt, azimuth) -> pandas.DataFrame:
    """
    This function takes an irradiance dataframe as input. This dataframe should contain ghi, dni and dhi
    irradiance values.
    These values are then projected to the panel surfaces either using simple geometry or more complex equations.

    :param irradiance_df: Solar irradiance dataframe with ghi, dni and dhi components.
    :return: Dataframe with dni, ghi and dhi plane of array irradiance projections
    """

    # handling dni and dhi
    irradiance_df["dni_poa"] = __project_dni_to_panel_surface_using_time_fast(
        irradiance_df["dni"], irradiance_df.index, latitude, longitude, tilt, azimuth)

    # perez dhi function, this had continuity issues before it was changed to modified perez
    irradiance_df["dhi_poa"] = __project_dhi_to_panel_surface_perez_fast(
        irradiance_df.index, irradiance_df["dhi"], irradiance_df["dni"], latitude, longitude, tilt, azimuth)

    # and finally ghi
    if "albedo" in irradiance_df.columns:
        irradiance_df["ghi_poa"] = __project_ghi_to_panel_surface(irradiance_df["ghi"], tilt, irradiance_df["albedo"])
    else:
        irradiance_df["albedo"] = fmi_pv_forecaster.helpers.default_parameters.albedo
        irradiance_df["ghi_poa"] = __project_ghi_to_panel_surface(irradiance_df["ghi"], tilt, irradiance_df["albedo"])

    # adding the sum of projections to df as poa
    irradiance_df["poa"] = irradiance_df["dhi_poa"] + irradiance_df["dni_poa"] + irradiance_df["ghi_poa"]

    return irradiance_df


"""
PROJECTION FUNCTIONS
5 functions for 3 components, 2 functions for DNI as either date or angle of incidence can be used for computing the
same result.

2 functions for DHI as the sky can be assumed as uniform on non-uniform(perez)
"""


def __project_dni_to_panel_surface_using_time_fast(dni: float, dt: datetime,
                                                   latitude, longitude, tilt, azimuth) -> float:
    """
    :param DNI: Direct sunlight irradiance component in W
    :param dt: Time of simulation
    :return: Direct radiation per 1m² of solar panel surface

    This version of the function is fairly well optimized.
    """

    angle_of_incidence = astronomical_calculations.get_solar_angle_of_incidence_limited(dt, latitude, longitude,
                                                                                        tilt, azimuth)
    output = numpy.abs(__project_dni_to_panel_surface_using_angle(dni, angle_of_incidence))

    return output


def __project_dni_to_panel_surface_using_angle(dni: float, angle_of_incidence: float) -> float:
    """
    Based on https://pvpmc.sandia.gov/modeling-steps/1-weather-design-inputs/plane-of-array-poa-irradiance
    /calculating-poa-irradiance/poa-beam/
    :param dni: Direct sunlight irradiance component in W
    :param angle_of_incidence: angle between sunlight and solar panel normal, calculated by astronomical_calculations.py
    :return: Direct radiation hitting solar panel surface.
    """

    return dni * numpy.cos(numpy.radians(angle_of_incidence))


def __project_dhi_to_panel_surface_perez_fast(time: datetime, dhi: float, dni: float, latitude, longitude,
                                              tilt: float, azimuth: float, driesse=True) -> float:
    """
    Often more accurate DHI transposition model.
    Calculated internally by pvlib, pvlib documentation at:
    https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.perez_driesse.html

    Perez model assumes that the region of the sky near to sun is brighter than the rest. The model contains a data table
    from which values are read and used for the transposition. This works well regardless of the angle of the panels and
    the position of the sun.

    The downside is that regular perez has discontinuities which may show up when the model switches between values
    in the perez table. These discontinuities can be somewhat significant when the ratio of dhi and dni is abnormal or
    when the sun is near or even below the horizon.

    Discontinuities are fixed with perez-driesse which is a continuous version of the same perez model.

    One remaining issue is that if dhi is 100W and the sun is far enough below the horizon, this
    model will give 0W as panel projected value even when panel tilt is zero. You would not expect dhi to be 100W when
    sun is below the horizon, but you would expect the panel surface radiation from dhi to be 100W when tilt is 0.
    """

    # function parameters
    dni_extra = pvlib.irradiance.get_extra_radiation(time)

    # this should take sun-earth distance variation into account
    # empirical constant 1366.1 should work nearly as well

    # installation angles
    surface_tilt = tilt
    surface_azimuth = azimuth

    # sun angles
    solar_azimuth, solar_zenith = astronomical_calculations.get_solar_azimuth_zenith_fast(time, latitude, longitude)

    # air mass
    airmass = astronomical_calculations.get_air_mass_fast(time, latitude, longitude)

    # Continuous perez
    if driesse:
        dhi_perez = pvlib.irradiance.perez_driesse(surface_tilt, surface_azimuth, dhi, dni, dni_extra,
                                                   solar_zenith, solar_azimuth, airmass, return_components=False)
    else:
        # piecewise perez
        dhi_perez = pvlib.irradiance.perez(surface_tilt, surface_azimuth, dhi, dni, dni_extra,
                                           solar_zenith, solar_azimuth, airmass, return_components=False)

    return dhi_perez


def __project_ghi_to_panel_surface(ghi: float, tilt: float, albedo) -> float:
    """
    Equation from
    https://pvpmc.sandia.gov/modeling-guide/1-weather-design-inputs/plane-of-array-poa-irradiance/calculating-poa-irradiance/poa-ground-reflected/

    Uses ground albedo and panel angles to estimate how much of the sunlight per 1m² of ground is radiated towards solar
    panel surfaces. Expected value is 0 for tilt = 0, increases as tilt increases.
    :param ghi: Ground reflected solar irradiance.
    :return: Ground reflected solar irradiance hitting the solar panel surface.
    """

    step1 = (1.0 - math.cos(numpy.radians(tilt))) / 2
    step2 = ghi * albedo * step1
    return step2  # ghi * config.albedo * ((1.0 - math.cos(numpy.radians(config.tilt))) / 2.0)


"""
UNUSED FUNCTIONS BELOW
"""


def __project_dhi_to_panel_surface(dhi: float, tilt) -> float:
    """
    Uses atmosphere scattered sunlight and solar panel angles to estimate how much of the scattered light is radiated
    towards solar panel surfaces.

    This version uses the isotropic sky model. Meaning it will assume the sky as a uniform emitter. Accurate when panel
    tilt is low regardless of the position of the sun.
    :param dhi: Atmosphere scattered irradiation.(Radiation on horizontal plane, direct sunlight is blocked)
    :return: Atmosphere scattered irradiation projected to solar panel surfaces.
    """
    return dhi * ((1.0 + math.cos(numpy.radians(tilt))) / 2.0)

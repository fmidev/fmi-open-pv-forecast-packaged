"""
This file contains functions for estimating PV panel temperatures and transferring temperature data from another
dataframe.

Author: TimoSalola (Timo Salola).
"""
import math

import pandas

from fmi_pv_forecaster.helpers import default_parameters


def add_estimated_panel_temperature(df: pandas.DataFrame) -> pandas.DataFrame:
    """
    Adds an estimate for panel temperature based on wind speed, air temperature and absorbed radiation.
    If air temperature, wind speed or absorbed radiation columns are missing, aborts.
    If columns exists but temperature function returns nan due to faulty input, uses air temperature which should always
    be present in df.
    :param df:
    :return:

    """

    # checking that all required variables exist in df

    if "T" not in df.columns:
        #print("No air temperature in dataframe, using constant value: " + str(default_parameters.air_temperature)+"°C")
        df["T"] = default_parameters.air_temperature

    if "wind" not in df.columns:
        #print("No wind speed in dataframe, using constant value: " + str(default_parameters.wind_speed)+"m/s")
        df["wind"] = default_parameters.wind_speed

    if "poa_ref_cor" not in df.columns:
        print("no reflection corrected poa value in df 'poa_ref_cor'")
        print("Aborting")
        return df

    def helper_add_panel_temp(df):
        estimated_temp = temperature_of_module(df["poa_ref_cor"], df["wind"], default_parameters.panel_elevation,
                                               df["T"])

        if math.isnan(estimated_temp):
            return df["T"]
        else:
            return estimated_temp

    # applying helper function to dataset and storing result as a new column
    df["module_temp"] = df.apply(helper_add_panel_temp, axis=1)

    return df


def temperature_of_module(absorbed_radiation: float, wind: float,
                          module_elevation: float, air_temperature: float) -> float:
    """
    :param absorbed_radiation: radiation hitting solar panel after reflections are accounted for in W
    :param wind: wind speed in meters per second
    :param module_elevation: module elevation from ground, in meters
    :param air_temperature: air temperature at 2m in Celsius
    :return: module temperature in Celsius

    King 2004 model
    D.~King, J.~Kratochvil, and W.~Boyson,
    Photovoltaic Array Performance Model Vol. 8,
    PhD thesis (Sandia National Laboratories, 2004).
    """

    # two empirical constants
    constant_a = -3.47
    constant_b = -0.0594

    # wind is sometimes given as west/east components

    # wind speed at model elevation, assumes 0 speed at ground, given wind value at 10m and generates a transition curve
    # that goes from 0 to 10 and above. Should be somewhat accurate.
    wind_speed = wind * (module_elevation / 10) ** 0.1429

    # actual model temperature equation
    module_temperature = absorbed_radiation * math.e ** (constant_a + constant_b * wind_speed) + air_temperature

    return module_temperature

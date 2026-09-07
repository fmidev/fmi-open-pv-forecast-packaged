import random

import fmi_pv_forecaster as pvfc
import pandas as pd


def random_int(a, b):
    # helper, generates ints for some functions
    return random.randint(a, b)


def random_float(a, b):
    # helper, generates floats for some functions. 6 decimal values can do geolocation at 1m accuracy so 6 should be
    # enough for testing purposes. Also keeps prints neater.
    return round(random.uniform(a, b), 6)


def print_full(x: pd.DataFrame):
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


def test_clearsky_forecast_default_range():
    print("====================================================")
    print("==== Testing default clearsky interval complete")
    print("====================================================")

    tilt = random_float(0, 90)
    azimuth = random_float(0, 360)

    latitude = 60
    longitude = 25.0

    pvfc.set_location(latitude, longitude)
    pvfc.set_angles(tilt, azimuth)

    pvfc.set_extended_output(True)


    pvfc.set_snow_sliding(True)


    powerdata = pvfc.get_default_clearsky_forecast()

    print_full(powerdata)

    print("====================================================")
    print("==== Clearsky default interval test complete")
    print("====================================================")

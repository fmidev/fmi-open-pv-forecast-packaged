import pandas as pd
import pytest

import fmi_pv_forecaster.pv_forecaster as pvfc


"""
This file contains tests for radiation forecasting, a subset of pv_forecaster functions
"""


@pytest.fixture(scope="module", autouse=True)
def setUp():
    """
    This function runs when any of the tests in this file is called.
    Geolocation should be the only required input for these tests.
    """
    print("\nFeeding geolocation to pvfc via setup function.")
    print("No other setters needed.")
    pvfc.set_location(65, 25)


def test_forecast_returns_dataframe():
    radiation_forecast = pvfc.get_fmi_radiation_forecast()

    assert type(radiation_forecast) is pd.DataFrame, (
        "Radiation forecasting function returned something else than a pandas dataframe."
    )
    print("Radiation forecast returns a dataframe like it should. ")


def test_radiation_forecasting_timestep():
    """
    This function tests if the FMI open data server is returning a valid dataframe with 60 minute timesteps.
    """

    radiation_forecast = pvfc.get_fmi_radiation_forecast()

    timedelta_minutes = None  # This value holds the time delta between two rows in the dataframe
    expected_timedelta_minutes = 60  # this is the expected timedelta

    # going through the forecast each row by row checking if timedelta is wrong.
    for i in range(len(radiation_forecast)):
        if i == 0:
            continue
        row = radiation_forecast.iloc[i]
        last_row = radiation_forecast.iloc[i - 1]

        timedelta = row.name - last_row.name
        timedelta_minutes = timedelta.seconds // 60

        assert timedelta_minutes == expected_timedelta_minutes, (
            "Error with FMI radiation forecast timesteps."
            "Distance between rows should have been 60 minutes."

        )

    print("Timedelta between rows was " + str(timedelta_minutes) + " minutes")
    print("The set timestep was: " + str(60))


def test_required_parameters():
    """
    This function tests if the FMI open data is returning all required parameters.
    """
    radiation_forecast = pvfc.get_fmi_radiation_forecast()

    columns = radiation_forecast.columns
    # expected columns = ['dni', 'dhi', 'ghi', 'albedo', 'T', 'wind', 'cloud_cover']

    # radiation components
    assert "dni" in columns, (
        "Direct normal irradiance \"dni\" is missing from radiation forecast. "
        "dni is a critical component, something is wrong."
    )
    assert "dhi" in columns, (
        "Diffuse horizontal radiation \"dhi\" is missing from radiation forecast. "
        "dhi is a critical component, something is wrong."
    )
    assert "ghi" in columns, (
        "Global horizontal radiation \"ghi\" is missing from radiation forecast. "
        "ghi is a critical component, something is wrong."
    )

    print("Radiation forecast included dni, dhi and ghi. These are are required parameters.")


def test_nice_to_have_parameters():
    """
    This function tests if the FMI open data is returning all optional parameters.
    """
    radiation_forecast = pvfc.get_fmi_radiation_forecast()

    columns = radiation_forecast.columns
    # expected columns = ['dni', 'dhi', 'ghi', 'albedo', 'T', 'wind', 'cloud_cover']
    # cloud cover is not really used, leaving it untested

    # radiation components
    assert "T" in columns, (
        "Air temperature T is missing from fmi open data forecast. "
        "This should not happen, forecasts can still be generated, but issue should be investigated."
    )

    assert "wind" in columns, (
        "Wind speed \"wind\" is missing from fmi open data forecast."
        "This should not happen, forecasts can still be generated, but issue should be investigated."
    )

    assert "albedo" in columns, (
        "Ground reflectivity \"albedo\" is missing from fmi open data forecast."
        "This should not happen, forecasts can still be generated, but issue should be investigated."
    )

    print("Radiation forecast included wind, air temp and albedo. These are optional nice to haves.")


def test_row_count_after_nandrop_reasonable():
    radiation_forecast = pvfc.get_fmi_radiation_forecast()

    radiation_forecast = radiation_forecast.dropna()

    # length should be 65. Apparently dni and dhi radiations are lacking for the first hour for some reason.
    assert len(radiation_forecast) > 60, (
        "Got less than 60 rows from FMI open data."
        "This is suspicious as timestep should be 60min and forecast len 66 hours."
    )
    assert len(radiation_forecast.index) < 70, (
        "Got more than 70 rows from FMI open data. "
        "This is suspicious as timestep should be 60min and forecast len 66 hours."
    )


    print("Forecast length checkup looks fine.")



def test_values_are_reasonable():
    """
    This function does some tests on dataframe columns and checks if radiation forecasts contain unreasonable values.
    """
    radiation_forecast = pvfc.get_fmi_radiation_forecast()

    """
                              dni         dhi         ghi    albedo    T  wind  cloud_cover
    Time
    2026-03-02 11:30:00  0.064532  113.664500  113.683528  0.364306 -3.7  2.39        100.0
    2026-03-02 12:30:00  0.000000   96.208806   96.202361  0.360213 -3.8  2.31        100.0
    2026-03-02 13:30:00  0.000000   68.659722   68.658861  0.358353 -3.9  1.37        100.0
    """

    min_dni = radiation_forecast["dni"].min()
    min_dhi = radiation_forecast["dhi"].min()
    min_ghi = radiation_forecast["ghi"].min()

    max_dni = radiation_forecast["dni"].max()
    max_dhi = radiation_forecast["dhi"].max()
    max_ghi = radiation_forecast["ghi"].max()

    min_albedo = radiation_forecast["albedo"].min()
    max_albedo = radiation_forecast["albedo"].max()

    min_wind = radiation_forecast["wind"].min()
    max_wind = radiation_forecast["wind"].max()

    min_T = radiation_forecast["T"].min()
    max_T = radiation_forecast["T"].max()

    min_cloud_cover = radiation_forecast["cloud_cover"].min()
    max_cloud_cover = radiation_forecast["cloud_cover"].max()

    assert min_dni >= 0, (
        print("dni radiation forecast had a value lower than 0. This is not physically possible. Possible filtering"
              "failure?")
    )

    assert min_dhi >= 0, (
        print("dhi radiation forecast had a value lower than 0. This is not physically possible. Possible filtering"
              "failure?")
    )

    assert min_ghi >= 0, (
        print("ghi radiation forecast had a value lower than 0. This is not physically possible. Possible filtering"
              "failure?")
    )

    assert min_wind >= 0, (
        print("Wind speed column had a value lower than 0. This is not physically possible.")
    )

    assert min_albedo >= 0, (
        print("Albedo column had a value lower than 0. This is not physically possible. Albedo is calculated by this"
              "package so the fault is likely in improper filtering inside this package.")
    )
    assert max_albedo <= 1, (
        print("Albedo column had a value highert han 1. This is not physically possible. Albedo is calculated by this"
              "package so the fault is likely in improper filtering inside this package.")
    )

    print("Radiation parameters, albedo and wind had physically possible values.")

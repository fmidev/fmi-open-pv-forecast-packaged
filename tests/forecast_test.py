import datetime
import random
from datetime import timedelta
import pandas
from fmi_pv_forecaster import pv_forecaster as pv_forecast


def random_int(a, b):
    # helper, generates ints for some functions
    return random.randint(a, b)


def random_float(a, b):
    # helper, generates floats for some functions. 6 decimal values can do geolocation at 1m accuracy so 6 should be
    # enough for testing purposes. Also keeps prints neater.
    return round(random.uniform(a, b), 6)


"""
### PVlib clear sky testing
"""


def test_clearsky_with_random_parameters(test_number=None):
    print("====================================================")
    print("==== Testing clearsky estimation for custom interval with random parameters")
    print("====================================================")

    tilt = random_float(0, 90)
    azimuth = random_float(0, 360)

    latitude = random_float(-90, 90)
    longitude = random_float(-180, 180)

    timestep = random_int(1, 60)

    time_start = datetime.datetime(random_int(2000, 2050), random_int(1, 12),
                                   random_int(1, 28), random_int(0, 23))
    time_end = time_start + timedelta(days=random_int(1, 10))

    pv_forecast.set_location(latitude, longitude)
    pv_forecast.set_angles(tilt, azimuth)

    clearsky_data = pv_forecast.__get_clearsky_radiation_for_interval(time_start, time_end, timestep)

    assert clearsky_data is not None, ("Clearsky data was none, something has to be wrong with the"
                                       "clearsky estimation function." + str(clearsky_data))

    # checking measurement count from df.

    expected_values_per_hour = 60.0 / timestep

    interval_length_in_hours = (time_end - time_start).total_seconds() / 3600

    expected_measurement_count = round(interval_length_in_hours * expected_values_per_hour)

    measurement_count = len(clearsky_data)

    # print(expected_measurement_count)
    # print(measurement_count) # this is usually the same or 1 higher than expected measurement count

    assert measurement_count >= expected_measurement_count, "Got fewer than expected measurements from clearsky estimation. There were " + str(
        measurement_count) + " measurements when " + str(expected_measurement_count) + "(+1) were expected."
    assert measurement_count - 1 <= expected_measurement_count, "Got more measurements than expected from clearsky estimation. There were " + str(
        measurement_count) + " measurements when " + str(expected_measurement_count) + "(+1) were expected."

    prt_string = "Clearsky test " + str(test_number) + " successful." + "Lat: " + str(latitude) + " Lon:" + str(
        longitude) + " tilt: " + str(tilt) + " azimuth:" + str(azimuth) + " date: " + str(time_start)

    print(prt_string)

    print("====================================================")
    print("==== Clearsky random parameter estimation complete")
    print("====================================================")


def test_clearsky_radiation_estimation():
    print("====================================================")
    print("==== Testing clearsky radiation estimation")
    print("====================================================")

    for i in range(10):
        test_clearsky_with_random_parameters(test_number=i)
        print("= Clearsky radiation test " + str(i) + " done.")

    print("====================================================")
    print("==== Testing clearsky radiation done")
    print("====================================================")


"""
### FMI forecast based testing
"""


def test_default_fmi_forecast():
    print("====================================================")
    print("==== Testing default time interval for FMI PV forecast")
    print("====================================================")

    tilt = random_float(0, 90)
    azimuth = random_float(0, 360)

    latitude = 60.0
    longitude = 25.0

    pv_forecast.set_location(latitude, longitude)
    pv_forecast.set_angles(tilt, azimuth)

    powerdata = pv_forecast.get_default_fmi_forecast()

    powerdata = powerdata.dropna()


    assert type(powerdata) is pandas.DataFrame, (
        "FMI forecast did not return a dataframe, something must be wrong."
    )

    print(len(powerdata))


    assert len(powerdata) > 60, (
        "FMI forecast length was too short. Something is wrong. Length was: " + str(len(powerdata))
        + " when expected 65 or 66."
    )

    assert len(powerdata) < 70, (
        "FMI forecast length was too long. Length was: " + str(len(powerdata)) + " when expected 65 or 66."
    )

    powerdata2 = pv_forecast.get_default_fmi_forecast(interpolate="15min")
    powerdata2 = powerdata2.dropna()

    assert type(powerdata2) is pandas.DataFrame, (
        "FMI forecast did not return a dataframe for 15min interpolated forecast, something must be wrong."
    )

    print(len(powerdata2))

    powerdata3 = pv_forecast.get_default_fmi_forecast(interpolate="1min")
    powerdata3 = powerdata3.dropna()

    assert type(powerdata3) is pandas.DataFrame, (
        "FMI forecast did not return a dataframe for 1min interpolated forecast, something must be wrong."
    )

    print(len(powerdata3))

    print("====================================================")
    print("==== FMI default interval forecast test done")
    print("====================================================")

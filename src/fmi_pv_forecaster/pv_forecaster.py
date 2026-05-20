import datetime

import pandas
import pandas as pd
import pytz

import fmi_pv_forecaster.helpers.default_parameters
from fmi_pv_forecaster import meps_loader
from fmi_pv_forecaster.helpers import irradiance_transpositions, output_estimator
from fmi_pv_forecaster.helpers import panel_temperature_estimator
from fmi_pv_forecaster.helpers import reflection_estimator

"""
Imports End
Program variables begin
"""

# These variables must be set before pv forecast is called
site_latitude = None
site_longitude = None
panel_tilt = None
panel_azimuth = None

# These variables can be changed if desired
extended_output = False  # set to true and the radiation parameters and intermediate steps of the pv output calculation
# will be included in the output

bifacial = False

power_rating = 1  # power in kw

align_clearsky_and_fmi = True

timezone = "UTC"

"""
Program variables end
Helper functions begin
"""


def print_info():
    print("System location(WGS84): " + str(site_latitude) + ", " + str(site_longitude) + ".")
    print("Panel angles: " + str(panel_tilt) + ", " + str(panel_azimuth) + ".")
    print("System power: " + str(power_rating))
    print("Timezone: " + str(timezone))
    print("Extended output: " + str(extended_output))


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


"""
Helpers end
Parameter set functions begin
"""


def set_location(latitude, longitude):
    """
    Call this function to set the PV site latitude and longitude. Values outside metcoop forecast region will cause
    issues with FMI forecast retrieval.
    :param latitude: WGS84 as float. Valid values are -90 to 90.
    :param longitude: WGS84 in float format. eq 60.4312. Valid values are -180 to 180.
    """

    global site_latitude
    global site_longitude

    if site_latitude != latitude or site_longitude != longitude:
        # at least one of the geolocation components was different
        # clearing cache, new location so data from old one can't be used anymore
        meps_loader.clear_cache()

    site_latitude = latitude
    site_longitude = longitude
    # print("Geolocation set at: " + str(site_latitude) + "°, " + str(site_longitude)+"°")




def set_angles(p_tilt, p_azimuth):
    """
    Call this function to set the panel angles for the PV system. Tilt 0 is for a
    :param p_tilt: 0 to 90. 0 for panel flat on the ground, 90 for vertical panel where center normal points to horizon.
    :param p_azimuth: 0 to 360. 0 for north, 90 for east, 180 south and so on. Accepts floats and integers.
    """

    global panel_tilt
    global panel_azimuth

    panel_tilt = p_tilt
    panel_azimuth = p_azimuth
    # print("Panel angles set at tilt: " + str(panel_tilt)+ "°  Azimuth: " + str(panel_azimuth)+"°")


def set_extended_output(extended: bool):
    """
    Use this function to enable or disable additional variables in the PV forecasts.
    Most of these variables are irrelevant to users and thus extended output is disabled as default.
    :param extended: True -> additional variables will be given, False -> additional variables will be hidden.
    :return:
    """
    global extended_output
    extended_output = extended


def set_nominal_power_kw(nominal_power: float):
    """
    This function sets the power rating of the PV system.
    :param nominal_power: Advertised power output of the PV system in standard conditions
    (perfect weather, direct sunlight)
    :return: None
    """
    global power_rating
    power_rating = nominal_power
    output_estimator.rated_power = nominal_power


def set_default_air_temp(air_temp_c: float):
    """
    This function will set the air temperature(in Celsius) which will be used by clearsky PV forecasts.
    FMI forecasts do not use the default value as air temperature is given by the forecast API.
    Air temperature influences panel temperature which in turn changes panel efficiency.
    """
    fmi_pv_forecaster.helpers.default_parameters.air_temperature = air_temp_c
    # print("Air temperature for clearsky simulations set at: " +
    # str(fmi_pv_forecast.helpers.default_parameters.air_temperature)+ "°C")


def set_default_wind_speed(wind_speed_ms: float):
    """
    This function will set the wind speed(in meters per second at 2m above ground) used by clearsky PV forecasts.
    FMI forecasts do not use the default value as wind speed at 2m is given by the forecast API.
    Wind transfers heat away from PV panels and decreases the difference between air temperature and panel temperature.
    """
    fmi_pv_forecaster.helpers.default_parameters.wind_speed = wind_speed_ms
    # print("Wind speed for clearsky simulations set at: " +
    # str(fmi_pv_forecast.helpers.default_parameters.wind_speed)+ "ms")


def set_module_elevation(module_elevation_m: float):
    """
    This function will set the physical module elevation(measured from ground, not sea level). Module elevation and
    wind speed at 2m are used together to estimate the wind at panel elevation.

    Higher than actual elevation can be used to compensate for exposed panels and
    lower than actual for sheltered panels.

    If you are processing external data with wind measured at panel elevation, use measured wind as wind value and
    set module elevation as 2m. This way exact wind speed measurements will be used.
    """

    fmi_pv_forecaster.helpers.default_parameters.panel_elevation = module_elevation_m
    # print("Module elevation set at: " + str(fmi_pv_forecast.helpers.default_parameters.panel_elevation) + "m")


def set_default_albedo(albedo: float):
    """
    Albedo here means ground reflectivity around the PV panel. Range is [0,1] with 0.12 being similar to grey old
    asphalt and 0.8 similar to snow.
    """

    fmi_pv_forecaster.helpers.default_parameters.albedo = albedo


def set_cache(cache_on):
    """
    Cache is on by default and this package was built with the intention of having cache always on.

    Disabling cache will cause every function with FMI in its name to make a new server query to
    FMI servers. This will result in unnecessary server calls.

    Having cache on will only make new server calls if data isn't cached yet, caching was done
    over a minute ago, geolocation was changed or cache was manually purged.
    """

    meps_loader.cache_enabled = cache_on


def set_bifacial(bifacial_on):
    global bifacial
    bifacial = bifacial_on



"""
Parameter set functions end
Internal helpers begin
"""


def __get_clearsky_radiation_for_interval(interval_start, interval_end, timestep):
    """
    Helper function, this will return a dataframe with clearsky radiation values dni, dhi and ghi
    """

    if site_latitude is None or site_longitude is None:
        raise ValueError(
            "Latitude and longitude must be defined before calling"
            " get_clearsky_radiation_for_interval(). Call pv_forecast.set_location(latitude, longitude) first with"
            " valid WGS84 coordinates."
        )

    clearsky_estimate = meps_loader.__get_irradiance_pvlib(site_latitude, site_longitude,
                                                           interval_start, interval_end, timestep)

    return clearsky_estimate

def get_clearsky_radiation_for_times(times):
    """
    Additional helper function, this returns clearsky radiation values at requested times for given location.
    """

    if site_latitude is None or site_longitude is None:
        raise ValueError(
            "Latitude and longitude must be defined before calling"
            " get_clearsky_radiation_for_interval(). Call pv_forecast.set_location(latitude, longitude) first with"
            " valid WGS84 coordinates."
        )


    clearsky_estimate = meps_loader.__get_irradiance_pvlib_flexible_times(site_latitude, site_longitude, times)

    return clearsky_estimate






def __get_fmi_forecast_for_interval(interval_start, interval_end):
    """
    Main function for getting FMI open data -radiation values.
    :param interval_start:
    :param interval_end:
    :return:
    """

    if site_latitude is None or site_longitude is None:
        raise ValueError(
            "Latitude and longitude must be defined before calling forecast -functions."
            " Call pv_forecast.set_location(latitude, longitude) first with valid WGS84 coordinates."
        )

    data = meps_loader.collect_fmi_opendata(site_latitude, site_longitude, interval_start, interval_end)

    return data


def __extract_nearest_row_from_power_df(power_df, time_value):
    """
    :param power_df: Dataframe with datetime index containing hourly time values with 30minute offsets. 12:30, 13:30 and
    so on. Will cause errors or crashes if
    :param time_value: Datetime timestamp,dateT12:45:21 for example. This would round to 12:30 which is then read from
    power_df.
    :return:
    """

    time_index = datetime.datetime(time_value.year, time_value.month, time_value.day, time_value.hour, 30)
    nearest_row = power_df.loc[str(time_index)]
    return nearest_row

def __interpolate_nearest_power_to_time_value(power_df, time_value):
    """
    This column interpolates 2 nearest rows with linear interpolation and returns a single row which is the linear
    inbetween of the 2 nearest rows. This function expects index to be hh:30 and hourly. eq. 13:30, 14:30 and so on.
    :param power_df:
    :param time_value:
    :return:
    """

    minute = time_value.minute

    timestamp1 = None
    timestamp2 = None

    if minute < 30:
        timestamp1 = (datetime.datetime(time_value.year, time_value.month, time_value.day, time_value.hour, 30)
                      - datetime.timedelta(minutes=60))
        timestamp2 = datetime.datetime(time_value.year, time_value.month, time_value.day, time_value.hour, 30)

    elif minute >= 30:
        timestamp1 = datetime.datetime(time_value.year, time_value.month, time_value.day, time_value.hour,
                                       30)
        timestamp2 = (datetime.datetime(time_value.year, time_value.month, time_value.day, time_value.hour, 30)
                      + datetime.timedelta(minutes=60))

    # distances between given time value and surrounding values

    if timestamp1 not in power_df.index or timestamp2 not in power_df.index:
        return None

    # print("timevalue:" + str(time_value))
    # print("timestamp1:" + str(timestamp1))
    # print("timestamp2:" + str(timestamp2))
    time_from1 = time_value - timestamp1  # a = X_pos - A_pos
    time_from2 = timestamp2 - time_value  # b = B_pos- X_pos
    total_time = time_from1 + time_from2  # C = a+b

    # A                         B
    # o------X------------------o
    # |--a---|-------b----------|
    # |------------C------------|

    # X = A*(1- a/C) + B*(1 - b/C)
    # C = 1
    # a = 0.1, b = 0.9
    # X = A*(0.9) + B*(0.1)

    # multipliers, fractional inverses, (1-a/c)
    fractional_distance_from1 = 1 - time_from1 / total_time  # 1-a/C
    fractional_distance_from2 = 1 - time_from2 / total_time  # 1-b/C

    # rows between which to interpolate
    row1 = power_df.loc[str(timestamp1)].copy()
    row2 = power_df.loc[str(timestamp2)].copy()

    # interpolated row
    interpolated_row = row1 * fractional_distance_from1 + row2 * fractional_distance_from2

    # returning interpolated value
    return interpolated_row


"""
Internal helpers end
Public fixed interval forecasting functions begin
"""


def get_default_fmi_forecast(interpolate=False) -> pd.DataFrame:
    """
    This function returns the whole 66~ish hour FMI forecast available at this moment in time.
    Timestamps in the forecast are every 60 minutes with a 30min offset. 12:30, 13:30 and so on, using UTC time.
    :param interpolate: Default false will skip interpolation. String "15min" will result in interpolated forecasts
    where power values are at 12:00, 12:15, 12:30...

    Interpolation works nicely with values which divide 60 into integers. 30, 20, 15, 12, 10, 6, 5, 4, 3, 2, 1
    :return:
    """

    # getting the hourly 66 hour forecast
    data = get_fmi_radiation_forecast()

    # if interpolation is left False, interpolation will not be done
    if interpolate is not False:
        # resampling to given time resolution, "15min" perhaps?
        data = data.resample(interpolate).asfreq()

        # interpolating nans from resampling
        data = data.interpolate(method="linear")
        # Note, this function supports other interpolation methods. Got a bunch of errors with them, but in theory
        # some interpolation functions could result in nicer output.

    # processing data with our pv model
    data = process_radiation_df(data)

    return data


def get_default_clearsky_forecast(timestep=60) -> pd.DataFrame:
    """

    """

    time_start = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(hours=3)
    time_start = datetime.datetime(time_start.year, time_start.month, time_start.day, time_start.hour)
    time_end = time_start + datetime.timedelta(hours=68)

    data = get_clearsky_estimate_for_interval(
        time_start,
        time_end,
        timestep)

    return data


"""
Public fixed interval forecasting functions end
Public flexible interval forecasting functions begin
"""


def get_fmi_forecast_for_interval(interval_start, interval_end):
    """
    Loads the complete fmi forecast and returns a subsection.

    Uses cache so if this or any other fmi function has been recently called, no additional server calls will be made.

    :param interval_start: Start time for subsection
    :param interval_end:  End time for subsection
    :return:
    """
    default_fmi_forecast = get_default_fmi_forecast()
    return default_fmi_forecast.loc[interval_start:interval_end]


def get_clearsky_estimate_for_interval(interval_start, interval_end, timestep=60):
    if site_latitude is None or site_longitude is None:
        raise ValueError(
            "Latitude and longitude must be defined before PV output is estimated."
            "Call pv_forecast.set_location(latitude, longitude) first with"
            " valid WGS84 coordinates."
        )

    if panel_tilt is None or panel_azimuth is None:
        raise ValueError(
            "Tilt and azimuth must be defined before PV output is estimated."
            " Call pv_forecast.set_angles(tilt, azimuth) first with"
            " valid 0-90, 0-360 degree panel angles."
        )

    # timeshifting
    # this cannot be used as setting a minute is not possible, this kills time offset function
    offset = 30

    interval_start = datetime.datetime(year=interval_start.year, month=interval_start.month, day=interval_start.day,
                                       hour=interval_start.hour, minute=offset)

    # step 1. getting clearsky radiation
    data = __get_clearsky_radiation_for_interval(interval_start, interval_end, timestep)

    # processing data with our pv model
    data = process_radiation_df(data)

    return data

def get_clearsky_estimate_for_times(times):

    if site_latitude is None or site_longitude is None:
        raise ValueError(
            "Latitude and longitude must be defined before PV output is estimated."
            "Call pv_forecast.set_location(latitude, longitude) first with"
            " valid WGS84 coordinates."
        )

    if panel_tilt is None or panel_azimuth is None:
        raise ValueError(
            "Tilt and azimuth must be defined before PV output is estimated."
            " Call pv_forecast.set_angles(tilt, azimuth) first with"
            " valid 0-90, 0-360 degree panel angles."
        )

    # step 1. getting clearsky radiation
    data = get_clearsky_radiation_for_times(times)

    # processing data with our pv model
    data = process_radiation_df(data)

    return data



def get_fmi_forecast_at_interpolated_time(given_time):
    fmi_power_forecast = get_default_fmi_forecast()
    return __interpolate_nearest_power_to_time_value(fmi_power_forecast, given_time)


"""
Public flexible interval forecast functions end
Other public functions begin
"""

def process_radiation_df_bifacial(data_in):
    """
    This function processes a radiation dataframe and estimates the output of a pv system.

    The input df must have columns:
    'time', 'dni', 'dhi', 'ghi'
    additional columns "T", "wind" and "albedo" are also useful

    time column is the mathematical point for which each row in the data is simulated for.
    Since weather at 18:00 represents weather between 17:00 and 18:00, the time column is often index-30min
    """

    data = data_in.copy()

    if "cloud_cover" not in data.columns:
        # If using pvlib clearsky data, there will not be a cloud cover column. Added here for compatibility.
        data["cloud_cover"] = 0

    # panel main surface:
    data_a = data.copy()
    # panel back surface:
    data_b = data.copy()

    if panel_tilt is None or panel_azimuth is None:
        raise ValueError(
            "Tilt and azimuth must be defined before PV output is estimated."
            " Call pv_forecast.set_angles(tilt, azimuth) first with"
            " valid 0-90, 0-360 degree panel angles."
        )




    # step 2. project irradiance components to plane of array:
    # panel front surface, same as always
    data_a = irradiance_transpositions.irradiance_df_to_poa_df(data_a, site_latitude, site_longitude, panel_tilt,
                                                             panel_azimuth)



    # panel back surface, requires recomputation of panel angles
    azimuth_b = panel_azimuth
    tilt_b = 180- panel_tilt

    #print("azimuth_b: " + str(azimuth_b))
    #print("tilt_b: " + str(tilt_b))
    data_b = irradiance_transpositions.irradiance_df_to_poa_df(data_b, site_latitude, site_longitude, tilt_b,
                                                             azimuth_b)


    # step 3. simulate how much of irradiance components is absorbed:
    data_a = reflection_estimator.add_reflection_corrected_poa_components_to_df(data_a, site_latitude, site_longitude,
                                                                              panel_tilt, panel_azimuth)

    data_b = reflection_estimator.add_reflection_corrected_poa_components_to_df(data_b, site_latitude, site_longitude,
                                                                              tilt_b, azimuth_b)


    # step 4. compute sum of reflection-corrected components:
    if "poa_ref_cor" in data_a.columns:
        #print("Reflection corrected POA already in dataframe, using it.")
        pass
    else:
        data_a = reflection_estimator.add_reflection_corrected_poa_to_df(data_a)

    if "poa_ref_cor_b" in data_b.columns:
        #print("Reflection corrected POA already in dataframe, using it.")
        data_b["poa_ref_cor"] = data_b["poa_ref_cor_b"]
    else:
        data_b = reflection_estimator.add_reflection_corrected_poa_to_df(data_b)

    #data_a = reflection_estimator.add_reflection_corrected_poa_to_df(data_a)
    #data_b = reflection_estimator.add_reflection_corrected_poa_to_df(data_b)


    # data_c = both sides, same as a+b when it comes to absorbed radiation
    data_c = pandas.DataFrame()
    data_c["time"] = data_a["time"]
    data_c["dni"] = data_a["dni"]
    data_c["dhi"] = data_a["dhi"]
    data_c["ghi"] = data_a["ghi"]
    data_c["cloud_cover"] = data_a["cloud_cover"]
    data_c["poa_ref_cor"] = data_a["poa_ref_cor"] + data_b["poa_ref_cor"]

    # adding temp to data if it exists
    if "T" in data_a.columns:
        data_c["T"] = data_a["T"]

    if "wind" in data_a.columns:
        data_c["wind"] = data_a["wind"]

    # copying module temp from input dataframe if it exists there
    if "module_temp" in data_a.columns:
        data_c["module_temp"] = data_a["module_temp"]

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    if "module_temp" not in data_c.columns:
        data_c = panel_temperature_estimator.add_estimated_panel_temperature(data_c)
    else:
        # print("Module temp already in data, using value from \"module_temp\" -column.")
        pass

    # step 6. estimate power output
    data_c = output_estimator.add_output_to_df(data_c)

    if not extended_output:
        # if extended output not in use, return only some columns
        return data_c[["T", "wind", "module_temp", "output"]]

    return data_c

def process_radiation_df(data_in):
    """
    This function processes a radiation dataframe and estimates the output of a pv system.

    The input df must have columns:
    'time', 'dni', 'dhi', 'ghi'
    additional columns "T", "wind" and "albedo" are also useful

    time column is the mathematical point for which each row in the data is simulated for.
    Since weather at 18:00 represents weather between 17:00 and 18:00, the time column is often index-30min
    """

    # this line breaks connections
    data = data_in.copy()

    #print("bifacial check")
    if bifacial:
        print("was bifacial, using bifacial processing")
        return process_radiation_df_bifacial(data)

    #print("was not bifacial, using common processing instead")

    if panel_tilt is None or panel_azimuth is None:
        raise ValueError(
            "Tilt and azimuth must be defined before PV output is estimated."
            " Call pv_forecast.set_angles(tilt, azimuth) first with"
            " valid 0-90, 0-360 degree panel angles."
        )


    if "cloud_cover" not in data.columns:
        # If using pvlib clearsky data, there will not be a cloud cover column. Added here for compatibility.
        data["cloud_cover"] = 0

    # print(data)
    # print(data.columns)

    # step 2. project irradiance components to plane of array:
    data = irradiance_transpositions.irradiance_df_to_poa_df(data, site_latitude, site_longitude, panel_tilt,
                                                             panel_azimuth)

    if "dni_shading" in data.columns:
        #print("dni_shading column detected in dataframe, multiplying dni_poa with (1-dni_shading)")

        # print("values pre change:")
        # print(data["dni_poa"])
        data["dni_poa"] = data["dni_poa"] * (1-data["dni_shading"])
        # print("values after change:")
        # print(data["dni_poa"])

    if "dhi_shading" in data.columns:
        #print("dhi_shading column detected in dataframe, multiplying dhi_poa with (1-dhi_shading)")

        # print("values pre change:")
        # print(data["dhi_poa"])
        data["dhi_poa"] = data["dhi_poa"] * (1-data["dhi_shading"])
        # print("values after change:")
        # print(data["dhi_poa"])


    # step 3. simulate how much of irradiance components is absorbed:
    data = reflection_estimator.add_reflection_corrected_poa_components_to_df(data, site_latitude, site_longitude,
                                                                              panel_tilt, panel_azimuth)

    # step 4. compute sum of reflection-corrected components:

    if "poa_ref_cor" in data.columns:
        print("Reflection corrected POA already in dataframe, using it.")
    else:
        data = reflection_estimator.add_reflection_corrected_poa_to_df(data)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    #print("Columns before module temp adding:")
    #print(data.columns)
    if "module_temp" not in data.columns:
        data = panel_temperature_estimator.add_estimated_panel_temperature(data)
    else:
        #print("Module temp already in data, using value from \"module_temp\" -column.")
        pass

    # step 6. estimate power output
    data = output_estimator.add_output_to_df(data)

    if not extended_output:
        # if extended output not in use, return only some columns
        return data[["T", "wind", "module_temp", "output"]]

    return data


def get_fmi_radiation_forecast():
    """
    This is a helper function for getting radiation data from FMI.
    :return:
    """
    interval_start = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(hours=6)
    # the line above creates a timezone naive utc timestamp. If timezone is included, server will return errors.
    # if time is local time, starting values will be wrong
    # looking 4 hours into the past just for some historical data to be included.

    interval_end = interval_start + datetime.timedelta(hours=70)

    if site_latitude is None or site_longitude is None:
        raise ValueError(
            "Latitude and longitude must be defined before PV output is estimated."
            "Call pv_forecast.set_location(latitude, longitude) first with"
            " valid WGS84 coordinates."
        )


    data = __get_fmi_forecast_for_interval(interval_start, interval_end)

    return data


"""
Public functions end
Dev functions begin
"""


def force_clear_fmi_cache():
    """
    This function will force clearing of FMI open data cache. Cache clearing should normally happen automatically when
    geolocation has been changed or when cache is old and so this function should be useless. Leaving it in for
    debugging.
    """

    meps_loader.clear_cache()

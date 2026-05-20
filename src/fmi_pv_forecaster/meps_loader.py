"""
This file retrieves irradiance values from FMI open API
Information on the service can be found here:
https://en.ilmatieteenlaitos.fi/open-data-manual-forecast-models

Data is available for a 66-hour period
Data updates every 3 hours starting from 00 UTC, slight variation in timing can occur
Data usually contains a couple of hours of historical data due to delays in running and transferring weather model data
between services before the fmi_pv_forecast becomes available.

Author: kalliov (Viivi Kallio).
Modifications by: TimoSalola (Timo Salola).
"""
import datetime as dt
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import numpy as np
import pandas
import pandas as pd
from fmiopendata.wfs import download_stored_query
from pvlib import location

cache_enabled = True
last_load_time = None
cached_data = None

min_seconds_between_fmi_calls = 60


def clear_cache():
    """
    Call this function to force cache clearing if cache is enabled.
    This function is automatically called when geolocation is changed.
    """
    global last_load_time
    global cached_data
    last_load_time = None
    cached_data = None


def get_solar_azimuth_zenit_fast(sim_dt: datetime, latitude, longitude):
    """
    Returns apparent solar zenith and solar azimuth angles in degrees.
    :param sim_dt: time to compute the solar position for.
    :param latitude: WGS84 latitude of pv system
    :param longitude: WGS84 longitude of pv system
    :return: azimuth, zenith
    """

    # panel location and installation parameters from config file
    panel_latitude = latitude
    panel_longitude = longitude

    # panel location object, required by pvlib
    panel_location = location.Location(panel_latitude, panel_longitude)

    # solar position object
    solar_position = panel_location.get_solarposition(sim_dt)

    # apparent zenith and azimuth, Using apparent for zenith as the atmosphere affects sun elevation.
    # apparent_zenith = Sun zenith as seen and observed from earth surface
    # zenith = True Sun zenith, would be observed if Earth had no atmosphere
    solar_apparent_zenith = solar_position["apparent_zenith"]
    solar_azimuth = solar_position["azimuth"]

    return solar_azimuth, solar_apparent_zenith


def collect_fmi_opendata(latitude: float, longitude: float,
                         start_time: datetime, end_time: datetime) -> pandas.DataFrame:
    """
    :param latitude:  wgs84 latitude of the pv system
    :param longitude: wgs84 longitude of the pv system
    :param start_time:  2013-03-05T12:00:00Z ISO TIME
    :param end_time:    2013-03-05T12:00:00Z ISO TIME
    :return: Pandas dataframe with columns ["time", "dni", "dhi", "ghi", "dir_hi", "albedo", "T", "wind", "cloud_cover"]
    """

    global cached_data
    global cache_enabled
    global last_load_time

    time_now = datetime.now()

    # print("checking caching")

    if cache_enabled:
        if last_load_time is None and cached_data is None:
            # print("Cache enabled but no data in cache. Loading data as normal and saving data to cache.")
            pass

        elif last_load_time is not None and cached_data is not None:
            # both last load time and cached data exist.
            seconds_since_cache_update = round((time_now - last_load_time).total_seconds())

            if seconds_since_cache_update > min_seconds_between_fmi_calls:
                # print("Cache age is " + str(seconds_since_cache_update)+ " seconds. Retrieving new data.")
                pass
            else:
                # print("Cache is new at " + str(seconds_since_cache_update) + " seconds. Reading data from cache.
                # This line should not print")
                pass
            print("Cached server call done.")
            return cached_data
        else:
            raise Exception(
                "Something wrong with caching. Last load time " + str(last_load_time))

    collection_string = "fmi::forecast::harmonie::surface::point::multipointcoverage"

    # List the wanted MEPS parameters
    parameters = ["Temperature",
                  "RadiationGlobalAccumulation",
                  "RadiationNetSurfaceSWAccumulation",
                  "RadiationSWAccumulation",
                  "WindSpeedMS",
                  "TotalCloudCover"
                  ]
    parameters_str = ','.join(parameters)

    # Collect data

    latlon = str(latitude) + "," + str(longitude)
    snd = download_stored_query(collection_string,
                                args=["latlon=" + latlon,
                                      "starttime=" + str(start_time),
                                      "endtime=" + str(end_time),
                                      'parameters=' + parameters_str])
    data = snd.data

    print("Server call done.")

    # checking if we got any data
    if len(data) == 0:
        raise Exception("FMI open data did not return a forecast with valid values. Check that geolocation is within "
                        "harmonie-arome model area shown in https://en.ilmatieteenlaitos.fi/weather-forecast-models "
                        "and that requested time interval contains hours between now("
                        + str(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")) + ") and "
                        "forecast interval end "
                        + str((datetime.now(timezone.utc) + timedelta(hours=66)).strftime("%Y-%m-%d %H:%M")))

    # print("Got " + str(len(data))+ " values as forecast.")

    # Times to use in forming dataframe
    data_list = []
    # Make the dict of dict of dict of.. into pandas dataframe
    for time_a, location_data in data.items():
        location = list(location_data.keys())[0]  # Get the location dynamically
        values = location_data[location]

        data_list.append({'Time': time_a,
                          'T': values['Air temperature']['value'],
                          'GHI_accum': values['Global radiation accumulation']['value'],
                          'NetSW_accum': values['Net short wave radiation accumulation at the surface']['value'],
                          'DirHI_accum': values['Short wave radiation accumulation']['value'],
                          'Wind speed': values['Wind speed']['value'],
                          'Total cloud cover': values['Total cloud cover']['value']})

    # Create a DataFrame and set time as index
    df = pd.DataFrame(data_list)

    df.set_index('Time', inplace=True)

    # index shift added since index is used as the time input of PVlib functions and using index is much easier
    # than using a separate time column
    df["time"] = df.index.copy()  # time backup
    # timeshift has to be here
    df.index = df.index + dt.timedelta(minutes=-30)

    # Calculate instant from accumulated values (only radiation parameters)
    diff = df.diff()
    df['GHI'] = diff['GHI_accum'] / (60 * 60)
    df['NetSW'] = diff['NetSW_accum'] / (60 * 60)
    df['DirHI'] = diff['DirHI_accum'] / (60 * 60)
    # GHI = grad_instant
    # DirHI = swavr_instant
    # netSW = nswrs_instant

    # Calculate albedo (refl/ghi), refl=ghi-net
    df['albedo'] = (df['GHI'] - df['NetSW']) / df['GHI']

    # restricting abledo to be within range of 0 to 1
    df['albedo'] = df['albedo'].mask(~df['albedo'].between(0, 1))

    # setting all nan values to mean of known values
    df['albedo'] = df['albedo'].fillna(df['albedo'].mean())

    # Calculate Diffuse horizontal from global and direct
    df['DHI'] = df['GHI'] - df['DirHI']
    #

    # Adding solar zenith angle to df
    df["sza"] = get_solar_azimuth_zenit_fast(df.index, latitude, longitude)[1]
    # solar zenit angle added

    # Calculate dni from dhi
    df['DNI'] = df['DirHI'] / np.cos(df['sza'] * (np.pi / 180))

    # Keep the necessary parameters
    df = df[['DNI', 'DHI', 'GHI', 'DirHI', 'albedo',
             'T', 'Wind speed', 'Total cloud cover']]

    df.columns = ["dni", "dhi", "ghi", "dir_hi", "albedo", "T", "wind", "cloud_cover"]
    df = df.drop('dir_hi', axis=1)


    # restricting values to zero
    clip_columns = ["dni", "dhi", "ghi"]
    df[clip_columns] = df[clip_columns].clip(lower=0.0)
    df.replace(-0.0, 0.0, inplace=True)

    # timeshift should not be done here, leaving as a comment for debugging reasons as this seems to cause all kinds
    # of odd symptoms in the PV model pipeline
    # df.index = df.index + dt.timedelta(minutes=-30)

    if cache_enabled:
        cached_data = df
        last_load_time = time_now

    return df


def __get_irradiance_pvlib(latitude, longitude, date_start: datetime, date_end: datetime,
                           minutes_between_measurements=60) -> pandas.DataFrame:
    """
    PVlib based clear sky irradiance modeling
    :param date: Datetime object containing a date
    :param mod: One of the 3 models supported by pvlib
    :return: Dataframe with ghi, dni, dhi. Or only GHI if using haurwitz
    """

    data_resolution = minutes_between_measurements

    # creating site data required by pvlib poa
    site = location.Location(latitude, longitude)

    # measurement frequency, for example "15min" or "60min"
    measurement_frequency = str(data_resolution) + "min"

    times = pd.date_range(start=date_start,
                          end=date_end,  # year + day for which the irradiance is calculated
                          freq=measurement_frequency,  # take measurement every 60 minutes
                          tz=site.tz)  # timezone

    # creating a clear sky and solar position entities
    clearsky = site.get_clearsky(times)

    # adds index as a separate time column, for some reason this is required as even a named index is not callable
    # with df[index_name] and df.index is not supported by function apply structures
    clearsky.insert(loc=0, column="time", value=clearsky.index)

    # returning clearsky irradiance df
    return clearsky

def __get_irradiance_pvlib_flexible_times(latitude, longitude, times):

    # additional function made for flexible time intervals

    # creating site data required by pvlib poa
    site = location.Location(latitude, longitude)

    # creating a clear sky and solar position entities
    clearsky = site.get_clearsky(times)

    # adds index as a separate time column, for some reason this is required as even a named index is not callable
    # with df[index_name] and df.index is not supported by function apply structures
    clearsky.insert(loc=0, column="time", value=clearsky.index)

    # returning clearsky irradiance df
    return clearsky



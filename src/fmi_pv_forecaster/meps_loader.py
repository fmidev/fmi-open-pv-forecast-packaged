from datetime import datetime, UTC, timedelta
import numpy as np
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from pvlib import location


cache_enabled = True
last_load_time = None
cached_data = None

min_seconds_between_fmi_calls = 60


"""
This file contains a new version of fmi open data forecast retrieval. Old version is meps_loader_old.py and it's not
being called anymore.

"""


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

def clear_cache():
    """
    Call this function to force cache clearing if cache is enabled.
    This function is automatically called when geolocation is changed.
    """
    global last_load_time
    global cached_data
    last_load_time = None
    cached_data = None

def collect_fmi_opendata(latitude: float, longitude: float) -> pd.DataFrame:
    """
    This is the new version of FMI open data forecast retrieval. Old relied on GPL licensed library.


    :param latitude: WGS84 latitude
    :param longitude: WGS84 longitude
    :return: time, dni, dhi, ghi, wind, T, cloud_cover, albedo - dataframe, time in utc
    """

    ### Cache bit begins

    global cached_data
    global cache_enabled
    global last_load_time

    time_now = datetime.now()

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
            #print("Cached server call done.")
            return cached_data
        else:
            raise Exception(
                "Something wrong with caching. Last load time " + str(last_load_time))

    ### Cache bit ends


    # this is what the url used to look like in our previous retrieval functions
    # url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage&latlon=60,25&starttime=2026-09-07 07:49:28.070700&endtime=2026-09-10 05:49:28.070700&parameters=Temperature,RadiationGlobalAccumulation,RadiationNetSurfaceSWAccumulation,RadiationSWAccumulation,WindSpeedMS,TotalCloudCover"

    # creating url in parts
    # base stuff in part 1
    url_part1 = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage"

    # geolocation in part 2
    url_part2 = "&latlon="+str(latitude)+","+str(longitude)

    # part 3 contains time interval, going with a minimal date since this seems to work
    url_part3 = "&starttime=" + "-6h" + "&endtime=" + str(datetime.now() + timedelta(hours=63))

    # url part 4 consists of parameters
    parameters = ["Temperature", "WindSpeedMS", "TotalCloudCover", "RadiationGlobalAccumulation",
                  "RadiationNetSurfaceSWAccumulation",
                  "RadiationSWAccumulation"]

    url_part4 = "&parameters=" +','.join(parameters)

    # complete url
    url = url_part1 + url_part2 + url_part3 + url_part4

    # requesting data from FMI servers
    response = requests.get(url)  # http return code and site response is stored here

    # extracting returned data
    response_xml = response.text

    # creating dataframe from xml with helper function
    df = main_xml_to_df(response_xml)

    return df

def main_xml_to_df(xml_string):
    """
    This function parses
    :param str:
    :return:
    """


    root = ET.fromstring(xml_string)

    ns = {
        "gmlcov": "http://www.opengis.net/gmlcov/1.0",
        "gml": "http://www.opengis.net/gml/3.2",
        "swe": "http://www.opengis.net/swe/2.0"
    }

    # --- 1. Extract timestamps from gmlcov:positions ---
    pos_elem = root.find(".//gmlcov:positions", ns)

    timestamps = []
    for line in pos_elem.text.strip().splitlines():
        parts = line.split()
        epoch = int(parts[-1])  # last column is timestamp
        timestamps.append(datetime.fromtimestamp(epoch, UTC))

    # --- 2. Extract field names from swe:field ---
    fields = root.findall(".//swe:field", ns)
    field_names = [f.attrib["name"] for f in fields]

    # --- 3. Extract values from doubleOrNilReasonTupleList ---
    values_elem = root.find(".//gml:doubleOrNilReasonTupleList", ns)

    rows = []
    for line in values_elem.text.strip().splitlines():
        values = list(map(float, line.split()))
        rows.append(values)

    # --- 4. Build DataFrame ---
    df = pd.DataFrame(rows, columns=field_names)
    df.insert(0, "timestamp", timestamps)

    df.index = df["timestamp"]

    # these are the columns we will eventually create,
    # these should be from here:
    # ['dni', 'dhi', 'ghi', 'albedo', 'T', 'wind', 'cloud_cover',
    #
    # these are calculated later:
    # 'dni_poa', 'dhi_poa', 'ghi_poa', 'poa', 'dni_rc', 'dhi_rc', 'ghi_rc',
    # 'poa_ref_cor', 'module_temp', 'output']

    # some values are accumulated, need to calculate diff to get the accumulated values:
    diff = df.diff()
    df['ghi'] = diff['RadiationGlobalAccumulation'] / (60 * 60)
    df['netsw'] = diff['RadiationNetSurfaceSWAccumulation'] / (60 * 60)
    df['dirhi'] = diff['RadiationSWAccumulation'] / (60 * 60)

    # calculating ground reflectivity
    df["albedo"] = (df["ghi"] -df["netsw"])/df["ghi"]

    # albedo can be a bit wonky with values outside range 0 to 1
    # this section replaces values outside valid range with nan, and sets values naxt to these nans as nans
    # finally interpolating linearly

    df["albedo"] = df["albedo"].where(
        (df["albedo"] >= 0) & (df["albedo"] <= 1),
        np.nan
    )

    nan_mask = df["albedo"].isna()

    neighbor_mask = (
            nan_mask |
            nan_mask.shift(1, fill_value=False) |
            nan_mask.shift(-1, fill_value=False)
    )

    df["albedo"] = df["albedo"].mask(neighbor_mask)
    df["albedo"] = df["albedo"].interpolate(method="linear", limit_direction="both")


    # calculating atmopsheric scattering
    df["dhi"] = df["ghi"]-df["dirhi"]

    # solar zenith angle for dni calculations
    df["sza"] = get_solar_azimuth_zenit_fast(df.index, 64, 25)[1]

    # Calculate dni from dhi and sun angle
    df['dni'] = df['dirhi'] / np.cos(df['sza'] * (np.pi / 180))


    # creating export DF and adding variables to it
    df_out = pd.DataFrame()
    df_out["dni"] = df["dni"]
    df_out["dhi"] = df["dhi"]
    df_out["ghi"] = df["ghi"]
    df_out["wind"] = df["WindSpeedMS"]
    df_out["T"] = df["Temperature"]
    df_out["cloud_cover"] = df["TotalCloudCover"]
    df_out["albedo"] = df["albedo"]
    df_out.index.name = "Time"

    # restricting values to zero
    clip_columns = ["dni", "dhi", "ghi"]
    df_out[clip_columns] = df_out[clip_columns].clip(lower=0.0)
    df_out.replace(-0.0, 0.0, inplace=True)

    # export df should now have all needed variables
    return df_out

def get_solar_azimuth_zenit_fast(sim_dt: datetime, latitude, longitude):
    """
    This function exists elsewhere in the system, but keeping a local copy in this file just to keep everything
    contained. Inputs are time and geolocation in wgs84 format.
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

def __get_irradiance_pvlib(latitude, longitude, date_start: datetime, date_end: datetime,
                           minutes_between_measurements=60) -> pd.DataFrame:
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


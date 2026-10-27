import datetime

import pandas
import pandas as pd
import pytz

import fmi_pv_forecaster.helpers.default_parameters
from fmi_pv_forecaster import meps_loader
from fmi_pv_forecaster.helpers import irradiance_transpositions, output_estimator
from fmi_pv_forecaster.helpers import panel_temperature_estimator
from fmi_pv_forecaster.helpers import reflection_estimator

# These variables must be set before pv forecast is called
site_latitude = None
site_longitude = None
panel_tilt = None
panel_azimuth = None

# These variables can be changed if desired
extended_output = False  # set to true and the radiation parameters and intermediate steps of the pv output calculation
# will be included in the output

bifacial = False
backside_efficiency = 1.0

snow_slide_modeling = False

power_rating = 1  # power in kw

timezone = "UTC"

def print_info():
    """
    This function prints the parameters of the model. Useful for debugging and research.
    """


    ### Common bits go here
    print("--- System information ---")
    print("System location(WGS84): " + str(site_latitude) + "°, " + str(site_longitude) + "°")
    if panel_tilt is not None and panel_azimuth is not None:
        print("Panel angles: " + str(panel_tilt) + "°, " + str(panel_azimuth) + "°")
    else:
        print("Panel angles: None")
    print("System power: " + str(power_rating) +"kW")

    ### Extra toggles and if they are on or not
    print("-- Extra options --")
    if extended_output:
        print("Extended output: ON")
    else:
        print("Extended output: OFF")

    if bifacial:
        print("Bifacial modeling: ON")
        print("Backside efficiency: " + str(backside_efficiency))
    else:
        print("Bifacial modeling: OFF")


    ###
    print("-- Model parameters --")

    mr_string = "Panel reflectivity constant (Martin & Ruiz 2001): " + str(reflection_estimator.reflectance_constant)

    print(mr_string)

    king_string = ("Panel temperature constants (King 2004): "
                   + "a=" + str(panel_temperature_estimator.constant_a)
                   + ", b=" + str(panel_temperature_estimator.constant_b))
    print(king_string)

    huld_string = ("System efficiency constants (Huld 2011): ["
                    + str(output_estimator.k1) + ", "
                    + str(output_estimator.k2) + ", "
                    + str(output_estimator.k3) + ", "
                    + str(output_estimator.k4) + ", "
                    + str(output_estimator.k5) + ", "
                    + str(output_estimator.k6) + "]")
    print(huld_string)

    print("--- System information ends ---")




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
Parameter setting functions begin here, some mandatory, some optional.
"""


def set_location(latitude, longitude):
    """
    Call this function to set the PV site latitude and longitude. Values outside metcoop forecast region will cause
    issues with FMI forecast retrieval, but modeling functions for clearsky and your own radiation data will still work
    without issues.

    :param latitude: WGS84 latitude as float. Valid values are -90 to 90.
    :param longitude: WGS84 longitude in float format. eq 60.4312. Valid values are -180 to 180.
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


def force_clear_fmi_cache():
    """
    This package keeps a single FMI weather forecasts in memory in order to limit the amount of server calls.
    This function removes the forecast from memory. Calling any of the .get_fmi_XXX functions after clearing
    cache will request a new forecast and store it in cache.

    Caching can also be disabled with .set_cache(False)

    Cache will also be cleared if geolocation of the installation is changed. This is done because forecasts retrieved
    from FMI are only for a single point.

    This function was originally made to test if caching works, but I'm leaving it in for experimentation.
    """

    meps_loader.clear_cache()


def set_angles(p_tilt, p_azimuth):
    """
    Call this function to set the panel angles for the PV system.
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
    This function sets the power rating of the PV system. Default value is 1 and this means that the system will
    simulate the DC output of a 1kW PV installation. 0.2 would mean 200W and 13 would be 13kW.


    :param nominal_power: nominal power in kW, float/int.
    :return: None
    """
    global power_rating
    power_rating = nominal_power
    output_estimator.rated_power = nominal_power


def set_default_air_temp(air_temp_c: float):
    """
    This function will set the air temperature(in Celsius) which will be used in PV output modeling if input
    dataframe doesn't contain a T column(air temp).

    FMI forecasts do not use the default value as air temperature is given by the forecast API.

    Air temperature influences efficiency of panels, good value here would be the max(or near max) air temp during the
    time you are modeling.
    """
    fmi_pv_forecaster.helpers.default_parameters.air_temperature = air_temp_c
    # print("Air temperature for clearsky simulations set at: " +
    # str(fmi_pv_forecast.helpers.default_parameters.air_temperature)+ "°C")


def set_default_wind_speed(wind_speed_ms: float):
    """
    This function will set the wind speed(m/s) at 10m which will be used in PV output modeling if input
    dataframe doesn't contain a wind column.

    FMI forecasts do not use the default value as wind speed is given by the forecast API.

    Wind at 10m and .set_module_elevation are used to calculate wind speed at PV panels. Wind at panels transfers heat
    away from PV panels and decreases the difference between air temperature and panel temperature.

    Default value is 2 meters.

    :param wind_speed_ms: wind speed at 10m above ground in m/s
    """
    fmi_pv_forecaster.helpers.default_parameters.wind_speed = wind_speed_ms
    # print("Wind speed for clearsky simulations set at: " +
    # str(fmi_pv_forecast.helpers.default_parameters.wind_speed)+ "ms")


def set_module_elevation(module_elevation_m: float):
    """
    This function will set the physical module elevation(measured from ground, not sea level). Module elevation and
    wind speed at 10m are used together to estimate the wind at panel elevation.

    Higher than actual elevation can be used to compensate for really windy locations and exposed panels. Lower for
    sheltered panels.

    If you are processing external data with wind measured at panel elevation, set elevation at 10m and use included
    wind speed. This way elevation compensation will not be done.

    Default value is 7 meters.

    :param module_elevation_m: module elevation in meters measured from ground
    """

    fmi_pv_forecaster.helpers.default_parameters.panel_elevation = module_elevation_m



def set_default_albedo(albedo: float):
    """
    Albedo here means ground reflectivity around the PV panel. Range is [0,1] with 0.12 being similar to grey old
    asphalt and 0.8 similar to snow. Albedo article on wikipedia has a nice table of values.

    Default value is 0.15 which is quite low.

    Albedo influences PV output on high tilt angle panels, but influence on low tilt systems is minor.

    :param albedo: albedo(ground reflectivity/brightness) in [0,1].
    """

    fmi_pv_forecaster.helpers.default_parameters.albedo = albedo


def set_cache(cache_on):
    """
    This package was built with the intention of having cache always on. And by default it is on.

    Disabling cache will cause every function with FMI in its name to make a new server query to
    FMI servers. This will result in unnecessary server calls and server may even refuse calls if load from your IP
    is too high.

    Having cache on will only make new server calls if data isn't cached yet, caching was done
    over a minute ago, geolocation was changed or cache was manually purged.
    """

    meps_loader.cache_enabled = cache_on


def set_bifacial(bifacial_on):
    """
    Bifaciality toggle, turning this on will estimate the PV output for a bifacial panel where front surface
    orientation matches the given panel angles, and backside is automatically calculated as the opposite side.

    Current model is fairly simple, temperatures and efficiency might be off. Set a custom backside efficiency with
    .set_relative_bifacial_backside_efficiency()

    :param bifacial_on: Boolean value, True for on, False for off
    :return:
    """
    global bifacial
    bifacial = bifacial_on


def set_relative_bifacial_backside_efficiency(bs_efficiency):
    """
    Bifacial panels have wirings/logic on the backside and thus backside is often a couple of percents worse at
    generating power than the frontside. This varies between panels. This function can be used to set custom multipliers.

    Default value is 1.0.


    :param bs_efficiency: Float in range of [0.7, 0.9] would be typical. 1.0 can be used for testing purposes.
    :return:
    """

    global backside_efficiency
    backside_efficiency = bs_efficiency


def set_snow_sliding(snow_on):
    """
    Turning snow sliding on will add column "snow sliding" into the model. This column represents the snow temperature
    and the model is based on the Marion model. When column value is positive, snow is being actively melted, and it
    can completely slide off from panels if tilt angle is sufficient and if there's nothing blocking the way.

    The value in the snow sliding column is also related to air temperature. At snow sliding = 3.2, ambient air could
    cool down by 3.2 degrees before snow stops melting.

    NOTE: We have not tested this model in practive. Physics looks good, but can't yet tell how accurate this is.

    :param snow_on: Boolean value, True for on, False for off
    """
    global snow_slide_modeling
    snow_slide_modeling = snow_on

def set_panel_reflectivity_model_constant(new_reflectivity_value : float):
    """
    Sets panel reflectivity constant used by martin&ruiz 2001 model. Reflectivity
    constant has to be between 0 and 1.

    Set to "None" to return default value for polycrystalline panels.
    """

    if new_reflectivity_value is None:
        reflection_estimator.reflectance_constant = 0.159
    elif type(new_reflectivity_value) is not float:
        raise TypeError("new_reflectivity value should be a float")
    elif new_reflectivity_value < 0 or new_reflectivity_value > 1:
        raise ValueError("Reflectivity value must be between 0 and 1")
    else:
        reflection_estimator.reflectance_constant = new_reflectivity_value

def set_panel_temperature_model_constants(a: float, b: float):
    """
    This function sets constants used by King 2004 panel temperature model.
    Higher values(closer to zero as these should always be negative) for a and b result in higher modeled panel
    temperatures. Constant b deals with wind derived cooling. Constant a handles the rest.

    Default values are for polycrystalline panels. Set to "None" to return defaults.
    """

    if a is None:
        panel_temperature_estimator.constant_a = -3.47
    else:
        panel_temperature_estimator.constant_a = a

    if b is None:
        panel_temperature_estimator.constant_b = -0.0594
    else:
        panel_temperature_estimator.constant_b = b

def set_output_model_constants(constants: list, min_efficiency = 0.5, max_efficiency = 1.0):
    """
    This functions sets the 6 Huld model constants from user given list.
    Set list to None to return default values.

    Default values are the original huld values for crystalline silicon panels.

    """

    if constants is None:
        output_estimator.k1 = -0.017162
        output_estimator.k2 = -0.040289
        output_estimator.k3 = -0.004681
        output_estimator.k4 = 0.000148
        output_estimator.k5 = 0.000169
        output_estimator.k6 = 0.000005
    elif type(constants) is not list:
        raise ValueError("Constants must be given as a list.")
    elif len(constants) != 6:
        raise ValueError("Output model constants must have 6 values.")
    else:
        output_estimator.k1 = constants[0]
        output_estimator.k2 = constants[1]
        output_estimator.k3 = constants[2]
        output_estimator.k4 = constants[3]
        output_estimator.k5 = constants[4]
        output_estimator.k6 = constants[5]


    if min_efficiency is None:
        output_estimator.min_efficiency = 0.5
    elif type(min_efficiency) is float and min_efficiency >= 0 and min_efficiency <= 1.0:
        output_estimator.min_efficiency = min_efficiency
    else:
        raise ValueError("Min_efficiency must be between 0 and 1, or \"None\" which resets back to 0.5.")

    if max_efficiency is None:
        output_estimator.max_efficiency = 1.0
    elif type(max_efficiency) is float and max_efficiency >= 0 and max_efficiency <= 1.0:
        output_estimator.max_efficiency = max_efficiency
    else:
        raise ValueError("Max_efficiency must be between 0 and 1, or \"None\" which resets back to 1.0",)




"""
Parameter setting functions end here.
Internal helper functions begin here. These are not exposed outside the package
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



"""
Internal helper functions  end here.
! Public functions begin
Starting with radiation table processing.
"""



def process_radiation_df(data):
    """
    This function processes a radiation dataframe and estimates the output of a pv system.

    The input df must have columns:
    'time', 'dni', 'dhi', 'ghi'
    additional columns "T", "wind" and "albedo" are also useful. Those contain the ambient air temperature, wind speed
    and ground reflectivity. If not included in the dataframe, defaults from the package are used. Those defaults can
    be adjusted with .set_default_xxx -functions.

    time column is the exact mathematical point for which each row in the data is simulated for. So if this is wrong,
    sun position will be wrong, and you will get wrong results. Since weather at 18:00 can represent the exact weather
    at 18:00, or the average of 17:00 to 18:00. You need to figure out how times are indexed in your dataset.

    With FMI radiation data, timestamp 18:00 represent time interval of 17:00 to 18:00, which is why a 30-minute time
    shift is needed.
    """

    #print("bifacial check")
    if bifacial:
        #print("was bifacial, using bifacial processing instead")
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

    # step 3. simulate how much of irradiance components is absorbed:
    data = reflection_estimator.add_reflection_corrected_poa_components_to_df(data, site_latitude, site_longitude,
                                                                              panel_tilt, panel_azimuth)

    # step 4. compute sum of reflection-corrected components:
    data = reflection_estimator.add_reflection_corrected_poa_to_df(data)


    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    data = panel_temperature_estimator.add_estimated_panel_temperature(data)

    if snow_slide_modeling:
        #print("Snow slide modeling is on")
        # uses a modified marion model, has to be after step 5 due to T requirement, which is only added to the data in
        # step 5 if it is missing.
        """
        Marion model:
        T_ambient > Gpoa/-80
        """
        data["degrees above snowsliding"] = data["T"] + data["poa"] / 80

    # step 6. estimate power output
    data = output_estimator.add_output_to_df(data)

    if not extended_output:
        # if extended output not in use, return only some columns
        if snow_slide_modeling:
            return data[["T", "wind", "module_temp","degrees above snowsliding", "output"]]
        else:
            return data[["T", "wind", "module_temp", "output"]]

    return data


def process_radiation_df_bifacial(data_in):
    """
    This function processes a radiation dataframe and estimates the output of a pv system.

    The input df must have columns:
    'time', 'dni', 'dhi', 'ghi'
    additional columns "T", "wind" and "albedo" are also useful

    time column is the mathematical point for which each row in the data is simulated for.
    Since weather at 18:00 represents weather between 17:00 and 18:00, the time column is often index-30min
    """

    if "cloud_cover" not in data_in.columns:
        # If using pvlib clearsky data, there will not be a cloud cover column. Added here for compatibility.
        data_in["cloud_cover"] = 0

    # panel main surface:
    data_a = data_in.copy()
    # panel back surface:
    data_b = data_in.copy()

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
    azimuth_b = (panel_azimuth + 180) % 360
    tilt_b = 180 - panel_tilt

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
    #print("Phase 4")
    data_a = reflection_estimator.add_reflection_corrected_poa_to_df(data_a)

    data_b = reflection_estimator.add_reflection_corrected_poa_to_df(data_b)

    output = data_a.copy()

    # 'time', 'ghi', 'dni', 'dhi', 'cloud_cover', 'dni_poa', 'dhi_poa',
    #        'ghi_poa', 'poa', 'dni_rc', 'dhi_rc', 'ghi_rc', 'poa_ref_cor'

    output["dni_poa_back"] = data_b["dni_poa"]
    output["dhi_poa_back"] = data_b["dhi_poa"]
    output["ghi_poa_back"] = data_b["ghi_poa"]

    output["dni_rc_back"] = data_b["dni_rc"]
    output["dhi_rc_back"] = data_b["dhi_rc"]
    output["ghi_rc_back"] = data_b["ghi_rc"]

    # adding absorbed radiation values for front, back and both sides.
    output["poa_ref_cor_front"] = data_a["poa_ref_cor"]
    output["poa_ref_cor_back"] = data_b["poa_ref_cor"]

    # adding both here at 100% for temperature calculations
    output["poa_ref_cor"] = output["poa_ref_cor_front"] + output["poa_ref_cor_back"]

    #print("phase 5")

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    output = panel_temperature_estimator.add_estimated_panel_temperature(output)

    # Rewriting the total absorbed radiation using backsíde efficiency as a backside multiplier.
    # This may appear odd, but I'm making the assumption that backside efficiency doesn't matter when it comes to
    # temperatures, but it does matter for output estimation.
    output["poa_ref_cor"] = output["poa_ref_cor_front"] + output["poa_ref_cor_back"] * backside_efficiency

    # step 6. estimate power output
    output = output_estimator.add_output_to_df(output)

    if not extended_output:
        # if extended output not in use, return only some columns
        #print("output not extended, returning minimal set of values")
        return output[["T", "wind", "module_temp", "output"]]

    #print("output was extended, returning all values")
    return output



"""
Flexible forecast functions with custom intervals:
"""


def get_clearsky_forecast_for_interval(interval_start, interval_end, timestep=60):
    """
    Returns an optimistic weather-unaware PV production for selected time interval using selected timestep.
    This clearsky forecast uses constant or given air temp, wind speed and albedo values. Set them with
    .set_default_air_temp, .set_default_albedo, .set_default_wind_speed

    :param interval_start: Datetime with year, month, day, hour. Minute and second will be ignored and set to zero.
    :param interval_end:  Datetime with year, month, day, hour. Minute and second will be ignored and set to zero.
    :param timestep: Minutes between rows in forecast. Only tested with integers.
    :return: DF with columns: datetime index, T, wind, module_temp, output. T is ambient air temperature in C. wind is
    wind speed in m/s.

    Example: interval_start = datetime(2026-08-17 13:20), interval_end = datetime(2026-08-17 13:20), timestep = 10
    Output:
                                T  wind  module_temp       output
    2026-08-17 13:00:00+00:00  20     2    39.187484  2581.720278
    2026-08-17 13:10:00+00:00  20     2    38.527107  2499.579738
    2026-08-17 13:20:00+00:00  20     2    37.833034  2412.422395
    2026-08-17 13:30:00+00:00  20     2    37.106726  2320.309278
    ...
    2026-08-18 12:50:00+00:00  20     2    39.691894  2643.946165
    2026-08-18 13:00:00+00:00  20     2    39.064610  2566.494637

    """



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


    interval_start = datetime.datetime(year=interval_start.year, month=interval_start.month, day=interval_start.day,
                                       hour=interval_start.hour, minute=0)

    interval_end = datetime.datetime(year=interval_end.year, month=interval_end.month, day=interval_end.day,
                                       hour=interval_end.hour, minute=0)

    # step 1. getting clearsky radiation
    data = __get_clearsky_radiation_for_interval(interval_start, interval_end, timestep)

    # processing data with our pv model
    data = process_radiation_df(data)

    return data


def get_fmi_forecast_for_interval(interval_start, interval_end):
    """
    Loads the complete fmi forecast and returns a subsection.

    Uses cache so if this or any other fmi function has been recently called, no additional server calls will be made.

    :param interval_start: Datetime, Start time for subsection
    :param interval_end: Datetime, End time for subsection
    :return:
    """
    default_fmi_forecast = get_default_fmi_forecast()
    return default_fmi_forecast.loc[interval_start:interval_end]


"""
Fixed interval forecast functions begin here
"""


def get_default_fmi_forecast(interpolate=False):
    """
    This function returns the whole 66~ish hour FMI forecast available at this moment in time.
    Timestamps in the forecast are every 60 minutes with a 30min offset. 12:30, 13:30 and so on, using UTC time.
    :param interpolate: Default false will skip interpolation. Interpolate = "15min" will result in interpolated
    forecasts where power values are at 12:00, 12:15, 12:30...

    Interpolation works nicely with values which divide 60 into integers.
    30, 20, 15, 12, 10, 6, 5, 4, 3, 2, 1.

    :return:
    """

    # getting the hourly 66-hour forecast
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


def get_default_clearsky_forecast(timestep=60):
    """
    This function returns an approximation for the clearsky PV output during a time window which should cover the
    FMI forecast based PV output from "get_default_fmi_forecast()"

    Forecast will have 60 minute time resolution, 70 hours of measurements and first measurement will be at xx:00 where
    xx is current hour.

    This clearsky forecast relies on default wind speed, air temperature and albedo built into the package. Adjust them
    with functions .set_default_air_temp, .set_default_albedo, .set_default_wind_speed

    :param timestep: Timestep in minutes between rows of the forecast. Default is 60.
    """

    time_start = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(hours=3)
    time_start = datetime.datetime(time_start.year, time_start.month, time_start.day, time_start.hour)
    time_end = time_start + datetime.timedelta(hours=68)

    data = get_clearsky_forecast_for_interval(
        time_start,
        time_end,
        timestep)

    return data


# Custom hour/day functions below this line


def get_fmi_forecast_at_interpolated_time(given_time):
    """
    This is a somewhat odd function. It will return the FMI weather forecast based PV forecast at the given time as
    long as the time is within the forecast window.

    So if you want to get the PV power today at this very second(12:43:33 for example), then this is the function to use.
    As the package uses cached FMI forecasts, you could call this function in a loop a thousand times if you really
    wanted to, without that resulting in any additional network traffic.

    Note that since this uses linear interpolation, outputs are just approximations of likely current output.


    :param given_time: datetime with seconds. Has to be within the approximate interval of [now, now+60hours]
    :return:
    """


    fmi_power_forecast = get_default_fmi_forecast()
    return __interpolate_nearest_power_to_time_value(fmi_power_forecast, given_time)


def __interpolate_nearest_power_to_time_value(power_df, time_value):
    """
    This column interpolates 2 nearest rows with linear interpolation and returns a single row which is the linear
    inbetween of the 2 nearest rows. This function expects index to be hh:30 and hourly. eq. 13:30, 14:30 and so on.
    :param power_df:
    :param time_value:
    :return:
    """

    time_value = pd.Timestamp(time_value)

    # Match the timezone of the DataFrame index.
    index_tz = power_df.index.tz

    if index_tz is not None:
        if time_value.tzinfo is None:
            time_value = time_value.tz_localize(index_tz)
        else:
            time_value = time_value.tz_convert(index_tz)
    elif time_value.tzinfo is not None:
        time_value = time_value.tz_localize(None)

    # Find the surrounding hh:30 timestamps.
    base_timestamp = time_value.replace(minute=30, second=0, microsecond=0)

    if time_value.minute < 30:
        timestamp1 = base_timestamp - pd.Timedelta(hours=1)
        timestamp2 = base_timestamp
    else:
        timestamp1 = base_timestamp
        timestamp2 = base_timestamp + pd.Timedelta(hours=1)

    # Check that both timestamps exist in the index.
    if timestamp1 not in power_df.index or timestamp2 not in power_df.index:
        return None

    # Calculate interpolation weights.
    total_time = timestamp2 - timestamp1
    fractional_distance_from1 = (timestamp2 - time_value) / total_time
    fractional_distance_from2 = (time_value - timestamp1) / total_time

    # A                         B
    # o------X------------------o
    # |--a---|-------b----------|
    # |------------C------------|

    # X = A*(1- a/C) + B*(1 - b/C)
    # C = 1
    # a = 0.1, b = 0.9
    # X = A*(0.9) + B*(0.1)

    # Retrieve the rows.
    row1 = power_df.loc[timestamp1]
    row2 = power_df.loc[timestamp2]

    # Linear interpolation.
    interpolated_row = (
            row1 * fractional_distance_from1
            + row2 * fractional_distance_from2
    )

    return interpolated_row


def get_fmi_radiation_forecast():
    """
    This function doesn't return a PV forecast, but rather the radiation and weather forecast that the PV forecast
    is based on.

    If you want to examine radiation forecasts or modify them in some way, you could call this function and
    .process_radiation_df(df) with the output of this function as an input.
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



    data = meps_loader.collect_fmi_opendata(site_latitude, site_longitude)

    return data



#set_location(60, 24)
#set_angles(15, 135)
#data = get_default_fmi_forecast()
#print_full(data)
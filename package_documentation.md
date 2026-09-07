# Package documentation 

Version 0.1.2

This file contains a rather verbose explanation of the functions available via this package.

---

Functions accessible to the user can be split into two main categories. Input functions which are used to feed
system parameters to the PV model, and forecasting functions which run the PV model and generate a forecast.

There are also developmental functions, but these are listed more as a curiosity than something users should
actively have to rely on or even be aware of.

<!-- TOC -->
* [Package documentation](#package-documentation)
* [1. Input functions](#1-input-functions)
  * [1.1. Required input functions](#11-required-input-functions)
  * [1.2. Optional input functions](#12-optional-input-functions)
  * [1.3. Conditional input functions](#13-conditional-input-functions)
* [2. Forecasting functions](#2-forecasting-functions)
  * [2.1. FMI forecasting functions](#21-fmi-forecasting-functions)
    * [2.1.1. Radiation forecasting function](#211-radiation-forecasting-function)
    * [2.1.2. Default FMI forecast](#212-default-fmi-forecast)
    * [2.1.3. Interval from FMI forecast](#213-interval-from-fmi-forecast)
    * [2.1.4. FMI forecast at interpolated time](#214-fmi-forecast-at-interpolated-time)
  * [2.2. Clear sky forecasting functions](#22-clear-sky-forecasting-functions)
  * [2.3. External data processing functions](#23-external-data-processing-functions)
* [3. Developmental functions](#3-developmental-functions)
<!-- TOC -->





---

# 1. Input functions

These functions set the parameters required by the PV model. Input functions can be split into 3 types:

* **Required:** The PV model will not work unless all of these functions are called with valid input values.
* **Optional:** The PV model will run even if these functions are not called, but calling these functions with valid
  input values can increase model accuracy.
* **Conditional:** The PV model will run even if these functions are not called. The values set by these functions
  will be ignored in some cases.

## 1.1. Required input functions

```python
pvfc.set_angles(tilt, azimuth)
pvfc.set_location(latitude, longitude)
```

* tilt: In degrees. Horisontal panel has tilt 0°. Vertical panel has 90°.
* azimuth: In degrees, [0°, 360°]. North facing panels have azimuth 0°, east 90° etc.
* latitude: In WGS84 coordinate format. [-90°, 90°]
* longitude : In WGS84 coordinate format. [-180°, 180°]

Coordinates can be retrieved from google maps. When browsing around, your url will contain the coordinates.

Tilt and azimuth should be set to an accuracy of 1 degree if possible. Deviations higher than 5 degrees can cause
noticeable modeling errors. If you have a method for plotting both forecasts and actual PV output, you can
and should use the actual PV output for tuning the input parameters.

Geolocation does not have to be exact and 1km from actual location is good enough. Even offsets of 5 kilometers
should not make a big difference due to uncertainties in weather forecasts. 

## 1.2. Optional input functions

```python
pvfc.set_module_elevation(elevation)
pvfc.set_nominal_power_kw(power_kw)
```

* elevation: Module distance from local ground level in meters. Panels on top of buildings have elevation of building
  height + distance from roof. Has a default value of 7.
* power_kw: Combined nominal power of the PV panels in the system in kilowatts. Has a default value of 1.

## 1.3. Conditional input functions

```python
pvfc.set_default_air_temp(degrees_C)
pvfc.set_default_albedo(albedo)
pvfc.set_default_wind_speed(wind_ms)
```

* degrees_C: Air temperature in Celsius. Overridden by "T" column in dataframe if column exists. Default is 20 degrees.
* albedo: Ground reflectivity in range [0,1]. Use 0.15 for dark ground, 0.6 for snow. Overridden by "albedo"
  column in dataframe if column exists. Default is 0.15.
* wind_ms: Wind speed in meters per second. Overridden by "wind" column in dataframe if column exists.
  Default value is 2.

---

## 1.4. Toggles

```python
pvfc.set_extended_output(True)
pvfc.set_snow_sliding(True)
pvfc.set_bifacial(True)
```
Extended output will not remove extra columns generated during processing of the input dataframe. This may have
uses for debugging or other purposes.

Set snow sliding will add a new column "degrees above snowsliding" into the output dataframe. Positive values mean
that snow on panels would either melt or slide off and negative values mean this is unlikely to happen. Modeling is 
based on Marion 2013 model. The value in this column is essentially the same as how many degrees air temperature could
drop before snow sliding would not happen. 

Setting bifaciality on will simulate radiation on both sides of the PV panel, with the backside having efficiency
of 1.0 or whatever the user has given with: `pvfc.set_relative_bifacial_backside_efficiency(value)`

Once radiation absorbed by the panel from the both sides is calculated, the two dataframes are merged so that the
same monofacial temperature and power output estimation models can be used. See [bifacial modeling](bifacial_modeling.md)
for additional information.


# 2. Forecasting functions

The forecasting functions can be split into 3 groups, FMI forecasts, clear sky forecasts and external data processing. 
The PV modeling pipeline(and model functions) are the same with all three,
but the source of the radiation data and the output returned to the user varies.

## 2.1. FMI forecasting functions

These are the FMI open data based forecasting functions. They utilize weather and radiation forecasts retrieved
from FMI open data service.


By default, they are cached. This means that unless user
changes the geolocation, or unless 60 seconds pass, the system will not make another API call. This is possible because
the forecasts only depend on the location and current time. This ensures that a python program using this package
will use as little bandwidth as possible.

Users can for example, call the FMI forecast for one set of panels, adjust panel angles and call the forecast again
without new API calls being made. The API will stop responding to calls if user attempts to make thousands of calls
per day, which is unlikely in any situation, but this caching should make it even less likely.



```python
# Forecasting functions:
pvfc.get_default_fmi_forecast() # <- main, calls helper
pvfc.get_fmi_forecast_for_interval(interval_start, interval_end) # <- wrapper, calls main
pvfc.get_fmi_forecast_at_interpolated_time(time) # <- wrapper, calls main

# Helper:
pvfc.get_fmi_radiation_forecast()
```

### 2.1.1. Radiation forecasting function

This is the helper function. It calls the FMI open data API and requests the available 66-ish hour 
radiation and weather forecast. This function exists so that users can make their own modifications to the forecasts
if needed or use them for purposes other than PV forecasting. 

**Calling the function:**
```python
# Calling the function:
radiation_forecast = pvfc.get_fmi_radiation_forecast()
```

**Usage example:**
```python
# sample usage:
radiation_forecast = pvfc.get_fmi_radiation_forecast()

# modifications to radiation_forecast happen here
radiation_forecast["dni"] = radiation_forecast["dni"]*0.90

# using radiation/weather forecast to generate PV output forecast:
pv_forecast = process_radiation_df(radiation_forecast)
```

More info on the weather forecast API: [https://en.ilmatieteenlaitos.fi/open-data-manual-wfs-examples-and-guidelines](https://en.ilmatieteenlaitos.fi/open-data-manual-wfs-examples-and-guidelines) 

And the python package used for accessing the API:
 [https://github.com/pnuu/fmiopendata](https://github.com/pnuu/fmiopendata)

### 2.1.2. Default FMI forecast

This is the forecasting function regular users would most likely use. This is a prime example of how the
radiation forecasts can be used together with the PV model.

This function takes one optional parameter `interpolate`. By default, it is set to `False`. If set to `"15min"` or
`"1min"`, the radiation forecast will be linearly interpolated to a new time resolution before being passed onto the PV
model. 

**Default FMI forecast function code:**
```python
def get_default_fmi_forecast(interpolate=False) -> pd.DataFrame:
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
```

**Usage example:**

```python
# Normal forecast
normal_forecast = pvfc.get_default_fmi_forecast()

# 15 min time resolution forecast
interpolated_forecast = pvfc.get_default_fmi_forecast(interpolate="15min")
```

### 2.1.3. Interval from FMI forecast
This function returns the output of the default fmi forecast function with interpolate set to `False` where timestamps
are between the two datetime inputs. Can be useful for retrieving daily power for tomorrow and calculating KWh values.

```python
pvfc.get_fmi_forecast_for_interval(interval_start, interval_end)
```


### 2.1.4. FMI forecast at interpolated time
This function can be used to retrieve a single interpolated dataframe row for any given time within the forecast window.
May be useful for requesting power right now or at tomorrow at 19:55:04 if needed. 
As the FMI radiation forecasts have a time resolution of 60 minutes, these arbitrary time forecasts are more of a
tool for convenience rather than something that could be considered accurate.


```python
pvfc.get_fmi_forecast_at_interpolated_time(time) 
```






## 2.2. Clear sky forecasting functions

```python
pvfc.get_default_clearsky_forecast()
pvfc.get_clearsky_estimate_for_interval(interval_start, interval_end, timestep)
```

The default clear sky estimate aligns with the FMI open data forecasting interval. This is a convenient
way to generate a comparable clear sky forecast for plotting and comparison. Optional parameter timestep can be used
to set time in minutes between datapoints.

The clear sky interval function takes two datetime values as start and end points, and a timestep value which tells how
many minutes there should be between rows in the resulting PV output estimate. As the function is not restricted to any
time interval or geographic location, this can be used for calculating power output during different seasons or even
over a whole year. See [example 5](examples.md#example-5-estimating-clearsky-power-for-custom-time-interval) for usage.

**Usage example:**
```python
# 60 min default forecast:
default_clearsky_forecast = pvfc.get_default_clearsky_forecast()

# generating 15 min clearsky and FMI forecasts
clearsky_forecast = pvfc.get_default_clearsky_forecast(timestep=15)
fmi_forecast = pvfc.get_default_fmi_forecast(interpolate="15min")
```

## 2.3. External data processing functions

```python
pvfc.process_radiation_df(radiation_df)
```

This function is actually the only PV model function in the program. When FMI or PVlib based forecasts are requested,
they generate radiation tables and then call this function with their radiation tables. See also [example 3](examples.md#example-3-processing-external-data-with-the-pv-model) for additional info.

**Expected input df structure:**
```commandline
                                 dni        dhi        ghi          T       wind     albedo
time                                                                                       
2024-05-31 23:30:00+00:00       0.00       0.00       0.00      21.54       2.79       0.13
2024-06-01 00:30:00+00:00       0.00       0.00       0.00      21.72       2.96       0.13
2024-06-01 01:30:00+00:00       0.00       8.87       8.87      21.24       3.40       0.10
2024-06-01 02:30:00+00:00      95.50      54.20      65.64      21.22       3.24       0.10
2024-06-01 03:30:00+00:00     458.27      66.92     173.24      21.47       3.64       0.10
```
**Generated output:**
```commandline
                                   T       wind  module_temp     output
time                                                                   
2024-05-31 23:30:00+00:00      21.54       2.79        21.54       0.00
2024-06-01 00:30:00+00:00      21.72       2.96        21.72       0.00
2024-06-01 01:30:00+00:00      21.24       3.40        21.45      85.43
2024-06-01 02:30:00+00:00      21.22       3.24        22.91   1,031.24
2024-06-01 03:30:00+00:00      21.47       3.64        26.74   4,018.16
```

> Note: T, wind and albedo are optional, time has to be in UTC. dni, dhi and ghi are watts.

**Warning: Model errors caused by misunderstandings on timestamps are extremely common.**

**Meteorological time:**
For meteorologists, 12:00 often means average of the time interval [11:00, 12:00] even when the better average time for this
interval would be 11:30. If not corrected, this can easily result in 30 minute errors in sun positions, causing
significant modeling errors. The FMI radiation retrieval function handles this for the user(which explains the xx:30:00
-times in timestamps), but when working with your own data, verify what the timestamps actually mean.

PVlib clearsky forecasts do not have timing related issues as PVlib uses the exact times to calculate the radiation.

# 3. Developmental functions

The following is a listing of functions included in the package but which are not typically useful to users.

* force_clear_fmi_cache()
* set_cache()
* set_extended_output()

Cache functions can be used to clear the local fmi cache or set caching to never occur. This will increase API calls
to FMI servers so these should not be touched if at all possible.

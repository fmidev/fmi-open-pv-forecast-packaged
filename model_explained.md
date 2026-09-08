# PV model explained 
Version 0.1.3

This document explains the steps of the PV model. The document is split into two sections, model overview for those who
would like to understand the basics and a more detailed description for those who want to use the model in research
applications.


<!-- TOC -->
* [PV model explained](#pv-model-explained)
  * [Model overview](#model-overview)
    * [Model as a python functions](#model-as-a-python-functions)
* [Detailed description](#detailed-description)
  * [Step 1. Data input](#step-1-data-input)
    * [Step 1.1. Constant input](#step-11-constant-input)
    * [Step 1.2. Radiation table sourcing](#step-12-radiation-table-sourcing)
  * [Step 2. Irradiance transposition](#step-2-irradiance-transposition)
  * [Step 3. Reflection estimation](#step-3-reflection-estimation)
  * [Step 4. Total absorbed irradiance](#step-4-total-absorbed-irradiance)
  * [Step 5. Panel temperature estimation](#step-5-panel-temperature-estimation)
  * [Step 6. Output estimation](#step-6-output-estimation)
* [2. Extras](#2-extras)
  * [2.1. Adding shadow modeling to the PV model](#21-adding-shadow-modeling-to-the-pv-model)
  * [2.2. Snow related issues](#22-snow-related-issues)
    * [2.2.1. Snow sliding](#221-snow-sliding)
    * [2.2.2. Snow reflections](#222-snow-reflections)
  * [2.3. Missing radiation values](#23-missing-radiation-values)
<!-- TOC -->

## Model overview

Explained in a simplified manner, the model is made up of multiple physical models chained together, forming a
data processing pipeline. The input of this pipeline is a pandas dataframe, these can be thought as data tables with
rows and columns. Each row
represents a moment in time and each column represents a measurable physical value such as temperature or
the amount some radiation type.

The steps in the processing pipeline represent the modeling of a physical phenomena. And they add a new column
or a set of columns to the data table. The last step is an
exception as while it adds the output column, it also removes a large amount of the intermediary columns which
are typically not useful to the user.

**Model diagram**

```mermaid

stateDiagram-v2 
    
    s1 : 1. Data input
    s2 : 2. POA transposition
    s3 : 3. Reflection estimation
    s4 : 4. Panel total radiation estimation
    s5 : 5. Panel temperature modeling
    s6 : 6. System output modeling
    
    s1 --> s2
    s2 --> s3
    s3 --> s4
    s4 --> s5
    s5 --> s6

```

**Model steps**

1. Data input: User feeds the system parameters and decides which radiation data source the model uses.
2. POA transposition: Radiation components are projected to the plane of array(POA).
3. Reflection estimation: Reflective losses for the three radiation types are calculated.
4. Panel total radiation estimation: Sum of absorbed radiation is calculated based on earlier reflective losses.
5. Panel temperature modeling: Panel temperature is estimated.
6. System output modeling: Output of the PV system is modeled using panel temperature and absorbed radiation.

### Model as a python functions

The python representation of the PV model is best thought as a single main PV model function and internal and external
helper functions.

The main PV model function is `process_radiation_df(data)` and it is also the function a user would call if they were
using their own radiation data as seen in [example 3](examples.md#example-3-processing-external-data-with-the-pv-model). The input has to be a python dataframe with solar irradiance data.

Inside the main PV model function are internal helper functions which add columns to the given dataframe.
The first of these internal helpers
projects the solar irradiance to the plane of array(POA), second estimates reflective losses and so on. These
internal helpers use the user given panel angles and other system properties together with the
current dataframe columns, or the default values built into the system if the user doesn't override them.

Outside we have external helper functions. These are available to the user and their task is to simplify using the
PV model. For example, the function `pvfc.get_default_fmi_forecast()` is an external helper which calls other functions
in order to retrieve a radiation dataframe from FMI open data. When this dataframe is ready, it is passed to the
main PV modeling function and the resulting output is given to the user. So in a way, the external helpers create
different
radiation dataframes depending on the external helper used, and then they pass the radiation data to the common main PV
function.

This program structure ensures that no matter how the forecast is requested, the model always remains the same.

**External helper `pvfc.get_default_fmi_forecast()`:**

```python
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
```

**Main PV model function:**

```python

def process_radiation_df(data):
    """
    This function processes a radiation dataframe and estimates the output of a pv system.

    The input df must have columns:
    'time', 'dni', 'dhi', 'ghi'
    additional columns "T", "wind" and "albedo" are also useful

    time column is the mathematical point for which each row in the data is simulated for.
    Since weather at 18:00 represents weather between 17:00 and 18:00, the time column is often index-30min
    """

    if panel_tilt is None or panel_azimuth is None:
        raise ValueError(
            "Tilt and azimuth must be defined before PV output is estimated."
            " Call pv_forecast.set_angles(tilt, azimuth) first with"
            " valid 0-90, 0-360 degree panel angles."
        )


    if "cloud_cover" not in data.index:
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

    # step 6. estimate power output
    data = output_estimator.add_output_to_df(data)

    if not extended_output:
        # if extended output not in use, return only some columns
        return data[["T", "wind", "module_temp", "output"]]

    return data
```

# Detailed description

Diagram colors guide:

- Red : Required constant.
- Orange : Optional constant.
- Yellow : Conditional constant. Only used if dataframe doesn't contain corresponding value.
- Blue : Existing dataframe column. Constants used when value is missing.
- Green : New dataframe column added by this step.

---

## Step 1. Data input

This step consists of feeding the system geolocation, panel angles, system size and other needed system
parameters. And the sourcing of a radiation dataframe. The data input step consists of two parts, constant input
and radiation data sourcing. Constant input is the step where the user feeds in physical parameters of the PV system
and default values which the model will use if better values are not available. Radiation data sourcing is the step
where the user chooses which radiation data source the model uses. The two built-in sources are FMI open data and PVlib,
but the user can also choose to use their own radiation dataframes.

--- 

### Step 1.1. Constant input

This is the first half of step 1. Here required(red), optional(orange) and conditional(yellow) parameters are
fed into the system.

- Required parameters should always be given to the PV model. System size has a default value of 1kW, but without
  geolocation or panel angles, attempting to run the model will result in a crash.

- Optional parameters increase the model performance. Default values for these parameters exist and defaults can often
  be used without major modeling errors.

- Conditional parameters are only used when the dataframe generated here in step 1 does not contain the corresponding
  values. For example: The FMI open data service already returns a dataframe with radiation, wind, air temp and
  albedo information. And so the conditional constants will never be used by the PV model. But as PVlib does not
  attempt to estimate wind, air temp or albedo, the model has to use either the built-in constants or user given
  constants. Default constants are tuned for regular midsummer conditions.

```mermaid
 stateDiagram-v2
    classDef constant stroke: red
    classDef optional_constant stroke: orange
    classDef conditional_constant stroke: yellow
    classDef df stroke: blue
    class geo, angles  constant
    class radw_table,external_radiation_table,pvlib_rad_table,  rad_table df
    class elevation optional_constant
    class air_t, albedo, wind, size conditional_constant
    user: User input
    geo: Geolocation
    angles: Panel Angles
    size: System size
    elevation: Default panel elevation
    wind: Default wind speed
    air_t: Default air temperature
    albedo: Default albedo
    user --> geo: .set_location(57.00,24.06)
    user --> angles: .set_angles(25, 235)
    user --> size: .set_nominal_power_kw(10)
    user --> wind: .set_default_wind_speed(2)
    user --> air_t: .set_default_air_temp(14)
    user --> elevation: .set_module_elevation(2)
    user --> albedo: .set_default_albedo(0.2)









```

--- 

### Step 1.2. Radiation table sourcing

The second half of step 1. consists of choosing the source for the radiation data used by the PV model. Regardless of
which source is used, the result should be a pandas dataframe with datetime index and radiation components
[dni, dhi, ghi] as dataframe columns.

+ The FMI open data returns additional variables [wind, T, albedo] which increase the accuracy of the model.

+ Both FMI open data and PVlib require a valid geolocation.

+ With external data, the required columns are [dni, dhi, ghi] but one, two or all three of the additional variables
  [wind, T, albedo] can also be included.

```mermaid
 stateDiagram-v2
    classDef constant stroke: red
    classDef optional_constant stroke: orange
    classDef conditional_constant stroke: yellow
    classDef df stroke: blue
    class geo, angles, size constant
    class radw_table,external_data,pvlib_rad_table,  rad_table df
    class elevation optional_constant
    class air_t, albedo, wind conditional_constant
    geo: Geolocation
    pvlib: PVlib
    fmi: FMI open data
    user: User input
    radw_table: Radiation and weather table
    rad_table: Radiation table
    pvlib_rad_table: PVlib radiation table
    fmi_path: Option 1. FMI open data
    pvlib_path: Option 2. PVlib
    external_data: External radiation data
    ext_path: Option 3. External data
    geo --> pvlib_path
    geo --> fmi_path

    state fmi_path {
        fmi --> radw_table: .get_default_fmi_forecast()
    }

    state pvlib_path {
        pvlib --> pvlib_rad_table: .get_default_clearsky_forecast()
    }

    state ext_path {
        user --> external_data: .process_radiation_df(radiation_data)
    }

    fmi_path --> rad_table
    pvlib_path --> rad_table
    ext_path --> rad_table


```

> Note: python function calls in the graph above are somewhat symbolical. The shown functions do not only
> give the model a radiation table, but they also start the processing pipeline. Python functions will not be named
> in further steps as they are not accessible to the user.

---

## Step 2. Irradiance transposition

The radiation table from step 1. should contain DNI, DHI and GHI radiation values. These three values
tell us the radiation at a specific location measured by three different methods and irradiance transposition
is the process of calculating how much of the radiation reaches the panel surface.

**Components**

**DNI** is the direct normal irradiance. This can be measured by a sun tracking tube where the radiation per unit of
surface area is measured at the end of the tube. This tube is used to block radiation from the atmosphere from
influencing the results. DNI is the most significant of the three radiation components. DNI is used for calculating
the direct solar radiation on the PV panel surface.

**DHI** is the direct horizontal irradiance. This is measured with a similar instrument as DNI, but the tracker actively
block direct solar irradiance from reaching the instrument. This is done so that only the radiation scattered by the
atmosphere is measured. DHI is used when calculating radiation scattered from the atmosphere.

**GHI** is the global horizontal irradiance. This is the total radiation reaching a horizontal plane at measuring
location.
GHI measurements do not require a tracker. GHI is used when calculating radiation scattered from the ground directly
to the panel surface.

**Physical phenomena**

<img src="readme_images/irradiancetypes.png" height="300"/>


**Transposition model**

As the geometry is different with all the radiation components, three transposition functions are required. The data
flow showing the used parameters and function is approximately as shown in the diagram below.

```mermaid

stateDiagram-v2
    
    classDef constant stroke:red
     classDef optional_constant stroke:orange
     classDef conditional_constant stroke:yellow
     classDef df stroke:blue
     classDef newdf stroke:green
     
     class dni, dhi, ghi, dni_poa, ghi_poa, dhi_poa, albedo, time df
     class dni_poa, ghi_poa, dhi_poa newdf
     
     class panel_angles, geo constant 
     
     
     time : Time
     geo : Geolocation
    
    dni : dni
    dhi : dhi
    ghi : ghi
    
    dni_fun : DNI transposition model
    ghi_fun : GHI transposition model
    perez : DHI transposition model
    
    albedo : Albedo
    sun_pos : Sun tilt and azimuth
    
    dni_poa : dni_poa
    dhi_poa : dhi_poa
    ghi_poa : ghi_poa
    
    panel_angles : Panel angles
    
    
    time --> sun_pos
    geo --> sun_pos
    
    
    dhi --> perez
    panel_angles --> perez
    sun_pos --> perez
    
    dni --> perez
    time --> perez
    perez --> dhi_poa
    
    
    sun_pos --> dni_fun
    panel_angles -->dni_fun
    dni --> dni_fun
    
    dni_fun--> dni_poa
    
    
    panel_angles--> ghi_fun
    ghi --> ghi_fun
    albedo -->ghi_fun
    ghi_fun--> ghi_poa
```

[dni_poa, dhi_poa, ghi_poa] values are not combined at the end into a single POA value as while they do represent
radiation on panel surface, reflective losses are still not accounted for and different
equations are required for each _plane of array_ transposed radiation value.

The transposition models used here are described by Sandia on their page. The DHI model is the most complex and the
DHI Perez-Driesse model built into PVlib itself is used. DNI and GHI transposition models are implemented in python.

[GHI model](https://pvpmc.sandia.gov/modeling-guide/1-weather-design-inputs/plane-of-array-poa-irradiance/calculating-poa-irradiance/poa-ground-reflected/),
[DNI model](https://pvpmc.sandia.gov/modeling-guide/1-weather-design-inputs/plane-of-array-poa-irradiance/calculating-poa-irradiance/poa-beam/),
[DHI model](https://pvpmc.sandia.gov/modeling-guide/1-weather-design-inputs/plane-of-array-poa-irradiance/calculating-poa-irradiance/poa-sky-diffuse/perez-sky-diffuse-model/)
descriptions on Sandia's web page.

---

## Step 3. Reflection estimation

The direction of radiation is different for the 3 radiation components and thus we need 3 reflection estimation
functions. The functions used here are from Martin & Ruiz 2001 paper which is an excellent example of how to write
a test-based research paper.

```mermaid

stateDiagram-v2
    classDef constant stroke:red
    classDef optional_constant stroke:orange
    classDef conditional_constant stroke:yellow
    classDef df stroke:blue
    classDef newdf stroke:green
    
    dni_poa : dni_poa
    dhi_poa : dhi_poa
    ghi_poa : ghi_poa
    
    time : time 
    
    tilt : Panel tilt
    azimuth : Panel azimuth
    geo : Geolocation
    
    aoi : Angle of incidence(AOI)
    
    ghi_r : ghi reflection model
    dhi_r : dhi reflection model
    dni_r : dni reflection model
    
    dni_rc : dni_rc
    dhi_rc : dhi_rc
    ghi_rc : ghi_rc
    
    class dni_poa, dhi_poa, ghi_poa, time df
    class dni_rc, dhi_rc, ghi_rc newdf
    class tilt, azimuth, geo constant
    
    time --> aoi
    tilt --> aoi
    azimuth --> aoi
    geo --> aoi
    
    
    dni_poa --> dni_r
    dni_r --> dni_rc
    aoi --> dni_r
    
 
    
    dhi_poa --> dhi_r
    dhi_r --> dhi_rc
    tilt --> dhi_r
    
    ghi_poa --> ghi_r
    ghi_r --> ghi_rc
    tilt --> ghi_r
```

The diagram above tells us that we need an additional value AOI in order to compute the reflective losses from direct
solar irradiance. AOI is the angle of incidence, and it tells us how far from the solar panel normal vector the ray
angle
of incoming sunlight is. AOI depends on the position of the Sun and it is calculated with functions included in PVlib.

> PVlib returns apparent solar zenith and solar zenith when solar angles are requested. Apparent zenith takes the
> influence of the atmosphere into account and it should be used.

With dhi and ghi the takeaways are that the location of the PV system, panel azimuth, time of day or solar angles do not
matter. This is a result of simplifications in the dhi and ghi models. The only relevant parameters are the
plane of array irradiance and panel tilt angle.

**Sources:**

Martin & Ruiz 2001
"Calculation of the PV modules angular losses under field conditions by means of an analytical model".

---

## Step 4. Total absorbed irradiance

This step merges the 3 reflection corrected plane of array irradiance values into one value poa_rc. This reflection
corrected
POA irradiance value tells us the amount of radiation absorbed by the PV panels.

No complex math here:

`poa_rc = dni_rc+dhi_rc+ghi_rc`

```mermaid
stateDiagram-v2
    classDef constant stroke:red
    classDef optional_constant stroke:orange
    classDef conditional_constant stroke:yellow
    classDef df stroke:blue
    classDef newdf stroke:green
    
    dni_rc : dni_rc
    dhi_rc : dhi_rc
    ghi_rc : ghi_rc
    poa_rc : poa_rc
    
    class dni_rc, dhi_rc, ghi_rc  df
    class poa_rc newdf
    class tilt, azimuth, geo constant
    
    dni_rc --> poa_rc
    dhi_rc --> poa_rc
    ghi_rc --> poa_rc

```

---

## Step 5. Panel temperature estimation

Panel temperature is estimated with King 2004 model.

```mermaid

stateDiagram-v2

    classDef constant stroke:red
    classDef optional_constant stroke:orange
    classDef conditional_constant stroke:yellow
    classDef df stroke:blue
    classDef newdf stroke:green
    

    wind : wind at 10m
    elevation : panel elevation
    t : air temperature
    rad : poa_rc
    panel_t : panel temperature
    
    wind_at_panel : wind at panel model
    
    panel_t_mod : panel temperature model
    
    class wind, t, rad  df
    class panel_t newdf
    class elevation, azimuth, geo constant
    
    
    wind --> wind_at_panel
    elevation --> wind_at_panel
    
    wind_at_panel --> panel_t_mod
    t --> panel_t_mod
    rad --> panel_t_mod
    
    panel_t_mod--> panel_t

```

The method for panel temperature estimation first calculates the wind experienced by the PV panels.
Weather forecasting services often report wind as wind at 10m elevation, and we can estimate wind at
different reasonable elevations based on the 10m wind speed.

The actual panel temperature model sets panel temperature as the same as `air_temperature + A` where A is a
positive value based on absorbed radiation(poa_rc) and wind speed. Higher wind values reduce the value of A
and higher absorbed radiation values increase it.

> If the dataframe doesn't contain T column, the model will use a constant air temperature instead.

> If the dataframe doesn't contain wind column, the model will use a constant wind speed instead.




**Sources:**

D.~King, J.~Kratochvil, and W.~Boyson,
Photovoltaic Array Performance Model Vol. 8,
PhD thesis (Sandia Naitional Laboratories, 2004).

---


### 5.1. Snow sliding modeling

Snow sliding is the phenomena where snow on the panels is heated to a temperature at which small layer of water can 
form between the panel surface and the snow on top of it. When this occurs, gravity can slide some or all the snow from the
panel surface. The model used by this package is the based on the Marion model. _"Measured and modeled photovoltaic 
system energy losses from snow for Colorado and Wisconsin locations"_ Marion et al. 2013. The original Marion model 
returns a boolean value which describes if snow sliding conditions are possible.

---
**Our model:**

```
"degrees above snowsliding" = T_air + POA/80
```
Where:

* T_air is air temperature in Celsius.
* POA is radiation on solar panel surface in W/m².
* "degrees above snowsliding is how many degrees above "snow would slide" our panels are at. 

Example:

T_air = -1C, POA = 160W/m²
```
"degrees above snowsliding" = T_air + POA/80
"degrees above snowsliding" = -1 + 160/80
"degrees above snowsliding" = -1 + 2
"degrees above snowsliding" = 1
```
In this case, air temperature is -1C and snow should not melt or slide. But due to solar radiation, snow on the panel
surface is actively melting. Snow will continue melting unless air temperature drops by 1 degree or radiation decreases
by 80W/m².

Knowing how far we are from snow melting point can be useful if the there's some bias present in local temperatures.
Or if users want to if there's even a slim chance that snow could melt, or be very sure that snow will melt when the 
model suggests so.







## Step 6. Output estimation

Final output of the PV model is estimated by using Huld 2010 model. This same model is sometimes referred
as the Huld 6k model as it has 6 constants, k1, k2 ... k6 which can be used to tune the model.

The constants used are:

```python
# huld 2010 constants
k1 = -0.017162
k2 = -0.040289
k3 = -0.004681
k4 = 0.000148
k5 = 0.000169
k6 = 0.000005
```

```mermaid


stateDiagram-v2
    classDef constant stroke:red
    classDef optional_constant stroke:orange
    classDef conditional_constant stroke:yellow
    classDef df stroke:blue
    classDef newdf stroke:green
    


    rad : poa_rc
    panel_t : panel temperature
    rated_power : nominal power
    
    output_power : output
    
    

    class poa_rc, panel_t, rad  df
    class output_power newdf
    class rated_power constant
    
    output_model : DC output model
    
 
    
    rad --> output_model
    panel_t --> output_model
    rated_power --> output_model
    
    output_model --> output_power
```

The way the Huld model works is that it computes `efficiency` based on panel temperature and absorbed radiation
values. Output is then set to be:

`output = efficiency*rated_power*absorbed_radiation`

The Huld model calculates efficiency with a set of logarithms which were fitted to solar panel output data. This data
included a set of PV panels operating at panel temperatures of 23 to 60C and receiving between 50 to 1000W/m² of
radiation.

We have decided to add a 50% lower limit to the efficiency estimated by the model. This limit was set as the efficiency
of the Huld model starts behaving erratically when radiation nears zero due to the logarithm components. And because
the Huld model was not fitted to data which would have included low radiation values of 0 to 50W/m².

Despite the odd behavior at 0 to 50W and despite being fitted to panel temperatures of 20C or higher, the Huld model
has proven to work well with our own data.

<img src="readme_images/huld_efficiency.png"/>

**Improvements?**

The Huld model could be fitted to our data for more accurate low temperature and radiation modeling, but
this comes with the risk of overfitting.

In a perfect world, we would have a solar panel efficiency model which is based on measurements at a
wide range of temperatures, radiations and panel types.

**Sources:**

Huld 2010 model
T.~Huld, R.~Gottschalg, H.~G. Beyer, and M.~Topič,
Mapping the performance of PV modules, effects of module type and
data averaging, Solar Energy, 84 324--338 (2010).

---

# 2. Extras

This section contain tips and things we have noticed while using the PV model.


## 2.1. Adding shadow modeling to the PV model

If you'd like to add shading modeling to the system (shading = direct radiation is decreased by an obstacle), 
fairly accurate results can be achieved by multiplying DNI radiation component by a shading coefficient. This
coefficient should be Sun angle dependent, and figuring out how to generate a shading map will be left to the user.

IMPORTANT: If you do this, you will run into some odd issues with DHI transpositions, even if transposed DNI would
work perfectly. This happens since the Perez-Driesse DHI transposition uses DHI and DNI as inputs. Internally the 
DHI Perez-Driesse does something like this:

Low DNI, High DHI -> Assume cloudy sky and thus DHI radiation is uniform.

High DNI, High DHI -> Assume clear sky and thus DHI radiation is higher from the direction of the Sun.

In actuality the model is a bit more complex, and it consists of a large-ish number table which is used to estimate 
uniformity, but the point here remains the same. Adjusting DNI too early will change the geometry of the DHI 
transpositions.

We figured this out by accident while using the older Perez(not Perez-Driesse) model. Any abnormal combinations of 
DNI and DHI given to the Perez can result in rather amusing sawtooth patterns due to how the model changes the
multipliers it uses. Perez-Driesse makes the sawtooth pattern disappear, but the sky geometry issue will still exist.

If you are doing shading modeling, reach out to us, and we will deliver you a modified model with physically accurate
DNI shading functionality. Or you can create your own version of the package.



## 2.2. Snow related issues

### 2.2.1. Snow sliding

Snow sliding modeling is new in 0.1.1. This is based on the Marion snow sliding model, improvements and a more
complete snow sliding model implementation is among the next goals for this PV package.

As of now, the model calculates the temperature of the snow on the panels and if this temperature is positive,
snow sliding should occur. 

### 2.2.2. Snow reflections

Snow can be highly reflective and nearly vertical south facing PV panels can generate significantly higher amounts
of power than the PV model suggests. The model does not take this into account, and we are uncertain if this will ever
change
due to the difficulty of the problem.

## 2.3. Missing radiation values

On-site datasets are often missing either DNI or DHI irradiance.
This happens because GHI radiation is easy to measure as it doesn't require a tracker whereas DHI and DNI require
trackers.
If you have 2 of the 3 radiation components, you can use the apparent solar angles and the two known radiation values
to calculate the missing 3rd radiation parameter. Calculated values are not as accurate as directly measured, but
they can still be used.

Required functions are somewhat complex and we will leave searching out for one to you.












import datetime

import pandas as pd

import fmi_pv_forecaster as pvfc
from fmi_pv_forecaster import pv_forecaster

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

#### Part 1
# angles and location
pvfc.set_location(65, 25)
pvfc.set_angles(15, 135)

data = pvfc.get_fmi_radiation_forecast()



#### Part 2, adjusting model constants
huld_params = [-0.02, -0.06, -0.003, 0.001, 0.00005, 0.0000020]

# 3 setters
pvfc.set_panel_reflectivity_model_constant(0.5)
pvfc.set_panel_temperature_model_constants(-2, -0.54)
pvfc.set_output_model_constants(huld_params)

# printing model data
pvfc.print_info()

#### Part 3, resettitng model constants
# 3 resetting values
pvfc.set_panel_temperature_model_constants(None, None)
pvfc.set_panel_reflectivity_model_constant(None)
pvfc.set_output_model_constants(None)

# printing model data
pvfc.print_info()

#print_full(data)

#### Part 4, testing effect on forecasts
date_start = datetime.datetime(2018, 6, 15, 8)
date_end = datetime.datetime(2018, 6, 15, 23)
fc1 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)
pvfc.set_panel_reflectivity_model_constant(0.32)
fc2 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)

pvfc.set_panel_reflectivity_model_constant(None)


delta_df = pd.DataFrame()

delta_df['output_normal'] = fc1["output"]
delta_df['output_higher_reflectivity'] = fc2["output"]
delta_df["difference"] = delta_df['output_higher_reflectivity']- delta_df['output_normal']

max_difference = max(delta_df['difference'])
mean_difference = delta_df['difference'].mean()

print("-------------")
print("Showing the difference between default reflectance constant and 0.32")
print_full(delta_df)
print(max_difference)
print(mean_difference)
print("-------------")

#### Part 5 testing
date_start = datetime.datetime(2018, 6, 15, 8)
date_end = datetime.datetime(2018, 6, 15, 23)
fc1 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)
pvfc.set_panel_temperature_model_constants(-4, -0.1) # a=-3.47, b=-0.0594
fc2 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)

pvfc.set_panel_reflectivity_model_constant(None)


delta_df = pd.DataFrame()

delta_df['output_normal'] = fc1["output"]
delta_df['output_higher_cooling'] = fc2["output"]
delta_df["difference"] = delta_df['output_higher_cooling']- delta_df['output_normal']

mean_difference = delta_df['difference'].mean()
min_difference = min(delta_df['difference'])



print("-------------")
print("Showing the difference between normal cooling values and increased cooling")
print_full(delta_df)
print(min_difference)
print(mean_difference)
print("-------------")
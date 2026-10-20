import datetime

import pandas as pd

import fmi_pv_forecaster as pvfc

###################################

def test_that_temp_model_constant_set_and_reset_dont_crash():
    # setting valid value
    no_crashes = True
    try:
        pvfc.set_panel_temperature_model_constants(-0.2, -0.1)
    except:
        no_crashes = False

    assert no_crashes

    # resetting
    no_crashes = True
    try:
        pvfc.set_panel_temperature_model_constants(None, None)
    except:
        no_crashes = False

    assert no_crashes


def test_that_reflection_model_constant_set_and_reset_dont_crash():
    # testing valid value
    no_crashes = True
    try:
        pvfc.set_panel_reflectivity_model_constant(0.17)
    except:
        no_crashes = False

    assert no_crashes

    # Testing reset
    try:
        pvfc.set_panel_reflectivity_model_constant(None)
    except:
        no_crashes = False

    assert no_crashes

def test_that_huld_model_constant_set_and_reset_dont_crash():
    # testing valid value
    no_crashes = True

    huld_news = [0.3, 0.3, 0.7, 0.2, 0.1, 0.1]

    try:
        pvfc.set_output_model_constants(huld_news, 0.1, 1.0)
    except:
        no_crashes = False

    assert no_crashes

    # testing reset
    try:
        pvfc.set_output_model_constants(None, min_efficiency=None, max_efficiency=None)
    except:
        no_crashes = False

    assert no_crashes

def test_that_higher_reflections_decrease_output():
    date_start = datetime.datetime(2018, 6, 15, 8)
    date_end = datetime.datetime(2018, 6, 15, 23)
    pvfc.set_location(60, 25)
    pvfc.set_angles(80, 180)

    pvfc.set_panel_reflectivity_model_constant(None)
    fc1 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)
    pvfc.set_panel_reflectivity_model_constant(0.31)
    fc2 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)

    pvfc.set_panel_reflectivity_model_constant(None)

    delta_df = pd.DataFrame()

    delta_df['output_normal'] = fc1["output"]
    delta_df['output_higher_reflectivity'] = fc2["output"]
    delta_df["difference"] = delta_df['output_higher_reflectivity'] - delta_df['output_normal']

    max_difference = max(delta_df['difference'])
    mean_difference = delta_df['difference'].mean()

    assert max_difference <= 0.0, (
        "Higher reflectivity increased output for at least one df row. This should never happen"
    )

    assert mean_difference < 0.0, (
        "Higher reflectivity had on average higher output, this should never happen"
    )

def test_that_increased_cooling_increases_output():
    date_start = datetime.datetime(2018, 6, 15, 8)
    date_end = datetime.datetime(2018, 6, 15, 23)
    pvfc.set_location(60, 25)
    pvfc.set_angles(80, 180)

    pvfc.set_panel_temperature_model_constants(None, None) # defaults a=-3.47, b=-0.0594
    fc1 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)
    pvfc.set_panel_temperature_model_constants(-3.5, -0.06) # marginally lower values, should result in power gains
    fc2 = pvfc.get_clearsky_forecast_for_interval(date_start, date_end, timestep=30)

    pvfc.set_panel_temperature_model_constants(None, None)

    delta_df = pd.DataFrame()

    delta_df['output_normal'] = fc1["output"]
    delta_df['output_higher_cooling'] = fc2["output"]
    delta_df["difference"] = delta_df['output_higher_cooling'] - delta_df['output_normal']

    min_difference = min(delta_df['difference'])
    mean_difference = delta_df['difference'].mean()

    assert min_difference >= 0, (
        "Better cooling resulted in at least one row with lower power output. This should never happen"
    )

    assert mean_difference >= 0.0, (
        "Better cooling resulted in lower power output on average. This should never happen"
    )



#########################
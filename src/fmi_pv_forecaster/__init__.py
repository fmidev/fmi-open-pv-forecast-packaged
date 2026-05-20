# System parameters

# debug
from .pv_forecaster import force_clear_fmi_cache, set_bifacial
from .pv_forecaster import get_clearsky_estimate_for_interval
# Forecast functions
from .pv_forecaster import get_default_fmi_forecast
from .pv_forecaster import get_fmi_forecast_at_interpolated_time
from .pv_forecaster import get_fmi_forecast_for_interval
from .pv_forecaster import get_default_clearsky_forecast
from .pv_forecaster import get_fmi_radiation_forecast
from .pv_forecaster import get_clearsky_estimate_for_times
from .pv_forecaster import get_clearsky_radiation_for_times

# external usage
from .pv_forecaster import process_radiation_df
from .pv_forecaster import set_angles
from .pv_forecaster import set_cache
from .pv_forecaster import set_default_air_temp
# clearsky system parameters
from .pv_forecaster import set_default_albedo
from .pv_forecaster import set_default_wind_speed
# toggles
from .pv_forecaster import set_extended_output
from .pv_forecaster import set_location
# optional system parameters
from .pv_forecaster import set_module_elevation
from .pv_forecaster import set_nominal_power_kw

__all__ = [
    # system parameters
    "set_angles",
    "set_location",
    "set_nominal_power_kw",

    # optional system parameters
    "set_module_elevation",

    # clearsky system parameters
    "set_default_albedo",
    "set_default_wind_speed",
    "set_default_air_temp",

    # forecast functions
    "get_default_fmi_forecast",
    "get_clearsky_estimate_for_interval",
    "get_fmi_forecast_for_interval",
    "get_fmi_forecast_at_interpolated_time",
    "get_default_clearsky_forecast",
    "get_fmi_radiation_forecast",
    "get_clearsky_estimate_for_times",
    "get_clearsky_radiation_for_times",

    # toggles
    "set_extended_output",
    "set_cache",
    "set_bifacial",

    # external usage
    "process_radiation_df",

    # debug
    "force_clear_fmi_cache"
]

__version__ = "0.1.0"

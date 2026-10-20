# System parameters

# debug
from .pv_forecaster import force_clear_fmi_cache
from .pv_forecaster import get_clearsky_forecast_for_interval
from .pv_forecaster import print_info
# Forecast functions
from .pv_forecaster import get_default_fmi_forecast
from .pv_forecaster import get_fmi_forecast_at_interpolated_time
from .pv_forecaster import get_fmi_forecast_for_interval
from .pv_forecaster import get_default_clearsky_forecast
from .pv_forecaster import get_fmi_radiation_forecast
# external usage
from .pv_forecaster import process_radiation_df
from .pv_forecaster import set_angles
from .pv_forecaster import set_cache
from .pv_forecaster import set_default_air_temp
from .pv_forecaster import set_relative_bifacial_backside_efficiency
# clearsky system parameters
from .pv_forecaster import set_default_albedo
from .pv_forecaster import set_default_wind_speed
# toggles
from .pv_forecaster import set_extended_output
from .pv_forecaster import set_location
from .pv_forecaster import set_snow_sliding
from .pv_forecaster import set_bifacial
# optional system parameters
from .pv_forecaster import set_module_elevation
from .pv_forecaster import set_nominal_power_kw
from .pv_forecaster import set_panel_reflectivity_model_constant
from .pv_forecaster import set_panel_temperature_model_constants
from .pv_forecaster import set_output_model_constants


__all__ = [
    # system parameters
    "set_angles",
    "set_location",
    "set_nominal_power_kw",

    # optional system parameters
    "set_module_elevation",
    "set_relative_bifacial_backside_efficiency",

    # model value adjustments
    "set_panel_reflectivity_model_constant",
    "set_panel_temperature_model_constants",
    "set_output_model_constants",

    # clearsky system parameters
    "set_default_albedo",
    "set_default_wind_speed",
    "set_default_air_temp",

    # forecast functions
    "get_default_fmi_forecast",
    "get_clearsky_forecast_for_interval",
    "get_fmi_forecast_for_interval",
    "get_fmi_forecast_at_interpolated_time",
    "get_default_clearsky_forecast",
    "get_fmi_radiation_forecast",

    # toggles
    "set_extended_output",
    "set_cache",
    "set_snow_sliding",
    "set_bifacial",

    # external usage
    "process_radiation_df",

    # debug
    "force_clear_fmi_cache",
    "print_info"

]

__version__ = "0.1.4"

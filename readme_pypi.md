# FMI open pv forecast package

Current version: 0.1.3 - License: MIT

The main functionality of this package is the PV forecasting tool which is a combination of the FMI PV model and
weather forecasts from FMI open data. The resulting PV forecasting tool generates hourly weather-aware PV forecasts for
a 66-hour period. These forecasts take panel orientation, panel surface reflections, panel temperature, and other
factors
into account, resulting in generally accurate modeling of PV output when weather forecasts align with actual experienced
weather.

The forecasting package has in-built functionality for using clear sky radiation estimates from PVlib. These clear sky
forecasts can be used for testing purposes, system monitoring or in cases when internet access is not available.

The PV model can also be used with external data sources by feeding it dataframes with the required radiation
components.

Full package documentation, examples and source code available on github at: 
https://github.com/fmidev/fmi-open-pv-forecast-packaged

### Version history:

- 0.1.3 (2026-09-08) New FMI open data retrieval code. Also updates to tests. Now the
project should be fully MIT compliant.
- 0.1.2 (2026-08-18) License switched from GPL 3.0 to MIT. 
- 0.1.1 (2026-06-02) Added bifaciality and Marion -based snow sliding.
- 0.1.0 Initial PV Model with monofacial modeling features.

### Usage example

This minimal example shows how to use the forecasting tool by computing a forecast for a 4kw system.

```python
import fmi_pv_forecaster as pvfc

pvfc.set_angles(25, 180)
pvfc.set_location(60.1576, 24.8762)
pvfc.set_nominal_power_kw(4)

data = pvfc.get_default_fmi_forecast()

print("Forecast:")
print(data)
```

Resulting print:

```commandline
Forecast:
                        T  wind  module_temp     output
Time                                                   
2026-01-20 10:30:00  -0.8  0.79    -0.800000   0.000000
2026-01-20 11:30:00  -0.6  1.33    -0.048916  38.589095
2026-01-20 12:30:00  -0.5  1.78    -0.136189  25.854990
2026-01-20 13:30:00  -0.7  2.30    -0.627352   5.316707
2026-01-20 14:30:00  -1.0  2.37    -0.999996   0.000000
...                   ...   ...          ...        ...
2026-01-23 01:30:00 -15.2  0.73   -15.200000   0.000000
2026-01-23 02:30:00 -15.6  0.73   -15.600000   0.000000
2026-01-23 03:30:00   NaN   NaN          NaN   0.000000
2026-01-23 04:30:00   NaN   NaN          NaN   0.000000
2026-01-23 05:30:00   NaN   NaN          NaN   0.000000
```

### Authors and acknowledgements

Timo Salola.

Additional help from: Viivi Kallio, William Wandji, Anders Lindfors, Juha Karhu.

This package relies on Pandas, Numpy, PVlib and FMI open data API.

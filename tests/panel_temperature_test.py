import random
import numpy as np
import fmi_pv_forecaster.helpers.panel_temperature_estimator


"""
This file contains tests for file panel_temperature_estimator
"""



def test_module_temp():

    for i in range(0, 300):

        radiation = random.randrange(-50, 1000)
        radiation = np.clip(radiation, 0, 1000)
        wind = random.randrange(-3, 10)
        wind = np.clip(wind, 0, 10)
        air_temperature = random.randrange(-30, 35)
        module_elevation = random.randrange(0, 20)


        module_t = fmi_pv_forecaster.helpers.panel_temperature_estimator.temperature_of_module(radiation, wind, module_elevation, air_temperature)

        module_t2 = fmi_pv_forecaster.helpers.panel_temperature_estimator.temperature_of_module(radiation + 50, wind,
                                                                                               module_elevation,
                                                                                               air_temperature)

        module_t3 = fmi_pv_forecaster.helpers.panel_temperature_estimator.temperature_of_module(radiation, wind + 5,
                                                                                                module_elevation,
                                                                                                air_temperature)

        module_t4 = fmi_pv_forecaster.helpers.panel_temperature_estimator.temperature_of_module(radiation, wind,
                                                                                                module_elevation + 5,
                                                                                                air_temperature)

        module_t5 = fmi_pv_forecaster.helpers.panel_temperature_estimator.temperature_of_module(radiation, wind,
                                                                                                module_elevation,
                                                                                                air_temperature + 5)

        assert isinstance(module_t, float) or isinstance(module_t, np.float64), (
            "Module Temperature type was not float like expected. Type was: " + str(type(module_t))
        )
        module_t_r = round(module_t, 2)

        print("=====")
        print("Radiation: ", radiation)
        print("Wind: ", wind)
        print("Air Temperature: ", air_temperature)
        print("Module Elevation: ", module_elevation)
        print("Module Temperature: ", module_t)
        print("---")
        print("More rad panel: " + str(module_t2))
        print("More wind panel: " + str(module_t3))
        print("Higher elevation panel: " + str(module_t4))
        print("higher air temp panel: " + str(module_t5))
        print("=====")


        assert module_t >= air_temperature, (
            "Module Temperature was not greater than or equal to air temperature."
        )

        assert module_t < module_t2, (
            "Simulated temperature was lower when radiation was higher. This should never happen."
        )

        assert module_t >= module_t3, (
            "Simulated temperature was higher when wind was higher. This should never happen as wind cools panels."
        )

        assert module_t >= module_t4, (
            "Module temperature was higher for a panel at higher installation elevation. Should not happen since "
            "panels at higher elevations cool down more due to higher wind."
            ""
        )

        assert module_t < module_t5, (
            "Module temperature was lower when air temperature was higher. Should not happen since temperature is based"
            "on ambient air temp."
        )

    print("Module temperature equation does not fail in obvious ways.")


import numpy as np
import fmi_pv_forecaster.helpers.output_estimator as output_estimator
import random

"""
This file contains tests for file output_estimator

"""


def test_power_output_estimation_function():
    """
    This function tests if the power output estimation function is outputting reasonable values.
    """

    random.seed(1)

    for i in range(0, 100):
        kwh_rating1 = random.randint(1,100)
        kwh_rating2 = random.randint(1, 100)
        panel_temp = random.randint(-40, 100)

        absorbed_radiation = random.random() * 1000
        output_estimator.rated_power = kwh_rating1
        estimated_output1 = output_estimator.__estimate_output(absorbed_radiation, panel_temp)
        output_estimator.rated_power = kwh_rating2
        estimated_output2 = output_estimator.__estimate_output(absorbed_radiation, panel_temp)

        #print("Nominal power 1: " +str(kwh_rating1))
        #print("Nominal power 2: " +str(kwh_rating2))
        #print("absorbed radiation: " + str(absorbed_radiation))
        #print("Power 1: " +str(estimated_output1))
        #print("Power 2: " + str(estimated_output2))
        #print("Upper limit1: " + str(absorbed_radiation*kwh_rating1))
        #print("Upper limit2: " + str(absorbed_radiation * kwh_rating2))
        #print("Power ratio: " + str(rating_ratio))
        #print("panel temp: " + str(panel_temp))

        assert np.issubdtype(type(estimated_output1), np.floating), (
            # np.floating is a group in which all numpy.float -types belong to. Type seems to be float64 but
            # being careful here, perhaps on some systems the package returns a float32 or some other.
            print("Output type was not numpy float, type was instead: " + str(type(estimated_output1)))
        )

        assert estimated_output1 >= 0, (
            "Estimated power output was negative, this should never happen."
        )
        assert estimated_output1 < absorbed_radiation * kwh_rating1 * 1.01, (
            # including a 1% margin due to floating point errors.
            "Estimated power was greater than absorbed radiation, this should never happen.",
            str(estimated_output1) + " < " + str(absorbed_radiation * kwh_rating1)
        )

        # power rating values should be just simple multipliers, this bit tests if both estimated power values are
        # within a 2% range when scaling is reversed
        assert estimated_output1 / kwh_rating1 >= (estimated_output2 / kwh_rating2) * 0.98, (
            "Nominal system power scaling does not appear to be linear."
        )

        assert estimated_output1 / kwh_rating1 <= (estimated_output2 / kwh_rating2) * 1.02, (
            "Nominal system power scaling does not appear to be linear."
        )


    print("Power output function is returning values which seem physically possible and reasonable.")

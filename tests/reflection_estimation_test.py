import datetime
import random
import fmi_pv_forecaster.helpers.reflection_estimator

test_count = 300



def test_dni_reflections():

    for i in range(test_count):


        latitude = random.uniform(-90,90)
        longitude = random.uniform(-90,90)
        tilt = random.uniform(-90,90)
        azimuth = random.uniform(-90,90)
        dni = random.uniform(0,1000)
        time = datetime.datetime.now()


        reflection_loss = fmi_pv_forecaster.helpers.reflection_estimator.__dni_reflected(
                            time, latitude, longitude, tilt, azimuth)

        reflection_loss = reflection_loss.values[0]

        aoi = fmi_pv_forecaster.helpers.astronomical_calculations.get_solar_angle_of_incidence_fast_unlimited(
            time, latitude, longitude, tilt, azimuth).values[0]


        print("=====")
        print("latitude: " + str(latitude))
        print("longitude: " + str(longitude))
        print("tilt: " + str(tilt))
        print("azimuth: " + str(azimuth))
        print("aoi(unlimited): " + str(aoi))
        print("dni: " + str(dni))
        print("reflection_loss: " + str(reflection_loss))
        print("=====")


        assert reflection_loss >= 0 and reflection_loss <= 1, (
            "Reflective loss does not stay in range [0, 1], this time it was " + str(reflection_loss)
        )

        if aoi > 90:
            assert reflection_loss > 0.99, (
                "Reflective losses should be near 100% when aoi is higher than 90 degrees. Now aoi was " + str(aoi)
                + "and reflective losses were " + str(reflection_loss)
            )

    print("Ran " + str(test_count) + " tests on dni reflections. Did not find obvious issues.")



def test_dhi_reflections():

    """
    DHI reflections are super strange.
    Reflectivity should be about 4.1% to 4.8% depending on panel angle with the lowest losses near 60 degrees.
    Same at 0 and 90 due to radiation being different, but geometry being the same.
    """


    for tilt in range(0, 91, 1):

        reflection_loss = fmi_pv_forecaster.helpers.reflection_estimator.__dhi_reflected(tilt)

        """
        print("=====")
        print("tilt: " + str(tilt))
        print("reflection_loss: " + str(reflection_loss))
        print("=====")
        """

        assert reflection_loss >= 0 and reflection_loss <= 1, (
                "Reflective loss does not stay in range [0, 1], this time it was " + str(reflection_loss)
        )

        assert reflection_loss > 0.04, (
            "dhi reflective losses were lower than 4%, this is unexpected."
        )

        assert reflection_loss <= 0.05, (
            "dhi reflective losses were higher than 5%, this is unexpected."
        )


    print("Ran tests on dhi reflections. Did not find obvious issues.")


def test_ghi_reflections():


    for tilt in range(0, 120, 1):

        reflection_loss = fmi_pv_forecaster.helpers.reflection_estimator.__ghi_reflected(tilt)


        print("=====")
        print("tilt: " + str(tilt))
        print("reflection_loss: " + str(reflection_loss))
        print("=====")


        assert reflection_loss >= 0 and reflection_loss <= 1, (
            "Reflective losses not in range [0, 1] like expected. Was " + str(reflection_loss)
        )


    # low tilt, near 100% loss
    rl1 = fmi_pv_forecaster.helpers.reflection_estimator.__dhi_reflected(1)
    # higher tilt, near 5 to 10% loss
    rl2 = fmi_pv_forecaster.helpers.reflection_estimator.__dhi_reflected(60)


    assert rl1 > rl2, (
        "Reflective losses for near horizontal panel were higher than 60deg panel. Should not be possible."
    )

    print("Ran tests on ghi reflections. Did not find obvious issues.")

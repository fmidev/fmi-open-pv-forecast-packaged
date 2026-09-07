import datetime
import fmi_pv_forecaster.helpers.irradiance_transpositions as irradiance_transpositions
import fmi_pv_forecaster.helpers.astronomical_calculations as astronomical_calculations
import random

"""
This file contains tests for irradiance transposition functions. Uses some transposition functions for testing which
the regular forecasts would not use.
"""

test_count = 300


def test_ghi_transposition():

    for i in range(0, test_count):
        ghi = random.random() * 1000
        tilt = random.randint(0, 90)
        albedo = random.random()

        transposed_irradiance = irradiance_transpositions.__project_ghi_to_panel_surface(ghi, tilt, albedo)

        #print(transposed_irradiance)

        assert transposed_irradiance >= 0, (
            "Transposed ghi was negative, this should never happen."
        )

        assert transposed_irradiance <= ghi, (
            "Transposed ghi was greater than ghi, this should never happen."
        )

    print("Tested " + str(test_count) + " random ghi transpositions, no obvious faults found.")


def test_dhi_transposition_tilt0():
    """
    This function tests dhi transpositions, proper testing is unfortunately difficult so this just checks physical
    impossibilities.

    This set of tests focuses on tilt 0 cases as these tend to be easier to check.

    Only the isotropic model is easy to understand, it will always equal to dhi when tilt is 0.
    Both perez and perez_driesse models start to decrease when AOI is 85+
    This might be unwanted since if DHI is 100W/m² and panel tilt is 0, panels should receive 100w of dhi radiation
    no matter where the sun is positioned.

    """

    test_count = 300

    for i in range(0, test_count):

        time = datetime.datetime.now()

        dhi = round(random.random() * 300, 2)
        dni = round(random.random() * 1000, 2)
        latitude = round(random.random() * 90, 2)
        longitude = round(180 - random.random() * 360, 2)

        tilt = 0  # random.randint(0,90)
        azimuth = random.randint(0, 360)

        aoi = round(astronomical_calculations.get_solar_angle_of_incidence_fast_unlimited(time,
                                            latitude, longitude, tilt, azimuth), 2)


        # Irradiance transpositions and rounding
        irradiance_driesse = round(irradiance_transpositions.__project_dhi_to_panel_surface_perez_fast(time, dhi, dni,
                                latitude, longitude, tilt, azimuth), 2)
        irradiance_driesse = irradiance_driesse.values[0]

        irradiance_perez = round(
            irradiance_transpositions.__project_dhi_to_panel_surface_perez_fast(time, dhi, dni,
                                       latitude, longitude, tilt, azimuth, driesse=False), 2)
        irradiance_perez = irradiance_perez.values[0]

        irradiance_isotropic = irradiance_transpositions.__project_dhi_to_panel_surface(dhi, tilt)

        """
        print("=====")
        print("dni: " + str(dni)+"W")
        print("dhi: " + str(dhi)+"W")
        print("tilt: " + str(tilt)+" deg")
        print("azimuth: " + str(azimuth)+" deg")
        print("aoi: " + str(aoi)+" deg")
        print("-- Transposed irradiances --")
        print("Driesse: " + str(irradiance_driesse) +"W")
        print("Perez: " + str(irradiance_perez) + "W")
        print("Isotropic:: " + str(irradiance_isotropic) + "W")
        print("=====")
        """


        # negative tests
        assert irradiance_driesse >= 0, (
            "Driesse transposed dhi was negative, this should never happen." + str(irradiance_driesse)
        )

        assert irradiance_perez >= 0, (
                "Perez transposed dhi was negative, this should never happen." + str(irradiance_perez)
        )

        assert irradiance_isotropic >= 0, (
                "Isotropic transposed dhi was negative, this should never happen." + str(irradiance_isotropic)
        )

        # higher than dhi tests
        assert irradiance_driesse <= dhi, (
            "Driesse transposed dhi was greater than dhi, this should never happen."
        )
        assert irradiance_perez <= dhi, (
            "Perez transposed dhi was greater than dhi, this should never happen."
        )
        assert irradiance_isotropic <= dhi, (
            "Transposed dhi was greater than dhi, this should never happen."
        )



        # isotropic tests
        assert irradiance_isotropic == dhi, (
            "Isotropic projection model should result in dhi projection values equal to dhi when panel tilt is 0."
        )

        assert irradiance_isotropic >= irradiance_perez, (
            "Perez model should not result in values higher than isotropic."
        )
        assert irradiance_isotropic >= irradiance_perez, (
            "Perez-driesse model should not result in values higher than isotropic."
        )

    print("Tested " + str(test_count) + " random dhi transpositions with fixed tilt. No faults found.")


def test_dhi_transposition_random_panel_angles():
    """
    This function tests dhi transpositions, proper testing is unfortunately difficult so this just checks physical
    impossibilities.

    This tests random panel angles. Results are more random and fewer restrictions are in place.
    """

    test_count = 300
    for i in range(0, test_count):
        time = datetime.datetime.now()

        dhi = round(random.random() * 300, 2)
        dni = round(random.random() * 1000, 2)
        latitude = round(random.random() * 90, 2)
        longitude = round(180 - random.random() * 360, 2)

        tilt = random.randint(0, 90)
        azimuth = random.randint(0, 360)

        aoi = round(astronomical_calculations.get_solar_angle_of_incidence_fast_unlimited(time,
                                                        latitude, longitude, tilt, azimuth), 2)

        # Irradiance values as floats
        irradiance_driesse = round(
            irradiance_transpositions.__project_dhi_to_panel_surface_perez_fast(time, dhi, dni,
            latitude, longitude, tilt, azimuth), 2)

        irradiance_driesse = irradiance_driesse.values[0]

        irradiance_perez = round(
            irradiance_transpositions.__project_dhi_to_panel_surface_perez_fast(time, dhi, dni,
            latitude, longitude, tilt, azimuth, driesse=False), 2)
        irradiance_perez = irradiance_perez.values[0]

        irradiance_isotropic = irradiance_transpositions.__project_dhi_to_panel_surface(dhi, tilt)

        # negative tests
        assert irradiance_driesse >= 0, (
                "Driesse transposed dhi was negative, this should never happen." + str(irradiance_driesse)
        )

        assert irradiance_perez >= 0, (
                "Perez transposed dhi was negative, this should never happen." + str(irradiance_perez)
        )

        assert irradiance_isotropic >= 0, (
                "Isotropic transposed dhi was negative, this should never happen." + str(irradiance_isotropic)
        )

        # higher than dhi tests
        assert irradiance_isotropic <= dhi, (
            "Transposed dhi was greater than dhi, this should never happen."
        )

    print("Tested " + str(test_count) + " random dhi transpositions with all random inputs. No faults found.")


def test_dni_transposition():

    test_count = 300

    for i in range(0, test_count):
        time = datetime.datetime.now()
        dni = round(random.random() * 1000, 2)

        latitude = round(random.random() * 90, 2)
        longitude = round(180 - random.random() * 360, 2)
        tilt = random.randint(0, 90)
        azimuth = random.randint(0, 360)


        transposed_dni = round(irradiance_transpositions.__project_dni_to_panel_surface_using_time_fast(dni,
                                time, latitude, longitude, tilt, azimuth), 2).values[0]

        # true aoi
        aoi = round(astronomical_calculations.get_solar_angle_of_incidence_fast_unlimited(time,
                       latitude, longitude, tilt, azimuth), 2).values[0]
        # 90 deg limited aoi
        aoi_limited = round(astronomical_calculations.get_solar_angle_of_incidence_limited(time,
                           latitude, longitude, tilt, azimuth), 2).values[0]

        """
        print("=====")
        print("dni: " + str(dni) + "w")
        print("tilt: " + str(tilt) + "deg")
        print("azimuth: " + str(azimuth) + "deg")
        print("Transposed dni: " + str(transposed_dni) + "w")
        print("AOI: " + str(aoi) + "deg")
        print("AOI limited: " + str(aoi_limited) + "deg")
        print("=====")
        """


        if aoi_limited == 90.0:
            assert transposed_dni == 0, (
                "Transposed DNI should be zero when AOI is 90 or higher. AOI was: " + str(aoi)
                + "deg. Transposed DNI was: " + str(transposed_dni) + "w"
            )

        assert transposed_dni >= 0, (
            "Transposed DNI was " + str(transposed_dni)
            + " W, should never be negative. AOI was: " + str(aoi_limited) + " deg."
        )

        assert transposed_dni <= dni, (
            "Transposed DNI(" + str(transposed_dni) + ") was higher than DNI(" + str(dni) + ")"

        )

    print("Tested " + str(test_count) + " random dni transpositions. No faults found.")

import pandas as pd
from matplotlib import pyplot as plt
import fmi_pv_forecaster as pvfc



"""
This file contain a test for bifacial panel modeling.
The test consists of feeding the system parameters such as geolocation and panel angles AND setting bifacial toggle to
true. This should result in the package generating a multi part figure with both sides and the combined system output
as curves.

For future reference, https://www.pvsyst.com/help-pvsyst7/bifacial_systems.htm
seems like a good source on bifaciality modeling.
"""

latitude = 64
longitude = 25
tilt1 = 45
azimuth1 = 90


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


pvfc.set_location(latitude, longitude)
pvfc.set_angles(tilt1, azimuth1)

pvfc.set_extended_output(True)
pvfc.set_bifacial(True)
pvfc.set_relative_bifacial_backside_efficiency(0.90)

data1 = pvfc.get_default_clearsky_forecast(5)

print("Results from model")
print_full(data1)

#print(data1.columns)


fig, ax = plt.subplots(4,3)

ax1 = ax[0,0]
ax2 = ax[1,0]
ax3 = ax[2,0]
ax4 = ax[3,0]

ax5 = ax[0,1]
ax6 = ax[1,1]
ax7 = ax[2,1]
ax8 = ax[3,1]


ax9 = ax[0,2]
ax10 = ax[1,2]
ax11 = ax[2,2]
ax12 = ax[3,2]


#print(data1)

# col 1
ax4.set_title('Output')
ax4.plot(data1.index, data1["poa_ref_cor_front"], label="Frontside absorbed radiation")
ax4.plot(data1.index, data1["poa_ref_cor_back"], label="Backside absorbed radiation")
ax4.plot(data1.index, data1["output"], label="Total output")
ax4.legend()


# col 2

ax5.set_title('Panel frontside radiation values' + " t: " + str(tilt1) + " a: " + str(azimuth1))
ax5.plot(data1.index, data1["dni"], label="dni")
ax5.plot(data1.index, data1["dni_poa"], label="panel 1 dni_poa")
ax5.plot(data1.index, data1["dni_rc"], label="panel 1 dni_rc")
ax5.legend()


ax6.plot(data1.index, data1["dhi"], label="dhi")
ax6.plot(data1.index, data1["dhi_poa"], label="front dhi_poa")
ax6.plot(data1.index, data1["dhi_rc"], label="front dhi_rc")
ax6.legend()

ax7.plot(data1.index, data1["ghi"], label="ghi")
ax7.plot(data1.index, data1["ghi_poa"], label="front ghi_poa")
ax7.plot(data1.index, data1["ghi_rc"], label="front ghi_rc")
ax7.legend()

ax8.plot(data1.index, data1["poa_ref_cor_front"], label="Frontside absorbed radiation")
ax8.legend()

# col 3

ax9.set_title('Panel backside radiation values, t: ' + str(180 - tilt1) + " a: " + str((azimuth1 + 180) % 360))
ax9.plot(data1.index, data1["dni"], label="dni")
ax9.plot(data1.index, data1["dni_poa_back"], label="back dni_poa")
ax9.plot(data1.index, data1["dni_rc_back"], label="back dni_rc")
ax9.legend()


ax10.plot(data1.index, data1["dhi"], label="dhi")
ax10.plot(data1.index, data1["dhi_poa_back"], label="back dhi_poa")
ax10.plot(data1.index, data1["dhi_rc_back"], label="back dhi_rc")
ax10.legend()

ax11.plot(data1.index, data1["ghi"], label="ghi")
ax11.plot(data1.index, data1["ghi_poa_back"], label="back ghi_poa")
ax11.plot(data1.index, data1["ghi_rc_back"], label="back ghi_rc")
ax11.legend()


ax12.plot(data1.index, data1["poa_ref_cor_back"], label="Backside absorbed radiation")
ax12.legend()


plt.show()

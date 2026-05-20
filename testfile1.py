import datetime

from matplotlib import pyplot as plt

import fmi_pv_forecaster as pvfc


pvfc.set_location(54.103,18.024)

pvfc.set_angles(35, 180)

data = pvfc.get_default_fmi_forecast()
dataB = pvfc.get_default_fmi_forecast(interpolate="15min")

data2 = pvfc.get_default_clearsky_forecast()
data3 = pvfc.get_default_clearsky_forecast(timestep=15)
data4 = pvfc.get_default_clearsky_forecast(timestep=1)


#print(data)
#print(type(data))

#print(data2)
#print(type(data2))


# plotting forecast
fig, ax = plt.subplots(layout='constrained')

plt.plot(data.index, data["output"], label="Forecast", color="#303193")
plt.plot(dataB.index, dataB["output"], label="Forecast 15min interpolated", color="skyblue")
#plt.plot(data2.index, data2["output"], label="Cloud free forecast",  color="#6ec8fa")
#plt.plot(data3.index, data3["output"], label="Cloud free forecast 15min",  color="red")
plt.plot(data4.index, data4["output"], label="Cloud free forecast 1min",  color="black")


# adding axis labels, titles and other text elements
ax.set_xlabel("Time")
ax.set_ylabel("Power(W)")

timenow = datetime.datetime.now()
timenow_string = datetime.datetime.fromtimestamp(timenow.timestamp()).strftime('%Y-%m-%d %H:%M')
plt.title("PV Forecast - " + timenow_string)

plt.legend(loc='upper right')

# showing plot
plt.show()


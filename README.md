Air Quality Monitoring and Control System

Overview

This system continuously monitors indoor and outdoor air quality (PM2.5), temperature, and humidity using sensors and stores the data in a SQLite database. It provides a web-based dashboard for real-time visualization and historical trend analysis. Additionally, it integrates with MQTT to control a fan (filter system) based on AQI thresholds, and leverages a relay controlled by a Raspberry Pi’s GPIO pins to manage the fan’s ON/OFF states.

Components
	1.	Indoor Sensor Script
Collects PM2.5 data from an SPS30 particulate sensor and temperature/humidity from a BME280 sensor. Stores the results in the Indoor table of SAPPHIRES.db.
	2.	Outdoor Sensor MQTT Script
Subscribes to MQTT messages from an external sensor (e.g., another device publishing PM2.5, temperature, humidity, and WiFi strength). On receiving data, it stores these values in the Outdoor table of SAPPHIRES.db.
	3.	Baseline Calculation Script
Periodically calculates a baseline PM2.5 value from historical data. Ensures that outlier baseline values are corrected before insertion. Stores this baseline in a dedicated baseline table.
	4.	Filter State Logic Script
Analyzes recent PM2.5 readings to determine whether the fan (filter) should be turned ON or OFF. A rising edge in PM2.5 beyond a threshold will trigger the relay ON, and a return to baseline will turn it OFF. This state is recorded in a filter_state table.
	5.	MQTT Relay Control Script
Runs on the Raspberry Pi, subscribes to the Filter MQTT topic. When receiving “ON”, it activates the GPIO pin to power the fan. When receiving “OFF”, it deactivates it. Ensures the fan state follows the logic determined by the filter state script.
	6.	Dashboard (Dash/Plotly)
Provides a web interface for:
	•	Viewing real-time indoor and outdoor AQI, temperature, and humidity.
	•	Interactively enabling or disabling the fan, with confirmation and warning steps.
	•	Viewing historical AQI data trends via line charts.
The dashboard reads from the same SAPPHIRES.db database and updates at set intervals.
	7.	Start/Stop SPS30 Scripts
Example scripts to start or stop the SPS30 sensor measurements as needed.

Architecture
+------------+       +------------+           +-------------------+
|  Sensors   | ----> |  Raspberry | -- MQTT -> | MQTT Broker       |
| (SPS30,BME)|       |   Pi       | <--- MQTT -| (e.g. 10.42.1.1) |
+------------+       +------------+           +---------+---------+
                                                        |
                                                        v
                                               +-------------------+
                                               | Dashboard (Dash) |
                                               |  & Scripts       |
                                               | (SAPPHIRES.db)   |
                                               +---------+---------+
                                                         |
                                                         v
                                                +-----------------+
                                                | Relay Control   |
                                                | (GPIO)          |
                                                +-----------------+

Prerequisites
	•	Hardware:
	•	Raspberry Pi (or similar SBC) running these scripts.
	•	SPS30 particulate sensor for indoor PM2.5.
	•	BME280 sensor for indoor temperature/humidity.
	•	A device publishing outdoor AQI data via MQTT.
	•	A relay controlled by the Pi’s GPIO pin to control the fan.
	•	Software & Libraries:
	•	Python 3.7+
 
• Dash and Plotly for the dashboard UI:
  pip install dash plotly dash-bootstrap-components pandas

•	paho-mqtt for MQTT communication:
  pip install paho-mqtt

•	sps30 for reading SPS30 sensor data:
  pip install sps30

•	adafruit-circuitpython-bme280 for BME280 sensor:
  pip install adafruit-circuitpython-bme280

	•	SQLite3 (usually included with Python).

	•	Database:
	•	SAPPHIRES.db SQLite database.
	•	The dashboard and sensor scripts create tables if they do not exist.
Ensure that the database paths in the scripts match your environment.

Running the System
	1.	Set Up the Database:
Ensure that SAPPHIRES.db is in the same directory as your scripts (or update the paths accordingly). The scripts will create necessary tables if they don’t exist.
	2.	Start Sensors:
	•	Run the indoor sensor script periodically (e.g., via cron) to insert indoor PM2.5 and temperature/humidity into Indoor table.
	•	Run the MQTT subscriber script to continuously listen for outdoor AQI data and insert into Outdoor table.
	3.	Run the Dashboard:
Start the Dash server:
python app.py
Access it at http://127.0.0.1:8050.
Navigation:
	•	Main page: current conditions and fan control.
	•	Swipe left or navigate to /historical for historical AQI charts.

	4.	Filter State Logic:
Run the script that checks for rising edges and sets the relay state in the filter_state table. This can be a scheduled job (e.g., via cron every minute).
	5.	Relay Control via MQTT:
Run the relay control script on a Raspberry Pi that’s wired to the relay. It listens to MQTT messages and changes GPIO pin accordingly.
	6.	Baseline Calculation:
Periodically run the baseline calculation script (e.g., via cron every hour) to update the baseline PM2.5 value. The baseline helps determine when the fan should be turned ON or OFF.

Cron Examples

You might use cron on the Raspberry Pi to schedule the scripts. For example:
#@reboot /usr/bin/python3 /home/mainhubs/dashboarddb.py >> /home/mainhubs/dashboard.log 2>&1 &
@reboot /home/mainhubs/start_chromium.sh >> /home/mainhubs/chromium_startup.log 2>&1
#*/5 * * * * python /home/mainhubs/checkzerow.py
#@reboot sleep 10 && python /home/mainhubs/remotefiltercontrol.py 
* * * * * python /home/mainhubs/filterdatatest.py
* * * * * python /home/mainhubs/filtertestalgo.py
0 6 * * * python /home/mainhubs/filtertestbaseline.py
* * * * * python /home/mainhubs/filtertestcontrol.py
@reboot sleep 20 && python /home/mainhubs/startsps30.py
30 8 * * * python /home/mainhubs/stopsps30.py
31 8 * * * python /home/mainhubs/startsps30.py
30 18 * * * python /home/mainhubs/stopsps30.py
31 18 * * * python /home/mainhubs/startsps30.py
* * * * * python /home/mainhubs/readindoor.py
#@reboot python  /home/mainhubs/filterdash.py
#@reboot /home/mainhubs/start_chromium2.sh

Adjust paths and intervals as needed.

Error Handling
	•	If the database is inaccessible, scripts log the error to stdout.
	•	If MQTT messages are malformed, the script prints a warning and skips inserting data.
	•	If sensors fail to read values, the script handles exceptions gracefully and logs errors.

Customization
	•	Database Paths:
Update db_path or DB_PATH variables in scripts to point to the correct SQLite database location.
	•	MQTT Broker & Topics:
Update the broker_address, MQTT_BROKER, and MQTT_TOPIC constants in the MQTT scripts to match your setup.
	•	Thresholds and Windows:
Adjust WINDOW_SIZE, baseline thresholds, and AQI thresholds in the filter logic scripts.
	•	UI/UX in Dashboard:
Edit the layout and styling in the Dash app to customize fonts, colors, and overall UI. Add tooltips or legends for clarity.

Maintenance & Troubleshooting
	•	Logs & Monitoring:
Review the console output regularly. Consider using logging Python module for more robust error tracking.
	•	Database Integrity:
Periodically back up the SQLite database. Consider switching to a more scalable database if the system grows.
	•	Scaling:
If data volume or traffic increases, implement caching mechanisms or optimize queries and sensor read intervals.




    
 

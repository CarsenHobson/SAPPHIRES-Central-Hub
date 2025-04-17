This repository contains all of the code for the central hub for the SAPPHIRES project

There are two separate dashboard codes, one for the automated phase of the project and one for the manual phase. They are named filterdashautomated and filterdashmanual

The code for applying the event detection algorithm is called filteralgo

The code for creating the tables are split into automated and manual since the database structure is different for the phases, as well as easier dileneation of which data belongs to which phase. These are named create_tables_automated and create_tables_manual

The code for starting up and stopping the sps30 are named startsps30 and stopsps30. These need to be implemented properly in the cronjob in order to reset the sps30 every twelve hours. This will be shown in the cronjob provided.

The code to read the sensors in the central hub is called readindoor

The code that receives the data from the outdoor nodes through MQTT is called receivedata. This code looks for the data from the respective individual topics on the MQTT server and then distributes that data to the correct location in the database. This data includes PM2.5, Temperature, Humidity, and Wifi Strength. Pressure collection is currently not implemented.

The code that looks for filter_state in the database and then sends either OFF or ON to the RPi inside the filter is called filtersignal.

The code that is responsible for inserting either OFF or ON into the filter_state table in the database is called insert_filter_state for the automated phase and insert_filter_state_manual for the manual phase. This code looks to see if both the system_control and user_control tables contain an ON, then this code will insert an ON into filter_state. It essentially determines if both the system has detected an event and if the user wants the system to be on. If either are not true it will insert OFF into filter_State.

There are a few other scripts in this repository that are not main functions but are essential. These are start_chromium.sh which is the script that launches the dashboard onto the screen. The remove_cursor code removes the cursor from the screen on the dashbaord for visual appeal.

There are also some code meant for testing the system before deploying it. These are simulatedata which just creates random data for the dashboard as well as creates an event every 30 minutes for testing. the last one is testfiltercontrol.py which just inserts ON into system_input forcing the system to turn on the fan.

The cronjob for the central hub is also contained in this repository under cronjob






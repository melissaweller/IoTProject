# Project description
By utilizing sensors, actuators, motors, Single-board computers, and micro-controllers, students
design and simulate a smart home. They capture environmental information and make a decision
based on received data. They also develop access control and occupancy systems and transfer all
data to the cloud or a local server. Finally, they design and develop a web-based IoT dashboard to
control and monitor the system.

# Phase 1 instructions
In this phase of the final project, each group works on the IoT dashboard structure and data
presentation.

The requirements of this phase are:
- LED
- Resistor
- Wires
- Breadboard
- Raspberry-Pi

This phase has the following steps:
- Data capture
- Data communication
- Data presentation

## Data Capture:
Design a button on your dashboard to work as a switch. You must get data from this switch and then
turn on or off an LED on the breadboard. The switch has two states, ON and OFF.

## Data communication:
The captured data (Switch State) is transferred to an RPi

## Data Presentation:
Students should create an IoT dashboard and present the captured data (A switch and LED Status) on
the dashboard. The user should be able to change the switch status from ON to OFF (vice versa) and the
light icon on the webpage should show the status of the LED.

# Phase 2 instructions
In this phase of the final project, each group works on the IoT dashboard structure and data presentation. 
The requirements of this phase are: 
- DHT 11 Temperature and Humidity sensor
- Resistors
- Wires
- Breadboard
- Raspberry-Pi
- DC motor and driver

This phase has the following steps:
- Data capture
- Data communication
- Data presentation

## Data Capture: 
By a DHT-11 sensor, current temperature and humidity are captured. 

## Data communication: 
The captured data is transferred to an RPi 

## Data Presentation:
Students should create an IoT dashboard and present the captured data (Temperature and Humidity) on the dashboard. For each value, a gauge or another type of gadget should be utilized. 
If the current temperature is greater than 24, send an email to the user with this message  “The current temperature is ***. Would you like to turn on the fan?” If the user replies YES, then turn on the fan. Otherwise, do nothing. The Fan status should be presented on the dashboard. Also, on the breadboard DC motor is used as a fan. Therefore, when the dashboard shows the fan is ON, the DC motor should work. 

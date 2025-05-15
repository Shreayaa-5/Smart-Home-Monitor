Smart Room Automation System – Functional Overview
This smart automation system is designed to intelligently control lighting and ventilation (fans) in a room based on environmental conditions and human presence, with manual override features. The system is managed by a Raspberry Pi Pico (WiFi), which acts as the central controller, interfacing with a suite of sensors to monitor and respond to room conditions.

Key Functionalities:
1.Automated Lighting Control
	Lights automatically turn ON only when:
		Ambient light levels are low (i.e., the room is dark), and
		Presence of a person is detected via motion, proximity, or sound.
	Lights turn OFF when no presence is detected for an extended period.

2.Intelligent Fan Operation
	Fans automatically adjust based on:
		1.Temperature and humidity levels in the room.
	The system uses threshold-based control to regulate fan speed or switch the fan ON/OFF accordingly.

3.Advanced Presence Detection
	Presence is determined using a multi-sensor fusion approach involving:
		Motion detection (MPU6050 – accelerometer/gyroscope),
		Proximity sensing (APDS-9960),
		Sound analysis (Electret microphone – e.g., for claps).
	This ensures accurate detection and minimizes false positives.

4.Gesture-Based Manual Override
	Users can manually override automatic controls using predefined gestures detected by the APDS-9960.
	Useful for situations where the user wants to turn the lights or fan ON/OFF regardless of current environmental or presence conditions.

5.Auto Power Cut for Energy Efficiency
	All connected appliances (lights, fan) are automatically powered off after a configurable delay if no presence is detected continuously.
	Helps in conserving energy and improving safety

Components used :
 • Raspberry Pi Pico (WiFi) – Central Controller
 • Sensors:
 • TSL2561 / Photoresistor → Ambient Light Detection
 • DHT11/DHT22 + BMP280 → Temp & Humidity Monitoring
 • MPU6050 → Motion Detection
 • APDS-9960 → Gesture/Proximity for override or detection
 • Electret Microphone → Clap/Sound-Based Trigger

from machine import I2C, Pin, ADC
import machine
from mpu6050 import MPU6050
from apds9960LITE import APDS9960LITE
from tsl2561 import TSL2561
import bme280_float as bme280
import dht
from time import sleep, sleep_ms, time

# --- I2C Buses ---
i2c1 = I2C(1, scl=Pin(7), sda=Pin(6))     # For BME280, MPU6050, TSL2561
i2c2 = I2C(0, scl=Pin(17), sda=Pin(16))   # For APDS9960

# --- Sensors Initialization ---
bme = bme280.BME280(i2c=i2c1)
dht_sensor = dht.DHT11(Pin(2))
imu = MPU6050(i2c1)
tsl = TSL2561(i2c1)
apds9960 = APDS9960LITE(i2c2)
apds9960.prox.enableSensor()

# --- LEDs ---
led_fan = Pin(18, Pin.OUT)       # Fan LED (temp/humidity + presence)
led_presence = Pin(15, Pin.OUT)  # Presence indicator
led_light = Pin(0, Pin.OUT)      # Light LED (dark + presence)

# --- Microphone ---
mic = ADC(Pin(26))
mic_threshold = 3000

# --- Thresholds ---
TEMP_THRESHOLD = 25
HUMIDITY_THRESHOLD = 80
LUX_THRESHOLD = 300
DELAY_OFF = 5  # seconds

# --- Last active timestamps ---
last_detect_time = time()
last_light_on_time = 0
last_fan_on_time = 0

while True:
    try:
        # --- Read Temperature from BME280 ---
        temp_str, _, _ = bme.values
        temp = float(temp_str[:-1])
        print("🌡️ Temp (BME280):", temp, "°C")

        # --- Read Humidity from DHT11 ---
        dht_sensor.measure()
        humidity = dht_sensor.humidity
        print("💧 Humidity (DHT11):", humidity, "%")

        # --- Presence Detection ---
        person_present = False
        status_log = []

        # Proximity
        sleep_ms(25)
        proximity = apds9960.prox.proximityLevel
        print("📏 Proximity:", proximity)
        if proximity > 1:
            person_present = True
            status_log.append("🟢 Proximity Detected")

        # Motion (MPU6050)
        ax, ay, az = imu.accel.xyz
        gx, gy, gz = imu.gyro.xyz
        if abs(ax) > 1.5 or abs(ay) > 1.5 or abs(az) > 1.5:
            person_present = True
            status_log.append("🏃 Accel Movement")
        if abs(gx) > 20 or abs(gy) > 20 or abs(gz) > 20:
            person_present = True
            status_log.append("🔁 Gyro Gesture")

        # Microphone
        mic_val = mic.read_u16()
        status_log.append(f"🎤 Mic: {mic_val}")
        if mic_val > mic_threshold:
            person_present = True
            status_log.append("🔊 Sound Detected")

        # --- Timers ---
        current_time = time()

        if person_present:
            last_detect_time = current_time
            led_presence.value(1)
            status_log.append("✅ Person Present")

            # --- Room Light Logic ---
            lux = tsl.lux()
            if lux is not None:
                status_log.append(f"🔆 Lux: {lux:.2f}")
                if lux < LUX_THRESHOLD:
                    led_light.value(1)
                    last_light_on_time = current_time
                    status_log.append("💡 Room LED ON (Dark + Present)")
                else:
                    led_light.value(0)
                    status_log.append("🌞 Bright – Room LED OFF")
            else:
                led_light.value(0)
                status_log.append("❗ TSL2561 Error")

            # --- Fan LED Logic ---
            if temp > TEMP_THRESHOLD or humidity > HUMIDITY_THRESHOLD:
                led_fan.value(1)
                last_fan_on_time = current_time
                status_log.append("💨 Fan LED ON (Hot/Humid + Present)")
            else:
                led_fan.value(0)
                status_log.append("💤 Normal Temp/Humidity – Fan OFF")
        else:
            # --- Delay-based behavior for all 3 LEDs ---
            if current_time - last_detect_time < DELAY_OFF:
                led_presence.value(1)
                status_log.append("⌛ Delay Active – Keep Presence LED ON")
            else:
                led_presence.value(0)

            if current_time - last_light_on_time < DELAY_OFF:
                led_light.value(1)
                status_log.append("⌛ Delay Active – Keep Room LED ON")
            else:
                led_light.value(0)
                status_log.append("❌ Room LED OFF (No Presence + Delay Expired)")

            if current_time - last_fan_on_time < DELAY_OFF:
                led_fan.value(1)
                status_log.append("⌛ Delay Active – Keep Fan LED ON")
            else:
                led_fan.value(0)
                status_log.append("❌ Fan LED OFF (No Presence + Delay Expired)")

        # --- Print Status ---
        print("\n--- System Status ---")
        for line in status_log:
            print(line)
        print("----------------------\n")

    except Exception as e:
        print("❗ Error:", e)

    sleep(2)
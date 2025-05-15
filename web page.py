import network
import socket
from machine import Pin, I2C, ADC
import time
import dht
from mpu6050 import MPU6050
from tsl2561 import TSL2561
import bme280_float as bme280
from apds9960LITE import APDS9960LITE

# ================== HARDWARE CONFIGURATION ==================
i2c1 = I2C(1, scl=Pin(7), sda=Pin(6))   # BME280, MPU6050, TSL2561
i2c0 = I2C(0, scl=Pin(17), sda=Pin(16))  # APDS9960

imu = MPU6050(i2c1)
light_sensor = TSL2561(i2c1)
bme = bme280.BME280(i2c=i2c1)
apds = APDS9960LITE(i2c0)
apds.prox.enableSensor()
dht_sensor = dht.DHT11(Pin(2))
mic = ADC(Pin(26))

fan = Pin(18, Pin.OUT)
light = Pin(0, Pin.OUT)
presence_led = Pin(15, Pin.OUT)

# ================== PARAMETERS ==================
TEMP_THRESHOLD = 30
HUMIDITY_THRESHOLD =70
LUX_THRESHOLD = 200
MIC_THRESHOLD = 15000
DELAY_OFF = 3

last_detect_time = time.ticks_ms()
last_light_on = 0
last_fan_on = 0
person_present = False
auto_mode = True


SSID = 'SK'
PASSWORD = '53535353'

def connect_wifi():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(SSID, PASSWORD)
    while not station.isconnected():
        pass
    print('Connection successful')
    print(station.ifconfig())
    return station

def detect_presence():
    global person_present
    person_present = False
    proximity = apds.prox.proximityLevel
    ax, ay, az = imu.gyro.xyz
    mic_val = mic.read_u16()
    if abs(ax) > 20 or abs(ay) > 20 or abs(az) > 20:
        motion = True
    else:
        motion= False
    loud_sound = mic_val > MIC_THRESHOLD
    close_proximity = proximity > 10

    if motion or loud_sound or close_proximity:
        person_present = True

    return {
        'person': person_present,
        'motion': motion,
        'sound': mic_val,
        'proximity': proximity
    }

def manage_automation():
    global last_detect_time, last_light_on, last_fan_on
    current_time = time.ticks_ms()

    if person_present:
        last_detect_time = current_time
        presence_led.on()
        lux = light_sensor.lux() or 0
        if lux < LUX_THRESHOLD:
            light.on()
            last_light_on = current_time
        else:
            light.off()

        temp = float(bme.values[0][:-1])
        humidity = dht_sensor.humidity
        if temp > TEMP_THRESHOLD or humidity > HUMIDITY_THRESHOLD:
            fan.on()
            last_fan_on = current_time
        else:
            fan.off()
    else:
        if time.ticks_diff(current_time, last_detect_time) < DELAY_OFF * 1000:
            presence_led.on()
        else:
            presence_led.off()

        if time.ticks_diff(current_time, last_light_on) < DELAY_OFF * 1000:
            light.on()
        else:
            light.off()

        if time.ticks_diff(current_time, last_fan_on) < DELAY_OFF * 1000:
            fan.on()
        else:
            fan.off()

def get_sensor_html():
    try:
        temp = f"{float(bme.values[0][:-1]):.1f}"
        humidity = dht_sensor.humidity
        lux = light_sensor.lux() or 0
        brightness = "Very Dark" if lux < 10 else "Dim" if lux < 50 else "Normal" if lux < 300 else "Bright" if lux < 1000 else "Sunny"
    except:
        temp = humidity = brightness = lux = "N/A"

    mic_val = mic.read_u16()
    sound_level = "Loud" if mic_val > MIC_THRESHOLD else "Normal"
    prox = apds.prox.proximityLevel
    ax, ay, az = imu.gyro.xyz
    if abs(ax) > 20 or abs(ay) > 20 or abs(az) > 20:
        motion_detected= True
    else:
        motion_detected= False
    auto = auto_mode  # Access global flag

    html=f"""
    <html>
    <head>
        <title>Smart Energy Automation</title>
        <meta http-equiv='refresh' content='2'>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #eef2f3;
                margin: 0;
                padding: 0;
                text-align: center;
            }}

            .box {{
                background: white;
                margin: 50px auto;
                padding: 30px 25px;
                max-width: 400px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }}

            h2 {{
                margin-bottom: 25px;
                color: #333;
            }}

            .info-line {{
                font-size: 16px;
                margin: 10px 0;
            }}

            .status {{
                font-weight: bold;
            }}

            .on {{
                color: green;
                background: #d4edda;
                padding: 5px 10px;
                border-radius: 5px;
                display: inline-block;
                font-weight: 600;
            }}

            .off {{
                color: red;
                background: #f8d7da;
                padding: 5px 10px;
                border-radius: 5px;
                display: inline-block;
                font-weight: 600;
            }}

            .btn {{
                margin: 6px 3px;
                padding: 10px 18px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                transition: background 0.3s ease, transform 0.2s ease;
            }}

            .btn:hover {{
                background: #0056b3;
                transform: translateY(-2px);
            }}

            a {{
                text-decoration: none;
            }}
            
            .box .brightness {{
                display: inline-block;
                padding: 5px 10px;
                background: #e9ecef;
                border-radius: 5px;
                font-weight: 600;
            }}

            @media (max-width: 480px) {{
                .box {{
                    width: 90%;
                    padding: 20px;
                }}

                .btn {{
                    width: 100%;
                    margin: 8px 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class='box'>
            <h2>Smart Energy Automation</h2>
            <div class="info-line">Auto Mode: <span class='{ 'on' if auto else 'off' }'>{'ON' if auto else 'OFF'}</span></div>
            <a href='/?auto=on'><button class='btn'>Enable Auto</button></a>
            <a href='/?auto=off'><button class='btn'>Disable Auto</button></a>

            <div class="info-line">Temperature: {temp} &#8451;</div>
            <div class="info-line">Humidity: {humidity} %</div>
            <div class="info-line">Lux: {lux}</div>
            <div class="info-line">Brightness: <span class="brightness">{brightness}</span></div>
            
            <div class="info-line">Mic Value: {mic_val}</div>
            <div class="info-line">Sound Level: <span class='{ 'on' if mic_val > MIC_THRESHOLD else 'off' }'>{sound_level}</span></div>
            <div class="info-line">Proximity Level: {prox}</div>
            <div class="info-line">Presence: <span class='{ 'on' if person_present else 'off' }'>{'YES' if person_present else 'NO'}</span></div>
            <div class="info-line">Motion Detection: <span class='{ 'on' if motion_detected else 'off' }'>{'YES' if motion_detected else 'NO'}</span></div>
            <div class="info-line">Fan: <span class='{ 'on' if fan.value() else 'off' }'>{'ON' if fan.value() else 'OFF'}</span></div>
            <a href='/?fan=on'><button class='btn'>Turn Fan ON</button></a>
            <a href='/?fan=off'><button class='btn'>Turn Fan OFF</button></a>
            <div class="info-line">Light: <span class='{ 'on' if light.value() else 'off' }'>{'ON' if light.value() else 'OFF'}</span></div>
            <a href='/?light=on'><button class='btn'>Turn Light ON</button></a>
            <a href='/?light=off'><button class='btn'>Turn Light OFF</button></a>
        </div>
    </body>
</html>

    """
    return html

def main():
    global auto_mode
    wlan = connect_wifi()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        request = str(request)

        if '/?fan=on' in request:
            fan.value(1)
        if '/?fan=off' in request:
            fan.value(0)
        if '/?light=on' in request:
            light.value(1)
        if '/?light=off' in request:
            light.value(0)
        if '/?presence=on' in request:
            presence_led.value(1)
        if '/?presence=off' in request:
            presence_led.value(0)
        if '/?auto=on' in request:
            auto_mode = True
        if '/?auto=off' in request:
            auto_mode = False

        detect_presence()

        if auto_mode:
            manage_automation()

        response = get_sensor_html()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()


if __name__ == '__main__':
    main()
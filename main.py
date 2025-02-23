import ujson
import network
import urequests as requests
import time
import dht
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import socket

# Konfigurasi WiFi
WIFI_SSID = "Balai_Diklat_Perpus"
WIFI_PASS = "diklat2024!!"

# Konfigurasi Ubidots
UBIDOTS_TOKEN = "BBUS-7FWNuir6VymmrrgbRLe6E8pYyaYHQZ"
DEVICE_LABEL = "esp32rhakatest"
UBIDOTS_URL = f"http://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}/"

# Inisialisasi I2C untuk OLED
def init_oled():
    try:
        i2c = I2C(0, scl=Pin(23), sda=Pin(22))
        time.sleep(1)  
        devices = i2c.scan()
        if not devices:
            raise Exception("No I2C devices found")
        oled_addr = devices[0]
        oled = SSD1306_I2C(128, 64, i2c, addr=oled_addr)
        print(f"OLED found at address {hex(oled_addr)}")
        return oled
    except Exception as e:
        print("OLED Error:", e)
        return None

oled = init_oled()

# Inisialisasi sensor DHT11 & PIR
sensor = dht.DHT11(Pin(19))
pir_sensor = Pin(5, Pin.IN)  # Sensor PIR di GPIO5
led = Pin(2, Pin.OUT)        # LED di GPIO2
motion_count = 0  # Counter deteksi gerakan
temp_readings = []
hum_readings = []

# Fungsi koneksi ke WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    for _ in range(5):
        if wlan.isconnected():
            print("Connected to WiFi! IP Address:", wlan.ifconfig()[0])
            return True
        time.sleep(1)
    
    print("Failed to connect to WiFi")
    return False

# Fungsi cek koneksi DNS
def check_dns():
    try:
        addr = socket.getaddrinfo("industrial.api.ubidots.com", 80)
        print("DNS Resolution Success:", addr)
        return True
    except Exception as e:
        print("DNS Resolution Failed:", e)
        return False

# Fungsi baca suhu & kelembaban
def read_dht11():
    retries = 5
    for _ in range(retries):
        try:
            time.sleep(2)
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            print(f"Temp: {temp}C, Humidity: {hum}%")
            return temp, hum
        except Exception as e:
            print("DHT11 Error:", e)
            time.sleep(1)
    return None, None

# Fungsi tampilkan data di OLED
def display_oled(temp, hum, motion_count):
    if oled:
        oled.fill(0)
        oled.text("ESP32 Sensor", 20, 0)
        if temp is not None and hum is not None:
            oled.text(f"Temp: {temp}C", 0, 20)
            oled.text(f"Humidity: {hum}%", 0, 40)
        else:
            oled.text("DHT11 Error!", 0, 20)
        oled.text(f"Motion: {motion_count}", 0, 55)
        oled.show()
    else:
        print("OLED not initialized")

# Fungsi kirim data ke Ubidots
def send_data_ubidots(temp, hum, avg_temp, avg_hum, motion_count):
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }
    
    data = {
        "temperature": {"value": temp},
        "humidity": {"value": hum},
        "average_temperature": {"value": avg_temp},
        "average_humidity": {"value": avg_hum},
        "motion_count": {"value": motion_count}
    }

    try:
        print("Sending data to Ubidots:", data)
        response = requests.post(UBIDOTS_URL, json=data, headers=headers)
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", e)

# Kirim data ke MongoDB
URL_SERVER = 'http://172.16.1.226:8000/sensor_data'
def send_data_to_mongo(payload):
    response = urequest.post(URL_SERVER, json = payload, headers = HEADERS)
    print('Mongo response:',response.text)

# Fungsi utama
def main():
    global motion_count, temp_readings, hum_readings
    if not connect_wifi():
        print("WiFi connection failed. Please check credentials.")
        return

    if not check_dns():
        print("DNS resolution failed. Check internet connection.")
        return

    while True:
        temp, hum = read_dht11()
        if temp is not None and hum is not None:
            temp_readings.append(temp)
            hum_readings.append(hum)

        avg_temp = sum(temp_readings) / len(temp_readings) if temp_readings else None
        avg_hum = sum(hum_readings) / len(hum_readings) if hum_readings else None
        
        
        # Cek sensor PIR
        if pir_sensor.value() == 1:
            print("Motion detected! Turning LED ON")
            led.value(1)
            motion_count += 1  # Tambah counter deteksi gerakan
            send_data_ubidots(temp, hum, avg_temp, avg_hum, motion_count)
            temp_readings.clear()
            hum_readings.clear()
            time.sleep(2)  # LED nyala selama 2 detik
            led.value(0)
            print("LED OFF")
        else:
            send_data_ubidots(temp, hum, avg_temp, avg_hum, motion_count)
        
        display_oled(temp, hum, motion_count)

        payload={
            'Temperature':temp,
            'Humidity':hum
        }
        send_data_to_mongo(payload)

        time.sleep(2) 
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

# Fungsi koneksi ke WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    for _ in range(10):  # Tambah waktu koneksi hingga 10 percobaan
        if wlan.isconnected():
            print("Connected to WiFi! IP Address:", wlan.ifconfig()[0])
            return True
        time.sleep(1)
    
    print("Failed to connect to WiFi")
    return False

# Cek DNS
def check_dns():
    try:
        addr = socket.getaddrinfo("industrial.api.ubidots.com", 80)
        print("DNS Resolution Success:", addr)
        return True
    except Exception as e:
        print("DNS Resolution Failed:", e)
        return False

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
led_hijau = Pin(2, Pin.OUT)  # LED hijau (gerakan)
led_merah = Pin(4, Pin.OUT)  # LED merah (suhu > 23°C)

led_hijau.value(1)
led_merah.value(1)  # Awalnya LED merah mati

motion_count = 0
temp_readings = []
hum_readings = []


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
            oled.text("DHT11 OFF", 0, 20)
        oled.text(f"Motion: {motion_count}", 0, 55)
        oled.show()
    else:
        print("OLED not initialized")

# Fungsi kirim data ke Ubidots
def send_data_ubidots(temp, hum, avg_temp, avg_hum, motion_count):
    HEADER = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }
    
    data = {}
    if temp is not None:
        data["temperature"] = {"value": temp}
        data["average_temperature"] = {"value": avg_temp}
    if hum is not None:
        data["humidity"] = {"value": hum}
        data["average_humidity"] = {"value": avg_hum}
    
    data["motion_count"] = {"value": motion_count}

    try:
        print("Sending data to Ubidots:", data)
        response = requests.post(UBIDOTS_URL, json=data, headers=HEADER)
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", e)

# Fungsi utama
def main():
    global motion_count, temp_readings, hum_readings,led
    if not connect_wifi():
        print("WiFi connection failed. Please check credentials.")
        return

    if not check_dns():
        print("DNS resolution failed. Check internet connection.")
        return

    while True:
        temp, hum = read_dht11()

        if temp is not None:
            temp_readings.append(temp)
            if temp > 24:
                led_merah.value(0)  # LED merah menyala jika suhu > 23°C
            else:
                led_merah.value(1)  # LED merah mati jika suhu <= 23°C

        if hum is not None:
            hum_readings.append(hum)

        avg_temp = sum(temp_readings) / len(temp_readings) if temp_readings else None
        avg_hum = sum(hum_readings) / len(hum_readings) if hum_readings else None
        
        # Cek sensor PIR
        if pir_sensor.value() == 1:
            print("Motion detected! Turning LED ON")
            led_hijau.value(0)
            motion_count += 1  # Tambah counter deteksi gerakan
            send_data_ubidots(temp, hum, avg_temp, avg_hum, motion_count)
            temp_readings.clear()
            hum_readings.clear()
            time.sleep(2)  # LED nyala selama 2 detik
            led_hijau.value(1)
            print("LED OFF")
        else:
            send_data_ubidots(temp, hum, avg_temp, avg_hum, motion_count)
        
        send_data_ubidots(temp, hum, avg_temp, avg_hum, motion_count)
        display_oled(temp, hum, motion_count)
        time.sleep(2)


if __name__ == "__main__":
    main()

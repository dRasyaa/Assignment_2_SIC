from machine import Pin, I2C
import network
import dht
import time
import ujson
import urequests as requests
from ssd1306 import SSD1306_I2C

# KONFIGURASI WiFi
WIFI_SSID = "Balai_Diklat"
WIFI_PASS = "diklat2024!!"

# KONFIGURASI UBIDOTS
UBIDOTS_TOKEN = "BBUS-7FWNuir6VymmrrgbRLe6E8pYyaYHQZ"
DEVICE_LABEL = "esp32rhakatest"
UBIDOTS_URL = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}/"

# INISIALISASI OLED
def init_oled():
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(23))
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

# INISIALISASI DHT11
sensor = dht.DHT11(Pin(19))

# INISIALISASI LED
led = Pin(2, Pin.OUT)

# FUNGSI KONEKSI KE WIFI
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    print("Connecting to WiFi...")
    for _ in range(5):  # Coba koneksi selama 10 detik
        if wlan.isconnected():
            print("Connected! IP:", wlan.ifconfig()[0])
            return True
        time.sleep(1)
    
    print("WiFi Connection Failed!")
    return False

# BACA DATA DHT11
def test_dht11():
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

# TAMPILKAN KE OLED
def display_oled(temp, hum):
    if oled:
        oled.fill(0)
        oled.text("ESP32 Sensor", 20, 0)
        if temp is not None and hum is not None:
            oled.text(f"Temp: {temp}C", 0, 20)
            oled.text(f"Humidity: {hum}%", 0, 40)
        else:
            oled.text("DHT11 Error!", 0, 20)
        oled.show()
    else:
        print("OLED not initialized")

# KENDALIKAN LED BERDASARKAN TEMPERATUR
def control_led(temp):
    if temp is not None:
        if temp > 20:
            led.value(1)  
        else:
            led.value(0)  

# KIRIM DATA KE UBIDOTS
def send_to_ubidots(temp, hum):
    if temp is None or hum is None:
        print("Data tidak valid, tidak dikirim ke Ubidots")
        return False

    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }

    payload = ujson.dumps({
        "temperature": {"value": temp},
        "humidity": {"value": hum}
    })

    print("Sending to Ubidots:", payload)

    try:
        response = requests.post(UBIDOTS_URL, headers=headers, data=payload)
        print("Response:", response.text)
        response.close()
        return True
    except Exception as e:
        print("Error sending data to Ubidots:", e)
        return False

# MAIN PROGRAM
def main():
    if not connect_wifi():
        return  # Stop jika WiFi tidak terhubung

    while True:
        temp, hum = test_dht11()
        display_oled(temp, hum)
        control_led(temp)
        send_to_ubidots(temp, hum)
        time.sleep(5)

if __name__ == "__main__":
    main()


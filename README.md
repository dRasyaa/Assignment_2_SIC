# Assignment_2_SIC
# Assignment 2 Samsung Innovation Campus

# ESP32 & DHT11 & OLED
from machine import Pin, I2C
import dht
import time
from ssd1306 import SSD1306_I2C


def init_oled():
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(23))
        time.sleep(1)  # Tunggu sebelum akses I2C
        devices = i2c.scan()
        
        if not devices:
            raise Exception("No I2C devices found")
        
        oled_addr = devices[0]  # Ambil alamat pertama yang ditemukan
        oled = SSD1306_I2C(128, 64, i2c, addr=oled_addr)
        print(f"OLED found at address {hex(oled_addr)}")
        return oled
    except Exception as e:
        print("OLED Error:", e)
        return None

oled = init_oled()


print("Scanning I2C devices...")
i2c_devices = I2C(0, scl=Pin(22), sda=Pin(23)).scan()
print("I2C devices found:", i2c_devices)
if not i2c_devices:
    print("No I2C devices found. Check wiring!")


sensor = dht.DHT11(Pin(19))


led = Pin(2, Pin.OUT)

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

def control_led(temp):
    if temp is not None:
        if temp > 20:
            led.value(1)  
        else:
            led.value(0)  

def main():
    while True:
        temp, hum = test_dht11()
        display_oled(temp, hum)
        control_led(temp)
        time.sleep(5)

if __name__ == "__main__":
    main()







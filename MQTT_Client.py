import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json

# Konfigurasi MongoDB
MONGO_URI = "mongodb+srv://denivo:bismillahbisa@assignmentsic2hsc069.58tod.mongodb.net/?appName=AssignmentSIC2HSC069"
client = MongoClient(MONGO_URI)
db = client["sensor_data"]
collection = db["readings"]

# Konfigurasi MQTT
MQTT_BROKER = "broker.emqx.io"  # Bisa diganti dengan broker lain
MQTT_TOPIC = "esp32/sensor"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        collection.insert_one(data)
        print("Data received and stored:", data)
    except Exception as e:
        print("Error processing message:", e)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, 1883, 60)

mqtt_client.loop_forever()

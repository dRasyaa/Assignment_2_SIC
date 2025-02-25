from flask import Flask, request, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = Flask(__name__)

# # MongoDB
uri = "mongodb+srv://denivo:bismillahbisa@assignment2sic.58tod.mongodb.net/?retryWrites=true&w=majority&appName=Assignment2SIC"

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    # Cek koneksi dengan ping
    client.admin.command('ping')
    print("Ping berhasil! Terkoneksi dengan MongoDB.")
except Exception as e:
    print("Terjadi kesalahan:", e)  
    
# Database & Collection
db = client['AssignmentDataBase']
collection = db['SensorData']


# Flask
@app.route('/sensor_data', methods = ['POST'])
def collect_data():
    data2 = request.json

    collection.insert_one(data2)
    print('Success')
    return jsonify({"status": "success", "message": "Data saved"}),201

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5500)
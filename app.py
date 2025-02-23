from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

uri = ""

client = MongoClient(uri)
db = client["esp32_data"]
collection = db["sensor"]

@app.route('/ESP32', methods = ['POST'])
def collect_data():
    data = request.json

    collection.insert_one(data)
    return jsonify({"status": "success", "message": "Data saved"}),201

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)
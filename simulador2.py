import os
import time
import json
import random
import threading
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensores/termopar")
INTERVAL = float(os.getenv("INTERVAL", "2"))

START_SENSOR_ID = int(os.getenv("START_SENSOR_ID", "1"))
NUM_SENSORS = int(os.getenv("NUM_SENSORS", "1"))

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def sensor_simulator(sensor_id):
    while True:
        temperatura = round(random.uniform(20.0, 30.0), 2)  # Simula temperatura
        timestamp = time.time()

        payload = json.dumps({
            "sensor_id": f"sensor_{sensor_id}",
            "temperatura": temperatura,
            "timestamp": timestamp
        })

        client.publish(MQTT_TOPIC, payload)
        time.sleep(INTERVAL)

threads = []
for sensor_id in range(START_SENSOR_ID, START_SENSOR_ID + NUM_SENSORS):
    t = threading.Thread(target=sensor_simulator, args=(sensor_id,), daemon=True)
    t.start()
    threads.append(t)

client.loop_forever()

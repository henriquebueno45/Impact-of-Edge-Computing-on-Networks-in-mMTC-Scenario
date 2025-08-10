import json
import time
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Configurações InfluxDB 2.x
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "e0-D13f383K7FTPZmlf_K2yue80RQIkL95d7Dq1aiRqNeYGqyOtljUZCECwYf_xC24M6WZ7JXHQHThccuRFYQA=="
INFLUX_ORG = "meuTCC"
INFLUX_BUCKET = "meusdados"

client_influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_influx.write_api(write_options=SYNCHRONOUS)

# MQTT
MQTT_BROKER = "192.168.15.20"
MQTT_PORT = 1883
MQTT_TOPIC = "sensores/termopar"

# Para cálculo de latência e jitter
last_timestamp = None
last_receive_time = None

# Para cálculo de throughput e uso banda (simples, bytes por segundo médio)
bytes_received = 0
window_start_time = time.time()
WINDOW_SIZE = 10  # segundos

# Último throughput calculado (para não mostrar None)
last_throughput = None

def on_connect(client, userdata, flags, rc):
    print("MQTT conectado com código", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global last_timestamp, last_receive_time, bytes_received, window_start_time, last_throughput

    receive_time = time.time()
    payload = msg.payload.decode('utf-8')
    bytes_received += len(msg.payload)

    try:
        data = json.loads(payload)
    except Exception as e:
        print("Erro ao decodificar JSON:", e)
        return

    sensor_timestamp = data.get("timestamp", None)
    if sensor_timestamp is None:
        sensor_timestamp = receive_time  # usa tempo atual se não tiver timestamp

    # Latência (tempo entre envio e recebimento)
    latency = receive_time - sensor_timestamp

    # Jitter (variação da latência)
    jitter = None
    if last_timestamp is not None and last_receive_time is not None:
        last_latency = last_receive_time - last_timestamp
        jitter = abs(latency - last_latency)

    last_timestamp = sensor_timestamp
    last_receive_time = receive_time

    # Cálculo de throughput médio (bytes por segundo na janela)
    elapsed = receive_time - window_start_time
    throughput = None
    if elapsed >= WINDOW_SIZE:
        throughput = bytes_received / elapsed
        bytes_received = 0
        window_start_time = receive_time
        last_throughput = throughput  # atualiza último throughput calculado
    else:
        throughput = last_throughput  # usa último valor conhecido

    points = []

    # Ponto do dado original (temperatura)
    p1 = Point("temperatura")\
        .tag("sensor_id", data.get("sensor_id", "unknown"))\
        .field("valor", float(data.get("temperatura", 0)))\
        .time(int(sensor_timestamp * 1e9), WritePrecision.NS)
    points.append(p1)

    # Ponto latência
    p2 = Point("latencia")\
        .tag("sensor_id", data.get("sensor_id", "unknown"))\
        .field("valor", latency)\
        .time(int(receive_time * 1e9), WritePrecision.NS)
    points.append(p2)

    # Ponto jitter (se calculado)
    if jitter is not None:
        p3 = Point("jitter")\
            .tag("sensor_id", data.get("sensor_id", "unknown"))\
            .field("valor", jitter)\
            .time(int(receive_time * 1e9), WritePrecision.NS)
        points.append(p3)

    # Ponto throughput (se calculado)
    if throughput is not None:
        p4 = Point("throughput")\
            .tag("sensor_id", data.get("sensor_id", "unknown"))\
            .field("bytes_por_segundo", throughput)\
            .time(int(receive_time * 1e9), WritePrecision.NS)
        points.append(p4)

    # Grava no InfluxDB
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

    print(f"Dados gravados: temperatura={data.get('temperatura')} latencia={latency:.3f}s jitter={jitter} throughput={throughput}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_forever()

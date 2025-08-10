import yaml

NUM_CONTAINERS = 10
SENSORS_PER_CONTAINER = 100
RASPBERRY_IP = "192.168.15.20"
INTERVAL = 2

compose_content = {
    "version": "3.8",
    "services": {}
}

for i in range(NUM_CONTAINERS):
    service_name = f"sensor_group_{i+1}"
    start_sensor_id = i * SENSORS_PER_CONTAINER + 1

    compose_content["services"][service_name] = {
        "build": ".",
        "environment": [
            f"START_SENSOR_ID={start_sensor_id}",
            f"NUM_SENSORS={SENSORS_PER_CONTAINER}",
            f"MQTT_BROKER={RASPBERRY_IP}",
            "MQTT_PORT=1883",
            "MQTT_TOPIC=sensores/termopar",
            f"INTERVAL={INTERVAL}"
        ],
        "network_mode": "host"
    }

with open("docker-compose.yml", "w") as f:
    yaml.dump(compose_content, f, sort_keys=False)

print(f"Arquivo docker-compose.yml gerado com {NUM_CONTAINERS} containers, cada um simulando {SENSORS_PER_CONTAINER} sensores.")

import time
from Freenove_DHT import DHT

DHT_PIN = 17
dht_sensor = DHT(DHT_PIN)

while True:
    result = dht_sensor.readDHT11()
    if result == 0:
        temperature = dht_sensor.getTemperature()
        humidity = dht_sensor.getHumidity()
        print(f"Temperature: {temperature}, Humidity: {humidity}")
    else:
        print("Failed to read from sensor.")
    time.sleep(2)

import board
import adafruit_bme280.basic as adafruit_bme280
import time
import csv
import os
from datetime import datetime

i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

LOG_FILE = "weather_data.csv"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "temperature_c", "humidity", "pressure_hpa"])

print("Weather station logging started...")
print("Press Ctrl+C to stop")

while True:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temperature = round(bme280.temperature, 1)
    humidity = round(bme280.relative_humidity, 1)
    pressure = round(bme280.pressure, 1)
    print(f"{timestamp} | Temp: {temperature}C | Humidity: {humidity}% | Pressure: {pressure}hPa")
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, temperature, humidity, pressure])
    time.sleep(10)

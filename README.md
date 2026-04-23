# Pi Weather Station

An indoor environmental monitoring system built on Raspberry Pi hardware, combining real-time sensor data acquisition, calculated atmospheric metrics, and a web-based dashboard with live world weather integration.

---

## Overview

This project implements a full-stack IoT environmental monitoring system using a Raspberry Pi 3 Model B and a BME280 sensor. The system continuously logs temperature, humidity, and barometric pressure data, calculates derived atmospheric metrics, and serves a live web dashboard accessible from any device on the local network.

The dashboard includes historical data visualization, statistical summaries, a 7-day weather forecast, and real-time world weather lookup powered by the Open-Meteo API.

---

## Features

- Live temperature, humidity, and barometric pressure readings
- Calculated metrics: heat index, dew point, humidex, vapor pressure, absolute humidity, air density, and estimated altitude
- Indoor comfort indicators: comfort level, mold risk, and air quality assessment
- Historical data logging to CSV with min, max, and average statistics
- Interactive time-series charts for all three primary measurements
- 7-day weather forecast for New York (default location)
- Real-time world weather for 10 fixed cities
- Search functionality for any city worldwide via Open-Meteo geocoding API
- Side-by-side comparison of local sensor data against world cities
- CSV data export via browser
- Mobile-responsive dashboard
- Auto-refresh every 10 seconds

---

## Hardware Requirements

| Component | Specification |
|---|---|
| Single-board computer | Raspberry Pi 3 Model B |
| Environmental sensor | Bosch BME280 (breakout board) |
| Jumper wires | Male-to-female, 4 required |
| MicroSD card | 32GB minimum (SanDisk Ultra recommended) |
| Power supply | 5V / 2.5A via Micro USB |

---

## Wiring

The BME280 communicates over I2C. Connect as follows:

| BME280 Pin | Raspberry Pi Pin | GPIO |
|---|---|---|
| VIN | Pin 1 | 3.3V Power |
| GND | Pin 6 | Ground |
| SDI (SDA) | Pin 3 | GPIO 2 |
| SCK (SCL) | Pin 5 | GPIO 3 |

Note: Use 3.3V only. Do not connect VIN to the 5V pin (Pin 2) as this may damage the sensor.

---

## Software Requirements

### Operating System

- Raspberry Pi OS (32-bit, Debian 13 Trixie)
- Kernel 6.12

### Python Libraries

| Library | Purpose |
|---|---|
| adafruit-circuitpython-bme280 | BME280 sensor driver |
| flask | Web server and dashboard |
| requests | Open-Meteo API integration |

### Installation

Enable I2C on the Raspberry Pi:

```bash
sudo raspi-config
```

Navigate to Interface Options > I2C > Enable, then reboot.

Install required Python libraries:

```bash
sudo pip3 install adafruit-circuitpython-bme280 --break-system-packages
pip3 install requests --break-system-packages
```

---

## Project Structure
pi-weather-station/

│
├── weather_station.py    # Sensor data acquisition and CSV logging
├── dashboard.py          # Flask web server and dashboard
├── weather_data.csv      # Logged sensor data (auto-generated)
└── README.md

---

## Usage

### Starting the Data Logger

Open a terminal and run:

```bash
python3 weather_station.py
```

The logger reads the BME280 sensor every 10 seconds and appends each reading to weather_data.csv. Output is printed to the terminal in real time.

### Starting the Dashboard

Open a second terminal and run:

```bash
python3 dashboard.py
```

The dashboard will be available at:
http://<raspberry-pi-ip-address>:8080
To find your Pi's IP address:

```bash
hostname -I
```

Both scripts must be running simultaneously for the dashboard to display live data.

### Accessing via SSH

To run the system headlessly from a remote machine:

```bash
ssh <username>@<raspberry-pi-ip-address>
```

Run each script in a separate SSH session.

---

## Dashboard Sections

### My Station Tab

- Live readings: temperature (Celsius and Fahrenheit), humidity, pressure, and heat index
- Comfort, mold risk, and air quality status indicators
- Time-series charts for temperature, humidity, and pressure
- Calculated atmospheric metrics
- Min, max, and average statistics for the current dataset
- Full history table (most recent 50 readings)

### World Weather Tab

- 7-day forecast for New York with daily high, low, precipitation probability, and wind speed
- City search: enter any city name to retrieve current conditions via Open-Meteo API
- Fixed city cards for 10 major world cities with current conditions
- Comparison table: local sensor data versus world cities

---

## Data Logging

Sensor data is written to weather_data.csv in the following format:

| Column | Description |
|---|---|
| timestamp | Date and time of reading (YYYY-MM-DD HH:MM:SS) |
| temperature_c | Temperature in degrees Celsius |
| humidity | Relative humidity percentage |
| pressure_hpa | Barometric pressure in hectopascals |

Data can be exported directly from the dashboard using the Export CSV button.

---

## Calculated Metrics

| Metric | Method |
|---|---|
| Temperature (F) | Standard Celsius to Fahrenheit conversion |
| Heat Index | NWS heat index equation |
| Dew Point | Magnus formula approximation |
| Humidex | Canadian Meteorological Service formula |
| Vapor Pressure | August-Roche-Magnus approximation |
| Absolute Humidity | Ideal gas law derivation |
| Air Density | Pressure and temperature correction |
| Estimated Altitude | Barometric formula (ISA standard atmosphere) |

---

## API Reference

This project uses the Open-Meteo API for weather forecast and world city data. No API key is required.

- Forecast endpoint: https://api.open-meteo.com/v1/forecast
- Geocoding endpoint: https://geocoding-api.open-meteo.com/v1/search

---

## Planned Improvements

- Migrate data storage from CSV to SQLite for improved performance and query capability
- Implement date range filtering on historical charts
- Configure read-only overlay filesystem on the SD card to improve longevity
- Deploy public URL access via Cloudflare Tunnel
- Add configurable alert thresholds for temperature and humidity
- Expand sensor array to support outdoor monitoring

---

## Author

Jonathan — Electrical Engineer  
GitHub: github.com/jmedju

---

## License

MIT License

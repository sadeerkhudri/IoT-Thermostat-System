# IoT Thermostat System (Raspberry Pi + Real-Time Web Dashboard)

A physical thermostat that you can control from a browser. The Raspberry Pi runs a Flask-SocketIO server that:
- authenticates users via RFID (PN532) or password,
- streams live temperature/humidity from a DHT11,
- accepts a desired temperature setpoint from the dashboard,
- drives heating/cooling outputs (heater + fan) using a ±2 °C deadband,
- displays status on an I2C LCD + NeoPixel 8×8 matrix (fire/snow),
- plays a buzzer on invalid actions,
- shows outside weather on the dashboard using the OpenWeather API.

---

## Features
- RFID + password login with invalid login feedback (buzzer + LCD + UI border highlight)
- Live DHT11 temperature/humidity updates every ~2 seconds
- Enter a desired temperature (0–40 °C validation)
- Closed-loop control with a ±2 °C deadband:
  - Heat when setpoint >= current temp + 2
  - Cool when setpoint <= current temp - 2
  - Turn outputs off when within range
- NeoPixel 8×8 status icons:
  - Fire when heating
  - Snowflake when cooling
- “Turn Off / New Desired Temperature” button resets the system back to login
- Outside weather (temp/feels-like/climate) shown at the bottom via OpenWeather

---

## Tech Stack
Backend (Raspberry Pi):
- Python, Flask, Flask-SocketIO, APScheduler
- Requests (OpenWeather API)
- Hardware libs: gpiozero, RPLCD, adafruit_dht, PN532_I2C, neopixel

Frontend:
- HTML/CSS/JavaScript
- Socket.IO client

---

## Hardware Used
- Raspberry Pi
- DHT11 temperature/humidity sensor
- PN532 RFID reader (I2C)
- I2C LCD 1602 (PCF8574 @ 0x27)
- NeoPixel 8×8 matrix (WS2812, 64 pixels)
- Tonal buzzer
- Fan output (GPIO-controlled)
- Heater output (GPIO-controlled; e.g., relay/driver to a heat source)

GPIO configuration in the current code:
- NeoPixel data: D18
- DHT11: D21
- Buzzer: GPIO 23
- Fan: GPIO 26
- Heater: GPIO 12
- PN532 + LCD: I2C (SCL/SDA), LCD address 0x27

---

## How It Works (high level)
1) Login screen:
   - LCD shows “Log In”
   - Web page prompts for password or RFID scan
   - Pi reads RFID via PN532 and emits `uid` to the browser

2) On successful login:
   - Browser emits `startTemp`
   - Pi begins streaming DHT11 readings (`dht11`) every ~2 seconds
   - LCD shows current temp/humidity and prompts for “Desired Temp.?”

3) Setpoint:
   - User enters desired temp (0–40 °C)
   - Browser emits `desiredTemp`
   - Pi starts control loop (`checkTemp`) every ~2 seconds:
     - if setpoint >= temp + 2 → heater ON + fire icon
     - if setpoint <= temp - 2 → fan ON + snow icon
     - else → heater OFF + fan OFF + LEDs OFF (“Temp Reached”)

4) Reset:
   - User clicks “Turn Off/New Desired Temperature”
   - Browser reloads and emits `reset`
   - Pi stops control loop and returns to RFID login scanning

---

## WebSocket Events
Pi → Browser
- `uid`: RFID UID detected
- `dht11`: { temp, humidity }
- `checkTemp`: tells UI to update Heating/Cooling/Off label based on current temp vs setpoint
- `tempOut`: { tempOut, feelsLike, climate } from OpenWeather API

Browser → Pi
- `startTemp`: begin streaming temperature/humidity
- `desiredTemp`: send setpoint to Pi
- `invalid`: tell Pi what error occurred (1 = invalid login, 2 = invalid setpoint)
- `reset`: stop control loop and return to login scanning

---

## Setup (Raspberry Pi)

### 1) Enable I2C
- `sudo raspi-config` → Interface Options → I2C → Enable
- Reboot

### 2) Create a venv (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

### 3) Install dependencies
Minimum:
pip install flask flask-socketio flask-apscheduler requests

Common hardware libraries (install what your Pi setup requires):
pip install gpiozero RPLCD
pip install adafruit-circuitpython-dht adafruit-circuitpython-pn532
pip install rpi_ws281x adafruit-circuitpython-neopixel

### 4) Place files into Flask folders
- Move index.html → templates/index.html
- Move style.css + buzzer.mp3 + JS file → static/
- Ensure the script path matches (static/app.js vs static/script.js)

### 5) Run
python3 app.py

Then open:
http://<raspberry-pi-ip>:5000/

---

## Troubleshooting
- If the page loads but JS doesn’t run: check `static/app.js` filename matches the HTML.
- If LCD doesn’t display: verify I2C address (0x27 is common but not universal).
- If PN532 isn’t detected: confirm I2C wiring and that I2C is enabled.
- If NeoPixels don’t light: verify GPIO pin (D18) and power requirements.

---

## Future Improvements
- Replace hard-coded user IDs/passwords with a config file or hashed credentials
- Add HIL/MIL-style test stubs for the control loop
- Package as a mobile-friendly UI or dedicated app
- Add additional sensors for redundancy (e.g., BMP280) and average readings
- Containerize the backend with Docker for repeatable deployment

---

## License
This project is licensed under the MIT License — see the LICENSE file.

#import all libraries
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_apscheduler import APScheduler
from time import sleep
from RPLCD.i2c import CharLCD
from gpiozero import TonalBuzzer, LED
import neopixel
import board
import busio
import adafruit_dht
from adafruit_pn532.i2c import PN532_I2C
import requests


scheduler = APScheduler()
pixel_pin = board.D18 # initialize LED matrix pin
fan = LED(26)
heater = LED(12)
i2c = busio.I2C(board.SCL, board.SDA) # I2C connection
lcd = CharLCD('PCF8574', 0x27)
t = TonalBuzzer(23) # initialize buzzer pin
dhtDevice = adafruit_dht.DHT11(board.D21) #initialize DHT11 pin
pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

num_pixels = 64 # initialize # of LED pixels
ORDER = neopixel.GRB # The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER) # set brightness and format of pizels

snowPixelW = [7, 9, 12, 21, 27, 29, 31, 32, 34, 36, 42, 51, 54, 56] # White Snow Pixel arrangement
snowPixelB = [0, 3, 14, 18, 19, 25, 28, 35, 38, 44, 45, 49, 60, 63] # Blue Snow Pixel arrangement
firePixelR = [2, 3, 7, 11, 12, 20, 21, 22, 29, 30, 31, 36, 37, 43, 44, 47, 49, 50, 54, 55, 57] # Red Fire Pixel arrangement
firePixelO = [0, 1, 8, 9, 10, 14, 17, 18, 19, 26, 27, 28, 34, 35, 41, 42, 46, 51, 56, 62] # Orange Fire Pixel arrangement
firePixelY = [16, 24, 25, 32, 33, 40, 48] # Yellow Fire Pixel arrangement

def weather():
   response = requests.get ('https://api.openweathermap.org/data/2.5/weather?lat=43&lon=-79&appid=<put_your_API_key_here>')
   if response.status_code == 200:
       weather = response.json()
       temperatureOut = round((weather['main']['temp']) - 273.15, 0)
       feelsLike = round((weather['main']['feels_like']) - 273.15, 0)
       climate = weather['weather'][0]['description'].capitalize()
       socketio.emit('tempOut', {'tempOut': temperatureOut, 'feelsLike': feelsLike, 'climate': climate})


def temp():
   # globalize the temp and humidity variable so it can be used anywhere in the program
   global temperature_c
   global humidity
   temperature_c = dhtDevice.temperature # read the temperature from the sensor and store it as a variable
   temperature_f = temperature_c * (9 / 5) + 32 # convert from celsius to farenheit
   humidity = dhtDevice.humidity # read the humidity from the sensor and store it as a variable
   print("Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(temperature_f, temperature_c, humidity))
   socketio.emit('dht11', {'temp': temperature_c, 'humidity': humidity}) # emit the temperature and humidity value to the javascript (web server)


def secure():
   global uid # globalize the card number variable so it can be used anywhere in the program
   uid = pn532.read_passive_target(timeout=0.5) # check if a card is available to read
   print(".", end="")
   fan.off()
   heater.off()
   pixels.fill((0,0,0))
   pixels.show() #turn off LED Matrix
   sleep(0.5)
   lcd.clear()
   lcd.write_string("     Log In     ") # print to LCD
   if uid is None: # try again if no card is available.
       print("Waiting...")
   else:
       uid = uid[0]
       print(uid)
       socketio.emit('uid', {'uid': uid}) # emit the card number to the javascript (web server)


def readTemp():
   temp()
   lcd.clear()
   lcd.write_string(f"    {temperature_c}C | {humidity}%        Desired Temp.? ") # print to LCD


def checkTemp():
   temp()
   socketio.emit('checkTemp')
   lcd.clear()
   lcd.write_string(f"    {temperature_c}C | {humidity}%       Desired Temp: {tempDesired}C") # print to LCD
   if tempDesired >= (temperature_c + 2):
       heater.on()
       for i in range(len(firePixelR)):
           pixels[firePixelR[i]] = (255, 0, 0)
       for i in range(len(firePixelO)):
           pixels[firePixelO[i]] = (255, 40, 0)
       for i in range(len(firePixelY)):
           pixels[firePixelY[i]] = (255, 80, 0)
   elif tempDesired <= (temperature_c - 2):
       fan.on()
       for i in range(len(snowPixelW)):
           pixels[snowPixelW[i]] = (255, 255, 255)
       for i in range(len(snowPixelB)):
           pixels[snowPixelB[i]] = (0, 0, 255)
   else:
       fan.off()
       heater.off()
       pixels.fill((0,0,0))
       lcd.clear()
       lcd.write_string(f"    {temperature_c}C | {humidity}%         Temp Reached  ") # print to LCD
   pixels.show() #display the snowflake or fire
   sleep(0.5)


@app.route("/")
def index():
   return render_template('index.html')


@socketio.on('startTemp')
def startTemp():
   scheduler.add_job(func=readTemp, trigger='interval', id='readTemp', seconds=2)
   scheduler.remove_job('secure')
   scheduler.start()     


@socketio.on('invalid')
def invalid(invalid):
   if invalid.get('invalid', 0) == 1:
       lcd.clear()
       lcd.write_string("     Log In          Invalid Log In ")
   elif invalid.get('invalid', 0) == 2:
       lcd.clear()
       lcd.write_string(" Invalid Input.      Desired Temp.? ")
   t.play("D4") # play the buzzer for 1 second
   sleep(1)
   t.stop()       
       

@socketio.on('desiredTemp')
def desiredTemp(desiredTemp):
   global tempDesired
   tempDesired = desiredTemp.get('desiredTemp', 0)
   scheduler.add_job(func=checkTemp, trigger='interval', id='checkTemp', seconds=2)
   scheduler.remove_job('readTemp') 
   scheduler.start()  
  

@socketio.on('reset')
def reset():
   scheduler.add_job(func=secure, trigger='interval', id='secure', seconds=2)
   scheduler.remove_job('checkTemp')
   scheduler.start()


if __name__ == '__main__':
   scheduler.add_job(func=secure, trigger='interval', id='secure', seconds=2)
   scheduler.add_job(func=weather, trigger='interval', id='weather', seconds=2)
   scheduler.start()
   socketio.run(app, host='0.0.0.0')
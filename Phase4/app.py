from flask import Flask, jsonify, render_template
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import os
import threading
import Adafruit_DHT  # Assumes you are using the DHT library for temperature/humidity

app = Flask(__name__)

# Load environment variables for security (recommended way for credentials)
SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'iotproject87@gmail.com')
SMTP_PASSWORD = 'eeka ftkg smpe qknf'  # Ensure this is loaded securely
SMTP_SSL_HOST = 'smtp.gmail.com'
SMTP_SSL_PORT = 465
FROM_ADDR = SMTP_USERNAME
TO_ADDRS = 'testingsample2003@gmail.com'
email_sent = False

# GPIO setup
GPIO.setmode(GPIO.BCM)
LED_PIN = 17  # Example LED pin for controlling based on light intensity
FAN_PIN = 18  # Example fan pin for DHT11 temperature control
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(FAN_PIN, GPIO.OUT)

# DHT11 sensor setup
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4  # Replace with the correct pin for your setup

# MQTT Settings
BROKER = "10.0.0.89"
TOPIC = "home/light/intensity"

# Variables to track state
last_email_sent_time = None
EMAIL_DELAY = timedelta(seconds=10)
light_intensity = 0
led_status = False
temperature = None
humidity = None

# MQTT Callback for messages
def on_message(client, userdata, msg):
    global last_email_sent_time, light_intensity, led_status, email_sent
    try:
        # Decode light intensity from message payload
        light_intensity = int(msg.payload.decode())

        print(f"Received light intensity: {light_intensity}")

        # Control LED and send email if needed based on light intensity
        if light_intensity < 400 and not email_sent:
            GPIO.output(LED_PIN, GPIO.HIGH)
            send_email("Light ON notification")
            email_sent = True
            last_email_sent_time = datetime.now()
        elif light_intensity >= 400:
            GPIO.output(LED_PIN, GPIO.LOW)
            email_sent = False
    except ValueError as e:
        print(f"Error processing message: {e}")

# Function to read DHT11 data
def read_dht_sensor():
    global temperature, humidity
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if temperature is not None and humidity is not None:
            # Control the fan based on temperature threshold (example threshold: 30°C)
            if temperature > 30:
                GPIO.output(FAN_PIN, GPIO.HIGH)
            else:
                GPIO.output(FAN_PIN, GPIO.LOW)
        threading.Event().wait(2)  # Poll every 2 seconds

# Email function
def send_email(subject):
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    message = MIMEText(f"{subject} at {time_str}.")
    message['subject'] = subject
    message['from'] = FROM_ADDR
    message['to'] = TO_ADDRS

    try:
        with smtplib.SMTP_SSL(SMTP_SSL_HOST, SMTP_SSL_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_ADDR, TO_ADDRS, message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        'led_status': led_status,
        'light_intensity': light_intensity,
        'temperature': temperature,
        'humidity': humidity,
        'email_sent_time': last_email_sent_time.strftime("%H:%M:%S") if last_email_sent_time else None
    })

# MQTT setup
client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.subscribe(TOPIC)
client.loop_start()

# Start DHT sensor thread
threading.Thread(target=read_dht_sensor, daemon=True).start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

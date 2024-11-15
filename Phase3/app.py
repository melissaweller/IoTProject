import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, jsonify, render_template
import RPi.GPIO as GPIO
import os

app = Flask(__name__)

# Load environment variables for security (recommended way for credentials)
SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'iotproject87@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Ensure this is loaded securely
SMTP_SSL_HOST = 'smtp.gmail.com'
SMTP_SSL_PORT = 465
FROM_ADDR = SMTP_USERNAME
TO_ADDRS = 'testingsample2003@gmail.com'

# GPIO setup (assuming a default pin setup; modify as needed)
LED_PIN = 25  # Example GPIO pin for LED
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# MQTT Settings
BROKER = "localhost"  # Ensure Mosquitto broker is correctly configured
TOPIC = "home/light/intensity"

# Callback for when a message is received
def on_message(client, userdata, msg):
    try:
        light_value = int(msg.payload.decode())
        print(f"Received Light Intensity Value: {light_value}")  # Log the received value

        if light_value < 100:
            print("Light value is very low.")
            # Additional actions for very low light intensity (e.g., warning)
        elif light_value < 400:
            # Turn on LED
            GPIO.output(LED_PIN, GPIO.HIGH)
            print("Turning on the LED (light value below 400)")
            
            # Send email notification
            send_email()
        else:
            # Turn off LED
            GPIO.output(LED_PIN, GPIO.LOW)
            print("Turning off the LED (light value 400 or above)")

    except ValueError as e:
        print(f"Error processing message: {e}")

# Send email
def send_email():
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    message = MIMEText(f"The Light is ON at {time_str}.")
    message['Subject'] = "Light Status Notification"
    message['From'] = FROM_ADDR
    message['To'] = TO_ADDRS
    
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

# MQTT setup
client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.subscribe(TOPIC)
client.loop_start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

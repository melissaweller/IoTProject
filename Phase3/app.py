from flask import Flask, jsonify, render_template
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import os

app = Flask(__name__)

# Load environment variables for security (recommended way for credentials)
SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'iotproject87@gmail.com')
SMTP_PASSWORD = 'eeka ftkg smpe qknf'  # Ensure this is loaded securely
SMTP_SSL_HOST = 'smtp.gmail.com'
SMTP_SSL_PORT = 465
FROM_ADDR = SMTP_USERNAME
TO_ADDRS = 'testingsample2003@gmail.com'

# GPIO setup
LED_PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# MQTT Settings
BROKER = "localhost"
TOPIC = "home/light/intensity"

# Variables to track state
last_email_sent_time = None
EMAIL_DELAY = timedelta(seconds=10)
light_intensity = 0
led_status = False

# Callback for MQTT messages
def on_message(client, userdata, msg):
    global last_email_sent_time, light_intensity, led_status
    try:
        light_intensity = int(msg.payload.decode())
        print(f"Received Light Intensity Value: {light_intensity}")

        if light_intensity < 400:
            GPIO.output(LED_PIN, GPIO.HIGH)
            led_status = True
            now = datetime.now()
            if not last_email_sent_time or now - last_email_sent_time > EMAIL_DELAY:
                send_email()
                last_email_sent_time = now
        else:
            GPIO.output(LED_PIN, GPIO.LOW)
            led_status = False
    except ValueError as e:
        print(f"Error processing message: {e}")

# Email function
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

@app.route('/status')
def status():
    return jsonify({
        'led_status': led_status,
        'light_intensity': light_intensity,
        'email_sent_time': last_email_sent_time.strftime("%H:%M:%S") if last_email_sent_time else None
    })

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

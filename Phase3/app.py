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
email_sent = False

# MQTT Settings
BROKER = "10.0.0.89"
TOPIC = "home/light/intensity"

# Variables to track state
last_email_sent_time = None
EMAIL_DELAY = timedelta(seconds=10)
light_intensity = 0
led_status = False

# Callback for MQTT messages
def on_message(client, userdata, msg):
    global last_email_sent_time, light_intensity, led_status, email_sent
    try:
        # Decode light intensity from message payload
        light_intensity = int(msg.payload.decode())

        print(f"Received light intensity: {light_intensity}")

        # If light intensity is below 400 and email has not been sent
        if light_intensity < 400 and not email_sent:
            # Set LED status to True (light is on)
            led_status = True
            send_email()  # Send the email
            email_sent = True  # Set flag to prevent further emails
            last_email_sent_time = datetime.now()  # Record the time the email was sent
            print("Email sent.")
        elif light_intensity >= 400:
            # Reset the email_sent flag if light intensity goes above threshold

            led_status = False  # Turn LED off if light is above 400
            email_sent = False  # Reset email_sent flag to allow sending the next email when intensity falls below 400
    except ValueError as e:
        print(f"Error processing message: {e}")



# Email function
def send_email():
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    message = MIMEText(f"The Light is ON at {time_str}.")
    message['subject'] = "Light Status Notification"
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

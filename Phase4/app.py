from flask import Flask, jsonify, render_template
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import os
import threading
from Freenove_DHT import DHT
import mysql.connector
from mysql.connector import Error
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
DHT_PIN = 17
dht_sensor = DHT(DHT_PIN)

# MQTT Settings
BROKER = "192.168.0.138"
TOPIC = "home/light/intensity"
TOPIC2 = "home/rfid/tag"

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
    rfid_id = msg.payload.decode()
    print(f"RFID ID Received: {rfid_id}")

    # Query the database for RFID information
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE rfid_id = %s"
        cursor.execute(query, (rfid_id,))
        user = cursor.fetchone()

        if user:
            print(f"User Found: {user}")
            # Optional: Use MQTT to publish the user data back to another topic
            client.publish("home/rfid/userinfo", str(user))
        else:
            print("RFID not found in database.")

    except Error as e:
        print(f"Database error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    try:
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

def read_dht_sensor():
    global temperature, humidity
    try:
        result = dht_sensor.readDHT11()
        if result == 0:
            humidity = dht_sensor.getHumidity()
            temperature = dht_sensor.getTemperature()
            print(f"Temperature: {temperature}, Humidity: {humidity}")
            if temperature is not None and humidity is not None:
                if temperature > 20 and not email_sent:
                    send_email(temperature)
                    email_sent = True
                return jsonify({'temperature': temperature, 'humidity': humidity})
            else:
                return jsonify({'error': 'Failed to read from sensor'}), 500
        else:
            print("DHT read failed.")
            return jsonify({'error': 'Failed to read from sensor'}), 500
    except Exception as e:
        print(f"Exception in /data route: {e}")
        return jsonify({'error': str(e)}), 500

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
client.subscribe(TOPIC2)
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

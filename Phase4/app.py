import json
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import mysql.connector
from flask import Flask, jsonify, render_template
import paho.mqtt.client as mqtt
import requests
import smtplib
from email.mime.text import MIMEText
import email
import imaplib
import time
from Freenove_DHT import DHT

app = Flask(__name__)

# GPIO Setup
GPIO.setmode(GPIO.BCM)

# DHT11 Setup
DHT_PIN = 17
dht_sensor = DHT(DHT_PIN)

# Motor setup
Motor1 = 22  # Enable Pin
Motor2 = 27  # Input Pin
Motor3 = 23  # Input Pin
GPIO.setup(Motor1, GPIO.OUT)
GPIO.setup(Motor2, GPIO.OUT)
GPIO.setup(Motor3, GPIO.OUT)
GPIO.output(Motor1, GPIO.LOW)

# MQTT Settings
BROKER = "10.0.0.89"  # Your MQTT Broker IP
TOPIC_RFID = "home/rfid/tag"
TOPIC_LIGHT = "home/light/intensity"
TOPIC_LIGHT_CONTROL = "home/light/control"  # Topic to control the light (send command to ESP32)

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="IoT",  # DB username
        password="password",  # DB password
        database="IoT_Project"  # The name of your database
    )

# Email setup
smtp_ssl_host = 'smtp.gmail.com'
smtp_ssl_port = 465
username = 'iotproject87@gmail.com'
password = 'eeka ftkg smpe qknf'
from_addr = 'iotproject87@gmail.com'
to_addrs = 'testingsample2003@gmail.com'
email_sent = False

# Tracking Variables
email_sent = False
last_email_sent_time = None
light_intensity = 0
temperature = None
humidity = None

# Initialize MQTT Client
mqtt_client = mqtt.Client()

def on_message(client, userdata, msg):
    global light_intensity, email_sent, last_email_sent_time, temperature, humidity

    try:
        print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

        if msg.topic == TOPIC_RFID:
            rfid_code = msg.payload.decode()
            response = requests.get(f"http://10.0.0.89:5001/get_user_favorites/{rfid_code}")

            if response.status_code == 200:
                user_data = response.json()

                # Fetch user preferences with defaults
                user_light_intensity = user_data.get('light_intensity', 300)
                user_temperature = user_data.get('temperature', 25.0)
                user_humidity = user_data.get('humidity', 45.0)

                # Debugging: print out the user data
                print(f"User data fetched: light_intensity = {user_light_intensity}, temperature = {user_temperature}, humidity = {user_humidity}")

                # If light intensity is lower than the user's preference, send control command to ESP32
                if light_intensity < user_light_intensity:
                    print(f"Light intensity {light_intensity} is less than user's preferred {user_light_intensity}. Sending control signal to ESP32.")
                    mqtt_client.publish(TOPIC_LIGHT_CONTROL, "ON")  # Turn on light via ESP32

                # Control the Fan based on temperature
                if temperature is not None and temperature > user_temperature:
                    GPIO.output(Motor1, GPIO.HIGH)  # Turn on fan
                    GPIO.output(Motor2, GPIO.HIGH)
                    GPIO.output(Motor3, GPIO.LOW)
                    print("Fan turned on due to high temperature.")
                    if not email_sent:  # Send email only once
                        send_email(temperature)
                        email_sent = True
                else:
                    GPIO.output(Motor1, GPIO.LOW)  # Turn off fan if temp is lower
                    GPIO.output(Motor2, GPIO.LOW)
                    GPIO.output(Motor3, GPIO.LOW)
                    print("Fan turned off due to normal temperature.")

                # Control air conditioning (or other devices) based on humidity
                if humidity is not None and humidity > user_humidity:
                    print("Humidity is high, you might want to consider activating air conditioning.")
                    # GPIO code for AC control can go here if needed.

        elif msg.topic == TOPIC_LIGHT:
            light_intensity = int(msg.payload.decode())  # Update light intensity from MQTT message
            print(f"Light Intensity: {light_intensity}")

    except Exception as e:
        print(f"Error processing message: {e}")

def send_email(temperature):
    message = MIMEText(f"The current temperature is {temperature}°C. Would you like to turn on the fan?")
    message['subject'] = 'Temperature Alert'
    message['from'] = from_addr
    message['to'] = to_addrs  

    try:
        server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
        server.login(username, password)
        server.sendmail(from_addr, to_addrs, message.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

def check_email_response():
    global email_sent
    while True:
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(username, password)
            mail.select('inbox')
            status, data = mail.search(None, 'UNSEEN')  
            mail_ids = []

            for block in data:
                mail_ids += block.split()

            if mail_ids:
                for i in mail_ids:
                    status, data = mail.fetch(i, '(RFC822)')
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            message = email.message_from_bytes(response_part[1])
                            mail_from = message['from']
                            mail_subject = message['subject']
                            mail_content = ""
                            
                            if message.is_multipart():
                                for part in message.walk():
                                    if part.get_content_type() == 'text/plain':
                                        mail_content = part.get_payload(decode=True).decode()
                            else:
                                mail_content = message.get_payload(decode=True).decode()

                            print(f'From: {mail_from}')
                            print(f'Subject: {mail_subject}')
                            print(f'Content: {mail_content}')

                            if 'Re: Temperature Alert' in mail_subject and mail_from == 'Melissa Weller <' + to_addrs + '>':
                                if 'yes' in mail_content.lower():
                                    GPIO.output(Motor1, GPIO.HIGH)  # Start the motor
                                    GPIO.output(Motor2, GPIO.HIGH)
                                    GPIO.output(Motor3, GPIO.LOW)
                                    print("Fan turned ON based on email response.")
                                elif 'no' in mail_content.lower():
                                    GPIO.output(Motor1, GPIO.LOW)  # Stop the motor
                                    print("Fan is OFF based on email response.")
                                    email_sent = False 

            mail.logout()
        except Exception as e:
            print(f"Error checking email: {e}")

        time.sleep(30)

@app.route('/get_user_favorites/<rfid_tag>', methods=['GET'])
def get_user_favorites(rfid_tag):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # SQL query to fetch user data based on the RFID tag
    cursor.execute("SELECT * FROM users WHERE rfid_tag = %s", (rfid_tag,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        # User found, return user data
        return jsonify({
            "name": user["name"],
            "temperature": user["temperature"] or 25.0,  # default temperature if None
            "humidity": user["humidity"] or 45.0,        # default humidity if None
            "light_intensity": user["light_intensity"] or 300,  # default light intensity
            "temperature_favorite": user["temperature"] or 25.0,
            "light_intensity_favorite": user["light_intensity"] or 300
        })
    else:
        # User not found
        return jsonify({"error": "User not found"}), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        'light_intensity': light_intensity,
        'temperature': temperature,
        'humidity': humidity,
        'email_sent_time': last_email_sent_time.strftime("%H:%M:%S") if last_email_sent_time else None
    })

@app.route('/data')
def data():
    global email_sent, temperature, humidity
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

if __name__ == '__main__':
    # MQTT Client Setup
    mqtt_client.on_message = on_message
    mqtt_client.connect(BROKER, 1883, 60)
    mqtt_client.subscribe(TOPIC_RFID)
    mqtt_client.subscribe(TOPIC_LIGHT)
    mqtt_client.loop_start()

    # Start Email Checking in Background Thread
    import threading
    threading.Thread(target=check_email_response, daemon=True).start()

    # Run Flask App
    app.run(debug=True, host='0.0.0.0', port=5001)

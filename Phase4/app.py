import json
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import mysql.connector
from flask import Flask, request, jsonify, render_template
import paho.mqtt.client as mqtt
import requests
import smtplib
from email.mime.text import MIMEText
import email
import imaplib
import time
import threading
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
BROKER = "192.168.2.81"  # Your MQTT Broker IP
TOPIC_RFID = "home/rfid/tag"
TOPIC_LIGHT = "home/light/intensity"
TOPIC_LIGHT_CONTROL = "home/light/control"  # Topic to control the light (send command to ESP32)

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="username",  # DB username
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
fan_status = False
last_email_sent_time = None
light_intensity = 0
temperature = None
humidity = None

# Initialize MQTT Client
mqtt_client = mqtt.Client()

def on_message(client, userdata, msg):
    global light_intensity, email_sent, last_email_sent_time, temperature, humidity

    try:
        if msg.topic == TOPIC_RFID:
            rfid_code = msg.payload.decode()
            response = requests.get(f"http://192.168.2.81:5001/get_user_favorites/{rfid_code}")

            if response.status_code == 200:
                user_data = response.json()

                # Fetch user preferences with defaults, convert them to appropriate types
                user_light_intensity = int(user_data.get('light_intensity', 300))  # Ensure it's an integer
                user_temperature = float(user_data.get('temperature', 25.0))  # Ensure it's a float
                user_humidity = float(user_data.get('humidity', 45.0))  # Ensure it's a float

                # Debugging: print out the user data
                #print(f"User data fetched: light_intensity = {user_light_intensity}, temperature = {user_temperature}, humidity = {user_humidity}")

                # If light intensity is lower than the user's preference, send control command to ESP32
                if light_intensity < user_light_intensity:
                    #print(f"Light intensity {light_intensity} is less than user's preferred {user_light_intensity}. Sending control signal to ESP32.")
                    mqtt_client.publish(TOPIC_LIGHT_CONTROL, "ON")  # Turn on light via ESP32

                # Control the Fan based on temperature
                if temperature is not None and temperature > user_temperature:
                    GPIO.output(Motor1, GPIO.HIGH)  # Turn on fan
                    GPIO.output(Motor2, GPIO.HIGH)
                    GPIO.output(Motor3, GPIO.LOW)
                    #print("Fan turned on due to high temperature.")
                    if not email_sent:  # Send email only once
                        send_email(temperature)
                        email_sent = True
                else:
                    GPIO.output(Motor1, GPIO.LOW)  # Turn off fan if temp is lower
                    GPIO.output(Motor2, GPIO.LOW)
                    GPIO.output(Motor3, GPIO.LOW)
                    #print("Fan turned off due to normal temperature.")

                # Control air conditioning (or other devices) based on humidity
                if humidity is not None and humidity > user_humidity:
                    print("Humidity is high, you might want to consider activating air conditioning.")
                    # GPIO code for AC control can go here if needed.

        elif msg.topic == TOPIC_LIGHT:
            light_intensity = int(msg.payload.decode())  # Update light intensity from MQTT message
            #print(f"Light Intensity: {light_intensity}")

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
        last_email_sent_time = datetime.now()
        print(f"Email sent at {last_email_sent_time}")
    except Exception as e:
        print(f"Error sending email: {e}")

def check_email_response():
    global email_sent
    while True:
        try:
            # Connect to the email server
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(username, password)
            mail.select('inbox')  # Access the inbox

            # Search for unseen (new) emails
            status, data = mail.search(None, 'UNSEEN')
            mail_ids = data[0].split()

            if mail_ids:
                for mail_id in mail_ids:
                    status, email_data = mail.fetch(mail_id, '(RFC822)')
                    for response_part in email_data:
                        if isinstance(response_part, tuple):
                            # Parse the email
                            message = email.message_from_bytes(response_part[1])
                            subject = message['subject']
                            sender = message['from']
                            email_body = ""

                            if message.is_multipart():
                                for part in message.walk():
                                    if part.get_content_type() == 'text/plain':
                                        email_body = part.get_payload(decode=True).decode()
                            else:
                                email_body = message.get_payload(decode=True).decode()

                            print(f"From: {sender}")
                            print(f"Subject: {subject}")
                            print(f"Body: {email_body}")

                            # Check for the specific reply
                            if 'Temperature Alert' in subject and 'yes' in email_body.lower():
                                # Turn on the motor
                                GPIO.output(Motor1, GPIO.HIGH)
                                GPIO.output(Motor2, GPIO.HIGH)
                                GPIO.output(Motor3, GPIO.LOW)
                                print("Motor turned ON based on email response.")
                                email_sent = False  # Reset the email_sent flag

                            elif 'Temperature Alert' in subject and 'no' in email_body.lower():
                                # Ensure the motor stays off
                                GPIO.output(Motor1, GPIO.LOW)
                                GPIO.output(Motor2, GPIO.LOW)
                                GPIO.output(Motor3, GPIO.LOW)
                                print("Motor remains OFF based on email response.")
                                email_sent = False  # Reset the email_sent flag

            mail.logout()
        except Exception as e:
            print(f"Error checking email: {e}")

        # Poll every 30 seconds
        time.sleep(30)


def get_user_by_rfid(rfid_tag):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE rfid_tag = %s", (rfid_tag,))
    user = cursor.fetchone()
    conn.close()
    return user

def read_temperature():
    global temperature, humidity, email_sent, last_email_sent_time
    while True:
        result = dht_sensor.readDHT11()
        if result == 0:
            temperature = dht_sensor.getTemperature()
            humidity = dht_sensor.getHumidity()
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
            
            # Check if temperature exceeds 20°C and send email if not already sent
            if temperature > 20:
                if not email_sent or (last_email_sent_time and (datetime.now() - last_email_sent_time > timedelta(minutes=30))):
                    send_email(temperature)
                    email_sent = True
                    last_email_sent_time = datetime.now()
                    print("Temperature alert email sent!")
            else:
                email_sent = False  # Reset the email_sent flag if temperature drops below the threshold
        else:
            print("Failed to read from DHT11 sensor.")
        time.sleep(2)


@app.route('/get_user_favorites/<rfid_tag>', methods=['GET'])
def get_user_favorites(rfid_tag):
    user = get_user_by_rfid(rfid_tag)  # Fetch the user data from the DB based on RFID tag

    if user:
        print("user found")
        return jsonify({
            'name': user['name'],
            'temperature': user['temperature'],
            'humidity': user['humidity'],
            'light_intensity': user['light_intensity'],
        })
    else:
        print("user not found 404")
        return jsonify({'error': 'User not found'}), 404
        

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def status():
    # Get RFID tag from the query parameters
    rfid_tag = request.args.get('rfid_tag')
    
    if rfid_tag:
        # Fetch the user's current settings from the database based on the RFID tag
        user_data = get_user_by_rfid(rfid_tag)
        
        if user_data:
            return jsonify({
                'name': user_data['name'],
                'light_intensity': user_data['light_intensity'],
                'temperature': user_data['temperature'],
                'humidity': user_data['humidity'],
            })
        else:
            return jsonify({'error': 'User not found'}), 404
    else:
        return jsonify({'error': 'RFID tag not provided'}), 400

# @app.route('/data')
# def data():
#     global temperature, humidity, light_intensity

#     # Assuming you already have temperature, humidity, and light_intensity updated
#     try:
#         if temperature is not None and humidity is not None and light_intensity is not None:
#             return jsonify({
#                 'temperature': temperature,
#                 'humidity': humidity,
#                 'light_intensity': light_intensity,
#                 'fan_status': 'ON' if GPIO.input(Motor1) == GPIO.HIGH else 'OFF'
#             })
#         else:
#             return jsonify({'error': 'Sensor data not available'}), 500
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/data', methods=['GET'])
def data():
    global temperature, humidity, light_intensity, last_email_sent_time

    # Fetch RFID tag from the query parameters
    rfid_tag = request.args.get('rfid_tag')

    # Check if the RFID tag is provided
    if not rfid_tag:
        return jsonify({'error': 'RFID tag is required'}), 400

    # Get user data from the database based on the RFID tag
    user = get_user_by_rfid(rfid_tag)  # This function should fetch user data from DB

    if user:
        # User-specific preferences
        fav_temperature = user['temperature']
        fav_humidity = user['humidity']
        fav_light_intensity = user['light_intensity']

    if temperature is not None and humidity is not None and light_intensity is not None:
                # Return the sensor data and user preferences
         return jsonify({
                'temperature': temperature,
                'humidity': humidity,
                'light_intensity': light_intensity,
                'fan_status': fan_status,
                'fav_temperature': user['temperature'] if user else 0, # User's favorite temperature
                'fav_humidity': user['humidity'] if user else 0, # User's favorite humidity
                'fav_light_intensity': user['light_intensity'] if user else 0, # User's favorite light intensity
                'last_email_sent_time': last_email_sent_time.strftime('%Y-%m-%d %H:%M:%S') if last_email_sent_time else 'N/A'
            })
    else:
        return jsonify({'error': 'Sensor data not available'}), 500
 

if __name__ == '__main__':
    # Start the background thread for temperature and humidity readings
    temperature_thread = threading.Thread(target=read_temperature)
    temperature_thread.daemon = True
    temperature_thread.start()

    # Start the background thread for email response checking
    email_thread = threading.Thread(target=check_email_response)
    email_thread.daemon = True
    email_thread.start()


    # Start MQTT client and Flask server
    mqtt_client.connect(BROKER, 1883, 60)
    mqtt_client.subscribe(TOPIC_RFID)
    mqtt_client.subscribe(TOPIC_LIGHT)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()
    
    app.run(debug=True, host='0.0.0.0', port=5001)

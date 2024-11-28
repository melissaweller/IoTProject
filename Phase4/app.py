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

# GPIO 
GPIO.setmode(GPIO.BCM)

# DHT11 
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

user_data = None
user_data_lock = threading.Lock()

# MQTT 
BROKER = "172.20.10.8"  
TOPIC_RFID = "home/rfid/tag"
TOPIC_LIGHT = "home/light/intensity"
TOPIC_USER_LIGHT = "home/user/light/intensity"

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="IoT", 
        password="password",  
        database="IoT_Project"  
    )

# Email 
smtp_ssl_host = 'smtp.gmail.com'
smtp_ssl_port = 465
username = 'iotproject87@gmail.com'
password = 'eeka ftkg smpe qknf'
from_addr = 'iotproject87@gmail.com'
to_addrs = 'testingsample2003@gmail.com'

email_sent = False
fan_status = 0
led_status = False
last_email_sent_time = None
light_intensity = 0
temperature = None
humidity = None

mqtt_client = mqtt.Client()

def on_message(client, userdata, msg):
    global light_intensity, email_sent, last_email_sent_time, temperature, humidity, user_data, led_status

    try:
        if msg.topic == TOPIC_RFID:
            rfid_code = msg.payload.decode()
            print(f"RFID Tag Detected: {rfid_code}")

            user_info = get_user_info(rfid_code)

            if user_info: 
                with user_data_lock:  
                    user_data = {
                        'rfid_tag': rfid_code,
                        'name': user_info['name'],
                        'light_intensity': int(user_info['light_intensity']),
                        'temperature': float(user_info['temperature']),
                        'humidity': float(user_info['humidity']),
                        'user_pic': user_info['profile_pic']
                    }

                send_log_email()

                if user_data and 'light_intensity' in user_data:
                    mqtt_client.publish(TOPIC_USER_LIGHT, str(user_data['light_intensity']))

                if light_intensity < user_data['light_intensity']:
                    send_light_email()
                else:
                    print("Light is OFF")

                if user_data and 'temperature' in user_data and temperature is not None:
                    if temperature > user_data['temperature']:
                        if not email_sent or (last_email_sent_time and (datetime.now() - last_email_sent_time > timedelta(minutes=30))):
                            send_email(temperature)
                            email_sent = True
                            last_email_sent_time = datetime.now()
                            print("Temperature alert email sent!")
                    return jsonify({'temperature': temperature, 'humidity': humidity})
                else:
                    email_sent = False
            else:
                print(f"No user found for RFID: {rfid_code}")
                
        elif msg.topic == TOPIC_LIGHT:
            light_intensity = int(msg.payload.decode()) 
            print(f"Received light intensity: {light_intensity}")
            
            if user_data and 'light_intensity' in user_data:
                if light_intensity < user_data['light_intensity'] and not email_sent:
                    led_status = True
                    send_light_email()
                    email_sent = True  
                    last_email_sent_time = datetime.now() 
                    print("Email sent.")
                elif light_intensity >= user_data['light_intensity']:
                    led_status = False
                    email_sent = False  

    except Exception as e:
        print(f"Error processing message: {e}")

def get_user_info(rfid_tag):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE rfid_tag = %s", (rfid_tag,))
    user = cursor.fetchone()
    conn.close()
    return user

# Email to turn fan on
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

# Email for new user logged in
def send_log_email():
    global user_data
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    message = MIMEText(f"The user {user_data['name']} just signed in at {time_str}!")
    message['subject'] = 'User Logged In'
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

# Email for turning on light
def send_light_email():
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    message = MIMEText(f"The Light is ON at {time_str}.")
    message['subject'] = "Light Status Notification"
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

# To check email to turn on fan
def check_email_response():
    global email_sent
    while True:
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(username, password)
            mail.select('inbox')  

            status, data = mail.search(None, 'UNSEEN')
            mail_ids = data[0].split()

            if mail_ids:
                for mail_id in mail_ids:
                    status, email_data = mail.fetch(mail_id, '(RFC822)')
                    for response_part in email_data:
                        if isinstance(response_part, tuple):
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

                            if 'Temperature Alert' in subject and 'yes' in email_body.lower():
                                #fan_status = 1
                                GPIO.output(Motor1, GPIO.HIGH)
                                GPIO.output(Motor2, GPIO.HIGH)
                                GPIO.output(Motor3, GPIO.LOW)
                                print("Motor turned ON based on email response.")
                                print(fan_status)
                                email_sent = False 
                            elif 'Temperature Alert' in subject and 'no' in email_body.lower():
                                #fan_status = 0
                                GPIO.output(Motor1, GPIO.LOW)
                                GPIO.output(Motor2, GPIO.LOW)
                                GPIO.output(Motor3, GPIO.LOW)
                                print("Motor remains OFF based on email response.")
                                email_sent = False 

            mail.logout()
        except Exception as e:
            print(f"Error checking email: {e}")
        time.sleep(30)

def read_temperature():
    global temperature, humidity, email_sent, last_email_sent_time
    while True:
        result = dht_sensor.readDHT11()
        if result == 0:
            temperature = dht_sensor.getTemperature()
            humidity = dht_sensor.getHumidity()
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
        else:
            print("Failed to read from DHT11 sensor.")
        time.sleep(2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def data():
    global temperature, humidity, light_intensity, last_email_sent_time, user_data, email_sent
    motor_status = GPIO.input(Motor1)
    fan_status = motor_status == GPIO.LOW
    print(fan_status)

    if user_data is None:
        return jsonify({
            'light_intensity': light_intensity,
            'temperature': temperature,
            'humidity': humidity,
            'last_email_sent_time': last_email_sent_time.strftime('%Y-%m-%d %H:%M:%S') if last_email_sent_time else 'N/A',
            'led_status': led_status,
            'fan_status': fan_status,
            'user_pic': "/static/user_avatar.jpg"
        })

    with user_data_lock: 
        return jsonify({
            'light_intensity': light_intensity,
            'temperature': temperature,
            'humidity': humidity,
            'rfid': user_data['rfid_tag'],
            'name': user_data['name'],
            'user_light_intensity' : user_data['light_intensity'],
            'user_temperature': user_data['temperature'],
            'user_humidity': user_data['humidity'],
            'user_pic': user_data['user_pic'],
            'last_email_sent_time': last_email_sent_time.strftime('%Y-%m-%d %H:%M:%S') if last_email_sent_time else 'N/A',
            'led_status': led_status,
            'fan_status': fan_status
        })

if __name__ == '__main__':
    temperature_thread = threading.Thread(target=read_temperature)
    temperature_thread.daemon = True
    temperature_thread.start()

    email_thread = threading.Thread(target=check_email_response)
    email_thread.daemon = True
    email_thread.start()

    mqtt_client.connect(BROKER, 1883, 60)
    mqtt_client.subscribe(TOPIC_RFID)
    mqtt_client.subscribe(TOPIC_LIGHT)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()
    
    app.run(debug=True, host='0.0.0.0', port=5001)

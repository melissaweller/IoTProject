import RPi.GPIO as GPIO
import time
from Freenove_DHT import DHT
from flask import Flask, jsonify, render_template
import smtplib
from email.mime.text import MIMEText
import email
import imaplib
import threading

app = Flask(__name__)

# GPIO setup
GPIO.setmode(GPIO.BCM)

# LED
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

# Initial LED status (False = OFF, True = ON)
led_status = False

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

# Email setup
smtp_ssl_host = 'smtp.gmail.com'
smtp_ssl_port = 465
username = 'iotproject87@gmail.com'
password = 'kxro xgri kvhb jbdq'
from_addr = 'iotproject87@gmail.com'
to_addrs = 'testingsample2003@gmail.com'
email_sent = False

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
# Global variable to track motor state
motor_running = False

def check_email_response():
    global email_sent, motor_running
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
                                    motor_running = True
                                    print("Fan turned ON based on email response.")
                                elif 'no' in mail_content.lower():
                                    GPIO.output(Motor1, GPIO.LOW)  # Stop the motor
                                    motor_running = False
                                    print("Fan turned OFF based on email response.")
                                    email_sent = False 

            mail.logout()
        except Exception as e:
            print(f"Error checking email: {e}")

        time.sleep(30)

@app.route('/')
def index():
    global led_status
    motor_status = GPIO.input(Motor1)
    fan_status = motor_status == GPIO.HIGH 
    return render_template('index.html', fan_status=fan_status, led_status=led_status)

@app.route('/data')
def data():
    global email_sent
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

@app.route('/toggle', methods=['POST'])
def toggle():
    global led_status

    led_status = not led_status
    GPIO.output(LED_PIN, GPIO.HIGH if led_status else GPIO.LOW)
    
    return render_template('index.html', led_status=led_status)

@app.route('/fan/status')
def fan_status():
    status = GPIO.input(Motor1)
    return jsonify({'fan_status': status})

email_thread = threading.Thread(target=check_email_response)
email_thread.daemon = True 
email_thread.start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, jsonify, render_template
import RPi.GPIO as GPIO

app = Flask(__name__)

# MQTT Settings
broker = "10.0.0.89"  # IP address of your Raspberry Pi running Mosquitto broker
topic = "home/light/intensity"

# Email Settings
smtp_ssl_host = 'smtp.gmail.com'
smtp_ssl_port = 465
username = 'iotproject87@gmail.com'
password = 'kxro xgri kvhb jbdq'  # App password, not your Gmail account password
from_addr = 'iotproject87@gmail.com'
to_addrs = 'testingsample2003@gmail.com'

# Initialize variables
light_value = 0
led_status = False
email_sent = False

# LED pin setup (assuming LED is connected to GPIO17)
LED_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# Global variables to be updated by the MQTT callback
def on_message(client, userdata, msg):
    global light_value, led_status, email_sent

    try:
        # Log the message received
        print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
        
        light_value = int(msg.payload.decode())
        print(f"Decoded Light Intensity: {light_value}")
        
        if light_value < 400:
            led_status = True
            GPIO.output(LED_PIN, GPIO.HIGH)
            if not email_sent:
                send_email()
                email_sent = True
        else:
            led_status = False
            GPIO.output(LED_PIN, GPIO.LOW) 
            email_sent = False

    except Exception as e:
        print(f"Error processing MQTT message: {e}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")
    else:
        print(f"Failed to connect with result code {rc}")

# Connect to MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(broker, 1883, 60)
mqtt_client.subscribe(topic)
mqtt_client.loop_start()

# Send email function
def send_email():
    print("Sending email...")  # Add this line to debug
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    message = MIMEText(f"The Light is ON at {time_str}.")
    message['Subject'] = "Light Status Notification"
    message['From'] = from_addr
    message['To'] = to_addrs

    try:
        server = smtplib.SMTP(smtp_ssl_host, smtp_ssl_port)
        server.login(username, password)
        server.sendmail(from_addr, to_addrs, message.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


# Flask Routes
@app.route('/')
def index():
    # Render the index page with current status
    return render_template('index.html', light_value=light_value, led_status=led_status, email_sent=email_sent)

@app.route('/status')
def status():
    # Return current LED status and light intensity as JSON
    return jsonify({
        'led_status': led_status,
        'light_value': light_value
    })

@app.route('/data')
def get_data():
    # Placeholder data for temperature and humidity (update as needed)
    data = {
        "temperature": 22,  # Placeholder value
        "humidity": 50,     # Placeholder value
    }
    return jsonify(data)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

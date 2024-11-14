import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# MQTT Settings
broker = "localhost"  # Mosquitto broker running on RPi
topic = "home/light/intensity"

# Email Settings
smtp_ssl_host = 'smtp.gmail.com'
smtp_ssl_port = 465

username = 'iotproject87@gmail.com'
password = 'kxro xgri kvhb jbdq' # actual password: iotproject2024

from_addr = 'iotproject87@gmail.com'
to_addrs = 'testingsample2003@gmail.com'

# Callback for when a message is received
def on_message(client, userdata, msg):
    light_value = int(msg.payload.decode())
    print(f"Light Intensity: {light_value}")
    
    if light_value < 400:
        # Turn on LED (RPi GPIO control code can go here)
        print("Turning on the LED")
        
        # Send email notification
        send_email()

# Send email
def send_email():
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
    except Exception as e:
        print(f"Error sending email: {e}")

# MQTT setup
client = mqtt.Client()
client.on_message = on_message
client.connect(broker, 1883, 60)
client.subscribe(topic)

client.loop_start()
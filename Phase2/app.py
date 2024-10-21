import Adafruit_DHT
import RPi.GPIO as GPIO
from flask import Flask, jsonify, render_template
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# GPIO setup for fan
FAN_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)

# DHT sensor setup
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 17

# connect with Google's servers
smtp_ssl_host = 'smtp.gmail.com'
smtp_ssl_port = 465

# Email configuration
EMAIL_ADDRESS = "iotproject87@gmail.com"
EMAIL_PASSWORD = "vucp oftn gupf ttjv" # actual password: iotproject2024

def send_email(temperature):
    msg = MIMEText(f"The current temperature is {temperature}°C. Would you like to turn on the fan?")
    msg['Subject'] = 'Temperature Alert'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS  # Send to yourself for testing

    with smtplib.SMTP(smtp_ssl_host, smtp_ssl_host) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    
    if temperature is not None and humidity is not None:
        if temperature > 24:
            send_email(temperature)
        
        return jsonify({'temperature': temperature, 'humidity': humidity})
    else:
        return jsonify({'error': 'Failed to retrieve data'}), 500

@app.route('/fan/<status>')
def control_fan(status):
    if status.lower() == 'on':
        GPIO.output(FAN_PIN, GPIO.HIGH)
    else:
        GPIO.output(FAN_PIN, GPIO.LOW)
    return '', 204

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()  # Cleanup GPIO on exit

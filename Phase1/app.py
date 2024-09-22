from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO

app = Flask(__name__)

# Setup the GPIO
GPIO.setmode(GPIO.BCM)
LED_PIN = 4
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

# Global variable to track the LED state
led_state = 'off'

@app.route("/")
def index():
    return render_template('hello_there.html', led_state=led_state)

@app.route("/toggle", methods=['POST'])
def toggle_led():
    global led_state
    state = request.form['state']
    
    if state == 'on':
        GPIO.output(LED_PIN, GPIO.HIGH)
        led_state = 'on'  # Update the state to 'on'
        print("LED turned on")
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        led_state = 'off'  # Update the state to 'off'
        print("LED turned off")
    
    return jsonify({'led_state': led_state})  # Return the new state as JSON

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()

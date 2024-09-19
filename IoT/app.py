from flask import Flask, render_template, request

# **** COMMENTED IT OUT SO I COULD RUN ON WINDOWS
# import RPi.GPIO as GPIO 

app = Flask(__name__)

# Set up the GPIO pin for the LED

# **** COMMENTED IT OUT SO I COULD RUN ON WINDOWS
# LED_PIN = 17
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(LED_PIN, GPIO.OUT)

# Initial LED status (False = OFF, True = ON)
led_status = False

@app.route('/')
def index():
    global led_status
    # Render the HTML template with the current LED status
    return render_template('index.html', led_status=led_status)

@app.route('/toggle', methods=['POST'])
def toggle():
    global led_status

    led_status = not led_status
    # GPIO.output(LED_PIN, GPIO.HIGH if led_status else GPIO.LOW)
    
    return render_template('index.html', led_status=led_status)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

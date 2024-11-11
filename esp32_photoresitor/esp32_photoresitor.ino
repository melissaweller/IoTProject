
// constants won't change
#define LIGHT_SENSOR_PIN 36  // ESP32 pin GPIO36 (ADC0) connected to light sensor
#define LED_PIN 33           // ESP32 pin GPIO22 connected to LED
#define ANALOG_THRESHOLD 4000

void setup() {
  analogSetAttenuation(ADC_11db);
  pinMode(LED_PIN, OUTPUT);  // set ESP32 pin to output mode
}

void loop() {
  int analogValue = analogRead(LIGHT_SENSOR_PIN);  // read the value on analog pin

  if (analogValue < ANALOG_THRESHOLD)
    digitalWrite(LED_PIN, HIGH);  // turn on LED
  else
    digitalWrite(LED_PIN, LOW);  // turn off LED
}

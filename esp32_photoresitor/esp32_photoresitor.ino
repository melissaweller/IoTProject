#include <WiFi.h>
#include <PubSubClient.h>

// Wi-Fi settings for school
//const char* ssid = "TP-Link_2AD8";
//const char* password = "14730078";

// Wi-Fi settings for home
const char* ssid = "Helix-GW";
const char* password = "miagw0707";

// MQTT Broker settings
const char* mqtt_server = "10.0.0.89";        
const char* mqtt_topic = "home/light/intensity";

// Pins
#define LIGHT_SENSOR_PIN 36  // ESP32 pin GPIO36 (ADC0) connected to light sensor
#define LED_PIN 33           // ESP32 pin GPIO33 connected to LED
#define ANALOG_THRESHOLD 400

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  // Initialize serial and Wi-Fi
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("WiFi connected");

  // Connect to MQTT Broker
  client.setServer(mqtt_server, 1883);
  while (!client.connected()) {
    if (client.connect("ESP32_Client")) {
      Serial.println("Connected to MQTT Broker");
    } else {
      Serial.print("Failed to connect to MQTT, state: ");
      Serial.println(client.state());
      delay(2000);
    }
  }

  // Set attenuation for ADC (adjust according to sensor range)
  analogSetAttenuation(ADC_11db);
}

void loop() {
  // Read light intensity value
  int lightValue = analogRead(LIGHT_SENSOR_PIN);

  // Send light value to the MQTT broker
  if (client.connected()) {
    String payload = String(lightValue);
    client.publish(mqtt_topic, payload.c_str());
  } else {
    // If disconnected, try reconnecting
    client.connect("ESP32_Client");
  }

  // Control the LED based on the light intensity
  if (lightValue < ANALOG_THRESHOLD) {
    digitalWrite(LED_PIN, HIGH);  // Turn on the LED if light is too low
  } else {
    digitalWrite(LED_PIN, LOW);  // Turn off the LED if light is sufficient
  }

  client.loop();  // Keep MQTT connection alive
  delay(1000);    // Delay to avoid sending data too rapidly
}

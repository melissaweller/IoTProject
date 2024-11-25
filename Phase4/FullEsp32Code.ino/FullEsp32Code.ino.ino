#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

// Wi-Fi settings
// const char* ssid = "TP-Link_2AD8";
// const char* password = "14730078";

 const char* ssid = "DavidesiPhone";
 const char* password = "who is joe";

// MQTT Broker settings
const char* mqtt_server = "172.20.10.7";        
const char* mqtt_light_topic = "home/light/intensity"; // Topic for light intensity
const char* mqtt_rfid_topic = "home/rfid/tag";         // Topic for RFID data

// Pins
#define LIGHT_SENSOR_PIN 36  // ESP32 pin GPIO36 (ADC0) connected to light sensor
#define LED_PIN 33           // ESP32 pin GPIO33 connected to LED
#define ANALOG_THRESHOLD 400

// RFID Module pins (adjust based on your setup)
#define RST_PIN 5  // Reset pin
#define SDA_PIN 4  // SDA pin

// Declare RFID module instance
MFRC522 rfid(SDA_PIN, RST_PIN);

WiFiClient espClient;
PubSubClient client(espClient);

// Function prototypes
void setupWiFi();
void setupMQTT();
void handleLightSensor();
void handleRFID();

void setup() {
  // Initialize serial and peripherals
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  // Connect to Wi-Fi
  setupWiFi();

  // Connect to MQTT Broker
  setupMQTT();

  // Initialize SPI bus
  SPI.begin();

  // Initialize RFID reader
  rfid.PCD_Init();
  Serial.println("RFID reader initialized. Place a card near the reader...");
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    setupMQTT();
  }
  client.loop();

  // Handle light intensity sensor and MQTT publishing
  handleLightSensor();

  // Handle RFID reading and MQTT publishing
  handleRFID();

  delay(1000);  // Loop delay
}

// Function to set up Wi-Fi
void setupWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

// Function to set up MQTT
void setupMQTT() {
  client.setServer(mqtt_server, 1883);
  Serial.println("Connecting to MQTT Broker...");
  while (!client.connected()) {
    if (client.connect("ESP32_Client")) {
      Serial.println("Connected to MQTT Broker");
    } else {
      Serial.print("Failed to connect to MQTT, state: ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// Function to handle light intensity sensor
void handleLightSensor() {
  int lightValue = analogRead(LIGHT_SENSOR_PIN);

  // Publish light intensity to MQTT broker
  if (client.connected()) {
    String payload = String(lightValue);
    client.publish(mqtt_light_topic, payload.c_str());
    Serial.println("Published light intensity: " + payload);
  }

  // Control LED based on light intensity
  if (lightValue < ANALOG_THRESHOLD) {
    digitalWrite(LED_PIN, HIGH);  // Turn on LED
    Serial.println("LED ON: Low light detected");
  } else {
    digitalWrite(LED_PIN, LOW);  // Turn off LED
    Serial.println("LED OFF: Sufficient light");
  }
}

// Function to handle RFID
void handleRFID() {
  // Check if a new card is present
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return; // No new card detected
  }

  // Read and format the UID of the card
  String rfidTag = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    rfidTag += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "") + String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) rfidTag += ":"; // Add a colon between bytes
  }

  Serial.println("RFID Tag Detected: " + rfidTag);

  // Publish the RFID UID to the MQTT topic
  if (client.connected()) {
    client.publish(mqtt_rfid_topic, rfidTag.c_str());
    Serial.println("Published RFID data: " + rfidTag);
  }

  // Halt the card to stop further reads
  rfid.PICC_HaltA();
}

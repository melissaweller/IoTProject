#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

// Wi-Fi settings
const char* ssid = "Helix-GW";
const char* password = "miagw0707";

// MQTT Broker settings
const char* mqtt_server = "10.0.0.89";        
const char* mqtt_light_topic = "home/light/intensity";
const char* mqtt_rfid_topic = "home/rfid/tag";         

// Pins
#define LIGHT_SENSOR_PIN 36 
#define LED_PIN 33       
#define ANALOG_THRESHOLD 400

#define RST_PIN 4 
#define SDA_PIN 5  

MFRC522 rfid(SDA_PIN, RST_PIN);

WiFiClient espClient;
PubSubClient client(espClient);

void setupWiFi();
void setupMQTT();
void handleLightSensor();
void handleRFID();

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  setupWiFi();
  setupMQTT();

  SPI.begin();

  rfid.PCD_Init();
  Serial.println("RFID reader initialized. Place a card near the reader...");
}

void loop() {
  if (!client.connected()) {
    setupMQTT();
  }
  client.loop();

  handleLightSensor();
  handleRFID();

  delay(1000);  
}

void setupWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

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

void handleLightSensor() {
  int lightValue = analogRead(LIGHT_SENSOR_PIN);

  if (client.connected()) {
    String payload = String(lightValue);
    client.publish(mqtt_light_topic, payload.c_str());
  }

  if (lightValue < ANALOG_THRESHOLD) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);  
  }
}

void handleRFID() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return; 
  }

  String rfidTag = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    rfidTag += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "") + String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) rfidTag += ":"; 
  }

  Serial.println("RFID Tag Detected: " + rfidTag);

  if (client.connected()) {
    client.publish(mqtt_rfid_topic, rfidTag.c_str());
  }

  rfid.PICC_HaltA();
}

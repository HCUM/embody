#include <esp_wifi.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <WiFiClient.h>
#include <ESP_WiFiManager.h>

#define ESP_getChipId()   ((uint32_t)ESP.getEfuseMac())
#define PERIODE    4L //equals to 250Hz sampling rate -> adjust if higher sampling rate is required

// SSID and PW for Config Portal
String ssid = "EMG_" + String(ESP_getChipId(), HEX);
const char* password = "emg";

// SSID and PW for your Router
String Router_SSID;
String Router_Pass;


//sensor pins, change to your configuration if needed
#define SENSOR_PIN_1 32
#define SENSOR_PIN_2 33
#define SENSOR_PIN_3 34
#define SENSOR_PIN_4 35
#define SENSOR_PIN_5 36
#define SENSOR_PIN_6 39

//broadcasting
IPAddress udpAddress; //gets assigned when connected to a network
const uint udpPort = 3333; //adjust if port is n/a

//sensor values
int value1;
int value2;
int value3;
int value4;
int value5;
int value6;
unsigned long time1;

WiFiUDP udp;
boolean connected = false;

//trigger for config
const int TRIGGER_PIN = 0;

// Indicates whether ESP has WiFi credentials saved from previous session
bool initialConfig = false;

void setup() 
{
  // initialize the LED digital pin as an output.
  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  pinMode(SENSOR_PIN_1, INPUT);
  pinMode(SENSOR_PIN_2, INPUT);
  pinMode(SENSOR_PIN_3, INPUT);
  pinMode(SENSOR_PIN_4, INPUT);
  pinMode(SENSOR_PIN_5, INPUT);
  pinMode(SENSOR_PIN_6, INPUT);
  Serial.begin(115200);
  Serial.println("\nStarting");

  unsigned long startedAt = millis();
  
  ESP_WiFiManager ESP_wifiManager("ConfigOnSwitch");
  ESP_wifiManager.setMinimumSignalQuality(-1);

  //check for previous credentials
  Router_SSID = ESP_wifiManager.WiFi_SSID();
  Router_Pass = ESP_wifiManager.WiFi_Pass();
  ssid.toUpperCase();
  
  if (Router_SSID == "")
  {
    Serial.println("We haven't got any access point credentials, so get them now");   
    //it starts an access point 
    //and goes into a blocking loop awaiting configuration
    if (!ESP_wifiManager.startConfigPortal((const char *) ssid.c_str(), password)) 
      Serial.println("Not connected to WiFi but continuing anyway.");
    else 
      Serial.println("WiFi connected...yeey :)");    
  }

  #define WIFI_CONNECT_TIMEOUT        30000L
  #define WHILE_LOOP_DELAY            200L
  #define WHILE_LOOP_STEPS            (WIFI_CONNECT_TIMEOUT / ( 3 * WHILE_LOOP_DELAY ))
  
  startedAt = millis();
  
  while ( (WiFi.status() != WL_CONNECTED) && (millis() - startedAt < WIFI_CONNECT_TIMEOUT ) )
  {   
    WiFi.mode(WIFI_STA);
    WiFi.persistent (true);
    // We start by connecting to a WiFi network
  
    Serial.print("Connecting to ");
    Serial.println(Router_SSID);

    //register for WiFiEvents
    WiFi.onEvent(WiFiEvent);
    WiFi.begin(Router_SSID.c_str(), Router_Pass.c_str());

    int i = 0;
    while((!WiFi.status() || WiFi.status() >= WL_DISCONNECTED) && i++ < WHILE_LOOP_STEPS)
    {
      delay(WHILE_LOOP_DELAY);
    }    
  }

  Serial.print("After waiting ");
  Serial.print((millis()- startedAt) / 1000);
  Serial.print(" secs more in setup(), connection result is ");

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.print("connected. Local IP: ");
    Serial.println(WiFi.localIP());

  }
  else
    Serial.println(ESP_wifiManager.getStatus(WiFi.status()));
}


//wifi event handler
void WiFiEvent(WiFiEvent_t event) {
  switch (event) {
    case SYSTEM_EVENT_STA_GOT_IP:
      //When connected set
      Serial.print("WiFi connected! IP address: ");
      Serial.println(WiFi.localIP());
      //initializes the UDP state
      udp.begin(WiFi.localIP(), udpPort);
      assignBroadcastAddress();
      //This initializes the transfer buffer
      connected = true;
      break;
    case SYSTEM_EVENT_STA_DISCONNECTED:
      Serial.println("WiFi lost connection");
      connected = false;
      break;
  }
}

void assignBroadcastAddress(void){
  udpAddress = WiFi.localIP();
  udpAddress[3] = 255;
}

void loop()
{
  ulong roundtime = millis();
  // is configuration portal requested?
  if (digitalRead(TRIGGER_PIN) == LOW) {
    doConfig();
  }
   
  //only send data when connected
  if (connected) {
    sendPacket();
  }
  //Wait for a total time of approx. 4 milliseconds to ensure 250Hz
  while((millis() - roundtime) < PERIODE);
}

void doConfig(void){
    Serial.println("\nConfiguration portal requested.");
    
    ESP_WiFiManager ESP_wifiManager;
    Serial.print("Opening configuration portal. ");
    
    //Check if there is stored WiFi router/password credentials.
    Router_SSID = ESP_wifiManager.WiFi_SSID();
    if (Router_SSID != ""){
      Serial.println("Got stored Credentials. No timeout");
    }
    else{
      Serial.println("No stored Credentials. No timeout");
    }

    //start config
    if (!ESP_wifiManager.startConfigPortal((const char *) ssid.c_str(), password)){
      Serial.println("Not connected to WiFi but continuing anyway.");
    } 
    else{
      //if you get here you have connected to the WiFi
      Serial.println("connected.");
    }
}

void sendPacket(void){
    //read out all channels to allow for time-consistent values
    value1 = analogRead(SENSOR_PIN_1);
    value2 = analogRead(SENSOR_PIN_2);
    value3 = analogRead(SENSOR_PIN_3);
    value4 = analogRead(SENSOR_PIN_4);
    value5 = analogRead(SENSOR_PIN_5);
    value6 = analogRead(SENSOR_PIN_6);
    time1 = millis();

    //remove if sampling rate is of importance
    delayMicroseconds(500);
    
    udp.beginPacket(udpAddress, udpPort);
    udp.printf("%lu;%u;%u;%u;%u;%u;%u", time1, value1, value2, value3, value4, value5, value6);
    udp.endPacket();
    delayMicroseconds(500);
}

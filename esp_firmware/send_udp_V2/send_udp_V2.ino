#include <WiFi.h>
#include <WiFiUdp.h>

// WiFi network name and password:
//TODO: update network credentials if needed
const char * networkName = "TODO";
const char * networkPswd = "TODO";

//sensor pin
#define SENSOR_PIN_1 32
#define SENSOR_PIN_2 33
#define SENSOR_PIN_3 34
#define SENSOR_PIN_4 35
#define SENSOR_PIN_5 36
#define SENSOR_PIN_6 39

#define PERIODE    4L //equals to 250Hz sampling rate -> adjust if higher sampling rate is required


//IP address to send UDP data to:
// either use the ip address of the server or
// a network broadcast address
//TODO: update if needed
//broadcast
const char * udpAddress = "x.x.x.255";
const int udpPort = 3333;

//Are we currently connected?
boolean connected = false;

//sensor value
int value1;
int value2;
int value3;
int value4;
int value5;
int value6;
unsigned long time1;

//The udp library class
WiFiUDP udp;

void setup() {
  // Initilize hardware serial:
  Serial.begin(115200);
  pinMode(SENSOR_PIN_1, INPUT);
  pinMode(SENSOR_PIN_2, INPUT);
  pinMode(SENSOR_PIN_3, INPUT);
  pinMode(SENSOR_PIN_4, INPUT);
  pinMode(SENSOR_PIN_5, INPUT);
  pinMode(SENSOR_PIN_6, INPUT);

  //Connect to the WiFi network
  connectToWiFi(networkName, networkPswd);
}

void loop() {
  ulong roundtime = millis();
   
  //only send data when connected
  if (connected) {
    sendPacket();
  }
  //Wait for a total time of approx. 4 milliseconds to ensure 250Hz
  while((millis() - roundtime) < PERIODE);
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

void connectToWiFi(const char * ssid, const char * pwd) {
  Serial.println("Connecting to WiFi network: " + String(ssid));

  // delete old config
  WiFi.disconnect(true);
  //register event handler
  WiFi.onEvent(WiFiEvent);

  //Initiate connection
  WiFi.begin(ssid, pwd);

  Serial.println("Waiting for WIFI connection...");
}

//wifi event handler
void WiFiEvent(WiFiEvent_t event) {
  switch (event) {
    case SYSTEM_EVENT_STA_GOT_IP:
      //When connected set
      Serial.print("WiFi connected! IP address: ");
      Serial.println(WiFi.localIP());
      //initializes the UDP state
      //This initializes the transfer buffer
      udp.begin(WiFi.localIP(), udpPort);
      connected = true;
      break;
    case SYSTEM_EVENT_STA_DISCONNECTED:
      Serial.println("WiFi lost connection");
      connected = false;
      break;
  }
}

#include "EspMQTTClient.h"
#include <Wire.h>
#include "SparkFun_AS7265X.h" //Click here to get the library: http://librarymanager/All#SparkFun_AS7265X

//---- Setup update frequency -----//
const long TEMP_updateInterval = 3000; // How long to change temp and update, 10000 = 10 sec
unsigned long TEMP_currentMillis = 0;
unsigned long TEMP_previousMillis = 0; // store last time temp update

int WifiTryCount=0;
long randNumber;
int led = 5;

AS7265X sensor;

int A,B,C,D,E,F,G,H,I,J,K,L,R,S,T,U,V,W;
int A2,B2,C2,D2,E2,F2,G2,H2,I2,J2,K2,L2,R2,S2,Td2,U2,V2,W2;

// EspMQTTClient client(
//   "JayY",
//   "a22658802",
//   "172.20.10.13",  // MQTT Broker server ip
//   "",   // Can be omitted if not needed
//   "",   // Can be omitted if not needed
//   "SpectrumSensor",     // Client name that uniquely identify your device
//   1883              // The MQTT port, default to 1883. this line can be omitted
// );

EspMQTTClient client(
  "Etch_Edge",
  "etch123123",
  "192.168.68.100",  // MQTT Broker server ip
  "",   // Can be omitted if not needed
  "",   // Can be omitted if not needed
  "SpectrumSensor",     // Client name that uniquely identify your device
  1883              // The MQTT port, default to 1883. this line can be omitted
);

void setup()
{
  Serial.begin(115200);
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW); 
  // Optionnal functionnalities of EspMQTTClient :
  client.enableDebuggingMessages(); // Enable debugging messages sent to serial output
  //client.enableHTTPWebUpdater();  // Enable the web updater. User and password default to values of MQTTUsername and MQTTPassword. These can be overrited with enableHTTPWebUpdater("user", "password").
  //client.enableLastWillMessage("TestClient/lastwill", "I am going offline"); // You can activate the retain flag by setting the third parameter to true


  if (sensor.begin() == false)
  {
    Serial.println("感測器錯誤");
    delay(2000);
    
    ESP.restart();
  }
    //There are four measurement modes - the datasheet describes it best
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
  //sensor.setMeasurementMode(AS7265X_MEASUREMENT_MODE_4CHAN); //Channels STUV on x51
  //sensor.setMeasurementMode(AS7265X_MEASUREMENT_MODE_4CHAN_2); //Channels RTUW on x51
  //sensor.setMeasurementMode(AS7265X_MEASUREMENT_MODE_6CHAN_CONTINUOUS); //All 6 channels on all devices
  sensor.setMeasurementMode(AS7265X_MEASUREMENT_MODE_6CHAN_ONE_SHOT); //Default: All 6 channels, all devices, just once
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

  //Drive current can be set for each LED
  //4 levels: 12.5, 25, 50, and 100mA
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
  //White LED has max forward current of 120mA
  sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_12_5MA, AS7265x_LED_WHITE); //Default
  //sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_25MA, AS7265x_LED_WHITE); //Allowed
  // sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_50MA, AS7265x_LED_WHITE); //Allowed
  // sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_100MA, AS7265x_LED_WHITE); //Allowed

  //UV LED has max forward current of 30mA so do not set the drive current higher
  sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_12_5MA, AS7265x_LED_UV); //Default
  // sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_25MA, AS7265x_LED_UV-bad); //Not allowed
  // sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_50MA, AS7265x_LED_UV-bad); //Not allowed
  //sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_100MA, AS7265x_LED_UV-bad); //Not allowed

  //IR LED has max forward current of 65mA
  sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_12_5MA, AS7265x_LED_IR); //Default
  //sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_25MA, AS7265x_LED_IR); //Allowed
  // sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_50MA, AS7265x_LED_IR); //Allowed
  //sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_100MA, AS7265x_LED_IR-bad); //Not allowed
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

  //The status indicator (Blue LED) can be enabled/disabled and have its current set
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
  sensor.disableIndicator();

  //sensor.setIndicatorCurrent(AS7265X_INDICATOR_CURRENT_LIMIT_1MA);
  sensor.setIndicatorCurrent(AS7265X_INDICATOR_CURRENT_LIMIT_2MA);
  //sensor.setIndicatorCurrent(AS7265X_INDICATOR_CURRENT_LIMIT_4MA);
  // sensor.setIndicatorCurrent(AS7265X_INDICATOR_CURRENT_LIMIT_8MA); //Default
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

  //The interrupt pin is active low and can be enabled or disabled
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    //sensor.enableInterrupt(); //Default
  sensor.disableInterrupt();
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

  //There are four gain settings. It is possible to saturate the reading so don't simply jump to 64x.
  //有四種增益設置。 讀數可能會飽和，因此不要簡單地跳到 64x。
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
  // sensor.setGain(AS7265X_GAIN_1X); //Default
  // sensor.setGain(AS7265X_GAIN_37X); //This is 3.7x
  sensor.setGain(AS7265X_GAIN_16X);
  // sensor.setGain(AS7265X_GAIN_64X);
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

  //Integration cycles is from 0 (2.78ms) to 255 (711ms)
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
  sensor.setIntegrationCycles(255); //Default 255*2.8ms = 711ms per reading (Max ADC 65535)
  // sensor.setIntegrationCycles(128);
  //  sensor.setIntegrationCycles(64); //Default 65*2.8ms = 182ms per reading (Max ADC 65535)
  // sensor.setIntegrationCycles(49); //Default 50*2.8ms = 140ms per reading
  // sensor.setIntegrationCycles(1); //2*2.8ms = 5.6ms per reading (Max ADC 2047)
  //-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

  Wire.setClock(400000);

  sensor.disableBulb(AS7265x_LED_IR);
  sensor.disableBulb(AS7265x_LED_WHITE);
  sensor.disableBulb(AS7265x_LED_UV);

  // sensor.enableBulb(AS7265x_LED_WHITE);
}
 
// This function is called once everything is connected (Wifi and MQTT)
// WARNING : YOU MUST IMPLEMENT IT IF YOU USE EspMQTTClient
void onConnectionEstablished()
{
    // sensor.enableBulb(AS7265x_LED_WHITE);
    // Subscribe to "mytopic/test" and display received message to Serial
    client.subscribe("message/hello", [](const String &payload)
                     { Serial.println(payload); });
 
    // Subscribe to "mytopic/wildcardtest/#" and display received message to Serial
    //client.subscribe("mytopic/wildcardtest/#", [](const String &topic, const String &payload)
    //                 { Serial.println("(From wildcard) topic: " + topic + ", payload: " + payload); });
 
    // Publish a message to "mytopic/test"
    client.publish("studio/temp1", "Let's go!"); // You can activate the retain flag by setting the third parameter to true
 
    // Execute delayed instructions
    //client.executeDelayed(5 * 1000, []()
    //                      { client.publish("mytopic/wildcardtest/test123", "This is a message sent 5 seconds later"); });
}
 
String getData(){
  sensor.takeMeasurements(); 
  
  A = sensor.getA();
  B = sensor.getB();
  C = sensor.getC();
  D = sensor.getD();
  E = sensor.getE();
  F = sensor.getF();
  G = sensor.getG();
  H = sensor.getH();
  I = sensor.getI();
  J = sensor.getJ();
  K = sensor.getK();
  L = sensor.getL();
  R = sensor.getR();
  S = sensor.getS();
  T = sensor.getT();
  U = sensor.getU();
  V = sensor.getV();
  W = sensor.getW();

  String string_value_1 = String(A)+","+String(B)+","+String(C)+","+String(D)+","+String(E)+","+String(F)+","+String(G)+","+String(H)+","+String(I)+"," ;
  String string_value_2 = String(J)+","+String(K)+","+String(L)+","+String(R)+","+String(S)+","+String(T)+","+String(U)+","+String(V)+","+String(W);

  String str_val =  string_value_1 + string_value_2;

  return str_val;
}

String getCalibratedData(){
  sensor.takeMeasurements(); 
  
  A2 = sensor.getCalibratedA();
  B2 = sensor.getCalibratedB();
  C2 = sensor.getCalibratedC();
  D2 = sensor.getCalibratedD();
  E2 = sensor.getCalibratedE();
  F2 = sensor.getCalibratedF();
  G2 = sensor.getCalibratedG();
  H2 = sensor.getCalibratedH();
  I2 = sensor.getCalibratedI();
  J2 = sensor.getCalibratedJ();
  K2 = sensor.getCalibratedK();
  L2 = sensor.getCalibratedL();
  R2 = sensor.getCalibratedR();
  S2 = sensor.getCalibratedS();
  Td2 = sensor.getCalibratedT();
  U2 = sensor.getCalibratedU();
  V2 = sensor.getCalibratedV();
  W2 = sensor.getCalibratedW();

  String string_value_1 = String(A2)+","+String(B2)+","+String(C2)+","+String(D2)+","+String(E2)+","+String(F2)+","+String(G2)+","+String(H2)+","+String(I2)+"," ;
  String string_value_2 = String(J2)+","+String(K2)+","+String(L2)+","+String(R2)+","+String(S2)+","+String(Td2)+","+String(U2)+","+String(V2)+","+String(W2);

  String str_val =  string_value_1 + string_value_2;

  return str_val;
}

void loop()
{

  TEMP_currentMillis = millis();
  if(TEMP_currentMillis - TEMP_previousMillis >= TEMP_updateInterval){
      TEMP_previousMillis = TEMP_currentMillis;

      digitalWrite(led, HIGH);

      // delay(300);

      int oneSensorTemp = sensor.getTemperature();
      String tempStr = String(oneSensorTemp);

      String data = getData();
      String calibratedData = getCalibratedData();

      digitalWrite(led, LOW); //Turn on led
      
      //Publish
      client.publish("spectrum/getData", data);
      client.publish("spectrum/calibratedData", calibratedData);
      client.publish("spectrum/Temp", tempStr);

      // Here is how to subscribe
      // client.subscribe("message/hello", [](const String &payload) { Serial.println(payload); });

      
  }
  

  client.loop();

  if (!client.isConnected()) {
      // sensor.disableBulb(AS7265x_LED_WHITE);
      if (WifiTryCount++ >= 20)  ESP.restart();
      delay(500);
  }

}
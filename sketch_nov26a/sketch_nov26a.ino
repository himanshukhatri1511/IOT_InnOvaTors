#include <Wire.h>
#include <RTClib.h>
#include <LowPower.h>
#include <SoftwareSerial.h>
#include <DHT.h>

#define DHTPIN 3
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
RTC_DS3231 rtc;
SoftwareSerial rfModule(10, 11);

const int interruptPin = 2;
volatile bool alarmTriggered = false;
String key = "YDN3h0nw1vv6SE0Buwx0h3K0foeDV2yU";  // Encryption key as a string

void setup() {
  Serial.begin(9600);
  rfModule.begin(9600);
  dht.begin();

  if (!rtc.begin()) {
    Serial.println("Couldn't find RTC!");
    while (1);
  }

  if (rtc.lostPower()) {
    Serial.println("RTC lost power, setting time!");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  // Set Alarm1 for today at 23:26:30
  rtc.clearAlarm(1);
  rtc.setAlarm1(DateTime(0, 0, 0, 11, 41, 0), DS3231_A1_Hour);

  pinMode(interruptPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(interruptPin), wakeUp, FALLING);

  Serial.println("Setup complete, going to sleep.");
  enterDeepSleep();
}

void loop() {
  if (alarmTriggered) {
    alarmTriggered = false;
    sendData();
    rtc.clearAlarm(1); 
    enterDeepSleep();
  }
}

void wakeUp() {
  alarmTriggered = true;
}

void sendData() {
  Serial.println("Sending temperature data...");

  int i = 0;
  while (i < 30) {
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    String message = "{\"bin_num\":4, \"Temp\":\"" + String(temperature, 2) + "\", \"Humidity\":\"" + String(humidity, 2) + "\"}";
    String encryptedMessage = xorEncryptToHex(message, key);  // Encrypt the message and convert to hex
    rfModule.println(encryptedMessage);
    Serial.println("Sent: " + encryptedMessage);
    i++;
    delay(1000);
  }

  Serial.println("Data transmission complete.");
}

String xorEncryptToHex(String input, String key) {
  String output = "";
  int keyLength = key.length();
  for (int i = 0; i < input.length(); i++) {
    char encryptedChar = input[i] ^ key[i % keyLength];
    char buf[3]; // Buffer to hold hex value
    sprintf(buf, "%02x", encryptedChar); // Format as hex
    output += String(buf);
  }
  return output;
}

void enterDeepSleep() {
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
}
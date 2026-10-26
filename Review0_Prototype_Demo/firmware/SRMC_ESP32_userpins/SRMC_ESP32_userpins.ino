
/*
  SRMC Review-0 Firmware -- ESP32 DevKit / WROOM-32

  Serial format (115200 baud):
  SRMC,millis,tempC,rh,soilRaw,rainWet,rainRaw

  soilRaw : Soil moisture ADC (0-4095)
  rainWet : 1 = wet, 0 = dry
  rainRaw : Rain sensor AO ADC (0-4095)
*/

#include <Arduino.h>
#include <DHT.h>

// ---------------- PIN CONFIGURATION ----------------
#define PIN_DHT       32
#define PIN_SOIL      35
#define PIN_RAIN_AO   34
#define PIN_RAIN_DO   27
#define PIN_SOIL_DO   26
#define PIN_LED        2

#define DHT_TYPE DHT11

// Most rain modules output LOW when wet.
// Change to false if your module outputs HIGH when wet.
#define RAIN_ACTIVE_LOW true

#define SAMPLE_MS     1000
#define DHT_PERIOD_MS 2000

DHT dht(PIN_DHT, DHT_TYPE);

float lastT = -999.0;
float lastH = -999.0;

unsigned long lastDHT = 0;
unsigned long lastPrint = 0;

// Average ADC readings to reduce noise.
int readAverage(int pin) {
  long total = 0;

  for (int i = 0; i < 16; i++) {
    total += analogRead(pin);
    delay(2);
  }

  return total / 16;
}

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  pinMode(PIN_RAIN_DO, INPUT);
  pinMode(PIN_SOIL_DO, INPUT);
  pinMode(PIN_LED, OUTPUT);

  digitalWrite(PIN_LED, LOW);

  dht.begin();

  delay(1000);

  Serial.println(
    "# SRMC firmware ESP32 baud=115200 "
    "fields=SRMC,ms,tempC,rh,soilRaw,rainWet,rainRaw"
  );
}

void loop() {
  unsigned long now = millis();

  // Read DHT11 every 2 seconds.
  if (now - lastDHT >= DHT_PERIOD_MS) {
    lastDHT = now;

    float t = dht.readTemperature();
    float h = dht.readHumidity();

    if (!isnan(t) && !isnan(h)) {
      lastT = t;
      lastH = h;
    } else {
      lastT = -999.0;
      lastH = -999.0;
    }
  }

  // Send one data line every second.
  if (now - lastPrint >= SAMPLE_MS) {
    lastPrint = now;

    int soilRaw = readAverage(PIN_SOIL);
    int rainRaw = readAverage(PIN_RAIN_AO);

    int rainLevel = digitalRead(PIN_RAIN_DO);

    bool wet = RAIN_ACTIVE_LOW
               ? (rainLevel == LOW)
               : (rainLevel == HIGH);

    digitalWrite(PIN_LED, wet ? HIGH : LOW);

    // Preserve the exact MATLAB serial protocol.
    Serial.printf(
      "SRMC,%lu,%.1f,%.1f,%d,%d,%d\n",
      now,
      lastT,
      lastH,
      soilRaw,
      wet ? 1 : 0,
      rainRaw
    );
  }
}

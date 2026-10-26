/*
  SRMC Review-0 firmware  --  NodeMCU ESP8266 (CP2102)
  Reads: DHT11 (temperature, humidity), soil moisture (analog), rain sensor (digital output)
  Sends one text line per second over USB serial for the MATLAB dashboard:

      SRMC,<millis>,<tempC>,<rhPercent>,<soilRaw>,<rainWet>,<rainRaw>

  soilRaw : raw ADC 0..1023 (NodeMCU A0 accepts 0..3.3 V)   rainWet : 1 = wet, 0 = dry   rainRaw : -1 (ESP8266 has only one ADC)
  tempC / rhPercent are -999 when the DHT11 read failed (MATLAB keeps the last good value).

  Board:  Tools > Board > "NodeMCU 1.0 (ESP-12E Module)"      Serial Monitor / MATLAB baud: 115200
  Wiring: see PIN_MAP.md in the firmware folder.   No external library needed (DHT11 is decoded below).
  NOTE: written without access to the hardware - run the checklist in documents/ before trusting the numbers.
*/
#include <Arduino.h>

// ---------------- pins (NodeMCU labels) ----------------
#define PIN_DHT      D2        // GPIO4   DHT11 data
#define PIN_RAIN_DO  D5        // GPIO14  rain module DO (digital output)
#define PIN_SOIL     A0        //         soil module AO (analog)
#define PIN_LED      LED_BUILTIN   // GPIO2 on-board LED (active LOW) : lit while rain is detected

#define RAIN_ACTIVE_LOW 1      // most rain modules pull DO LOW when wet; set 0 if yours is the opposite
#define SAMPLE_MS       1000   // print period
#define DHT_PERIOD_MS   2000   // DHT11 needs >= 1 s between reads

static float lastT = -999, lastH = -999;
static unsigned long tDht = 0, tPrint = 0;

// Minimal DHT11 decoder (works without any library). Returns true when the checksum is valid.
bool readDHT11(uint8_t pin, float &t, float &h) {
  uint8_t d[5] = {0, 0, 0, 0, 0};
  pinMode(pin, OUTPUT); digitalWrite(pin, LOW); delay(20);        // start signal >= 18 ms
  digitalWrite(pin, HIGH); delayMicroseconds(30);
  pinMode(pin, INPUT_PULLUP);
  noInterrupts();
  bool ok = true;
  if (pulseIn(pin, HIGH, 300) == 0) ok = false;                    // sensor response (80 us high)
  for (int i = 0; ok && i < 40; i++) {
    unsigned long w = pulseIn(pin, HIGH, 300);                     // 26-28 us = bit 0, ~70 us = bit 1
    if (w == 0) { ok = false; break; }
    d[i / 8] <<= 1; if (w > 45) d[i / 8] |= 1;
  }
  interrupts();
  if (!ok) return false;
  if (((d[0] + d[1] + d[2] + d[3]) & 0xFF) != d[4]) return false;  // checksum
  h = d[0] + d[1] * 0.1f;
  t = (d[2] & 0x7F) + (d[3] & 0x0F) * 0.1f; if (d[2] & 0x80) t = -t;
  return true;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RAIN_DO, INPUT);
  pinMode(PIN_LED, OUTPUT); digitalWrite(PIN_LED, HIGH);
  delay(500);
  Serial.println();
  Serial.println("# SRMC firmware v1 board=ESP8266 baud=115200 fields=SRMC,ms,tempC,rh,soilRaw,rainWet,rainRaw");
}

void loop() {
  unsigned long now = millis();
  if (now - tDht >= DHT_PERIOD_MS) {
    tDht = now; float t, h;
    if (readDHT11(PIN_DHT, t, h)) { lastT = t; lastH = h; } else { lastT = -999; lastH = -999; }
  }
  if (now - tPrint >= SAMPLE_MS) {
    tPrint = now;
    long s = 0; for (int i = 0; i < 8; i++) { s += analogRead(PIN_SOIL); delay(2); }   // average 8 reads
    int soilRaw = (int)(s / 8);
    int level = digitalRead(PIN_RAIN_DO);
    int wet = RAIN_ACTIVE_LOW ? (level == LOW) : (level == HIGH);
    digitalWrite(PIN_LED, wet ? LOW : HIGH);
    char buf[96];
    snprintf(buf, sizeof(buf), "SRMC,%lu,%.1f,%.1f,%d,%d,%d", now, lastT, lastH, soilRaw, wet ? 1 : 0, -1);
    Serial.println(buf);
  }
}

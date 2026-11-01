/* ESP32 sketch (Arduino core): reads the six sensors, runs the distilled network every 60 s and drives the winch.
 * NOT FLASHED OR TESTED ON A BOARD (this project is computer-only so far): pins, calibration constants and the winch interface are placeholders to check on the bench.
 * Copy srmc_nn.h and srmc_nn_weights.h (made by train_export.py) into this folder before compiling. */
#include <DHT.h>
#include <time.h>
#include "srmc_nn.h"

#define PIN_DHT 4
#define PIN_SOIL 34          // analog, capacitive probe
#define PIN_RAIN 35          // digital, wet = LOW on most boards (check)
#define PIN_PYRANO 32        // analog from the pyranometer amplifier
#define PIN_PAR 33           // analog from the PAR sensor amplifier
#define PIN_ANEMO 27         // pulse input of the cup anemometer
#define LAT_DEG 9.88f        // site latitude
DHT dht(PIN_DHT, DHT11);
volatile uint32_t pulses = 0; void IRAM_ATTR onPulse() { pulses++; }
float angleNow = 15.0f;

float readGhi()  { return analogRead(PIN_PYRANO) * (1200.0f / 4095.0f); }          // W/m2: CALIBRATE against a reference
float readPar()  { return analogRead(PIN_PAR) * (2400.0f / 4095.0f); }             // umol/m2/s: CALIBRATE
float readSoil() { float raw = analogRead(PIN_SOIL); float pct = 100.0f * (3300.0f - raw) / (3300.0f - 1400.0f); return pct < 0 ? 0 : (pct > 100 ? 100 : pct); }  // dry/wet raw values: CALIBRATE
float readWind(uint32_t ms) { float hz = pulses * 1000.0f / ms; pulses = 0; return hz * 0.875f; }                 // m/s per Hz: from the anemometer datasheet
void moveWinchTo(float deg) { /* TODO: send the target angle to the motor drive; the winch has its own limit switches and angle encoder */ }

void setup() { Serial.begin(115200); dht.begin(); pinMode(PIN_RAIN, INPUT_PULLUP); pinMode(PIN_ANEMO, INPUT_PULLUP); attachInterrupt(PIN_ANEMO, onPulse, FALLING); configTime(19800, 0, "pool.ntp.org"); }

void loop() {
  static uint32_t last = 0; uint32_t now = millis(); if (now - last < 60000) return; uint32_t dt = now - last; last = now;
  struct tm t; if (!getLocalTime(&t)) return;
  float hour = t.tm_hour + t.tm_min / 60.0f;                                   // clock time; the model expects solar time: apply the longitude and equation-of-time correction on the bench
  float T = dht.readTemperature(), RH = dht.readHumidity(); if (isnan(T) || isnan(RH)) { T = 30; RH = 50; }   // simple fallback; the full safety layer is in the JavaScript controller
  float a = srmc_decide(LAT_DEG, t.tm_yday + 1, hour, readGhi(), readPar(), T, RH, readSoil(), digitalRead(PIN_RAIN) == LOW, readWind(dt), angleNow);
  if (fabsf(a - angleNow) >= 1.0f) { angleNow = a; moveWinchTo(angleNow); }
  Serial.printf("tilt %.1f deg\n", angleNow);
}

/*
  SRMC firmware, ESP32 DevKit: six sensors -> serial line for the logger, MATLAB dashboard and digital twin.

  Serial format (115200 baud, one line per second):
    SRMC,ms,tempC,rh,soilRaw,rainWet,rainRaw,ghiWm2,parUmol,windMs

  The first 7 fields are the same as the Review 0 firmware (your pins), so review0_dashboard and the old parser still work.
  NEW fields: ghiWm2 (pyranometer), parUmol (PAR sensor under the canopy), windMs (cup anemometer).

  NOT TESTED ON HARDWARE (written without the board). Check each sensor against a reference and set the calibration numbers below.

  Pins (your Review 0 wiring + three new inputs; all ADC pins are ADC1, so they work with Wi-Fi off or on):
    DHT11 data  GPIO32      soil AO GPIO35      rain AO GPIO34      rain DO GPIO27
    pyranometer GPIO36 (VP)  PAR sensor GPIO39 (VN)  anemometer pulse GPIO25
  Pyranometer and PAR sensors give a small voltage (mV). Use an amplifier or an ADS1115 for good accuracy; the ESP32 ADC is non-linear below 0.15 V.
*/
#include <Arduino.h>
#include <DHT.h>

#define PIN_DHT      32
#define PIN_SOIL     35
#define PIN_RAIN_AO  34
#define PIN_RAIN_DO  27
#define PIN_PYR      36
#define PIN_PAR      39
#define PIN_ANEMO    25
#define PIN_LED       2

#define DHT_TYPE DHT11
#define RAIN_ACTIVE_LOW true          // most rain modules give LOW when wet

// ---------------- calibration: SET THESE FROM YOUR SENSOR DATASHEETS ----------------
const float ADC_VREF        = 3.3;    // volts at full scale (ADC_11db)
const float PYR_W_PER_VOLT  = 1000.0; // pyranometer sensitivity: W/m2 per volt after the amplifier (example: 1 V = 1000 W/m2)
const float PYR_OFFSET_V    = 0.0;    // volts at darkness
const float PAR_UMOL_PER_V  = 1000.0; // PAR sensor: umol/m2/s per volt after the amplifier
const float PAR_OFFSET_V    = 0.0;
const float ANEMO_MS_PER_HZ = 0.667;  // cup anemometer: m/s per pulse per second (reed type 2.4 km/h per Hz = 0.667 m/s)
// -------------------------------------------------------------------------------------

#define SAMPLE_MS     1000
#define DHT_PERIOD_MS 2000

DHT dht(PIN_DHT, DHT_TYPE);
float lastT = -999.0, lastH = -999.0;
unsigned long lastDHT = 0, lastPrint = 0;
volatile unsigned long pulses = 0, lastPulseUs = 0;

void IRAM_ATTR onPulse() {
  unsigned long now = micros();
  if (now - lastPulseUs > 2000) { pulses++; lastPulseUs = now; }   // 2 ms debounce
}

int readAverage(int pin) {
  long total = 0;
  for (int i = 0; i < 16; i++) { total += analogRead(pin); delay(2); }
  return total / 16;
}

float volts(int raw) { return raw * ADC_VREF / 4095.0; }

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  pinMode(PIN_RAIN_DO, INPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_ANEMO, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ANEMO), onPulse, FALLING);
  dht.begin();
  delay(1000);
  Serial.println("# SRMC firmware ESP32 six sensors baud=115200 fields=SRMC,ms,tempC,rh,soilRaw,rainWet,rainRaw,ghiWm2,parUmol,windMs");
}

void loop() {
  unsigned long now = millis();

  if (now - lastDHT >= DHT_PERIOD_MS) {
    lastDHT = now;
    float t = dht.readTemperature(), h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) { lastT = t; lastH = h; } else { lastT = -999.0; lastH = -999.0; }
  }

  if (now - lastPrint >= SAMPLE_MS) {
    unsigned long dtMs = now - lastPrint; lastPrint = now;
    int soilRaw = readAverage(PIN_SOIL);
    int rainRaw = readAverage(PIN_RAIN_AO);
    bool wet = RAIN_ACTIVE_LOW ? (digitalRead(PIN_RAIN_DO) == LOW) : (digitalRead(PIN_RAIN_DO) == HIGH);
    digitalWrite(PIN_LED, wet ? HIGH : LOW);

    float ghi = (volts(readAverage(PIN_PYR)) - PYR_OFFSET_V) * PYR_W_PER_VOLT;       if (ghi < 0) ghi = 0;
    float par = (volts(readAverage(PIN_PAR)) - PAR_OFFSET_V) * PAR_UMOL_PER_V;       if (par < 0) par = 0;
    noInterrupts(); unsigned long p = pulses; pulses = 0; interrupts();
    float wind = (p * 1000.0 / (float)dtMs) * ANEMO_MS_PER_HZ;

    Serial.printf("SRMC,%lu,%.1f,%.1f,%d,%d,%d,%.1f,%.1f,%.1f\n", now, lastT, lastH, soilRaw, wet ? 1 : 0, rainRaw, ghi, par, wind);
  }
}

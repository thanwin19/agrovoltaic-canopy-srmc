/* SRMC distilled six-sensor tilt controller: portable C (no malloc, no libraries beyond math.h), runs on an ESP32 or on a PC.
 * The network was trained to copy the angle search of the full controller (train_export.py); weights are in srmc_nn_weights.h.
 * Inputs: clock (day of year, solar hour), latitude, and the readings of the six sensors.  Output: tilt angle in degrees, 0.5 deg steps.
 * Rules of the full controller that do not need the network stay as plain code: storm stow, rain flat, night park. */
#ifndef SRMC_NN_H
#define SRMC_NN_H
#include <math.h>
#include "srmc_nn_weights.h"

#define SRMC_PI 3.14159265358979f
#define SRMC_LO 15.0f
#define SRMC_HI 60.0f

static inline float srmc_declination_deg(int doy) { return 23.45f * sinf(SRMC_PI / 180.0f * 360.0f / 365.0f * (284.0f + (float)doy)); }

/* sun height term sz and east term sx, same formulas as the digital twin */
static inline void srmc_sun(float lat_deg, int doy, float hour, float *sz, float *sx) {
  float d = srmc_declination_deg(doy) * SRMC_PI / 180.0f, ph = lat_deg * SRMC_PI / 180.0f, w = 15.0f * (hour - 12.0f) * SRMC_PI / 180.0f;
  *sz = sinf(ph) * sinf(d) + cosf(ph) * cosf(d) * cosf(w);
  *sx = -cosf(d) * sinf(w);
}

/* network on the 10 raw features: sz, sx, kt, T, RH, soil, lsr, prev, sin_doy, cos_doy */
static inline float srmc_nn_raw(const float f[SRMC_NF]) {
  float x[SRMC_NF], h1[SRMC_H], h2[SRMC_H], out;
  for (int i = 0; i < SRMC_NF; i++) x[i] = (f[i] - SRMC_MU[i]) / SRMC_SD[i];
  for (int j = 0; j < SRMC_H; j++) { float s = SRMC_B1[j]; for (int i = 0; i < SRMC_NF; i++) s += SRMC_W1[j * SRMC_NF + i] * x[i]; h1[j] = tanhf(s); }
  for (int j = 0; j < SRMC_H; j++) { float s = SRMC_B2[j]; for (int i = 0; i < SRMC_H; i++) s += SRMC_W2[j * SRMC_H + i] * h1[i]; h2[j] = tanhf(s); }
  out = SRMC_B3[0]; for (int i = 0; i < SRMC_H; i++) out += SRMC_W3[i] * h2[i];
  return out;
}

static inline float srmc_round_angle(float net_out) {
  float a = floorf((net_out * 22.5f + 37.5f) * 2.0f + 0.5f) / 2.0f;
  return a < SRMC_LO ? SRMC_LO : (a > SRMC_HI ? SRMC_HI : a);
}

/* angle from the 10 raw features (used by the test program) */
static inline float srmc_nn_angle_from_features(const float f[SRMC_NF]) { return srmc_round_angle(srmc_nn_raw(f)); }

/* full decision from sensor readings. prev_deg = angle now in use. rain = 1 when the rain sensor is wet. wind in m/s. par_umol = PAR under the panels (umol/m2/s). */
static inline float srmc_decide(float lat_deg, int doy, float hour, float ghi, float par_umol, float T, float RH, float soil, int rain, float wind, float prev_deg) {
  float sz, sx; srmc_sun(lat_deg, doy, hour, &sz, &sx);
  if (wind >= 15.0f || (prev_deg >= 90.0f && wind >= 12.0f)) return 90.0f;           /* storm stow, resume below 12 m/s */
  if (rain) return 3.0f;                                                              /* flat roof to the gutter */
  if (ghi < 20.0f || sz < 0.02f) return SRMC_LO;                                      /* night park */
  float g0 = 1361.0f * (1.0f + 0.033f * cosf(2.0f * SRMC_PI * (float)doy / 365.0f)), kt = ghi / (g0 * sz);
  float lsr = par_umol / 2.05f / (ghi > 1.0f ? ghi : 1.0f);
  float f[SRMC_NF] = { sz, sx, kt, T, RH, soil, lsr, prev_deg, sinf(2.0f * SRMC_PI * (float)doy / 365.0f), cosf(2.0f * SRMC_PI * (float)doy / 365.0f) };
  return srmc_nn_angle_from_features(f);
}
#endif

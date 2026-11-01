/* Check that the C network gives the same angles as the Python model on test vectors:  see run_c_check.py */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "srmc_nn.h"
int main(int argc, char **argv) {
  const char *fn = argc > 1 ? argv[1] : "test_vectors.csv"; FILE *fp = fopen(fn, "r"); char line[512]; int n = 0, bad = 0, off = 0; double maxd = 0;
  if (!fp) { printf("cannot open %s\n", fn); return 2; }
  fgets(line, sizeof line, fp);
  while (fgets(line, sizeof line, fp)) {
    float f[SRMC_NF], py; char *p = line;
    for (int i = 0; i < SRMC_NF; i++) { f[i] = strtof(p, &p); if (*p == ',') p++; }
    py = strtof(p, &p); float a = srmc_nn_angle_from_features(f);
    double d = fabs((double)a - (double)py); if (d > maxd) maxd = d; if (d > 0.0) bad++; if (d > 0.5) off++; n++;
  }
  fclose(fp);
  printf("%d vectors, %d differ, %d differ by more than 0.5 deg, largest difference %.1f deg\n", n, bad, off, maxd);
  /* decision rules */
  printf("rules: stow=%.1f rain=%.1f night=%.1f resume_hold=%.1f day=%.1f\n",
         srmc_decide(9.88f, 105, 12.5f, 800, 300, 30, 50, 25, 0, 16, 40),
         srmc_decide(9.88f, 105, 12.5f, 300, 100, 30, 90, 25, 1, 3, 40),
         srmc_decide(9.88f, 105, 2.5f, 0, 0, 25, 70, 25, 0, 2, 40),
         srmc_decide(9.88f, 105, 12.5f, 800, 300, 30, 50, 25, 0, 13, 90),
         srmc_decide(9.88f, 105, 12.5f, 800, 300, 30, 50, 25, 0, 3, 40));
  return off ? 1 : 0;
}

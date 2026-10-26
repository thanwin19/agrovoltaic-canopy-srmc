# Live digital twin

Open `SRMC_Digital_Twin.html` in Chrome or Edge (works offline; no server needed). Tabs: 3D twin (sensor card, HUD with soil probe, irrigation and cistern), Sun and light, Mechanism (offset lever arm, storm stow), Tilt trade-off, Rain and water (water link), Crops and soil, Economics, Accuracy (with a live test), Method.

URL parameters for demos: `?tab=acc&day=106&hour=9.5` (tab names: twin, light, mech, tilt, water, crops, eco, acc, method).

The `screens` folder holds a screenshot of every tab (taken from this file with headless Chrome; the 3D views use software WebGL, which gives the same picture as a graphics card but may look slightly softer). All sensor values in the twin are simulated; the optional Connect-board button reads a real ESP board.

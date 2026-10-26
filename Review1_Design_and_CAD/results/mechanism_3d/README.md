# 3D tilt mechanism: how it works

**Open `SRMC_Mechanism_3D.html`** in Chrome or Edge (works offline, no install). Or watch `SRMC_Mechanism_Animation.mp4` (about one minute, narrated with on-screen captions).

## What it shows (real scale, metres, final strength-checked design)
Sensors, then controller, then 0.25 kW motor and self-locking worm gearbox, then the 120 mm drum, then one closed-loop 6 mm stainless drive wire over sheaves, then the 0.44 m lever arm (fixed at 45 deg) on every torque tube, then the 114 x 4 mm tube turning in bearing rings on the 16 mm carrier rope, then all panel rows tilting together. Also the columns, stays and anchors, the weather mast (pyranometer, rain sensor, cup anemometer), the PAR / DHT11 / soil probe stake, and the gutter and cistern.

## How to use it
- Drag to turn, scroll to zoom, right-drag (or Shift-drag) to move.
- **Tilt slider**: move the panels yourself and watch the wire, the lever arm and the drum turn. The panel on the right reads out tilt, wire moved (mm), drum turns, and how much of the sun hits the panel.
- **Weather buttons** (Night, Morning, Noon, Hot dry, Rain, Storm) set the angle the controller would choose; **Play a day** runs them all.
- **Camera buttons** jump to the motor and drum, the wire and arms, one lever arm, the rope bearing, a side section, a top view and the sensors. Click a numbered circle (or press the arrow keys) to step through the 11 steps.
- **See-through panels** shows the tube, arms and rails under the panels.
- Link parameters for screenshots: `?view=winch&tilt=40&ui=0&lab=0` (views: overview, winch, tips, arm, bearing, side, top, sensors, ground).

## Numbers it reproduces
Wire travel d = 0.44 x [sin 45 + sin(angle - 45)] minus the value at the flat 3 deg: 408 mm at 60 deg and 606 mm at the 90 deg stow; drum turns 1.08 to 60 deg and 1.61 to 90 deg. These match the Mechanism tab of the digital twin and the strength check.

## Honest limits
- It is a design model, not a photograph of a built system. Wires and ropes are drawn about four times thicker so they are visible.
- Animation is far faster than the real winch (a full sweep would take minutes).
- The weather angles are examples of what the controller chooses; the controller itself is in Review 4.
- Anchors, foundations, bearing rings, sheave sizes and the closed-loop drive layout need a supplier and a structural engineer before building.

Rebuild: `code_reference/build_mechanism_3d.py` (needs only Python). Video: `code_reference/make_mechanism_video.py` (needs Chrome, ffmpeg and a web server on port 8766).

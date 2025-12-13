# 3D-Printer Motion Programming System (Prusa I3 MK3S)

**Purpose:** repurpose a Prusa I3 MK3S as a deterministic 3-axis motion platform for research (raster scans, sensor sweeps, motion-control experiments).  
**Alex Zheng / PhD Silas Ifyeani:** [PI Kevin Musselman] — Research code for motion experiments and metrology.

---

![me](https://github.com/al3xzheng/MultiSpectral-Thin-Film-Imaging-Interface/blob/main/WIN_GANTRY_SAMPLES___SILICON_WAFER_AND_PLA.gif)
![me](https://github.com/al3xzheng/MultiSpectral-Thin-Film-Imaging-Interface/blob/main/WINGANTRYCOMPILEDHD8k.gif)

## Quick summary

This repository contains:

- A **PySide6 GUI** that collects motion parameters and generates G-code.
- A **GCodePlaceholders** backend that writes motion-only G-code files.
- A **raster G-code template** (raster_gcode_template.py) for X/Y raster and oscillatory scan patterns.
- A **SerialWorker** demo that listens for `M118 START` / `M118 END` messages for timing/synchronization.

**Important:** This software bypasses the printer's normal homing and self-checks. Use only on modified hardware that you control. You accept responsibility for safety.

---

## Hardware & Software Requirements

- Prusa I3 MK3S (Einsy RAMBo)
- Computer with USB-A port
- USB-A → USB-B cable
- [Pronterface (Printrun) 2.2.0](https://github.com/kliment/Printrun/releases/tag/printrun-2.2.0)
- Python 3.8+ virtual environment
  - `pip install -r requirements.txt` (includes PySide6, pyserial)

---

## How it works (high level)

1. Launch the Python UI.
2. Select scan **mode** (1..4) and enter motion parameters:
   - `X_initial`, `Y_initial`, `Z_initial` (mm)
   - `ΔX`, `ΔY`, `ΔZ` increments (mm)
   - `XBound`, `YBound`, `ZBound` safe ranges (mm)
   - `Speed` (F value), `Acceleration` (M204), `Jerk` (M205)
   - `n_x`, `n_y` (discretization placeholders)
3. Click **Confirm Parameters**, then **Generate G-code**.
4. Open **Pronterface**, connect to the printer, load the generated file, and **Print**/stream.
5. Optional: use serial messages (`M118 START` / `M118 END`) to synchronize external DAQ.

---

## G-code policy / constraints

- **Only movement commands are used.** No extrusion or heating commands.
- Always uses **absolute positioning (G90)**.
- Uses `M205` and `M204` to set jerk and acceleration.
- The output file: `3d-printer_scan_pattern_output.txt`.

---

## Safety & best practices

- Validate bounds before printing. Never exceed the printer's mechanical travel limits.
- Start with low speeds and acceleration to confirm expected motion.
- Use Pronterface to preview and step through commands before streaming the full file.
- Keep emergency power-off and physical access to axes while testing.

---

## Example quick CLI

```bash
python raster_gcode_template.py 1 50 50 0 100 -20 0 200 200 150 12000 700 4 3 3
# mode=1, Xinit=50, Yinit=50, Zinit=0, dx=100, dy=-20, dz=0,
# Xbound=200, Ybound=200, Zbound=150, feed=12000, accel=700, jerk=4, nx=3, ny=3

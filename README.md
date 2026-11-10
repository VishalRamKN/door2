# door2: motorised bottle-drop door

A two-leaf rack-and-pinion door that opens and closes a Ø120 bottle hole in a steel sheet. It uses an
ESP32 38-pin DevKit, 2 × MG995 360° servos (one per leaf) and 4 × KW11 limit switches.

The door is assembled. This repo is for the wiring and firmware work.

## Start here

Watch **[out/door2_wiring_firmware.mp4](out/door2_wiring_firmware.mp4)** (7:48, no sound, pause on any
diagram). Chapters are in [out/door2_wiring_firmware_chapters.txt](out/door2_wiring_firmware_chapters.txt).

Follow this order: wire, check with a multimeter, flash with the servo supply off, `?`, `n`, jog, `o` / `c`, tune.

## Status

| | |
|---|---|
| Sketch | [firmware/door2/door2.ino](firmware/door2/door2.ino) compiles on ESP32 Arduino core 2.0.17. No extra libraries |
| Servo direction | Confirmed by jog test on 2026-11-06: `L+` closes, `R+` opens. These match the defaults |
| Full open and close | **Not yet logged on this firmware.** Treat the first run as a test |

## Flash

PlatformIO, from the `firmware` folder:

```bash
pio run -t upload -t monitor
```

Arduino IDE: install **esp32 by Espressif, version 2.0.17**, open `firmware/door2/door2.ino`, select
**ESP32 Dev Module** and your port, then upload. Keep the servo supply off while flashing.

Serial Monitor: **115200 baud, line ending Newline**. Without Newline, commands are ignored.

## Pins

Full rules and the board layout are in [firmware/WIRING.md](firmware/WIRING.md).

| Connection | ESP32 |
|---|---|
| Left servo signal (orange) | GPIO18 |
| Right servo signal (orange) | GPIO19 |
| Left OPEN switch, NC | GPIO32 |
| Left CLOSED switch, NC | GPIO33 |
| Right OPEN switch, NC | GPIO25 |
| Right CLOSED switch, NC | GPIO26 |
| Push button (optional, other leg to GND) | GPIO27 |
| COM of all 4 switches | GND |
| Servo supply minus (common ground) | GND |

Servo power is a separate 5–6 V supply, at least 3 A, with 1000 µF across the rails. It must never come from the
ESP32's 5V or 3V3 pin.

**Left** is the end that hangs on the tongues. **Right** is the end with the 2 M4 bolts. Turned over, they can swap
sides on the bench, so go by tongues and bolts.

## Serial commands

| Command | Action |
|---|---|
| `o` / `c` | Open / close both leaves |
| `s` | Stop |
| `?` | Status and command list |
| `r` | Clear a fault |
| `L+` `L-` `R+` `R-` | Short jog of one servo. **Ignores the switches** |
| `n` | Stop pulse for 10 s, to check for creep |

## First-run warning

The comment at the top of `door2.ino` says to leave the pinions off the racks. The door is already assembled, so
instead **only jog away from a pressed switch**. From closed, use `L-` and `R+`. From open, use `L+` and `R-`.

## Adding your own logic

Call `startMove(OPENING)`, `startMove(CLOSING)` and `stopAll()`. Read `state`, `L.swOpen.state`, `R.swClosed.state`
and so on. The video has a worked example.

- No `delay()` or waiting loops. The switches are read in `loop()`, so a blocked loop lets a leaf run into its stop.
- Keep the switch stops and the timeout. A stalled MG995 is about as strong as a printed PLA gear tooth.
- Do not clear FAULT in code. A person checks the door and sends `r`.

## What else is here

| Path | What |
|---|---|
| `PROJECT.md` | Full design reference: geometry, parts, control logic |
| `NOTES.md` | Dated history of decisions and fixes |
| `out/door2_how_it_works.mp4` | How the mechanism works (62 s) |
| `out/door2_assembly.mp4` | How it was built (2:32) |
| `out/renders/`, `out/stl/`, `out/step/`, `out/door2.FCStd` | Pictures and CAD exports |
| `model.py` | Parametric CAD source. Reference only: it needs the CadKit library from the main CAD workspace |

# door2 wiring: ESP32 38-pin DevKit + 2 × MG995 360° + 4 × KW11

```
                 SERVO SUPPLY 5–6 V, ≥ 3 A
                  (+)                 (–)
                   │                   │
                   ├── 1000 µF ────────┤        (electrolytic, + to +, close to the servos)
                   │                   │
   MG995 LEFT  red ┤             brown ┼──────────────┐
   MG995 RIGHT red ┘             brown ┤              │   COMMON GROUND
                                       │              │   (supply – to ESP32 GND: required)
   MG995 LEFT  orange (signal) ──────────────────── GPIO18
   MG995 RIGHT orange (signal) ──────────────────── GPIO19
                                                      │
                                               ESP32 GND ──┬── COM of all 4 KW11
                                                           └── push button (optional)

   KW11 left  OPEN   (left end wall)     NC ── GPIO32
   KW11 left  CLOSED (back rail, left)   NC ── GPIO33
   KW11 right OPEN   (right end wall)    NC ── GPIO25
   KW11 right CLOSED (back rail, right)  NC ── GPIO26
   push button (optional)                   ── GPIO27   (other leg to GND)

   ESP32 power: USB, or a 5 V supply on the 5V/VIN pin. Not from the servo rail unless it is a clean 5 V.
```

## 38-pin board: where the pins are

With the USB port at the bottom, antenna at the top:

| Left header (top → bottom) | used | Right header (top → bottom) | used |
|---|---|---|---|
| 3V3, EN, VP, VN, 34, 35 | — | GND | GND |
| **32** | L open sw | 23, 22, TX, RX, 21, GND | — |
| **33** | L closed sw | **19** | R servo |
| **25** | R open sw | **18** | L servo |
| **26** | R closed sw | 5, 17, 16, 4, 0, 2, 15… | (2 = on-board LED) |
| **27** | button | | |
| 14, 12, **GND** | GND | | |

Board layouts vary. Check the silkscreen labels, not the position.

## Rules

1. **Servo power never comes from the ESP32's 5 V / 3V3 pin.** One MG995 can draw over 1 A at stall,
   so two can brown out the ESP32 (it resets mid-move).
2. **Servo supply 4.8–7.2 V.** If your supply is 12 V, put a buck converter set to 6 V (≥ 3 A) in
   between, or the servos burn out.
3. **Common ground:** the supply's (–) must be wired to an ESP32 GND, or the signal does nothing.
4. **The switches use the NC contact** (COM to GND, NC to the GPIO). Pressed reads HIGH, free reads
   LOW. A broken or unplugged switch wire then reads "pressed", so that leaf won't move instead
   of crashing into the stop. Find NC with a multimeter: it beeps to COM when the lever is *free*.
   (If you wire NO instead, set `SW_USE_NC = false`. A broken wire then goes unnoticed and only the
   timeout stops the servo.)
5. The switch wires run beside the servo leads, so they can pick up motor noise. The code debounces,
   but if a leaf stops early at random, add a **10 kΩ pull-up (GPIO → 3V3)** and **100 nF (GPIO → GND)**
   at the ESP32 for each switch. Twisting each switch's two wires together also helps.
6. Do not use GPIO 34–39 for switches (no internal pull-up) or 0/2/12/15 (boot strapping pins).
7. 3.3 V signal into the MG995 normally works. If a servo jitters or ignores commands, add a 74HCT125
   or a 1-transistor level shifter to 5 V.

## MG995 lead colours

brown = GND, red = +V, orange = signal.

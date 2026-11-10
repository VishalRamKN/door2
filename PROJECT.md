# door2: bottle-drop door (rack & pinion) — START HERE

Motorised bi-parting door that opens and closes the Ø120 bottle-drop hole in an MS-steel
sheet of a bigger machine. Rework of the user's FreeCAD design "2nd dorr.FCStd".
Everything fits in the **30 mm directly under the sheet**.

`NOTES.md` is the dated history (what the original was, every decision and fix, in order).
This file is the current state.

---

## 1. Status (2026-11-01)

| | |
|---|---|
| CAD | Done. `cad check door2` → **CHECK PASSED**, incl. assembly checks (every screw reachable, every part can get in, mount holds) |
| G-code | Sliced 2026-11-01, black PLA, 6 plates, ≈ 13 h 35, ≈ 330 g (`out/gcode/`) |
| Printed | Plate 1 (2026-11-01): spline fit, mesh, coupon, switch click all OK; some stringing |
| Next step | Plate 1 printed + all tests passed (2026-11-01). Print plate 2, then 3, 4, 5, 6 (re-sliced: black 215 °C against stringing) |
| Videos | `out/door2_how_it_works.mp4` (62 s), `out/door2_assembly.mp4` (2:32, build reference: buy list, print order, 11 steps each ending on a checklist; chapters in `out/door2_assembly_chapters.txt`) |
| Editable FreeCAD | `out/door2.FCStd` (same coordinates as the original, overlays it) |
| Hand-over video | `out/door2_wiring_firmware.mp4` (7:48, 1080p, silent: wiring, flashing, bring-up, code walk-through, faults; chapters in `out/door2_wiring_firmware_chapters.txt`). Build: `uv run python projects/door2/video/wiring_anim.py`, `python3 projects/door2/video/extract_fw_code.py`, then `npm run render:firmware` in `video/` |
| Firmware | `firmware/door2/door2.ino` (ESP32 38-pin, compiles on core 2.0.17) + `firmware/WIRING.md`. Not yet run on the hardware (2026-11-06) |

Open items: switch trip point, MG995 dims, spline press fit, printed gear mesh, epoxy on the
steel (see §10). 2026-10-25: mounting redesigned (own brackets, removable unit) and an assembly
audit fixed the servo tab screws and the switch screws (NOTES.md).

---

## 2. Quick commands (run from `~/VSDocs/CadProjects`)

```bash
uv run cad all door2        # build STL/STEP + checks + renders (out/)
uv run cad check door2      # just the checks
uv run cad slice door2      # G-code for the Kobra 2 Neo (out/gcode/), uses PLATES in model.py
uv run cad freecad door2    # out/door2.FCStd
# videos (after model changes): re-render frames, then Remotion
uv run python projects/door2/video/anim.py            # how-it-works frames
uv run python projects/door2/video/assembly_anim.py   # assembly frames
cd projects/door2/video && npm run render && npm run render:assembly
npm run studio                                        # live editor for captions/timing
```

---

## 3. Requirements (from the user)

- Open/close the Ø120 hole with a rack-and-pinion mechanism (the user's concept).
- Workspace: **z −30 … 0 under the sheet**, inside the sheet's footprint. Nothing below or outside.
- Actuators: **2 × MG995 continuous-rotation (360°) servos**, one per leaf.
- Leaves open outward to an **end limit switch** each; close together on command.
- Limit switches: **KW11 hinge-lever micro switches** (16 A, the user's photos).
- Mounting: no screws into the sheet; brackets are **epoxied** to the steel (user, 2026-10-25).
  Nothing past the sheet edge. The **left end (15 mm to the edge) can't be reached** once mounted;
  the right end can. There is no existing adjacent part: the brackets are designed here.
- The hole drops bottles: when open, nothing may be in the drop path.

---

## 4. How it works

- **Frame** (fixed, two printed halves joined at the hole centre) hangs under the sheet. Its
  front and back rails have 45° **shelves**; the front floor carries two **racks** (teeth up).
- **Leaves** (2, mirror images) are 3.4 mm plates whose edges rest on the shelves. Screwed-on
  **retainer strips** above the edges stop them lifting (0.5 mm max), so the gears can't skip.
- Each leaf carries its **MG995** (lying on its side, shaft toward the front) with an
  **8 mm, 18-tooth pinion** on the spline. The servo turns → the pinion walks along the fixed
  rack → the leaf slides. 69 mm travel ≈ 1.22 pinion turns.
- **Closed:** leaves meet at the hole centre with a 45° bevelled seam (2.8 mm overlap, 0.42 mm
  gap) and overlap the hole edge by 5.5 mm each side.
- **Open:** leaves sit fully outside the hole (≥ 3 mm clear of the hole edge).
- **Switches (4):**
  - *Open* (one per end wall, the user's original position): a pad on the leaf's outer wall
    presses only the lever tip, **1.8 mm** at full open. The switch pedestal is the hard stop
    at **2.5 mm** press. The wall is set back 2.5 mm beside the pad so it never touches the
    lever's pivot end or the plunger.
  - *Closed* (one per leaf, on the back rail, lever toward the hole): a 45° cam on the leaf
    presses it **1.8 mm** at full close. The leaves themselves are the hard stop.
  - All switch screw holes are **slots, ±1.5 mm**, to tune the trip point. The nuts sit in a
    printed **nut bar** on top of each switch, so the screws can be turned from below when mounted.
- **Mounting** (4 printed brackets, epoxied to the sheet; the unit itself comes off):
  - *Left end* (15 mm to the sheet edge, unreachable): each bracket has a 14 × 8 tongue that goes
    through a window in the end wall; the wall hangs on it. No fasteners.
  - *Right end* (reachable): a flange on the frame bottom sits under each bracket; M4 × 16 from
    below into a nut slid into the bracket.
  - On/off: lift the unit 10 mm right of its place, slide left onto the tongues, 2 × M4. Off is
    the reverse. The check sweeps this path and proves the frame is held (down, sideways, up).

---

## 5. Coordinates and key numbers

World = the original FCStd's frame: **X** along the travel, **Y** across, **Z = 0 is the sheet
underside**, workspace z −30…0. In `model.py` geometry is written in **u = x − XC**
(u = 0 is the hole centre and the seam); the design is mirror-symmetric about u = 0.
Right leaf u > 0, closes toward −u. **Front = −Y** (racks, servos), **back = +Y** (closed switches).

| What | Value |
|---|---|
| Sheet | 370 × 200 × 1.7 MS, centred on x = 0 |
| Hole | Ø120 at (x −22.96, y 10) → `XC = -22.96`, `HOLE_Y = 10` |
| Frame | u ±147 (end walls 5 mm), y ±100, z −30…0; each half 152.5 × 200 |
| Space to sheet edge | **left end 15 mm**, right end 61 mm (frame is off-centre) |
| Leaf plate | z −6.9…−3.5 (3.4 mm), y ±90.5; rests on shelf z −7, retainer underside z −3 |
| Leaf travel `T` | 68.98 mm (derived from the end-switch lever, see §7) |
| Servo shaft | z −15.75, y −52.5 (spline end); case centre u 32 (closed) |
| Gears | module 1, 20°, z = 18 (pitch Ø18), face 8, backlash 0.10, centre distance 9.000 |
| Rack | u 31…122, y −61.5…−52.3, on the floor at z −28, 2 pegs Ø2.8 |
| Mounting | brackets at y −70 and 60, 32 wide. Left: u −161.5…−147.3, tongue z −14…−6, 9 mm engaged. Right: u 157.5…174, flange z −30…−22 to u 175, M4 at u 165.75 |
| Wire notches | 6.5 × 10.5, open at the bottom, end walls at y ±92 |

---

## 6. Parts

### Printed (`out/stl`, `out/step`, print orientation)

| Part | Qty | Plate | Notes |
|---|---|---|---|
| frame_right / frame_left | 1 + 1 | 2, 3 | 3 walls, 20 % (screws self-tap into it); right has the bolt flanges, left the tongue windows |
| leaf_right / leaf_left | 1 + 1 | 4 | printed plate-down (flipped); 3 walls |
| pinion | 2 | 1 + 5 | 0.16 mm layers; bore Ø5.7 press on spline + M3 centre screw |
| rack | 2 | 1 + 5 | 0.16 mm layers, flat, teeth up |
| retainer_end | 4 | 5 | identical at all four corners |
| retainer_mid | 2 | 5 | spans the frame joint (front + back) |
| splice | 2 | 5 | joins the frame halves on the floor (front + back) |
| bracket_left | 2 | 6 | printed on its outer face (tongue up, no overhang) |
| bracket_right | 2 | 6 | glue face on the bed |
| nut_bar | 4 | 6 | one per switch, skin on the bed |

| Plate | Time | Filament |
|---|---|---|
| 1_test_pinion_rack | 46 min | 7.8 g |
| 2_frame_right | 3 h 45 | 96.7 g |
| 3_frame_left | 3 h 26 | 89.1 g |
| 4_leaves | 2 h 55 | 84.2 g |
| 5_small_parts | 2 h 00 | 28.0 g |
| 6_mount_parts | 1 h 03 | 24.9 g |

### Bought

| Item | Qty | Source of dimensions |
|---|---|---|
| MG995 360° servo | 2 | user's MG996 model in the FCStd (same case) → `components/step/mg995_servo.step`, VERIFY |
| KW11 hinge-lever switch | 4 | body from the FCStd; **lever, plunger and holes measured from the user's photo** → `cadkit.components.KW11` |
| M3 × 8 countersunk | 8 | splices |
| M3 × 10 countersunk | 20 | retainers (flush: this face sits against the steel) |
| M3 × 20 socket head + nut | 4 + 4 | end switches, from below (exact length: ends flush with the nut bar) |
| M3 × 16 socket head + nut | 4 + 4 | closed switches (M3 × 20 here hits the leaf) |
| M3 × 8 self-tapping pan head + Ø7 washer | 8 | servo tabs, from the shaft side (washer: tab holes are Ø4.6) |
| M3 × 8 button head | 2 | pinion centre screws (head must fit the 1.8 mm counterbore) |
| M4 × 16 socket head + nut | 2 + 2 | right-end brackets |
| 2-part epoxy | | brackets to the sheet (sand + degrease the steel); optional drop of CA under the racks |

---

## 7. Why it is the way it is (decisions)

| Original flaw | Fix |
|---|---|
| Leaves hung on the pinion / servo shaft | Plate edges rest on shelves in both rails |
| No guide: tilt, pinion could lift out of mesh | Retainer strips trap the edges (0.5 mm lift max) |
| Left leaf had no pinion, its servo clashed with the leaf | Both leaves identical (mirror), each with servo + pinion + rack |
| Back rack unused | Removed; back rail carries the closed switches |
| 37 mm pinion cantilevered off the spline | 8 mm pinion at the spline |
| Zero overlap closed | 5.5 mm overlap at the hole edges, 45° bevel seam |
| 0 mm clearances everywhere | 0.1–0.5 mm, checked by sweeps |
| Frame 305 mm long, too big for the bed | Two halves + splices + middle retainers |
| (found later) KW11 lever in the file was 9.7 mm tall; real one is 3.8 mm | Travel 64 → 69 mm, striker pad + recess, cam re-derived, holes re-centred |
| (review) no wire exit | Bottom-open notches in the end walls at y ±92 |
| (review) open leaf 0.4 mm from the bolt heads | (superseded 2026-10-25: no bolts inside the frame any more) |
| (audit 2026-10-25) placeholder M10 blocks: front bolts sealed in once mounted, nut slot in the glue face, CA in peel | Own brackets: left tongues through wall windows, right M4 from below; unit removable |
| (audit) upper servo tab screws unreachable (inner rib, back beam), head clashed with the rib | Bulkhead moved behind the tabs; screws from the shaft side; driver channel under the inner rib + front beam |
| (audit) "M3 × 16–20" switch screws: × 20 hits the leaf at the closed switch; nut on top unreachable once mounted | Exact lengths; nut bars hold the nuts |
| (audit) fasteners were never in the checks | All screws/nuts modelled (`leaf_hw`, `switch_hw`, `mount_hw`) and swept; tool-access + insertion-path checks |

Other choices:
- Servos ride on the leaves (the user's concept) rather than fixed to the frame: fixed servos
  didn't fit the 30 mm budget with a captive guide. Cost: servo leads move 69 mm (they slide through the end-wall holes).
- Racks and pinions are separate small parts so a bad mesh means a 30-min reprint, not a frame.
- Retainers are separate because the leaves drop in from above and overhanging lips can't be
  printed on the frame without supports.

---

## 8. Switch geometry and control logic

KW11 (measured from the photo, scale = 28 mm body): holes Ø3 at **22.6 × 10.3** (diagonal,
2.7 mm from the edges); lever pivot 11.4 mm, tip 25.6 mm from the terminal end; **lever tip
free height 3.8 mm**; red plunger at 22.6 mm, 3.1 mm tall. The STEP lever (9.7 mm) is wrong for
this switch. Trip point assumed ~1 mm of lever-tip travel (**VERIFY**).

Control (firmware, any MCU):
- OPEN: run both servos outward until each one's end switch trips, then stop that servo.
- CLOSE: run both inward until each one's closed switch trips. If a seam gap remains, run
  ~0.1 s more or move the closed switches in their slots.
- **Always** also stop each move on a timeout (~2 s; a move takes ~1.2 s at ~60 rpm).
- Never run with the switches unplugged. A stalled MG995 (~10 kg·cm, ~110 N at the pinion)
  is about the strength limit of a PLA m1 tooth. If a pinion strips, print it in PETG.

---

## 9. Assembly and mounting (matches the assembly video)

Everything up to step 8 on the bench. The retainer and splice screws can't be reached later.

1. Join the frame halves; splice plates front + back (8 × M3×8 countersunk).
2. Racks onto their pegs (teeth up).
3. Switches: end switches through the end-wall notch, closed switches on the back pedestals;
   nut bar (nuts in its pockets) on top, M3 from below through the slots, finger-tight. Solder wires first.
4. Leaf upside down: servo drops in between the bulkhead pillars; 4 × M3×8 self-tapping + washers from the
   shaft side (the upper two go along the channel under the rib); press the pinion on, M3×8 button head.
5. Drop the leaves in (edges on the shelves, pinion on the rack). Push by hand: must glide.
   Servo leads: thread the plug through the leaf's outer-wall notch and the 10 × 10 end-wall hole (in line
   with the servo); the lead slides through it 69 mm as the leaf moves (user manages the slack outside).
   Never route a lead across the bottle hole. Closed-switch leads along the back floor to the back notch.
6. Retainer strips (20 × M3×10 countersunk, flush).
7. **Bench test**: open/close, tune the switch slots.
8. Brackets on the bench: left brackets' tongues through the end-wall windows; right brackets
   on the flanges, M4 nut into each slot from the outside, M4 × 16 from below, snug. Put tape on
   the frame wherever it touches a bracket (and on the frame top beside them) so epoxy can't glue
   the frame.
9. Sand and degrease the steel. Epoxy on the bracket tops, lift the unit under the hole (leaves
   closed, seam under the hole centre), prop it flat against the steel until fully cured.
10. Taking it off later: 2 × M4 out (from below, right end), slide the unit 10 mm right, lower.
    Re-fit: up 10 mm right of its place, slide left, M4s.
11. Real test with a bottle.

Reachable once mounted: switch screws (re-tune from below; the nut bars hold the nuts) and the
2 right-end M4s. Everything else: take the unit off first.

First test print (plate 1): press the pinion on a servo (firm, must not slip when twisted), roll
it along the rack by hand (smooth, no binding, little play), and measure the switch's click point
on the lever tip. Fastener coupon (`coupon`, left to right): drive an M3 into the vertical pilot
(retainers/splices) and the horizontal one (servo tabs): it must cut a thread with firm effort, not
crack the plastic or spin loose; an M3 countersunk must sit flush in the countersink; an M3 nut must
drop into the hex pocket and not turn. Report anything off and only `hw.SCREWS` / the small parts
get adjusted.

---

## 10. VERIFY / open items

- [x] KW11 trip point (lever-tip travel to click). Design: nominal 1.8, stop 2.5.
- [x] KW11 mounting holes Ø3.0 (from the photo): an M3 must pass. If tight, drill to 3.2 (not M2.5: the nut bars are sized for M3).
- [ ] MG995 real dims (user's drawing 2026-11-01: case 40.3 × 20, holes 10 across, "48" along; pocket now fits 40.7): case 40 × 20, tab holes 49.5 × 10, shaft 10 mm off centre, spline Ø5.8 × 4.2.
- [x] Spline bore Ø5.7 press fit (`BORE_D`).
- [x] Printed gear mesh (`BACKLASH` 0.10).
- [x] MG995 lead exits at the gear end (user, 2026-11-01): servo turned 180° so it points outward.
- [ ] Epoxy on the user's steel (paint/oil?). Test-glue one spare bracket first if unsure.
- [ ] Servo tab screws: M3 × 8 self-tapping + Ø7 washer (tab holes Ø4.6, from the user's model).
- [x] MG995 horn screw thread (M3 assumed for the pinion centre screw).
- [ ] MG995 with calipers (2026-10-26 seat review, NOTES.md): tab thickness (2.5 or 2.0), the ridge between
      the tab holes (~0.6 high), spline height above the case top. Leaf and pinion are designed for the worst case.

---

## 11. Changing things (where to look in `model.py`)

| Want to change | Parameter(s) | Notes |
|---|---|---|
| Gear fit | `BORE_D`, `BACKLASH`, `PIN_W` | only plate 1/5 reprint |
| Switch press / stop | `SW_PRESS`, `SW_STOP_PRESS` | `T` (travel) and the cam follow automatically |
| Switch model | `cadkit/components.py` → `KW11` | lever/holes measured; re-measure if a different switch |
| Leaf overlap at the hole | `OUTER` | travel re-derives from the end switch |
| Seam | `BEVEL_C`, `BEVEL_H`, `SEAM_GAP` | |
| Leaf ↔ sheet / retainer gaps | `PLATE_Z`, `SHELF_Z`, `RET_Z` | |
| Mounting | `MOUNT_Y`, `BR_W`, `TONGUE_*`, `BR_L_U`, `FLANGE_*`, `BR_R_U`, `MOUNT_BOLT` | check 12 sweeps the on/off path and proves it holds |
| Fasteners | `TAB_SCREW`, `SW_SCREW`, `NUT_BAR_T`, `MOUNT_BOLT`, `DRIVER_R` | all modelled; checks 10 + 13 test screwdriver access |
| Print settings | `PLATES`, `GEARS`, `FRAME` | then `cad slice door2` |

After any change: `uv run cad all door2` must say **CHECK PASSED**, then look at the renders,
re-slice, and re-render the videos if the geometry changed. The checks (`checks()` in
`model.py`): sweeps of both leaves to the hard stop (rolling pinion, bolt heads included),
drop path clear when open, hole fully covered when closed, switches pressed only at their ends,
hard stop clear of the switch body, leaves captive (lift/drop), gear centre distance and overlap,
and since 2026-10-25 the assembly itself: servo goes into the leaf, leaves drop into the frame,
a Ø5 × 60 screwdriver reaches every leaf screw (bench) and every switch/mount screw (mounted, from
below), the unit's on/off path is clear, and the mounted frame is held in every direction.

---

## 12. Files

```
PROJECT.md            this file (current state)
NOTES.md              history log: original analysis, user answers, every fix with dates
firmware/             ESP32 sketch (door2/door2.ino), platformio.ini, WIRING.md
model.py              the design (CadQuery): parameters at the top, parts(), assembly(), checks(), PLATES
source/door2_original.FCStd   copy of the user's original (never edit "/home/vishal/FreeCAD Projs/2nd dorr.FCStd")
out/stl, out/step     printable parts (print orientation)
out/gcode/            G-code per plate (+ 3mf/ for the Orca GUI)
out/door2.FCStd       editable FreeCAD assembly
out/renders/          PNG views and sections
out/*.mp4             the two explainer videos
video/                anim.py, assembly_anim.py (VTK frames), src/*.tsx (Remotion), package.json
../../components/step/mg995_servo.step, kw11_microswitch.step   (KW11 lever in the STEP is wrong; use KW11 dict)
```

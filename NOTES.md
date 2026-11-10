# door2: history log

Current state, numbers and how-to: **PROJECT.md**. This file is the dated record of how the
design got there; later sections override earlier ones.

Source: `/home/vishal/FreeCAD Projs/2nd dorr.FCStd` (original, do not touch). Working copy:
`source/door2_original.FCStd`. The design is `model.py` (CadQuery).

## Goal (from the user, 2026-10-24)

Open and close the round opening in the base sheet with a rack-and-pinion mechanism.
Everything must fit in the 30 mm directly below the sheet (z = -30 … 0).

## What the original model does (studied 2026-10-24)

Coordinates are the FreeCAD file's own: X along the door travel, sheet top surface at z=+1.7.

- **BaseSheet**: 370 × 200 × 1.7 plate, z 0…1.7, with a Ø120 hole centred at (-22.96, 10).
- **SliderBase** (frame, fixed under the sheet): 294 × 200 × 30 open tray, x -170…124,
  5 mm walls. Floor strips only along the long edges (y -100…-52 and 52…100), open in the middle.
  Two module-1 involute racks (90 teeth, 20°) are fused onto the floor strips, teeth up,
  pitch line z = -26: front rack y -95…-52 (43 wide), back rack y 72…95 (23 wide).
  Limit-switch pockets in both end walls (mirrored about x = -23, the hole centre).
  M5 holes in the end walls.
- **Salidera** (the door): two leaves, bi-parting. Each is a 60 × 188 × 5 plate right under
  the sheet with a keel and a servo pocket hanging below. Open: left leaf x -143…-83,
  right leaf x 37…97, i.e. exactly either side of the hole (-83…37). Closing: each leaf
  moves 60 mm toward the centre and they meet at x = -23.
- **MotorFixture**: one MG996 servo on each leaf, shaft along -Y, travelling with the leaf.
- **GeaBigO**: pinion on the right servo's spline: m1, 18 teeth (pitch Ø18), 37 mm long,
  centre z = -17, meshing the front rack (centre distance checks out, 0.25 root clearance).
  The servo drives itself along the fixed rack, carrying its leaf.
- **Limit switches**: one in each frame end wall (fully open), one on the left leaf's inner
  edge (closed / leaves meet).

## Implied requirements

- 60 mm travel per leaf. One pinion turn = 56.5 mm, so ~382° of servo rotation: needs a
  360° (continuous) MG996R, with the limit switches as end stops. VERIFY which servo the
  user has.
- Two servos, so the two leaves are timed in software (no mechanical sync).

## Flaws found in the original

1. Nothing holds the leaves up. The leaf plate only touches the sheet's underside; the keel
   ends over the open middle of the frame. The leaf's weight hangs on the pinion resting on
   the rack, i.e. on the servo shaft.
2. No guide in Y or Z: leaves can tilt, and the pinion can lift out of mesh.
3. Left leaf has no pinion; its servo intersects the leaf (~2950 mm³, servo at y -47…-34
   vs keel/pocket at y -52…-42). Its spline sits at y -51, the right one at y -56.
4. Back rack (y 72…95) has no pinion. Either unused or meant to be a second drive.
5. Pinion is 37 mm long, cantilevered from the servo spline. Only ~6–8 mm of face is needed.
6. Leaves cover the hole edge-to-edge (60 + 60 = Ø120) with zero overlap at the edges and
   at the centre seam, so light/dirt gaps when closed.
7. Leaves sit flush against the sheet and frame (0 mm clearance), so they will rub/jam once printed.
8. Frame is 305 mm long and 200 wide; it does not fit the 220 × 220 bed in one piece.

## User answers (2026-10-24)

- Servo: **MG995, continuous 360°**. Two of them, one per leaf.
- Sheet: MS steel, part of a bigger machine. The hole drops bottles.
- Mounting: the frame screws through the two Ø11 holes in each end wall (beside the end switch)
  to an adjacent part that is superglued to the machine. Keep the frame inside the original
  envelope (x -175.5 … 129.5) so those adjacent parts still fit.
- Leaves: both slide out to an end switch each when opening, come together on command to close.
- Switch: KW11-type hinge-lever micro switch (photo), same as the model in the file.

## v2 design (model.py, 2026-10-24)

Same concept, flaws fixed. Coordinates are the original file's (x along travel, sheet underside
z=0), so `out/door2.FCStd` overlays the original.

| Original flaw | Fix |
|---|---|
| Leaves hung on the pinion | Leaf plate edges rest on 45° shelves in both side rails |
| No guide, pinion could lift out | Retainer strips (screwed on top of the rails) trap the plate edges: 0.5 mm lift max, 0.5 mm side play |
| Left leaf had no pinion, servo clashed | Both leaves identical (mirror): servo screwed by its tabs to a bulkhead, own pinion and rack |
| Back rack unused | Removed; back rail carries the closed switches instead |
| 37 mm cantilevered pinion | 8 mm pinion right at the spline (press fit + M3 centre screw) |
| Zero overlap closed | Leaves overlap the hole by 5.5 mm each side; 45° bevelled seam overlaps 2.8 mm |
| 0 mm clearances | 0.1–0.5 mm everywhere, checked by sweeps |
| Frame too big for the bed | Two mirror halves (152.5 × 200) joined at the seam line by 2 splice plates + the middle retainers |

Kept exactly from the original: frame outer envelope, end-wall Ø11 holes (y -70 / 60, z -15),
end-switch position and screw holes, module-1 / 20° / 18-tooth pinion, Ø5.7 spline bore.

Mechanism: rack bars (separate, printed flat) sit on the front floor on two pegs; the pinion
above holds them down. Travel 69 mm per leaf (1.22 pinion turns), set by the end switch. Pinion pressure pushes the
leaf up into the retainers, never out of mesh.

Switches (4 × KW11):
- Open: end-wall switches as in the original. A pad on the leaf's outer wall presses only the
  lever tip, 1.8 mm at full open (the wall is set back 2.5 mm beside it, clear of the lever's pivot
  end and the plunger). The switch pedestal is the hard stop at 2.5 mm press.
- Closed: one per leaf on the back rail, lever toward the hole. A 45° cam on the leaf presses it
  1.8 mm at full close. The leaves themselves are the hard stop (0.42 mm seam gap).
- All switch screw holes are slots (±1.5 mm) to tune the trip point.

Hardware: 2 × MG995 (360°), 4 × KW11, 4 × M3 self-tap for the servo tabs per servo (VERIFY size:
tab holes are Ø4.6), 2 × M3 × 6–8 pinion screws, 8 × M3 × 16 + nuts for the switches (from below),
20 × M3 × 10 countersunk for the retainers, 8 × M3 × 8 countersunk for the splices.

Assembly order: racks onto the pegs → servos into leaves, pinions on → leaves dropped into
the frame halves (pinion onto rack) → splice plates → retainers → switches → mount on the machine.

Control: close each leaf until its closed switch trips (run ~0.1 s more if a gap remains,
or move the switch in its slots). Open until the end switch trips. Never run without the switches.

Checks (`cad check door2`): sweeps of both leaves to the hard stop incl. the rolling pinion, drop path
clear when open, full hole coverage closed, switch press/free, hard stop, captive lift/drop,
pinion-rack overlap 0 at closed / mid / open. CHECK PASSED 2026-10-24.

## VERIFY before printing

- MG995 dims are from the user's MG996 model (same case). Measure: case 40 × 20, tab holes
  49.5 × 10, shaft 10 mm off centre, spline Ø5.8 and 4.2 long.
- Spline bore Ø5.7 press fit (pinion is a 2 g part; reprint if loose/tight).
- KW11 trip point: press the lever tip by hand and note how far it moves before it clicks.
  Design assumes ~1 mm; nominal press 1.8, hard stop 2.5. The slots give ±1.5 mm.
- Rack/pinion mesh (backlash 0.1 printed). Print one pinion + one rack first (~20 min) and
  test on the servo before the long frame prints.

## Videos (2026-10-24)

`out/door2_how_it_works.mp4` (62 s) and `out/door2_assembly.mp4` (87 s, assembly + mounting).
Frames: `video/anim.py`, `video/assembly_anim.py` (VTK, from model.py). Edit: `video/src/*.tsx`
(Remotion 4.0.534), then `npm run render` / `npm run render:assembly` in `video/`.
The mounting blocks in the assembly video are a PLACEHOLDER for the user's own adjacent part.
Mounting order: everything (incl. retainers, which screw from the top) is done on the bench;
bolt the blocks to the end walls first, then glue the block tops to the sheet with the unit
attached, so the frame lines up with the hole.

## Switch re-measured from the user's photo (2026-10-24)

The KW11 model in the original FCStd had a 9.7 mm-tall lever; the real switch's lever tip is only
3.8 mm off the body (pivot 11.4 mm, tip 25.6 mm from the terminal end, red plunger at 22.6 mm,
3.1 mm tall). Holes are 22.6 × 10.3 apart (model had 23 × 11). With the old lever the leaf would
have stopped 3 mm short of the end switch. Fixed: travel 64 -> 69 mm, striker pad + recess on the
leaf wall, cam re-derived, hole slots re-centred. Scale was taken from the 28 mm body length.

## Zone check (2026-10-24)

All design parts stay inside z -30..0 and the sheet footprint (x ±185, y ±100) with the leaves
closed, open and at the hard stop. The frame is off-centre on the sheet (hole at x -22.96): the
LEFT end wall has only 15 mm to the sheet edge (right: 61 mm). A mounting block there can be at
most ~14 mm thick and nothing may stick out of it: nut trapped in a slot in the block, bolt head
inside the frame. The assembly video's placeholder blocks now do this. (The 0.4 mm head clearance
noted here was fixed in the design review below: now 1.9 mm with a washer.)

## Design review (2026-10-24)

Fixed:
- No wire exit existed (frame closed on all sides; the only way out was the bottle path). Added
  bottom-open notches 6.5 × 10.5 in each end wall at y ±92: servo leads (front) and closed-switch
  leads (back) run along the floor under the shelves and leave there, clear of the mounting blocks.
- Open leaf came within 0.4 mm of the M10 heads; a washer would have collided. Leaf corners are
  notched 3.5 mm at the bolt positions; bolt head + washer envelopes (Ø20 × 8.4) are now in the
  assembly, so sweeps check them (1.9 mm clear at the hard stop). Rack rib shortened to clear them.

Remaining risks (not fixable in CAD, test them):
- Stall load: MG995 stall ~10 kg·cm (VERIFY) is ~110 N at the pinion: Lewis bending ~45 MPa on a
  PLA m1 tooth, about PLA's strength. Normal running load is a few N. Firmware MUST stop on the
  switches and also time out (~2 s per move). If a pinion strips, print it in PETG.
- Switch trip point, MG995 dims, spline press fit, rack/pinion printed backlash, servo cable exit
  side (route + 70 mm slack loop on the front floor), the user's mounting blocks.

## Sliced (2026-10-24, black PLA, `cad slice door2`)

| Plate | Time | Filament |
|---|---|---|
| 1_test_pinion_rack (0.16 mm) | 30 min | 4.8 g |
| 2_frame_right (3 walls, 20 %) | 3 h 23 | 88.1 g |
| 3_frame_left | 3 h 25 | 89.0 g |
| 4_leaves (3 walls) | 2 h 53 | 83.8 g |
| 5_small_parts (0.16 mm) | 2 h 00 | 28.1 g |
| total | ~12 h 11 | ~294 g |

All G-code inside the bed, thumbnails injected. Print plate 1 first and test the mesh.

## Mounting redesign + assembly audit (2026-10-25)

The user spotted that the mounting blocks in the assembly video (1:00-1:03) couldn't work. They were
a placeholder that existed only in the video script and were never checked. Confirmed in the model:
- Front M10 bolts (y -70): sheet above, front floor below, leaf corner over them when open, so they
  could never be undone once mounted (the video's "unbolt the unit" was false).
- Nut slot cut into the glued face (~40 % of the glue area, 1.2 mm outer skin); CA in peel.

User answers: right end reachable once mounted, left end (15 mm) not; no screws into the sheet,
epoxy OK; no existing adjacent part. New design (model.py, "Mounting"): left brackets with a tongue
through a window in the end wall (the wall hangs on it); right brackets over a flange on the frame,
M4 x 16 from below into a nut slid into the bracket. Lift 10 mm right of place, slide left, bolt.
First attempt had the tongue in a notch open at the top: clash-free but it held nothing. Caught by a
negative test; check 12b now proves the frame is held (down/sideways/up), not just clear.

Audit of every fastener and assembly step (none were in the checks before):
- Servo tab screws: the upper two couldn't be driven (inner rib, back beam in the way; screwdriver
  axis 4 mm under the plate) and their heads hit the inner rib. Bulkhead moved behind the tabs
  (normal servo mounting), screws from the shaft side, driver channel under the inner rib and the
  front beam (front half of the leaf, low bending moment there).
- Switch screws "M3 x 16-20": M3 x 20 in the closed switch hits the leaf. Now exact: end x 20,
  closed x 16. Nut on top couldn't be held once mounted: printed nut bars (one per switch).
- Removed: Ø11 end-wall holes, leaf corner notches, bolt-head envelopes.
- New checks (model.py 9-13): servo into leaf, leaf-screw driver corridors, leaves drop into the
  frame, mounting path + mount holds, switch/mount screws reachable from below when mounted. All
  fasteners are now solids in the assembly, so the sweeps include them. Negative tests confirmed the
  checks fail on the old screw direction, on M3 x 20, and on the open-top notch.
Re-sliced: 6 plates, 13 h 34, 328 g. Videos and FreeCAD file regenerated.
- (2026-10-25, later) Splice screws: M3 x 8 countersunk from z -21 ends at z -29, exactly the bottom
  of the old blind pilot, so a screw could bottom out before its head clamped. Pilots now go through
  the frame floor. Frames re-sliced (plates 2, 3; times unchanged).
- (2026-10-25, later) Thread audit of every self-tapping hole (new check 14: >= 1.2 mm plastic round
  the M3 thread, bite >= 4 mm, tip >= 0.5 mm off a blind bottom). Found: all 20 retainer screws had
  ~0.5 mm between thread and the leaf slot (could bulge into the leaf's path). RET_HOLE_Y 93 -> 94.5.
  Countersinks widened to Ø7.0 (ISO 10642 heads, 6.72, now sit flush; they face the steel).
  Splices and servo tabs passed. Still VERIFY: M3 through the KW11's Ø3.0 holes (from the photo).
- (2026-10-25, later) M3 pilot Ø2.6 is not yet CONFIRMED on this printer (DESIGN_GUIDE: only M4
  clearance is). Added `coupon` to plate 1 (47 min now): vertical + horizontal pilot, countersink,
  nut-bar pocket. All self-tap bosses also meet the guide's 2 mm wall round the pilot.

## MG995 seat review (2026-10-26)
Prompted by the lidar_scanner pan servo, which did not seat because of a tab ridge our MG995 STEP
leaves out (see `components/CATALOG.md`). With the ridge, root fillets, label plate and the second
STEP's taller spline in `ref_mg995()`, door2 had: root fillets 0.1 mm into the 0.3 mm case pocket (both
tab faces) and the bulkhead pillars on the way in, the label plate 0.2 mm into the pocket end, and
the pinion's blind bore 0.5 mm short if the spline is the taller one. Fixed: relief 0.5 wider for 1.2 mm
each side of the tabs down the full pillar, pocket end clears the label plate, pinion bore to
`spline_top_b` with a 1.8 counterbore (1.2 floor). The tab ridge itself clears (the bulkhead is on the case
side; Ø7 washers stop 0.75 short of it). CHECK PASSED. Nothing printed yet, so re-slice before printing.


## Pre-print review + servo turned round (2026-11-01)
Full re-check before printing (CHECK PASSED, G-code was current). Found and fixed:
- Servo pocket was 40.6 long for a 40.0 model case. The user's drawing says 40.3, retail spec 40.7. The
  servo is held by its tab screws, so the pocket is now sized for 40.7 + 0.3 per side (`SERVO_CASE_L`).
- The user's MG995 lead leaves at the **gear end** (confirmed by the user). With the old orientation it
  pointed at the seam: both leads would have shared a 7 mm gap between the leaves and could be pinched
  as they closed; the route in PROJECT.md (front-floor loop) was blocked by the bulkhead pillar. The user
  wants no cable anywhere near the bottle hole. Fix: servo turned 180° about its shaft (case footprint
  and tab screws unchanged, shaft u 22 -> 42, racks/pegs follow `SHAFT_U`). Lead goes straight out: a
  bottom-open notch in the leaf's outer wall and a 10 x 10 hole in each end wall at (y -18.4, z -15.75);
  the plug passes both. The lead slides through the wall as the leaf moves; the user handles the slack.
  New check 15: a grommet-sized path from the servo's outer end through the end wall is clear closed and
  open and never inside the drop path. Rack/pinion shapes unchanged (plate 1 parts still valid).
- Noted, not changed: coupon is printed at 0.16 mm, frames/leaves at 0.28 mm (screw-hole results are
  only indicative). Bottle load: none (user: bottles only pass when the door is open; nothing rests on the leaves).
Re-sliced: 13 h 35, 330 g. Videos (captions: lead route) and out/door2.FCStd re-rendered 2026-11-01.

## Plate 1 printed (2026-11-01)
User: pinion press fit on the spline, rack mesh, coupon (both pilots, countersink, nut pocket), switch
click point, M3 through the KW11 holes, horn screw all OK. Some stringing: black PLA was run at 225 °C
(Anycubic's profile says 215) with travel over open air. Fixed in `cadkit/slicer.py` for all projects:
black 215 °C after a 230 °C first layer, `reduce_crossing_wall` on. Re-sliced (about +3 min per plate).

## Left leaf servo pillar broke (2026-11-06)
User: one bulkhead pillar (servo tab mount) on `leaf_left` broke off. Likely cause: pillar is a 4 x 8 x 21 mm
post printed with layers across the load (leaf prints plate-down), plus the 0.5 mm root-fillet relief notch.
User chose to reprint the whole leaf, unchanged geometry (STL matches model: 51 245 mm³). Sliced alone:
`out/gcode_reprint/4L_leaf_left_reprint.gcode`, black, 3 walls, 1 h 30, 42.5 g. Which pillar / where / when it
broke: not yet known. The right leaf has the same weakness; strengthening (thicker pillars, gussets) not done.

## Firmware (2026-11-06)
`firmware/door2/door2.ino`: ESP32 38-pin, no libraries, core 2.x + 3.x (LEDC). Servos GPIO18 (L) / 19 (R),
switches NC to GND on 32 (L open) 33 (L closed) 25 (R open) 26 (R closed), button 27. Serial commands
o/c/s/?/r, jog L+/L-/R+/R-, n (neutral trim). Each leaf stops on its own switch; faults on a 4 s timeout,
on not leaving the start switch within 0.8 s, or on both switches of one leaf pressed. PWM is switched off
after each stop (servo limp, no creep). OPEN_SIGN_L/R (-1/+1) and STOP_US are guesses: set on the first run.
Compiled with PlatformIO (core 2.0.17); not run on hardware yet.
Jog test (user, 2026-11-06): L+ closes, R+ opens -> OPEN_SIGN_L = -1, OPEN_SIGN_R = +1 confirmed (the defaults).

## Wiring + firmware hand-over video (2026-11-10)
`out/door2_wiring_firmware.mp4` for the person writing the code (user has assembled the door). Source: `video/src/Firmware.tsx`, `video/src/fw/`,
`video/wiring_anim.py` (plan view + callout positions from model.py), `video/extract_fw_code.py` (code excerpts from door2.ino; fails if the lines move).
Rerun the extractor and render after any firmware change. Serial text on screen checked against door2.ino; the integration example
(`video/fw_hook_example.cpp`) compiles against the sketch on core 2.0.17. Sample output is illustrative: a full open/close is still not logged.
The sketch header says to leave the pinions off for the first run; the video replaces that with "only jog away from a pressed switch" because the door is already assembled.

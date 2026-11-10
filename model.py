"""door2: motorised bi-parting door under the bottle-drop hole (rack and pinion).

Rework of the user's "2nd dorr.FCStd" (copy in source/). Two leaves close a Ø120 hole in an
MS sheet. Each leaf carries a 360° MG995 whose pinion walks along a fixed rack in the frame.
Everything lives in the 30 mm under the sheet.

Run from the workspace root:
    cad all door2        build STL/STEP + checks + renders   (out/)
    cad freecad door2    editable FreeCAD assembly           (out/door2.FCStd)

World = the original FCStd's frame: X along the door travel, Y across, sheet underside at Z=0,
workspace Z -30..0. Geometry is written in u = x - XC (u=0 is the hole centre and the seam
between the leaves); the design is mirror-symmetric about u=0. W() moves u to world X.
Right leaf: u > 0, closes toward -u. Front = -Y (racks, servos), back = +Y (closed switches).
Values marked VERIFY come from the user's models, not from a measured part.
"""

import math

import cadquery as cq

from cadkit import hardware as hw
from cadkit.components import KW11, MG995, ref_kw11, ref_kw11_lever, ref_mg995
from cadkit.geom import box, union_all, xy_prism, xz_prism, yz_prism, ycyl, zcyl
from cadkit.io import flip

NAME = "door2"

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------
# Machine (from the original file)
XC = -22.96                      # hole centre X; mirror plane of the design
HOLE_Y, HOLE_R = 10.0, 60.0      # Ø120 bottle-drop hole
SHEET = (370.0, 200.0, 1.7)      # MS sheet, centred on x=0, underside at z=0
Z_BOT = -30.0                    # workspace limit under the sheet

# Frame (two mirror halves joined at u=0)
U_END, END_T = 147.0, 5.0        # end wall outer face / thickness (original x -169.96 / 124.04)
Y_OUT, SIDE_T = 100.0, 4.0
FLOOR_T = 2.0
FRONT_FLOOR_Y = -51.5            # front floor stops 1.5 mm outside the hole (y=-50)
BACK_FLOOR_Y = 72.0              # back floor starts 2 mm outside the hole (y=+70)
SLOT_Y = 91.0                    # leaf edges run in |y| <= SLOT_Y
SHELF_Y = 86.0                   # shelf and retainer inner edge
SHELF_Z = -7.0                   # leaf plate rests on the shelves
RET_Z = -3.0                     # retainer strip underside (strip top flush at z=0)
CABLE_NOTCH = (6.5, 10.5, 92.0)  # end-wall wire notches, open at the bottom: width, height, |y|

# Mounting (redesigned 2026-10-25). Four printed brackets are epoxied to the sheet; the unit itself is
# removable. Left end: 15 mm to the sheet edge and out of reach once mounted, so each left bracket has
# a tongue that slides through a window in the end wall; the wall above the window hangs on it.
# Right end (reachable): an M4 from below
# through a flange on the frame into a nut in each right bracket. Install: lift the unit MOUNT_SLIDE
# to the right of its place, slide it left onto the tongues, bolt the right end.
U_SHEET_L, U_SHEET_R = SHEET[0] / 2 + XC, SHEET[0] / 2 - XC   # sheet edges in u (162.04, 207.96)
MOUNT_Y = (-70.0, 60.0)          # bracket centres: clear of the end switch (y -8..31) and wire notches
BR_W = 32.0                      # bracket width (y)
TONGUE_W, TONGUE_Z = 14.0, (-14.0, -6.0)   # tongue width (y) and z range
WINDOW_CLR = (0.3, 0.2)          # window in the end wall around the tongue: below, above (the frame
                                 # hangs 0.2 low at the left end)
TONGUE_IN = 4.0                  # tongue tip past the end wall's inner face
MOUNT_SLIDE = END_T + TONGUE_IN + 1.0                     # 10
BR_L_U = (U_END + 0.3, U_SHEET_L - 0.5)                   # left bracket (mirrored u), 14.2 thick
BR_L_Z = -16.0
FLANGE_T, FLANGE_L = 8.0, 28.0   # right flange on the frame bottom: thickness, reach past the wall
BR_R_U = (U_END + MOUNT_SLIDE + 0.5, U_END + FLANGE_L - 1.0)   # clears the wall while the unit is offset
BR_R_Z = Z_BOT + FLANGE_T + 0.3  # bracket underside; the bolt pulls the frame top onto the sheet
MOUNT_BOLT = ("M4", 16.0, 4.0)   # socket head cap screw from below: size, length, head height
MOUNT_NUT_Z = -16.0              # nut slot bottom (nut slides in from the bracket's outer face)

# Leaf (right leaf, closed position; the left leaf is its mirror)
PLATE_Z = (SHELF_Z + 0.1, -3.5)  # rests on the shelf, 0.5 under the retainer
LEAF_Y = SLOT_Y - 0.5
OUTER = 65.5                     # outer edge closed: covers the hole edge (u=60) by 5.5
# Switches (KW11, lever measured from the user's photo; trip point VERIFY).
END_SW = (-131.54, -5.0, -25.19)         # left end switch: (lz, lx, ly) + this, in u (user's position)
CLOSED_SW = (15.0, 64.56, -29.19)        # right closed switch: (lx, -lz, ly) + this, in u
SW_PRESS = 1.8                           # nominal lever-tip press at the end of travel (free tip 3.8)
SW_STOP_PRESS = 2.5                      # hard stop: never pressed further than this
SLOT_ADJ = 1.5                           # switch screw slots: +-1.5 mm adjustment
# Switch screws: M3 socket head from below, nuts on top held by a printed nut bar, so a switch can be
# re-tuned from below with the unit mounted. Lengths end exactly at the bar's top.
NUT_BAR_T = 3.0                          # nut pockets 2.6 deep from below, 0.4 skin on top
SW_SCREW = {"end": 20.0, "closed": 16.0}
END_LEVER_U = -(KW11["lever_tip_z"] + END_SW[0])          # right end switch, free lever tip (132.68)
T = round(END_LEVER_U + SW_PRESS - OUTER, 2)               # travel of each leaf (68.98)
BEVEL_C, BEVEL_H = 0.7, 1.7      # 45° bevel seam: centre and half-run (plate is 3.4 thick)
SEAM_GAP = 0.6                   # horizontal gap between the two bevels (0.42 normal to them)
RIB_T, RIB_Z = 4.0, -10.0
WALL_Y, WALL_Z = (-35.0, 40.0), -23.0   # striker wall on the outer edge, hits the end switch
WALL_T, WALL_RECESS = 6.0, 2.5          # striker wall thickness; set-back beside the lever tip pad

# Servo MG995 (360°), lying on its side, shaft along -Y
SERVO_U = 32.0                   # case centre u (closed)
SERVO_Y = -40.0                  # y of the tab plane (local z=0 of the servo model)
SERVO_Z = -15.75                 # shaft height = case centre
# The user's MG995 has its lead at the gear end (2026-11-01). The servo is turned 180° about its shaft
# so the lead points outward (away from the bottle hole) and leaves straight through the end wall.
SHAFT_U = SERVO_U - MG995["shaft_x"]
SERVO_CASE_L = 40.7              # pocket length: user's drawing 40.3, retail spec 40.7 (model 40.0)
CABLE_HOLE = 10.0                # square lead exit (passes the 3-pin plug), centred on the grommet
CABLE_Y = SERVO_Y + sum(MG995["grommet"][2]) / 2
CABLE_Z = SERVO_Z - sum(MG995["grommet"][1]) / 2
# Bulkhead behind the tabs (case side), as in any servo mount: the tab screws go in from the shaft
# side (-y), where a screwdriver reaches past the leaf's front edge. (Until 2026-10-25 the bulkhead was
# on the shaft side and the upper screws could not be reached: ribs in the way.)
BULK_Y = (SERVO_Y + MG995["tab_z"][1], SERVO_Y + MG995["tab_z"][1] + 4.0)
TAB_SCREW = 8.0                  # M3 x 8 self-tapping, pan head + washer (Ø7: covers the Ø4.6 tab hole)
SERVO_CLR = 0.3
DRIVER_R = 2.5                   # screwdriver shaft radius for the tool-access checks

# Gears: module 1, 20°, z=18 pinion (as original), printed backlash
MOD, PA, PIN_Z = 1.0, 20.0, 18
BACKLASH = 0.10                  # tooth thinning on each part (pitch-line, total)
R_PITCH = MOD * PIN_Z / 2
PIN_W = 8.0                      # face width (original was 37)
PIN_Y1 = SERVO_Y + MG995["spline_z"][1] - 0.3          # inner face, 0.3 off the servo boss
PIN_Y0 = PIN_Y1 - PIN_W
BORE_D = 5.7                     # press on the 25T spline, VERIFY (user's value)
PIN_CB = 1.8                     # screw head counterbore depth (button head 1.65); leaves a 1.2 floor
PITCH_Z = SERVO_Z - R_PITCH      # rack pitch line
RACK_Y = (PIN_Y0 - 0.7, PIN_Y1 + 0.5)
RACK_U = (SHAFT_U - 11.0, SHAFT_U + T + 11.0)
RACK_Z0 = Z_BOT + FLOOR_T        # rack bar sits on the floor
PEG_D, PEG_H = 2.8, 1.0
PEGS_U = (SHAFT_U - 2.0, SHAFT_U + T + 2.0)
RIB_Y = (RACK_Y[0] - 4.5, RACK_Y[0] - 0.3)              # floor rib behind the rack


# Retainers / splices
RET_SPLIT = 40.0                         # retainer strips: [-142,-40] [-40,40] [40,142]
SPLICE = (16.0, 20.0, 3.0)               # u x y x z, joins the frame halves on the floor
FRONT_SPLICE_Y, BACK_SPLICE_Y = -82.0, 84.0


def W(s):
    """u-frame -> world X."""
    return s.translate((XC, 0, 0))


def mu(s):
    """Mirror across u=0 (left-hand copy)."""
    return s.mirror("YZ")


def my(s):
    """Mirror across y=0 (front <-> back copy)."""
    return s.mirror("XZ")


# --------------------------------------------------------------------------
# Small geometry helpers
# --------------------------------------------------------------------------
def slot_z(r, z0, z1, x, y, dx=0.0, dy=0.0):
    """Vertical slot (stadium) from (x-dx, y-dy) to (x+dx, y+dy)."""
    a = zcyl(r, z0, z1, x - dx, y - dy).union(zcyl(r, z0, z1, x + dx, y + dy))
    if dx:
        a = a.union(box(x - dx, x + dx, y - r, y + r, z0, z1))
    if dy:
        a = a.union(box(x - r, x + r, y - dy, y + dy, z0, z1))
    return a


def cbore_up(size, z_bot, depth, x, y, z_top, dx=0.0, dy=0.0):
    """Screw from below: clearance slot to z_top, head counterbore opening at the bottom face."""
    s = hw.screw(size)
    return slot_z(s["clear"] / 2, z_bot - 1, z_top + 1, x, y, dx, dy).union(
        slot_z(s["head_d"] / 2 + hw.CLR, z_bot - 1, z_bot + depth, x, y, dx, dy))


def csink(size, z_top, x, y, through=20.0):
    """Countersunk screw from the top (90° head)."""
    s = hw.screw(size)
    hd = s["head_d"] + 1.5                               # 7.0 for M3: ISO 10642 heads (6.72) sit flush too
    cone = cq.Workplane(obj=cq.Solid.makeCone(s["clear"] / 2, hd / 2, (hd - s["clear"]) / 2,
                                              cq.Vector(x, y, z_top - (hd - s["clear"]) / 2)))
    return cone.union(zcyl(s["clear"] / 2, z_top - through, z_top + 0.1, x, y)).union(
        zcyl(hd / 2, z_top - 0.01, z_top + 1, x, y))


def acyl(r, p, d, h):
    """Cylinder from point p along unit direction d."""
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, h, cq.Vector(*p), cq.Vector(*d)))


def hex_nut(size, p, d, af=None, h=None):
    """Hex prism (a nut, or a pocket for one with af/h given) from p along an axis-aligned d."""
    s = hw.screw(size)
    af, h = af or s["nut_af"], h or s["nut_h"]
    n = cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(h)
    if d[1]:
        n = n.rotate((0, 0, 0), (1, 0, 0), -90 * d[1])
    elif d[2] < 0:
        n = n.mirror("XY")
    return n.translate(p)


def screw_ref(size, p, d, length, head_d, head_h):
    """Fastener envelope: head below p (against -d), shank from p along d.
    Shank drawn at the self-tap pilot size so it sits in pilot and clearance holes without overlap.
    Also returns the screwdriver corridor (DRIVER_R, 60 mm) out of the head."""
    top = tuple(pi - di * head_h for pi, di in zip(p, d))
    s = acyl(hw.screw(size)["pilot"] / 2 - 0.1, p, d, length).union(acyl(head_d / 2, top, d, head_h))
    return s, acyl(DRIVER_R, top, tuple(-di for di in d), 60.0)


# --------------------------------------------------------------------------
# Gears
# --------------------------------------------------------------------------
def _inv(a):
    return math.tan(a) - a


def pinion_profile(z=PIN_Z, m=MOD, pa=PA, backlash=BACKLASH, n=8):
    """Involute spur gear outline (closed point list), tooth 0 centred on +X."""
    a = math.radians(pa)
    r = m * z / 2
    rb, ra, rf = r * math.cos(a), r + m, r - 1.25 * m
    psi = (math.pi * m / 2 - backlash) / (2 * r)          # half tooth angle at the pitch circle

    def half(rr):
        return psi + _inv(a) - _inv(math.acos(min(1.0, rb / rr)))

    r0 = max(rb, rf)
    radii = [r0 + (ra - r0) * i / n for i in range(n + 1)]
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        hb = half(r0)
        flank = [(rr, half(rr)) for rr in radii]
        right = ([(rf, c - hb)] if rf < r0 else []) + [(rr, c - h) for rr, h in flank]
        left = [(rr, c + h) for rr, h in reversed(flank)] + ([(rf, c + hb)] if rf < r0 else [])
        pts += right + left
        pts.append((rf, c + math.pi / z))                 # root midpoint
    return [(rr * math.cos(t), rr * math.sin(t)) for rr, t in pts]


def rack_profile(u0, u1, z_pitch, z_base, centres, m=MOD, pa=PA, backlash=BACKLASH):
    """Rack outline in (u, z), teeth up, tooth centres given; flat base down to z_base."""
    t = math.tan(math.radians(pa))
    s2 = (math.pi * m / 2 - backlash) / 2
    zr, zt = z_pitch - 1.25 * m, z_pitch + m
    wr, wt = s2 + 1.25 * m * t, s2 - m * t
    pts = [(u0, z_base), (u1, z_base), (u1, zr)]
    for c in sorted(centres, reverse=True):
        if c - wr < u0 or c + wr > u1:
            continue
        pts += [(c + wr, zr), (c + wt, zt), (c - wt, zt), (c - wr, zr)]
    pts.append((u0, zr))
    return pts


def pinion():
    """On the right servo's spline, closed position. Teeth are phased so a space faces down."""
    g = (cq.Workplane("XZ", origin=(SHAFT_U, PIN_Y1, SERVO_Z)).polyline(pinion_profile()).close()
         .extrude(PIN_W))                                 # XZ normal is -Y: PIN_Y1 -> PIN_Y0
    spline_end = SERVO_Y + MG995["spline_top_b"]          # the taller of the two STEPs' splines (VERIFY)
    g = g.cut(ycyl(BORE_D / 2, spline_end - 0.3, PIN_Y1 + 1, SHAFT_U, SERVO_Z))
    g = g.cut(ycyl(hw.screw("M3")["clear"] / 2, PIN_Y0 - 1, PIN_Y1, SHAFT_U, SERVO_Z))
    return g.cut(ycyl(hw.screw("M3")["head_d"] / 2 + 0.35, PIN_Y0 - 1, PIN_Y0 + PIN_CB, SHAFT_U, SERVO_Z))


def rack():
    """Right rack bar on the front floor, located by two frame pegs; the pinion holds it down."""
    centres = [SHAFT_U + k * math.pi * MOD for k in range(-6, 30)]
    r = xz_prism(rack_profile(RACK_U[0], RACK_U[1], PITCH_Z, RACK_Z0, centres), *RACK_Y)
    for pu in PEGS_U:
        r = r.cut(zcyl((PEG_D + 0.4) / 2, RACK_Z0 - 1, RACK_Z0 + PEG_H + 0.4, pu, sum(RACK_Y) / 2))
    return r


# --------------------------------------------------------------------------
# Bought parts, placed
# --------------------------------------------------------------------------
def servo_place(s):
    """MG995 model frame -> right leaf (closed): local x->-u (lead end outward), z->y, y->z."""
    return s.rotate((0, 0, 0), (0, 0, 1), 180).rotate((0, 0, 0), (1, 0, 0), -90).translate((SERVO_U, SERVO_Y, SERVO_Z))


def end_switch_place(s):
    """KW11 frame -> left end switch, exactly as in the user's file (lever toward +u)."""
    return s.rotate((0, 0, 0), (1, 1, 1), 120).translate(END_SW)


def closed_switch_place(s):
    """KW11 frame -> right closed switch, lever toward -y (toward the hole)."""
    return s.rotate((0, 0, 0), (1, 0, 0), 90).translate(CLOSED_SW)


def end_sw_pt(lx, ly, lz):
    return lz + END_SW[0], lx + END_SW[1], ly + END_SW[2]


def closed_sw_pt(lx, ly, lz):
    return lx + CLOSED_SW[0], -lz + CLOSED_SW[1], ly + CLOSED_SW[2]


# derived switch geometry (right side, u > 0)
END_BODY_U = -end_sw_pt(0, 0, KW11["body"][2][1])[0]                       # 136.48 body face
END_STOP_U = END_LEVER_U + SW_STOP_PRESS                                     # leaf hard stop
CL_LEVER_Y = closed_sw_pt(0, 0, KW11["lever_tip_z"])[1]                     # 65.72 free tip
CAM_Y = CL_LEVER_Y + SW_PRESS                                               # cam flat
CL_LEVER_U = (closed_sw_pt(KW11["lever_x"][0], 0, 0)[0], closed_sw_pt(KW11["lever_x"][1], 0, 0)[0])


# --------------------------------------------------------------------------
# Printed parts (u frame, right-hand / front versions)
# --------------------------------------------------------------------------
def side_profile_front():
    """Front rail cross-section (y, z): wall + retainer seat + 45° shelf."""
    y0, ys = -Y_OUT, -Y_OUT + SIDE_T
    wall = [(y0, Z_BOT), (ys, Z_BOT), (ys, RET_Z), (y0, RET_Z)]
    shelf = [(ys - 0.5, SHELF_Z - 3 - (-ys + 0.5 - SHELF_Y)), (-SHELF_Y, SHELF_Z - 3), (-SHELF_Y, SHELF_Z),
             (-SLOT_Y, SHELF_Z), (-SLOT_Y, RET_Z), (ys - 0.5, RET_Z)]
    return wall, shelf


def frame_half(end="right"):
    """Right frame half, u 0 .. U_END (+ the end-switch pedestal outside the wall). end="left" builds the
    left half's own mounting (tongue notches) in this right-hand frame; parts() mirrors it."""
    u0, u1 = 0.0, U_END - END_T + 0.5
    wall, shelf = side_profile_front()
    rail_f = yz_prism(wall, u0, u1).union(yz_prism(shelf, u0, u1))
    rail = rail_f.union(my(rail_f))
    floor_f = box(u0, u1, -Y_OUT + 1, FRONT_FLOOR_Y, Z_BOT, Z_BOT + FLOOR_T)
    floor_b = box(u0, u1, BACK_FLOOR_Y, Y_OUT - 1, Z_BOT, Z_BOT + FLOOR_T)
    rib = box(u0, min(RACK_U[1] + 10.0, U_END - END_T + 0.5), RIB_Y[0], RIB_Y[1], Z_BOT + 1, RACK_Z0 + 4.0)
    wall = box(U_END - END_T, U_END, -Y_OUT, Y_OUT, Z_BOT, 0.0)
    f = union_all([rail, floor_f, floor_b, rib, wall])

    # splice bosses at the joint (front and back), thick enough for self-tapping screws
    for yc in (FRONT_SPLICE_Y, BACK_SPLICE_Y):
        f = f.union(box(u0, SPLICE[0] / 2 + 2, yc - SPLICE[1] / 2 - 2, yc + SPLICE[1] / 2 + 2, Z_BOT, -24.0))

    # rack pegs
    for pu in PEGS_U:
        f = f.union(zcyl(PEG_D / 2, RACK_Z0 - 0.5, RACK_Z0 + PEG_H, pu, sum(RACK_Y) / 2))

    # end switch: pedestal (also the leaf's hard stop), notch through the wall
    sw = ref_kw11(lever=False)
    sb = mu(end_switch_place(sw)).val().BoundingBox()          # incl. terminals
    (bx0, bx1), _, _ = KW11["body"]
    body_y = (bx0 + END_SW[1], bx1 + END_SW[1])
    f = f.union(box(END_STOP_U, END_BODY_U + 16.0, body_y[0] - 1.0, body_y[1] + 1.0, Z_BOT, sb.zmin))
    f = f.cut(box(U_END - END_T - 1, U_END + 1, sb.ymin - 0.4, sb.ymax + 0.4, sb.zmin - 0.3, 1.0))
    for lx, lz in KW11["holes"]:
        hu, hy, _ = end_sw_pt(lx, 0, lz)
        f = f.cut(cbore_up("M3", Z_BOT, 3.0, -hu, hy, sb.zmin, dx=SLOT_ADJ))

    # closed switch: pedestal on the back floor
    cb = closed_switch_place(sw).val().BoundingBox()
    f = f.union(box(CLOSED_SW[0] + bx0 - 1.5, CLOSED_SW[0] + bx1 + 1.5, cb.ymin - 0.5, SHELF_Y + 1.5, Z_BOT, cb.zmin))
    for lx, lz in KW11["holes"]:
        hu, hy, _ = closed_sw_pt(lx, 0, lz)
        f = f.cut(cbore_up("M3", Z_BOT, 3.0, hu, hy, cb.zmin, dy=SLOT_ADJ))

    # mounting: left = windows in the wall for the bracket tongues; right = bolt flanges
    for y in MOUNT_Y:
        if end == "left":
            f = f.cut(box(U_END - END_T - 1, U_END + 1, y - TONGUE_W / 2 - 0.3, y + TONGUE_W / 2 + 0.3,
                          TONGUE_Z[0] - WINDOW_CLR[0], TONGUE_Z[1] + WINDOW_CLR[1]))
        else:
            ub = sum(BR_R_U) / 2
            f = f.union(box(U_END - 0.5, U_END + FLANGE_L, y - BR_W / 2, y + BR_W / 2, Z_BOT, Z_BOT + FLANGE_T))
            f = f.cut(cbore_up(MOUNT_BOLT[0], Z_BOT, MOUNT_BOLT[2] + 0.3, ub, y, Z_BOT + FLANGE_T, dx=1.0))

    # wire exits: switch leads run along the floor under the shelves and leave through these notches,
    # outside the mounting blocks
    w, h, yc = CABLE_NOTCH
    for sy in (-1, 1):
        f = f.cut(box(U_END - END_T - 1, U_END + 1, sy * yc - w / 2, sy * yc + w / 2, Z_BOT - 1, Z_BOT + h))
    # servo lead: straight out from the servo's outer end, slides through this hole as the leaf moves
    c = CABLE_HOLE / 2
    f = f.cut(box(U_END - END_T - 1, U_END + 1, CABLE_Y - c, CABLE_Y + c, CABLE_Z - c, CABLE_Z + c))

    # retainer and splice screw pilots
    for uh in retainer_holes():
        for ys in (-1, 1):
            if 0 < uh < U_END:
                f = f.cut(zcyl(hw.screw("M3")["pilot"] / 2, RET_Z - 10, RET_Z + 1, uh, ys * RET_HOLE_Y))
    for yc in (FRONT_SPLICE_Y, BACK_SPLICE_Y):
        for hu, hy in splice_holes():
            if hu > 0:
                # through the floor: an M3 x 8 countersunk from z -21 ends at -29, which was exactly
                # the old blind pilot's bottom (it could bottom out before the head clamps)
                f = f.cut(zcyl(hw.screw("M3")["pilot"] / 2, Z_BOT - 1, -23.0, hu, yc + hy))

    # never anything inside the drop path
    return f.cut(zcyl(HOLE_R + 1.0, Z_BOT - 1, 1, 0, HOLE_Y))


# Retainer screws sit outboard of the strip's centre: at the centre (y 93) the thread was 0.5 mm from
# the leaf slot and could bulge it (found 2026-10-25); here >= 2 mm all round
RET_HOLE_Y = Y_OUT - 5.5


def retainer_holes():
    """u of every retainer screw (right half and the shared middle)."""
    mid = [-RET_SPLIT + 8, -10.0, 10.0, RET_SPLIT - 8]
    e0, e1 = RET_SPLIT, U_END - END_T
    end = [e0 + 8, (e0 + e1) / 2, e1 - 8]
    return mid + end


def retainer(kind):
    """Front retainer strip: 'mid' spans the joint, 'end' runs to the end wall."""
    u0, u1 = (-RET_SPLIT + 0.2, RET_SPLIT - 0.2) if kind == "mid" else (RET_SPLIT + 0.2, U_END - END_T - 0.2)
    r = box(u0, u1, -Y_OUT, -SHELF_Y, RET_Z, 0.0)
    for uh in retainer_holes():
        if u0 < uh < u1:
            r = r.cut(csink("M3", 0.0, uh, -RET_HOLE_Y))
    return r


def splice_holes():
    return [(sx * SPLICE[0] / 4, sy * SPLICE[1] / 4) for sx in (-1, 1) for sy in (-1, 1)]


def splice():
    """Front splice plate across the frame joint."""
    s = box(-SPLICE[0] / 2, SPLICE[0] / 2, FRONT_SPLICE_Y - SPLICE[1] / 2, FRONT_SPLICE_Y + SPLICE[1] / 2,
            -24.0, -24.0 + SPLICE[2])
    for hu, hy in splice_holes():
        s = s.cut(csink("M3", -24.0 + SPLICE[2], hu, FRONT_SPLICE_Y + hy))
    return s


def bracket_left(y=MOUNT_Y[0]):
    """Left mounting bracket (built at +u, mirrored into place): block epoxied to the sheet beside the
    end wall, tongue through the wall window. The frame hangs on it and can't move -u or ±y."""
    b = box(BR_L_U[0], BR_L_U[1], y - BR_W / 2, y + BR_W / 2, BR_L_Z, 0.0)
    t = box(U_END - END_T - TONGUE_IN, BR_L_U[0] + 0.5, y - TONGUE_W / 2, y + TONGUE_W / 2, *TONGUE_Z)
    return b.union(t)


def bracket_right(y=MOUNT_Y[0]):
    """Right mounting bracket: block epoxied to the sheet over the frame flange; M4 nut slides in from
    the outer face, the bolt comes up through the flange."""
    s = hw.screw(MOUNT_BOLT[0])
    ub = sum(BR_R_U) / 2
    b = box(BR_R_U[0], BR_R_U[1], y - BR_W / 2, y + BR_W / 2, BR_R_Z, 0.0)
    b = b.cut(zcyl(s["clear"] / 2, BR_R_Z - 1, -8.0, ub, y))
    w = s["nut_af"] + 2 * hw.CLR
    c = s["nut_af"] / math.sqrt(3) + hw.CLR             # nut corner points along -u
    return b.cut(box(ub - c, BR_R_U[1] + 1, y - w / 2, y + w / 2, MOUNT_NUT_Z, MOUNT_NUT_Z + s["nut_h"] + 0.4))


def nut_bar():
    """Printed bar on top of a KW11 (switch frame): holds both M3 nuts so the screws can be turned from
    below. Pockets open toward the switch."""
    (x0, x1), (_, y1), (z0, z1) = KW11["body"]
    b = box(x0, x1, y1, y1 + NUT_BAR_T, z0, z1)
    for hx, hz in KW11["holes"]:
        b = b.cut(hex_nut("M3", (hx, y1 - 0.1, hz), (0, 1, 0), af=5.5 + 2 * hw.CLR, h=NUT_BAR_T - 0.3))
        b = b.cut(ycyl(hw.screw("M3")["clear"] / 2, y1 - 1, y1 + NUT_BAR_T + 1, hx, hz))
    return b


def bevel_u(z, side=1):
    """Seam bevel: right leaf keeps u >= bevel_u(z); left keeps u <= bevel_u(z, -1)."""
    u = BEVEL_C + BEVEL_H - (z - PLATE_Z[0])
    return u if side > 0 else u - SEAM_GAP


def leaf_body():
    """Right leaf before the seam bevel (closed position)."""
    zb, zt = PLATE_Z
    plate = box(-4.0, OUTER, -LEAF_Y, LEAF_Y, zb, zt)
    ri = 3.6                                             # ribs start clear of the bevel
    parts = [plate,
             box(ri, OUTER, SHELF_Y - 6.0, SHELF_Y - 0.5, RIB_Z, zb + 0.5),        # back edge beam
             box(ri, OUTER, -SHELF_Y + 0.5, -SHELF_Y + 6.0, RIB_Z, zb + 0.5),      # front edge beam
             box(ri, ri + RIB_T, -SHELF_Y + 0.5, SHELF_Y - 0.5, RIB_Z, zb + 0.5),  # inner rib
             box(OUTER - RIB_T, OUTER, -SHELF_Y + 0.5, SHELF_Y - 0.5, RIB_Z, zb + 0.5),
             box(OUTER - WALL_T, OUTER, *WALL_Y, WALL_Z, zb + 0.5)]               # striker wall
    # servo bulkhead: two pillars either side of the case, tabs screw to the +y face
    cu = max(MG995["case"][0], SERVO_CASE_L) / 2 + SERVO_CLR
    for a, b in ((ri, SERVO_U - cu), (SERVO_U + cu, OUTER - RIB_T + 0.5)):
        parts.append(box(a, b, *BULK_Y, SERVO_Z - 11.5, zb + 0.5))
    # cam for the closed switch: 45° ramp, then flat
    cu0 = CL_LEVER_U[1] - 0.3                           # full press just before the leaves meet
    cu1 = cu0 + 6.0                                      # flat: overtravel
    ramp = CAM_Y - (CL_LEVER_Y - 0.8)
    parts.append(xy_prism([(cu0 - ramp - 0.2, 55.0), (cu1, 55.0), (cu1, CAM_Y), (cu0, CAM_Y),
                           (cu0 - ramp, CL_LEVER_Y - 0.8)], WALL_Z, zb + 0.5))
    lf = union_all(parts)
    # the lever's pivot end and plunger stand ~2.5 mm off the switch: only a pad at the lever tip may
    # reach in that far, so the wall is set back over the rest of the switch
    tip_y = KW11["lever_x"][0] + END_SW[1]                # pad starts just past the plunger
    lf = lf.cut(box(OUTER - WALL_RECESS, OUTER + 1, -0.5, tip_y, -19.6, -10.4))
    # servo lead exit: notch open at the bottom, so the servo (lead fitted) still drops in from below
    c = CABLE_HOLE / 2
    lf = lf.cut(box(SERVO_U + cu, OUTER + 1, CABLE_Y - c, CABLE_Y + c, WALL_Z - 1, CABLE_Z + c))

    # servo: case clearance (pocket in the plate, window in the bulkhead) and tab screw pilots
    cz = MG995["case"][1] / 2 + SERVO_CLR
    top_z = min(MG995["case_z"][0], *(bz[0] for _, _, bz in MG995["top_cap"]))     # label plate stands proud
    lf = lf.cut(box(SERVO_U - cu, SERVO_U + cu, SERVO_Y + top_z - SERVO_CLR,
                    SERVO_Y + MG995["case_z"][1] + SERVO_CLR, SERVO_Z - cz, SERVO_Z + cz))
    tu = MG995["tab_len"] / 2 + SERVO_CLR
    tab_y0 = SERVO_Y + MG995["tab_z"][0]
    lf = lf.cut(box(SERVO_U - tu, SERVO_U + tu, tab_y0 - SERVO_CLR, BULK_Y[0], SERVO_Z - cz, SERVO_Z + cz))
    # tab root fillets on both faces: case clearance 0.5 wider for 1.2 mm either side of the tab
    lf = lf.cut(box(SERVO_U - cu - 0.5, SERVO_U + cu + 0.5, tab_y0 - 1.2, BULK_Y[0] + 1.2, SERVO_Z - 12.5, SERVO_Z + cz))
    lf = lf.cut(ycyl(R_PITCH + MOD + 0.5, RACK_Y[0], RACK_Y[1] + 2.0, SHAFT_U, SERVO_Z))   # pinion
    hx, hz = MG995["holes"]
    for su in (-1, 1):
        for sz in (-1, 1):
            hu, hzz = SERVO_U + su * hx, SERVO_Z + sz * hz
            lf = lf.cut(ycyl(hw.screw("M3")["pilot"] / 2, BULK_Y[0] - 0.1, BULK_Y[1] + 3.0, hu, hzz))
            if sz > 0:
                # upper screws sit 4 mm under the plate: head recess, and a screwdriver path out under
                # the inner rib and the front beam (the shallow front half of the leaf)
                top = hzz + DRIVER_R + 0.4
                lf = lf.cut(ycyl(3.8, tab_y0 - 3.6, tab_y0 + 0.1, hu, hzz))
                lf = lf.cut(box(hu - DRIVER_R - 0.4, hu + DRIVER_R + 0.4, -LEAF_Y - 1, tab_y0, RIB_Z - 1, top))
    return lf


def leaf(side=1):
    body = leaf_body() if side > 0 else mu(leaf_body())
    zb, zt = PLATE_Z[0] - 1.0, PLATE_Z[1] + 1.0
    if side > 0:
        cut = xz_prism([(-20, zb), (bevel_u(zb), zb), (bevel_u(zt), zt), (-20, zt)], -Y_OUT, Y_OUT)
    else:
        cut = xz_prism([(bevel_u(zb, -1), zb), (20, zb), (20, zt), (bevel_u(zt, -1), zt)], -Y_OUT, Y_OUT)
    return body.cut(cut)


def coupon():
    """Fastener test piece for plate 1 (~10 min), as the real holes print. Left to right:
    A vertical M3 pilot in a 10 mm boss (retainer/splice screws), countersink (retainers, splices),
    nut-bar pocket + clearance hole (switches), horizontal pilot through a 4 mm wall (servo tabs)."""
    s = hw.screw("M3")
    c = box(0, 44, 0, 14, 0, 3).union(box(0, 12, 0, 14, 0, 10)).union(box(36, 40, 0, 14, 0, 12))
    c = c.cut(zcyl(s["pilot"] / 2, -1, 11, 6, 7))
    c = c.cut(csink("M3", 3.0, 18, 7))
    c = c.cut(hex_nut("M3", (28, 7, 3.0 - (NUT_BAR_T - 0.3)), (0, 0, 1), af=5.5 + 2 * hw.CLR, h=NUT_BAR_T))
    c = c.cut(zcyl(s["clear"] / 2, -1, 4, 28, 7))
    return c.cut(cq.Workplane("YZ").circle(s["pilot"] / 2).extrude(6).translate((35, 7, 7)))


def parts():
    return {
        "frame_right": W(frame_half("right")),
        "frame_left": W(mu(frame_half("left"))),
        "leaf_right": W(leaf(1)),
        "leaf_left": W(leaf(-1)),
        "pinion": W(pinion()),
        "rack": W(rack()),
        "retainer_end": W(retainer("end")),
        "retainer_mid": W(retainer("mid")),
        "splice": W(splice()),
        "bracket_left": W(mu(bracket_left())),
        "bracket_right": W(bracket_right()),
        "nut_bar": nut_bar(),                            # switch frame; placed by switch_hw()
        "coupon": coupon(),                              # print-only test piece (plate 1)
    }


QTY = {"pinion": 2, "rack": 2, "retainer_end": 4, "retainer_mid": 2, "splice": 2,
       "bracket_left": 2, "bracket_right": 2, "nut_bar": 4}

# Print plan. Plate 1 is the gear test: print it first and check the mesh on a real servo.
GEARS = {"layer_height": "0.16", "initial_layer_print_height": "0.2", "wall_loops": "3"}
FRAME = {"wall_loops": "3", "sparse_infill_density": "20%"}
PLATES = [
    ("1_test_pinion_rack", ["pinion", "rack", "coupon"], GEARS),
    ("2_frame_right", ["frame_right"], FRAME),
    ("3_frame_left", ["frame_left"], FRAME),
    ("4_leaves", ["leaf_left", "leaf_right"], {"wall_loops": "3"}),
    ("5_small_parts", ["retainer_end"] * 4 + ["retainer_mid"] * 2 + ["splice"] * 2 + ["pinion", "rack"], GEARS),
    ("6_mount_parts", ["bracket_left"] * 2 + ["bracket_right"] * 2 + ["nut_bar"] * 4, {"wall_loops": "3"}),
]


def orient(name, shape):
    if name.startswith("leaf") or name == "bracket_right":
        return flip(shape)                               # plate top / glue face on the bed
    if name == "bracket_left":
        return shape.rotate((0, 0, 0), (0, 1, 0), -90)   # outer face on the bed, tongue up (no overhang)
    if name == "pinion":
        return shape.rotate((0, 0, 0), (1, 0, 0), -90)   # axis vertical, servo side down
    if name == "nut_bar":
        return shape.rotate((0, 0, 0), (1, 0, 0), -90)   # skin on the bed, nut pockets up
    return shape


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------
COLORS = {
    "frame_right": (0.30, 0.33, 0.38), "frame_left": (0.36, 0.39, 0.44),
    "leaf": (0.85, 0.55, 0.20), "pinion": (0.80, 0.30, 0.30), "rack": (0.80, 0.30, 0.30),
    "retainer": (0.55, 0.57, 0.62), "splice": (0.55, 0.57, 0.62),
    "ref_servo": (0.20, 0.45, 0.85), "ref_switch": (0.10, 0.50, 0.25), "ref_lever": (0.75, 0.75, 0.72),
    "ref_sheet": (0.80, 0.80, 0.80), "bracket": (0.86, 0.78, 0.60), "nut_bar": (0.55, 0.57, 0.62),
}


def ref_sheet():
    s = box(-SHEET[0] / 2, SHEET[0] / 2, -SHEET[1] / 2, SHEET[1] / 2, 0.0, SHEET[2])
    return s.cut(zcyl(HOLE_R, -1, 3, XC, HOLE_Y))


def leaf_hw():
    """Right leaf's fasteners (closed position, u frame): 4 tab screws from the shaft side, and the
    pinion centre screw (drawn only inside the pinion). Returns (solid, {name: screwdriver corridor})."""
    hx, hz = MG995["holes"]
    tab_y0 = SERVO_Y + MG995["tab_z"][0]
    solids, tools = [], {}
    for su in (-1, 1):
        for sz in (-1, 1):
            s, t = screw_ref("M3", (SERVO_U + su * hx, tab_y0, SERVO_Z + sz * hz), (0, 1, 0), TAB_SCREW, 7.0, 2.9)
            solids.append(s)
            tools[f"tab screw {'outer' if su > 0 else 'inner'} {'upper' if sz > 0 else 'lower'}"] = t
    y0 = PIN_Y0 + PIN_CB                                 # counterbore floor; M3 x 8 button head (1.65)
    s, t = screw_ref("M3", (SHAFT_U, y0, SERVO_Z), (0, 1, 0), SERVO_Y + MG995["spline_top_b"] - y0 - 0.1, 5.7, 1.7)
    solids.append(s)
    tools["pinion screw"] = t
    return union_all(solids), tools


def leaf_group(side, d, p=None):
    """One leaf with its servo, pinion and screws, opened by d (0 = closed, T = open)."""
    p = p or parts()
    sh = side * d
    pin = p["pinion"].rotate((XC + SHAFT_U, 0, SERVO_Z), (XC + SHAFT_U, 1, SERVO_Z), math.degrees(d / R_PITCH))
    servo = W(servo_place(ref_mg995()))
    g = {"leaf": p["leaf_right" if side > 0 else "leaf_left"], "pinion": pin, "ref_servo": servo,
         "ref_screws": W(leaf_hw()[0])}
    if side < 0:                                         # left = mirror image of the right group
        g["pinion"] = W(mu(pin.translate((-XC, 0, 0))))
        g["ref_servo"] = W(mu(servo_place(ref_mg995())))
        g["ref_screws"] = W(mu(leaf_hw()[0]))
    return {k: v.translate((sh, 0, 0)) for k, v in g.items()}


SWITCH_POS = {"end_l": lambda s: end_switch_place(s), "end_r": lambda s: mu(end_switch_place(s)),
              "closed_r": lambda s: closed_switch_place(s), "closed_l": lambda s: mu(closed_switch_place(s))}


def switch_hw(tag):
    """One switch's nut bar, screws, nuts and screwdriver corridors (from below), world placed."""
    kind = tag.split("_")[0]
    z_sw = (END_SW if kind == "end" else CLOSED_SW)[2]  # switch frame y -> world z - z_sw
    y1 = KW11["body"][1][1]
    seat = Z_BOT + 3.0 - z_sw                            # counterbore floor (cbore_up depth 3)
    screws, nuts, tools = [], [], []
    for hx, hz in KW11["holes"]:
        s, t = screw_ref("M3", (hx, seat, hz), (0, 1, 0), SW_SCREW[kind], 5.5, 3.0)
        screws.append(s)
        nuts.append(hex_nut("M3", (hx, y1, hz), (0, 1, 0)))
        tools.append(t)
    place = SWITCH_POS[tag]
    return dict(bar=W(place(nut_bar())), screws=W(place(union_all(screws))), nuts=W(place(union_all(nuts))),
                tools=[W(place(t)) for t in tools])


def mount_hw():
    """Right-end M4 bolts, nuts and screwdriver corridors (from below), world placed."""
    size, length, hh = MOUNT_BOLT
    ub = sum(BR_R_U) / 2
    bolts, nuts, tools = [], [], []
    for y in MOUNT_Y:
        s, t = screw_ref(size, (ub, y, Z_BOT + hh + 0.3), (0, 0, 1), length, 7.0, hh)
        bolts.append(W(s))
        nuts.append(W(hex_nut(size, (ub, y, MOUNT_NUT_Z + 0.2), (0, 0, 1))))
        tools.append(W(t))
    return dict(bolts=bolts, nuts=nuts, tools=tools)


def brackets(p=None):
    p = p or parts()
    out = {}
    for y in MOUNT_Y:
        out[f"l{int(y)}_bracket"] = W(mu(bracket_left(y)))
        out[f"r{int(y)}_bracket"] = W(bracket_right(y))
    return out


def static_parts(p=None, mount=True):
    """Everything fixed: frame, racks, retainers, splices, switch hardware, and (mount=True) the
    brackets and mounting bolts."""
    p = p or parts()
    out = {"frame_right": p["frame_right"], "frame_left": p["frame_left"],
           "rack_right": p["rack"], "rack_left": W(mu(p["rack"].translate((-XC, 0, 0))))}
    re, rm = p["retainer_end"].translate((-XC, 0, 0)), p["retainer_mid"].translate((-XC, 0, 0))
    for tag, s in (("end_fr", re), ("end_fl", mu(re)), ("end_br", my(re)), ("end_bl", mu(my(re))),
                   ("mid_f", rm), ("mid_b", my(rm))):
        out[f"retainer_{tag}"] = W(s)
    sp = p["splice"].translate((-XC, 0, 0))
    out["splice_f"] = W(sp)
    out["splice_b"] = W(my(sp).translate((0, BACK_SPLICE_Y + FRONT_SPLICE_Y, 0)))
    for tag in SWITCH_POS:
        h = switch_hw(tag)
        out[f"{tag}_nut_bar"] = h["bar"]
        out[f"ref_screw_sw_{tag}"] = h["screws"].union(h["nuts"])
    if mount:
        out.update(brackets(p))
        out["ref_screw_mount"] = union_all(mount_hw()["bolts"] + mount_hw()["nuts"])
    return out


def switches(lever=True):
    """The four KW11s: (body, lever) per position."""
    out = {}
    for tag, place in SWITCH_POS.items():
        out[f"ref_switch_{tag}"] = W(place(ref_kw11(lever=False)))
        if lever:
            out[f"ref_lever_{tag}"] = W(place(ref_kw11_lever()))
    return out


def assembly(d_right=0.0, d_left=0.0, p=None):
    p = p or parts()
    a = {**static_parts(p), **switches(), "ref_sheet": ref_sheet()}
    for side, d, tag in ((1, d_right, "right"), (-1, d_left, "left")):
        for k, v in leaf_group(side, d, p).items():
            a[f"{tag}/{k}"] = v
    return a


# By design: the pinion is pressed on the spline; the cam/striker press the switch levers;
# the leaf plate rests 0.1 above the shelf.
CLASH_IGNORE = [("right/pinion", "right/ref_servo"), ("left/pinion", "left/ref_servo"),
                ("right/leaf", "ref_lever_closed_r"), ("left/leaf", "ref_lever_closed_l")]


# --------------------------------------------------------------------------
# Views and checks
# --------------------------------------------------------------------------
def views(parts_, asm):
    from cadkit.render import ISO_FRONT, TOP, section
    opened = assembly(T, T, parts_)
    no_sheet = {k: v for k, v in asm.items() if k != "ref_sheet"}
    no_sheet_open = {k: v for k, v in opened.items() if k != "ref_sheet"}
    under = (-0.6, -1.0, -0.9)
    sec_x = section(no_sheet, "x", XC + SHAFT_U, keep="below")
    sec_y = section({k: v for k, v in no_sheet.items() if "right" in k}, "y", -56.8, keep="below")
    sec_sw = section(no_sheet, "z", -17.0, keep="below")
    near = {k: v for k, v in assembly(6.0, 6.0, parts_).items() if k != "ref_sheet"}
    sw_detail = section(section(near, "x", XC + 70, keep="below"), "x", XC + 5, keep="above")
    sec_mount = section(asm, "y", MOUNT_Y[0], keep="above")
    left_end = section(sec_mount, "x", XC - 120, keep="below")
    right_sec = section(sec_mount, "x", XC + 120, keep="above")
    right_end = section(no_sheet, "x", XC + 100, keep="above")
    return [
        ("section_mount_left.png", left_end, (0, -1, 0.05), 1.3),
        ("section_mount_right.png", right_sec, (0, -1, 0.05), 1.3),
        ("mount_right_under.png", right_end, (0.8, -0.7, -0.8), 1.3),
        ("closed_top.png", asm, TOP, 1.1),
        ("open_top.png", opened, TOP, 1.1),
        ("closed_under.png", no_sheet, under, 1.15),
        ("open_under.png", no_sheet_open, under, 1.15),
        ("open_iso.png", no_sheet_open, ISO_FRONT, 1.15),
        ("section_servo_x.png", sec_x, (1, 0, 0.05), 1.4),
        ("section_rack_y.png", sec_y, (0, 1, 0.05), 1.6),
        ("closed_switch_6mm_before.png", sw_detail, (0.3, 0.6, -1), 1.6),
        ("section_z17_closed.png", sec_sw, (0, -0.05, -1), 1.1),
    ]


def checks(parts_, asm):
    from cadkit.check import overlap_volume, sweep
    ok = True
    p = parts_
    static = {**static_parts(p), **switches(lever=False)}

    # 1. sweep each leaf group closed -> open (pinion rolls on its rack) plus 5 mm past open
    #    up to the hard stop
    for side, tag in ((1, "right"), (-1, "left")):
        d_max = END_STOP_U - OUTER - 0.1                 # up to the hard stop
        steps = [round(i * d_max / 23, 2) for i in range(24)]
        found = sweep(lambda d: leaf_group(side, d, p), static, steps, tol=0.5, verbose=False)
        print(f"Sweep {tag} leaf 0..{steps[-1]} mm: " + ("clear" if not found else f"{len(found)} hits"))
        for st, mn, sn, v in found[:8]:
            print(f"   d={st}: {mn} x {sn}: {v:.2f} mm^3")
        ok &= not found

    # 2. leaves never touch each other while both move
    for d in (0.0, 2.0, 10.0):
        v = overlap_volume(leaf_group(1, d, p)["leaf"], leaf_group(-1, d, p)["leaf"])
        if v > 0.01:
            print(f"Leaves overlap at d={d}: {v:.2f}")
            ok = False

    # 3. open: nothing inside the drop path (Ø120 hole extruded down)
    path = W(zcyl(HOLE_R, Z_BOT - 1, -0.01, 0, HOLE_Y))
    hits = {k: overlap_volume(v, path) for k, v in assembly(T, T, p).items() if k != "ref_sheet"}
    hits = {k: v for k, v in hits.items() if v > 0.01}
    print("Drop path when open: " + ("clear" if not hits else str(hits)))
    ok &= not hits

    # 4. closed: the leaves cover the whole hole (sampled from above)
    lr, ll = leaf_group(1, 0, p)["leaf"].val(), leaf_group(-1, 0, p)["leaf"].val()
    miss, n = [], 0
    for i in range(-60, 61, 3):
        for j in range(-60, 61, 3):
            if i * i + j * j > HOLE_R ** 2:
                continue
            n += 1
            pts = [cq.Vector(XC + i, HOLE_Y + j, z) for z in (PLATE_Z[0] + 0.3, PLATE_Z[1] - 0.3)]
            if not any(s.isInside(q) for s in (lr, ll) for q in pts):
                miss.append((i, j))
    print(f"Closed coverage: {n - len(miss)}/{n} points covered" + (f", missing {miss[:6]}" if miss else ""))
    ok &= not miss

    # 5. switches: pressed at the end positions, free in between
    lev = switches()
    def press(d_r, key):
        return overlap_volume(leaf_group(1, d_r, p)["leaf"], lev[key])
    rows = [("closed_r @closed", press(0, "ref_lever_closed_r") > 0.05),
            ("closed_r free @8mm", press(8, "ref_lever_closed_r") < 0.01),
            ("end_r @open", press(T, "ref_lever_end_r") > 0.05),
            ("end_r free @open-6", press(T - 6, "ref_lever_end_r") < 0.01)]
    print("Switches: " + ", ".join(f"{n} {'ok' if g else 'FAIL'}" for n, g in rows))
    print(f"   end switch: lever free tip u={END_LEVER_U:.2f}, leaf face at open u={OUTER + T:.2f} "
          f"(press {OUTER + T - END_LEVER_U:.2f}), hard stop u={END_STOP_U:.2f}")
    print(f"   closed switch: lever tip y={CL_LEVER_Y:.2f}, cam y={CAM_Y:.2f} (press {CAM_Y - CL_LEVER_Y:.2f})")
    ok &= all(g for _, g in rows)

    # 6. hard stop: 0.5 mm past the stop hits the pedestal, never the switch body
    d_stop = END_STOP_U - OUTER + 0.5
    g = leaf_group(1, d_stop, p)["leaf"]
    hit_ped = overlap_volume(g, static["frame_right"]) > 0.05
    hit_body = overlap_volume(g, static["ref_switch_end_r"]) > 0.01
    print(f"Hard stop at d={d_stop:.1f}: pedestal {'hit' if hit_ped else 'MISSED'}, switch body "
          f"{'HIT' if hit_body else 'clear'}")
    ok &= hit_ped and not hit_body

    # 7. captive: lifting the leaf 0.6 mm hits the retainers; dropping it 0.2 hits the shelf
    lf = leaf_group(1, 20, p)["leaf"]
    up = sum(overlap_volume(lf.translate((0, 0, 0.6)), v) for k, v in static.items() if k.startswith("retainer"))
    dn = overlap_volume(lf.translate((0, 0, -0.2)), static["frame_right"])
    print(f"Leaf captive: lift 0.6 -> retainers {up:.1f} mm^3, drop 0.2 -> shelf {dn:.1f} mm^3")
    ok &= up > 0.1 and dn > 0.1

    # 8. gear mesh: centre distance and pinion/rack overlap at both ends
    cd = SERVO_Z - PITCH_Z
    mesh = [overlap_volume(leaf_group(1, d, p)["pinion"], p["rack"]) for d in (0, T / 2, T)]
    print(f"Mesh: centre distance {cd:.3f} (pitch r {R_PITCH}), pinion x rack overlap "
          + ", ".join(f"{v:.3f}" for v in mesh) + " mm^3")
    ok &= abs(cd - R_PITCH) < 1e-6 and max(mesh) < 0.5

    # --- assembly feasibility: every part can get in, every screw can be reached (2026-10-25) ---
    def hits(moving, fixed, ignore=()):
        return [(a, b, round(v, 2)) for a, s in moving.items() for b, t in fixed.items()
                if (a, b) not in ignore and (v := overlap_volume(s, t)) > 0.05]

    # 9. servo drops into the leaf from below (leaf upside down on the bench)
    lf = {"leaf": p["leaf_right"]}
    found = [h for dz in (-40, -20, -10, -5, -2, -0.5)
             for h in hits({"servo": W(servo_place(ref_mg995())).translate((0, 0, dz))}, lf)]
    print("Servo into leaf from below: " + ("clear" if not found else str(found[:4])))
    ok &= not found

    # 10. screwdriver corridors for the leaf screws (bench: leaf + servo + pinion)
    bench = {"leaf": p["leaf_right"], "servo": W(servo_place(ref_mg995())), "pinion": p["pinion"]}
    _, tools = leaf_hw()
    bad = {k: hits({k: W(t)}, bench) for k, t in tools.items()}
    bad = {k: v for k, v in bad.items() if v}
    print("Leaf screws reachable (Ø5 x 60 driver): " + ("all 5" if not bad else str(bad)))
    ok &= not bad

    # 11. leaves drop into the frame from above (switches + nut bars fitted, no retainers yet)
    fixed = {k: v for k, v in {**static_parts(p, mount=False), **switches()}.items()
             if not k.startswith("retainer")}
    found = []
    for side in (1, -1):
        for dz in (40, 20, 10, 5, 2, 0.5):
            g = {k: v.translate((0, 0, dz)) for k, v in leaf_group(side, T / 2, p).items()}
            found += hits(g, fixed)
    print("Leaves drop in at mid travel: " + ("clear" if not found else str(found[:4])))
    ok &= not found

    # 12. mounting: lift the unit MOUNT_SLIDE right of its place, slide it left onto the tongues
    unit = {k: v for k, v in assembly(0, 0, p).items()
            if k != "ref_sheet" and not k.endswith("bracket") and k != "ref_screw_mount"}
    fixed = {**brackets(p), "ref_sheet": ref_sheet()}
    path = [(MOUNT_SLIDE, z) for z in (-40, -20, -10, -2, -0.5, 0)] + [(s, 0) for s in (8, 5, 2, 0.5)]
    found = []
    for dx, dz in path:
        found += [(dx, dz) + h for h in hits({k: v.translate((dx, 0, dz)) for k, v in unit.items()}, fixed)]
    print(f"Mounting path (up at +{MOUNT_SLIDE:.0f} mm, slide left): " + ("clear" if not found else str(found[:4])))
    print(f"   tongue engagement {END_T + TONGUE_IN:.1f} mm, left bracket {BR_L_U[1] - BR_L_U[0]:.1f} mm thick "
          f"({U_SHEET_L - BR_L_U[1]:.1f} to the sheet edge), right bracket ends {U_SHEET_R - BR_R_U[1]:.1f} "
          f"from its edge")
    ok &= not found

    # 12b. held once mounted: each frame half hits its brackets/bolts when pushed down or sideways
    #      (a clear path alone would also pass for a mount that holds nothing)
    held = {**brackets(p), "bolts": union_all(mount_hw()["bolts"]), "ref_sheet": ref_sheet()}
    def blocked(name, dx, dz, by):
        s = p[name].translate((dx, 0, dz))
        return sum(overlap_volume(s, v) for k, v in held.items() if by in k) > 0.05
    rows = [("left down 0.5 -> tongues", blocked("frame_left", 0, -0.5, "l")),
            ("left -x 0.5 -> brackets", blocked("frame_left", -0.5, 0, "l")),
            ("left up 0.5 -> sheet", blocked("frame_left", 0, 0.5, "sheet")),
            ("right down 0.5 -> bolts", blocked("frame_right", 0, -0.5, "bolts")),
            ("right +x 3 -> bolts", blocked("frame_right", 3.0, 0, "bolts")),
            ("right up 0.5 -> sheet", blocked("frame_right", 0, 0.5, "sheet"))]
    print("Mount holds: " + ", ".join(f"{n} {'ok' if g else 'FAIL'}" for n, g in rows))
    ok &= all(g for _, g in rows)

    # 13. reachable once mounted, from below: switch screws (re-tuning) and the right mount bolts
    every = {**assembly(0, 0, p), **{f"o/{k}": v for k, v in assembly(T, T, p).items() if "/" in k}}
    corr = {f"switch {tag} #{i}": t for tag in SWITCH_POS for i, t in enumerate(switch_hw(tag)["tools"])}
    corr.update({f"mount bolt #{i}": t for i, t in enumerate(mount_hw()["tools"])})
    bad = {k: hits({k: t}, every) for k, t in corr.items()}
    bad = {k: v for k, v in bad.items() if v}
    print(f"Reachable from below when mounted ({len(corr)} screws): " + ("all" if not bad else str(bad)))
    ok &= not bad

    # 14. self-tapping holes: >= 1.2 mm of plastic round the M3 thread over the whole bite, the bite
    #     >= 4 mm, and the screw tip >= 0.5 mm off the bottom of a blind pilot
    fr, lfb = frame_half("right"), leaf_body()
    r_thr, r_pil = 1.5, hw.screw("M3")["pilot"] / 2
    sites = []                                           # (name, part, axis, a, b = bite, pilot end)
    for uh in [u for u in retainer_holes() if 0 < u < U_END]:
        sites.append((f"retainer u{uh:.0f}", fr, "z", (uh, -RET_HOLE_Y), RET_Z, -10.0, RET_Z - 10))
    for hu, hy in splice_holes():
        if hu > 0:
            sites.append((f"splice u{hu:.0f} y{hy:+.0f}", fr, "z", (hu, FRONT_SPLICE_Y + hy), -24.0, -29.0, Z_BOT - 1))
    hx, hz = MG995["holes"]
    for su in (-1, 1):
        for sz in (-1, 1):
            sites.append((f"servo tab {su:+d}{sz:+d}", lfb, "y", (SERVO_U + su * hx, SERVO_Z + sz * hz),
                          BULK_Y[0], BULK_Y[1], BULK_Y[1] + 3.0))
    bad = []
    for name, part, ax, (c0, c1), a, b, end in sites:
        cyl = (lambda r, p, q: zcyl(r, min(p, q), max(p, q), c0, c1)) if ax == "z" else \
              (lambda r, p, q: ycyl(r, min(p, q), max(p, q), c0, c1))
        thin = cyl(r_thr + 1.2, a, b).cut(part).cut(cyl(r_pil, a - 20, a + 20)).val().Volume()
        bite = abs(b - a)
        margin = abs(end - b)
        if thin > 0.05 or bite < 4.0 or margin < 0.5:
            bad.append(f"{name}: thin {thin:.2f} mm^3, bite {bite:.1f}, tip margin {margin:.1f}")
    print(f"Self-tap holes ({len(sites)} kinds): " + ("walls >= 1.2, bite >= 4, no bottoming" if not bad else str(bad)))
    ok &= not bad

    # 15. servo lead (2026-11-01): a grommet-sized path straight from the servo's outer end out through
    #     the end wall is clear closed and open, and never inside the drop path
    (gx0, _), (gy0, gy1), (gz0, gz1) = MG995["grommet"]
    tip = SERVO_U - gx0
    drop = W(zcyl(HOLE_R, Z_BOT - 1, -0.01, 0, HOLE_Y))
    bad = []
    for d in (0.0, T):
        lead = W(box(tip + d, U_END + 2, SERVO_Y + gz0, SERVO_Y + gz1, SERVO_Z + gy0, SERVO_Z + gy1))
        near = {**static, "leaf": leaf_group(1, d, p)["leaf"], "drop path": drop}
        bad += [(d, k, round(v, 2)) for k, s in near.items() if (v := overlap_volume(lead, s)) > 0.01]
    print("Servo lead out through the end wall: " + ("clear closed and open" if not bad else str(bad)))
    ok &= not bad
    return ok

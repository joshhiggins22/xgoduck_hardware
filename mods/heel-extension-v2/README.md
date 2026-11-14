# V2 whole-foot heel extension (+15 mm)

A monolithic replacement for the **V2_STANDARD** foot that extends the heel **15 mm
rearward** to add backward support and stop the duck tipping backward at the end of
stand-up (head-lift). Built by mesh-boolean from the stock STL (no STEP needed). The
ankle/servo hub is **untouched**; the rear TPU-pad screw holes are **preserved**.

> Supersedes the earlier clip-on and the RL-sim-based `whole_foot_*` (those used the wrong
> foot geometry). This one is built on the actual hardware foot:
> `structure/V2_STANDARD_/V2_STANDARD_LEFT_FOOT.stl` / `..._RIGHT_FOOT.stl`.

## Files (units = mm, print-ready)
| File | Print | Material | Mass |
|---|---|---|---|
| `v2_whole_foot_left.stl`  | 1× | PLA / PETG | ~26 g |
| `v2_whole_foot_right.stl` | 1× | PLA / PETG | ~26 g |
| `v2_whole_foot.py`        | —  | generator (CadQuery + trimesh/manifold) | |
| `v2_whole_foot_views.png` | —  | render (top/side/iso + heel close-up) | |

## Geometry
- Heel edge moves from `x = -27 mm` to `x = -42 mm` (**+15 mm** rearward). Toe unchanged.
- Extension is a rounded, sole-matched plate (~37 mm wide, 8 mm thick) unioned only into the
  heel pad — ~20 mm clear of the ankle hub, so the hub stays clean.
- Rear ski-tip bevel to ride over carpet instead of catching.
- Both rear TPU-pad screw holes re-opened after the union (verified: Euler number matches stock).

## Verified
- Watertight, single body, winding-consistent (both feet).
- Heel `x_min = -42.0 mm`; hole count matches stock (no filled screw holes).
- Visual inspection: hub intact, heel reads as a deliberate sole extension, no spikes/self-intersections.
- Minor cosmetic note: a small step at the heel/body top junction (does not affect the flat
  ground-contact surface).

## How to attach
Replaces the stock V2 foot at the **same servo-horn / ankle-axis interface** — the hub is
byte-identical to stock, so it mounts exactly like the original. The rear TPU-pad screw holes
are preserved, so the stock `FOOT_BOTTOM_TPU` pad still screws on (it covers the original sole;
the new 15 mm heel is bare PLA — add a glue-on TPU strip there if you want grip on carpet).

## Print (Bambu / H2C-class FDM)
- PLA or PETG, 0.20 mm layer, **sole-down**, 3–4 perimeters, 25–30% infill.
- Supports only if your slicer flags the hub/arch overhang; the heel bevel is self-supporting.

## Regenerate / tune
```
python v2_whole_foot.py --ext 15 --width 37     # sweep --ext 8..20, --width 30..40
```
Requires `cadquery`, `trimesh`, `manifold3d`. Reads the stock feet from `structure/V2_STANDARD_/`.

## Caveat
The RL simulation uses a *different* foot mesh, so the sim's exact margin numbers do not transfer.
This adds 15 mm of real rearward support — **test on the physical duck** (bench-press the heel,
then a careful stand-up) to confirm it clears the backward tip.

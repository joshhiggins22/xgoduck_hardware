# V2 whole-foot heel extension (+15 mm) + matching TPU pad

A monolithic replacement for the **V2_STANDARD** foot that extends the heel **15 mm
rearward** to add backward support and stop the duck tipping backward at the end of
stand-up (head-lift), plus an **updated TPU sole pad** that covers the new heel. Built by
mesh-boolean from the stock STLs (no STEP needed). The ankle/servo hub is **untouched**;
screw holes are **preserved**.

> Supersedes the earlier clip-on and the RL-sim-based `whole_foot_*` (wrong foot geometry).
> Built on the actual hardware: `structure/V2_STANDARD_/V2_STANDARD_LEFT_FOOT.stl` /
> `..._RIGHT_FOOT.stl` and `..._2x_FOOT_BOTTOM_TPU_01.stl`.

## Files (units = mm, print-ready)
| File | Print | Material | Mass |
|---|---|---|---|
| `v2_whole_foot_left.stl`  | 1× | PLA / PETG | ~28 g |
| `v2_whole_foot_right.stl` | 1× | PLA / PETG | ~28 g |
| `v2_tpu_pad.stl`          | 2× | TPU | ~18 g each |
| `v2_whole_foot.py` / `v2_tpu_pad.py` | — | generators (CadQuery + trimesh/manifold) | |
| `v2_whole_foot_views.png` / `v2_tpu_pad_views.png` | — | renders | |

## Geometry (reworked per feedback)
- Heel edge `x = -27 → -42 mm` (**+15 mm** rearward). Toe unchanged.
- **Full width (~39.7 mm), same as the foot — no rear taper.** Rear edge is blunt/full-width
  with only small corner radii (no ski-tip bevel, no narrowing).
- Extension is **sole-matched in height** and its top **blends up into the foot's sole**, so
  the heel flows into the foot instead of stepping down. Unioned only into the heel pad,
  ~20 mm clear of the ankle hub (hub stays clean).
- TPU pad extended the same 15 mm, full width, to cover the new heel (no bare-PLA heel).
- Rear screw holes re-opened after each union (verified: Euler number matches stock).

## Verified
- Watertight, single body, winding-consistent (feet + pad).
- Heel `x_min = -42.0 mm`; hole count matches stock (no filled screw holes).
- Pad footprint matches the foot (overlay checked); front pad screws align with the foot
  (~0.05 mm); rear pad holes match the stock pad position.
- Visual inspection: hub intact, full-width untapered heel, smooth blend, no spikes/self-intersections.

## How to attach
- **Foot:** replaces the stock V2 foot at the **same servo-horn / ankle-axis interface** — the
  hub is byte-identical to stock, so it mounts exactly like the original.
- **Pad:** the updated `v2_tpu_pad.stl` replaces the stock `FOOT_BOTTOM_TPU` (print 2). It
  mounts like the stock pad (front screws align with the foot; rear matches stock).

## Print (Bambu / H2C-class FDM)
- **Feet:** PLA or PETG, 0.20 mm, **sole-down**, 3–4 perimeters, 25–30% infill. Supports only
  if the slicer flags the hub/arch overhang.
- **Pad:** TPU, 0.20 mm, flat, no supports.

## Regenerate / tune
```
python v2_whole_foot.py --ext 15 --width 39.7   # sweep --ext 8..20
python v2_tpu_pad.py    --ext 15 --width 40
```
Requires `cadquery`, `trimesh`, `manifold3d`. Reads stock parts from `structure/V2_STANDARD_/`.

## Caveat
The RL simulation uses a *different* foot mesh, so the sim's exact margin numbers do not transfer.
This adds 15 mm of real rearward support — **test on the physical duck** (bench-press the heel,
then a careful stand-up) to confirm it clears the backward tip.

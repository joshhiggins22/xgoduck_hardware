#!/usr/bin/env python3
"""Clean whole-foot heel extension for the XgoDuck V2_STANDARD foot (the real hardware).

Base: structure/V2_STANDARD_/V2_STANDARD_LEFT_FOOT.stl (and RIGHT). Heel is the -x end
(x=-27); ankle hub is at x~-7, so the extension stays ~20mm clear of the hub. We extend
the heel sole rearward by `--ext` mm with a rounded, sole-matched plate (NOT a crude block),
unioned only into the heel pad. Units mm. Outputs print-ready STL per side.
"""
import argparse, os, tempfile
import numpy as np
import trimesh
import cadquery as cq

HW = "/home/joshhiggins/workspace/xgoduck_hardware/structure/V2_STANDARD_"
OUT = os.path.dirname(os.path.abspath(__file__))

def build_extension(ext, width, sole_top=8.0, corner_r=5.0, bevel=2.0):
    heel_x = -27.0
    x_rear = heel_x - ext          # new heel edge
    x_front = -19.0                # overlap 8mm into the existing heel pad
    hw = width / 2.0
    # rounded rectangular sole plate (fillet the vertical corner edges)
    plate = (cq.Workplane("XY")
             .center((x_rear + x_front) / 2.0, 0)
             .rect(x_front - x_rear, width)
             .extrude(sole_top)
             .edges("|Z").fillet(corner_r))
    # rear ski-tip bevel: cut a wedge off the rear-bottom edge so it rides over carpet
    if bevel > 0:
        wedge = (cq.Workplane("XY")
                 .center(x_rear + bevel / 2.0, 0)
                 .rect(bevel + 2, width + 4)
                 .extrude(sole_top + 2))
        # slope the wedge: keep only material above the bevel plane at the rear
        # simpler: chamfer the rear-bottom edge of the plate
        try:
            plate = plate.edges("<X and <Z").chamfer(bevel)
        except Exception:
            pass
    return plate

def to_trimesh(shape):
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
        cq.exporters.export(shape, f.name, tolerance=0.03, angularTolerance=0.1)
        m = trimesh.load(f.name)
    os.unlink(f.name)
    return m

def rear_holes(mesh):
    """Detect the small rear corner screw-holes (x<-15) in the sole; return (cx,cy,r)."""
    sec = mesh.section(plane_origin=[0, 0, 3.0], plane_normal=[0, 0, 1])
    p = sec.to_planar()[0]
    holes = []
    for e in p.entities:
        pts = p.vertices[e.points]
        cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
        r = np.linalg.norm(pts - [cx, cy], axis=1).mean()
        if e.closed and r < 3.0 and cx < -15.0:   # small rear holes only
            holes.append((cx, cy, r))
    return holes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ext", type=float, default=15.0)
    ap.add_argument("--width", type=float, default=37.0)
    args = ap.parse_args()

    ext_mesh = to_trimesh(build_extension(args.ext, args.width))
    print("extension bounds:", np.round(ext_mesh.bounds, 2).tolist(),
          "watertight:", ext_mesh.is_watertight)

    for side, fn in [("left", "V2_STANDARD_LEFT_FOOT.stl"),
                     ("right", "V2_STANDARD_RIGHT_FOOT.stl")]:
        base = trimesh.load(os.path.join(HW, fn))
        holes = rear_holes(base)
        union = trimesh.boolean.union([base, ext_mesh], engine="manifold")
        # re-open any rear screw-holes the overlap plate covered
        cutters = []
        for (cx, cy, r) in holes:
            cyl = trimesh.creation.cylinder(radius=r + 0.3, height=14.0, sections=48)
            cyl.apply_translation((cx, cy, 4.0))
            cutters.append(cyl)
        if cutters:
            union = trimesh.boolean.difference([union] + cutters, engine="manifold")
        union.merge_vertices()
        b = union.bounds
        out = os.path.join(OUT, f"v2_whole_foot_{side}.stl")
        union.export(out)
        print(f"[{side}] rear_holes={[(round(a,1),round(b_,1)) for a,b_,_ in holes]} "
              f"stock_euler={base.euler_number} new_euler={union.euler_number}")
        print(f"[{side}] watertight={union.is_watertight} winding={union.is_winding_consistent} "
              f"bodies={union.body_count}")
        print(f"[{side}] bbox {np.round(b,2).tolist()} heel_xmin={b[0][0]:.2f} "
              f"gain=+{(-27.0)-b[0][0]:.2f}mm vol={union.volume/1000:.1f}cm3 "
              f"PLA={union.volume/1000*1.24:.1f}g -> {out}")

if __name__ == "__main__":
    main()

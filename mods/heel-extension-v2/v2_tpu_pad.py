#!/usr/bin/env python3
"""Updated TPU sole pad for the V2 whole-foot heel extension. Extends the stock
FOOT_BOTTOM_TPU pad 15mm rearward (full width, no rear taper) to cover the new heel.
Pad is identical left/right -> one STL, print 2. Preserves the rear screw holes."""
import argparse, os, tempfile
import numpy as np
import trimesh
import cadquery as cq

HW = "/home/joshhiggins/workspace/xgoduck_hardware/structure/V2_STANDARD_"
OUT = os.path.dirname(os.path.abspath(__file__))
PAD = os.path.join(HW, "V2_STANDARD_2x_FOOT_BOTTOM_TPU_01.stl")

def build_extension(ext, width, sole_top=5.8, corner_r=2.5, blend_top=7.2):
    heel_x = -27.0
    x_rear = heel_x - ext
    x_front = -19.0
    x_blend = -26.0
    pts = [(x_rear,0.0),(x_front,0.0),(x_front,blend_top),(x_blend,sole_top),(x_rear,sole_top)]
    plate = (cq.Workplane("XZ").polyline(pts).close().extrude(width/2.0, both=True))
    try:
        plate = plate.edges("|Z").fillet(corner_r)
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
    sec = mesh.section(plane_origin=[0,0,3.0], plane_normal=[0,0,1])
    p = sec.to_planar()[0]
    holes=[]
    for e in p.entities:
        pts=p.vertices[e.points]; cx,cy=pts[:,0].mean(),pts[:,1].mean()
        r=np.linalg.norm(pts-[cx,cy],axis=1).mean()
        if e.closed and r<3.0 and cx<-15.0:
            holes.append((cx,cy,r))
    return holes

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ext",type=float,default=15.0)
    ap.add_argument("--width",type=float,default=40.0)
    args=ap.parse_args()
    base=trimesh.load(PAD)
    ext=to_trimesh(build_extension(args.ext,args.width))
    holes=rear_holes(base)
    union=trimesh.boolean.union([base,ext],engine="manifold")
    cutters=[]
    for (cx,cy,r) in holes:
        c=trimesh.creation.cylinder(radius=r+0.3,height=14.0,sections=48)
        c.apply_translation((cx,cy,4.0)); cutters.append(c)
    if cutters:
        union=trimesh.boolean.difference([union]+cutters,engine="manifold")
    union.merge_vertices()
    out=os.path.join(OUT,"v2_tpu_pad.stl"); union.export(out)
    b=union.bounds
    print(f"rear_holes={[(round(a,1),round(b_,1)) for a,b_,_ in holes]}")
    print(f"stock_euler={base.euler_number} new_euler={union.euler_number}")
    print(f"watertight={union.is_watertight} winding={union.is_winding_consistent} bodies={union.body_count}")
    print(f"bbox {np.round(b,2).tolist()} heel_xmin={b[0][0]:.2f} gain=+{(-27.0)-b[0][0]:.2f}mm "
          f"vol={union.volume/1000:.2f}cm3 TPU={union.volume/1000*1.20:.1f}g -> {out}")

if __name__=="__main__":
    main()

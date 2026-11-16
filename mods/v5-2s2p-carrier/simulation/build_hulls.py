"""Regenerate enclosure floor-contact support points from installed-pose CAD in millimeters."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull
import trimesh

HERE = Path(__file__).resolve().parent
# The print spindle axis Z points toward the robot's front.
PRINT_TO_TRUNK = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])


def placed(path, offset):
    mesh = trimesh.load_mesh(path)
    return mesh.vertices @ PRINT_TO_TRUNK.T + offset


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("hardware", type=Path, help="Root of joshhiggins22/xgoduck_hardware")
    p.add_argument("--cad", type=Path, default=HERE.parent)
    p.add_argument("--out", type=Path, default=HERE / "floor_hulls.json")
    a = p.parse_args()
    v5 = a.hardware / "structure" / "V5_AUDIO_VIDEO_"
    cover = placed(
        v5 / "V5_AUDIO_VIDEO_ENCLOSURE_FOR_V1P1.stl", [-60.506, -0.01, -30.497]
    )
    original = placed(v5 / "V5_AUDIO_VIDEO_BATTERY.stl", [-35.986, 0.055, -29.837])
    modified = placed(a.cad / "V5_2S2P_carrier.stl", [-56.486, 0.055, -29.837])
    keeper = placed(a.cad / "V5_2S2P_keeper.stl", [-11.486, -0.003, -33.337])
    shells = {"v5": (cover, original), "2s2p": (cover - [20.5, 0, 0], modified, keeper)}
    out = {}
    for name, parts in shells.items():
        points = np.concatenate(parts)
        hull = points[ConvexHull(points).vertices]
        out[name] = np.unique(hull.round(4), axis=0).tolist()
    a.out.write_text(json.dumps(out, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()

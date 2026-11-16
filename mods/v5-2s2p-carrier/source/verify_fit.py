"""Check the Fusion print STLs against a rigid nominal pack and the stock V5 holder."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

PACKAGE = Path(__file__).resolve().parents[1]


def load(path):
    part = trimesh.load_mesh(path)
    occurrences = np.bincount(part.edges_unique_inverse)
    if not part.is_volume or part.body_count != 1 or not np.all(occurrences == 2):
        raise ValueError(f"{path} must be one closed, positively oriented solid")
    solid = mf.Manifold(
        mf.Mesh(part.vertices.astype("float32"), part.faces.astype("uint32"))
    )
    if solid.status() != mf.Error.NoError:
        raise ValueError(solid.status())
    return part, solid


def block(minimum, maximum):
    return mf.Manifold.cube(np.array(maximum) - minimum).translate(minimum)


def measure(part):
    return {
        "volume_mm3": part.volume,
        "center_mm": part.center_mass.tolist(),
        "inertia_about_own_com_m2_per_kg": (
            part.moment_inertia / part.volume * 1e-6
        ).tolist(),
        "bounds_mm": part.bounds.tolist(),
        "watertight": part.is_watertight,
        "components": part.body_count,
    }


def loops(part, z):
    section = part.section([0, 0, 1], [0, 0, z])
    values = []
    for loop in section.discrete:
        points = loop[:, :2]
        xy_min = points.min(axis=0)
        diameters = np.ptp(points, axis=0)
        values.append((xy_min + diameters / 2, diameters))
    return values


def compare_mounts(
    stock, carrier, stock_plane, carrier_plane, diameter_range, count, target_xy=None
):
    candidates = [
        (center, diameter)
        for center, diameter in loops(stock, stock_plane)
        if np.all(diameter > diameter_range[0]) and np.all(diameter < diameter_range[1])
    ]
    if target_xy is not None:
        candidates = [
            (center, d)
            for center, d in candidates
            if np.linalg.norm(center - target_xy) < 0.1
        ]
    assert len(candidates) == count, (candidates, count)
    result = []
    destination = loops(carrier, carrier_plane)
    for center, expected_diameter in candidates:
        near = [(xy, d) for xy, d in destination if np.linalg.norm(xy - center) < 0.15]
        new_center, diameter = min(
            near, key=lambda feature: max(abs(feature[1] - expected_diameter))
        )
        center_difference = np.linalg.norm(new_center - center)
        diameter_difference = max(abs(diameter - expected_diameter))
        assert center_difference < 0.08 and diameter_difference < 0.13
        result.append(
            {
                "stock_center_xy_mm": center.tolist(),
                "new_center_xy_mm": new_center.tolist(),
                "stock_section_diameters_xy_mm": expected_diameter.tolist(),
                "new_section_diameters_xy_mm": diameter.tolist(),
                "center_displacement_mm": center_difference,
                "maximum_axis_diameter_difference_mm": diameter_difference,
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock_stl", type=Path)
    parser.add_argument("--parts", type=Path, default=PACKAGE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    carrier_file = args.parts / "V5_2S2P_carrier.stl"
    keeper_file = args.parts / "V5_2S2P_keeper.stl"
    stock, stock_solid = load(args.stock_stl)
    carrier, carrier_solid = load(carrier_file)
    keeper, keeper_solid = load(keeper_file)
    keeper_xyz = [-0.058, -3.5, 45.0]
    keeper_installed = keeper_solid.translate(keeper_xyz)
    pack = block([-18.608, -33.55, 7.50], [18.492, 33.45, 44.40])
    sweep = block(
        [-18.608 - 0.77, -33.55 - 0.67, 7.501], [18.492 + 0.77, 33.45 + 0.67, 75]
    )
    pairs = {
        "pack_case": (pack, carrier_solid),
        "pack_keeper": (pack, keeper_installed),
        "case_keeper": (carrier_solid, keeper_installed),
        "insertion_plus_clearance": (sweep, carrier_solid),
    }
    overlaps = {k: abs((a ^ b).volume()) for k, (a, b) in pairs.items()}
    assert max(overlaps.values()) < 0.001
    xy = [24.078, 19.617]
    # Prove the fourth PCB-facing boss is solid along its central axis between z=0.01 and 8.40 mm.
    probe = block(
        [xy[0] - 0.05, xy[1] - 0.05, 0.01], [xy[0] + 0.05, xy[1] + 0.05, 8.40]
    )
    for part in (stock_solid, carrier_solid):
        assert abs((probe - part).volume()) < 0.0001
    report = {
        "units": "mm unless otherwise specified",
        "nominal_pack": {
            "length": 67,
            "width": 37.1,
            "thickness": 36.9,
            "measured_mass_g": 182,
            "assembled_center": [-0.058, -0.05, 25.95],
        },
        "source_and_print_stl_sha256": {
            p.name: sha256(p.read_bytes()).hexdigest()
            for p in (args.stock_stl, carrier_file, keeper_file)
        },
        "stock": measure(stock),
        "carrier": measure(carrier),
        "keeper": measure(keeper),
        "keeper_print_to_assembly_translation": keeper_xyz,
        "assembly_shift_relative_to_stock_for_fixed_chassis": [0, 0, -20.5],
        "pack_to_keeper_clearance": 0.60,
        "insertion_sweep_extra_XY_clearance_each_side": [0.77, 0.67],
        "solid_overlap_mm3": overlaps,
        "four_chassis_mounts_z25_original_vs_z45_5_new": compare_mounts(
            stock, carrier, 25, 45.5, (1.5, 2.5), 4
        ),
        "three_open_pcb_mounts_z1_5": compare_mounts(
            stock, carrier, 1.5, 1.5, (2.5, 3.0), 3
        ),
        "fourth_solid_pcb_boss_z1_5": compare_mounts(
            stock, carrier, 1.5, 1.5, (5, 5.75), 1, np.array(xy)
        ),
        "physical_fit": "Unverified. The model represents the rectangular pack body only.",
    }
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        print(output)


if __name__ == "__main__":
    main()

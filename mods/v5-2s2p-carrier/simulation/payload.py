"""Adjust the compiled rigid trunk's mass, first moments and full inertia about its origin."""

from pathlib import Path
import json
import numpy as np
import mujoco as mj
from assembly import configuration


def parallel_axis(center):
    return np.eye(3) * (center @ center) - np.outer(center, center)


def part_properties(part):
    """A component's own central tensor in trunk coordinates, SI."""
    mass = part["mass_g"] * 0.001
    center = np.array(part["center_mm"], float) * 0.001
    if "inertia_kg_m2" in part:
        tensor = np.array(part["inertia_kg_m2"], float)
    elif "specific_inertia_mm2" in part:
        tensor = mass * 1e-6 * np.array(part["specific_inertia_mm2"], float)
    else:
        dim = np.array(part["size_mm"], float) * 0.001
        tensor = mass / 12 * np.diag(np.sum(dim**2) - dim**2)
    if mass <= 0 or not np.isfinite(np.r_[center, tensor.ravel()]).all():
        raise ValueError(part)
    return mass, center, tensor


def iquat_matrix(q):
    flat = np.empty(9)
    mj.mju_quat2Mat(flat, q)
    return flat.reshape(3, 3)


def report(env):
    m = env.model
    b = env.trunk
    R = iquat_matrix(m.body_iquat[b])
    mat = R @ np.diag(m.body_inertia[b]) @ R.T
    sample = mj.MjData(m)
    mj.mj_resetDataKeyframe(m, sample, m.key("STAND").id)
    mj.mj_forward(m, sample)
    world_cm = sample.subtree_com[b]
    com_in_trunk = sample.xmat[b].reshape(3, 3).T @ (world_cm - sample.xpos[b])
    return dict(
        standing_robot_center_from_trunk_mm=(com_in_trunk * 1e3).tolist(),
        trunk_mass_kg=float(m.body_mass[b]),
        trunk_center_m=m.body_ipos[b].tolist(),
        central_inertia_kg_m2=mat.tolist(),
        robot_mass_kg=float(m.body_subtreemass[b]),
    )


def apply_payload(env, config, case):
    m, d = env.model, env.data
    b = env.trunk
    old = report(env)
    if case == "original":
        return old, None
    parts = configuration(config, case)
    signed = []
    for sign, group in ((-1, "removed"), (1, "added")):
        for p in parts[group]:
            signed.append((sign, *part_properties(p)))
    base_mass = old["trunk_mass_kg"]
    base_center = np.asarray(old["trunk_center_m"])
    base_tensor = np.asarray(old["central_inertia_kg_m2"])
    mass = base_mass
    first = base_mass * base_center
    tensor = base_tensor + base_mass * parallel_axis(base_center)
    residual = None
    for sign, weight, pos, own in signed:
        mass += sign * weight
        first += sign * weight * pos
        tensor += sign * (own + weight * parallel_axis(pos))
        if sign == -1:
            props = np.linalg.eigvalsh(tensor - mass * parallel_axis(first / mass))
            if mass <= 0 or props.min() <= 0 or props[2] > props[0] + props[1] + 1e-12:
                raise ValueError(
                    f"The specified removed components cannot form part of the legacy trunk in {case}."
                )
            residual = dict(
                mass_g=float(1000 * mass), central_principal_kg_m2=props.tolist()
            )
    center = first / mass
    tensor -= mass * parallel_axis(center)
    diag, axes = np.linalg.eigh(tensor)
    if mass <= 0 or diag.min() <= 0 or diag[2] > diag[0] + diag[1] + 1e-12:
        raise ValueError(f"Invalid rigid trunk inertia in {case}: {diag}")
    if np.linalg.det(axes) < 0:
        axes[:, 0] *= -1
    m.body_mass[b] = mass
    m.body_ipos[b] = center
    m.body_inertia[b] = diag
    mj.mju_mat2Quat(m.body_iquat[b], np.ascontiguousarray(axes).flatten())
    site = m.site("imu").id
    m.site_pos[site] += (
        np.asarray(parts.get("imu_translation_mm", [0, 0, 0]), float) * 0.001
    )
    mj.mj_setConst(m, d)
    rec = report(env)
    if not np.allclose(rec["central_inertia_kg_m2"], tensor, atol=1e-12):
        raise ValueError("Inertia frame mismatch")
    if not np.isclose(rec["robot_mass_kg"] - old["robot_mass_kg"], mass - base_mass):
        raise ValueError("Robot mass mismatch")
    support = json.loads(Path(__file__).with_name("floor_hulls.json").read_text())
    hull = np.asarray(support[case.split("-", 1)[0]], dtype=float) * 0.001
    rec["remaining_legacy_trunk"] = residual
    rec["imu_site_mm"] = (m.site_pos[site] * 1000).tolist()
    rec["delta_g"] = (mass - base_mass) * 1000
    rec["old_trunk"] = old
    return rec, hull

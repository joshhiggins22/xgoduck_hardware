"""Resolve one before/after assembly from registered component moments and weighed inputs."""

from copy import deepcopy
import numpy as np


def changed(component, *, grams=None, delta=None):
    p = deepcopy(component)
    if grams is not None:
        p["mass_g"] = grams
    if delta is not None:
        p["center_mm"] = (np.asarray(p["center_mm"]) + delta).tolist()
    return p


def configuration(config, case):
    state, level = case.split("-", 1)
    if state not in ("v5", "2s2p"):
        raise ValueError(case)
    upgraded = state == "2s2p"
    p = config["geometry"]
    s = config["conditions"][level]
    removed = [
        changed(p["old_pack"], grams=s["embedded_pack_g"]),
        p["old_carrier"],
        changed(p["legacy_pcb"], grams=s["embedded_pcb_g"]),
    ]
    shift = -config["extension_mm"] if upgraded else 0.0
    boards = changed(
        p["boards"], grams=s["boards_g"], delta=[shift + s["boards_x_bias_mm"], 0, 0]
    )
    enclosure = changed(p["enclosure"], delta=[shift, 0, 0])
    if upgraded:
        pack = changed(
            p["new_pack"], grams=s["new_pack_g"], delta=s["new_pack_xyz_bias_mm"]
        )
        added = [
            pack,
            changed(
                p["new_carrier"],
                grams=p["new_carrier"]["mass_g"] * s["new_print_factor"],
            ),
            changed(p["keeper"], grams=p["keeper"]["mass_g"] * s["new_print_factor"]),
            p["keeper_screws"],
            boards,
            enclosure,
        ]
    else:
        added = [
            changed(p["old_pack"], grams=s["old_pack_g"]),
            p["old_carrier"],
            boards,
            enclosure,
        ]
    return dict(
        removed=removed,
        added=added,
        imu_translation_mm=[shift, 0, 0],
    )

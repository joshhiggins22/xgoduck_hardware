"""Compare the installed Walk actor during left/right turns with the original and upgraded packs."""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import benchmark as bench
import numpy as np


def yaw(env):
    forward = env.data.xmat[env.trunk].reshape(3, 3)[:, 0]
    return np.arctan2(forward[1], forward[0])


def one_turn(env, actor, seed, rate, hull):
    env.reset(seed=seed)
    actor.reset(env.data)
    angles = [yaw(env)]
    positions = [env.data.xpos[env.trunk, :2].copy()]
    min_clearance_m = np.inf
    for tick in range(300):
        turning = 100 <= tick < 200
        targets = actor.targets(command=[0.0, 0.0, rate if turning else 0.0])
        _, _, fell, _, info = env.advance(
            targets, actor.raw_action, sample_callback=actor.sample
        )
        angles.append(yaw(env))
        positions.append(env.data.xpos[env.trunk, :2].copy())
        rotation = env.data.xmat[env.trunk].reshape(3, 3)
        gap = env.data.xpos[env.trunk, 2] + np.min(hull @ rotation[2])
        min_clearance_m = min(min_clearance_m, gap)
        if fell or gap <= 0:
            break
    headings = np.degrees(np.unwrap(angles))
    turn_degrees = (
        float(headings[200] - headings[100]) if len(headings) >= 201 else None
    )
    finished = len(headings) == 301
    settled = (
        finished
        and min_clearance_m > 0
        and not info["fell"]
        and info["upright_streak_s"] >= 0.5
        and np.linalg.norm(positions[-1] - positions[-26]) / 0.5 <= 0.05
        and abs(headings[-1] - headings[-26]) / 0.5 <= 5.0
    )
    return {
        "seed": seed,
        "fell": bool(info["fell"]),
        "min_case_floor_clearance_mm": float(1000 * min_clearance_m),
        "yaw_during_command_deg": turn_degrees,
        "yaw_after_release_deg": float(headings[-1] - headings[200])
        if finished
        else None,
        "pivot_translation_m": float(np.linalg.norm(positions[200] - positions[100]))
        if len(positions) >= 201
        else None,
        "settled": bool(settled),
    }


def run(task):
    config, foot, case, rate, first, count = task
    env = bench.DuckSitStandEnv(foot=foot, surface="carpet", start="stand", episode_s=6)
    try:
        _, hull = bench.apply_payload(env, config, case)
        actor = bench.StockPolicy(env.model, bench.LAB / "runtime", bench.ACTOR)
        rows = [
            one_turn(env, actor, s, rate, hull) for s in range(first, first + count)
        ]
    finally:
        env.close()
    return {"foot": foot, "case": case, "rate_rad_s": rate, "episodes": rows}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--first-seed", type=int, default=16400)
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--out", type=Path, default=Path(__file__).with_name("turns.json"))
    args = p.parse_args()
    configfile = Path(__file__).with_name("assembly.json")
    config_bytes = configfile.read_bytes()
    config = json.loads(config_bytes)
    tasks = [
        (config, foot, case, rate, args.first_seed, args.trials)
        for foot in ("v2-heel5", "v2-heel15")
        for case in ("v5-nominal", "2s2p-nominal")
        for rate in (0.5, -0.5)
    ]
    import hashlib

    if hashlib.sha256(bench.ACTOR.read_bytes()).hexdigest() != bench.WALK_SHA:
        raise ValueError("Walk model checksum mismatch")
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(run, tasks))
    args.out.write_text(
        json.dumps(
            {
                "walk_sha256": bench.WALK_SHA,
                "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
                "phases_s": [2, 2, 2],
                "groups": rows,
            },
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )

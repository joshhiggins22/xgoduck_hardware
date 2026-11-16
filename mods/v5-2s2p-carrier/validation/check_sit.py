"""Replay measured seating and rear-shell clearance with the installed SitStand actor."""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LAB = Path(
    os.environ.get("XGO_DUCK_LAB", HERE.parent.parent / "XGO-Duck-Lab")
).resolve()
SIM = HERE.parent / "simulation"
sys.path[:0] = [str(SIM), str(LAB)]

from duck_env import DuckSitStandEnv
from learner import onnx_session, predict_onnx
from payload import apply_payload


def evaluate(foot, case, seeds):
    env = DuckSitStandEnv(foot, "carpet", "stand", 8)
    config = json.loads((SIM / "assembly.json").read_text())
    _, hull = apply_payload(env, config, case)
    sitstand = onnx_session(LAB / "runs/stock-49k/policy.onnx")
    walk = onnx_session(LAB / "runtime/walk-4ce3315c.onnx")
    rows = []
    for seed in seeds:
        obs, _ = env.reset(seed=seed)
        seated_streak = 0
        seated = False
        lowest = np.inf
        for tick in range(env.max_steps):
            if tick < 150:
                obs = env.feedback.obs(env._last_action, cmd=[1.0, 0.0, 0.0])
            elif tick == 150:
                seated = seated_streak >= 12
            elif tick == 200:
                env.actions.reset()
                obs = env.feedback.obs(np.zeros(14, np.float32))
            elif tick >= 225:
                obs = env.feedback.obs(env._last_action, cmd=[0.12, 0.0, 0.0])
            action = predict_onnx(sitstand if tick < 200 else walk, obs)
            obs, _, fell, _, info = env.step(action)
            vertical = env.data.xmat[env.trunk].reshape(3, 3)[2]
            gap = 1000 * (env.data.xpos[env.trunk, 2] + (hull @ vertical).min())
            lowest = min(lowest, gap)
            if tick < 150:
                knees = np.abs(env.data.qpos[env.qpos_adr[[3, 12]]])
                deep = info["z"] < 0.115 and info["tilt_deg"] < 25 and min(knees) > 0.8
                seated_streak = seated_streak + 1 if deep else 0
            if fell or gap <= 0:
                break
        rows.append(
            {
                "seed": seed,
                "seat": seated,
                "stage": "sit" if tick < 150 else "stand" if tick < 200 else "walk",
                "first_strike_s": round(0.02 * (tick + 1), 4) if gap <= 0 else None,
                "kinematic_fall": fell,
                "min_floor_mm": round(lowest, 3),
                "final_upright_s": round(info["upright_streak_s"], 3),
                "complete": bool(
                    tick == 399
                    and seated
                    and not fell
                    and lowest > 0
                    and info["upright_streak_s"] >= 1.0
                ),
            }
        )
    env.close()
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foot", choices=["v2-heel5", "v2-heel15"], required=True)
    parser.add_argument("--seed", type=int, default=1601)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.episodes <= 0:
        parser.error("episode count must be positive")
    result = {
        case: evaluate(args.foot, case, range(args.seed, args.seed + args.episodes))
        for case in ("v5-nominal", "2s2p-nominal")
    }
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    for case, rows in result.items():
        print(
            case,
            sum(r["seat"] for r in rows),
            "seated;",
            sum(r["first_strike_s"] is not None for r in rows),
            "floor strikes;",
            sum(r["complete"] for r in rows),
            "completed",
        )

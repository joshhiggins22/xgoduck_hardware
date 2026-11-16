"""Compare the previously trained stock-foot recovery Walk actor on the measured 2S2P configuration."""

import argparse
import hashlib
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import benchmark as bench


def run(task):
    config, foot, impulse, name, model, first_seed, count = task
    env = bench.DuckSitStandEnv(
        foot=foot, surface="carpet", start="stand", episode_s=bench.END * bench.DT
    )
    try:
        _, hull = bench.apply_payload(env, config, "2s2p-nominal")
        actor = bench.StockPolicy(env.model, bench.LAB / "runtime", model, scale=1.0)
        episodes = [
            bench.trial(env, actor, i, 0.20, impulse, hull)
            for i in range(first_seed, first_seed + count)
        ]
    finally:
        env.close()
    return {"foot": foot, "name": name, "impulse": impulse, "episodes": episodes}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--first-seed", type=int, default=18140)
    p.add_argument(
        "--out", type=Path, default=Path(__file__).with_name("candidate.json")
    )
    args = p.parse_args()
    config_bytes = Path(__file__).with_name("assembly.json").read_bytes()
    config = json.loads(config_bytes)
    models = {
        "installed": bench.ACTOR,
        "stock-recovery": bench.LAB / "runs/stock-walk-recovery-stress/walk.onnx",
    }
    hashes = {
        name: hashlib.sha256(model.read_bytes()).hexdigest()
        for name, model in models.items()
    }
    if hashes["installed"] != bench.WALK_SHA:
        raise ValueError("Wrong baseline model")
    tasks = [
        (config, foot, impulse, name, models[name], args.first_seed, args.trials)
        for foot, impulse, name in itertools.product(
            ["v2-heel5", "v2-heel15"], [0.35, 0.85], models
        )
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run, tasks))
    args.out.write_text(
        json.dumps(
            {
                "models": hashes,
                "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
                "speed_m_s": 0.2,
                "scale": 1.0,
                "groups": results,
            },
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )

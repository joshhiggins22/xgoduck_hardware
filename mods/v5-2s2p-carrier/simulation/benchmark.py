"""Paired upright, forward, braking and backward-perturbation trials on MuJoCo CPU."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
LAB = Path(
    os.environ.get("XGO_DUCK_LAB", HERE.parent.parent / "XGO-Duck-Lab")
).resolve()
sys.path.insert(0, str(LAB))
from duck_env import DuckSitStandEnv
from stock_policy import StockPolicy
from payload import apply_payload

ACTOR = LAB / "runtime/walk-4ce3315c.onnx"
WALK_SHA = "1fc079512fe3fe23e274e7a9d8c9ad007e88439f0385ecf20c9596e57886249f"
DT = 0.02
SETTLE, MOVE, STOP, PULSE, RECOVER = 100, 100, 100, 5, 125
END_MOVE = SETTLE + MOVE
END_STOP = END_MOVE + STOP
END = END_STOP + PULSE + RECOVER


def heading(env):
    h = env.data.xmat[env.trunk].reshape(3, 3)[:2, 0]
    return h / np.linalg.norm(h)


def touchdowns(env):
    present = set()
    for c in env.data.contact:
        if c.dist <= 0.001 and env.floor in c.geom:
            present.update(i for i, g in enumerate(env.soles) if g in c.geom)
    return np.array([i in present for i in (0, 1)])


def trial(env, actor, seed, speed, impulse, case_hull):
    _, reset = env.reset(seed=seed)
    data = env.data
    actor.reset(data)
    force_n = impulse * env.model.body_subtreemass[env.trunk] / (PULSE * DT)
    wrench = data.xfrc_applied[env.trunk]
    wrench[:] = 0
    trace = [data.xpos[env.trunk, :2].copy()]
    directions = {}
    held = stopped = ready = recovered = False
    peak = 0.0
    floor_gap_mm = None
    flight_ticks = np.zeros(2, dtype=int)
    contacts = np.zeros(2, dtype=int)
    min_sag = float("inf")
    max_joint_load = 0.0

    def sample(data):
        nonlocal floor_gap_mm
        actor.sample(data)
        if case_hull is not None:
            nz = data.xmat[env.trunk].reshape(3, 3)[2]
            lowest = 1000 * (data.xpos[env.trunk, 2] + (case_hull @ nz).min())
            floor_gap_mm = lowest if floor_gap_mm is None else min(floor_gap_mm, lowest)

    for tick in range(END):
        if tick == SETTLE:
            directions["gait"] = heading(env)
            held = bool(
                info["upright_streak_s"] >= 0.5
                and np.linalg.norm(trace[-1] - trace[-51]) <= 0.05
            )
        if tick == END_STOP:
            stopped = bool(info["upright_streak_s"] >= 0.5)
            ready = stopped and np.linalg.norm(trace[-1] - trace[-26]) / 0.5 <= 0.05
            wrench[:2] = -force_n * heading(env)
        elif tick == END_STOP + PULSE:
            wrench[:] = 0
        vx = speed if SETTLE <= tick < END_MOVE else 0.0
        target = actor.targets(command=[vx, 0.0, 0.0])
        _, _, fell, _, info = env.advance(
            target, actor.raw_action, sample_callback=sample
        )
        trace.append(data.xpos[env.trunk, :2].copy())
        torque = np.abs(env.ctrl._prev_motor_torque)
        max_joint_load = max(max_joint_load, float(torque.max()))
        min_sag = min(
            min_sag,
            max(
                env.ctrl.vin_min,
                env.ctrl.model.actuator.vin - env.ctrl.vin_drop_gain * torque.sum(),
            ),
        )
        if SETTLE <= tick < END_MOVE:
            grounded = touchdowns(env)
            contacts += grounded & (flight_ticks >= 2)
            flight_ticks = np.where(grounded, 0, flight_ticks + 1)
        if tick >= END_STOP:
            peak = max(peak, info["tilt_deg"])
        case_strike = floor_gap_mm is not None and floor_gap_mm <= 0.0
        if fell or case_strike:
            break
    wrench[:] = 0
    trace = np.asarray(trace)
    displacement = lateral = tail_speed = hold_drift = None
    if len(trace) > SETTLE:
        hold_drift = np.linalg.norm(trace[SETTLE] - trace[SETTLE - 50])
    if len(trace) > END_MOVE:
        delta = trace[END_MOVE] - trace[SETTLE]
        direction = directions["gait"]
        displacement = delta @ direction
        lateral = delta @ [-direction[1], direction[0]]
    if len(trace) > END_STOP:
        tail_speed = np.linalg.norm(trace[END_STOP] - trace[END_STOP - 25]) / 0.5
    if len(trace) == END + 1 and not fell and not case_strike:
        recovered = bool(
            info["upright_streak_s"] >= 1
            and np.linalg.norm(trace[-1] - trace[-26]) / 0.5 <= 0.05
        )
    return dict(
        seed=seed,
        carpet={k: v for k, v in reset.items() if k in ("tau_s", "friction")},
        held=held,
        last_hold_second_drift_m=hold_drift,
        walk_dx_m=displacement,
        walk_dy_m=lateral,
        swing_touchdowns=contacts.tolist(),
        stop_speed_m_s=tail_speed,
        stopped=bool(ready),
        push_eligible=bool(ready),
        recovered=bool(ready and recovered),
        fell=bool(fell or case_strike),
        kinematic_fall=bool(fell),
        case_strike=bool(case_strike),
        fell_phase=(
            "settle"
            if tick < SETTLE
            else "gait"
            if tick < END_MOVE
            else "stop"
            if tick < END_STOP
            else "push/recovery"
        )
        if fell or case_strike
        else None,
        final_time_s=round(float(data.time), 3),
        peak_push_tilt_deg=peak if tick >= END_STOP else None,
        min_case_floor_gap_mm=floor_gap_mm,
        min_estimated_bus_v=min_sag,
        max_simulated_joint_torque_Nm=max_joint_load,
        gait_pass=bool(
            speed
            and held
            and displacement is not None
            and displacement * np.sign(speed) >= 0.5 * abs(speed) * MOVE * DT
            and min(contacts) > 0
        ),
    )


def run_group(task):
    foot, case, seeds, speed, impulse, config, scale, *fixed = task
    absolute_impulse = fixed[0] if fixed else None
    env = DuckSitStandEnv(
        foot=foot, surface="carpet", start="stand", episode_s=END * DT
    )
    try:
        record, corners = apply_payload(env, config, case)
        if absolute_impulse is not None:
            impulse = absolute_impulse / record["robot_mass_kg"]
        actor = StockPolicy(env.model, LAB / "runtime", ACTOR, scale=scale)
        rows = [trial(env, actor, seed, speed, impulse, corners) for seed in seeds]
        return dict(
            foot=foot,
            case=case,
            speed=speed,
            scale=scale,
            push_Ns_per_kg=impulse,
            push_Ns=impulse * record["robot_mass_kg"],
            model=record,
            episodes=rows,
        )
    finally:
        env.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=HERE / "assembly.json")
    p.add_argument("--case", nargs="+", default=["v5-nominal", "2s2p-nominal"])
    p.add_argument(
        "--foot",
        nargs="+",
        choices=["v2-heel5", "v2-heel15"],
        default=["v2-heel5", "v2-heel15"],
    )
    p.add_argument("--speed", nargs="+", type=float, default=[0.0, 0.2])
    p.add_argument(
        "--scale",
        type=float,
        nargs="+",
        default=[1.0],
        help="Ordinary action scale from the runtime slider",
    )
    pulse = p.add_mutually_exclusive_group()
    pulse.add_argument(
        "--impulse", type=float, default=0.35, help="Impulse per kg of this robot"
    )
    pulse.add_argument(
        "--absolute-impulse",
        type=float,
        help="Use the same physical N s for every robot",
    )
    p.add_argument("--first-seed", type=int, default=16400)
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if (
        min(a.trials, a.workers) < 1
        or a.impulse < 0
        or (a.absolute_impulse is not None and a.absolute_impulse < 0)
    ):
        p.error("Positive trial/worker counts and nonnegative impulse required")
    if hashlib.sha256(ACTOR.read_bytes()).hexdigest() != WALK_SHA:
        raise ValueError("Installed Walk checksum mismatch")
    config = json.loads(a.config.read_text())
    seeds = list(range(a.first_seed, a.first_seed + a.trials))
    tasks = [
        (foot, case, seeds, v, a.impulse, config, scale, a.absolute_impulse)
        for case in a.case
        for foot in a.foot
        for v in a.speed
        for scale in a.scale
    ]
    context = (
        ProcessPoolExecutor(max_workers=a.workers) if a.workers > 1 else nullcontext()
    )
    results = []
    with context as pool:
        for r in (
            pool.map(run_group, tasks) if pool is not None else map(run_group, tasks)
        ):
            results.append(r)
            print(
                r["case"],
                r["foot"],
                r["speed"],
                {
                    k: sum(ep[k] for ep in r["episodes"])
                    for k in ["held", "gait_pass", "stopped", "recovered", "fell"]
                },
                flush=True,
            )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(
        json.dumps(
            dict(
                walk_sha256=WALK_SHA,
                seed_start=a.first_seed,
                trial_count=a.trials,
                phase_seconds=dict(
                    settle=SETTLE * DT,
                    move=MOVE * DT,
                    stop=STOP * DT,
                    push=PULSE * DT,
                    recover=RECOVER * DT,
                ),
                config_sha256=hashlib.sha256(a.config.read_bytes()).hexdigest()
                if a.config.exists()
                else None,
                hull_sha256=hashlib.sha256(
                    (HERE / "floor_hulls.json").read_bytes()
                ).hexdigest(),
                groups=results,
            ),
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()

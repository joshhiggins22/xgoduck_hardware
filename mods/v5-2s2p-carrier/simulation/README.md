# Carpet benchmark for the V5 battery change

With the measured **182 g pack**, the installed Walk model held a stand, stepped forward and came to a stop on both heel lengths. Average forward speed during a two-second command dropped by about a third. The larger backward perturbations exposed a greater loss of balance, especially on the 5 mm heels. The 15 mm heels gave the more consistent result on these upright tasks. Sitting and rising were outside this benchmark.

## Installed Walk on the nominal builds

All four builds held their initial stand in 8/8 trials and stopped in 8/8 after walking. Each walking trial included at least one swing and touchdown on each foot. Median forward speed uses the full two-second interval, including starting from rest. The command requested +0.20 m/s.

| Heel | Pack | Median forward speed | Recovered after walking and stopping, 0.35 N·s/kg | Recovered after walking and stopping, 0.85 N·s/kg | Recovered from stationary, 0.85 N·s/kg |
| --- | --- | ---: | ---: | ---: | ---: |
| 5 mm | Original | 0.144 m/s | 8/8 | 3/8 | 3/8 |
| 5 mm | 2S2P | 0.093 m/s | 7/8 | 1/8 | 0/8 |
| 15 mm | Original | 0.150 m/s | 8/8 | 8/8 | 8/8 |
| 15 mm | 2S2P | 0.102 m/s | 8/8 | 1/8 | 0/8 |

At 0.35 N·s/kg from sustained stationary standing, all four configurations recovered in 8/8. The one missed post-walk recovery with the new 5 mm build stayed on its feet but did not settle within the time limit. The larger pulse takes 0.10 s and applies 7.12 N to the original 5 mm build or 7.89 N to its heavier replacement. These two levels are defined simulation challenges. [Moderate episodes](nominal.json) · [Strong episodes](stress.json)

A separate comparison applied the **same 6.8 N backward force** for 0.10 s to every build, after a walk and stop, using eight fresh seeds. On the 5 mm heels the original pack recovered 3/8 and the replacement 0/8. On the 15 mm heels the original recovered 6/8 and the replacement 5/8. This comparison controls for the larger physical force applied to a heavier robot in the normalized tests. [Equal-force episodes](equal-force.json)

## Which parts and masses changed

The robot’s trunk X axis points forward and Z points up. The old pack geometry in the published trunk mesh has a center 17.84 mm aft and 32.80 mm below the trunk origin. The replacement's registered center is 30.54 mm aft and 29.89 mm below. The 20.5 mm carrier extension moves the existing rear electronics, their cover, and the QMI8658A IMU aft together. Both pack configurations use the existing 2S voltage model.

| Component | Original value | Replacement value |
| --- | ---: | ---: |
| Battery pack | 100 g estimate | 182 g measured |
| Printed carrier | 19.00 g sliced | 25.62 g sliced |
| Keeper and its two screws | — | 0.96 g sliced + 0.30 g estimated |
| Existing rear enclosure and two boards | 19.17 g sliced + 40 g estimated | Same mass, 20.5 mm farther aft |

The nominal mass gain is **89.88 g**. With 5 mm heels the modeled complete robot goes from 838.0 to 927.9 g and its whole-body center of mass at the standing keyframe moves 6.50 mm aft and 1.51 mm downward. With 15 mm heels the masses are 850.0 and 939.9 g, and the shifts are 6.38 mm aft and 1.33 mm downward. Installed wires, accessories and actual infill can vary.

The published MJCF provides one 228.62 g trunk inertia. To construct both V5 cases, the calculation removes the presumed embedded original pack, original carrier and simplified PCB first. It then adds the explicitly modeled V5 parts for that case. The nominal embedded PCB approximation is 25 g. Removing an entire physical two-board assembly and cover directly from the legacy aggregate would leave an impossible residual tensor. The code checks the principal inertias and their triangle inequality on the residual and final body, sums the full rigid-body tensors about a common origin, and verifies compiled mass and orientation. Each episode group includes the resulting masses, centers and tensors. Slicer-derived inertia includes only deposited part material. The new pack uses four long-axis cylinder mass distributions with the measured total mass and CAD cell spacing. All other joints and head mass use the lab's published XGO model. [Editable inputs](assembly.json) · [Assembly choices](assembly.py) · [Moment calculation](payload.py)

## Sensitivity and controller changes

All sensitivity cases keep the actual pack at **182 g**. The light/heavy combinations span estimated original pack weights of 110/90 g, 30/50 g for the two boards, a ±3 mm fore/aft board-center shift, ±15% printed replacement mass, a ±1.5 mm fore/aft pack-center shift and small vertical/lateral biases. Plausible legacy PCB contribution varies from 30 to 20 g. These are deliberately bundled scenarios. The JSON exposes each input to vary separately.

| Heel | New pack speed, light / heavy | New pack recoveries after walk, light / heavy, 0.35 N·s/kg |
| --- | ---: | ---: |
| 5 mm | 0.104 / 0.075 m/s | 7/8 / 6/8 |
| 15 mm | 0.112 / 0.090 m/s | 8/8 / 8/8 |

All builds still stood and stopped in all eight trials per condition. The adverse 5 mm build fell once after the moderate pulse. [Sensitivity episodes](uncertainty.json)

With the 182 g setup the runtime already offers an ordinary action scale setting. On fresh paired seeds, changing it from 1.0 to 1.1 raised median forward speed from 0.091 to 0.102 m/s on the 5 mm heels and 0.103 to 0.114 m/s on the 15 mm heels. Both settings stopped and recovered in 8/8 moderate-pulse trials for each heel. Peak inferred motor torque rose in both cases. These results support using the installed model for a first supported stationary test. Recovering the original speed or strong-push performance makes payload-specific training worthwhile. The separate existing balance-correction model was also tested for transfer. [Action-scale episodes](scale-validation.json) · [Existing recovery controller](candidate.json)

## Protocol and scope

- The tester verifies the SHA-256 of the owner’s archived Walk ONNX. The duck starts upright on a randomized synthetic carpet. Identical seeds pair floor friction, compliance and initial attitude across mass, heel and controller variants. MuJoCo runs at 200 Hz, encoders and IMU feed the runtime filter at 100 Hz, and policy decisions run at 50 Hz.
- The first 2 s use zero command. The next 2 s use either zero or +0.20 m/s. After 2 s at zero, the experiment applies a 0.10 s backward trunk force along the current heading, then allows 2.5 s to recover.
- Counting a hold requires continuous upright posture for the final 0.5 s of the initial phase and no more than 50 mm drift over its last second. Stopping requires 0.5 s continuously upright and less than or equal to 0.05 m/s net horizontal drift speed over that half-second. Recovery requires an eligible stop, survival, 1 s continuously upright at the end and the same final drift-speed threshold. Upright uses trunk height ≥124 mm, tilt <15° and both knee angles within 0.40 rad.
- Each JSON also records `gait_pass`, a stricter speed-tracking measure that requires at least half the requested forward speed plus a touchdown on both feet following ≥40 ms airborne. A trial can move and step normally while missing that speed threshold. Ground contact with the actual external case or cover counts as a failed balance trial. Plane clearance is calculated at 100 Hz from support vertices of the registered CAD parts. A fall also terminates the trial at tilt >65° or height <52 mm.
- This is a rigid-body comparison on an unmeasured compliant plane. It omits carpet pile snagging, flexible TPU behavior, wired accessory loads, actual pack resistance and physical motor temperature. The IMU’s relative translation follows the carrier. Its absolute original mounting position and the actuators’ load model are inherited approximations. The simulation stops at a case strike and does not predict a bounce or powered get-up. A sustained stand in this model is distinct from measured stability on the owner's carpet.

## Reproduce

Install the companion [XGO-Duck-Lab](https://github.com/joshhiggins22/xgoduck_rl/tree/d14afc89d53480a7e4b8c2984883f151ab253e40/XGO-Duck-Lab) and run its setup. From this simulation folder, the commands below assume the lab directory is a sibling of `XGO-V5-2S2P`. For another layout, set `XGO_DUCK_LAB` to the lab's absolute path. The `--case original` option exposes the untouched legacy trunk for diagnostic comparison.

```sh
lab="../../XGO-Duck-Lab"
"$lab/.venv/bin/python" benchmark.py --trials 8 --out nominal-replay.json
"$lab/.venv/bin/python" benchmark.py --impulse .85 --trials 8 --out stress-replay.json
"$lab/.venv/bin/python" benchmark.py --speed .2 --absolute-impulse .68 \
  --first-seed 16800 --trials 8 --out equal-force-replay.json
"$lab/.venv/bin/python" benchmark.py --case v5-light 2s2p-light v5-heavy 2s2p-heavy \
  --speed .2 --first-seed 16500 --trials 8 --out uncertainty-replay.json
"$lab/.venv/bin/python" benchmark.py --case 2s2p-nominal --speed .2 --scale 1 1.1 \
  --first-seed 16700 --trials 8 --out scale-replay.json
```

The supplied support vertices are sufficient for all runs. To regenerate them following a CAD change, use [build_hulls.py](build_hulls.py) with NumPy, SciPy, trimesh and a local copy of the [V5 hardware](https://github.com/joshhiggins22/xgoduck_hardware/tree/1bc89265dd9427e44b4cfc664a98079f225d5609/structure/V5_AUDIO_VIDEO_).

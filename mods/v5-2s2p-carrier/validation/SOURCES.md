# Battery swap measurements and checks

## Placement and mass

The owner weighed the replacement pack at **182 g**. The supplied drawing shows a maximum envelope of **67 × 37.1 × 36.9 mm**. In the assembled duck the long axis is vertical. The original pack is unweighed. The nominal model uses **100 g** based on a comparable protected two-cell pack. The model assigns **40 g** to the two stacked circuit boards together, with a 30–50 g sensitivity range. The board mass and the distribution of mass inside each pack are estimates. [Comparable original pack](https://www.keeppower.com/product/2s1p-protected-18650-li-ion-battery-pack-7-2v-3500mah-with-connector-xt30/) · [V5 board assembly](https://wiki.xgorobot.com/kb/the-xgo-series-robot/duck-guide-06)

The published V5 print project provides the original battery carrier and V1.1 rear cover. Matching its carrier to the training model gives a median sampled surface distance of 0.28 mm. The older model includes a separate two-cell-shaped solid and an 11 mm deep electronics block. The V5 cover is 25.2 mm deep, and the expansion board carries the QMI8658A IMU at U1. The replacement moves the original cover and stacked boards 20.5 mm toward the rear. The simulation translates the IMU by the same amount. Its original absolute site position remains the upstream approximation. [V5 source parts](https://github.com/joshhiggins22/xgoduck_hardware/tree/1bc89265dd9427e44b4cfc664a98079f225d5609/structure/V5_AUDIO_VIDEO_) · [Upstream trunk and robot model](https://github.com/LuwuDynamics/xgoduck_rl/tree/a4c78aacd5eaa724cf246fe12d24bfe1e837fa50/src/mjlab_microduck/robot/xgoduck) · [Expansion-board components](https://github.com/joshhiggins22/xgoduck_hardware/blob/1bc89265dd9427e44b4cfc664a98079f225d5609/docs/BOM.md)

We sliced the two final Fusion STL exports and the two original V5 STL files individually with the vendor’s P1P/PLA profile. Summing the extrusion assigned to each finished part gives **19.00 g original carrier**, **19.17 g unchanged rear cover**, **25.62 g replacement carrier** and **0.96 g keeper**. The estimated material increase is **7.58 g**. The two keeper screws add another estimated 0.3 g. Including the 82 g nominal increase in pack mass gives **89.88 g added**. Actual printed mass depends on the user’s material, slicer and hardware. [Source 3MF and print settings](https://github.com/joshhiggins22/xgoduck_hardware/blob/1bc89265dd9427e44b4cfc664a98079f225d5609/3DManufacturingFormat/xgoduckV5.3mf) · [Mass inputs](../simulation/assembly.json) · [Slice details, centroids, tensors and file hashes](evidence.json)

## Rigid geometry

The exported carrier and keeper each form one watertight, consistently wound solid. The maximum-size rectangular pack envelope touches its seating pads and has **0.60 mm** clearance below the keeper. Both meshes have zero positive overlap volume with that envelope. The drawing dimensions exclude wire, plug and strain-relief space. Confirm those on the physical print. [Fusion geometry checks](../fusion-check.json)

One 8.6-second walking trial per heel used the 182 g nominal assembly, seed 91601, archived Walk at gain 1.0, a 0.20 m/s forward command, braking and a backward pulse of 0.35 N·s/kg. Across 215 frames sampled per heel, the closest moving part on both ducks was the left shin. The minimum rigid mesh clearances were **3.49 mm on 5 mm heels** and **4.72 mm on 15 mm heels**. The lowest backpack-to-floor distances sampled were 48.1 and 57.8 mm respectively. The test covers those trajectories and excludes loose cables, print variation and structural flex. [Per-foot results](evidence.json)

## Deep seated command

We separately tested the installed stock-foot SitStand ONNX at gain 1.0 using the final assembly and matching randomized carpet on seeds 1601–1612. A three-second Sit command began from upright. A full cycle required a sustained measured seat, a subsequent Stand and no fall or contact between the rear enclosure and the floor.

| Feet | Original V5 pack | 182 g replacement |
| --- | --- | --- |
| 5 mm heel | 12/12 reached the deep seat. All 12 then struck the floor during Stand. | 12/12 struck the floor during Sit at 0.68–0.82 s. |
| 15 mm heel | 0/12 reached the deep seat. Eleven struck the floor during Sit. | 12/12 struck the floor during Sit at 0.98–1.02 s. |

No tested configuration completed the cycle under this command sequence. The screen stops at the first nonpositive floor clearance. It does not model the backpack bearing weight after contact. These results concern deep sitting. The walking measurements above started upright. [Per-seed results, criteria and actor checksum](evidence.json)

To repeat the Sit check from the battery-package folder with the Mac lab in the neighboring directory, run the following commands. Set `XGO_DUCK_LAB` to the lab directory if it is installed elsewhere.

```sh
../XGO-Duck-Lab/.venv/bin/python validation/check_sit.py --foot v2-heel5
../XGO-Duck-Lab/.venv/bin/python validation/check_sit.py --foot v2-heel15
```

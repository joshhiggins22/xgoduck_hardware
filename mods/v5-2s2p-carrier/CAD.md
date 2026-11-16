# V5 battery carrier and removable keeper

The replacement fits a nominal **67.0 × 37.1 × 36.9 mm** pack weighing **182 g**. Four factory chassis mounting ears stay at their original positions on the robot. The carrier holds the pack vertically and moves the electronics-side mounting face and rear cover **20.5 mm rearward**. Check that the board harness can reach its new position before printing.

| File | Purpose |
| --- | --- |
| [Fusion assembly](V5_2S2P_assembly.f3d) | Two editable components with the keeper in its installed position |
| [STEP assembly](V5_2S2P_assembly.step) | Neutral solids with the same placement |
| [Carrier STL](V5_2S2P_carrier.stl) | Print one, large opening toward +Z |
| [Keeper STL](V5_2S2P_keeper.stl) | Print one flat, countersinks facing upward |

## Printing and assembly

1. Import the two STLs in millimetres at 100% scale. Each is oriented for its own print. The reference slice used the V5 project settings for a Bambu P1P, 0.4 mm nozzle, 0.20 mm layers, three walls, 10% infill and PLA. Inspect the slicer's bridge and support preview around the side windows and the keeper screw bosses. Remove loose support and sharp burrs from pack-contact surfaces.
2. With the robot powered off and pack disconnected, compare the carrier mounting ears and board standoffs against your actual holder. Try the empty carrier and rear electronics cover in place with the original hardware. Check harness reach at the board and cable slack through head and leg movement.
3. With the carrier off the chassis and keeper removed, lower the pack straight into the broad opening until it rests on the support lands. The lead exits at the pack's upper end through a 14 mm opening. Paired 2.6 × 5 mm slots accept a small external cable tie or lacing loop. Leave a service loop so the connector can be unplugged without pulling on the leads.
4. Fasten the keeper with **two additional M2 × 6 mm, 90° countersunk self-tapping screws**. Its 2.25 mm clearance holes and 4.25 mm head recesses align with 1.65 mm blind pilots outside the pack outline. A flush 6 mm screw gives about 3.85 mm engagement and 1.15 mm pilot-bottom clearance. Check head seating and screw engagement. The bar should retain the pack without pressing on its wrap. If the actual pack rattles, a thin nonconductive pad can take up the measured gap.
5. Refit the carrier to the chassis and rear electronics. The stock assembly guide on page 23 specifies four M2 × 6 mm chassis screws and four M3 × 16 mm electronics screws. The published V5 carrier mesh has four chassis holes, **three open rear PCB bores and one solid rear standoff**. The replacement reproduces those features. Compare screw engagement and standoff use with your physical board and cover revision. Leave the solid standoff intact for the initial fit. [Factory assembly guide](https://github.com/joshhiggins22/xgoduck_hardware/blob/main/Assembly_Guide.pdf)

## Dimensions and fit checks

The CAD frame inherits the stock carrier STL coordinates. X runs across the duck, +Y points up toward the lead exit, and +Z points from the electronics toward the chassis. The rectangular pack lies **37.1 mm across X, 67.0 mm along Y and 36.9 mm along Z**. Its installed center is (−0.058, −0.050, 25.950) mm. The cavity is 38.70 × 68.40 mm across X and Y, giving 0.80 mm and 0.70 mm per side. The pack's lower face rests at Z 7.50 mm, its upper face reaches Z 44.40 mm, and the keeper underside is at Z 45.00 mm. The keeper STL's print origin is translated by (−0.058, −3.50, 45.00) mm in the assembly.

A solid intersection check confirmed that the nominal pack fits and can translate along −Z through the unmounted carrier with the keeper removed. The insertion test extended the rectangular pack envelope another 0.77 mm per side along X and 0.67 mm per side along Y. The installed pack clears the keeper by 0.60 mm. Its leads, connector and local projections from the wrapping or protection board require a physical check. The design awaits a prototype print, retention test and powered hardware test. [Fit results](cad-fit-check.json)

The board and chassis interfaces come from the fork's original V5 carrier mesh. The extraction simplifies the donor tessellation with a 0.075 mm tolerance before building solids. At the measured planes the three open board screw centres moved at most 0.025 mm and the four chassis screw centres at most 0.020 mm. The largest change in sectional hole diameter was 0.087 mm. The fork's original V2 print-project holder also matched the V5 donor in a bidirectional surface comparison, with a maximum sample distance of 0.0032 mm over 2,500 points in each direction. [Factory V5 carrier](https://github.com/joshhiggins22/xgoduck_hardware/blob/main/structure/V5_AUDIO_VIDEO_/V5_AUDIO_VIDEO_BATTERY.stl)

## Editing or rebuilding

Open the F3D directly in Fusion to change the design. Its 38 timeline entries include the imported stock interfaces, wall extension, clearance pocket, support lands, rounded windows, lead exit, keeper bosses, pilot bores and countersinks. The `AddedDepth` user parameter controls the spacing of the stock interfaces. When changing pack dimensions, also check the pocket sketch, keeper placement and hole engagement. The archived file reopened with two solid components and no timeline warnings. The STEP reimported into FreeCAD as two valid solids. [Fusion check](fusion-check.json) · [STEP check](step-check.json)

To regenerate from the vendor mesh, work from this directory and pass the stock V5 STL path. The first script uses NumPy, trimesh and manifold3d. The conversion step uses FreeCAD's Python runtime. On macOS a standard FreeCAD installation includes the executable shown here.

```sh
python source/prepare_mounts.py /path/to/V5_AUDIO_VIDEO_BATTERY.stl
/Applications/FreeCAD.app/Contents/Resources/bin/python source/convert_mounts.py
```

In Autodesk Fusion, open **Utilities → Scripts and Add-Ins**, add the local **source/BuildV5Carrier** script folder, and run **BuildV5Carrier**. The script reads the two prepared STEP files beside it and writes a fresh archive, STEP and two STLs to `source/BuildV5Carrier/generated/`. On other systems, use the corresponding FreeCAD Python runtime and set `FREECAD_LIB` to its module directory if needed. To repeat the geometric checks against the distributed print STLs, run the following command in the environment with NumPy, trimesh, SciPy and manifold3d.

```sh
python source/verify_fit.py /path/to/V5_AUDIO_VIDEO_BATTERY.stl
```

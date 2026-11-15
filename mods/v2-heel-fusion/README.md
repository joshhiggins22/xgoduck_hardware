# XGO Duck V2 · 15 mm heel pair

Replacement left and right feet and matching TPU pads for the V2 Standard build. The ankle mounts and forefeet come from the individual V2_STANDARD stock meshes in joshhiggins22/xgoduck_hardware at 99523aa74bc0cbdd92140a4565e29b3073155362. Source geometry by Luwu Dynamics. See the repository’s LICENSING.md for provenance.

## Open and print

Open XGO_V2_heel_pair.f3d in Autodesk Fusion. The assembly contains four named components. Change **HeelExtension** under Modify → Change Parameters to adjust both heels and both pads together. The archive is set to 15 mm. Re-export all four components if you change the dimension.

The four supplied STL files use millimeters and are individually placed on their flat mounting faces. Print one of each at 100% scale. Use your stock rigid-foot material and settings for Left_foot and Right_foot, and your stock sole TPU and settings for Left_TPU and Right_TPU. Left and right are from the duck's perspective. Fit the named pad to the corresponding foot with the factory hardware. The flat faces mate, the counterbores face the ground, the thicker TPU edges face inward, and both long ends face rearward. See page 15 of the V2 assembly guide for the pad orientation.

## Design and checks

The replacement continues the factory sidewall profile aft, then rounds the end with 5 mm plan-view corner radii and a rolled upper edge on the rigid part and lower edge on the installed TPU. It retains the factory lateral wedge and screw pattern. The rigid foot is 69 mm long (stock 54 mm) and about 39.70 mm wide. New rear bores are 1.70 mm diameter, and TPU screw-head recesses are 3.70 mm diameter with 2.50 mm of TPU from the mounting face to the screw seat.

The factory supplies triangulated parts. Their inherited ankle and front surfaces are faceted B-rep solids. The heel length, end trimming, screw bores, and pad seats are modeled as features in Fusion.

The F3D was reopened in Fusion and recomputed at 10 and 15 mm. At each length all four components remained solid and the timeline reported no warnings. All four STL exports were independently checked as single, closed solids. The assembled screw axes aligned within 0.002 mm with no measurable foot–pad volume overlap. Transverse sections behind the ankle retained stock width and height through the straight part of the extension. The rear limit within 0.05 mm of the nominal sloped ground-contact plane moved 15.04 mm on each TPU pad. This is a CAD measurement. Carpet compression will affect the loaded contact patch.

## First fit on the duck

With power off, hand-check smooth movement through sitting and rising and clearance around the new heel. Confirm all pads seat flat against their feet and all screw heads sit below the TPU. For a stability trial, use the same stand-up command and carpet patch as with the stock feet. Observe the end of the head lift from the side and whether either heel catches on the first backward step. The design has been checked digitally only.

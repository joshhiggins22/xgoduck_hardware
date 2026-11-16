import math
import traceback
from pathlib import Path

import adsk.core as C
import adsk.fusion as F

SOURCE = Path(__file__).resolve().parent
OUTPUT = SOURCE / "generated"
V = C.ValueInput.createByString
P = C.Point3D.create
NEW = F.FeatureOperations.NewBodyFeatureOperation
CUT = F.FeatureOperations.CutFeatureOperation
JOIN = F.FeatureOperations.JoinFeatureOperation


def log(msg):
    with (OUTPUT / "fusion-log.txt").open("a") as f:
        f.write(msg + "\n")


def objects(values):
    q = C.ObjectCollection.create()
    for v in values:
        q.add(v)
    return q


def mm(v):
    return (str(v) + " mm") if isinstance(v, (float, int)) else v


def sketch(c, axis, distance, name):
    plane = {
        "xy": c.xYConstructionPlane,
        "yz": c.yZConstructionPlane,
        "xz": c.xZConstructionPlane,
    }[axis]
    if distance != 0:
        inp = c.constructionPlanes.createInput()
        inp.setByOffset(plane, V(mm(distance)))
        plane = c.constructionPlanes.add(inp)
        plane.name = name + " datum"
    s = c.sketches.add(plane)
    s.name = name + " profile"
    return s


def project(s, axis, x, y):
    xyz = {"xy": (x, y, 0), "xz": (x, 0, y), "yz": (0, x, y)}[axis]
    pos = s.modelToSketchSpace(P(*(n / 10 for n in xyz)))
    return P(pos.x, pos.y, 0)


def outline(s, axis, x0, y0, x1, y1, r=0):
    p = lambda xy: project(s, axis, *xy)
    if r == 0:
        s.sketchCurves.sketchLines.addTwoPointRectangle(p((x0, y0)), p((x1, y1)))
        return
    # Tangent quarter circles, oriented consistently in each principal plane.
    pts = [
        (x0 + r, y0),
        (x1 - r, y0),
        (x1, y0 + r),
        (x1, y1 - r),
        (x1 - r, y1),
        (x0 + r, y1),
        (x0, y1 - r),
        (x0, y0 + r),
    ]
    centers = [(x1 - r, y0 + r), (x1 - r, y1 - r), (x0 + r, y1 - r), (x0 + r, y0 + r)]
    for i, cen in enumerate(centers):
        a = pts[2 * i]
        b = pts[2 * i + 1]
        end = pts[(2 * i + 2) % 8]
        s.sketchCurves.sketchLines.addByTwoPoints(p(a), p(b))
        halfway = (
            cen[0] + (b[0] + end[0] - 2 * cen[0]) / math.sqrt(2),
            cen[1] + (b[1] + end[1] - 2 * cen[1]) / math.sqrt(2),
        )
        s.sketchCurves.sketchArcs.addByThreePoints(p(b), p(halfway), p(end))


def extrude(c, prof, amount, op, name):
    ex = c.features.extrudeFeatures
    inp = ex.createInput(prof, op)
    inp.setDistanceExtent(False, V(mm(amount)))
    f = ex.add(inp)
    f.name = name
    return f


def extrusion(c, s, amount, op, name):
    assert s.profiles.count > 0, name
    profiles = objects(list(s.profiles))
    return extrude(c, profiles, amount, op, name)


def source_body(app, doc, c, name):
    tmp = F.TemporaryBRepManager.get()
    other = app.importManager.importToNewDocument(
        app.importManager.createSTEPImportOptions(str(SOURCE / (name + ".step")))
    )
    log("Imported " + name)
    bodies = [
        b
        for component in F.Design.cast(app.activeProduct).allComponents
        for b in component.bRepBodies
    ]
    assert len(bodies) == 1, name
    shape = tmp.copy(bodies[0])
    other.close(False)
    doc.activate()
    log("Copied " + name)
    f = c.features.baseFeatures.add()
    f.name = "V5 " + name
    f.startEdit()
    b = c.bRepBodies.add(shape, f)
    b.name = name
    f.finishEdit()
    return f.bodies.item(0)


def part(root, name, xyz):
    m = C.Matrix3D.create()
    m.translation = C.Vector3D.create(*(i / 10 for i in xyz))
    c = root.occurrences.addNewComponent(m).component
    c.name = name
    return c


def build():
    OUTPUT.mkdir(exist_ok=True)
    app = C.Application.get()
    doc = app.documents.add(C.DocumentTypes.FusionDesignDocumentType)
    doc.name = "XGO V5 - 2S2P battery carrier"
    d = F.Design.cast(app.activeProduct)
    d.designIntent = F.DesignIntentTypes.HybridDesignIntentType
    d.designType = F.DesignTypes.ParametricDesignType
    d.userParameters.add(
        "AddedDepth",
        V("20.5 mm"),
        "mm",
        "Distance between the two stock mounting interfaces added for this pack",
    )
    c = part(d.rootComponent, "V5 2S2P battery carrier", (0, 0, 0))
    log("Import board interface")
    b = source_body(app, doc, c, "Board-side mount")
    log("Added lower mount")
    faces = [
        f
        for f in b.faces
        if abs(f.boundingBox.minPoint.z - 2) < 1e-5
        and abs(f.boundingBox.maxPoint.z - 2) < 1e-5
    ]
    assert len(faces) > 0
    extrude(
        c,
        max(faces, key=lambda f: f.area),
        "AddedDepth",
        JOIN,
        "Continue factory cage wall between mounting faces",
    )
    log("Bridge made")
    upper = source_body(app, doc, c, "Chassis-side mount")
    mv = c.features.moveFeatures
    mi = mv.createInput2(objects([upper]))
    mi.defineAsTranslateXYZ(V("0 mm"), V("0 mm"), V("AddedDepth"), False)
    mv.add(mi).name = "Space chassis interface for deeper pack"
    high = max(c.bRepBodies, key=lambda b: b.boundingBox.minPoint.z)
    low = min(c.bRepBodies, key=lambda b: b.boundingBox.minPoint.z)
    join = c.features.combineFeatures
    ci = join.createInput(low, objects([high]))
    ci.operation = JOIN
    join.add(ci).name = "Unite stock chassis mounting ears"
    log("Both interfaces joined")
    cx = -0.058
    cy = -0.05
    bar_y = -3.5
    s = sketch(c, "xy", 7.5, "Battery and insertion envelope")
    outline(s, "xy", cx - 19.35, cy - 34.2, cx + 19.35, cy + 34.2)
    extrusion(c, s, "AddedDepth + 22 mm", CUT, "Clear pack envelope and stock ribs")
    log("Pocket")
    s = sketch(c, "xy", 5.5, "Pack seat")
    for y in (-14.0, 14.0):
        outline(s, "xy", -8, y - 2.2, 8, y + 2.2, 1.6)
    extrusion(c, s, 2, JOIN, "Form coplanar battery support lands")
    s = sketch(c, "xy", 7.5, "Top lead exit")
    outline(s, "xy", cx - 7, 32, cx + 7, 39)
    extrusion(c, s, "AddedDepth + 22 mm", CUT, "Open 14 mm wire exit")
    s = sketch(c, "yz", -30, "Side relief")
    for y in (-17, 17):
        outline(s, "yz", y - 10, 24.5, y + 10, 35.5, 4)
    extrusion(c, s, 60, CUT, "Round ventilation windows in both walls")
    s = sketch(c, "xz", 0, "Lead restraint")
    for x in (10.0, 16.0):
        outline(s, "xz", x - 1.3, 29, x + 1.3, 34, 1)
    extrusion(c, s, -40, CUT, "Cut paired external lead tie slots")
    log("Vents, exit, strain relief")
    s = sketch(c, "xy", "AddedDepth + 24.5 mm", "Keeper pocket")
    outline(s, "xy", -26, bar_y - 4.7, 26, bar_y + 4.7)
    extrusion(c, s, 7, CUT, "Recess removable keeper below chassis face")
    s = sketch(c, "xy", "AddedDepth + 18.5 mm", "Keeper screw lands")
    for x in (cx - 22, cx + 22):
        outline(s, "xy", x - 2.9, bar_y - 4.2, x + 2.9, bar_y + 4.2, 2.0)
    extrusion(c, s, 6, JOIN, "Add two protected keeper screw bosses")
    s = sketch(c, "xy", "AddedDepth + 18.45 mm", "Inside boss clearance")
    outline(s, "xy", cx - 19.35, cy - 34.2, cx + 19.35, cy + 34.2)
    extrusion(c, s, 6.2, CUT, "Align inner edges of bosses to pack envelope")
    s = sketch(c, "xy", "AddedDepth + 24.5 mm", "Keeper pilots")
    for x in (cx - 22, cx + 22):
        s.sketchCurves.sketchCircles.addByCenterRadius(P(x / 10, bar_y / 10, 0), 0.0825)
    extrusion(c, s, -5, CUT, "Blind keeper pilot bores")
    log("Carrier complete")
    k = part(d.rootComponent, "Removable pack keeper", (cx, bar_y, 45.0))
    s = sketch(k, "xy", 0, "Retaining bar")
    outline(s, "xy", -25, -4.2, 25, 4.2, 3.3)
    extrusion(k, s, 2.15, NEW, "Form keeper with rounded ends")
    s = sketch(k, "xy", 2.15, "Keeper screws")
    pt = objects([s.sketchPoints.add(P(x / 10, 0, 0)) for x in (-22, 22)])
    hole = k.features.holeFeatures
    hi = hole.createCountersinkInput(V("2.25 mm"), V("4.25 mm"), V("90 deg"))
    hi.setPositionBySketchPoints(pt)
    hi.setDistanceExtent(V("2.4 mm"))
    hole.add(hi).name = "Countersink M2 flat-head keeper screws"
    log("Keeper complete")
    assert c.bRepBodies.count == k.bRepBodies.count == 1
    exp = d.exportManager
    for comp, file in [(c, "V5_2S2P_carrier"), (k, "V5_2S2P_keeper")]:
        body = comp.bRepBodies.item(0)
        body.name = comp.name
        assert body.isSolid
        m = exp.createSTLExportOptions(body, str(OUTPUT / (file + ".stl")))
        m.unitType = F.DistanceUnits.MillimeterDistanceUnits
        m.meshRefinement = F.MeshRefinementSettings.MeshRefinementHigh
        assert exp.execute(m)
        log(file + " STL")
    assert exp.execute(
        exp.createSTEPExportOptions(str(OUTPUT / "V5_2S2P_assembly.step"))
    )
    log("STEP")
    vp = app.activeViewport
    vp.visualStyle = C.VisualStyles.ShadedVisualStyle
    cam = vp.camera
    cam.eye = P(10, 7, 11)
    cam.target = P(0, 0, 2)
    cam.upVector = C.Vector3D.create(0, 0, 1)
    cam.isSmoothTransition = False
    vp.camera = cam
    vp.fit()
    vp.refresh()
    assert exp.execute(
        exp.createFusionArchiveExportOptions(str(OUTPUT / "V5_2S2P_assembly.f3d"))
    )
    log("F3D exported")

    print("Complete", d.timeline.count)


def run(_):
    try:
        build()
    except:
        log(traceback.format_exc())
        raise

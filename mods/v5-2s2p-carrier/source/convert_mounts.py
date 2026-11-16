"""Convert the prepared mounting interfaces to STEP using FreeCAD's Python runtime."""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "BuildV5Carrier"
    )
    args = parser.parse_args()
    # FreeCAD's bundled macOS Python has its FreeCAD modules under Resources/lib.
    freecad_lib = os.environ.get(
        "FREECAD_LIB", "/Applications/FreeCAD.app/Contents/Resources/lib"
    )
    if Path(freecad_lib).is_dir():
        sys.path.append(freecad_lib)
    import FreeCAD  # noqa: F401  (initialize the FreeCAD runtime)
    import Mesh
    import Part

    for name in ("Board-side mount", "Chassis-side mount"):
        mesh = Mesh.Mesh(str(args.out / (name + ".stl")))
        shape = Part.Shape()
        shape.makeShapeFromMesh(mesh.Topology, 0.000002)
        if len(shape.Shells) != 1:
            raise ValueError(f"{name} was not a single shell")
        solid = Part.makeSolid(shape.Shells[0]).removeSplitter()
        if not solid.isValid():
            raise ValueError(f"{name} could not be converted to a valid solid")
        solid.exportStep(str(args.out / (name + ".step")))


if __name__ == "__main__":
    main()

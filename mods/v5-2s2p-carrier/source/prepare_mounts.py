"""Extract mount interfaces from the factory V5 carrier in its own print frame."""

import argparse
from pathlib import Path

import manifold3d
import trimesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("factory_stl", type=Path)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "BuildV5Carrier"
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    stock = trimesh.load_mesh(args.factory_stl)
    solid = manifold3d.Manifold(
        manifold3d.Mesh(stock.vertices.astype("float32"), stock.faces.astype("uint32"))
    )
    if solid.status() != manifold3d.Error.NoError:
        raise ValueError(f"Invalid factory mesh: {solid.status()}")
    upper, lower = solid.simplify(0.075).split_by_plane((0, 0, 1), 20.0)
    for name, half in (("Chassis-side mount", upper), ("Board-side mount", lower)):
        mesh = half.to_mesh()
        part = trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts)
        if not part.is_volume or part.body_count != 1:
            raise ValueError(f"Invalid {name} mesh")
        part.export(args.out / (name + ".stl"))


if __name__ == "__main__":
    main()

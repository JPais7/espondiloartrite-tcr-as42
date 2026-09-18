#!/usr/bin/env python3
"""Assess whether one compact binder footprint can engage the AS4.2 hotspot."""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from analyze_tcr_surface import AA3_TO_1, VDW, parse_pdb, sphere_points  # noqa: E402


TARGET = set(range(95, 104))
KEY_RESIDUES = [98, 99, 100, 101]


def exposed_surface(atoms, probe=1.4, n_points=480):
    unit = sphere_points(n_points)
    xyz = np.array([a["xyz"] for a in atoms])
    radii = np.array([VDW.get(a["element"], 1.70) + probe for a in atoms])
    records = []
    for i, atom in enumerate(atoms):
        r = radii[i]
        samples = atom["xyz"] + r * unit
        center_d2 = np.sum((xyz - atom["xyz"]) ** 2, axis=1)
        possible = np.where((center_d2 < (r + radii) ** 2) & (center_d2 > 1e-8))[0]
        accessible = np.ones(n_points, dtype=bool)
        for j in possible:
            accessible &= np.sum((samples - xyz[j]) ** 2, axis=1) >= radii[j] ** 2
        area_per_point = 4.0 * math.pi * r * r / n_points
        for point in samples[accessible]:
            records.append((atom, point, area_per_point))
    return records


def weighted_centroid(points):
    xyz = np.array([p for p, _ in points])
    w = np.array([a for _, a in points])
    return np.average(xyz, axis=0, weights=w)


def angle_deg(a, b):
    c = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def analyze(pdb):
    all_atoms = parse_pdb(Path("data/raw") / f"{pdb}.pdb")
    tcr = [a for a in all_atoms if a["chain"] in {"D", "F"}]
    surface = exposed_surface(tcr)
    by_residue = defaultdict(list)
    for atom, point, area in surface:
        key = (atom["chain"], atom["resseq"], atom["resname"])
        by_residue[key].append((point, area))

    tcr_center = np.mean([a["xyz"] for a in tcr], axis=0)
    centers, normals, areas = {}, {}, {}
    for resseq in KEY_RESIDUES:
        key = next(k for k in by_residue if k[0] == "F" and k[1] == resseq)
        centers[resseq] = weighted_centroid(by_residue[key])
        normals[resseq] = centers[resseq] - tcr_center
        areas[resseq] = sum(a for _, a in by_residue[key])

    pairwise = {}
    for i, a in enumerate(KEY_RESIDUES):
        for b in KEY_RESIDUES[i + 1:]:
            pairwise[f"{a}-{b}"] = {
                "surface_centroid_distance_A": round(float(np.linalg.norm(centers[a] - centers[b])), 2),
                "outward_normal_angle_deg": round(angle_deg(normals[a], normals[b]), 1),
            }

    # Approximate a compact binder footprint as exposed target surface within
    # 12 A of the F98 surface centroid. This is a geometric screen, not docking.
    footprint = defaultdict(float)
    for atom, point, area in surface:
        if np.linalg.norm(point - centers[98]) <= 12.0:
            footprint[(atom["chain"], atom["resseq"], atom["resname"])] += area
    total = sum(footprint.values())
    core = sum(v for (ch, res, _), v in footprint.items() if ch == "F" and res in TARGET)
    key_area = sum(v for (ch, res, _), v in footprint.items() if ch == "F" and res in KEY_RESIDUES)
    alpha = sum(v for (ch, _, _), v in footprint.items() if ch == "D")
    ranked = sorted(footprint.items(), key=lambda kv: kv[1], reverse=True)

    return {
        "pdb": pdb,
        "key_residue_accessible_area_A2": {str(k): round(v, 2) for k, v in areas.items()},
        "pairwise_geometry": pairwise,
        "footprint_radius_A": 12.0,
        "footprint_total_A2": round(total, 2),
        "cdr3beta_core_fraction": round(core / total, 3),
        "F98_S99_T100_D101_fraction": round(key_area / total, 3),
        "alpha_chain_fraction": round(alpha / total, 3),
        "top_footprint_residues": [
            {"chain": k[0], "resseq": k[1], "residue": AA3_TO_1[k[2]], "area_A2": round(v, 2)}
            for k, v in ranked[:15]
        ],
    }


def main():
    results = {pdb: analyze(pdb) for pdb in ("7N2O", "7N2N")}
    Path("results/interface_geometry.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Low-cost structural feasibility analysis for the AS4.2 TCR.

Uses only NumPy. Implements a Shrake-Rupley solvent-accessible surface
calculation and a Kabsch structural alignment so the analysis is reproducible
without a molecular-modelling suite.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}

# Bondi-like radii (A); sufficient for a comparative feasibility screen.
VDW = {"C": 1.70, "N": 1.55, "O": 1.52, "S": 1.80, "P": 1.80}


def parse_pdb(path: Path):
    atoms = []
    seen = set()
    for line in path.read_text().splitlines():
        if not line.startswith("ATOM  "):
            continue
        alt = line[16]
        if alt not in (" ", "A"):
            continue
        key = (line[21], int(line[22:26]), line[26], line[12:16].strip())
        if key in seen:
            continue
        seen.add(key)
        element = line[76:78].strip() or line[12:16].strip()[0]
        if element == "H":
            continue
        atoms.append({
            "name": line[12:16].strip(), "resname": line[17:20].strip(),
            "chain": line[21], "resseq": int(line[22:26]), "icode": line[26].strip(),
            "xyz": np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
            "element": element,
        })
    return atoms


def sphere_points(n=480):
    # Fibonacci sphere: deterministic, near-uniform surface sampling.
    i = np.arange(n, dtype=float)
    y = 1.0 - 2.0 * (i + 0.5) / n
    radius = np.sqrt(1.0 - y * y)
    theta = math.pi * (3.0 - math.sqrt(5.0)) * i
    return np.column_stack((np.cos(theta) * radius, y, np.sin(theta) * radius))


def sasa(atoms, context_atoms, probe=1.4, n_points=480):
    """Return per-atom SASA for atoms, occluded by context_atoms."""
    points = sphere_points(n_points)
    context_xyz = np.array([a["xyz"] for a in context_atoms])
    context_r = np.array([VDW.get(a["element"], 1.70) + probe for a in context_atoms])
    out = []
    for atom in atoms:
        r = VDW.get(atom["element"], 1.70) + probe
        samples = atom["xyz"] + r * points
        center_dist2 = np.sum((context_xyz - atom["xyz"]) ** 2, axis=1)
        possible = np.where(center_dist2 < (r + context_r) ** 2)[0]
        # Exclude the atom itself by requiring non-zero centre distance.
        possible = possible[center_dist2[possible] > 1e-8]
        accessible = np.ones(n_points, dtype=bool)
        for j in possible:
            accessible &= np.sum((samples - context_xyz[j]) ** 2, axis=1) >= context_r[j] ** 2
            if not accessible.any():
                break
        out.append(4.0 * math.pi * r * r * accessible.mean())
    return np.array(out)


def residue_sasa(atoms, values):
    totals = {}
    for atom, value in zip(atoms, values):
        key = (atom["chain"], atom["resseq"], atom["icode"], atom["resname"])
        totals[key] = totals.get(key, 0.0) + float(value)
    return totals


def ca_map(atoms, chain="F"):
    return {(a["resseq"], a["icode"]): a["xyz"] for a in atoms
            if a["chain"] == chain and a["name"] == "CA"}


def kabsch(mobile, reference):
    mc, rc = mobile.mean(0), reference.mean(0)
    m, r = mobile - mc, reference - rc
    u, _, vt = np.linalg.svd(m.T @ r)
    d = np.linalg.det(u @ vt)
    rot = u @ np.diag([1.0, 1.0, d]) @ vt
    return rot, rc - mc @ rot


def rmsd(a, b):
    return float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1))))


def analyze_pair(pdb_o, pdb_n, outdir, n_points=480):
    structures = {p.stem: parse_pdb(p) for p in (pdb_o, pdb_n)}
    rows = []
    summaries = {}
    target_res = set(range(95, 104))

    for name, all_atoms in structures.items():
        tcr = [a for a in all_atoms if a["chain"] in {"D", "F"}]
        target_atoms = [a for a in tcr if a["chain"] == "F" and a["resseq"] in target_res]
        isolated = sasa(tcr, tcr, n_points=n_points)
        bound = sasa(tcr, all_atoms, n_points=n_points)
        iso_res, bound_res = residue_sasa(tcr, isolated), residue_sasa(tcr, bound)

        for key in sorted(iso_res, key=lambda k: (k[0], k[1], k[2])):
            chain, resseq, icode, resname = key
            if chain == "F" and resseq in target_res:
                rows.append({
                    "structure": name, "chain": chain, "resseq": resseq,
                    "residue": AA3_TO_1[resname], "sasa_tcr_isolated_A2": round(iso_res[key], 2),
                    "sasa_in_pmhc_complex_A2": round(bound_res[key], 2),
                    "pmhc_buried_A2": round(iso_res[key] - bound_res[key], 2),
                })

        # Candidate anchoring residues: alpha/beta residues with exposed SASA and
        # any heavy atom within 8 A of the characteristic nine-residue segment.
        target_xyz = np.array([a["xyz"] for a in target_atoms])
        patch = []
        residue_atoms = {}
        for a in tcr:
            key = (a["chain"], a["resseq"], a["icode"], a["resname"])
            residue_atoms.setdefault(key, []).append(a["xyz"])
        for key, xyzs in residue_atoms.items():
            xyzs = np.array(xyzs)
            min_dist = float(np.sqrt(np.min(np.sum((xyzs[:, None, :] - target_xyz[None, :, :]) ** 2, axis=2))))
            if min_dist <= 8.0 and iso_res[key] >= 20.0:
                patch.append({
                    "chain": key[0], "resseq": key[1], "residue": AA3_TO_1[key[3]],
                    "sasa_A2": round(iso_res[key], 2), "distance_to_motif_A": round(min_dist, 2),
                })
        patch.sort(key=lambda x: (x["chain"], x["resseq"]))
        summaries[name] = {
            "target_total_sasa_isolated_A2": round(sum(iso_res[k] for k in iso_res if k[0] == "F" and k[1] in target_res), 2),
            "target_total_sasa_bound_A2": round(sum(bound_res[k] for k in bound_res if k[0] == "F" and k[1] in target_res), 2),
            "candidate_patch_residues": patch,
        }

    # Align beta-chain framework, excluding CDR3 beta (residues 92-105).
    maps = {name: ca_map(atoms) for name, atoms in structures.items()}
    common = sorted(set.intersection(*(set(m) for m in maps.values())))
    framework = [k for k in common if k[0] <= 110 and not 92 <= k[0] <= 105]
    target = [k for k in common if 95 <= k[0] <= 103]
    a = np.array([maps[pdb_n.stem][k] for k in framework])
    b = np.array([maps[pdb_o.stem][k] for k in framework])
    rot, trans = kabsch(a, b)
    aligned_framework = a @ rot + trans
    ta = np.array([maps[pdb_n.stem][k] for k in target]) @ rot + trans
    tb = np.array([maps[pdb_o.stem][k] for k in target])
    comparison = {
        "alignment_chain": "F", "framework_CA_count": len(framework),
        "framework_CA_RMSD_A": round(rmsd(aligned_framework, b), 3),
        "target_CA_RMSD_A": round(rmsd(ta, tb), 3),
        "target_per_residue_CA_displacement_A": {
            str(k[0]): round(float(np.linalg.norm(x - y)), 3)
            for k, x, y in zip(target, ta, tb)
        },
    }

    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "cdr3b_sasa.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    metadata = {"sasa_sphere_points": n_points, "probe_radius_A": 1.4}
    (outdir / "analysis.json").write_text(json.dumps({"metadata": metadata, "structures": summaries, "comparison": comparison}, indent=2) + "\n")
    return summaries, comparison


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdb-o", type=Path, default=Path("data/raw/7N2O.pdb"))
    parser.add_argument("--pdb-n", type=Path, default=Path("data/raw/7N2N.pdb"))
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    parser.add_argument("--points", type=int, default=480)
    args = parser.parse_args()
    summaries, comparison = analyze_pair(args.pdb_o, args.pdb_n, args.outdir, args.points)
    print(json.dumps({"structures": summaries, "comparison": comparison}, indent=2))


if __name__ == "__main__":
    main()

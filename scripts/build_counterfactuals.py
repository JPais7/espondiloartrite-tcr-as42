#!/usr/bin/env python3
"""Build explicit, fixed-backbone AS4.2 counterfactual PDB models.

Alanine substitutions retain N/CA/C/O/CB. F98Y uses the experimentally
resolved 7N2S tyrosine side chain after beta-framework alignment. Natural
motif replacements are represented by their experimental structures rather
than fabricated coordinates. These are perturbation models, not relaxed
binding predictions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_tcr_surface import ca_map, kabsch, parse_pdb


SOURCE = Path("data/raw/7N2O.pdb")
OUTDIR = Path("data/counterfactuals")
BACKBONE_CB = {"N", "CA", "C", "O", "OXT", "CB"}


def replace_residue(lines, chain, resseq, new_resname, keep_atoms):
    out = []
    for line in lines:
        if not line.startswith("ATOM  ") or line[21] != chain or int(line[22:26]) != resseq:
            out.append(line)
            continue
        if line[12:16].strip() not in keep_atoms:
            continue
        out.append(line[:17] + f"{new_resname:>3}" + line[20:])
    return out


def f98y_from_7n2s(lines):
    target = parse_pdb(SOURCE)
    donor = parse_pdb(Path("data/raw/7N2S.pdb"))
    tmap, dmap = ca_map(target, "F"), ca_map(donor, "F")
    common = sorted(set(tmap) & set(dmap))
    framework = [k for k in common if k[0] <= 110 and not 92 <= k[0] <= 105]
    rot, trans = kabsch(np.array([dmap[k] for k in framework]),
                        np.array([tmap[k] for k in framework]))
    donor_atoms = [a for a in donor if a["chain"] == "F" and a["resseq"] == 98]
    serial = max(int(x[6:11]) for x in lines if x.startswith(("ATOM  ", "HETATM"))) + 1
    out, inserted = [], False
    for line in lines:
        if line.startswith("ATOM  ") and line[21] == "F" and int(line[22:26]) == 98:
            if not inserted:
                for a in donor_atoms:
                    xyz = a["xyz"] @ rot + trans
                    name = a["name"]
                    element = a["element"]
                    out.append(f"ATOM  {serial:5d} {name:>4} TYR F  98    {xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00 20.00          {element:>2}")
                    serial += 1
                inserted = True
            continue
        out.append(line)
    return out


def write_pdb(name, lines, mutation, method):
    path = OUTDIR / f"{name}.pdb"
    remark = [
        "REMARK 950 COMPUTATIONAL COUNTERFACTUAL; NOT AN EXPERIMENTAL STRUCTURE",
        f"REMARK 950 SOURCE 7N2O; MUTATION {mutation}; METHOD {method}",
    ]
    path.write_text("\n".join(remark + lines) + "\n")
    return {"id": name, "path": str(path), "mutation": mutation, "method": method,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    lines = SOURCE.read_text().splitlines()
    records = []
    records.append(write_pdb("AS4_2_F98Y_fixed_backbone", f98y_from_7n2s(lines), "F:F98Y",
                             "7N2S Y98 side chain transferred after beta-framework Kabsch alignment"))
    for wt, pos in [("F", 98), ("S", 99), ("T", 100), ("D", 101)]:
        records.append(write_pdb(f"AS4_2_{wt}{pos}A_fixed_backbone",
                                 replace_residue(lines, "F", pos, "ALA", BACKBONE_CB),
                                 f"F:{wt}{pos}A", "side-chain truncation to alanine; no relaxation"))
    natural = [
        {"id": "VGLYSTDTQ", "pdbid": "7N2S", "chain": "F", "residues": "95-103"},
        {"id": "VGTYSTDTQ", "pdbid": "8CX4", "chain": "F", "residues": "95-103"},
        {"id": "PATYSTDTQ_9PBG", "pdbid": "9PBG", "chain": "E", "residues": "95-103"},
        {"id": "PATYSTDTQ_9PBH", "pdbid": "9PBH", "chain": "E", "residues": "95-103"},
    ]
    manifest = {
        "schema_version": 1,
        "reference": "data/raw/7N2O.pdb chain F",
        "fixed_backbone_models": records,
        "natural_motif_counterfactuals": natural,
        "limitations": [
            "No side-chain repacking or energy minimization was performed.",
            "Point-mutant models are suitable only for residue-dependence perturbation tests.",
            "Natural replacements use experimental structures and retain their observed conformations.",
        ],
    }
    (OUTDIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixed_backbone_models": len(records), "natural_models": len(natural)}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Quantify local chemistry at the AS4.2 F98 specificity hotspot."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from analyze_tcr_surface import ca_map, kabsch, parse_pdb, sasa  # noqa: E402


STRUCTURES = {
    "7N2O": ("AS4.2", "PHE"),
    "7N2N": ("AS4.2", "PHE"),
    "7N2P": ("AS4.3", "TYR"),
    "7N2Q": ("AS4.3", "TYR"),
    "7N2S": ("AS3.1", "TYR"),
}


def pdb_bfactors(path, chain="F", resseq=98):
    values = {}
    for line in path.read_text().splitlines():
        if (line.startswith("ATOM  ") and line[21] == chain
                and int(line[22:26]) == resseq and line[16] in (" ", "A")):
            values[line[12:16].strip()] = float(line[60:66])
    return values


def main():
    parsed = {pdb: parse_pdb(Path("data/raw") / f"{pdb}.pdb") for pdb in STRUCTURES}
    reference_ca = ca_map(parsed["7N2O"])
    rows = []

    for pdb, (label, expected_resname) in STRUCTURES.items():
        atoms = parsed[pdb]
        beta_ca = ca_map(atoms)
        common = sorted(set(reference_ca) & set(beta_ca))
        framework = [k for k in common if k[0] <= 110 and not 92 <= k[0] <= 105]
        mobile = np.array([beta_ca[k] for k in framework])
        fixed = np.array([reference_ca[k] for k in framework])
        rot, trans = kabsch(mobile, fixed)

        tcr = [a for a in atoms if a["chain"] in {"D", "F"}]
        atom_sasa = sasa(tcr, tcr, n_points=960)
        residue = [(a, float(v)) for a, v in zip(tcr, atom_sasa)
                   if a["chain"] == "F" and a["resseq"] == 98]
        if not residue or any(a["resname"] != expected_resname for a, _ in residue):
            raise ValueError(f"Unexpected residue F98 in {pdb}")

        sidechain = [(a, v) for a, v in residue if a["name"] not in {"N", "CA", "C", "O"}]
        ring_names = {"CG", "CD1", "CD2", "CE1", "CE2", "CZ"}
        ring_sasa = sum(v for a, v in sidechain if a["name"] in ring_names)
        oh_sasa = sum(v for a, v in sidechain if a["name"] == "OH")
        bf = pdb_bfactors(Path("data/raw") / f"{pdb}.pdb")
        side_b = [bf[a["name"]] for a, _ in sidechain if a["name"] in bf]

        coords = {a["name"]: a["xyz"] @ rot + trans for a, _ in sidechain}
        ref_atoms = {a["name"]: a["xyz"] for a in parsed["7N2O"]
                     if a["chain"] == "F" and a["resseq"] == 98
                     and a["name"] not in {"N", "CA", "C", "O"}}
        shared = sorted(set(coords) & set(ref_atoms))
        shared_rmsd = float(np.sqrt(np.mean([
            np.sum((coords[n] - ref_atoms[n]) ** 2) for n in shared
        ])))

        # For Tyr, measure how far its terminal oxygen protrudes beyond the
        # corresponding phenyl para carbon (CZ) after framework alignment.
        oh_to_ref_cz = float(np.linalg.norm(coords["OH"] - ref_atoms["CZ"])) if "OH" in coords else None
        rows.append({
            "pdb": pdb, "tcr": label, "residue_98": expected_resname,
            "sidechain_SASA_A2": round(sum(v for _, v in sidechain), 2),
            "aromatic_ring_SASA_A2": round(ring_sasa, 2),
            "tyr_OH_SASA_A2": round(oh_sasa, 2),
            "shared_sidechain_atom_RMSD_vs_7N2O_A": round(shared_rmsd, 3),
            "tyr_OH_to_7N2O_Phe_CZ_A": None if oh_to_ref_cz is None else round(oh_to_ref_cz, 3),
            "mean_sidechain_B_factor_A2": round(float(np.mean(side_b)), 2),
        })

    out = Path("results/hotspot_chemistry.csv")
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    Path("results/hotspot_chemistry.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()

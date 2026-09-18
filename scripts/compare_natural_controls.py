#!/usr/bin/env python3
"""Compare AS4.2 with experimentally solved natural near-neighbour TCRs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from analyze_tcr_surface import AA3_TO_1, ca_map, kabsch, parse_pdb, residue_sasa, rmsd, sasa


STRUCTURES = {
    "7N2O": {"label": "AS4.2", "core": "VGLFSTDTQ"},
    "7N2N": {"label": "AS4.2", "core": "VGLFSTDTQ"},
    "7N2P": {"label": "AS4.3", "core": "VATYSTDTQ"},
    "7N2Q": {"label": "AS4.3", "core": "VATYSTDTQ"},
    "7N2S": {"label": "AS3.1", "core": "VGLYSTDTQ"},
}


def observed_residues(atoms, chain="F"):
    seen, residues = set(), []
    for a in atoms:
        if a["chain"] != chain:
            continue
        key = (a["resseq"], a["icode"])
        if key not in seen:
            seen.add(key)
            residues.append((key, AA3_TO_1[a["resname"]]))
    return residues


def locate_core(atoms, core):
    residues = observed_residues(atoms)
    seq = "".join(x[1] for x in residues)
    start = seq.find(core)
    if start < 0:
        raise ValueError(f"Core {core} not found")
    return [residues[i][0] for i in range(start, start + len(core))]


def main():
    data = {pdb: parse_pdb(Path("data/raw") / f"{pdb}.pdb") for pdb in STRUCTURES}
    reference = data["7N2O"]
    reference_ca = ca_map(reference)
    reference_core_keys = locate_core(reference, STRUCTURES["7N2O"]["core"])
    rows, details = [], {}

    for pdb, meta in STRUCTURES.items():
        atoms = data[pdb]
        beta_ca = ca_map(atoms)
        core_keys = locate_core(atoms, meta["core"])
        if [k[0] for k in core_keys] != [k[0] for k in reference_core_keys]:
            raise ValueError(f"Inconsistent core numbering in {pdb}")
        common = sorted(set(reference_ca) & set(beta_ca))
        framework = [k for k in common if k[0] <= 110 and not 92 <= k[0] <= 105]
        mobile = np.array([beta_ca[k] for k in framework])
        fixed = np.array([reference_ca[k] for k in framework])
        rot, trans = kabsch(mobile, fixed)
        aligned = mobile @ rot + trans
        core_mobile = np.array([beta_ca[k] for k in core_keys]) @ rot + trans
        core_fixed = np.array([reference_ca[k] for k in reference_core_keys])

        tcr = [a for a in atoms if a["chain"] in {"D", "F"}]
        iso = residue_sasa(tcr, sasa(tcr, tcr))
        core_sasa = sum(v for k, v in iso.items() if k[0] == "F" and (k[1], k[2]) in set(core_keys))
        displacements = [float(np.linalg.norm(a - b)) for a, b in zip(core_mobile, core_fixed)]
        substitutions = [
            f"{a}{key[0]}{b}" for key, a, b in zip(core_keys, STRUCTURES["7N2O"]["core"], meta["core"]) if a != b
        ]
        row = {
            "pdb": pdb, "tcr": meta["label"], "cdr3beta_core": meta["core"],
            "substitutions_vs_AS4.2": ";".join(substitutions) or "none",
            "framework_CA_RMSD_A": round(rmsd(aligned, fixed), 3),
            "core_CA_RMSD_A": round(rmsd(core_mobile, core_fixed), 3),
            "max_core_CA_displacement_A": round(max(displacements), 3),
            "core_SASA_isolated_A2": round(core_sasa, 2),
        }
        rows.append(row)
        details[pdb] = {**row, "per_residue_CA_displacement_A": {
            str(k[0]): round(d, 3) for k, d in zip(core_keys, displacements)
        }}

    out = Path("results")
    with (out / "natural_control_comparison.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    (out / "natural_control_comparison.json").write_text(json.dumps(details, indent=2) + "\n")
    print(json.dumps(details, indent=2))


if __name__ == "__main__":
    main()

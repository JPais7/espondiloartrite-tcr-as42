#!/usr/bin/env python3
"""Place one designed binder against all preregistered TCR states.

Run inside the pinned Foundry environment.  The binder coordinates are taken
from an MPNN-designed complex (chain A). Each experimental TCR is aligned to
the 7N2O beta framework, cropped to its variable domains, and relabelled B/C.
The resulting CIF files are RF3 inputs; they are hypotheses, not structures.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from biotite.structure import AtomArray, concatenate
from biotite.structure.io import load_structure, save_structure


def ca_map(arr, chain):
    sel = (arr.chain_id == chain) & (arr.atom_name == "CA")
    return {int(r): xyz for r, xyz in zip(arr.res_id[sel], arr.coord[sel])}


def kabsch(mobile, reference):
    mc, rc = mobile.mean(0), reference.mean(0)
    m, r = mobile - mc, reference - rc
    u, _, vt = np.linalg.svd(m.T @ r)
    d = np.linalg.det(u @ vt)
    rot = u @ np.diag([1.0, 1.0, d]) @ vt
    return rot, rc - mc @ rot


def first(field):
    return field.split(",")[0]


def target_array(pdb, alpha, beta, reference_beta):
    arr = load_structure(pdb)
    mobile_beta = ca_map(arr, beta)
    common = sorted(set(reference_beta) & set(mobile_beta))
    framework = [r for r in common if r <= 110 and not 92 <= r <= 105]
    if len(framework) < 40:
        raise ValueError(f"Insufficient beta framework for {pdb}: {len(framework)}")
    rot, trans = kabsch(np.array([mobile_beta[r] for r in framework]),
                        np.array([reference_beta[r] for r in framework]))
    keep = np.isin(arr.chain_id, [alpha, beta]) & (arr.res_id <= 110)
    out = arr[keep].copy()
    out.coord = out.coord @ rot + trans
    out.chain_id[out.chain_id == alpha] = "B"
    out.chain_id[out.chain_id == beta] = "C"
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True,
                        help="MPNN output CIF containing binder chain A")
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    panel = {r["pdbid"]: r for r in csv.DictReader(open("data/phase1_5_negative_controls.csv"))}
    spec = json.load(open("config/pilot_target_spec.json"))
    candidate = load_structure(args.candidate)
    binder = candidate[candidate.chain_id == "A"].copy()
    if len(binder) == 0:
        raise ValueError("Candidate has no binder chain A")
    ref = load_structure("data/raw/7N2O.pdb")
    ref_beta = ca_map(ref, "F")
    states = []
    for item in spec["positives"] + spec["mandatory_negatives"]:
        pdbid = item["pdbid"]
        row = panel[pdbid]
        tcr = target_array(Path("data/raw") / f"{pdbid}.pdb",
                           first(row["alpha_chain"]), first(row["beta_chain"]), ref_beta)
        out = concatenate([binder, tcr])
        args.outdir.mkdir(parents=True, exist_ok=True)
        path = args.outdir / f"{args.candidate.stem}__{pdbid}.cif"
        save_structure(path, out)
        states.append({"state": pdbid, "path": str(path)})
    # Fixed-backbone point mutants retain the reference alpha/beta chains.
    for p in sorted(Path("data/counterfactuals").glob("AS4_2_*_fixed_backbone.pdb")):
        tcr = target_array(p, "D", "F", ref_beta)
        path = args.outdir / f"{args.candidate.stem}__{p.stem}.cif"
        save_structure(path, concatenate([binder, tcr]))
        states.append({"state": p.stem, "path": str(path)})
    (args.outdir / f"{args.candidate.stem}__manifest.json").write_text(
        json.dumps({"candidate": str(args.candidate), "states": states}, indent=2) + "\n"
    )
    print(json.dumps({"candidate": args.candidate.stem, "state_count": len(states)}))


if __name__ == "__main__":
    main()

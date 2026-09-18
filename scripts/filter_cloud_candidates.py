#!/usr/bin/env python3
"""Apply frozen sequence/contact filters to generated MPNN candidate poses."""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from biotite.structure.io import load_structure


AA3 = {"ALA":"A","ARG":"R","ASN":"N","ASP":"D","CYS":"C","GLN":"Q","GLU":"E",
       "GLY":"G","HIS":"H","ILE":"I","LEU":"L","LYS":"K","MET":"M","PHE":"F",
       "PRO":"P","SER":"S","THR":"T","TRP":"W","TYR":"Y","VAL":"V"}


def residue_sequence(arr, chain):
    sel = arr.chain_id == chain
    ids, seq, seen = [], [], set()
    for rid, name in zip(arr.res_id[sel], arr.res_name[sel]):
        key = int(rid)
        if key not in seen:
            seen.add(key); ids.append(key); seq.append(AA3.get(str(name), "X"))
    return ids, "".join(seq)


def entropy(seq):
    counts = Counter(seq)
    return -sum((n/len(seq))*math.log2(n/len(seq)) for n in counts.values())


def contact_residues(arr, cutoff):
    b = arr[(arr.chain_id == "A") & (arr.element != "H")]
    t = arr[np.isin(arr.chain_id, ["B", "C"]) & (arr.element != "H")]
    d2 = np.sum((b.coord[:, None, :] - t.coord[None, :, :])**2, axis=2)
    hit = np.any(d2 <= cutoff**2, axis=0)
    return {(str(c), int(r)) for c, r in zip(t.chain_id[hit], t.res_id[hit])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="results/pilot/cloud/mpnn/*.cif")
    ap.add_argument("--out", type=Path, default=Path("results/pilot/cloud/generation_prefilter.csv"))
    args = ap.parse_args()
    cfg = json.load(open("config/pilot_acceptance_criteria.json"))
    p = cfg["generation_pose_prefilter"]
    req = cfg["required"]
    rows = []
    for name in sorted(glob.glob(args.glob)):
        arr = load_structure(name)
        _, seq = residue_sequence(arr, "A")
        contacts = contact_residues(arr, p["heavy_atom_contact_cutoff_A"])
        beta_contacts = {r for c, r in contacts if c == "C"}
        core = sorted(beta_contacts & set(range(95, 104)))
        germline = sum(not (c == "C" and 91 <= r <= 105) for c, r in contacts)
        germline_fraction = germline / len(contacts) if contacts else 1.0
        ent = entropy(seq) if seq else 0.0
        max_fraction = max(Counter(seq).values()) / len(seq) if seq else 1.0
        reasons = []
        if not p["minimum_binder_length"] <= len(seq) <= p["maximum_binder_length"]: reasons.append("length")
        if "X" in seq: reasons.append("noncanonical")
        if ent < p["minimum_binder_sequence_shannon_entropy_bits"]: reasons.append("low_entropy")
        if max_fraction > p["maximum_single_amino_acid_fraction"]: reasons.append("single_AA_enrichment")
        if len(core) < req["minimum_distinct_core_residues_contacted"]: reasons.append("too_few_core_contacts")
        if 98 not in core: reasons.append("no_F98_contact")
        if len({99, 100, 101} & set(core)) < req["minimum_additional_hotspot_residues_contacted"]:
            reasons.append("too_few_additional_hotspots")
        if germline_fraction > req["maximum_germline_contact_fraction"]: reasons.append("germline_dominated")
        rows.append({"candidate": name, "binder_length": len(seq), "sequence_entropy_bits": round(ent,4),
                     "maximum_single_AA_fraction": round(max_fraction,4), "core_contacts": ";".join(map(str,core)),
                     "germline_contact_fraction": round(germline_fraction,4), "pass": not reasons,
                     "rejection_reasons": ";".join(reasons)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else ["candidate"]); w.writeheader(); w.writerows(rows)
    print(json.dumps({"evaluated":len(rows),"passed":sum(r["pass"] for r in rows)}))


if __name__ == "__main__": main()

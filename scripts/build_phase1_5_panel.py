#!/usr/bin/env python3
"""Build the Phase 1.5 negative-control panel from TCR3d records."""

from __future__ import annotations

import csv
import json
import re
import urllib.request
from pathlib import Path


TCR3D = {
    "alpha": "https://tcr3d.ibbr.umd.edu/tcra",
    "beta": "https://tcr3d.ibbr.umd.edu/tcrb",
}

SELECTED = {
    "7N2O": ("positive", "AS4.2 reference; TRAV21/TRBV9 with VGLFSTDTQ"),
    "7N2N": ("positive_replicate", "AS4.2 second experimental complex"),
    "7N2P": ("natural_near_negative", "AS4.3; TRAV21/TRBV9 with VATYSTDTQ"),
    "7N2Q": ("natural_near_negative", "AS4.3 replicate; TRAV21/TRBV9 with VATYSTDTQ"),
    "7N2S": ("natural_near_negative", "AS3.1; TRAV21/TRBV9 with VGLYSTDTQ"),
    "8CX4": ("near_motif_negative", "TRAV21/TRBV9 with VGTYSTDTQ"),
    "9PBG": ("near_motif_negative", "TRAV21/TRBV9 with PATYSTDTQ"),
    "9PBH": ("near_motif_negative", "TRAV21/TRBV9 with PATYSTDTQ replicate"),
    "8RYP": ("germline_hard_negative", "TRAV21/TRBV9 with unrelated CDR3 beta"),
    "8RYQ": ("germline_hard_negative", "TRAV21/TRBV9 with unrelated CDR3 beta replicate"),
    "5KS9": ("trbv9_alt_alpha_negative", "TRBV9 with TRAV20 and non-Y/FSTDTQ CDR3 beta"),
    "5KSA": ("trbv9_alt_alpha_negative", "TRBV9 with TRAV20 and non-Y/FSTDTQ CDR3 beta"),
    "9J4S": ("trbv9_alt_alpha_negative", "TRBV9 with TRAV3 and non-Y/FSTDTQ CDR3 beta"),
    "6ZKW": ("trav21_alt_beta_negative", "TRAV21 with TRBV6-5 and unrelated CDR3 beta"),
    "9YIR": ("trav21_alt_beta_negative", "TRAV21 with TRBV27 and unrelated CDR3 beta"),
}


def fetch_tcr3d(endpoint: str):
    html = urllib.request.urlopen(TCR3D[endpoint], timeout=30).read().decode()
    match = re.search(r"var data = (\[.*?\]);", html, re.S)
    if not match:
        raise RuntimeError(f"Could not find embedded TCR3d data for {endpoint}")
    return json.loads(match.group(1))


def one_record(records, pdbid):
    matches = [r for r in records if r["pdbid"] == pdbid and r.get("species") == "Human"]
    if not matches:
        return {}
    # Prefer exact gene matches, but keep approximate entries if that is all TCR3d provides.
    matches.sort(key=lambda r: (r.get("exact_match") != "exact", r.get("chain", "")))
    return matches[0]


def main():
    outdir = Path("data/provenance")
    outdir.mkdir(parents=True, exist_ok=True)
    alpha = fetch_tcr3d("alpha")
    beta = fetch_tcr3d("beta")
    (outdir / "tcr3d_alpha_records.json").write_text(json.dumps(alpha, indent=2) + "\n")
    (outdir / "tcr3d_beta_records.json").write_text(json.dumps(beta, indent=2) + "\n")

    rows = []
    for pdbid, (category, rationale) in SELECTED.items():
        a = one_record(alpha, pdbid)
        b = one_record(beta, pdbid)
        rows.append({
            "pdbid": pdbid,
            "category": category,
            "rationale": rationale,
            "alpha_chain": a.get("chain", ""),
            "alpha_gene": a.get("gene_name", ""),
            "alpha_cdr3": a.get("cdr3seq", ""),
            "alpha_gene_match": a.get("exact_match", ""),
            "beta_chain": b.get("chain", ""),
            "beta_gene": b.get("gene_name", ""),
            "beta_cdr3": b.get("cdr3seq", ""),
            "beta_gene_match": b.get("exact_match", ""),
            "species": a.get("species") or b.get("species", ""),
            "tcr3d_alpha_url": TCR3D["alpha"],
            "tcr3d_beta_url": TCR3D["beta"],
            "rcsb_url": f"https://www.rcsb.org/structure/{pdbid}",
        })

    with Path("data/phase1_5_negative_controls.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()


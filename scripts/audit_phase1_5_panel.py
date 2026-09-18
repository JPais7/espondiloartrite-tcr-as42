#!/usr/bin/env python3
"""Audit every Phase 1.5 TCR chain/CDR3 assignment against deposited PDB atoms.

This deliberately does not infer gene calls.  Gene provenance remains the raw
TCR3d record; this script verifies that the declared chains are TCR chains in
the PDB header and that the declared CDR3 sequences occur in resolved atoms.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from analyze_phase1_5_negatives import locate_sequence
from analyze_tcr_surface import parse_pdb


PANEL = Path("data/phase1_5_negative_controls.csv")
OUT = Path("results/pilot/panel_audit.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compnd_text(path: Path) -> str:
    return " ".join(line[10:].strip() for line in path.read_text().splitlines()
                    if line.startswith("COMPND"))


def chain_is_declared_tcr(header: str, chain: str, kind: str) -> bool:
    blocks = re.split(r"MOL_ID:\s*\d+;", header)
    for block in blocks:
        generic_tcr = re.search(r"T[ -]?CELL RECEPTOR|TCR[A-Z0-9.]|\bAS\d", block, re.I)
        chain_role = (re.search(r"ALPHA|TRAV", block, re.I) if kind == "alpha"
                      else re.search(r"BETA|TRBV", block, re.I))
        if generic_tcr or chain_role:
            match = re.search(r"CHAIN:\s*([^;]+)", block)
            if match and chain in [x.strip() for x in match.group(1).split(",")]:
                return True
    return False


def main() -> None:
    rows = list(csv.DictReader(PANEL.open()))
    audit = []
    for row in rows:
        pdb = Path("data/raw") / f"{row['pdbid']}.pdb"
        atoms = parse_pdb(pdb)
        header = compnd_text(pdb)
        item = {
            "pdbid": row["pdbid"],
            "category": row["category"],
            "pdb_sha256": sha256(pdb),
            "rcsb_url": row["rcsb_url"],
            "tcr3d_alpha_url": row["tcr3d_alpha_url"],
            "tcr3d_beta_url": row["tcr3d_beta_url"],
            "chains": {},
            "status": "pass",
        }
        for kind in ("alpha", "beta"):
            declared = [x.strip() for x in row[f"{kind}_chain"].split(",")]
            checks = []
            for chain in declared:
                try:
                    observed, keys = locate_sequence(atoms, chain, row[f"{kind}_cdr3"])
                    checks.append({
                        "chain": chain,
                        "declared_tcr_in_pdb_header": chain_is_declared_tcr(header, chain, kind),
                        "declared_cdr3": row[f"{kind}_cdr3"],
                        "observed_cdr3": observed,
                        "resolved_start": keys[0][0],
                        "resolved_end": keys[-1][0],
                        "exact_sequence_match": observed == row[f"{kind}_cdr3"],
                    })
                except ValueError as exc:
                    checks.append({"chain": chain, "error": str(exc)})
                    item["status"] = "fail"
            if not checks or not all(c.get("exact_sequence_match") and
                                     c.get("declared_tcr_in_pdb_header") for c in checks):
                item["status"] = "fail"
            item["chains"][kind] = checks
        audit.append(item)

    legacy = list(csv.DictReader(Path("data/negative_controls.csv").open()))
    obsolete = [r["control_id"] for r in legacy if "TBD" in " ".join(r.values())]
    result = {
        "schema_version": 1,
        "panel_path": str(PANEL),
        "panel_sha256": sha256(PANEL),
        "entries": audit,
        "summary": {
            "entry_count": len(audit),
            "pass_count": sum(x["status"] == "pass" for x in audit),
            "fail_count": sum(x["status"] == "fail" for x in audit),
            "legacy_TBD_controls_marked_obsolete": obsolete,
        },
        "scope_note": "Resolved-chain/CDR3 identity is verified from PDB ATOM records; gene calls are provenance assertions from stored TCR3d records, not independently re-inferred.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
    if result["summary"]["fail_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

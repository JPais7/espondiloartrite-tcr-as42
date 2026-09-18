#!/usr/bin/env python3
"""Select at most two RF3-screened candidates without manual substitution."""

from __future__ import annotations

import csv
import glob
import json
from pathlib import Path


def main():
    pref = {r["candidate"]: r for r in csv.DictReader(open("results/pilot/cloud/generation_prefilter.csv"))}
    cfg = json.load(open("config/pilot_acceptance_criteria.json"))["rf3_metrics"]["absolute_positive_thresholds"]
    eligible = []
    for path in glob.glob("results/pilot/cloud/rf3_screen/**/*_summary_confidences.json", recursive=True):
        # Ignore per-sample copies when an aggregate summary exists.
        if "/seed-" in path: continue
        d = json.load(open(path))
        stem = Path(path).name.removesuffix("_summary_confidences.json")
        candidates = [p for p in pref if Path(p).stem == stem]
        if len(candidates) != 1 or pref[candidates[0]]["pass"].lower() != "true": continue
        pair_pae = d["chain_pair_pae_min"]
        binder_target_pae = [pair_pae[0][1], pair_pae[0][2]]
        if any(x is None for x in binder_target_pae):
            continue
        best_pae = min(binder_target_pae)
        binder_ptm = d["chain_ptm"][0]
        if (d["iptm"] >= cfg["minimum_iptm"] and binder_ptm >= cfg["minimum_binder_chain_ptm"] and
                best_pae <= cfg["maximum_best_binder_target_chain_pair_PAE_min_A"] and
                bool(d["has_clash"]) == cfg["has_clash"]):
            q = float(d["iptm"]) - sum(map(float, binder_target_pae)) / 2.0 / 31.0
            eligible.append((q, candidates[0]))
    eligible.sort(reverse=True)
    selected = [p for _, p in eligible[:2]]
    out = Path("results/pilot/cloud/top2.txt")
    out.write_text("".join(p + "\n" for p in selected))
    print(json.dumps({"eligible":len(eligible),"selected":selected}, indent=2))


if __name__ == "__main__": main()

#!/usr/bin/env python3
"""Compare selected Phase 1.5 negative controls against AS4.2."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

from analyze_tcr_surface import AA3_TO_1, ca_map, kabsch, parse_pdb, residue_sasa, rmsd, sasa


TARGET_CORE = "VGLFSTDTQ"
REFERENCE = "7N2O"


def first_chain(chain_field: str) -> str:
    return chain_field.split(",")[0]


def observed_residues(atoms, chain):
    seen, residues = set(), []
    for atom in atoms:
        if atom["chain"] != chain:
            continue
        key = (atom["resseq"], atom["icode"])
        if key not in seen:
            seen.add(key)
            residues.append((key, AA3_TO_1.get(atom["resname"], "X")))
    return residues


def locate_sequence(atoms, chain, sequence):
    residues = observed_residues(atoms, chain)
    observed = "".join(aa for _, aa in residues)
    candidates = [sequence, sequence[1:], sequence[:-1], sequence[1:-1]]
    for candidate in candidates:
        if not candidate:
            continue
        start = observed.find(candidate)
        if start >= 0:
            return candidate, [residues[i][0] for i in range(start, start + len(candidate))]
    raise ValueError(f"Could not locate {sequence} in chain {chain}")


def beta_core(cdr3):
    core = re.sub(r"^CA?S+", "", cdr3)
    core = re.sub(r"[A-Z]?F$", "", core)
    return core


def best_window(core, n=len(TARGET_CORE)):
    if len(core) <= n:
        return core, 0
    best = None
    for i in range(0, len(core) - n + 1):
        window = core[i:i + n]
        identity = sum(a == b for a, b in zip(window, TARGET_CORE))
        aromatic98 = window[3] in {"F", "Y"} if len(window) > 3 else False
        score = (identity, aromatic98)
        if best is None or score > best[0]:
            best = (score, window, i)
    return best[1], best[2]


def sequence_metrics(core):
    window, offset = best_window(core)
    identity = sum(a == b for a, b in zip(window, TARGET_CORE)) / len(TARGET_CORE) if len(window) == len(TARGET_CORE) else None
    motif_tail = window.endswith("STDTQ") if len(window) == len(TARGET_CORE) else False
    aromatic_98_like = len(window) == len(TARGET_CORE) and window[3] in {"F", "Y"}
    return window, offset, identity, motif_tail, aromatic_98_like


def main():
    panel = list(csv.DictReader(Path("data/phase1_5_negative_controls.csv").open()))
    parsed = {row["pdbid"]: parse_pdb(Path("data/raw") / f"{row['pdbid']}.pdb") for row in panel}
    ref_atoms = parsed[REFERENCE]
    ref_beta_chain = "F"
    ref_beta_ca = ca_map(ref_atoms, ref_beta_chain)
    ref_core_seq, ref_core_keys = locate_sequence(ref_atoms, ref_beta_chain, "VGLFSTDTQ")
    ref_core_ca = np.array([ref_beta_ca[k] for k in ref_core_keys])

    rows = []
    details = {}
    for row in panel:
        pdbid = row["pdbid"]
        alpha_chain = first_chain(row["alpha_chain"])
        beta_chain = first_chain(row["beta_chain"])
        atoms = parsed[pdbid]
        beta_cdr3 = row["beta_cdr3"]
        located_cdr3, cdr3_keys = locate_sequence(atoms, beta_chain, beta_cdr3)
        core = beta_core(beta_cdr3)
        window, offset, identity, motif_tail, aromatic_98_like = sequence_metrics(core)

        beta_ca = ca_map(atoms, beta_chain)
        common = sorted(set(ref_beta_ca) & set(beta_ca))
        framework = [k for k in common if k[0] <= 110 and not 92 <= k[0] <= 105]
        framework_rmsd = None
        window_rmsd = None
        if len(framework) >= 40:
            mobile = np.array([beta_ca[k] for k in framework])
            fixed = np.array([ref_beta_ca[k] for k in framework])
            rot, trans = kabsch(mobile, fixed)
            framework_rmsd = rmsd(mobile @ rot + trans, fixed)
            if len(window) == len(TARGET_CORE):
                # Map the sequence window back onto located CDR3 residues by searching
                # within the located observed sequence.
                observed_cdr3_seq = located_cdr3
                start = observed_cdr3_seq.find(window)
                if start >= 0:
                    window_keys = cdr3_keys[start:start + len(window)]
                    if all(k in beta_ca for k in window_keys):
                        mobile_window = np.array([beta_ca[k] for k in window_keys]) @ rot + trans
                        window_rmsd = rmsd(mobile_window, ref_core_ca)

        tcr_atoms = [a for a in atoms if a["chain"] in {alpha_chain, beta_chain}]
        iso = residue_sasa(tcr_atoms, sasa(tcr_atoms, tcr_atoms))
        cdr3_sasa = sum(v for k, v in iso.items() if k[0] == beta_chain and (k[1], k[2]) in set(cdr3_keys))
        window_sasa = None
        start = located_cdr3.find(window)
        if start >= 0:
            window_keys = set(cdr3_keys[start:start + len(window)])
            window_sasa = sum(v for k, v in iso.items() if k[0] == beta_chain and (k[1], k[2]) in window_keys)

        out = {
            "pdbid": pdbid,
            "category": row["category"],
            "alpha_gene": row["alpha_gene"],
            "beta_gene": row["beta_gene"],
            "alpha_chain_used": alpha_chain,
            "beta_chain_used": beta_chain,
            "beta_cdr3": beta_cdr3,
            "derived_beta_core": core,
            "best_9mer_vs_AS4.2_core": window,
            "best_9mer_identity_to_AS4.2": None if identity is None else round(identity, 3),
            "has_STDTQ_tail_in_best_9mer": motif_tail,
            "has_F_or_Y_at_AS4.2_F98_equivalent": aromatic_98_like,
            "framework_CA_count": len(framework),
            "framework_CA_RMSD_vs_7N2O_A": None if framework_rmsd is None else round(framework_rmsd, 3),
            "best_9mer_CA_RMSD_vs_AS4.2_core_A": None if window_rmsd is None else round(window_rmsd, 3),
            "beta_CDR3_SASA_isolated_A2": round(cdr3_sasa, 2),
            "best_9mer_SASA_isolated_A2": None if window_sasa is None else round(window_sasa, 2),
            "rcsb_url": row["rcsb_url"],
        }
        rows.append(out)
        details[pdbid] = out

    outdir = Path("results/phase1_5")
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "negative_control_comparison.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (outdir / "negative_control_comparison.json").write_text(json.dumps(details, indent=2) + "\n")
    print(json.dumps(details, indent=2))


if __name__ == "__main__":
    main()


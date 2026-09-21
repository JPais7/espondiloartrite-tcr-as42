#!/usr/bin/env python3
"""Fail-fast static validation of the frozen AS4.2 cloud pilot package."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def load_json(relative: str):
    path = ROOT / relative
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        ERRORS.append(f"cannot read valid JSON {relative}: {exc}")
        return {}


def require(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def residue_names(path: Path, chain: str) -> dict[int, str]:
    residues: dict[int, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith(("ATOM  ", "HETATM")) and line[21].strip() == chain:
            try:
                residues.setdefault(int(line[22:26]), line[17:20].strip())
            except ValueError:
                pass
    return residues


def main() -> int:
    run = load_json("config/pilot_run.json")
    criteria = load_json("config/pilot_acceptance_criteria.json")
    target = load_json("config/pilot_target_spec.json")
    rfd3 = load_json("config/rfd3_pilot.json").get("as42_negative_design_pilot", {})
    counterfactual = load_json("data/counterfactuals/manifest.json")
    panel = load_json("results/pilot/panel_audit.json")
    models = load_json("cloud/model_manifest.json")
    environment = load_json("cloud/environment.json")

    generation = run.get("generation", {})
    sequence = run.get("sequence_design", {})
    validation = run.get("validation", {})
    require(generation.get("n_batches") == 1, "pilot must use one RFD3 batch")
    require(generation.get("diffusion_batch_size") == 4, "RFD3 batch size must be four")
    require(generation.get("maximum_backbones") == 4, "maximum_backbones must be four")
    require(sequence.get("sequences_per_backbone") == 3, "ProteinMPNN must make three sequences per backbone")
    require(sequence.get("maximum_total_candidates") == 12, "candidate cap must be 12")
    require(criteria.get("candidate_count_cap") == 12, "acceptance candidate cap must be 12")
    require(generation.get("maximum_backbones", 0) * sequence.get("sequences_per_backbone", 0) == 12,
            "backbone/sequence product must be 12")
    require(generation.get("seed") == 42017 and sequence.get("seed") == 42018,
            "generation seeds do not match frozen protocol")
    require(validation.get("replicate_seeds") == [42017, 42018, 42019],
            "RF3 replicate seeds do not match frozen protocol")

    positives = [x.get("pdbid") for x in target.get("positives", [])]
    negatives = [x.get("pdbid") for x in target.get("mandatory_negatives", [])]
    mutations = [x.get("mutation", "").split(":")[-1] for x in counterfactual.get("fixed_backbone_models", [])]
    require(positives == ["7N2O", "7N2N"], "mandatory positives must be 7N2O and 7N2N")
    require(negatives == ["7N2S", "8CX4", "9PBG", "9PBH"], "mandatory negative panel mismatch")
    require(validation.get("targets") == positives, "pilot_run positive panel mismatch")
    require(validation.get("mandatory_negatives") == negatives, "pilot_run negative panel mismatch")
    require(validation.get("counterfactuals") == ["F98Y", "F98A", "S99A", "T100A", "D101A"],
            "pilot_run perturbation panel mismatch")
    require(mutations == ["F98Y", "F98A", "S99A", "T100A", "D101A"],
            "counterfactual manifest perturbation panel mismatch")

    required = criteria.get("required", {})
    cdr = target.get("target_cdr3beta", {})
    require(cdr.get("core_residues") == list(range(95, 104)), "CDR3 beta core numbering mismatch")
    require(cdr.get("required_hotspot_residues") == [98, 99, 100, 101], "hotspot numbering mismatch")
    require(required.get("minimum_distinct_core_residues_contacted") == 4, "minimum core contacts changed")
    require(required.get("must_contact_residue_F98") is True, "F98 contact must be required")
    require(required.get("minimum_additional_hotspot_residues_contacted") == 2,
            "additional hotspot requirement changed")
    require(required.get("maximum_germline_contact_fraction") == 0.40,
            "germline-contact ceiling changed")
    require(target.get("germline_contact_penalty", {}).get("maximum_fraction_of_target_contacts") == 0.40,
            "target-spec germline-contact ceiling mismatch")

    rf3_metrics = criteria.get("rf3_metrics", {})
    require(rf3_metrics.get("selectivity_quality_Q") ==
            "iptm - mean(binder_to_alpha_chain_pair_PAE_min, binder_to_beta_chain_pair_PAE_min) / 31.0",
            "Q definition changed")
    absolute = rf3_metrics.get("absolute_positive_thresholds", {})
    require(absolute == {"minimum_iptm": 0.60, "minimum_binder_chain_ptm": 0.70,
                         "maximum_best_binder_target_chain_pair_PAE_min_A": 5.0, "has_clash": False},
            "absolute RF3 thresholds changed")
    require(criteria.get("uncertainty", {}).get("minimum_independent_score_replicates") == 3,
            "uncertainty calculation must require three replicates")

    require(rfd3.get("input") == "../data/pilot/7N2O_AS4_2_variable_domains.pdb", "RFD3 input mismatch")
    require(rfd3.get("contig") == "55-75,/0,D2-110,/0,F3-110", "RFD3 contig mismatch")
    require(set(rfd3.get("select_hotspots", {})) == {"F98", "F99", "F100", "F101"},
            "RFD3 hotspot selection mismatch")

    audit_entries = panel.get("entries", [])
    require(len(audit_entries) == 15, "panel audit must contain 15 entries")
    require(all(x.get("status") == "pass" for x in audit_entries), "not every panel audit entry passes")
    audited_ids = {x.get("pdbid") for x in audit_entries}
    for pdbid in positives + negatives:
        path = ROOT / "data" / "raw" / f"{pdbid}.pdb"
        require(path.is_file(), f"missing required structure: {path.relative_to(ROOT)}")
        require(pdbid in audited_ids, f"required structure absent from panel audit: {pdbid}")

    target_pdb = ROOT / "data/pilot/7N2O_AS4_2_variable_domains.pdb"
    require(target_pdb.is_file(), "missing prepared 7N2O target")
    if target_pdb.is_file():
        alpha = residue_names(target_pdb, "D")
        beta = residue_names(target_pdb, "F")
        require(min(alpha, default=0) == 2 and max(alpha, default=0) == 110, "target alpha chain D range must be 2-110")
        require(min(beta, default=0) == 3 and max(beta, default=0) == 110, "target beta chain F range must be 3-110")
        require({k: beta.get(k) for k in (98, 99, 100, 101)} ==
                {98: "PHE", 99: "SER", 100: "THR", 101: "ASP"},
                "target beta hotspot identities/numbering mismatch")

    for item in counterfactual.get("fixed_backbone_models", []):
        path = ROOT / item.get("path", "")
        require(path.is_file(), f"missing counterfactual: {item.get('path')}")
        if path.is_file():
            require(sha256(path) == item.get("sha256"), f"counterfactual hash mismatch: {item.get('path')}")

    checksum_lines = (ROOT / "cloud/checksums.sha256").read_text().splitlines()
    checksum_map = {line.split()[1]: line.split()[0] for line in checksum_lines if line.strip()}
    for model in models.get("models", []):
        require(checksum_map.get(model.get("filename")) == model.get("sha256"),
                f"checkpoint checksum mismatch in manifests: {model.get('filename')}")
    require(models.get("foundry_commit") == environment.get("packages", {}).get("foundry_git_commit"),
            "Foundry commit mismatch between manifests")

    dockerfile = (ROOT / "cloud/Dockerfile").read_text()
    require(environment.get("cloud_target", {}).get("cuda_base") in dockerfile, "Docker CUDA base mismatch")
    require(environment.get("packages", {}).get("foundry_git_commit") in dockerfile, "Docker Foundry commit mismatch")
    for script in ("cloud/run_stage0.sh", "cloud/run_generation.sh", "cloud/run_validation.sh"):
        text = (ROOT / script).read_text() if (ROOT / script).is_file() else ""
        require(text.startswith("#!/usr/bin/env bash\nset -euo pipefail"), f"{script} lacks strict shell mode")

    generation_script = (ROOT / "cloud/run_generation.sh").read_text()
    validation_script = (ROOT / "cloud/run_validation.sh").read_text()
    require(": \"${PILOT_RUN_ID:?" in generation_script, "generation must require PILOT_RUN_ID")
    require(": \"${PILOT_CONTAINER_DIGEST:?" in generation_script, "generation must require container digest")
    require('run_dir="results/pilot/cloud/$PILOT_RUN_ID"' in generation_script,
            "generation must use a per-run directory")
    require('out_dir="$run_dir/rfd3"' in generation_script and 'out_directory "$run_dir/mpnn"' in generation_script,
            "generation outputs must remain inside the per-run directory")
    require("${#backbones[@]} -eq 4" in generation_script and "${#candidates[@]} -eq 12" in generation_script,
            "generation count guards changed")
    require(": \"${PILOT_RUN_ID:?" in validation_script and ": \"${PILOT_CONTAINER_DIGEST:?" in validation_script,
            "validation must require run ID and container digest")
    require('run_dir="results/pilot/cloud/$PILOT_RUN_ID"' in validation_script,
            "validation must use the generation run directory")
    require("--glob \"$run_dir/mpnn/*.cif\"" in validation_script,
            "validation must use only the selected run's candidates")
    require("${#selected[@]} -le 2" in validation_script and "${#selected[@]} * 11" in validation_script,
            "validation focused caps changed")
    require("seed=42019" in validation_script and "for seed in 42017 42018 42019" in validation_script,
            "validation seeds changed")
    require("rf3 fold" not in generation_script, "generation must not launch RF3")
    require('current_git_status="$(git status --porcelain=v1 --untracked-files=no)"' in validation_script and
            'tracked checkout files must be clean before validation' in validation_script,
            "validation must check current git status")
    require("cloud/run_validation.sh" in generation_script and
            "cloud/run_validation.sh" in validation_script and
            "cloud/checksums.sha256" in generation_script and
            "cloud/model_manifest.json" in generation_script and
            "cloud/environment.json" in generation_script,
            "validation and provenance manifests must be included in execution hashes")

    stage0 = (ROOT / "cloud/run_stage0.sh").read_text() if (ROOT / "cloud/run_stage0.sh").is_file() else ""
    require("diffusion_batch_size=1" in stage0 and "n_batches=1" in stage0,
            "Stage 0 must request exactly one backbone")
    require(not re.search(r"\b(mpnn|rf3)\b|run_generation|run_validation", stage0),
            "Stage 0 must not invoke ProteinMPNN, RF3, or Stage 1 scripts")
    require("MemTotal" in stage0 and "60 * 1024 * 1024" in stage0,
            "Stage 0 must enforce the 60 GiB visible-RAM minimum")
    require("resource_class.txt" in stage0 and "host_memory_total_kib.txt" in stage0,
            "Stage 0 must record the RAM resource class and total")
    require("meminfo_before.txt" in stage0 and "meminfo_after.txt" in stage0,
            "Stage 0 must preserve before/after meminfo")
    require("resource_memory.log" in stage0 and "peak_host_memory_used_mib.txt" in stage0 and
            "min_host_memory_available_mib.txt" in stage0 and "peak_swap_used_mib.txt" in stage0,
            "Stage 0 must record host memory/swap telemetry")
    require("PIPESTATUS" in stage0 and "out of memory|CUDA" in stage0,
            "Stage 0 must preserve RFD3 exit status and detect OOM signatures")

    if ERRORS:
        print(json.dumps({"status": "FAIL", "errors": ERRORS}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "checks": "frozen protocol, manifests, inputs, numbering and isolation"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

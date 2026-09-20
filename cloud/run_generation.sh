#!/usr/bin/env bash
set -euo pipefail

: "${PILOT_RUN_ID:?Set PILOT_RUN_ID, e.g. pilot-20260920T120000Z}"
: "${PILOT_CONTAINER_DIGEST:?Set PILOT_CONTAINER_DIGEST to the immutable container ID/digest}"
[[ "$PILOT_RUN_ID" =~ ^pilot-[A-Za-z0-9._-]+$ ]] || { echo "ERROR: invalid PILOT_RUN_ID" >&2; exit 2; }

bash cloud/verify_runtime.sh
git_status="$(git status --porcelain=v1)"
[[ -z "$git_status" ]] || { echo "ERROR: checkout must be clean before generation" >&2; exit 3; }

run_dir="results/pilot/cloud/$PILOT_RUN_ID"
[[ ! -e "$run_dir" ]] || { echo "ERROR: refusing existing run directory: $run_dir" >&2; exit 4; }
mkdir -p "$run_dir"/{rfd3,mpnn,logs,provenance}

git rev-parse HEAD > "$run_dir/provenance/git_commit.txt"
printf '%s' "$git_status" > "$run_dir/provenance/git_status.txt"
printf '%s\n' "$PILOT_CONTAINER_DIGEST" > "$run_dir/provenance/container_digest.txt"
python --version > "$run_dir/provenance/python_version.txt" 2>&1
pip freeze --all > "$run_dir/provenance/pip_freeze.txt"
foundry list-installed > "$run_dir/provenance/foundry_installed.txt" 2>&1
nvidia-smi -q > "$run_dir/provenance/nvidia-smi-q.txt"
(cd "$FOUNDRY_CHECKPOINT_DIRS" && sha256sum -c /workspace/cloud/checksums.sha256) > "$run_dir/provenance/checkpoint_hashes.txt"
sha256sum config/*.json > "$run_dir/provenance/config_hashes.txt"
sha256sum cloud/run_generation.sh cloud/verify_runtime.sh scripts/filter_cloud_candidates.py scripts/select_cloud_top2.py scripts/prepare_cloud_validation_complexes.py > "$run_dir/provenance/execution_script_hashes.txt"

python scripts/audit_phase1_5_panel.py > "$run_dir/logs/panel_audit.log"
python scripts/build_counterfactuals.py > "$run_dir/logs/counterfactuals.log"
python scripts/prepare_pilot_target.py > "$run_dir/logs/target_preparation.log"

rfd3 design out_dir="$run_dir/rfd3" inputs=config/rfd3_pilot.json n_batches=1 diffusion_batch_size=4 seed=42017 inference_sampler.step_scale=3 inference_sampler.gamma_0=0.2 dump_trajectories=false 2>&1 | tee "$run_dir/logs/rfd3.log"

mapfile -t backbones < <(find "$run_dir/rfd3" -maxdepth 1 -type f -name '*.cif.gz' | sort)
[[ ${#backbones[@]} -eq 4 ]] || { echo "ERROR: expected exactly 4 RFD3 backbones" >&2; exit 5; }

for structure in "${backbones[@]}"; do
  mpnn --model_type protein_mpnn --checkpoint_path "$FOUNDRY_CHECKPOINT_DIRS/proteinmpnn_v_48_020.pt" --is_legacy_weights True --structure_path "$structure" --out_directory "$run_dir/mpnn" --fixed_chains B,C --batch_size 3 --number_of_batches 1 --temperature 0.1 --seed 42018 --write_fasta True --write_structures True 2>&1 | tee -a "$run_dir/logs/mpnn.log"
done

mapfile -t candidates < <(find "$run_dir/mpnn" -maxdepth 1 -type f -name '*.cif' | sort)
[[ ${#candidates[@]} -eq 12 ]] || { echo "ERROR: expected exactly 12 MPNN candidates" >&2; exit 6; }

python - "$run_dir" <<'PY'
import hashlib, json, sys
from pathlib import Path
run = Path(sys.argv[1])
files = sorted(run.joinpath("mpnn").glob("*.cif"))
manifest = {"run_id": run.name, "candidate_count": len(files), "candidates": [{"path": str(p.relative_to(run)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(run / "provenance/candidate_inventory.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY

sha256sum config/*.json cloud/run_generation.sh cloud/verify_runtime.sh scripts/filter_cloud_candidates.py scripts/select_cloud_top2.py scripts/prepare_cloud_validation_complexes.py > "$run_dir/provenance/config_and_script_hashes_for_validation.txt"
printf '%s\n' "PASS: generation complete; exactly 4 backbones and 12 candidates. Stage 2 validation requires a separate invocation." | tee "$run_dir/GENERATION_COMPLETE.txt"

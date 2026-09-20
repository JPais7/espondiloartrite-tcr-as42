#!/usr/bin/env bash
set -euo pipefail

: "${PILOT_RUN_ID:?Set the same PILOT_RUN_ID used by generation}"
: "${PILOT_CONTAINER_DIGEST:?Set PILOT_CONTAINER_DIGEST to the immutable container ID/digest}"
[[ "$PILOT_RUN_ID" =~ ^pilot-[A-Za-z0-9._-]+$ ]] || { echo "ERROR: invalid PILOT_RUN_ID" >&2; exit 2; }
bash cloud/verify_runtime.sh

run_dir="results/pilot/cloud/$PILOT_RUN_ID"
[[ -f "$run_dir/GENERATION_COMPLETE.txt" ]] || { echo "ERROR: generation completion marker missing" >&2; exit 3; }
[[ -f "$run_dir/provenance/git_commit.txt" && -f "$run_dir/provenance/git_status.txt" ]] || { echo "ERROR: generation provenance missing" >&2; exit 4; }
[[ -z "$(cat "$run_dir/provenance/git_status.txt")" ]] || { echo "ERROR: generation checkout was not clean" >&2; exit 5; }
[[ "$(git rev-parse HEAD)" == "$(cat "$run_dir/provenance/git_commit.txt")" ]] || { echo "ERROR: generation commit differs from current checkout" >&2; exit 6; }
[[ "$(cat "$run_dir/provenance/container_digest.txt")" == "$PILOT_CONTAINER_DIGEST" ]] || { echo "ERROR: container digest differs from generation" >&2; exit 7; }
for required in provenance/checkpoint_hashes.txt provenance/config_and_script_hashes_for_validation.txt provenance/candidate_inventory.json mpnn; do
  [[ -e "$run_dir/$required" ]] || { echo "ERROR: missing generation provenance: $required" >&2; exit 8; }
done
(cd "$FOUNDRY_CHECKPOINT_DIRS" && sha256sum -c /workspace/cloud/checksums.sha256) > "$run_dir/logs/checkpoint_hashes_validation.txt"
sha256sum config/*.json cloud/run_generation.sh cloud/verify_runtime.sh scripts/filter_cloud_candidates.py scripts/select_cloud_top2.py scripts/prepare_cloud_validation_complexes.py > "$run_dir/logs/config_and_script_hashes_validation.txt"
sha256sum config/*.json > "$run_dir/logs/config_hashes_validation.txt"
cmp "$run_dir/logs/config_hashes_validation.txt" "$run_dir/provenance/config_hashes.txt" || { echo "ERROR: config hashes differ from generation" >&2; exit 9; }
cmp "$run_dir/logs/checkpoint_hashes_validation.txt" "$run_dir/provenance/checkpoint_hashes.txt" || { echo "ERROR: checkpoint hashes differ from generation" >&2; exit 9; }
cmp "$run_dir/logs/config_and_script_hashes_validation.txt" "$run_dir/provenance/config_and_script_hashes_for_validation.txt" || { echo "ERROR: config/script hashes differ from generation" >&2; exit 9; }

python - "$run_dir" <<'PY'
import hashlib, json, sys
from pathlib import Path
run = Path(sys.argv[1])
manifest = json.loads((run / "provenance/candidate_inventory.json").read_text())
files = sorted((run / "mpnn").glob("*.cif"))
if len(files) != 12 or manifest.get("candidate_count") != 12:
    raise SystemExit("candidate inventory must contain exactly 12 files")
expected = {x["path"]: x["sha256"] for x in manifest["candidates"]}
actual = {str(p.relative_to(run)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
if actual != expected:
    raise SystemExit("candidate inventory/hash mismatch; manual additions or modifications are forbidden")
PY

for path in "$run_dir/generation_prefilter.csv" "$run_dir/prefilter_passed.txt" "$run_dir/rf3_screen" "$run_dir/top2.txt" "$run_dir/validation_inputs" "$run_dir/rf3_panel"; do
  [[ ! -e "$path" ]] || { echo "ERROR: validation output already exists: $path" >&2; exit 9; }
done
mkdir -p "$run_dir/logs" "$run_dir/provenance"
python scripts/filter_cloud_candidates.py --glob "$run_dir/mpnn/*.cif" --out "$run_dir/generation_prefilter.csv" --passed-out "$run_dir/prefilter_passed.txt" > "$run_dir/logs/prefilter.log"
mapfile -t candidates < "$run_dir/prefilter_passed.txt"
if [[ ${#candidates[@]} -eq 0 ]]; then
  printf '%s\n' "No candidates passed the frozen prefilter; no RF3 work was started." > "$run_dir/NO_CANDIDATES_AFTER_PREFILTER.txt"
  printf '%s\n' "PASS: validation stopped after empty prefilter." > "$run_dir/VALIDATION_COMPLETE.txt"
  exit 0
fi
[[ ${#candidates[@]} -le 12 ]] || { echo "ERROR: prefilter survivors exceed 12" >&2; exit 10; }

mkdir -p "$run_dir/rf3_screen"
for candidate in "${candidates[@]}"; do
  rf3 fold inputs="$candidate" out_dir="$run_dir/rf3_screen" diffusion_batch_size=1 seed=42019 dump_trajectories=false 2>&1 | tee -a "$run_dir/logs/rf3_screen.log"
done
python scripts/select_cloud_top2.py --prefilter "$run_dir/generation_prefilter.csv" --rf3-screen-dir "$run_dir/rf3_screen" --out "$run_dir/top2.txt" > "$run_dir/logs/top2_selection.json"
mapfile -t selected < "$run_dir/top2.txt"
[[ ${#selected[@]} -le 2 ]] || { echo "ERROR: more than two candidates selected" >&2; exit 11; }
if [[ ${#selected[@]} -eq 0 ]]; then
  printf '%s\n' "No candidates passed the frozen target-only screen; focused validation was not started." > "$run_dir/NO_CANDIDATES_AFTER_RF3_SCREEN.txt"
  printf '%s\n' "PASS: validation stopped after empty target-only screen." > "$run_dir/VALIDATION_COMPLETE.txt"
  exit 0
fi

mkdir -p "$run_dir/validation_inputs" "$run_dir/rf3_panel"
for candidate in "${selected[@]}"; do
  python scripts/prepare_cloud_validation_complexes.py --candidate "$candidate" --outdir "$run_dir/validation_inputs"
done
state_count=$(find "$run_dir/validation_inputs" -maxdepth 1 -type f -name '*.cif' | wc -l | tr -d ' ')
expected_states=$((${#selected[@]} * 11))
[[ "$state_count" -eq "$expected_states" && "$state_count" -le 22 ]] || { echo "ERROR: invalid focused state count" >&2; exit 12; }
expected_predictions=$((state_count * 3))
[[ "$expected_predictions" -le 66 ]] || { echo "ERROR: focused RF3 prediction cap exceeded" >&2; exit 13; }

for state in "$run_dir"/validation_inputs/*.cif; do
  for seed in 42017 42018 42019; do
    name="$(basename "$state" .cif)__seed_${seed}"
    rf3 fold inputs="$state" out_dir="$run_dir/rf3_panel/$name" diffusion_batch_size=1 seed="$seed" dump_trajectories=false 2>&1 | tee -a "$run_dir/logs/rf3_panel.log"
  done
done
printf '%s\n' "PASS: validation complete for ${#selected[@]} candidates; focused predictions: $expected_predictions." | tee "$run_dir/VALIDATION_COMPLETE.txt"

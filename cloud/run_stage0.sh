#!/usr/bin/env bash
set -euo pipefail

: "${STAGE0_RUN_ID:?Set STAGE0_RUN_ID to a unique identifier, for example stage0-20260918T120000Z}"
: "${PILOT_CONTAINER_DIGEST:?Set PILOT_CONTAINER_DIGEST to the immutable container image ID/digest}"

[[ "$STAGE0_RUN_ID" =~ ^stage0-[A-Za-z0-9._-]+$ ]] || {
  echo "ERROR: invalid STAGE0_RUN_ID" >&2
  exit 2
}

bash cloud/verify_runtime.sh

git_status="$(git status --porcelain=v1)"
if [[ -n "$git_status" ]]; then
  echo "ERROR: repository must be clean before Stage 0 so the recorded commit fully defines the run" >&2
  exit 4
fi

run_dir="results/pilot/stage0/$STAGE0_RUN_ID"
if [[ -e "$run_dir" ]]; then
  echo "ERROR: Stage 0 run directory already exists: $run_dir" >&2
  exit 5
fi
mkdir -p "$run_dir"/{output,logs,provenance}

git rev-parse HEAD > "$run_dir/provenance/git_commit.txt"
printf '%s' "$git_status" > "$run_dir/provenance/git_status.txt"
printf '%s\n' "$PILOT_CONTAINER_DIGEST" > "$run_dir/provenance/container_digest.txt"
python --version > "$run_dir/provenance/python_version.txt" 2>&1
pip freeze --all > "$run_dir/provenance/pip_freeze.txt"
foundry list-installed > "$run_dir/provenance/foundry_installed.txt" 2>&1
nvidia-smi -q > "$run_dir/provenance/nvidia-smi-q.txt"
(cd "$FOUNDRY_CHECKPOINT_DIRS" && sha256sum -c /workspace/cloud/checksums.sha256) \
  > "$run_dir/provenance/checkpoint_hashes.txt"
sha256sum config/*.json cloud/model_manifest.json cloud/environment.json \
  > "$run_dir/provenance/config_hashes.txt"

vram_log="$run_dir/logs/gpu_memory_mib.log"
monitor_vram() {
  while true; do
    printf '%s ' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$vram_log"
    nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits >> "$vram_log"
    sleep 1
  done
}
monitor_vram &
monitor_pid=$!
cleanup() {
  kill "$monitor_pid" 2>/dev/null || true
  wait "$monitor_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

start_epoch=$(date +%s)
rfd3 design \
  out_dir="$run_dir/output" \
  inputs=config/rfd3_pilot.json \
  n_batches=1 \
  diffusion_batch_size=1 \
  seed=42017 \
  inference_sampler.step_scale=3 \
  inference_sampler.gamma_0=0.2 \
  dump_trajectories=false \
  2>&1 | tee "$run_dir/logs/rfd3.log"
end_epoch=$(date +%s)

cleanup
trap - EXIT INT TERM
python scripts/validate_stage0_output.py "$run_dir/output" | tee "$run_dir/logs/output_validation.json"
printf '%s\n' "$((end_epoch - start_epoch))" > "$run_dir/provenance/elapsed_seconds.txt"
awk '{for(i=2;i<=NF;i++) if (($i+0)>max) max=$i+0} END {print max+0}' "$vram_log" \
  > "$run_dir/provenance/peak_gpu_memory_mib.txt"
printf '%s\n' "PASS: Stage 0 completed. STOP. Human inspection and separate authorization are required before Stage 1." \
  | tee "$run_dir/STAGE0_COMPLETE.txt"

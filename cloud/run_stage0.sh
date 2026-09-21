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

memtotal_kib=$(awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo)
[[ "$memtotal_kib" =~ ^[0-9]+$ ]] || { echo "ERROR: could not read MemTotal" >&2; exit 6; }
printf '%s\n' "$memtotal_kib" > "$run_dir/provenance/host_memory_total_kib.txt"
cp /proc/meminfo "$run_dir/provenance/meminfo_before.txt"
if (( memtotal_kib < 60 * 1024 * 1024 )); then
  echo "ERROR: Stage 0 requires at least 60 GiB visible RAM" >&2
  exit 6
elif (( memtotal_kib < 96 * 1024 * 1024 )); then
  printf '%s\n' "CALIBRATION_ONLY: host RAM is below the >=96 GiB requirement retained for Stage 1-3." \
    > "$run_dir/provenance/resource_class.txt"
else
  printf '%s\n' "FULL_PILOT_RAM_CLASS: host RAM satisfies the >=96 GiB requirement retained for Stage 1-3." \
    > "$run_dir/provenance/resource_class.txt"
fi

vram_log="$run_dir/logs/gpu_memory_mib.log"
resource_log="$run_dir/logs/resource_memory.log"
monitor_vram() {
  while true; do
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    gpu_used_mib="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -n 1 | tr -d ' ')"
    mem_values="$(awk '/^MemTotal:/ {mt=$2} /^MemAvailable:/ {ma=$2} /^SwapTotal:/ {st=$2} /^SwapFree:/ {sf=$2} END {print mt, ma, st, sf}' /proc/meminfo)"
    printf '%s %s\n' "$timestamp" "$gpu_used_mib" >> "$vram_log"
    printf '%s %s %s %s %s %s\n' "$timestamp" $mem_values "$gpu_used_mib" >> "$resource_log"
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
set +e
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
rfd3_pipeline_status=( "${PIPESTATUS[@]}" )
set -e
rfd3_status="${rfd3_pipeline_status[0]}"
tee_status="${rfd3_pipeline_status[1]}"
end_epoch=$(date +%s)

cleanup
trap - EXIT INT TERM
cp /proc/meminfo "$run_dir/provenance/meminfo_after.txt"
printf '%s\n' "$((end_epoch - start_epoch))" > "$run_dir/provenance/elapsed_seconds.txt"
awk 'BEGIN {max=0} {if (($2+0)>max) max=$2+0} END {print max+0}' "$vram_log" \
  > "$run_dir/provenance/peak_gpu_memory_mib.txt"
awk 'BEGIN {peak=0; min=-1; swap=0} {used=$2-$3; if (used>peak) peak=used; if (min<0 || $3<min) min=$3; swap_used=$4-$5; if (swap_used>swap) swap=swap_used} END {print peak+0}' "$resource_log" \
  > "$run_dir/provenance/peak_host_memory_used_mib.txt"
awk 'BEGIN {min=-1} {if (min<0 || $3<min) min=$3} END {print min+0}' "$resource_log" \
  > "$run_dir/provenance/min_host_memory_available_mib.txt"
awk 'BEGIN {swap=0} {swap_used=$4-$5; if (swap_used>swap) swap=swap_used} END {print swap+0}' "$resource_log" \
  > "$run_dir/provenance/peak_swap_used_mib.txt"

if grep -Eiq 'out of memory|CUDA[^\n]*out of memory|oom-kill|Killed process' "$run_dir/logs/rfd3.log"; then
  echo "ERROR: RFD3 log contains an out-of-memory signature" >&2
  exit 14
fi
if (( rfd3_status != 0 )); then
  echo "ERROR: rfd3 design failed with exit code $rfd3_status" >&2
  exit "$rfd3_status"
fi
if (( tee_status != 0 )); then
  echo "ERROR: tee failed while recording the RFD3 log" >&2
  exit "$tee_status"
fi
python scripts/validate_stage0_output.py "$run_dir/output" | tee "$run_dir/logs/output_validation.json"
printf '%s\n' "PASS: Stage 0 completed. STOP. Human inspection and separate authorization are required before Stage 1." \
  | tee "$run_dir/STAGE0_COMPLETE.txt"

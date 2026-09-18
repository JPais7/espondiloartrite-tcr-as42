#!/usr/bin/env bash
set -euo pipefail

bash cloud/verify_runtime.sh

for path in results/pilot/cloud/rf3_screen results/pilot/cloud/validation_inputs results/pilot/cloud/rf3_panel; do
  if [[ -e "$path" ]]; then
    echo "ERROR: output path already exists; refusing to mix or overwrite results: $path" >&2
    exit 5
  fi
done

# Apply the frozen pose/sequence filter before any RF3 screen.
python scripts/filter_cloud_candidates.py

mapfile -t candidates < results/pilot/cloud/prefilter_passed.txt
if [[ ${#candidates[@]} -eq 0 ]]; then
  printf '%s\n' "No candidates passed the frozen prefilter; no RF3 work was started." \
    > results/pilot/cloud/NO_CANDIDATES_AFTER_PREFILTER.txt
  exit 0
fi
if [[ ${#candidates[@]} -gt 12 ]]; then
  echo "ERROR: candidate cap exceeded after prefilter" >&2
  exit 6
fi

# Stage 1 is intentionally target-only and one seed. Only its two best
# candidates proceed. Selection must use the frozen criteria, not inspection.
mkdir -p results/pilot/cloud/rf3_screen
for candidate in "${candidates[@]}"; do
  rf3 fold \
    inputs="$candidate" \
    out_dir=results/pilot/cloud/rf3_screen \
    diffusion_batch_size=1 \
    seed=42019 \
    dump_trajectories=false
done

python scripts/select_cloud_top2.py

mapfile -t selected < results/pilot/cloud/top2.txt
if [[ ${#selected[@]} -eq 0 ]]; then
  printf '%s\n' "No candidates passed the frozen target-only screen; multistate validation was not started." \
    > results/pilot/cloud/NO_CANDIDATES_AFTER_RF3_SCREEN.txt
  exit 0
fi
if [[ ${#selected[@]} -gt 2 ]]; then
  echo "ERROR: more than two candidates selected for focused validation" >&2
  exit 7
fi

# After the deterministic screen has written results/pilot/cloud/top2.txt,
# build 11 structural states and run three independent seeds per state.
mkdir -p results/pilot/cloud/validation_inputs results/pilot/cloud/rf3_panel
for candidate in "${selected[@]}"; do
  python scripts/prepare_cloud_validation_complexes.py \
    --candidate "$candidate" \
    --outdir results/pilot/cloud/validation_inputs
done

state_count=$(find results/pilot/cloud/validation_inputs -maxdepth 1 -type f -name '*.cif' | wc -l | tr -d ' ')
expected_states=$((${#selected[@]} * 11))
if [[ "$state_count" -ne "$expected_states" ]]; then
  echo "ERROR: expected $expected_states multistate inputs, found $state_count" >&2
  exit 8
fi

for state in results/pilot/cloud/validation_inputs/*.cif; do
  for seed in 42017 42018 42019; do
    name="$(basename "$state" .cif)__seed_${seed}"
    rf3 fold \
      inputs="$state" \
      out_dir="results/pilot/cloud/rf3_panel/$name" \
      diffusion_batch_size=1 \
      seed="$seed" \
      dump_trajectories=false
  done
done

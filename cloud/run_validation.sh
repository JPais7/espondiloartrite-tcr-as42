#!/usr/bin/env bash
set -euo pipefail

: "${FOUNDRY_CHECKPOINT_DIRS:=/checkpoints}"
export FOUNDRY_CHECKPOINT_DIRS

# Apply the frozen pose/sequence filter before any RF3 screen.
python scripts/filter_cloud_candidates.py

# Stage 1 is intentionally target-only and one seed. Only its two best
# candidates proceed. Selection must use the frozen criteria, not inspection.
mkdir -p results/pilot/cloud/rf3_screen
for candidate in results/pilot/cloud/mpnn/*.cif; do
  rf3 fold \
    inputs="$candidate" \
    out_dir=results/pilot/cloud/rf3_screen \
    diffusion_batch_size=1 \
    seed=42019 \
    dump_trajectories=false
done

python scripts/select_cloud_top2.py

# After the deterministic screen has written results/pilot/cloud/top2.txt,
# build 11 structural states and run three independent seeds per state.
mkdir -p results/pilot/cloud/validation_inputs results/pilot/cloud/rf3_panel
while IFS= read -r candidate; do
  python scripts/prepare_cloud_validation_complexes.py \
    --candidate "$candidate" \
    --outdir results/pilot/cloud/validation_inputs
done < results/pilot/cloud/top2.txt

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

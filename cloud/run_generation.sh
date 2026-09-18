#!/usr/bin/env bash
set -euo pipefail

: "${FOUNDRY_CHECKPOINT_DIRS:=/checkpoints}"
export FOUNDRY_CHECKPOINT_DIRS

python scripts/audit_phase1_5_panel.py
python scripts/build_counterfactuals.py
python scripts/prepare_pilot_target.py

# Exactly four backbones in one batch; do not increase without a new protocol.
rfd3 design \
  out_dir=results/pilot/cloud/rfd3 \
  inputs=config/rfd3_pilot.json \
  n_batches=1 \
  diffusion_batch_size=4 \
  seed=42017 \
  inference_sampler.step_scale=3 \
  inference_sampler.gamma_0=0.2 \
  dump_trajectories=false

mkdir -p results/pilot/cloud/mpnn
for structure in results/pilot/cloud/rfd3/*.cif.gz; do
  mpnn \
    --model_type protein_mpnn \
    --checkpoint_path "$FOUNDRY_CHECKPOINT_DIRS/proteinmpnn_v_48_020.pt" \
    --is_legacy_weights True \
    --structure_path "$structure" \
    --out_directory results/pilot/cloud/mpnn \
    --fixed_chains B,C \
    --batch_size 3 \
    --number_of_batches 1 \
    --temperature 0.1 \
    --seed 42018 \
    --write_fasta True \
    --write_structures True
done

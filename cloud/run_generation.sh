#!/usr/bin/env bash
set -euo pipefail

bash cloud/verify_runtime.sh

output_root="results/pilot/cloud"
for path in "$output_root/rfd3" "$output_root/mpnn"; do
  if [[ -e "$path" ]]; then
    echo "ERROR: output path already exists; refusing to mix or overwrite results: $path" >&2
    exit 5
  fi
done

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
mapfile -t backbones < <(find results/pilot/cloud/rfd3 -maxdepth 1 -type f -name '*.cif.gz' | sort)
if [[ ${#backbones[@]} -ne 4 ]]; then
  echo "ERROR: expected exactly four RFD3 backbones, found ${#backbones[@]}" >&2
  exit 6
fi
for structure in "${backbones[@]}"; do
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

candidate_count=$(find results/pilot/cloud/mpnn -maxdepth 1 -type f -name '*.cif' | wc -l | tr -d ' ')
if [[ "$candidate_count" -ne 12 ]]; then
  echo "ERROR: expected exactly 12 ProteinMPNN candidates, found $candidate_count" >&2
  exit 7
fi

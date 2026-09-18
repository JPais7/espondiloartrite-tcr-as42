#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f CLOUD_RUN_PLAN.md || ! -d .git ]]; then
  echo "ERROR: run from the repository root mounted at /workspace" >&2
  exit 2
fi

: "${FOUNDRY_CHECKPOINT_DIRS:=/checkpoints}"
export FOUNDRY_CHECKPOINT_DIRS

python scripts/precloud_validate.py

for checkpoint in rfd3_latest.ckpt proteinmpnn_v_48_020.pt rf3_foundry_01_24_latest_remapped.ckpt; do
  [[ -f "$FOUNDRY_CHECKPOINT_DIRS/$checkpoint" ]] || {
    echo "ERROR: missing checkpoint $FOUNDRY_CHECKPOINT_DIRS/$checkpoint" >&2
    exit 3
  }
done

(cd "$FOUNDRY_CHECKPOINT_DIRS" && sha256sum -c /workspace/cloud/checksums.sha256)

command -v nvidia-smi >/dev/null || {
  echo "ERROR: nvidia-smi is unavailable" >&2
  exit 4
}
nvidia-smi >/dev/null

python - <<'PY'
import sys
import torch

if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
    raise SystemExit("ERROR: CUDA GPU unavailable; CPU/MPS fallback is forbidden")
if not str(torch.version.cuda):
    raise SystemExit("ERROR: installed PyTorch has no CUDA runtime")
print({"cuda": torch.version.cuda, "devices": torch.cuda.device_count(),
       "device_0": torch.cuda.get_device_name(0)})
PY


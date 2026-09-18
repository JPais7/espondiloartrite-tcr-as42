# Pre-cloud execution audit

Date: 18 September 2026  
Scope: repository readiness for a human-authorized **Stage 0 only**  
Result: **PASS — ready to launch Stage 0 after the manual checks below**

This PASS does not authorize cloud spending or Stage 1. No paid cloud resource, credential or production-scale local inference was used during this audit.

## Frozen scientific definition verified

The human-readable plan and machine-readable files now agree on:

- one RFD3 batch containing exactly 4 scientific backbones;
- 3 ProteinMPNN sequences per backbone and a hard maximum of 12 scientific candidates;
- required positives 7N2O and 7N2N;
- required negatives 7N2S, 8CX4, 9PBG and 9PBH;
- perturbations F98Y, F98A, S99A, T100A and D101A;
- at least 4 contacted core residues, including F98 and at least 2 of S99/T100/D101;
- no more than 40% germline/framework target contacts;
- the frozen RF3 absolute thresholds, raw effect floors and three seeds 42017/42018/42019;
- `Q = ipTM - mean(binder–alpha PAE min, binder–beta PAE min) / 31`;
- effective uncertainty equal to the maximum of propagated replicate standard error, half the 7N2O/7N2N difference and 0.02;
- every required effect larger than its raw floor and `2 × sigma_eff`;
- no more than 2 candidates entering focused multistate validation.

No scientific threshold, candidate cap or decision rule was changed.

## Issues found and corrections made

1. `config/pilot_run.json` still declared 2 RFD3 batches and 8 maximum backbones, contradicting the frozen 4 × 3 = 12 design. It now declares 1 batch, 4 backbones and 3 sequences per backbone.
2. `README.md` described the project as still being before protein generation and treated cloud use as an unspecified future option. It now records completion of Phase 1/1.5, exclusion of local smoke outputs, the frozen pilot and Stage 0 as the only next execution step.
3. There was no isolated Stage 0 entry point. `cloud/run_stage0.sh` now runs exactly one disposable RFD3 backbone and stops. It contains no sequence-design, RF3, Stage 1 generation or Stage 1 validation invocation.
4. The package did not fail early on missing/altered checkpoints or absent CUDA. `cloud/verify_runtime.sh` now validates the static package, all three checkpoint hashes, `nvidia-smi` and PyTorch CUDA availability; CPU/MPS fallback is forbidden.
5. Stage 0 did not capture sufficient provenance. It now records Git commit and clean status, immutable container ID/digest, complete installed package list, Foundry component list, `nvidia-smi -q`, config hashes, checkpoint hashes, elapsed seconds, sampled GPU memory and the full RFD3 log.
6. Generation could mix with stale outputs or silently return the wrong count. It now refuses existing RFD3/MPNN output directories and fails unless exactly 4 backbones and exactly 12 sequence-designed CIFs are produced. It never retries or replaces failures.
7. Validation previously sent every generated sequence to RF3 even when it failed the frozen prefilter. It now sends only listed prefilter survivors and stops without RF3 if none survive.
8. Focused validation lacked hard output-count enforcement. It now stops if more than 2 candidates are selected and requires exactly 11 states per selected candidate before RF3.
9. Target-only selection calculated its PAE cutoff over the complete chain-pair matrix, which could select an alpha–beta target pair instead of binder–target. It now uses only binder–alpha and binder–beta entries and ranks eligible candidates using the preregistered `Q` definition.
10. Core package versions were documented but not explicitly reapplied after Foundry installation. `cloud/requirements-core.txt` and `pip check` now enforce the recorded core versions during image construction.

## Stage 0 isolation and safeguards

`cloud/run_stage0.sh`:

- uses `set -euo pipefail`;
- requires a unique `STAGE0_RUN_ID` and recorded immutable container ID/digest;
- requires a clean Git checkout and refuses an existing run directory;
- performs all checks before inference;
- requests `n_batches=1` and `diffusion_batch_size=1` with frozen seed `42017`;
- does not retry and cannot increase candidate count;
- validates exactly one output CIF/JSON, chains A/B/C, binder length 55–75 and expected target-chain lengths;
- writes a clear completion marker requiring human inspection;
- has no automatic transition to Stage 1.

The Stage 0 output lives under `results/pilot/stage0/<run-id>/`, is disposable and is excluded from scientific ranking.

## Files changed or added

- `README.md`
- `CLOUD_RUN_PLAN.md`
- `PRE_CLOUD_AUDIT.md`
- `config/pilot_run.json`
- `cloud/Dockerfile`
- `cloud/requirements-core.txt`
- `cloud/verify_runtime.sh`
- `cloud/run_stage0.sh`
- `cloud/run_generation.sh`
- `cloud/run_validation.sh`
- `scripts/precloud_validate.py`
- `scripts/validate_stage0_output.py`
- `scripts/filter_cloud_candidates.py`
- `scripts/select_cloud_top2.py`

## Lightweight checks performed

- static package validator: PASS;
- all relevant JSON parsed: PASS;
- panel audit state: 15/15 PASS;
- required PDB presence, chains, CDR3 numbering and F98/S99/T100/D101 identities: PASS;
- all five counterfactual SHA-256 values: PASS;
- checkpoint manifest/checksum cross-consistency: PASS;
- shell syntax for every cloud shell script: PASS;
- Python byte-code compilation for all scripts: PASS;
- whitespace/error check on the Git diff: PASS.

The Docker image was not built and the CUDA path was not executed on this Mac. Those operations belong on the authorized NVIDIA host and are enforced by the runtime preflight. No RFD3, ProteinMPNN or RF3 inference was run during this audit.

## Exact Stage 0 launch command

Run the following only on an explicitly authorized GPU host, from a clean repository checkout at this audit commit. The checkpoint directory must contain the three correctly named files listed in `cloud/checksums.sha256`.

```bash
export PILOT_CHECKPOINT_DIR=/absolute/path/to/checkpoints
export STAGE0_RUN_ID="stage0-$(date -u +%Y%m%dT%H%M%SZ)"
docker build --build-arg PILOT_GIT_COMMIT="$(git rev-parse HEAD)" -f cloud/Dockerfile -t as42-pilot:stage0 .
export PILOT_CONTAINER_DIGEST="$(docker image inspect as42-pilot:stage0 --format '{{.Id}}')"
docker run --rm --gpus all --ipc=host \
  -e STAGE0_RUN_ID -e PILOT_CONTAINER_DIGEST \
  -v "$PWD:/workspace" \
  -v "$PILOT_CHECKPOINT_DIR:/checkpoints:ro" \
  as42-pilot:stage0 bash cloud/run_stage0.sh
```

This command uses an already provisioned host; it does not itself create a RunPod/AWS/GCP/Lambda/Vast resource.

## Expected resources, runtime and cost

- GPU: one NVIDIA A100 80 GB or H100 80 GB;
- host RAM: at least 96 GB;
- free disk: at least 40 GB;
- Stage 0 inference after image/checkpoint staging: approximately 10–45 minutes;
- first-time image build, downloads and checks: an additional 30–60 minutes depending on network/cache.

Using the provider rates recorded in `CLOUD_RUN_PLAN.md`, Stage 0 inference is approximately **$0.40–$1.20 on A100 80 GB** or **$0.45–$1.75 on H100 80 GB**. A conservative first-time end-to-end allowance is **$2–$6**, excluding tax/egress. Price and availability must be checked immediately before launch, and the host must be terminated after logs are copied.

## Mandatory inspection before any Stage 1 authorization

Inspect all of the following under the new Stage 0 run directory:

1. `STAGE0_COMPLETE.txt` exists and says PASS;
2. `logs/rfd3.log` contains no traceback, fallback, OOM, retry or warning indicating changed chain/hotspot interpretation;
3. `logs/output_validation.json` says PASS and reports exactly chains A/B/C and a 55–75 residue binder;
4. `provenance/git_commit.txt` is the intended audit commit and `git_status.txt` is empty;
5. `provenance/container_digest.txt`, `pip_freeze.txt` and `foundry_installed.txt` are complete and match the planned environment;
6. `provenance/checkpoint_hashes.txt` reports all three files OK;
7. `provenance/nvidia-smi-q.txt` shows the intended NVIDIA GPU/driver and no CPU/MPS fallback;
8. `provenance/elapsed_seconds.txt` and `peak_gpu_memory_mib.txt` are plausible and within the selected GPU capacity;
9. `output/` contains exactly one CIF.gz and one JSON and neither is copied into scientific ranking directories;
10. the cloud instance has been stopped/terminated after copying these records.

Only a separate explicit human authorization may allow Stage 1. A Stage 0 PASS is a pipeline readiness result, not evidence of binding or selectivity.

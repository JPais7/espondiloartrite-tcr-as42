# Cloud GPU run plan — minimal AS4.2 negative-design pilot

## Status and boundary

This document defines a reproducible cloud run but does **not** authorize or launch cloud compute.

The local Mac run produced one RFD3 backbone, three ProteinMPNN sequences and one three-sample RF3 refold. It proved that the pipeline and file formats execute end to end. It is explicitly a **smoke test only** and is excluded from candidate ranking and the biological GO/NO-GO decision. Its manifest is `results/pilot/smoke_test_manifest.json`.

This remains a feasibility experiment. Predicted complex confidence is not evidence of binding, specificity, therapeutic activity or safety.

## Question answered by the run

Can a very small, preregistered design set yield at least one modeled interface that:

1. contacts F98 and at least two of S99/T100/D101, with at least four distinct residues of `VGLFSTDTQ` contacted;
2. derives no more than 40% of target contacts from residues outside CDR3β;
3. is structurally plausible with both 7N2O and 7N2N;
4. loses predicted interaction quality for F98Y, F98A and at least two of S99A/T100A/D101A;
5. separates 7N2O/7N2N from every mandatory negative (7N2S, 8CX4, 9PBG, 9PBH) by a margin larger than model uncertainty?

The frozen machine-readable definitions are:

- target and panels: `config/pilot_target_spec.json`;
- generation/validation size and seeds: `config/pilot_run.json`;
- acceptance/rejection rules: `config/pilot_acceptance_criteria.json`;
- RFD3 atom-level conditioning: `config/rfd3_pilot.json`.

## Inputs and audit state

The Phase 1.5 panel contains 15 structures. `scripts/audit_phase1_5_panel.py` verifies, from deposited PDB ATOM records, that every declared CDR3α/β sequence occurs exactly in every declared TCR chain and that those chains are identified as alpha/beta TCR components in the PDB header. Current result: 15/15 pass. The legacy `TBD` controls in `data/negative_controls.csv` are marked obsolete and superseded by the Phase 1.5 panel.

Required cloud inputs are already versioned in the repository:

- positive structures: `data/raw/7N2O.pdb`, `data/raw/7N2N.pdb`;
- mandatory negatives: `data/raw/7N2S.pdb`, `data/raw/8CX4.pdb`, `data/raw/9PBG.pdb`, `data/raw/9PBH.pdb`;
- fixed-backbone perturbations and natural counterfactual manifest: `data/counterfactuals/`;
- provenance audit: `results/pilot/panel_audit.json`;
- cropped generation target: `data/pilot/7N2O_AS4_2_variable_domains.pdb`.

Natural motif replacements use their experimental structures. Point mutants are deliberately fixed-backbone perturbations without repacking or minimization and may only be used for comparative residue-dependence tests.

## Exact environment

The reproducible container recipe is `cloud/Dockerfile`. The complete package set observed in the successful smoke environment is in `cloud/environment-smoke-lock.txt`; the concise version record is `cloud/environment.json`.

Core software:

| Component | Version |
|---|---|
| Foundry/RFD3/MPNN/RF3 | commit `a24335323b8fe8a927319d47b10f5bffffc17969` |
| rc-foundry | `0.0.1.dev1185+ga24335323` |
| PyTorch | `2.14.0` |
| AtomWorks | `2.2.1` |
| Biotite | `1.4.0` |
| Python | `3.12` |

The exact checkpoint URLs and SHA-256 digests are in `cloud/model_manifest.json`. The three checkpoints occupy about 5.34 GB. Hash verification is mandatory before inference.

## Smallest defensible experiment

### Stage 0 — cloud smoke check

Run `cloud/run_stage0.sh` inside the pinned container. It performs the static package audit, requires CUDA, verifies all checkpoint hashes, records provenance and generates **exactly one** disposable RFD3 backbone at batch size 1. It records elapsed time and peak observed GPU memory, validates the output chains/schema, then stops. It cannot invoke sequence design, RF3, `run_generation.sh` or `run_validation.sh`.

On an already provisioned and explicitly authorized GPU host, from the repository root, the exact launch sequence is:

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

The checkpoint directory must contain the three files named in `cloud/checksums.sha256`. Stage 0 output is not a scientific candidate and must never enter ranking. A successful stop does not authorize Stage 1.

Resource classes are deliberately separate: **Stage 0 calibration** requires an NVIDIA GPU with at least 80 GB VRAM and at least 60 GiB RAM visible inside the container. A host in the 60–96 GiB range is marked `CALIBRATION_ONLY` and cannot authorize Stage 1–3. The **Stage 1–3 scientific pilot** retains the requirement for an A100/H100-class NVIDIA GPU with at least 80 GB VRAM and at least 96 GiB RAM.

### Stage 1 — generation: 12 candidates maximum

- Generate exactly **4 RFD3 backbones** in one batch, seed `42017`, binder length 55–75 residues.
- Condition at atom level on F98, S99, T100 and D101.
- Generate exactly **3 ProteinMPNN sequences per backbone**, seed `42018`, temperature 0.1.
- Hard cap: **12 candidate sequences**. Do not replace failed designs or increase the batch.

After a separate authorization, set a unique `PILOT_RUN_ID` (for example `pilot-20260920T120000Z`) and the same immutable `PILOT_CONTAINER_DIGEST` used for Stage 0, then run `PILOT_RUN_ID=... PILOT_CONTAINER_DIGEST=... bash cloud/run_generation.sh`. All generation outputs and provenance are isolated under `results/pilot/cloud/<PILOT_RUN_ID>/`; the script refuses reuse of an existing run directory and writes `GENERATION_COMPLETE.txt` only after exactly 4 backbones and 12 candidates are inventoried and hashed.

Before RF3, reject candidates mechanically for missing chains, backbone clashes, noncanonical residues, gross low complexity, or failure to contact F98 plus two additional preregistered residues in the generated pose. This is a filter, not evidence of binding.

### Stage 2 — target-only screen

Refold at most 12 candidates against AS4.2 with one RF3 seed (`42019`). Rank automatically using the frozen structural and confidence metrics. Retain at most **two** candidates. If fewer than two meet the absolute target thresholds, continue with those that pass; if none pass, stop with NO-GO.

All three local smoke sequences fail the frozen generation-pose filter (single-residue enrichment, only three core contacts, insufficient additional hotspots and 55.56% germline/framework contacts). The one sequence also refolded as a smoke check had RF3 ipTM 0.272–0.278 and fails the positive ipTM threshold of 0.60. None can advance.

### Stage 3 — blinded multistate test

For at most two survivors, prepare 11 states per candidate:

- positives: 7N2O and 7N2N;
- mandatory negatives: 7N2S, 8CX4, 9PBG, 9PBH;
- perturbations: F98Y, F98A, S99A, T100A, D101A.

Run each state with three independent RF3 seeds: `42017`, `42018`, `42019`, one diffusion sample per process. Maximum focused validation: **66 predictions**. Including the target-only screen, the complete scientific run contains at most 78 RF3 predictions.

The structural states are built by `scripts/prepare_cloud_validation_complexes.py`. With the same `PILOT_RUN_ID` and `PILOT_CONTAINER_DIGEST`, run `PILOT_RUN_ID=... PILOT_CONTAINER_DIGEST=... bash cloud/run_validation.sh`. Validation checks the generation marker, commit, digest, checkpoint/config/script hashes and candidate inventory before any RF3 work, and writes all outputs under that same run directory.

## Frozen scoring and uncertainty

For each RF3 replicate define:

`Q = ipTM - mean(minimum binder–alpha PAE, minimum binder–beta PAE) / 31`

Absolute positive plausibility requires all of:

- ipTM ≥ 0.60;
- binder-chain pTM ≥ 0.70;
- best binder–target chain-pair minimum PAE ≤ 5.0 Å;
- no reported chain clash.

For every target/control comparison, calculate the mean difference in `Q` across independent seeds. The effective uncertainty is the maximum of:

- propagated standard error from the three seeds;
- half the absolute 7N2O-versus-7N2N difference in `Q`;
- a floor of 0.02 Q units.

A required effect passes only if its raw difference exceeds its specified floor **and** exceeds `2 × effective uncertainty`. The raw floors are 0.10 against every mandatory negative, 0.10 for F98A, and 0.05 for F98Y and for at least two of S99A/T100A/D101A. These rules are encoded in `config/pilot_acceptance_criteria.json`.

Predicted atom contacts are measured at ≤4.5 Å heavy-atom distance. At least four core CDR3β residues must contact the binder; F98 and at least two of S99/T100/D101 are mandatory. Contacts outside beta CDR3 residues 91–105 must be ≤40% of all target contacts.

No post-hoc metric substitution, threshold relaxation or selective omission of a negative is allowed.

## Decision

**GO** requires at least one candidate to pass every structural, contact, multistate, mutation-dependence and uncertainty rule.

**NO-GO** applies if no candidate passes, if a mandatory negative cannot be separated beyond uncertainty, or if the run cannot obtain stable confidence estimates. NO-GO does not justify increasing candidate count. The next change would need to be one of:

- narrow/redefine the biological target population so the strongest mimics are intended positives rather than off-targets;
- target a composite epitope containing additional clonotype-specific CDR3α/β features;
- use a recognition format capable of reading a larger discontinuous epitope rather than a compact F/Y–STDTQ surface;
- obtain experimental counterselection/binding data to calibrate or replace model-only ranking.

## GPU, storage, runtime and cost

Recommended single-node minimum for Stage 1–3:

- 1 × NVIDIA A100 80 GB or H100 80 GB;
- ≥96 GB host RAM;
- ≥40 GB free persistent disk (checkpoints, container layers, inputs and outputs);
- CUDA 12.8-compatible driver/runtime.

Stage 0 calibration may use 60–96 GiB visible RAM, but must record `MemTotal`, `MemAvailable`, swap and GPU memory telemetry. A 64 GiB host is calibration-only.

The 80 GB choice is conservative: it permits RFD3/RF3 batches without relying on unverified memory-saving changes. If Stage 0 shows peak VRAM below 45 GB, an L40S 48 GB may be tested, but it is not the preregistered execution target.

Estimated wall time, including a calibration margin:

| Work | H100 80 GB | A100 80 GB |
|---|---:|---:|
| setup, image, weights, hash checks | 0.5–1.0 h | 0.5–1.0 h |
| Stage 0 only: one disposable RFD3 backbone | 0.15–0.5 h | 0.25–0.75 h |
| Stage 1: 4 RFD3 backbones + MPNN | 0.5–1.0 h | 1–2 h |
| ≤12 target screens | 0.5–1.5 h | 1–3 h |
| ≤66 focused RF3 predictions | 3–6 h | 6–12 h |
| total reserved time | **5–10 h** | **9–18 h** |

These are planning estimates, not measured benchmarks; Stage 0 must record actual throughput and revise only the cost forecast, never the candidate cap or thresholds.

As of 18 September 2026, RunPod lists A100 80 GB pods at $1.59/h, H100 PCIe 80 GB at $2.89/h and H100 SXM 80 GB at $3.49/h ([current pricing](https://www.runpod.io/pricing)). This implies approximate compute costs, excluding storage/tax/egress:

- A100 80 GB, 9–18 h: **$14–$29**;
- H100 PCIe 80 GB, 5–10 h: **$15–$29**;
- H100 SXM 80 GB, 5–10 h: **$17–$35**.

Budget ceiling for authorization should be **$40 compute plus $5 storage/egress contingency**. The provider bills while the pod remains running, so the instance must be terminated after outputs and logs are copied. Prices and availability must be rechecked immediately before launch.

## Execution checklist — do not run yet

1. Build `cloud/Dockerfile` and record the resulting image digest.
2. Attach a 40 GB volume and download the three checkpoints from `cloud/model_manifest.json`.
3. Verify every SHA-256 digest.
4. Record `nvidia-smi`, container digest, package freeze and Git commit.
5. Run Stage 0 only; record peak VRAM and elapsed time.
6. Stop. Copy and inspect every Stage 0 provenance file, including RAM class, host-memory totals, peak host memory, minimum available memory, swap, peak VRAM, elapsed time, and the full RFD3 log for OOM signatures.
7. Obtain separate explicit human authorization for Stage 1. Only then may `cloud/run_generation.sh` be run once.
8. Apply the automatic filters; write `top2.txt` without manual candidate substitution.
9. Run `cloud/run_validation.sh` once.
10. Copy all logs, CIFs, JSON/CSV metrics and environment records back to the repository.
11. Terminate the cloud instance.
12. Produce `PILOT_RESULTS.md`, machine-readable rankings and `PILOT_GO_NO_GO.md` from the frozen rules.

No cloud resource has been created or started by preparation of this plan.

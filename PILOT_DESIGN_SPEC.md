# Minimal negative-design pilot specification

## Scope

This is a preregistered computational feasibility experiment. It tests whether a small design set can model differential recognition of AS4.2 `VGLFSTDTQ` over the closest known TCR mimics. It does not test or establish binding, specificity, therapeutic activity or safety.

Cloud execution is planned in `CLOUD_RUN_PLAN.md` but is not authorized or started.

## Frozen inputs

- positives: 7N2O and 7N2N;
- mandatory negatives: 7N2S, 8CX4, 9PBG and 9PBH;
- secondary germline controls: 7N2P, 7N2Q, 8RYP, 8RYQ, 5KS9, 5KSA, 9J4S, 6ZKW and 9YIR;
- point perturbations: F98Y, F98A, S99A, T100A and D101A;
- target core: beta-chain residues 95–103, `VGLFSTDTQ`;
- mandatory chemical anchor: F98 plus at least two of S99/T100/D101.

The authoritative machine-readable definition is `config/pilot_target_spec.json`. Chain/CDR3 provenance is recorded in `results/pilot/panel_audit.json` (15/15 entries pass).

## Candidate budget

- four RFD3 backbones, seed 42017;
- three ProteinMPNN sequences per backbone, seed 42018;
- hard maximum of 12 scientific candidates;
- target-only RF3 screen of at most 12 candidates;
- focused validation of at most two candidates across 11 states and three independent seeds;
- no replacement generation when candidates fail.

The local RFD3/ProteinMPNN/RF3 outputs under `results/pilot/*_smoke` are pipeline smoke tests and are excluded from this budget and from scientific ranking.

## Pre-generation conditioning

RFD3 receives both AS4.2 variable domains and atom-level hotspots on F98, S99, T100 and D101. ProteinMPNN designs only the binder chain; the TCR chains remain fixed. Exact inputs and parameters are in `config/rfd3_pilot.json` and `config/pilot_run.json`.

## Rejection rules

A candidate is rejected if any of the following is true:

- binder length is outside 55–75 residues, contains noncanonical residues, has sequence entropy below 2.5 bits, or one residue type exceeds 30%;
- the generated pose contacts fewer than four core CDR3β residues, misses F98, or contacts fewer than two of S99/T100/D101;
- more than 40% of target contacts are outside beta CDR3 residues 91–105;
- either AS4.2 conformer fails the absolute RF3 plausibility thresholds;
- any mandatory negative is not separated by the frozen raw margin and by more than twice effective uncertainty;
- F98Y/F98A or the additional alanine perturbations do not produce the required loss;
- predicted binding survives substantial mutation of the intended hotspot.

All numerical rules, including the RF3 quality score `Q`, uncertainty floor and raw-effect floors, are in `config/pilot_acceptance_criteria.json`.

## Decision

GO requires at least one candidate to pass every rule. Any missing comparison, unstable estimate or failure against one mandatory negative yields NO-GO for the current method and target definition. Compute will not be increased solely because the result is negative.

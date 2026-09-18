#!/usr/bin/env python3
"""Confirm that Stage 0 produced exactly one structurally valid disposable backbone."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from biotite.structure.io import load_structure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir", type=Path)
    args = parser.parse_args()
    structures = sorted(args.outdir.glob("*.cif.gz"))
    metadata = sorted(args.outdir.glob("*.json"))
    if len(structures) != 1:
        raise SystemExit(f"expected exactly one Stage 0 CIF, found {len(structures)}")
    if len(metadata) != 1:
        raise SystemExit(f"expected exactly one Stage 0 JSON, found {len(metadata)}")

    array = load_structure(structures[0])
    chains = set(map(str, array.chain_id))
    if chains != {"A", "B", "C"}:
        raise SystemExit(f"unexpected output chains: {sorted(chains)}")
    residues = {}
    for chain in sorted(chains):
        residues[chain] = sorted({int(x) for x in array.res_id[array.chain_id == chain]})
    if not 55 <= len(residues["A"]) <= 75:
        raise SystemExit(f"binder chain A has invalid length {len(residues['A'])}")
    if len(residues["B"]) != 109 or len(residues["C"]) != 108:
        raise SystemExit("target chain lengths do not match D2-110/F3-110")

    # Reading the compressed text catches a truncated gzip even if the parser was permissive.
    with gzip.open(structures[0], "rt") as handle:
        if "data_" not in handle.read(256):
            raise SystemExit("output is not a valid mmCIF data block")
    print(json.dumps({"status": "PASS", "structure": str(structures[0]),
                      "binder_residues": len(residues["A"]), "chains": sorted(chains)}))


if __name__ == "__main__":
    main()


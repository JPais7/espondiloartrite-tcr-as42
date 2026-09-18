#!/usr/bin/env python3
"""Prepare the cropped AS4.2 variable-domain target used by RFD3."""

from pathlib import Path


SOURCE = Path("data/raw/7N2O.pdb")
OUT = Path("data/pilot/7N2O_AS4_2_variable_domains.pdb")


def main():
    kept = []
    for line in SOURCE.read_text().splitlines():
        if line.startswith("ATOM  ") and line[21] in {"D", "F"} and int(line[22:26]) <= 110:
            kept.append(line)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join([
        "REMARK 950 CROPPED FROM 7N2O FOR RFD3 PILOT; CHAINS D/F RESIDUES 1-110",
        *kept,
        "END",
    ]) + "\n")
    print(f"wrote {OUT} with {len(kept)} atoms")


if __name__ == "__main__":
    main()

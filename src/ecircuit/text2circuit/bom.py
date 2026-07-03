# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Build and render a Bill of Materials from a Circuit."""

from __future__ import annotations

import csv
import io

from pydantic import BaseModel

from .models import Circuit


class BomLine(BaseModel):
    qty: int
    type: str
    value: str
    part_number: str | None
    refs: list[str]


def build_bom(circuit: Circuit) -> list[BomLine]:
    """Group identical parts (same type, value, part number) into BOM lines."""
    groups: dict[tuple[str, str, str | None], list[str]] = {}
    for component in circuit.components:
        key = (component.type, component.value, component.part_number)
        groups.setdefault(key, []).append(component.ref)
    lines = [
        BomLine(
            qty=len(refs), type=kind, value=value, part_number=part_number, refs=refs
        )
        for (kind, value, part_number), refs in groups.items()
    ]
    lines.sort(key=lambda line: line.refs[0])
    return lines


def to_csv(lines: list[BomLine]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["Qty", "Type", "Value", "Part Number", "References"])
    for line in lines:
        writer.writerow(
            [
                line.qty,
                line.type,
                line.value,
                line.part_number or "",
                " ".join(line.refs),
            ]
        )
    return buffer.getvalue()


def to_markdown(lines: list[BomLine]) -> str:
    rows = [
        "| Qty | Type | Value | Part Number | References |",
        "|---|---|---|---|---|",
    ]
    for line in lines:
        rows.append(
            f"| {line.qty} | {line.type} | {line.value} "
            f"| {line.part_number or ''} | {' '.join(line.refs)} |"
        )
    return "\n".join(rows) + "\n"

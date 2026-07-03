# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""eCircuit command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .rendering import render_circuit
from .text2circuit import (
    Circuit,
    CircuitParseError,
    DeepSeekError,
    build_bom,
    generate,
    to_csv,
    to_markdown,
    to_spice,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecircuit",
        description="eCircuit — AI-powered electronic circuit design toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    t2c = subparsers.add_parser(
        "text2circuit",
        help="generate a netlist and BOM from a text description",
    )
    t2c.add_argument("description", help="plain-text description of the circuit")
    t2c.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        metavar="DIR",
        help="write <name>.cir, <name>_bom.csv, <name>_bom.md, <name>.json and "
        "<name>.txt (schematic) to DIR (default: print to stdout)",
    )
    t2c.add_argument(
        "--ascii",
        action="store_true",
        help="draw the schematic with plain ASCII instead of Unicode",
    )

    render = subparsers.add_parser(
        "render",
        help="draw a text schematic from a saved circuit .json file",
    )
    render.add_argument(
        "circuit_json", type=Path, help="circuit .json produced by text2circuit"
    )
    render.add_argument(
        "--ascii",
        action="store_true",
        help="draw with plain ASCII instead of Unicode",
    )
    return parser


def _run_text2circuit(args: argparse.Namespace) -> int:
    result = generate(args.description)
    circuit = result.circuit
    if result.repair_rounds:
        print(
            f"note: design was repaired in {result.repair_rounds} round(s) "
            "after validation errors",
            file=sys.stderr,
        )
    for issue in result.warnings:
        print(f"warning: {issue.message}", file=sys.stderr)
    netlist = to_spice(circuit)
    bom_lines = build_bom(circuit)
    schematic = render_circuit(circuit, style="ascii" if args.ascii else "unicode")

    if args.out is None:
        print(schematic)
        print(netlist)
        print(to_markdown(bom_lines))
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{circuit.name}.cir").write_text(netlist)
    (args.out / f"{circuit.name}_bom.csv").write_text(to_csv(bom_lines))
    (args.out / f"{circuit.name}_bom.md").write_text(to_markdown(bom_lines))
    (args.out / f"{circuit.name}.json").write_text(
        circuit.model_dump_json(indent=2) + "\n"
    )
    (args.out / f"{circuit.name}.txt").write_text(schematic)
    print(
        f"wrote {circuit.name}.cir, {circuit.name}_bom.csv/.md, {circuit.name}.json, "
        f"{circuit.name}.txt to {args.out}"
    )
    return 0


def _run_render(args: argparse.Namespace) -> int:
    circuit = Circuit.model_validate_json(args.circuit_json.read_text())
    print(render_circuit(circuit, style="ascii" if args.ascii else "unicode"))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "text2circuit":
            return _run_text2circuit(args)
        if args.command == "render":
            return _run_render(args)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (DeepSeekError, CircuitParseError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1

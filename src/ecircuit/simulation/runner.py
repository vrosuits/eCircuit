# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Run ngspice in batch mode and parse its results."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel

from ecircuit.text2circuit.models import Circuit

from .deck import SimulationError, build_deck, recordable_nets

_OP_LINE = re.compile(r"^\s*(\S+)\s*=\s*([-+]?[\d.]+(?:[eE][-+]?\d+)?)\s*$")


class SimulationResult(BaseModel):
    """Transient traces: a shared time axis plus one voltage list per net."""

    time: list[float]
    traces: dict[str, list[float]]
    warnings: list[str] = []


def ngspice_available() -> bool:
    return shutil.which("ngspice") is not None


def _require_ngspice() -> None:
    if not ngspice_available():
        raise SimulationError(
            "ngspice is not installed — install it with e.g. 'sudo apt install ngspice'"
        )


def _run(deck: str, workdir: Path) -> str:
    deck_path = workdir / "deck.cir"
    log_path = workdir / "ngspice.log"
    deck_path.write_text(deck)
    result = subprocess.run(
        ["ngspice", "-b", "-o", str(log_path), str(deck_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    log = log_path.read_text() if log_path.exists() else ""
    if result.returncode != 0 and "Error" in log:
        raise SimulationError(f"ngspice failed:\n{_extract_errors(log)}")
    if "Error" in log and "simulation" not in log.lower():
        # ngspice often exits 0 even on fatal deck errors
        errors = _extract_errors(log)
        if errors:
            raise SimulationError(f"ngspice reported errors:\n{errors}")
    return log


def _extract_errors(log: str) -> str:
    lines = [line for line in log.splitlines() if "error" in line.lower()]
    return "\n".join(lines[:10])


def simulate_op(circuit: Circuit) -> tuple[dict[str, float], list[str]]:
    """DC operating point: net name -> voltage."""
    _require_ngspice()
    deck, warnings = build_deck(circuit, ["op", "print all"])
    with tempfile.TemporaryDirectory(prefix="ecircuit-sim-") as tmp:
        log = _run(deck, Path(tmp))
    voltages = parse_op_log(log)
    wanted = {net.lower(): net for net in recordable_nets(circuit)}
    return (
        {wanted[name]: value for name, value in voltages.items() if name in wanted},
        warnings,
    )


def simulate_tran(
    circuit: Circuit, step: str, stop: str, uic: bool = False
) -> SimulationResult:
    """Transient analysis; step/stop are SPICE time values like '1m' '5'.

    With uic=True the run starts from zero initial conditions (capacitors
    discharged) instead of the DC operating point.
    """
    _require_ngspice()
    nets = recordable_nets(circuit)
    vectors = " ".join(f"v({net})" for net in nets)
    with tempfile.TemporaryDirectory(prefix="ecircuit-sim-") as tmp:
        data_path = Path(tmp) / "trace.dat"
        deck, warnings = build_deck(
            circuit,
            [
                "set wr_singlescale",
                "set wr_vecnames",
                f"tran {step} {stop}{' uic' if uic else ''}",
                f"wrdata {data_path} {vectors}",
            ],
        )
        _run(deck, Path(tmp))
        if not data_path.exists():
            raise SimulationError("ngspice produced no trace data — check the deck")
        time, traces = parse_wrdata(data_path.read_text(), nets)
    return SimulationResult(time=time, traces=traces, warnings=warnings)


def parse_op_log(log: str) -> dict[str, float]:
    """Parse 'print all' output lines like 'vout = 4.999e+00' (ngspice lowercases)."""
    values: dict[str, float] = {}
    for line in log.splitlines():
        if match := _OP_LINE.match(line):
            name, value = match.groups()
            if "#branch" not in name:
                values[name.lower()] = float(value)
    return values


def parse_wrdata(
    text: str, nets: list[str]
) -> tuple[list[float], dict[str, list[float]]]:
    """Parse wrdata output (wr_singlescale + wr_vecnames: header, then columns)."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise SimulationError("empty trace data from ngspice")
    header = lines[0].split()
    lower_to_net = {f"v({net.lower()})": net for net in nets}
    columns: list[list[float]] = [[] for _ in header]
    for line in lines[1:]:
        for index, cell in enumerate(line.split()):
            columns[index].append(float(cell))
    time = columns[0]
    traces = {
        lower_to_net[name.lower()]: columns[index]
        for index, name in enumerate(header)
        if name.lower() in lower_to_net
    }
    return time, traces

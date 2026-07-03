# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Text2Circuit: translate text descriptions into schematics, BOMs, and netlists (DeepSeek API)."""

from .bom import BomLine, build_bom, to_csv, to_markdown
from .client import DeepSeekClient, DeepSeekError
from .models import Circuit, Component
from .netlist import to_spice
from .pipeline import CircuitParseError, generate_circuit, parse_circuit_response

__all__ = [
    "BomLine",
    "Circuit",
    "CircuitParseError",
    "Component",
    "DeepSeekClient",
    "DeepSeekError",
    "build_bom",
    "generate_circuit",
    "parse_circuit_response",
    "to_csv",
    "to_markdown",
    "to_spice",
]

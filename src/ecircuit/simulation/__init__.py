# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Simulation: SPICE/PSPICE integration and virtual instruments."""

from .deck import SimulationError, build_deck, recordable_nets
from .runner import (
    SimulationResult,
    ngspice_available,
    parse_op_log,
    parse_wrdata,
    simulate_op,
    simulate_tran,
)

__all__ = [
    "SimulationError",
    "SimulationResult",
    "build_deck",
    "ngspice_available",
    "parse_op_log",
    "parse_wrdata",
    "recordable_nets",
    "simulate_op",
    "simulate_tran",
]

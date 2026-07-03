# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Datasheet pinouts for common ICs, used to verify AI-generated wiring."""

from __future__ import annotations

# Canonical pin-function names, indexed by (pin number - 1).
_555 = ["GND", "TRIG", "OUT", "RESET", "CTRL", "THRES", "DISCH", "VCC"]

KNOWN_PINOUTS: dict[str, list[str]] = {
    "555": _555,
    "NE555": _555,
    "NE555P": _555,
    "LM555": _555,
    "NA555": _555,
    "SA555": _555,
    "SE555": _555,
    "TLC555": _555,
    "ICM7555": _555,
}

# Alternate spellings mapped to the canonical name used in KNOWN_PINOUTS.
_NAME_ALIASES = {
    "THRESHOLD": "THRES",
    "TH": "THRES",
    "TRIGGER": "TRIG",
    "TR": "TRIG",
    "DISCHARGE": "DISCH",
    "DIS": "DISCH",
    "CONTROL": "CTRL",
    "CONT": "CTRL",
    "CV": "CTRL",
    "RST": "RESET",
    "OUTPUT": "OUT",
    "Q": "OUT",
    "V+": "VCC",
    "VDD": "VCC",
    "VS": "VCC",
    "V-": "GND",
    "VSS": "GND",
    "GROUND": "GND",
}


def canonical_pin_name(name: str) -> str:
    name = name.strip().upper()
    return _NAME_ALIASES.get(name, name)


def lookup_pinout(device: str) -> list[str] | None:
    return KNOWN_PINOUTS.get(device.strip().upper())

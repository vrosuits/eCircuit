# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Datasheet pinouts for common ICs, used to verify AI-generated wiring.

Each pinout lists canonical pin-function names indexed by (pin number - 1).
A slot may be a tuple when several names are legitimate for the same pin
(e.g. the AMS1117's pin 1 is GND on fixed versions, ADJ on adjustable ones).
"""

from __future__ import annotations

import re

PinSlot = str | tuple[str, ...]

# --- timers ---------------------------------------------------------------
_555 = ["GND", "TRIG", "OUT", "RESET", "CTRL", "THRES", "DISCH", "VCC"]

# --- op-amps (canonical channel naming: OUT1, IN1-, IN1+, VCC, GND) -------
# Single, 741-style DIP-8: offset null on 1 and 5, NC on 8.
_OPAMP_SINGLE = ["NULL", "IN-", "IN+", "GND", "NULL", "OUT", "VCC", "NC"]
# OP07 differs: offset trim on 1 and 8, NC on 5.
_OP07 = ["NULL", "IN-", "IN+", "GND", "NC", "OUT", "VCC", "NULL"]
# Dual DIP-8 (LM358/TL072 style).
_OPAMP_DUAL = ["OUT1", "IN1-", "IN1+", "GND", "IN2+", "IN2-", "OUT2", "VCC"]
# Quad DIP-14 (LM324/TL074 style): V+ on 4, V- on 11.
_OPAMP_QUAD = [
    "OUT1",
    "IN1-",
    "IN1+",
    "VCC",
    "IN2+",
    "IN2-",
    "OUT2",
    "OUT3",
    "IN3-",
    "IN3+",
    "GND",
    "IN4+",
    "IN4-",
    "OUT4",
]

# --- voltage regulators (TO-220 pin order) ---------------------------------
_REG_78 = ["IN", "GND", "OUT"]  # 78xx positive fixed
_REG_78L = ["OUT", "GND", "IN"]  # 78Lxx TO-92 is reversed!
_REG_79 = ["GND", "IN", "OUT"]  # 79xx negative fixed
_LM317 = ["ADJ", "OUT", "IN"]  # positive adjustable
_LM337 = ["ADJ", "IN", "OUT"]  # negative adjustable
_LDO_1117: list[PinSlot] = [("GND", "ADJ"), "OUT", "IN"]

KNOWN_PINOUTS: dict[str, list[PinSlot]] = {
    # 555 timers
    "555": _555,
    "NE555": _555,
    "NE555P": _555,
    "LM555": _555,
    "NA555": _555,
    "SA555": _555,
    "SE555": _555,
    "TLC555": _555,
    "ICM7555": _555,
    # single op-amps
    "741": _OPAMP_SINGLE,
    "UA741": _OPAMP_SINGLE,
    "LM741": _OPAMP_SINGLE,
    "MC1741": _OPAMP_SINGLE,
    "TL071": _OPAMP_SINGLE,
    "TL081": _OPAMP_SINGLE,
    "LF351": _OPAMP_SINGLE,
    "OP07": _OP07,
    "OP-07": _OP07,
    # dual op-amps
    "LM358": _OPAMP_DUAL,
    "LM833": _OPAMP_DUAL,
    "LM4562": _OPAMP_DUAL,
    "TL072": _OPAMP_DUAL,
    "TL082": _OPAMP_DUAL,
    "NE5532": _OPAMP_DUAL,
    "RC4558": _OPAMP_DUAL,
    "MC1458": _OPAMP_DUAL,
    "LF353": _OPAMP_DUAL,
    # quad op-amps
    "LM324": _OPAMP_QUAD,
    "LM348": _OPAMP_QUAD,
    "TL074": _OPAMP_QUAD,
    "TL084": _OPAMP_QUAD,
    "LF347": _OPAMP_QUAD,
    # adjustable regulators
    "LM317": _LM317,
    "LM317T": _LM317,
    "LM338": _LM317,
    "LM350": _LM317,
    "LM337": _LM337,
    "LM337T": _LM337,
    # 1117-style LDOs
    "AMS1117": _LDO_1117,
    "LD1117": _LDO_1117,
    "LM1117": _LDO_1117,
    "TLV1117": _LDO_1117,
}

# Fixed 78xx/79xx/78Lxx regulators, with common manufacturer prefixes.
for _volts in ("05", "06", "08", "09", "10", "12", "15", "18", "24"):
    for _prefix in ("", "LM", "L", "MC", "UA", "KA"):
        KNOWN_PINOUTS[f"{_prefix}78{_volts}"] = _REG_78
        KNOWN_PINOUTS[f"{_prefix}79{_volts}"] = _REG_79
        KNOWN_PINOUTS[f"{_prefix}78L{_volts}"] = _REG_78L

# Alternate spellings mapped to the canonical name used in KNOWN_PINOUTS.
# Applied after uppercasing and stripping spaces/underscores.
_NAME_ALIASES = {
    # 555
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
    # outputs
    "OUTPUT": "OUT",
    "Q": "OUT",
    # supply rails
    "V+": "VCC",
    "VCC+": "VCC",
    "VDD": "VCC",
    "VS": "VCC",
    "VS+": "VCC",
    "V-": "GND",
    "VCC-": "GND",
    "VEE": "GND",
    "VSS": "GND",
    "VS-": "GND",
    "GROUND": "GND",
    # op-amp inputs
    "+IN": "IN+",
    "-IN": "IN-",
    "INP": "IN+",
    "INN": "IN-",
    "NONINVERTING": "IN+",
    "INVERTING": "IN-",
    # offset null / trim
    "OFFSETNULL": "NULL",
    "OFFSET": "NULL",
    "BALANCE": "NULL",
    "BAL": "NULL",
    "TRIM": "NULL",
    "VOSTRIM": "NULL",
    # regulators
    "VIN": "IN",
    "INPUT": "IN",
    "VI": "IN",
    "VOUT": "OUT",
    "VO": "OUT",
    "ADJUST": "ADJ",
}

_CHANNEL = {"A": "1", "B": "2", "C": "3", "D": "4"}


def canonical_pin_name(name: str) -> str:
    """Normalize a pin name: aliases, and channel spellings like 1OUT/OUTA -> OUT1."""
    name = name.strip().upper().replace(" ", "").replace("_", "")
    name = _NAME_ALIASES.get(name, name)
    # 1OUT / AOUT / 2IN+ / BIN- -> OUT1 / OUT1 / IN2+ / IN2-
    if match := re.fullmatch(r"([1-4A-D])(OUT|IN[+-])", name):
        channel, func = match.groups()
    # OUT1 / OUTA / IN1+ / INB- -> OUT1 / OUT1 / IN1+ / IN2-
    elif match := re.fullmatch(r"(OUT|IN)([1-4A-D])([+-])?", name):
        func = match.group(1) + (match.group(3) or "")
        channel = match.group(2)
    # +IN2 / -INA -> IN2+ / IN1-
    elif match := re.fullmatch(r"([+-])IN([1-4A-D])", name):
        func = "IN" + match.group(1)
        channel = match.group(2)
    else:
        return name
    channel = _CHANNEL.get(channel, channel)
    if func == "OUT":
        return f"OUT{channel}"
    if func == "IN":
        return f"IN{channel}"
    return f"IN{channel}{func[-1]}"


def acceptable_names(slot: PinSlot) -> tuple[str, ...]:
    return (slot,) if isinstance(slot, str) else slot


def lookup_pinout(device: str) -> list[PinSlot] | None:
    """Find a device's pinout; tolerates voltage suffixes like AMS1117-3.3."""
    key = device.strip().upper()
    if key in KNOWN_PINOUTS:
        return KNOWN_PINOUTS[key]
    return KNOWN_PINOUTS.get(key.split("-")[0])

# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Assemble a full schematic: title, IC packages, passive ladder, legend."""

from __future__ import annotations

from ecircuit.text2circuit.models import Circuit

from .canvas import CHARSETS, Charset
from .icbox import render_ic_box
from .ladder import ladder_components, render_ladder


def _legend(charset: Charset) -> str:
    return (
        f"legend: {charset.tee_down}/{charset.tee_up} = connected to rail, "
        f"{charset.cross} = wires cross (no connection)"
    )


def render_circuit(circuit: Circuit, style: str = "unicode") -> str:
    """Render a circuit as a text schematic in the given style ("unicode"/"ascii")."""
    try:
        charset = CHARSETS[style]
    except KeyError:
        raise ValueError(
            f"unknown rendering style: {style!r} (use 'unicode' or 'ascii')"
        ) from None

    sections = [f"=== {circuit.name} ==="]
    if circuit.description:
        sections.append(circuit.description)

    boxed = [c for c in circuit.components if c.pins or len(c.nodes) > 2]
    sections.extend(render_ic_box(component, charset) for component in boxed)

    if ladder := render_ladder(circuit, charset):
        sections.append(ladder)
    if ladder_components(circuit):
        sections.append(_legend(charset))
    return "\n\n".join(sections) + "\n"

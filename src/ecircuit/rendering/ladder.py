# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Render two-terminal components as a rail ladder.

Each net is a horizontal rail; each component hangs vertically between its
two rails in its own column. Attachment points use tee characters; a wire
passing over an intermediate rail uses the crossing character (no connection).
"""

from __future__ import annotations

import re

from ecircuit.text2circuit.models import GROUND_NODE, Circuit, Component

from .canvas import Canvas, Charset

_RAIL_SPACING = 4
_POWER_NET = re.compile(r"V(CC|DD|IN|\+|BAT)|^\+")


def ladder_components(circuit: Circuit) -> list[Component]:
    return [c for c in circuit.components if not c.pins and len(c.nodes) == 2]


def _order_nets(components: list[Component]) -> list[str]:
    nets = {node for component in components for node in component.nodes}
    power = sorted(net for net in nets if _POWER_NET.match(net))
    ground = [GROUND_NODE] if GROUND_NODE in nets else []
    middle = sorted(nets - set(power) - set(ground))
    return [*power, *middle, *ground]


def render_ladder(circuit: Circuit, charset: Charset) -> str:
    components = ladder_components(circuit)
    if not components:
        return ""
    nets = _order_nets(components)
    rail_row = {net: index * _RAIL_SPACING for index, net in enumerate(nets)}
    margin = max(len(net) for net in nets) + 1

    canvas = Canvas()
    column = margin + 3
    for component in components:
        top, bottom = sorted(component.nodes, key=lambda net: rail_row[net])
        top_row, bottom_row = rail_row[top], rail_row[bottom]
        for row in range(top_row + 1, bottom_row):
            is_rail = row % _RAIL_SPACING == 0
            canvas.put(row, column, charset.cross if is_rail else charset.v)
        canvas.put(top_row, column, charset.tee_down)
        canvas.put(bottom_row, column, charset.tee_up)
        canvas.text(top_row + 1, column + 2, component.ref)
        if component.value:
            canvas.text(top_row + 2, column + 2, component.value)
        column += max(len(component.ref), len(component.value)) + 4

    width = column
    for net, row in rail_row.items():
        canvas.text(row, 0, net.rjust(margin))
        for col in range(margin + 1, width):
            if canvas.get(row, col) == " ":
                canvas.put(row, col, charset.h)
    return canvas.render()

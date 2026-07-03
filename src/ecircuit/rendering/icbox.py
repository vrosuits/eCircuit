# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Render a multi-pin component as a DIP-style package box.

Pins 1..n/2 run down the left side, n..n/2+1 down the right — the way the
physical package looks. Each connected pin gets a stub labelled with its net.
"""

from __future__ import annotations

from ecircuit.text2circuit.models import Component, Pin
from ecircuit.text2circuit.pinouts import lookup_pinout

from .canvas import Charset

_MIN_GAP = 3


def _synthetic_pins(component: Component) -> list[Pin]:
    """Give pin-less multi-terminal parts (e.g. transistors) named pins."""
    kind = component.type.lower()
    if len(component.nodes) == 3 and ("fet" in kind or "mos" in kind):
        names = ["D", "G", "S"]
    elif len(component.nodes) == 3 and "transistor" in kind:
        names = ["C", "B", "E"]  # SPICE order, per the generation prompt
    else:
        names = [f"P{index}" for index in range(1, len(component.nodes) + 1)]
    return [
        Pin(pin=index, name=name, net=net)
        for index, (name, net) in enumerate(zip(names, component.nodes), start=1)
    ]


def render_ic_box(component: Component, charset: Charset) -> str:
    """Draw one component as a DIP package with net-labelled pin stubs."""
    pins = component.pins or _synthetic_pins(component)
    by_number = {pin.pin: pin for pin in pins}

    pinout = lookup_pinout(component.value)
    size = len(pinout) if pinout else max(by_number)
    if size % 2:
        size += 1
    half = size // 2

    left = [by_number.get(number) for number in range(1, half + 1)]
    right = [by_number.get(number) for number in range(size, half, -1)]

    left_name_w = max((len(pin.name) for pin in left if pin), default=0)
    right_name_w = max((len(pin.name) for pin in right if pin), default=0)
    inner_w = max(
        left_name_w + right_name_w + _MIN_GAP,
        len(component.ref) + 2,
        len(component.value) + 2,
    )
    net_w = max((len(pin.net) for pin in pins), default=0)
    indent = net_w + 5  # room for "NET --NN"

    h, v = charset.h, charset.v
    lines = [" " * indent + charset.tl + h * inner_w + charset.tr]
    for left_pin, right_pin in zip(left, right):
        if left_pin:
            stub = f"{left_pin.net:>{net_w}} {h}{h}{left_pin.pin:>2}"
            name = left_pin.name
        else:
            stub, name = " " * indent, ""
        row = stub + v + name.ljust(inner_w - right_name_w)
        if right_pin:
            row += f"{right_pin.name:>{right_name_w}}{v}{right_pin.pin:<2}{h}{h} {right_pin.net}"
        else:
            row += " " * right_name_w + v
        lines.append(row)
    lines.append(" " * indent + v + component.ref.center(inner_w) + v)
    if component.value:
        lines.append(" " * indent + v + component.value.center(inner_w) + v)
    lines.append(" " * indent + charset.bl + h * inner_w + charset.br)
    return "\n".join(line.rstrip() for line in lines)

# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Electrical sanity checks on a Circuit, beyond what the schema enforces."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel

from .models import GROUND_NODE, Circuit, Component
from .pinouts import canonical_pin_name, lookup_pinout

_POWER_PIN_NAMES = {"VCC", "GND"}


class Issue(BaseModel):
    severity: Literal["error", "warning"]
    message: str


def errors(issues: list[Issue]) -> list[Issue]:
    return [issue for issue in issues if issue.severity == "error"]


def validate_circuit(circuit: Circuit) -> list[Issue]:
    """Return every electrical problem found; empty list means clean."""
    issues: list[Issue] = []
    _check_net_degrees(circuit, issues)
    _check_ground(circuit, issues)
    for component in circuit.components:
        _check_current_path(component, issues)
        _check_known_pinout(component, issues)
        _check_output_shorts(component, issues)
    return issues


def _check_net_degrees(circuit: Circuit, issues: list[Issue]) -> None:
    degree = Counter(
        node for component in circuit.components for node in component.nodes
    )
    for net, count in sorted(degree.items()):
        if count < 2:
            issues.append(
                Issue(
                    severity="error",
                    message=f"net {net} connects only one pin — dangling connection",
                )
            )


def _check_ground(circuit: Circuit, issues: list[Issue]) -> None:
    if GROUND_NODE not in {node for c in circuit.components for node in c.nodes}:
        issues.append(
            Issue(severity="warning", message='circuit has no ground net "0"')
        )


def _check_current_path(component: Component, issues: list[Issue]) -> None:
    if len(set(component.nodes)) == 1:
        issues.append(
            Issue(
                severity="error",
                message=(
                    f"{component.ref}: every pin is on net {component.nodes[0]} — "
                    "no current path through the component"
                ),
            )
        )


def _check_known_pinout(component: Component, issues: list[Issue]) -> None:
    pinout = lookup_pinout(component.value)
    if pinout is None:
        return
    if not component.pins:
        issues.append(
            Issue(
                severity="warning",
                message=(
                    f"{component.ref} ({component.value}): known IC given without named "
                    "pins — wiring cannot be verified"
                ),
            )
        )
        return
    for pin in component.pins:
        if pin.pin > len(pinout):
            issues.append(
                Issue(
                    severity="error",
                    message=(
                        f"{component.ref} ({component.value}): pin {pin.pin} does not "
                        f"exist — the device has {len(pinout)} pins"
                    ),
                )
            )
        elif canonical_pin_name(pin.name) != pinout[pin.pin - 1]:
            issues.append(
                Issue(
                    severity="error",
                    message=(
                        f"{component.ref} ({component.value}): pin {pin.pin} is named "
                        f"{pin.name} but the datasheet says pin {pin.pin} is "
                        f"{pinout[pin.pin - 1]}"
                    ),
                )
            )


def _check_output_shorts(component: Component, issues: list[Issue]) -> None:
    if not component.pins:
        return
    by_name: dict[str, str] = {}
    for pin in component.pins:
        by_name.setdefault(canonical_pin_name(pin.name), pin.net)
    out_net = by_name.get("OUT")
    if out_net is None:
        return
    for rail in _POWER_PIN_NAMES:
        if by_name.get(rail) == out_net:
            issues.append(
                Issue(
                    severity="error",
                    message=(
                        f"{component.ref}: OUT pin is shorted to the {rail} rail "
                        f"(net {out_net})"
                    ),
                )
            )

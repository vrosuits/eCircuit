# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Circuit data model: components, named pins, nets, and the circuit itself."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

GROUND_NODE = "0"
_GROUND_ALIASES = {"GND", "GROUND", "VSS"}


def _clean_net(net: str) -> str:
    net = net.strip().upper() or GROUND_NODE
    return GROUND_NODE if net in _GROUND_ALIASES else net


class Pin(BaseModel):
    """One physical pin of a multi-pin device, tied to a net.

    Naming the pin's datasheet function (GND, TRIG, OUT, ...) lets the
    validator check the wiring against known pinouts.
    """

    pin: int = Field(ge=1, description="Physical pin number on the package")
    name: str = Field(description="Datasheet function name, e.g. GND, TRIG, OUT")
    net: str = Field(description="Net this pin connects to")

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, name: str) -> str:
        name = name.strip().upper()
        if not name:
            raise ValueError("pin name must not be empty")
        return name

    @field_validator("net")
    @classmethod
    def _normalize_net(cls, net: str) -> str:
        return _clean_net(net)


class Component(BaseModel):
    """One physical part with its net connections.

    Two-terminal parts use ``nodes`` (ordered pin-to-net: for a resistor
    ``["VIN", "OUT"]`` means pin 1 on net VIN, pin 2 on net OUT). Multi-pin
    devices (ICs) use ``pins`` with datasheet pin numbers and function names;
    ``nodes`` is then derived in pin-number order. Ground is always net "0".
    """

    ref: str = Field(description="Reference designator, e.g. R1, C2, U1")
    type: str = Field(description="Component kind, e.g. resistor, capacitor, ic")
    value: str = Field(
        default="", description="Value or device name, e.g. 10k, 100n, NE555"
    )
    part_number: str | None = None
    description: str | None = None
    nodes: list[str] = Field(
        default_factory=list,
        description="Ordered pin-to-net connections (two-terminal parts)",
    )
    pins: list[Pin] | None = Field(
        default=None, description="Named pins with nets (multi-pin devices)"
    )

    @field_validator("ref")
    @classmethod
    def _normalize_ref(cls, ref: str) -> str:
        ref = ref.strip().upper()
        if not ref or " " in ref:
            raise ValueError(f"invalid reference designator: {ref!r}")
        return ref

    @field_validator("nodes")
    @classmethod
    def _normalize_nodes(cls, nodes: list[str]) -> list[str]:
        return [_clean_net(node) for node in nodes]

    @model_validator(mode="after")
    def _wire_up(self) -> Component:
        if self.pins:
            numbers = [pin.pin for pin in self.pins]
            if len(set(numbers)) != len(numbers):
                raise ValueError(f"{self.ref}: duplicate pin numbers")
            self.pins = sorted(self.pins, key=lambda pin: pin.pin)
            self.nodes = [pin.net for pin in self.pins]
        if not self.nodes:
            raise ValueError(f"{self.ref}: component has no connections")
        return self


class Circuit(BaseModel):
    """A complete circuit: named components wired together by nets."""

    name: str = "untitled"
    description: str = ""
    components: list[Component] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_refs(self) -> Circuit:
        seen: set[str] = set()
        for component in self.components:
            if component.ref in seen:
                raise ValueError(f"duplicate reference designator: {component.ref}")
            seen.add(component.ref)
        return self

    @property
    def nets(self) -> list[str]:
        """All net names in the circuit, ground first, rest sorted."""
        names = {node for component in self.components for node in component.nodes}
        ordered = sorted(names - {GROUND_NODE})
        return [GROUND_NODE, *ordered] if GROUND_NODE in names else ordered

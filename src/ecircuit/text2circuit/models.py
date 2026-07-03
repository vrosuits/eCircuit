# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Circuit data model: components, nets, and the circuit itself."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

GROUND_NODE = "0"


class Component(BaseModel):
    """One physical part with its net connections.

    ``nodes`` is ordered pin-to-net: for a resistor ``["VIN", "OUT"]`` means
    pin 1 on net VIN, pin 2 on net OUT. Ground is always net ``"0"``.
    """

    ref: str = Field(description="Reference designator, e.g. R1, C2, U1")
    type: str = Field(description="Component kind, e.g. resistor, capacitor, ic")
    value: str = Field(
        default="", description="Value or device name, e.g. 10k, 100n, NE555"
    )
    part_number: str | None = None
    description: str | None = None
    nodes: list[str] = Field(min_length=1, description="Ordered pin-to-net connections")

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
        cleaned = []
        for node in nodes:
            node = node.strip().upper() or GROUND_NODE
            if node in {"GND", "GROUND", "VSS"}:
                node = GROUND_NODE
            cleaned.append(node)
        return cleaned


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

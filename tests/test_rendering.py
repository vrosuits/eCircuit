# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

import pytest

from ecircuit.rendering import ASCII, UNICODE, Canvas, render_circuit, render_ic_box
from ecircuit.text2circuit import Circuit, Component, Pin


def _blinker() -> Circuit:
    return Circuit(
        name="blinker",
        description="555 astable LED blinker",
        components=[
            Component(ref="BT1", type="battery", value="9V", nodes=["VCC", "0"]),
            Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "N1"]),
            Component(ref="R2", type="resistor", value="10k", nodes=["N1", "N2"]),
            Component(ref="C1", type="capacitor", value="100u", nodes=["N2", "0"]),
            Component(
                ref="U1",
                type="ic",
                value="NE555",
                pins=[
                    Pin(pin=1, name="GND", net="0"),
                    Pin(pin=2, name="TRIG", net="N2"),
                    Pin(pin=6, name="THRES", net="N2"),
                    Pin(pin=7, name="DISCH", net="N1"),
                    Pin(pin=8, name="VCC", net="VCC"),
                ],
            ),
        ],
    )


def test_canvas_renders_sparse_cells() -> None:
    canvas = Canvas()
    canvas.text(0, 2, "hi")
    canvas.put(2, 0, "x")
    assert canvas.render() == "  hi\n\nx"


def test_ic_box_is_dip_shaped() -> None:
    box = render_ic_box(_blinker().components[-1], UNICODE)
    lines = box.splitlines()
    assert "  0 ── 1│GND" in box
    assert "VCC│8 ── VCC" in box
    assert "DISCH│7 ── N1" in box
    # pin 3 exists on the package but is unconnected: row present, no stub
    assert any(line.lstrip().startswith("│") for line in lines)
    assert "U1" in box
    assert "NE555" in box


def test_transistor_gets_spice_order_pin_names() -> None:
    q1 = Component(
        ref="Q1", type="npn transistor", value="2N3904", nodes=["VC", "VB", "VE"]
    )
    box = render_ic_box(q1, UNICODE)
    assert "│C" in box
    assert "VB ── 2│B" in box
    assert "2N3904" in box


def test_ladder_layout() -> None:
    schematic = render_circuit(_blinker())
    lines = schematic.splitlines()
    # rails are in the ladder section, after the IC box (which also mentions nets)
    vcc_index = max(
        i for i, line in enumerate(lines) if line.lstrip().startswith("VCC ─")
    )
    ground_index = max(
        i for i, line in enumerate(lines) if line.lstrip().startswith("0 ─")
    )
    # power rail above ground rail, components attached with tees
    assert vcc_index < ground_index
    assert UNICODE.tee_down in lines[vcc_index]
    assert "BT1" in schematic
    assert "legend:" in schematic


def test_ascii_style_is_pure_ascii() -> None:
    schematic = render_circuit(_blinker(), style="ascii")
    assert all(ord(char) < 128 for char in schematic)
    assert "BT1" in schematic
    assert ASCII.tl == "+"


def test_unknown_style_rejected() -> None:
    with pytest.raises(ValueError, match="unknown rendering style"):
        render_circuit(_blinker(), style="sepia")


def test_circuit_without_ics_renders_ladder_only() -> None:
    divider = Circuit(
        name="divider",
        components=[
            Component(ref="V1", type="voltage_source", value="5", nodes=["VIN", "0"]),
            Component(ref="R1", type="resistor", value="10k", nodes=["VIN", "VOUT"]),
            Component(ref="R2", type="resistor", value="10k", nodes=["VOUT", "0"]),
        ],
    )
    schematic = render_circuit(divider)
    assert "=== divider ===" in schematic
    assert "R1" in schematic
    assert UNICODE.tl not in schematic  # no IC box drawn

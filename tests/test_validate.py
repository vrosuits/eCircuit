# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

import pytest

from ecircuit.text2circuit import Circuit, Component, Pin, validate_circuit
from ecircuit.text2circuit.validate import errors


def _pins(*triples: tuple[int, str, str]) -> list[Pin]:
    return [Pin(pin=number, name=name, net=net) for number, name, net in triples]


def _blinker_passives() -> list[Component]:
    return [
        Component(ref="BT1", type="battery", value="9V", nodes=["VCC", "0"]),
        Component(ref="R1", type="resistor", value="1meg", nodes=["VCC", "N1"]),
        Component(ref="R2", type="resistor", value="470k", nodes=["N1", "N2"]),
        Component(ref="C1", type="capacitor", value="1u", nodes=["N2", "0"]),
        Component(ref="C2", type="capacitor", value="100n", nodes=["N3", "0"]),
        Component(ref="R3", type="resistor", value="330", nodes=["N4", "N5"]),
        Component(ref="D1", type="led", value="red", nodes=["N5", "0"]),
    ]


def correct_555_blinker() -> Circuit:
    """The 555 astable LED blinker, wired per the datasheet."""
    u1 = Component(
        ref="U1",
        type="ic",
        value="NE555",
        pins=_pins(
            (1, "GND", "0"),
            (2, "TRIG", "N2"),
            (3, "OUT", "N4"),
            (4, "RESET", "VCC"),
            (5, "CTRL", "N3"),
            (6, "THRES", "N2"),
            (7, "DISCH", "N1"),
            (8, "VCC", "VCC"),
        ),
    )
    return Circuit(name="blinker", components=[*_blinker_passives(), u1])


def scrambled_555_blinker() -> Circuit:
    """Regression: the mis-wired 555 that DeepSeek produced in live testing.

    The intent (which function goes to which net) was right, but the pin
    numbers were scrambled — e.g. DISCH ended up on pin 2, which is TRIG.
    """
    u1 = Component(
        ref="U1",
        type="ic",
        value="NE555",
        pins=_pins(
            (1, "GND", "0"),
            (2, "DISCH", "N1"),
            (3, "VCC", "VCC"),
            (4, "TRIG", "N2"),
            (5, "CTRL", "N3"),
            (6, "RESET", "VCC"),
            (7, "OUT", "N4"),
            (8, "THRES", "VCC"),
        ),
    )
    return Circuit(name="blinker", components=[*_blinker_passives(), u1])


def test_correct_555_is_clean() -> None:
    assert validate_circuit(correct_555_blinker()) == []


def test_scrambled_555_pinout_is_caught() -> None:
    issues = validate_circuit(scrambled_555_blinker())
    messages = [issue.message for issue in errors(issues)]
    assert any(
        "pin 2 is named DISCH" in message and "TRIG" in message for message in messages
    )
    assert any(
        "pin 7 is named OUT" in message and "DISCH" in message for message in messages
    )
    assert len(messages) >= 5


def test_dangling_net_is_error() -> None:
    circuit = Circuit(
        components=[
            Component(ref="R1", type="resistor", value="1k", nodes=["VIN", "VOUT"]),
            Component(ref="R2", type="resistor", value="1k", nodes=["VIN", "0"]),
            Component(ref="C1", type="capacitor", value="1n", nodes=["0", "VIN"]),
        ]
    )
    messages = [issue.message for issue in errors(validate_circuit(circuit))]
    assert any("net VOUT connects only one pin" in message for message in messages)


def test_no_current_path_is_error() -> None:
    circuit = Circuit(
        components=[
            Component(ref="R1", type="resistor", value="1k", nodes=["A", "A"]),
            Component(ref="R2", type="resistor", value="1k", nodes=["A", "0"]),
            Component(ref="R3", type="resistor", value="1k", nodes=["A", "0"]),
        ]
    )
    messages = [issue.message for issue in errors(validate_circuit(circuit))]
    assert any("R1" in message and "no current path" in message for message in messages)


def test_out_shorted_to_rail_is_error() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="MYSTERY_IC",
        pins=_pins((1, "GND", "0"), (2, "OUT", "VCC"), (3, "VCC", "VCC")),
    )
    load = Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "0"])
    messages = [
        issue.message
        for issue in errors(validate_circuit(Circuit(components=[u1, load])))
    ]
    assert any("OUT pin is shorted to the VCC rail" in message for message in messages)


def test_known_ic_without_pins_is_warning() -> None:
    circuit = Circuit(
        components=[
            Component(ref="U1", type="ic", value="NE555", nodes=["0", "N1", "N1", "0"]),
            Component(ref="R1", type="resistor", value="1k", nodes=["N1", "0"]),
        ]
    )
    issues = validate_circuit(circuit)
    assert errors(issues) == []
    assert any("cannot be verified" in issue.message for issue in issues)


def test_pin_number_out_of_range() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="NE555",
        pins=_pins((1, "GND", "0"), (9, "VCC", "VCC")),
    )
    tie = Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "0"])
    messages = [
        issue.message
        for issue in errors(validate_circuit(Circuit(components=[u1, tie])))
    ]
    assert any("pin 9 does not exist" in message for message in messages)


def test_duplicate_pin_numbers_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate pin numbers"):
        Component(
            ref="U1",
            type="ic",
            value="NE555",
            pins=_pins((1, "GND", "0"), (1, "VCC", "VCC")),
        )

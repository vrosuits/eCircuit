# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

import pytest

from ecircuit.text2circuit import Circuit, Component, Pin, validate_circuit
from ecircuit.text2circuit.pinouts import canonical_pin_name, lookup_pinout
from ecircuit.text2circuit.validate import errors


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1OUT", "OUT1"),
        ("OUTA", "OUT1"),
        ("OUTB", "OUT2"),
        ("2IN+", "IN2+"),
        ("INB-", "IN2-"),
        ("+IN2", "IN2+"),
        ("IN1-", "IN1-"),
        ("+IN", "IN+"),
        ("-IN", "IN-"),
        ("V+", "VCC"),
        ("VCC+", "VCC"),
        ("VEE", "GND"),
        ("V-", "GND"),
        ("VIN", "IN"),
        ("VOUT", "OUT"),
        ("ADJUST", "ADJ"),
        ("OFFSET NULL", "NULL"),
        ("THRESHOLD", "THRES"),
    ],
)
def test_canonical_pin_name(raw: str, expected: str) -> None:
    assert canonical_pin_name(raw) == expected


def test_lookup_tolerates_voltage_suffix() -> None:
    assert lookup_pinout("AMS1117-3.3") == lookup_pinout("AMS1117")
    assert lookup_pinout("AMS1117-3.3") is not None
    assert lookup_pinout("XYZ9999") is None


def test_78xx_and_79xx_differ() -> None:
    assert lookup_pinout("7805") == ["IN", "GND", "OUT"]
    assert lookup_pinout("7905") == ["GND", "IN", "OUT"]
    assert lookup_pinout("78L05") == ["OUT", "GND", "IN"]


def _pins(*triples: tuple[int, str, str]) -> list[Pin]:
    return [Pin(pin=number, name=name, net=net) for number, name, net in triples]


def _powered(components: list[Component]) -> Circuit:
    return Circuit(
        components=[
            Component(ref="V1", type="voltage_source", value="9", nodes=["VCC", "0"]),
            *components,
        ]
    )


def test_lm358_follower_is_clean() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="LM358",
        pins=_pins(
            (1, "OUT1", "VOUT"),
            (2, "IN1-", "VOUT"),
            (3, "IN1+", "VIN"),
            (4, "V-", "0"),
            (8, "V+", "VCC"),
        ),
    )
    source = Component(ref="V2", type="voltage_source", value="2.5", nodes=["VIN", "0"])
    load = Component(ref="R1", type="resistor", value="10k", nodes=["VOUT", "0"])
    assert validate_circuit(_powered([u1, source, load])) == []


def test_lm358_scrambled_pins_caught() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="LM358",
        pins=_pins(
            (1, "IN1+", "VIN"),  # pin 1 is OUT1
            (2, "IN1-", "VOUT"),
            (3, "OUT1", "VOUT"),  # pin 3 is IN1+
            (4, "GND", "0"),
            (8, "VCC", "VCC"),
        ),
    )
    source = Component(ref="V2", type="voltage_source", value="2.5", nodes=["VIN", "0"])
    load = Component(ref="R1", type="resistor", value="10k", nodes=["VOUT", "0"])
    messages = [
        issue.message
        for issue in errors(validate_circuit(_powered([u1, source, load])))
    ]
    assert any(
        "pin 1 is named IN1+" in message and "OUT1" in message for message in messages
    )
    assert any(
        "pin 3 is named OUT1" in message and "IN1+" in message for message in messages
    )


def test_741_with_aliased_rails_is_clean() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="UA741",
        pins=_pins(
            (2, "-IN", "VOUT"),
            (3, "+IN", "VIN"),
            (4, "V-", "0"),
            (6, "OUTPUT", "VOUT"),
            (7, "V+", "VCC"),
        ),
    )
    source = Component(ref="V2", type="voltage_source", value="1", nodes=["VIN", "0"])
    load = Component(ref="R1", type="resistor", value="10k", nodes=["VOUT", "0"])
    assert validate_circuit(_powered([u1, source, load])) == []


def test_7805_regulator_correct_and_wrong() -> None:
    def reg(pin_names: tuple[str, str, str]) -> Circuit:
        u1 = Component(
            ref="U1",
            type="ic",
            value="7805",
            pins=_pins(
                (1, pin_names[0], "VCC"),
                (2, pin_names[1], "0"),
                (3, pin_names[2], "VOUT"),
            ),
        )
        load = Component(ref="R1", type="resistor", value="1k", nodes=["VOUT", "0"])
        return _powered([u1, load])

    assert validate_circuit(reg(("IN", "GND", "OUT"))) == []
    messages = [
        issue.message for issue in errors(validate_circuit(reg(("GND", "IN", "OUT"))))
    ]
    assert any(
        "pin 1 is named GND" in message and "IN" in message for message in messages
    )


def test_ams1117_accepts_gnd_or_adj_on_pin_1() -> None:
    def ldo(pin1_name: str, pin1_net: str) -> Circuit:
        u1 = Component(
            ref="U1",
            type="ic",
            value="AMS1117-3.3",
            pins=_pins((1, pin1_name, pin1_net), (2, "OUT", "VOUT"), (3, "IN", "VCC")),
        )
        load = Component(ref="R1", type="resistor", value="1k", nodes=["VOUT", "0"])
        extras = []
        if pin1_net != "0":
            extras.append(
                Component(ref="R2", type="resistor", value="1k", nodes=[pin1_net, "0"])
            )
        return _powered([u1, load, *extras])

    assert errors(validate_circuit(ldo("GND", "0"))) == []
    assert errors(validate_circuit(ldo("ADJ", "NADJ"))) == []


def test_opamp_output_shorted_to_rail_caught() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="LM358",
        pins=_pins(
            (1, "OUT1", "VCC"),  # output tied to the positive rail
            (2, "IN1-", "VIN"),
            (3, "IN1+", "VIN"),
            (4, "GND", "0"),
            (8, "VCC", "VCC"),
        ),
    )
    source = Component(ref="V2", type="voltage_source", value="1", nodes=["VIN", "0"])
    messages = [
        issue.message for issue in errors(validate_circuit(_powered([u1, source])))
    ]
    assert any("OUT1 pin is shorted to the VCC rail" in message for message in messages)

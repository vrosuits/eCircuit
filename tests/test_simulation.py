# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

import pytest

from ecircuit.simulation import (
    SimulationError,
    build_deck,
    ngspice_available,
    parse_op_log,
    parse_wrdata,
    simulate_op,
    simulate_tran,
)
from ecircuit.text2circuit import Circuit, Component, Pin

needs_ngspice = pytest.mark.skipif(
    not ngspice_available(), reason="ngspice not installed"
)


def _divider() -> Circuit:
    return Circuit(
        name="divider",
        components=[
            Component(ref="V1", type="voltage_source", value="5", nodes=["VIN", "0"]),
            Component(ref="R1", type="resistor", value="10k", nodes=["VIN", "VOUT"]),
            Component(ref="R2", type="resistor", value="10k", nodes=["VOUT", "0"]),
        ],
    )


def test_deck_basic_cards() -> None:
    deck, warnings = build_deck(_divider(), ["op"])
    assert "V1 VIN 0 5" in deck
    assert "R1 VIN VOUT 10k" in deck
    assert ".control" in deck
    assert ".END" in deck
    assert warnings == []


def test_battery_ref_gets_v_prefix_and_volts_stripped() -> None:
    circuit = Circuit(
        components=[
            Component(ref="BT1", type="battery", value="9V", nodes=["VCC", "0"]),
            Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "0"]),
        ]
    )
    deck, _ = build_deck(circuit, ["op"])
    assert "VBT1 VCC 0 9" in deck


def test_led_and_diode_models() -> None:
    circuit = Circuit(
        components=[
            Component(ref="V1", type="voltage_source", value="5", nodes=["VCC", "0"]),
            Component(ref="D1", type="led", value="red", nodes=["VCC", "N1"]),
            Component(ref="D2", type="diode", value="1N4148", nodes=["N1", "0"]),
        ]
    )
    deck, _ = build_deck(circuit, ["op"])
    assert "D1 VCC N1 DLED" in deck
    assert "D2 N1 0 D1N4148" in deck
    assert ".model DLED" in deck
    assert ".model D1N4148" in deck


def test_transistor_card() -> None:
    circuit = Circuit(
        components=[
            Component(ref="V1", type="voltage_source", value="5", nodes=["VC", "0"]),
            Component(
                ref="Q1", type="npn transistor", value="2N3904", nodes=["VC", "VB", "0"]
            ),
            Component(ref="R1", type="resistor", value="10k", nodes=["VC", "VB"]),
        ]
    )
    deck, _ = build_deck(circuit, ["op"])
    assert "Q1 VC VB 0 Q2N3904" in deck
    assert ".model Q2N3904 NPN" in deck


def test_555_x_card_in_pin_order() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="NE555",
        pins=[
            Pin(pin=1, name="GND", net="0"),
            Pin(pin=2, name="TRIG", net="N2"),
            Pin(pin=3, name="OUT", net="N4"),
            Pin(pin=4, name="RESET", net="VCC"),
            Pin(pin=5, name="CTRL", net="N3"),
            Pin(pin=6, name="THRES", net="N2"),
            Pin(pin=7, name="DISCH", net="N1"),
            Pin(pin=8, name="VCC", net="VCC"),
        ],
    )
    tie = Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "0"])
    deck, _ = build_deck(Circuit(components=[u1, tie]), ["op"])
    assert "XU1 0 N2 N4 VCC N3 N2 N1 VCC NE555" in deck
    assert ".SUBCKT NE555" in deck


def test_unconnected_ic_pins_get_private_nodes() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="LM358",
        pins=[
            Pin(pin=1, name="OUT1", net="VOUT"),
            Pin(pin=2, name="IN1-", net="VOUT"),
            Pin(pin=3, name="IN1+", net="VIN"),
            Pin(pin=4, name="GND", net="0"),
            Pin(pin=8, name="VCC", net="VCC"),
        ],
    )
    tie = Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "VIN"])
    deck, _ = build_deck(Circuit(components=[u1, tie]), ["op"])
    assert "XU1 VOUT VOUT VIN 0 NC_U1_5 NC_U1_6 NC_U1_7 VCC DUAL_OPAMP" in deck


def test_unmodelled_ic_rejected() -> None:
    u1 = Component(
        ref="U1",
        type="ic",
        value="LM324",
        pins=[Pin(pin=4, name="VCC", net="VCC"), Pin(pin=11, name="GND", net="0")],
    )
    tie = Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "0"])
    with pytest.raises(SimulationError, match="no SPICE model"):
        build_deck(Circuit(components=[u1, tie]), ["op"])


def test_connector_open_and_switch_closed() -> None:
    circuit = Circuit(
        components=[
            Component(ref="V1", type="voltage_source", value="5", nodes=["VIN", "0"]),
            Component(ref="J1", type="connector", value="Input", nodes=["VIN", "0"]),
            Component(ref="SW1", type="switch", value="SPST", nodes=["VIN", "N1"]),
            Component(ref="R1", type="resistor", value="1k", nodes=["N1", "0"]),
        ]
    )
    deck, warnings = build_deck(circuit, ["op"])
    assert "J1" not in deck.replace("* ", "")
    assert "RSW1 VIN N1 1" in deck
    assert any("connector" in warning for warning in warnings)
    assert any("switch" in warning for warning in warnings)


def test_parse_op_log() -> None:
    log = """\
Note: Starting dynamic gmin stepping
vin = 5.000000e+00
vout = 2.500000e+00
v1#branch = -2.50000e-04
"""
    values = parse_op_log(log)
    assert values == {"vin": 5.0, "vout": 2.5}


def test_parse_wrdata() -> None:
    text = """\
time v(vin) v(vout)
0.0 0.0 0.0
1e-3 5.0 2.5
2e-3 5.0 2.5
"""
    time, traces = parse_wrdata(text, ["VIN", "VOUT"])
    assert time == [0.0, 1e-3, 2e-3]
    assert traces["VOUT"] == [0.0, 2.5, 2.5]


@needs_ngspice
def test_op_divider_live() -> None:
    voltages, warnings = simulate_op(_divider())
    assert warnings == []
    assert voltages["VOUT"] == pytest.approx(2.5, abs=1e-3)
    assert voltages["VIN"] == pytest.approx(5.0, abs=1e-3)


@needs_ngspice
def test_tran_rc_charge_live() -> None:
    circuit = Circuit(
        name="rc",
        components=[
            Component(ref="V1", type="voltage_source", value="5", nodes=["VIN", "0"]),
            Component(ref="R1", type="resistor", value="1k", nodes=["VIN", "VOUT"]),
            Component(ref="C1", type="capacitor", value="1u", nodes=["VOUT", "0"]),
        ],
    )
    result = simulate_tran(circuit, "10u", "10m", uic=True)
    final = result.traces["VOUT"][-1]
    assert final == pytest.approx(5.0, abs=0.05)
    # starts discharged, ends charged
    assert result.traces["VOUT"][0] < 0.5


@needs_ngspice
def test_555_blinker_oscillates_live() -> None:
    """Regression: the behavioral NE555 must oscillate (discharge polarity)."""
    blinker = Circuit(
        name="blinker",
        components=[
            Component(ref="BT1", type="battery", value="9V", nodes=["VCC", "0"]),
            Component(ref="R1", type="resistor", value="1k", nodes=["VCC", "N1"]),
            Component(ref="R2", type="resistor", value="10k", nodes=["N1", "N2"]),
            Component(ref="C1", type="capacitor", value="10u", nodes=["N2", "0"]),
            Component(ref="R3", type="resistor", value="330", nodes=["N4", "N5"]),
            Component(ref="D1", type="led", value="red", nodes=["N5", "0"]),
            Component(
                ref="U1",
                type="ic",
                value="NE555",
                pins=[
                    Pin(pin=1, name="GND", net="0"),
                    Pin(pin=2, name="TRIG", net="N2"),
                    Pin(pin=3, name="OUT", net="N4"),
                    Pin(pin=4, name="RESET", net="VCC"),
                    Pin(pin=6, name="THRES", net="N2"),
                    Pin(pin=7, name="DISCH", net="N1"),
                    Pin(pin=8, name="VCC", net="VCC"),
                ],
            ),
        ],
    )
    # 10u cap -> ~6.9 Hz, so 1 second captures several cycles
    result = simulate_tran(blinker, "1m", "1", uic=True)
    out = result.traces["N4"]
    assert min(out) < 1.0  # output goes low
    assert max(out) > 7.0  # and high
    # it must actually toggle repeatedly, not just once
    crossings = sum(1 for a, b in zip(out, out[1:]) if (a < 4.5) != (b < 4.5))
    assert crossings >= 6

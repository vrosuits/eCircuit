# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""SPICE model library: device models and behavioral IC subcircuits."""

from __future__ import annotations

# --- diode models -----------------------------------------------------------

DIODE_MODELS = {
    "D1N4148": ".model D1N4148 D(IS=2.52n RS=0.568 N=1.752 CJO=4p TT=20n BV=100 IBV=0.1u)",
    "D1N4007": ".model D1N4007 D(IS=7.02u RS=0.0341 N=1.8 CJO=18p TT=5u BV=1000 IBV=5u)",
    # N=2 with tiny IS gives the ~2V forward drop of a typical LED
    "DLED": ".model DLED D(IS=1e-20 N=2.0 RS=1)",
    "DGEN": ".model DGEN D(IS=1e-14 N=1.0 RS=0.5)",
}

# --- BJT models --------------------------------------------------------------

BJT_MODELS = {
    "Q2N3904": (
        ".model Q2N3904 NPN(IS=6.734f XTI=3 EG=1.11 VAF=74.03 BF=416.4 NE=1.259"
        " ISE=6.734f IKF=66.78m XTB=1.5 BR=.7371 NC=2 RC=1 CJC=3.638p MJC=.3085"
        " VJC=.75 FC=.5 CJE=4.493p MJE=.2593 VJE=.75 TR=239.5n TF=301.2p ITF=.4"
        " VTF=4 XTF=2 RB=10)"
    ),
    "Q2N2222": (
        ".model Q2N2222 NPN(IS=14.34f XTI=3 EG=1.11 VAF=74.03 BF=255.9 NE=1.307"
        " ISE=14.34f IKF=.2847 XTB=1.5 BR=6.092 NC=2 RC=1 CJC=7.306p MJC=.3416"
        " VJC=.75 FC=.5 CJE=22.01p MJE=.377 VJE=.75 TR=46.91n TF=411.1p ITF=.6"
        " VTF=1.7 XTF=3 RB=10)"
    ),
    "Q2N3906": (
        ".model Q2N3906 PNP(IS=1.41f XTI=3 EG=1.11 VAF=18.7 BF=180.7 NE=1.5"
        " ISE=0 IKF=80m XTB=1.5 BR=4.977 NC=2 RC=2.5 CJC=9.728p MJC=.5776"
        " VJC=.75 FC=.5 CJE=8.063p MJE=.3677 VJE=.75 TR=33.42n TF=179.3p ITF=.4"
        " VTF=4 XTF=6 RB=10)"
    ),
    "QNPN": ".model QNPN NPN(IS=1e-14 BF=100)",
    "QPNP": ".model QPNP PNP(IS=1e-14 BF=100)",
}

# --- behavioral IC subcircuits ------------------------------------------------
# Port order matches the datasheet pin order used by the pinout registry, so an
# X card can list nets by pin number 1..N directly.

NE555_SUBCKT = """\
* Behavioral NE555: comparators + latch + discharge switch.
* Ports in datasheet pin order.
.SUBCKT NE555 GND TRIG OUT RESET CTRL THRES DISCH VCC
* internal reference divider (drives the CTRL pin like the real part)
RD1 VCC CTRL 5k
RD2 CTRL REFLO 5k
RD3 REFLO GND 5k
* comparators: set when TRIG < VCC/3, reset when THRES > 2VCC/3 or RESET low
BSET SETS GND V = V(TRIG,GND) < V(REFLO,GND) ? 1 : 0
BRST RSTS GND V = V(THRES,GND) > V(CTRL,GND) ? 1 : (V(RESET,GND) < 0.7 ? 1 : 0)
* SR latch with a small RC for state memory
BQ QN GND V = V(SETS) > 0.5 ? 1 : (V(RSTS) > 0.5 ? 0 : (V(Q) > 0.5 ? 1 : 0))
RQ QN Q 1k
CQ Q GND 10n
* push-pull output stage
BOUTV OUTI GND V = V(Q) > 0.5 ? V(VCC,GND) - 0.5 : 0.1
ROUT OUTI OUT 30
* open-collector discharge transistor: conducts when the latch is LOW
BQBAR QBAR GND V = 1 - V(Q)
SDIS DISCH GND QBAR GND SW555
.MODEL SW555 SW(VT=0.5 VH=0.2 RON=20 ROFF=1G)
.ENDS NE555
"""

DUAL_OPAMP_SUBCKT = """\
* Behavioral dual op-amp (LM358-class): high gain, rail-limited output.
* Ports in datasheet pin order: OUT1 IN1- IN1+ GND IN2+ IN2- OUT2 VCC
.SUBCKT DUAL_OPAMP OUT1 IN1- IN1+ GND IN2+ IN2- OUT2 VCC
BR1 RAW1 GND V = (V(IN1+,GND) - V(IN1-,GND)) * 1e5
BC1 CL1 GND V = V(RAW1) > V(VCC,GND) - 1.2 ? V(VCC,GND) - 1.2 : (V(RAW1) < 0.02 ? 0.02 : V(RAW1))
RO1 CL1 OUT1 50
BR2 RAW2 GND V = (V(IN2+,GND) - V(IN2-,GND)) * 1e5
BC2 CL2 GND V = V(RAW2) > V(VCC,GND) - 1.2 ? V(VCC,GND) - 1.2 : (V(RAW2) < 0.02 ? 0.02 : V(RAW2))
RO2 CL2 OUT2 50
.ENDS DUAL_OPAMP
"""

# Device value (as produced by Text2Circuit) -> (subcircuit name, subcircuit text).
_555_FAMILY = (
    "555",
    "NE555",
    "NE555P",
    "LM555",
    "NA555",
    "SA555",
    "SE555",
    "TLC555",
    "ICM7555",
)
_DUAL_OPAMP_FAMILY = (
    "LM358",
    "LM833",
    "LM4562",
    "TL072",
    "TL082",
    "NE5532",
    "RC4558",
    "MC1458",
    "LF353",
)

SUBCKT_BY_DEVICE: dict[str, tuple[str, str]] = {}
for _device in _555_FAMILY:
    SUBCKT_BY_DEVICE[_device] = ("NE555", NE555_SUBCKT)
for _device in _DUAL_OPAMP_FAMILY:
    SUBCKT_BY_DEVICE[_device] = ("DUAL_OPAMP", DUAL_OPAMP_SUBCKT)


def subckt_for_device(device: str) -> tuple[str, str] | None:
    """(subcircuit name, definition) for a device value, or None if unmodelled."""
    key = device.strip().upper()
    if key in SUBCKT_BY_DEVICE:
        return SUBCKT_BY_DEVICE[key]
    return SUBCKT_BY_DEVICE.get(key.split("-")[0])


def diode_model_for(value: str, kind: str) -> str:
    """Model name for a diode/LED; LEDs get the 2V-drop model, else by part."""
    key = value.strip().upper()
    if key in {"1N4148", "D1N4148"}:
        return "D1N4148"
    if key in {"1N4007", "D1N4007"}:
        return "D1N4007"
    if "LED" in kind.upper():
        return "DLED"
    return "DGEN"


def bjt_model_for(value: str, kind: str) -> str:
    """Model name for a transistor value; falls back to a generic NPN/PNP."""
    key = value.strip().upper()
    name = f"Q{key}"
    if name in BJT_MODELS:
        return name
    return "QPNP" if "PNP" in kind.upper() else "QNPN"

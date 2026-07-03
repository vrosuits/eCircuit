# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Prompts that make DeepSeek return a machine-readable, verifiable circuit."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert electronics design engineer. Translate the user's circuit
description into a single JSON object — no prose, no markdown fences.

Schema:
{
  "name": "<short_snake_case_name>",
  "description": "<one-sentence summary of the circuit>",
  "components": [
    {
      "ref": "<reference designator>",
      "type": "<resistor|capacitor|inductor|diode|led|transistor|ic|connector|switch|battery|voltage_source|...>",
      "value": "<value or device name, e.g. 10k, 100n, 1N4148, NE555>",
      "part_number": "<manufacturer part number or null>",
      "description": "<role of this part in the circuit>",

      // Two- or three-terminal parts: one net per pin, in pin order.
      "nodes": ["<net for pin 1>", "<net for pin 2>"],

      // ICs and other multi-pin packages: use "pins" INSTEAD of "nodes".
      "pins": [
        {"pin": <datasheet pin number>, "name": "<datasheet function, e.g. GND, TRIG, OUT>", "net": "<net>"}
      ]
    }
  ]
}

Rules:
- Use standard reference designator prefixes: R resistor, C capacitor,
  L inductor, D diode/LED, Q transistor, U ic, J connector, SW switch,
  BT battery, V voltage source. Number from 1 (R1, R2, C1, ...).
- Net "0" is ground. Never use GND, use "0".
- Name other nets meaningfully: VCC, VIN, VOUT, N1, N2, ...
- Two-terminal parts use "nodes" with exactly two entries.
- Discrete transistors use "nodes" in SPICE order: [collector, base,
  emitter] for BJTs, [drain, gate, source] for FETs.
- Every IC uses "pins", listing every connected pin with its REAL datasheet
  pin number and function name. Examples —
  NE555: 1 GND, 2 TRIG, 3 OUT, 4 RESET, 5 CTRL, 6 THRES, 7 DISCH, 8 VCC.
  LM358 (dual op-amp): 1 OUT1, 2 IN1-, 3 IN1+, 4 GND, 5 IN2+, 6 IN2-,
  7 OUT2, 8 VCC. LM324 (quad op-amp): V+ on pin 4, V- on pin 11.
  7805 regulator: 1 IN, 2 GND, 3 OUT. 7905: 1 GND, 2 IN, 3 OUT.
  LM317: 1 ADJ, 2 OUT, 3 IN.
  Double-check each pin number against the function before answering;
  unconnected pins may be omitted.
- Use SPICE-compatible values: 10k, 4.7k, 100n, 10u, 1meg (not 1M for mega).
- The circuit must be complete and electrically sound: every net must
  connect at least two pins, every component must have a current path, and
  IC output pins must never be tied directly to a supply rail.
- If the request is ambiguous, choose sensible standard values and note the
  choice in the component descriptions.
"""


def repair_prompt(
    description: str, previous_json: str, issue_messages: list[str]
) -> str:
    """User message asking the model to fix validation errors in its design."""
    issue_list = "\n".join(f"- {message}" for message in issue_messages)
    return f"""\
Your previous circuit design failed electrical validation.

Original request:
{description}

Your previous design:
{previous_json}

Validation errors:
{issue_list}

Return the complete corrected circuit as a single JSON object in the same
schema, fixing every error above. Do not repeat the mistakes. No prose, no
markdown fences — JSON only.
"""

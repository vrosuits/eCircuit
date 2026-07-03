# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Text description -> validated Circuit, via the DeepSeek API."""

from __future__ import annotations

import re

from pydantic import ValidationError

from .client import DeepSeekClient
from .models import Circuit
from .prompts import SYSTEM_PROMPT

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$")


class CircuitParseError(ValueError):
    """The AI response could not be parsed into a valid Circuit."""


def parse_circuit_response(raw: str) -> Circuit:
    """Parse the model's JSON reply, tolerating stray markdown fences."""
    text = _FENCE.sub("", raw.strip())
    try:
        return Circuit.model_validate_json(text)
    except ValidationError as exc:
        raise CircuitParseError(f"AI returned an invalid circuit: {exc}") from exc


def generate_circuit(description: str, client: DeepSeekClient | None = None) -> Circuit:
    """Turn a plain-text circuit description into a validated Circuit."""
    if not description.strip():
        raise ValueError("circuit description is empty")
    client = client or DeepSeekClient()
    raw = client.chat(SYSTEM_PROMPT, description)
    return parse_circuit_response(raw)

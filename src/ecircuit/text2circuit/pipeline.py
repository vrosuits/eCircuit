# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Text description -> validated Circuit, via the DeepSeek API.

Generation runs the AI's design through electrical validation; if errors are
found, they are sent back to the model for repair before the circuit is
accepted.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ValidationError

from .client import DeepSeekClient
from .models import Circuit
from .prompts import SYSTEM_PROMPT, repair_prompt
from .validate import Issue, errors, validate_circuit

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$")


class CircuitParseError(ValueError):
    """The AI response could not be parsed into a valid Circuit."""


class CircuitValidationError(ValueError):
    """The AI design still failed electrical validation after repair."""

    def __init__(self, issues: list[Issue]) -> None:
        self.issues = issues
        details = "; ".join(issue.message for issue in errors(issues))
        super().__init__(f"circuit failed electrical validation: {details}")


class GenerationResult(BaseModel):
    """A validated circuit plus any non-fatal warnings and repair history."""

    circuit: Circuit
    warnings: list[Issue] = []
    repair_rounds: int = 0


def parse_circuit_response(raw: str) -> Circuit:
    """Parse the model's JSON reply, tolerating stray markdown fences."""
    text = _FENCE.sub("", raw.strip())
    try:
        return Circuit.model_validate_json(text)
    except ValidationError as exc:
        raise CircuitParseError(f"AI returned an invalid circuit: {exc}") from exc


def generate(
    description: str,
    client: DeepSeekClient | None = None,
    max_repair_rounds: int = 1,
) -> GenerationResult:
    """Generate, validate, and if needed repair a circuit from a description."""
    if not description.strip():
        raise ValueError("circuit description is empty")
    client = client or DeepSeekClient()

    raw = client.chat(SYSTEM_PROMPT, description)
    circuit = parse_circuit_response(raw)
    issues = validate_circuit(circuit)

    rounds = 0
    while errors(issues) and rounds < max_repair_rounds:
        messages = [issue.message for issue in errors(issues)]
        raw = client.chat(SYSTEM_PROMPT, repair_prompt(description, raw, messages))
        circuit = parse_circuit_response(raw)
        issues = validate_circuit(circuit)
        rounds += 1

    if errors(issues):
        raise CircuitValidationError(issues)
    return GenerationResult(
        circuit=circuit,
        warnings=[issue for issue in issues if issue.severity == "warning"],
        repair_rounds=rounds,
    )


def generate_circuit(description: str, client: DeepSeekClient | None = None) -> Circuit:
    """Turn a plain-text circuit description into a validated Circuit."""
    return generate(description, client=client).circuit

# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

import json

import httpx
import pytest

from ecircuit.text2circuit import (
    CircuitValidationError,
    DeepSeekClient,
    DeepSeekError,
    generate,
    generate_circuit,
)

VALID_CIRCUIT_JSON = json.dumps(
    {
        "name": "rc_filter",
        "description": "1kHz RC low-pass filter",
        "components": [
            {
                "ref": "V1",
                "type": "voltage_source",
                "value": "AC 1",
                "nodes": ["VIN", "0"],
            },
            {
                "ref": "R1",
                "type": "resistor",
                "value": "1.6k",
                "nodes": ["VIN", "VOUT"],
            },
            {"ref": "C1", "type": "capacitor", "value": "100n", "nodes": ["VOUT", "0"]},
        ],
    }
)

# Net DANGLE connects only one pin — the validator must reject this.
BROKEN_CIRCUIT_JSON = json.dumps(
    {
        "name": "broken",
        "components": [
            {
                "ref": "R1",
                "type": "resistor",
                "value": "1k",
                "nodes": ["VIN", "DANGLE"],
            },
            {
                "ref": "V1",
                "type": "voltage_source",
                "value": "5",
                "nodes": ["VIN", "0"],
            },
            {"ref": "R2", "type": "resistor", "value": "1k", "nodes": ["VIN", "0"]},
        ],
    }
)


def _response(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def _mock_client(handler) -> DeepSeekClient:
    return DeepSeekClient(api_key="test-key", transport=httpx.MockTransport(handler))


def test_generate_circuit_end_to_end() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "deepseek-chat"
        assert body["response_format"] == {"type": "json_object"}
        return _response(VALID_CIRCUIT_JSON)

    result = generate("a 1kHz RC low-pass filter", client=_mock_client(handler))
    assert result.circuit.name == "rc_filter"
    assert result.circuit.nets == ["0", "VIN", "VOUT"]
    assert result.repair_rounds == 0
    assert result.warnings == []


def test_validation_errors_trigger_repair() -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return _response(BROKEN_CIRCUIT_JSON)
        return _response(VALID_CIRCUIT_JSON)

    result = generate("a filter", client=_mock_client(handler))
    assert result.repair_rounds == 1
    assert result.circuit.name == "rc_filter"
    assert len(requests) == 2
    repair_message = requests[1]["messages"][1]["content"]
    assert "failed electrical validation" in repair_message
    assert "net DANGLE connects only one pin" in repair_message


def test_unrepairable_circuit_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _response(BROKEN_CIRCUIT_JSON)

    with pytest.raises(CircuitValidationError, match="DANGLE"):
        generate("a filter", client=_mock_client(handler), max_repair_rounds=1)


def test_generate_circuit_wrapper_returns_circuit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _response(VALID_CIRCUIT_JSON)

    circuit = generate_circuit("a filter", client=_mock_client(handler))
    assert circuit.name == "rc_filter"


def test_api_error_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="invalid api key")

    with pytest.raises(DeepSeekError, match="401"):
        generate("anything", client=_mock_client(handler))


def test_empty_description_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        generate("   ")


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(DeepSeekError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient()

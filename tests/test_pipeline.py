# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

import json

import httpx
import pytest

from ecircuit.text2circuit import DeepSeekClient, DeepSeekError, generate_circuit

CIRCUIT_JSON = json.dumps(
    {
        "name": "rc_filter",
        "description": "1kHz RC low-pass filter",
        "components": [
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


def _mock_client(handler: httpx.MockTransport) -> DeepSeekClient:
    return DeepSeekClient(api_key="test-key", transport=handler)


def test_generate_circuit_end_to_end() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "deepseek-chat"
        assert body["response_format"] == {"type": "json_object"}
        return httpx.Response(
            200, json={"choices": [{"message": {"content": CIRCUIT_JSON}}]}
        )

    circuit = generate_circuit(
        "a 1kHz RC low-pass filter", client=_mock_client(httpx.MockTransport(handler))
    )
    assert circuit.name == "rc_filter"
    assert circuit.nets == ["0", "VIN", "VOUT"]


def test_api_error_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="invalid api key")

    with pytest.raises(DeepSeekError, match="401"):
        generate_circuit("anything", client=_mock_client(httpx.MockTransport(handler)))


def test_empty_description_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        generate_circuit("   ")


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(DeepSeekError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient()

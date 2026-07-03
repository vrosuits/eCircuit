# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Minimal DeepSeek chat-completions client (OpenAI-compatible API)."""

from __future__ import annotations

import os

import httpx

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
API_KEY_ENV = "DEEPSEEK_API_KEY"


class DeepSeekError(RuntimeError):
    """The DeepSeek API could not be reached or returned an error."""


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get(API_KEY_ENV)
        if not self.api_key:
            raise DeepSeekError(
                f"no DeepSeek API key: set the {API_KEY_ENV} environment variable "
                "or pass api_key explicitly"
            )
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._transport = transport

    def chat(self, system: str, user: str, temperature: float = 0.1) -> str:
        """Send one system+user exchange, return the assistant's text."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(
                timeout=self.timeout, transport=self._transport
            ) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            raise DeepSeekError(
                f"DeepSeek API error {exc.response.status_code}: {exc.response.text[:500]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise DeepSeekError(f"could not reach DeepSeek API: {exc}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise DeepSeekError(
                f"unexpected DeepSeek response shape: {data!r:.500}"
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise DeepSeekError("DeepSeek returned an empty response")
        return content

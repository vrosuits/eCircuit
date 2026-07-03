# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

from pathlib import Path

import pytest

from ecircuit import cli
from ecircuit.text2circuit import Circuit, Component, GenerationResult
from ecircuit.text2circuit.validate import Issue


@pytest.fixture
def fake_circuit(monkeypatch: pytest.MonkeyPatch) -> Circuit:
    circuit = Circuit(
        name="blinker",
        components=[
            Component(ref="R1", type="resistor", value="330", nodes=["VCC", "N1"]),
            Component(ref="D1", type="led", value="red", nodes=["N1", "0"]),
        ],
    )
    result = GenerationResult(
        circuit=circuit,
        warnings=[Issue(severity="warning", message="something to double-check")],
        repair_rounds=1,
    )
    monkeypatch.setattr(cli, "generate", lambda description: result)
    return circuit


def test_cli_prints_netlist_and_bom(
    fake_circuit: Circuit, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["text2circuit", "an led blinker"]) == 0
    captured = capsys.readouterr()
    assert "R1 VCC N1 330" in captured.out
    assert "| 1 | led | red |" in captured.out
    assert "repaired in 1 round(s)" in captured.err
    assert "warning: something to double-check" in captured.err


def test_cli_writes_files(fake_circuit: Circuit, tmp_path: Path) -> None:
    assert cli.main(["text2circuit", "an led blinker", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "blinker.cir").read_text().startswith("* blinker\n")
    assert (tmp_path / "blinker_bom.csv").exists()
    assert (tmp_path / "blinker_bom.md").exists()
    assert (tmp_path / "blinker.json").exists()


def test_cli_reports_missing_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert cli.main(["text2circuit", "an led blinker"]) == 2
    assert "DEEPSEEK_API_KEY" in capsys.readouterr().err

# CLAUDE.md

(c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Copyright headers

Every new source file must start with:

```
# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.
```

The project is proprietary (free personal use, paid commercial tiers) — see `LICENCE.md`. Do not add open-source licence boilerplate.

## Project

eCircuit ("Electronic Design Package") is an AI-powered electronic circuit design toolkit. It is currently **greenfield** — only `README.md` exists. See the README for the full vision.

Planned modules: Text2Circuit (text → schematic/BOM/netlist), Text2PCB (AI-assisted autorouting), graphical rendering of circuits and netlists, and integrated SPICE/PSPICE simulation with virtual instruments.

## Hard constraints

- **AI backend:** DeepSeek API powers the text2bom / text2netlist / text2circuit / text2pcb / text2spice features. Do not substitute another provider without asking.
- **Memory budget:** local ("narrow AI") tools must run within **2 GB RAM**.
- **Standards:** schematic and silkscreen rendering must be IEEE-compliant.

## Stack and commands

Python 3.12, managed with **uv** (src layout, package `ecircuit`, subpackages `text2circuit` / `text2pcb` / `rendering` / `simulation`).

- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Run CLI: `uv run ecircuit` (e.g. `uv run ecircuit text2circuit "an RC low-pass filter" -o out/`; `uv run ecircuit render out/<name>.json [--ascii]` draws a text schematic)
- `DEEPSEEK_API_KEY` must be set for AI features (Text2Circuit); put it in `.env` (gitignored), never in code. Tests mock the API and need no key.

Still undecided: GUI framework and SPICE engine (e.g., ngspice via PySpice vs. alternatives). Confirm with the user before committing to one.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs pytest, `ruff check`, and `ruff format --check` on every push/PR to main. Run all three locally before pushing. It installs with `uv sync --locked`, so commit `uv.lock` changes whenever dependencies change.

## Git

Remote: `git@github.com:vrosuits/eCircuit.git` (public). The SSH key is passphrase-protected and served by an agent at `~/.ssh/agent.sock` (see `IdentityAgent` in `~/.ssh/config`). If pushes fail with `publickey` after a reboot, restart the agent and have the user re-enter the passphrase in a GUI terminal window.

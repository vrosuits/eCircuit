# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

eCircuit ("Electronic Design Package") is an AI-powered electronic circuit design toolkit. It is currently **greenfield** — only `README.md` exists. See the README for the full vision.

Planned modules: Text2Circuit (text → schematic/BOM/netlist), Text2PCB (AI-assisted autorouting), graphical rendering of circuits and netlists, and integrated SPICE/PSPICE simulation with virtual instruments.

## Hard constraints

- **AI backend:** DeepSeek API powers the text2bom / text2netlist / text2circuit / text2pcb / text2spice features. Do not substitute another provider without asking.
- **Memory budget:** local ("narrow AI") tools must run within **2 GB RAM**.
- **Standards:** schematic and silkscreen rendering must be IEEE-compliant.

## Current status — read before scaffolding

- **Language: Python.** Still undecided: package manager/build tooling, GUI framework, and SPICE engine (e.g., ngspice via PySpice vs. alternatives). Confirm these with the user before scaffolding code; then record the decisions in this file.
- The GitHub link in the README (`vrosuits/eCircuit`) is a placeholder — no remote is configured yet.
- There is no build, test, lint, or format tooling yet. Update this file with the exact commands once they exist.

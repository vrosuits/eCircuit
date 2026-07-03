# (c) Copyright 2026 by Antony J Ingram of UNIVERSAL I.T SYSTEMS. All rights reserved.
# Licensed under the eCircuit Licence — see LICENCE.md.

"""Drawing primitives: a sparse character canvas and line-drawing charsets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Charset:
    """Line-drawing characters for one rendering style."""

    h: str  # horizontal wire
    v: str  # vertical wire
    tee_down: str  # wire attaches to a rail from below
    tee_up: str  # wire attaches to a rail from above
    cross: str  # wires cross without connecting
    tl: str  # box corners
    tr: str
    bl: str
    br: str


UNICODE = Charset(
    h="─", v="│", tee_down="┬", tee_up="┴", cross="┼", tl="┌", tr="┐", bl="└", br="┘"
)
ASCII = Charset(
    h="-", v="|", tee_down="+", tee_up="+", cross="|", tl="+", tr="+", bl="+", br="+"
)

CHARSETS = {"unicode": UNICODE, "ascii": ASCII}


class Canvas:
    """A sparse 2D character grid that renders to text."""

    def __init__(self) -> None:
        self._cells: dict[tuple[int, int], str] = {}

    def put(self, row: int, col: int, char: str) -> None:
        self._cells[(row, col)] = char

    def get(self, row: int, col: int) -> str:
        return self._cells.get((row, col), " ")

    def text(self, row: int, col: int, string: str) -> None:
        for offset, char in enumerate(string):
            self.put(row, col + offset, char)

    def render(self) -> str:
        if not self._cells:
            return ""
        max_row = max(row for row, _ in self._cells)
        lines = []
        for row in range(max_row + 1):
            cols = [col for (r, col) in self._cells if r == row]
            if not cols:
                lines.append("")
                continue
            line = "".join(self.get(row, col) for col in range(max(cols) + 1))
            lines.append(line.rstrip())
        return "\n".join(lines)

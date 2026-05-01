from __future__ import annotations

from dataclasses import dataclass, field


VALID_ORIENTATIONS = ("north", "south", "east", "west")
VALID_PIN_DIRECTIONS = ("input", "output")
VALID_PIN_SIDES = ("north", "south", "east", "west", "top", "bottom")


@dataclass(frozen=True)
class CellLibraryPin:
    name: str
    direction: str
    anchor: tuple[int, int, int]
    side: str


@dataclass(frozen=True)
class CellLibraryCell:
    name: str
    kind: str
    size: tuple[int, int, int]
    pins: tuple[CellLibraryPin, ...]
    orientations: tuple[str, ...]
    delay_ticks: int
    max_wire_without_repeater: int
    notes: str | None = None
    tags: tuple[str, ...] = ()

    def pin(self, name: str) -> CellLibraryPin | None:
        for pin in self.pins:
            if pin.name == name:
                return pin
        return None


@dataclass(frozen=True)
class CellLibrary:
    name: str
    version: str
    cells: tuple[CellLibraryCell, ...]
    source_path: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def get_cell(self, kind: str) -> CellLibraryCell | None:
        for cell in self.cells:
            if cell.kind == kind:
                return cell
        return None

    def kinds(self) -> tuple[str, ...]:
        return tuple(cell.kind for cell in self.cells)

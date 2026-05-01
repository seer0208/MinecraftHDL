from __future__ import annotations

from dataclasses import dataclass, field


NetBit = int | str


@dataclass(frozen=True)
class Port:
    name: str
    direction: str
    bits: tuple[NetBit, ...]

    @property
    def width(self) -> int:
        return len(self.bits)


@dataclass(frozen=True)
class CellPort:
    name: str
    direction: str
    bits: tuple[NetBit, ...]


@dataclass(frozen=True)
class Cell:
    name: str
    raw_type: str
    kind: str
    ports: tuple[CellPort, ...]
    attributes: dict[str, object] = field(default_factory=dict)
    parameters: dict[str, object] = field(default_factory=dict)

    def input_ports(self) -> tuple[CellPort, ...]:
        return tuple(port for port in self.ports if port.direction == "input")

    def output_ports(self) -> tuple[CellPort, ...]:
        return tuple(port for port in self.ports if port.direction == "output")


@dataclass(frozen=True)
class Module:
    name: str
    ports: tuple[Port, ...]
    cells: tuple[Cell, ...]
    netnames: dict[str, tuple[NetBit, ...]] = field(default_factory=dict)

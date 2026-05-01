from __future__ import annotations

from dataclasses import dataclass

from mhdlc.ir.netlist import NetBit


@dataclass(frozen=True)
class RedstonePinRef:
    instance: str
    pin: str


@dataclass(frozen=True)
class RedstoneCellInstance:
    name: str
    library_cell: str
    kind: str
    source_logical_module: str
    source_logical_cell: str | None
    source_port: str | None
    size: tuple[int, int, int]
    delay_ticks: int
    max_wire_without_repeater: int


@dataclass(frozen=True)
class RedstoneNet:
    name: str
    logical_bit: NetBit | None
    aliases: tuple[str, ...]
    driver: RedstonePinRef
    sinks: tuple[RedstonePinRef, ...]
    constant_value: int | None = None


@dataclass(frozen=True)
class RedstoneModule:
    name: str
    source_logical_module: str
    instances: tuple[RedstoneCellInstance, ...]
    nets: tuple[RedstoneNet, ...]


@dataclass(frozen=True)
class RedstoneDesign:
    library_name: str
    library_version: str
    modules: dict[str, RedstoneModule]
    source_creator: str | None = None

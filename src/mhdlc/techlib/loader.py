from __future__ import annotations

from pathlib import Path

import yaml

from mhdlc.techlib.models import (
    VALID_ORIENTATIONS,
    VALID_PIN_DIRECTIONS,
    VALID_PIN_SIDES,
    CellLibrary,
    CellLibraryCell,
    CellLibraryPin,
)


REQUIRED_PINS_BY_KIND: dict[str, set[str]] = {
    "AND": {"A", "B", "Y"},
    "OR": {"A", "B", "Y"},
    "XOR": {"A", "B", "Y"},
    "INV": {"A", "Y"},
    "MUX": {"A", "B", "S", "Y"},
    "INPUT": {"OUT"},
    "OUTPUT": {"IN"},
    "CONST0": {"OUT"},
    "CONST1": {"OUT"},
}

VALID_KINDS = tuple(REQUIRED_PINS_BY_KIND.keys())
REQUIRED_PIN_DIRECTIONS_BY_KIND: dict[str, dict[str, str]] = {
    "AND": {"A": "input", "B": "input", "Y": "output"},
    "OR": {"A": "input", "B": "input", "Y": "output"},
    "XOR": {"A": "input", "B": "input", "Y": "output"},
    "INV": {"A": "input", "Y": "output"},
    "MUX": {"A": "input", "B": "input", "S": "input", "Y": "output"},
    "INPUT": {"OUT": "output"},
    "OUTPUT": {"IN": "input"},
    "CONST0": {"OUT": "output"},
    "CONST1": {"OUT": "output"},
}


class CellLibraryError(ValueError):
    pass


def _require_mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CellLibraryError(f"{path} must be a mapping")
    return value


def _require_list(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise CellLibraryError(f"{path} must be a list")
    return value


def _require_str(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise CellLibraryError(f"{path} must be a non-empty string")
    return value


def _require_int(value: object, path: str) -> int:
    if not isinstance(value, int):
        raise CellLibraryError(f"{path} must be an integer")
    return value


def _parse_pin(raw_pin: object, path: str) -> CellLibraryPin:
    pin = _require_mapping(raw_pin, path)
    name = _require_str(pin.get("name"), f"{path}.name")
    direction = _require_str(pin.get("direction"), f"{path}.direction").lower()
    if direction not in VALID_PIN_DIRECTIONS:
        raise CellLibraryError(
            f"{path}.direction must be one of {', '.join(VALID_PIN_DIRECTIONS)}"
        )

    anchor_list = _require_list(pin.get("anchor"), f"{path}.anchor")
    if len(anchor_list) != 3:
        raise CellLibraryError(f"{path}.anchor must have exactly 3 coordinates")
    anchor = tuple(
        _require_int(value, f"{path}.anchor[{index}]")
        for index, value in enumerate(anchor_list)
    )

    side = _require_str(pin.get("side"), f"{path}.side").lower()
    if side not in VALID_PIN_SIDES:
        raise CellLibraryError(f"{path}.side must be one of {', '.join(VALID_PIN_SIDES)}")

    return CellLibraryPin(name=name, direction=direction, anchor=anchor, side=side)


def _validate_pin_within_size(pin: CellLibraryPin, size: tuple[int, int, int], path: str) -> None:
    x, y, z = pin.anchor
    sx, sy, sz = size
    if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
        raise CellLibraryError(
            f"{path}.anchor {pin.anchor!r} lies outside declared size {size!r}"
        )


def _parse_cell(raw_cell: object, path: str) -> CellLibraryCell:
    cell = _require_mapping(raw_cell, path)
    name = _require_str(cell.get("name"), f"{path}.name")
    kind = _require_str(cell.get("kind"), f"{path}.kind")
    if kind not in VALID_KINDS:
        raise CellLibraryError(f"{path}.kind must be one of {', '.join(VALID_KINDS)}")

    size_list = _require_list(cell.get("size"), f"{path}.size")
    if len(size_list) != 3:
        raise CellLibraryError(f"{path}.size must contain exactly 3 integers")
    size = tuple(
        _require_int(value, f"{path}.size[{index}]")
        for index, value in enumerate(size_list)
    )
    if any(axis <= 0 for axis in size):
        raise CellLibraryError(f"{path}.size values must all be > 0")

    pins_list = _require_list(cell.get("pins"), f"{path}.pins")
    pins = tuple(
        _parse_pin(raw_pin, f"{path}.pins[{index}]")
        for index, raw_pin in enumerate(pins_list)
    )
    for index, pin in enumerate(pins):
        _validate_pin_within_size(pin, size, f"{path}.pins[{index}]")

    required_pins = REQUIRED_PINS_BY_KIND[kind]
    declared_pins = {pin.name for pin in pins}
    missing = sorted(required_pins - declared_pins)
    if missing:
        raise CellLibraryError(f"{path}.pins missing required pin(s): {', '.join(missing)}")

    declared_pin_map = {pin.name: pin for pin in pins}
    for pin_name, expected_direction in REQUIRED_PIN_DIRECTIONS_BY_KIND[kind].items():
        if declared_pin_map[pin_name].direction != expected_direction:
            raise CellLibraryError(
                f"{path}.pins pin '{pin_name}' must have direction '{expected_direction}'"
            )

    orientations_list = _require_list(cell.get("orientations"), f"{path}.orientations")
    orientations = tuple(
        _require_str(value, f"{path}.orientations[{index}]").lower()
        for index, value in enumerate(orientations_list)
    )
    if not orientations:
        raise CellLibraryError(f"{path}.orientations must not be empty")
    invalid_orientations = [
        value for value in orientations if value not in VALID_ORIENTATIONS
    ]
    if invalid_orientations:
        raise CellLibraryError(
            f"{path}.orientations contains invalid value(s): "
            f"{', '.join(sorted(set(invalid_orientations)))}"
        )

    delay_ticks = _require_int(cell.get("delay_ticks"), f"{path}.delay_ticks")
    if delay_ticks < 0:
        raise CellLibraryError(f"{path}.delay_ticks must be >= 0")

    max_wire_without_repeater = _require_int(
        cell.get("max_wire_without_repeater"), f"{path}.max_wire_without_repeater"
    )
    if max_wire_without_repeater <= 0:
        raise CellLibraryError(f"{path}.max_wire_without_repeater must be > 0")

    notes = cell.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise CellLibraryError(f"{path}.notes must be a string when present")

    tags_raw = cell.get("tags", [])
    tags_list = _require_list(tags_raw, f"{path}.tags") if tags_raw is not None else []
    tags = tuple(
        _require_str(value, f"{path}.tags[{index}]")
        for index, value in enumerate(tags_list)
    )

    return CellLibraryCell(
        name=name,
        kind=kind,
        size=size,
        pins=pins,
        orientations=orientations,
        delay_ticks=delay_ticks,
        max_wire_without_repeater=max_wire_without_repeater,
        notes=notes,
        tags=tags,
    )


def load_cell_library(path: str | Path) -> CellLibrary:
    path = Path(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = _require_mapping(payload, str(path))

    name = _require_str(root.get("name"), f"{path}.name")
    version = _require_str(root.get("version"), f"{path}.version")
    cells_raw = _require_list(root.get("cells"), f"{path}.cells")
    cells = tuple(
        _parse_cell(raw_cell, f"{path}.cells[{index}]")
        for index, raw_cell in enumerate(cells_raw)
    )

    seen_names: set[str] = set()
    seen_kinds: set[str] = set()
    for cell in cells:
        if cell.name in seen_names:
            raise CellLibraryError(f"{path}.cells contains duplicate cell name '{cell.name}'")
        if cell.kind in seen_kinds:
            raise CellLibraryError(f"{path}.cells contains duplicate kind '{cell.kind}'")
        seen_names.add(cell.name)
        seen_kinds.add(cell.kind)

    return CellLibrary(
        name=name,
        version=version,
        cells=cells,
        source_path=str(path),
        metadata={k: v for k, v in root.items() if k not in {"name", "version", "cells"}},
    )

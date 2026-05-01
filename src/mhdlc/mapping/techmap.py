from __future__ import annotations

from collections import defaultdict

from mhdlc.ir.netlist import Design, Module, NetBit
from mhdlc.ir.redstone import (
    RedstoneCellInstance,
    RedstoneDesign,
    RedstoneModule,
    RedstoneNet,
    RedstonePinRef,
)
from mhdlc.techlib.models import CellLibrary, CellLibraryCell


CELL_PIN_MAP: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "AND": (("A", "B"), ("Y",)),
    "OR": (("A", "B"), ("Y",)),
    "XOR": (("A", "B"), ("Y",)),
    "INV": (("A",), ("Y",)),
    "MUX": (("A", "B", "S"), ("Y",)),
    "INPUT": ((), ("OUT",)),
    "OUTPUT": (("IN",), ()),
    "CONST0": ((), ("OUT",)),
    "CONST1": ((), ("OUT",)),
}


class MappingError(ValueError):
    pass


def _instance_from_library(
    *,
    instance_name: str,
    library_cell: CellLibraryCell,
    source_logical_module: str,
    source_logical_cell: str | None,
    source_port: str | None,
) -> RedstoneCellInstance:
    return RedstoneCellInstance(
        name=instance_name,
        library_cell=library_cell.name,
        kind=library_cell.kind,
        source_logical_module=source_logical_module,
        source_logical_cell=source_logical_cell,
        source_port=source_port,
        size=library_cell.size,
        delay_ticks=library_cell.delay_ticks,
        max_wire_without_repeater=library_cell.max_wire_without_repeater,
    )


def _require_library_cell(library: CellLibrary, kind: str) -> CellLibraryCell:
    library_cell = library.get_cell(kind)
    if library_cell is None:
        raise MappingError(f"cell library '{library.name}' has no definition for kind '{kind}'")
    return library_cell


def _require_library_pins(library_cell: CellLibraryCell, pin_names: tuple[str, ...], kind: str) -> None:
    for pin_name in pin_names:
        if library_cell.pin(pin_name) is None:
            raise MappingError(
                f"library cell '{library_cell.name}' for kind '{kind}' is missing pin '{pin_name}'"
            )


def _logical_aliases_by_bit(module: Module) -> dict[NetBit, tuple[str, ...]]:
    by_bit: dict[NetBit, list[str]] = defaultdict(list)
    for net in module.netnames.values():
        if len(net.bits) != 1:
            continue
        by_bit[net.bits[0]].append(net.name)
    return {bit: tuple(names) for bit, names in by_bit.items()}


def _preferred_net_name(bit: NetBit, aliases: tuple[str, ...]) -> str:
    if not aliases:
        return f"net_{bit}"
    visible = [alias for alias in aliases if not alias.startswith("$")]
    if visible:
        return visible[0]
    return aliases[0]


def map_module(module: Module, library: CellLibrary) -> RedstoneModule:
    instances: list[RedstoneCellInstance] = []
    net_drivers: dict[NetBit, RedstonePinRef] = {}
    net_sinks: dict[NetBit, list[RedstonePinRef]] = defaultdict(list)
    aliases_by_bit = _logical_aliases_by_bit(module)
    needed_constants: set[int] = set()

    input_cell = _require_library_cell(library, "INPUT")
    _require_library_pins(input_cell, ("OUT",), "INPUT")
    output_cell = _require_library_cell(library, "OUTPUT")
    _require_library_pins(output_cell, ("IN",), "OUTPUT")

    for port in module.ports:
        if port.direction == "input":
            for index, bit in enumerate(port.bits):
                instance_name = f"input:{port.name}[{index}]"
                instance = _instance_from_library(
                    instance_name=instance_name,
                    library_cell=input_cell,
                    source_logical_module=module.name,
                    source_logical_cell=None,
                    source_port=port.name,
                )
                instances.append(instance)
                net_drivers[bit] = RedstonePinRef(instance=instance_name, pin="OUT")
        elif port.direction == "output":
            for index, bit in enumerate(port.bits):
                instance_name = f"output:{port.name}[{index}]"
                instance = _instance_from_library(
                    instance_name=instance_name,
                    library_cell=output_cell,
                    source_logical_module=module.name,
                    source_logical_cell=None,
                    source_port=port.name,
                )
                instances.append(instance)
                if bit in {0, 1, "0", "1"}:
                    needed_constants.add(int(bit))
                    net_sinks[int(bit)].append(RedstonePinRef(instance=instance_name, pin="IN"))
                else:
                    net_sinks[bit].append(RedstonePinRef(instance=instance_name, pin="IN"))

    for cell in module.cells:
        library_cell = _require_library_cell(library, cell.kind)
        if cell.kind not in CELL_PIN_MAP:
            raise MappingError(f"phase-2 mapper does not support logical kind '{cell.kind}'")

        expected_inputs, expected_outputs = CELL_PIN_MAP[cell.kind]
        _require_library_pins(library_cell, expected_inputs + expected_outputs, cell.kind)

        ports = {port.name: port for port in cell.ports}
        for pin_name in expected_inputs + expected_outputs:
            if pin_name not in ports:
                raise MappingError(f"logical cell '{cell.name}' is missing expected pin '{pin_name}'")
            if len(ports[pin_name].bits) != 1:
                raise MappingError(
                    f"logical cell '{cell.name}' pin '{pin_name}' must be scalar for phase-2 mapping"
                )

        instance_name = f"cell:{cell.name}"
        instances.append(
            _instance_from_library(
                instance_name=instance_name,
                library_cell=library_cell,
                source_logical_module=module.name,
                source_logical_cell=cell.name,
                source_port=None,
            )
        )

        for pin_name in expected_inputs:
            bit = ports[pin_name].bits[0]
            if bit in {0, 1, "0", "1"}:
                needed_constants.add(int(bit))
                net_sinks[int(bit)].append(RedstonePinRef(instance=instance_name, pin=pin_name))
            else:
                net_sinks[bit].append(RedstonePinRef(instance=instance_name, pin=pin_name))

        for pin_name in expected_outputs:
            bit = ports[pin_name].bits[0]
            if bit in net_drivers:
                raise MappingError(f"logical bit {bit!r} has multiple mapped drivers")
            net_drivers[bit] = RedstonePinRef(instance=instance_name, pin=pin_name)

    for constant_value in sorted(needed_constants):
        kind = f"CONST{constant_value}"
        const_cell = _require_library_cell(library, kind)
        _require_library_pins(const_cell, ("OUT",), kind)
        instance_name = f"const:{constant_value}"
        instances.append(
            _instance_from_library(
                instance_name=instance_name,
                library_cell=const_cell,
                source_logical_module=module.name,
                source_logical_cell=None,
                source_port=None,
            )
        )
        net_drivers[constant_value] = RedstonePinRef(instance=instance_name, pin="OUT")

    nets: list[RedstoneNet] = []
    all_bits = sorted(
        set(net_drivers) | set(net_sinks),
        key=lambda value: (isinstance(value, str), str(value)),
    )
    for bit in all_bits:
        driver = net_drivers.get(bit)
        if driver is None:
            raise MappingError(f"logical bit {bit!r} has sink connections but no mapped driver")

        aliases = aliases_by_bit.get(bit, ())
        constant_value = int(bit) if bit in {0, 1, "0", "1"} else None
        net_name = (
            f"const_{constant_value}"
            if constant_value is not None
            else _preferred_net_name(bit, aliases)
        )
        nets.append(
            RedstoneNet(
                name=net_name,
                logical_bit=None if constant_value is not None else bit,
                aliases=aliases,
                driver=driver,
                sinks=tuple(net_sinks.get(bit, [])),
                constant_value=constant_value,
            )
        )

    return RedstoneModule(
        name=module.name,
        source_logical_module=module.name,
        instances=tuple(instances),
        nets=tuple(nets),
    )


def map_design(design: Design, library: CellLibrary) -> RedstoneDesign:
    return RedstoneDesign(
        library_name=library.name,
        library_version=library.version,
        modules={
            module_name: map_module(module, library)
            for module_name, module in design.modules.items()
        },
        source_creator=design.creator,
    )

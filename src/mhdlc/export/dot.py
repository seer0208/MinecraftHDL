from __future__ import annotations

from mhdlc.ir.netlist import Module


def module_to_dot(module: Module) -> str:
    lines = [f'digraph "{module.name}" {{', "  rankdir=LR;"]

    for port in module.ports:
        shape = "box" if port.direction == "input" else "oval"
        lines.append(f'  "port:{port.name}" [shape={shape}, label="{port.name}\\n{port.direction}"];')

    for cell in module.cells:
        lines.append(f'  "cell:{cell.name}" [shape=record, label="{cell.name}|{cell.kind}"];')

    drivers: dict[int | str, str] = {}
    for port in module.ports:
        if port.direction == "input":
            for bit in port.bits:
                drivers[bit] = f"port:{port.name}"
    for cell in module.cells:
        for output in cell.output_ports():
            for bit in output.bits:
                drivers[bit] = f"cell:{cell.name}"

    for cell in module.cells:
        for input_port in cell.input_ports():
            for bit in input_port.bits:
                driver = drivers.get(bit)
                if driver is not None:
                    lines.append(f'  "{driver}" -> "cell:{cell.name}" [label="{input_port.name}:{bit}"];')

    for port in module.ports:
        if port.direction == "output":
            for bit in port.bits:
                driver = drivers.get(bit)
                if driver is not None:
                    lines.append(f'  "{driver}" -> "port:{port.name}" [label="{bit}"];')

    lines.append("}")
    return "\n".join(lines) + "\n"

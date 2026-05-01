# Phase 2 Tech Mapping

Phase 2 adds a data-driven redstone technology layer on top of the logical netlist IR.

## Commands

Validate the default redstone library:

```bash
mhdlc techlib check src/mhdlc/techlib/libraries/redstone_v1.yaml
```

Map a logical design into the redstone technology netlist:

```bash
mhdlc map tests/fixtures/yosys/and_gate.json \
  --lib src/mhdlc/techlib/libraries/redstone_v1.yaml \
  --out build/and_gate.redstone.json
```

Map every module from a multi-module Yosys JSON file:

```bash
mhdlc map src/main/tests/json\ files/and.json \
  --all-modules \
  --lib src/mhdlc/techlib/libraries/redstone_v1.yaml \
  --out build/and_design.redstone.json
```

## Library Schema

Each cell entry in the YAML library defines:

- `name`
- `kind`
- `size`
- `pins`
- `orientations`
- `delay_ticks`
- `max_wire_without_repeater`
- optional `notes`
- optional `tags`

Each pin entry defines:

- `name`
- `direction`
- `anchor`
- `side`

## Supported Logical To Redstone Mapping

- `AND -> AND`
- `OR -> OR`
- `XOR -> XOR`
- `INV -> INV`
- `MUX -> MUX`
- input ports -> `INPUT`
- output ports -> `OUTPUT`
- literal `0 -> CONST0`
- literal `1 -> CONST1`

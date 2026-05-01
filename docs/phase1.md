# Phase 1 Scaffold

Phase 1 creates a standalone compiler core that can run without Minecraft or Forge.

## Commands

Import Yosys JSON into the normalized IR:

```bash
mhdlc import tests/fixtures/yosys/and_gate.json --out build/and_gate.mhdl.json
```

Import every module from a multi-module Yosys JSON design:

```bash
mhdlc import src/main/tests/json\ files/and.json --all-modules --out build/and.design.json
```

Validate a design:

```bash
mhdlc validate tests/fixtures/yosys/and_gate.json
```

Validate every module in a Yosys design and emit JSON:

```bash
mhdlc validate src/main/tests/json\ files/and.json --all-modules --json
```

List modules inside a Yosys JSON file:

```bash
mhdlc modules src/main/tests/json\ files/and.json
```

Export a DOT graph:

```bash
mhdlc graph tests/fixtures/yosys/and_gate.json --out build/and_gate.dot
```

## Design Rules for Phase 1

- Only acyclic combinational netlists are supported.
- Unsupported cells are treated as hard errors.
- Known sequential cells are recognized and rejected explicitly.
- Multi-module Yosys design files can be imported and validated as a whole.
- Net alias and hidden-net metadata are retained in the normalized IR.
- Structural validation runs on the normalized IR, not directly on the raw Yosys JSON.

## Next Work

- widen cell support
- capture assigns and net aliases more completely
- define the redstone cell library
- add placement/routing passes

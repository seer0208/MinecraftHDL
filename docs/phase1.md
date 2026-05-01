# Phase 1 Scaffold

Phase 1 creates a standalone compiler core that can run without Minecraft or Forge.

## Commands

Import Yosys JSON into the normalized IR:

```bash
mhdlc import tests/fixtures/yosys/and_gate.json --out build/and_gate.mhdl.json
```

Validate a design:

```bash
mhdlc validate tests/fixtures/yosys/and_gate.json
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
- Structural validation runs on the normalized IR, not directly on the raw Yosys JSON.

## Next Work

- widen cell support
- capture assigns and net aliases more completely
- define the redstone cell library
- add placement/routing passes

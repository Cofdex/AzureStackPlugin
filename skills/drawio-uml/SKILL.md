---
name: drawio-uml
description: >
  Generate production-grade UML diagrams as .drawio files using draw.io's native UML shape library.
  Use this skill whenever a user asks to create, draw, design, or visualize any UML diagram in draw.io
  or diagrams.net format. Triggers include: "draw a class diagram", "create a sequence diagram",
  "UML diagram in draw.io", "generate a .drawio UML file", "draw an activity diagram", "component
  diagram", "use case diagram", "state machine diagram", "ER diagram", "object diagram", "deployment
  diagram", "draw my system design as UML", "model these classes", "draw database schema", or any
  request to model software architecture, data models, workflows, object relationships, or system
  interactions visually. Also triggers when the user describes classes, entities, flows, sequences,
  or states and wants a diagram output — even without explicitly naming the UML type.
---

# Draw.io UML Diagrams

Generate production-grade `.drawio` XML for all standard UML 2.x diagram types plus ER diagrams.
Uses draw.io's built-in shape styles — no external imports or stencils required.

---

## Step 1 — Select Diagram Type

| User Intent | Diagram Type | Reference |
|---|---|---|
| Classes, attributes, methods, inheritance | Class Diagram | `references/class.md` |
| Method calls, time ordering, actors | Sequence Diagram | `references/sequence.md` |
| System actors, features, use cases | Use Case Diagram | `references/usecase.md` |
| Workflow, process steps, decisions, forks | Activity Diagram | `references/activity.md` |
| Software components, interfaces, ports | Component Diagram | `references/component.md` |
| States, transitions, guards, triggers | State Machine Diagram | `references/state.md` |
| Tables, columns, FK relationships | ER Diagram | `references/er.md` |
| Runtime instances, slot values | Object Diagram | `references/class.md` (instance mode) |
| Nodes, servers, deployment artifacts | Deployment Diagram | `references/deployment.md` |

**If the user's intent is ambiguous**, pick the most appropriate type and state your choice.

**If the diagram spans multiple types** (e.g., class + sequence), generate separate pages in one `.drawio` file using multiple `<diagram>` elements.

---

## Step 2 — Read the Reference

Read the reference file for the chosen diagram type. Each reference contains:
- The exact `style` strings for every element type
- A complete XML example you can adapt
- Layout rules and spacing conventions
- Common mistakes to avoid

**Do not guess style strings from memory.** The references contain the exact styles that render correctly in draw.io.

---

## Step 3 — Generate the Diagram

### .drawio XML Skeleton

Every diagram must use this exact wrapper. Missing any part causes draw.io to reject the file.

```xml
<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z"
        agent="Claude" version="24.0.0" type="device">
  <diagram id="page-1" name="Diagram Name">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827"
                  math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- All diagram content here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Multi-Page Diagrams

For diagrams spanning multiple types, add multiple `<diagram>` elements:

```xml
<mxfile ...>
  <diagram id="class-diagram" name="Class Diagram">
    <mxGraphModel ...> ... </mxGraphModel>
  </diagram>
  <diagram id="sequence-diagram" name="Sequence Diagram">
    <mxGraphModel ...> ... </mxGraphModel>
  </diagram>
</mxfile>
```

### Critical Rules

1. Root cells `id="0"` and `id="1" parent="0"` are **mandatory**
2. All elements must have `parent="1"` (or a group cell's ID)
3. IDs must be **unique** — use descriptive names like `class-user`, `edge-inherits-1`
4. Vertices: `vertex="1"` — Edges: `edge="1"` — mutually exclusive
5. Edges must reference valid `source` and `target` cell IDs
6. Always use **uncompressed XML** — never `compressed="true"`
7. Style strings are **semicolon-separated** and end with `;`
8. Coordinates: origin `(0,0)` is top-left; x→right, y→down

---

## UML Relationship Arrows — Quick Reference

These arrow styles apply across all diagram types:

| UML Relationship | Style String |
|---|---|
| **Association** (solid line) | `endArrow=none;strokeColor=#333333;strokeWidth=1;` |
| **Directed association** (→) | `endArrow=open;endFill=0;strokeColor=#333333;` |
| **Generalization / Inheritance** (△) | `endArrow=block;endFill=0;strokeColor=#333333;` |
| **Realization / Implementation** (△ dashed) | `endArrow=block;endFill=0;dashed=1;strokeColor=#333333;` |
| **Dependency** (→ dashed) | `endArrow=open;endFill=0;dashed=1;strokeColor=#333333;` |
| **Aggregation** (◇) | `endArrow=diamond;endFill=0;strokeColor=#333333;` |
| **Composition** (◆) | `endArrow=diamond;endFill=1;strokeColor=#333333;` |

### Edge Labels (Multiplicity, Role Names)

```xml
<mxCell id="edge-1" value="1..*" style="endArrow=open;endFill=0;strokeColor=#333333;"
  edge="1" parent="1" source="class-a" target="class-b">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

For source-side and target-side labels, use `Array` geometry with offsets:
```xml
<mxCell id="edge-1" style="endArrow=open;endFill=0;" edge="1" parent="1" source="a" target="b">
  <mxGeometry relative="1" as="geometry">
    <Array as="points" />
    <mxPoint as="sourcePoint" />
    <mxPoint as="targetPoint" />
  </mxGeometry>
</mxCell>
```

---

## Color Palette

Use these colors consistently across diagram types for visual coherence:

| Element | fillColor | strokeColor | Use For |
|---|---|---|---|
| Class / Entity | `#DAE8FC` | `#6C8EBF` | Classes, interfaces, entities |
| Abstract / Interface | `#E1D5E7` | `#9673A6` | Abstract classes, interfaces |
| Actor | `#F5F5F5` | `#666666` | UML actors |
| Component | `#D5E8D4` | `#82B366` | Components, packages |
| State | `#FFF2CC` | `#D6B656` | States, activities |
| Decision / Fork | `#F8CECC` | `#B85450` | Decisions, merge, fork, join |
| Note / Comment | `#FFFFC0` | `#FFD966` | Notes and annotations |
| Container / Boundary | `#F0F0F0` | `#999999` | System boundaries, packages |

---

## Layout Guidelines

### General Spacing

| Element | Spacing |
|---|---|
| Class boxes | 150–200px apart horizontally, 100–150px vertically |
| Lifelines (sequence) | 200px apart horizontally |
| States / Activities | 120–150px apart |
| Entities (ER) | 200–250px apart |

### Layout by Diagram Type

| Diagram | Preferred Layout |
|---|---|
| Class | Top-down: parent classes above children |
| Sequence | Left-to-right: actors/objects across top, time flows down |
| Activity | Top-to-bottom: start at top, end at bottom |
| Use Case | Center system boundary; actors outside left/right |
| State | Left-to-right or top-down: initial state → final state |
| Component | Left-to-right: data flow direction |
| ER | Grid: entities in a regular grid, relationships between |
| Deployment | Nested: nodes contain components |

---

## Pre-flight Checklist

Before outputting XML:

- [ ] Every `<mxCell>` has a unique `id`
- [ ] Root cells `id="0"` and `id="1"` are present
- [ ] All vertices have `vertex="1"`, all edges have `edge="1"`
- [ ] All edges have valid `source` and `target` IDs
- [ ] Children reference parent via `parent="..."` attribute
- [ ] Style strings come from the reference files — not guessed
- [ ] No overlapping elements
- [ ] Container cells are large enough for their children
- [ ] Complete `<mxfile>` → `<diagram>` → `<mxGraphModel>` → `<root>` wrapper

---

## Common Mistakes

| Mistake | Impact | Fix |
|---|---|---|
| Missing root cells | draw.io won't load | Always include `id="0"` and `id="1"` |
| Duplicate IDs | Elements overwrite | Use unique descriptive IDs |
| `compressed="true"` | AI output is invalid | Always uncompressed |
| Wrong arrow style | Misrepresents UML semantics | Check arrow reference table above |
| Children with absolute coords in group | Render outside parent | Children use relative coords |
| Swimlane height too small | Attributes overflow | Calculate: `startSize + (rowCount × rowHeight)` |

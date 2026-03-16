# State Machine Diagram Reference

## Overview

State machine diagrams show the states an object passes through during its lifecycle,
the events that trigger transitions, and the actions performed.

---

## Elements

### State

A rounded rectangle representing a stable condition.

**Simple state style:**
```
rounded=1;whiteSpace=wrap;html=1;arcSize=20;
fillColor=#FFF2CC;strokeColor=#D6B656;fontStyle=1;fontSize=12;
```

- Width: **140px**, Height: **40px**

### Composite State (with regions)

A state containing sub-states, drawn as a swimlane container.

**Composite state style:**
```
swimlane;fontStyle=1;align=center;startSize=26;html=1;
childLayout=stackLayout;horizontal=1;horizontalStack=0;
resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;
rounded=1;arcSize=12;
fillColor=#FFF2CC;strokeColor=#D6B656;
```

### Initial Pseudo-State (filled circle)

**Style:**
```
ellipse;html=1;
fillColor=#333333;strokeColor=#333333;
```

- Width/Height: **20px**

### Final State (bullseye)

**Style:**
```
ellipse;html=1;shape=doubleCircle;whiteSpace=wrap;
fillColor=#333333;strokeColor=#333333;aspect=fixed;
```

- Width/Height: **24px**

### Choice Pseudo-State (diamond)

**Style:**
```
rhombus;whiteSpace=wrap;html=1;
fillColor=#FFF2CC;strokeColor=#D6B656;
```

- Width/Height: **30px**

### Junction Pseudo-State (small filled circle)

**Style:**
```
ellipse;html=1;
fillColor=#333333;strokeColor=#333333;
```

- Width/Height: **10px**

### Fork / Join Bar

**Style:**
```
shape=line;html=1;strokeWidth=4;strokeColor=#333333;
fillColor=none;fontSize=0;
```

### History State (H / H*)

**Shallow history style:**
```
ellipse;html=1;
fillColor=#FFFFFF;strokeColor=#333333;fontSize=12;fontStyle=1;
```

- Value: `H` — Width/Height: **24px**

**Deep history:** Value: `H*`

---

## Transitions

Transitions are edges with labels in the format: `event [guard] / action`

**Transition style:**
```
endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;
```

**Self-transition** (loops back to the same state):
```
endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;curved=1;
```

### Transition Label Format

```
event [guard] / action
```

Examples:
- `coinInserted [amount >= price] / dispenseItem`
- `timeout / retry`
- `submit [valid]`

---

## Internal Activities

States can show internal activities using child cells:

| Keyword | Meaning |
|---|---|
| `entry / action` | Performed when entering the state |
| `do / activity` | Ongoing activity while in the state |
| `exit / action` | Performed when leaving the state |

Use `text` child cells to show these inside a composite state.

---

## Layout Rules

1. **Left-to-right** or **top-to-bottom** flow
2. Initial state at top-left (or top)
3. Final state at bottom-right (or bottom)
4. Composite states: sub-states use relative coordinates inside the parent
5. Keep transition arrows short and avoid crossings

---

## Complete Example — Order State Machine

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="state-1" name="Order States">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Initial pseudo-state -->
        <mxCell id="initial" value=""
          style="ellipse;html=1;fillColor=#333333;strokeColor=#333333;"
          vertex="1" parent="1">
          <mxGeometry x="80" y="90" width="20" height="20" as="geometry" />
        </mxCell>

        <!-- States -->
        <mxCell id="state-created" value="Created"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#FFF2CC;strokeColor=#D6B656;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="160" y="80" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="state-confirmed" value="Confirmed"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#FFF2CC;strokeColor=#D6B656;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="380" y="80" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="state-processing" value="Processing"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#FFF2CC;strokeColor=#D6B656;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="600" y="80" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="state-shipped" value="Shipped"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#FFF2CC;strokeColor=#D6B656;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="600" y="220" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="state-delivered" value="Delivered"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="380" y="220" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="state-cancelled" value="Cancelled"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#F8CECC;strokeColor=#B85450;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="160" y="220" width="140" height="40" as="geometry" />
        </mxCell>

        <!-- Final state -->
        <mxCell id="final" value=""
          style="ellipse;html=1;shape=doubleCircle;whiteSpace=wrap;fillColor=#333333;strokeColor=#333333;aspect=fixed;"
          vertex="1" parent="1">
          <mxGeometry x="215" y="320" width="24" height="24" as="geometry" />
        </mxCell>

        <!-- Transitions -->
        <mxCell id="t-init" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="initial" target="state-created">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-confirm" value="confirm()"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="state-created" target="state-confirmed">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-process" value="pay() [paid]"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="state-confirmed" target="state-processing">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-ship" value="ship()"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="state-processing" target="state-shipped">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-deliver" value="deliver()"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="state-shipped" target="state-delivered">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-cancel-1" value="cancel()"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="state-created" target="state-cancelled">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-cancel-2" value="cancel()"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="state-confirmed" target="state-cancelled">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-final-1" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="state-delivered" target="final">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="t-final-2" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="state-cancelled" target="final">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

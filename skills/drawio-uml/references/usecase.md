# Use Case Diagram Reference

## Overview

Use case diagrams show system functionality from the user's perspective. Actors interact
with use cases (ellipses) inside a system boundary (rectangle).

---

## Elements

### Actor

Stick-figure representation of an external entity (person, system, device).

**Actor style:**
```
shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;
html=1;outlineConnect=0;
fillColor=#F5F5F5;strokeColor=#666666;fontStyle=1;fontSize=12;
```

- Width: **30px**, Height: **60px**
- Place actors **outside** the system boundary, aligned left or right

### Use Case

An ellipse representing a system feature or behavior.

**Use case style:**
```
ellipse;whiteSpace=wrap;html=1;
fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=0;fontSize=12;
```

- Width: **140px**, Height: **60px**
- Place use cases **inside** the system boundary
- Label is the behavior name: `Login`, `Place Order`, `Generate Report`

### System Boundary

A rectangle that contains all use cases and separates them from actors.

**System boundary style:**
```
shape=umlFrame;whiteSpace=wrap;html=1;pointerEvents=0;
fillColor=#F0F0F0;strokeColor=#999999;strokeWidth=2;
fontStyle=1;fontSize=14;verticalAlign=top;align=left;spacingLeft=10;
```

- Must be large enough to contain all use cases
- Label: system name in the top-left corner

---

## Relationships

### Association (Actor → Use Case)

Simple solid line connecting actor to use case.

```
endArrow=none;strokeColor=#333333;strokeWidth=1;
```

### Include (<<include>>)

One use case always includes another.

```
endArrow=open;endFill=0;dashed=1;strokeColor=#333333;
```

Label the edge: `&lt;&lt;include&gt;&gt;`

### Extend (<<extend>>)

One use case optionally extends another.

```
endArrow=open;endFill=0;dashed=1;strokeColor=#333333;
```

Label the edge: `&lt;&lt;extend&gt;&gt;`

**Direction:**
- `<<include>>`: arrow from **base** use case to **included** use case
- `<<extend>>`: arrow from **extending** use case to **base** use case

### Generalization (Actor inherits Actor)

```
endArrow=block;endFill=0;strokeColor=#333333;
```

---

## Layout Rules

1. **System boundary centered**, actors outside on left and/or right
2. **Primary actors** on the left, **secondary actors** (systems, timers) on the right
3. Use cases arranged in a vertical stack or grid inside the boundary
4. Related use cases (include/extend) placed near each other
5. Actors: 60–80px from the boundary edge

---

## Complete Example — E-Commerce System

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="uc-1" name="Use Cases">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- System Boundary -->
        <mxCell id="sys-boundary" value="E-Commerce System"
          style="shape=umlFrame;whiteSpace=wrap;html=1;pointerEvents=0;fillColor=#F0F0F0;strokeColor=#999999;strokeWidth=2;fontStyle=1;fontSize=14;verticalAlign=top;align=left;spacingLeft=10;"
          vertex="1" parent="1">
          <mxGeometry x="200" y="40" width="500" height="360" as="geometry" />
        </mxCell>

        <!-- Actors -->
        <mxCell id="actor-customer" value="Customer"
          style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#F5F5F5;strokeColor=#666666;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="60" y="120" width="30" height="60" as="geometry" />
        </mxCell>

        <mxCell id="actor-admin" value="Admin"
          style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#F5F5F5;strokeColor=#666666;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="60" y="280" width="30" height="60" as="geometry" />
        </mxCell>

        <mxCell id="actor-payment" value="Payment Gateway"
          style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#F5F5F5;strokeColor=#666666;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="820" y="180" width="30" height="60" as="geometry" />
        </mxCell>

        <!-- Use Cases -->
        <mxCell id="uc-browse" value="Browse Products"
          style="ellipse;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="310" y="70" width="140" height="60" as="geometry" />
        </mxCell>

        <mxCell id="uc-order" value="Place Order"
          style="ellipse;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="310" y="170" width="140" height="60" as="geometry" />
        </mxCell>

        <mxCell id="uc-pay" value="Process Payment"
          style="ellipse;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="530" y="170" width="140" height="60" as="geometry" />
        </mxCell>

        <mxCell id="uc-manage" value="Manage Inventory"
          style="ellipse;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="310" y="300" width="140" height="60" as="geometry" />
        </mxCell>

        <!-- Associations -->
        <mxCell id="assoc-1" style="endArrow=none;strokeColor=#333333;"
          edge="1" parent="1" source="actor-customer" target="uc-browse">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="assoc-2" style="endArrow=none;strokeColor=#333333;"
          edge="1" parent="1" source="actor-customer" target="uc-order">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="assoc-3" style="endArrow=none;strokeColor=#333333;"
          edge="1" parent="1" source="actor-admin" target="uc-manage">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="assoc-4" style="endArrow=none;strokeColor=#333333;"
          edge="1" parent="1" source="actor-payment" target="uc-pay">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Include: Place Order includes Process Payment -->
        <mxCell id="include-1" value="&lt;&lt;include&gt;&gt;"
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#333333;html=1;fontSize=10;fontStyle=2;"
          edge="1" parent="1" source="uc-order" target="uc-pay">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

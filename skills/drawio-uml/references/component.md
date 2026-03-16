# Component Diagram Reference

## Overview

Component diagrams show the structural relationships between software components, their
interfaces, ports, and dependencies. They represent the modular structure of a system.

---

## Elements

### Component

A rectangle with the component icon (two small rectangles on the left side).

**Component style:**
```
shape=component;align=left;spacingLeft=36;rounded=1;html=1;
fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;
whiteSpace=wrap;
```

- Width: **160–200px**, Height: **60–80px**

### Package (Grouping)

A container that groups related components.

**Package style:**
```
shape=folder;fontStyle=1;spacingTop=10;tabWidth=80;tabHeight=14;
tabPosition=left;html=1;whiteSpace=wrap;
fillColor=#F0F0F0;strokeColor=#999999;fontSize=13;
```

- Acts as a container — child components use `parent="package-id"`

### Interface (Provided — Lollipop)

A small circle representing an interface the component provides.

**Provided interface style:**
```
ellipse;html=1;
fillColor=#FFFFFF;strokeColor=#333333;fontSize=10;
```

- Width/Height: **10px**
- Label below: the interface name
- Connect to component via a solid line

### Interface (Required — Socket)

A half-circle representing an interface the component requires.

**Required interface style:**
```
shape=requiredInterface;html=1;
strokeColor=#333333;fontSize=10;
```

- Width: **10px**, Height: **20px**
- Connect to a provided interface via assembly connector

### Port

A small square on the boundary of a component.

**Port style:**
```
shape=module;jettyWidth=8;jettyHeight=4;html=1;
fillColor=#FFFFFF;strokeColor=#333333;
```

- Width/Height: **16px**
- Positioned on the edge of the component (`parent="component-id"`)

### Artifact

A rectangle with a document icon, representing a deployable unit.

**Artifact style:**
```
shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=left;
fillColor=#F5F5F5;strokeColor=#666666;fontSize=11;
```

---

## Relationships

| Relationship | Style | Meaning |
|---|---|---|
| Dependency | `endArrow=open;endFill=0;dashed=1;strokeColor=#333333;` | Uses / depends on |
| Realization | `endArrow=block;endFill=0;dashed=1;strokeColor=#333333;` | Implements |
| Association | `endArrow=none;strokeColor=#333333;` | Connected |
| Assembly | `endArrow=none;strokeColor=#333333;` | Provided ↔ Required interface link |

---

## Layout Rules

1. **Left-to-right** or **layered** layout
2. High-level components on the left, dependencies flow right
3. Group related components in packages
4. Interfaces on the edges of components facing their consumers
5. Keep crossing lines to a minimum

---

## Complete Example — Web Application

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="comp-1" name="Components">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Presentation Layer Package -->
        <mxCell id="pkg-presentation" value="Presentation Layer"
          style="shape=folder;fontStyle=1;spacingTop=10;tabWidth=110;tabHeight=14;tabPosition=left;html=1;whiteSpace=wrap;fillColor=#F0F0F0;strokeColor=#999999;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="300" height="200" as="geometry" />
        </mxCell>

        <mxCell id="comp-ui" value="WebUI"
          style="shape=component;align=left;spacingLeft=36;rounded=1;html=1;fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;whiteSpace=wrap;"
          vertex="1" parent="pkg-presentation">
          <mxGeometry x="30" y="50" width="160" height="60" as="geometry" />
        </mxCell>

        <mxCell id="comp-controller" value="Controller"
          style="shape=component;align=left;spacingLeft=36;rounded=1;html=1;fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;whiteSpace=wrap;"
          vertex="1" parent="pkg-presentation">
          <mxGeometry x="30" y="130" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Business Layer Package -->
        <mxCell id="pkg-business" value="Business Layer"
          style="shape=folder;fontStyle=1;spacingTop=10;tabWidth=100;tabHeight=14;tabPosition=left;html=1;whiteSpace=wrap;fillColor=#F0F0F0;strokeColor=#999999;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="430" y="40" width="300" height="200" as="geometry" />
        </mxCell>

        <mxCell id="comp-auth" value="AuthService"
          style="shape=component;align=left;spacingLeft=36;rounded=1;html=1;fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;whiteSpace=wrap;"
          vertex="1" parent="pkg-business">
          <mxGeometry x="30" y="50" width="160" height="60" as="geometry" />
        </mxCell>

        <mxCell id="comp-order" value="OrderService"
          style="shape=component;align=left;spacingLeft=36;rounded=1;html=1;fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;whiteSpace=wrap;"
          vertex="1" parent="pkg-business">
          <mxGeometry x="30" y="130" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Data Layer Package -->
        <mxCell id="pkg-data" value="Data Layer"
          style="shape=folder;fontStyle=1;spacingTop=10;tabWidth=80;tabHeight=14;tabPosition=left;html=1;whiteSpace=wrap;fillColor=#F0F0F0;strokeColor=#999999;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="430" y="300" width="300" height="140" as="geometry" />
        </mxCell>

        <mxCell id="comp-repo" value="Repository"
          style="shape=component;align=left;spacingLeft=36;rounded=1;html=1;fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;whiteSpace=wrap;"
          vertex="1" parent="pkg-data">
          <mxGeometry x="30" y="50" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Dependencies -->
        <mxCell id="dep-1" value=""
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="comp-controller" target="comp-auth">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="dep-2" value=""
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="comp-controller" target="comp-order">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="dep-3" value=""
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="comp-order" target="comp-repo">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="dep-4" value=""
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="comp-auth" target="comp-repo">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="dep-ui-ctrl" value=""
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="comp-ui" target="comp-controller">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

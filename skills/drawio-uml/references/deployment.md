# Deployment Diagram Reference

## Overview

Deployment diagrams show the physical deployment of software artifacts onto hardware nodes.
They model the runtime architecture: servers, devices, execution environments, and the
artifacts deployed within them.

---

## Elements

### Node (Server / Device)

A 3D box representing a physical or virtual machine.

**Node style:**
```
shape=mxgraph.flowchart.display;html=1;whiteSpace=wrap;
fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;
```

For a simpler 3D-box appearance:

```
shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;
fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;
darkOpacity=0.05;darkOpacity2=0.1;
```

- Width: **200–300px**, Height: **150–250px**
- Nodes can be **containers** — deploy artifacts inside them

### Execution Environment

A node with a `<<execution environment>>` stereotype.

**Style:**
```
shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;
fillColor=#E1D5E7;strokeColor=#9673A6;fontStyle=1;fontSize=12;
darkOpacity=0.05;darkOpacity2=0.1;
```

- Value: `&lt;&lt;execution environment&gt;&gt;\nDocker Container`

### Artifact

A rectangle with a document icon (<<artifact>> stereotype).

**Artifact style:**
```
shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=center;
fillColor=#F5F5F5;strokeColor=#666666;fontSize=11;
```

- Value: `&lt;&lt;artifact&gt;&gt;\napp.war`
- Placed **inside** a node as a child cell

### Device

Physical hardware with a `<<device>>` stereotype.

**Device style:**
```
shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;
fillColor=#FFF2CC;strokeColor=#D6B656;fontStyle=1;fontSize=12;
darkOpacity=0.05;darkOpacity2=0.1;
```

### Database

**Database style:**
```
shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;
fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=1;fontSize=12;
```

- Width: **80px**, Height: **80px**

---

## Relationships

| Relationship | Style | Meaning |
|---|---|---|
| Communication path | `endArrow=none;strokeColor=#333333;strokeWidth=2;` | Network link between nodes |
| Deployment | `endArrow=open;endFill=0;dashed=1;strokeColor=#333333;` | Artifact deployed on node |
| Dependency | `endArrow=open;endFill=0;dashed=1;strokeColor=#999999;` | Component dependency |

Communication path labels typically show protocol: `<<HTTP>>`, `<<TCP>>`, `<<AMQP>>`

---

## Layout Rules

1. **Nested containment** — artifacts inside nodes, nodes inside devices
2. **Tier-based layout** — client tier left, server tier center, database tier right
3. Communication paths horizontal between tiers
4. Children use relative coordinates inside their parent node
5. Label communication paths with protocol

---

## Complete Example — 3-Tier Web App Deployment

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="deploy-1" name="Deployment">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Client Device -->
        <mxCell id="node-client" value="&lt;&lt;device&gt;&gt;&#xa;Client Browser"
          style="shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#FFF2CC;strokeColor=#D6B656;fontStyle=1;fontSize=12;darkOpacity=0.05;darkOpacity2=0.1;"
          vertex="1" parent="1">
          <mxGeometry x="40" y="120" width="200" height="120" as="geometry" />
        </mxCell>

        <mxCell id="art-spa" value="&lt;&lt;artifact&gt;&gt;&#xa;SPA Bundle"
          style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=center;fillColor=#F5F5F5;strokeColor=#666666;fontSize=11;"
          vertex="1" parent="node-client">
          <mxGeometry x="30" y="50" width="140" height="50" as="geometry" />
        </mxCell>

        <!-- Web Server -->
        <mxCell id="node-web" value="&lt;&lt;server&gt;&gt;&#xa;Web Server (nginx)"
          style="shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#D5E8D4;strokeColor=#82B366;fontStyle=1;fontSize=12;darkOpacity=0.05;darkOpacity2=0.1;"
          vertex="1" parent="1">
          <mxGeometry x="360" y="40" width="260" height="160" as="geometry" />
        </mxCell>

        <mxCell id="art-api" value="&lt;&lt;artifact&gt;&gt;&#xa;api-server.jar"
          style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=center;fillColor=#F5F5F5;strokeColor=#666666;fontSize=11;"
          vertex="1" parent="node-web">
          <mxGeometry x="20" y="60" width="140" height="50" as="geometry" />
        </mxCell>

        <!-- App Server -->
        <mxCell id="node-app" value="&lt;&lt;execution environment&gt;&gt;&#xa;Docker Container"
          style="shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#E1D5E7;strokeColor=#9673A6;fontStyle=1;fontSize=12;darkOpacity=0.05;darkOpacity2=0.1;"
          vertex="1" parent="1">
          <mxGeometry x="360" y="260" width="260" height="160" as="geometry" />
        </mxCell>

        <mxCell id="art-worker" value="&lt;&lt;artifact&gt;&gt;&#xa;worker.py"
          style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=center;fillColor=#F5F5F5;strokeColor=#666666;fontSize=11;"
          vertex="1" parent="node-app">
          <mxGeometry x="20" y="60" width="140" height="50" as="geometry" />
        </mxCell>

        <!-- Database Server -->
        <mxCell id="node-db" value="PostgreSQL"
          style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=1;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="740" y="160" width="100" height="100" as="geometry" />
        </mxCell>

        <!-- Communication paths -->
        <mxCell id="comm-1" value="&lt;&lt;HTTPS&gt;&gt;"
          style="endArrow=none;strokeColor=#333333;strokeWidth=2;html=1;fontSize=10;fontStyle=2;"
          edge="1" parent="1" source="node-client" target="node-web">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="comm-2" value="&lt;&lt;AMQP&gt;&gt;"
          style="endArrow=none;strokeColor=#333333;strokeWidth=2;html=1;fontSize=10;fontStyle=2;"
          edge="1" parent="1" source="node-web" target="node-app">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="comm-3" value="&lt;&lt;TCP&gt;&gt;"
          style="endArrow=none;strokeColor=#333333;strokeWidth=2;html=1;fontSize=10;fontStyle=2;"
          edge="1" parent="1" source="node-web" target="node-db">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="comm-4" value="&lt;&lt;TCP&gt;&gt;"
          style="endArrow=none;strokeColor=#333333;strokeWidth=2;html=1;fontSize=10;fontStyle=2;"
          edge="1" parent="1" source="node-app" target="node-db">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

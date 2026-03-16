# Activity Diagram Reference

## Overview

Activity diagrams model workflows, business processes, and algorithms. They show
control flow from activity to activity, with decisions, forks, and joins.

---

## Elements

### Initial Node (filled circle)

**Style:**
```
ellipse;html=1;shape=mxgraph.flowchart.start_2;
fillColor=#333333;strokeColor=#333333;
```

- Width/Height: **30px**

### Final Node (bullseye)

**Style:**
```
ellipse;html=1;shape=doubleCircle;whiteSpace=wrap;
fillColor=#333333;strokeColor=#333333;aspect=fixed;
```

- Width/Height: **30px**

### Flow Final (circle with X)

**Style:**
```
ellipse;html=1;shape=mxgraph.flowchart.terminate;
fillColor=#FFFFFF;strokeColor=#333333;
```

- Width/Height: **30px**

### Action / Activity (rounded rectangle)

**Style:**
```
rounded=1;whiteSpace=wrap;html=1;arcSize=40;
fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=0;fontSize=12;
```

- Width: **140px**, Height: **40px**
- Label: the action verb phrase — `Validate Input`, `Send Email`, `Process Payment`

### Decision / Merge Diamond

**Style:**
```
rhombus;whiteSpace=wrap;html=1;
fillColor=#FFF2CC;strokeColor=#D6B656;fontSize=11;
```

- Width/Height: **40px**
- Decision: one incoming, two+ outgoing edges with guard conditions
- Merge: two+ incoming, one outgoing edge
- Guards appear as edge labels in square brackets: `[valid]`, `[invalid]`

### Fork / Join Bar (horizontal)

**Horizontal bar style:**
```
shape=line;html=1;strokeWidth=4;strokeColor=#333333;
fillColor=none;fontSize=0;align=left;
```

- Width: **200px**, Height: **2px**
- Fork: one incoming, multiple outgoing
- Join: multiple incoming, one outgoing

### Swimlane (Partition)

Used to group activities by role or department.

**Swimlane container style:**
```
shape=table;startSize=0;container=1;collapsible=0;
childLayout=tableLayout;fixedRows=1;rowLines=0;
fontStyle=0;align=center;resizeLast=1;html=1;
fillColor=none;strokeColor=#999999;
```

**Swimlane column header:**
```
swimlane;startSize=30;html=1;
fillColor=#F0F0F0;strokeColor=#999999;fontStyle=1;fontSize=12;
```

### Note

**Style:**
```
shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=top;align=left;
fillColor=#FFFFC0;strokeColor=#FFD966;fontSize=11;
```

---

## Control Flow Edges

All edges in activity diagrams are simple directed arrows:

**Default flow:**
```
endArrow=block;endFill=1;strokeColor=#333333;
```

**With guard condition:**
```xml
<mxCell id="flow-1" value="[amount &gt; 100]"
  style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
  edge="1" parent="1" source="decision-1" target="activity-approve">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

---

## Layout Rules

1. **Top-to-bottom** flow as default
2. Initial node at the top, final node at the bottom
3. Decisions: place `[yes]` branch going straight down, `[no]` branch going right
4. Fork/Join bars span the width of their parallel activities
5. Swimlanes: divide canvas into vertical columns

---

## Complete Example — Order Processing

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="act-1" name="Order Processing">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Initial node -->
        <mxCell id="start" value=""
          style="ellipse;html=1;shape=mxgraph.flowchart.start_2;fillColor=#333333;strokeColor=#333333;"
          vertex="1" parent="1">
          <mxGeometry x="270" y="20" width="30" height="30" as="geometry" />
        </mxCell>

        <!-- Activities -->
        <mxCell id="act-receive" value="Receive Order"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="215" y="80" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="act-validate" value="Validate Order"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="215" y="160" width="140" height="40" as="geometry" />
        </mxCell>

        <!-- Decision -->
        <mxCell id="decision-valid" value=""
          style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;"
          vertex="1" parent="1">
          <mxGeometry x="265" y="240" width="40" height="40" as="geometry" />
        </mxCell>

        <mxCell id="act-reject" value="Reject Order"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor=#F8CECC;strokeColor=#B85450;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="420" y="240" width="140" height="40" as="geometry" />
        </mxCell>

        <!-- Fork bar -->
        <mxCell id="fork-1" value=""
          style="shape=line;html=1;strokeWidth=4;strokeColor=#333333;fillColor=none;fontSize=0;"
          vertex="1" parent="1">
          <mxGeometry x="185" y="320" width="200" height="2" as="geometry" />
        </mxCell>

        <!-- Parallel activities -->
        <mxCell id="act-pack" value="Pack Items"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="100" y="370" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="act-charge" value="Charge Payment"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="330" y="370" width="140" height="40" as="geometry" />
        </mxCell>

        <!-- Join bar -->
        <mxCell id="join-1" value=""
          style="shape=line;html=1;strokeWidth=4;strokeColor=#333333;fillColor=none;fontSize=0;"
          vertex="1" parent="1">
          <mxGeometry x="185" y="450" width="200" height="2" as="geometry" />
        </mxCell>

        <mxCell id="act-ship" value="Ship Order"
          style="rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
          vertex="1" parent="1">
          <mxGeometry x="215" y="490" width="140" height="40" as="geometry" />
        </mxCell>

        <!-- Final node -->
        <mxCell id="end" value=""
          style="ellipse;html=1;shape=doubleCircle;whiteSpace=wrap;fillColor=#333333;strokeColor=#333333;aspect=fixed;"
          vertex="1" parent="1">
          <mxGeometry x="270" y="570" width="30" height="30" as="geometry" />
        </mxCell>

        <!-- Edges -->
        <mxCell id="flow-start" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="start" target="act-receive">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-1" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="act-receive" target="act-validate">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-2" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="act-validate" target="decision-valid">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-yes" value="[valid]"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="decision-valid" target="fork-1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-no" value="[invalid]"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;fontSize=10;"
          edge="1" parent="1" source="decision-valid" target="act-reject">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-fork-pack" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="fork-1" target="act-pack">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-fork-charge" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="fork-1" target="act-charge">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-pack-join" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="act-pack" target="join-1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-charge-join" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="act-charge" target="join-1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-join-ship" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="join-1" target="act-ship">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="flow-ship-end" style="endArrow=block;endFill=1;strokeColor=#333333;"
          edge="1" parent="1" source="act-ship" target="end">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

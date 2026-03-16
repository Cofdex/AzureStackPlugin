# Sequence Diagram Reference

## Overview

Sequence diagrams show interactions between objects over time. Participants are arranged left-to-right
across the top; messages flow top-to-bottom to show temporal ordering.

---

## Elements

### Participant (Lifeline Header)

The rectangle at the top representing an object or actor.

**Participant style:**
```
shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;
container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;
portConstraint=eastwest;newEdgeStyle={"curved":0,"rounded":0};
fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=1;fontSize=13;
```

**Actor participant style** (stick figure):
```
shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;
whiteSpace=wrap;html=1;container=1;dropTarget=0;collapsible=0;
recursiveResize=0;outlineConnect=0;portConstraint=eastwest;
newEdgeStyle={"curved":0,"rounded":0};
fillColor=#F5F5F5;strokeColor=#666666;fontStyle=1;fontSize=13;
```

**Sizing:**
- Width: **100–140px**
- Height: **300–600px** (tall enough for the full conversation)
- Spacing: **200px** apart horizontally

### Activation Bar (Execution Specification)

A thin rectangle on a lifeline showing when a participant is processing.

**Activation style:**
```
html=1;points=[];perimeter=orthogonalPerimeter;outlineConnect=0;
targetShapes=umlLifeline;portConstraint=eastwest;newEdgeStyle={"curved":0,"rounded":0};
fillColor=#FFFFFF;strokeColor=#333333;
```

- Width: **10px**
- Positioned as a **child** of the lifeline (`parent="lifeline-id"`)
- x offset: **45px** (centers on a 100px lifeline) — formula: `(parentWidth - 10) / 2`
- y: positioned vertically at the message arrival point

### Destroy Marker (X)

Indicates object destruction at end of lifeline.

**Style:**
```
html=1;points=[];perimeter=orthogonalPerimeter;outlineConnect=0;
targetShapes=umlLifeline;portConstraint=eastwest;newEdgeStyle={"curved":0,"rounded":0};
shape=umlDestroy;strokeColor=#FF0000;
```

---

## Messages

Messages are edges connecting lifelines or activation bars. The y-coordinate of the edge
determines temporal ordering — messages lower on the diagram happen later.

### Message Types

| Type | Style | Line | Arrow |
|---|---|---|---|
| Synchronous call | `endArrow=block;endFill=1;strokeColor=#333333;` | Solid | Filled ▶ |
| Asynchronous call | `endArrow=open;endFill=0;strokeColor=#333333;` | Solid | Open → |
| Return | `endArrow=open;endFill=0;dashed=1;strokeColor=#999999;` | Dashed | Open → |
| Self-call | `endArrow=block;endFill=1;strokeColor=#333333;curved=1;` | Solid, curved | Filled ▶ |
| Create | `endArrow=open;endFill=0;dashed=1;strokeColor=#333333;` | Dashed | Open → |

### Message Labels

Message labels appear as the `value` attribute on the edge:

```xml
<mxCell id="msg-1" value="authenticate(user, pass)"
  style="endArrow=block;endFill=1;strokeColor=#333333;"
  edge="1" parent="1" source="act-client" target="act-server">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Self-Messages

For self-calls, source and target are the same lifeline. Add a loop using waypoints:

```xml
<mxCell id="msg-self" value="validate()"
  style="endArrow=block;endFill=1;strokeColor=#333333;curved=1;"
  edge="1" parent="1" source="act-server" target="act-server">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="520" y="200" />
    </Array>
  </mxGeometry>
</mxCell>
```

---

## Interaction Fragments (Frames)

Frames represent loops, conditions, and alternatives.

**Frame style:**
```
shape=umlFrame;whiteSpace=wrap;html=1;pointerEvents=0;
fillColor=none;strokeColor=#999999;strokeWidth=1;
```

- Place the frame **behind** the lifelines and messages it covers
- The `value` is the fragment keyword: `loop`, `alt`, `opt`, `break`, `par`, `ref`, `critical`

**Divider inside alt/par frames:**
```
line;strokeWidth=1;strokeColor=#999999;dashed=1;
```

---

## Layout Rules

1. **Participants left-to-right:** Place in order of first appearance in the scenario
2. **Time flows down:** Each subsequent message is 40–50px lower than the previous
3. **Activation bars:** Start at the incoming message, end at the return (or when processing ends)
4. **Self-messages:** Loop to the right and come back, 30–50px tall
5. **Fragments:** Span all involved lifelines with 10px padding on each side

---

## Complete Example — Login Sequence

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="seq-1" name="Login Sequence">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Participants -->
        <mxCell id="ll-user" value="User"
          style="shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#F5F5F5;strokeColor=#666666;fontStyle=1;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="80" y="40" width="100" height="400" as="geometry" />
        </mxCell>

        <mxCell id="ll-ui" value=":LoginForm"
          style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=1;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="280" y="40" width="100" height="400" as="geometry" />
        </mxCell>

        <mxCell id="ll-auth" value=":AuthService"
          style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=1;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="480" y="40" width="100" height="400" as="geometry" />
        </mxCell>

        <mxCell id="ll-db" value=":Database"
          style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#DAE8FC;strokeColor=#6C8EBF;fontStyle=1;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="680" y="40" width="100" height="400" as="geometry" />
        </mxCell>

        <!-- Activation bars -->
        <mxCell id="act-ui" value=""
          style="html=1;points=[];perimeter=orthogonalPerimeter;outlineConnect=0;targetShapes=umlLifeline;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#FFFFFF;strokeColor=#333333;"
          vertex="1" parent="ll-ui">
          <mxGeometry x="45" y="80" width="10" height="200" as="geometry" />
        </mxCell>

        <mxCell id="act-auth" value=""
          style="html=1;points=[];perimeter=orthogonalPerimeter;outlineConnect=0;targetShapes=umlLifeline;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#FFFFFF;strokeColor=#333333;"
          vertex="1" parent="ll-auth">
          <mxGeometry x="45" y="120" width="10" height="120" as="geometry" />
        </mxCell>

        <mxCell id="act-db" value=""
          style="html=1;points=[];perimeter=orthogonalPerimeter;outlineConnect=0;targetShapes=umlLifeline;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#FFFFFF;strokeColor=#333333;"
          vertex="1" parent="ll-db">
          <mxGeometry x="45" y="160" width="10" height="60" as="geometry" />
        </mxCell>

        <!-- Messages -->
        <mxCell id="msg-1" value="login(user, pass)"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="ll-user" target="act-ui">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="130" y="120" as="sourcePoint" />
          </mxGeometry>
        </mxCell>

        <mxCell id="msg-2" value="authenticate(user, pass)"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="act-ui" target="act-auth">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="msg-3" value="findUser(user)"
          style="endArrow=block;endFill=1;strokeColor=#333333;html=1;"
          edge="1" parent="1" source="act-auth" target="act-db">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="msg-4" value="user record"
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#999999;html=1;"
          edge="1" parent="1" source="act-db" target="act-auth">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="msg-5" value="token"
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#999999;html=1;"
          edge="1" parent="1" source="act-auth" target="act-ui">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <mxCell id="msg-6" value="login success"
          style="endArrow=open;endFill=0;dashed=1;strokeColor=#999999;html=1;"
          edge="1" parent="1" source="act-ui" target="ll-user">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

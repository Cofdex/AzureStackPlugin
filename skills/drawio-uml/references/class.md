# Class Diagram Reference

## Elements

### Class Box

A class is a `swimlane` cell with child `text` cells for attributes and methods.
The `startSize` controls the header height; child cells stack below it.

**Class header style:**
```
swimlane;fontStyle=1;align=center;startSize=26;html=1;
childLayout=stackLayout;horizontal=1;horizontalStack=0;
resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;
fillColor=#DAE8FC;strokeColor=#6C8EBF;swimlaneLine=1;
```

**Abstract class header style** (italic name):
```
swimlane;fontStyle=3;align=center;startSize=26;html=1;
childLayout=stackLayout;horizontal=1;horizontalStack=0;
resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;
fillColor=#E1D5E7;strokeColor=#9673A6;swimlaneLine=1;
```

**Interface header style** (`«interface»` stereotype):
```
swimlane;fontStyle=1;align=center;startSize=40;html=1;
childLayout=stackLayout;horizontal=1;horizontalStack=0;
resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;
fillColor=#E1D5E7;strokeColor=#9673A6;swimlaneLine=1;
```

### Attribute / Method Row

Each attribute or method is a child `text` cell inside the class.

**Row style:**
```
text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;
spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;
points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;
```

**Separator line** (between attributes and methods):
```
line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;
spacingTop=-1;spacingLeft=3;spacingRight=10;rotatable=0;labelPosition=left;
points=[];portConstraint=eastwest;strokeColor=#6C8EBF;
```

### Sizing Rules

- Class width: **160–220px** (accommodate longest member name)
- Header height: **26px** (plain class), **40px** (with stereotype)
- Row height: **26px** each
- Separator height: **8px**
- Total height: `startSize + (attributeCount × 26) + 8 + (methodCount × 26)`

---

## UML Visibility Notation

| Symbol | Visibility |
|---|---|
| `+` | public |
| `-` | private |
| `#` | protected |
| `~` | package |

Format: `visibility name : Type` for attributes, `visibility name(params) : ReturnType` for methods.

Static members: underline (`<u>...</u>`) in the HTML value.
Abstract methods: italicize (`<i>...</i>`) in the HTML value.

---

## Relationships

| Relationship | Style |
|---|---|
| Inheritance | `endArrow=block;endFill=0;strokeColor=#333333;` |
| Realization | `endArrow=block;endFill=0;dashed=1;strokeColor=#333333;` |
| Association | `endArrow=open;endFill=0;strokeColor=#333333;` |
| Aggregation | `endArrow=diamond;endFill=0;strokeColor=#333333;` |
| Composition | `endArrow=diamond;endFill=1;strokeColor=#333333;` |
| Dependency | `endArrow=open;endFill=0;dashed=1;strokeColor=#333333;` |

---

## Object Diagram Mode

An object diagram uses the same class box style but with instance notation:

- Header value: `objectName : ClassName` (underlined)
- Header style: add `fontStyle=4;` (underline) instead of `fontStyle=1;` (bold)
- Attribute rows: `name = value` (not `name : Type`)
- No method section

---

## Complete Example — Class Diagram

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="class-1" name="Class Diagram">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Animal (abstract) -->
        <mxCell id="class-animal" value="&lt;i&gt;Animal&lt;/i&gt;"
          style="swimlane;fontStyle=3;align=center;startSize=26;html=1;childLayout=stackLayout;horizontal=1;horizontalStack=0;resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;fillColor=#E1D5E7;strokeColor=#9673A6;swimlaneLine=1;"
          vertex="1" parent="1">
          <mxGeometry x="300" y="40" width="180" height="112" as="geometry" />
        </mxCell>
        <mxCell id="attr-animal-name" value="- name: String"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="class-animal">
          <mxGeometry y="26" width="180" height="26" as="geometry" />
        </mxCell>
        <mxCell id="sep-animal" value=""
          style="line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=10;rotatable=0;labelPosition=left;points=[];portConstraint=eastwest;strokeColor=#9673A6;"
          vertex="1" parent="class-animal">
          <mxGeometry y="52" width="180" height="8" as="geometry" />
        </mxCell>
        <mxCell id="method-animal-speak" value="+ speak(): void"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="class-animal">
          <mxGeometry y="60" width="180" height="26" as="geometry" />
        </mxCell>
        <mxCell id="method-animal-move" value="+ move(distance: int): void"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="class-animal">
          <mxGeometry y="86" width="180" height="26" as="geometry" />
        </mxCell>

        <!-- Dog -->
        <mxCell id="class-dog" value="Dog"
          style="swimlane;fontStyle=1;align=center;startSize=26;html=1;childLayout=stackLayout;horizontal=1;horizontalStack=0;resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;fillColor=#DAE8FC;strokeColor=#6C8EBF;swimlaneLine=1;"
          vertex="1" parent="1">
          <mxGeometry x="160" y="240" width="180" height="86" as="geometry" />
        </mxCell>
        <mxCell id="attr-dog-breed" value="- breed: String"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="class-dog">
          <mxGeometry y="26" width="180" height="26" as="geometry" />
        </mxCell>
        <mxCell id="sep-dog" value=""
          style="line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=10;rotatable=0;labelPosition=left;points=[];portConstraint=eastwest;strokeColor=#6C8EBF;"
          vertex="1" parent="class-dog">
          <mxGeometry y="52" width="180" height="8" as="geometry" />
        </mxCell>
        <mxCell id="method-dog-fetch" value="+ fetch(): void"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="class-dog">
          <mxGeometry y="60" width="180" height="26" as="geometry" />
        </mxCell>

        <!-- Cat -->
        <mxCell id="class-cat" value="Cat"
          style="swimlane;fontStyle=1;align=center;startSize=26;html=1;childLayout=stackLayout;horizontal=1;horizontalStack=0;resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;fillColor=#DAE8FC;strokeColor=#6C8EBF;swimlaneLine=1;"
          vertex="1" parent="1">
          <mxGeometry x="440" y="240" width="180" height="86" as="geometry" />
        </mxCell>
        <mxCell id="attr-cat-indoor" value="- indoor: boolean"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="class-cat">
          <mxGeometry y="26" width="180" height="26" as="geometry" />
        </mxCell>
        <mxCell id="sep-cat" value=""
          style="line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=10;rotatable=0;labelPosition=left;points=[];portConstraint=eastwest;strokeColor=#6C8EBF;"
          vertex="1" parent="class-cat">
          <mxGeometry y="52" width="180" height="8" as="geometry" />
        </mxCell>
        <mxCell id="method-cat-purr" value="+ purr(): void"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="class-cat">
          <mxGeometry y="60" width="180" height="26" as="geometry" />
        </mxCell>

        <!-- Inheritance: Dog → Animal -->
        <mxCell id="edge-dog-animal" style="endArrow=block;endFill=0;strokeColor=#333333;"
          edge="1" parent="1" source="class-dog" target="class-animal">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Inheritance: Cat → Animal -->
        <mxCell id="edge-cat-animal" style="endArrow=block;endFill=0;strokeColor=#333333;"
          edge="1" parent="1" source="class-cat" target="class-animal">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

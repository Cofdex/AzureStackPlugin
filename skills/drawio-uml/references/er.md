# ER Diagram Reference

## Overview

Entity-Relationship diagrams model database schemas. They show entities (tables),
their attributes (columns), and the relationships between them.

This reference uses draw.io's `shape=table` style for clean table-based ER diagrams
with proper PK/FK notation.

---

## Elements

### Entity (Table)

A swimlane-style cell where the header is the table name and child rows are columns.

**Table header style:**
```
shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;
fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;
fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=13;
```

### Column Row

Each column is a child cell inside the table.

**Primary key column style:**
```
text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;
spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;
points=[[0,0.5],[1,0.5]];portConstraint=eastwest;
fontStyle=5;fontColor=#333333;
```

(`fontStyle=5` = bold + underline, indicating primary key)

**Regular column style:**
```
text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;
spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;
points=[[0,0.5],[1,0.5]];portConstraint=eastwest;
fontColor=#333333;
```

**Foreign key column style:**
```
text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;
spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;
points=[[0,0.5],[1,0.5]];portConstraint=eastwest;
fontStyle=2;fontColor=#6C8EBF;
```

(`fontStyle=2` = italic, indicating foreign key; blue text to distinguish)

### Sizing Rules

- Table width: **180–240px** (fit longest column name + type)
- Header height: **30px**
- Row height: **26px**
- Total height: `30 + (columnCount × 26)`

### Column Name Format

Use this pattern for column values:

- **PK:** `🔑 column_name : TYPE`
- **FK:** `🔗 column_name : TYPE`
- **Regular:** `   column_name : TYPE`

Or use the simpler text format: `column_name TYPE PK`, `column_name TYPE FK`

---

## Relationships

ER relationships use Crow's Foot notation for cardinality.

### Cardinality Styles

| Cardinality | Source End | Target End | Style |
|---|---|---|---|
| One-to-One | `startArrow=ERone` | `endArrow=ERone` | `startArrow=ERone;endArrow=ERone;strokeColor=#333333;` |
| One-to-Many | `startArrow=ERone` | `endArrow=ERmany` | `startArrow=ERone;endArrow=ERmany;strokeColor=#333333;` |
| Many-to-Many | `startArrow=ERmany` | `endArrow=ERmany` | `startArrow=ERmany;endArrow=ERmany;strokeColor=#333333;` |
| Zero-or-One | `startArrow=ERone` | `endArrow=ERzeroToOne` | `startArrow=ERone;endArrow=ERzeroToOne;strokeColor=#333333;` |
| One-or-More | `startArrow=ERone` | `endArrow=ERoneToMany` | `startArrow=ERone;endArrow=ERoneToMany;strokeColor=#333333;` |
| Zero-or-More | `startArrow=ERone` | `endArrow=ERzeroToMany` | `startArrow=ERone;endArrow=ERzeroToMany;strokeColor=#333333;` |

**Full relationship style template:**
```
endArrow=ERmany;startArrow=ERone;endFill=0;startFill=0;
strokeColor=#333333;
```

**Important:** Always include `endFill=0;startFill=0;` for ER arrows.

---

## Layout Rules

1. **Grid layout** — entities in a regular grid, 200–250px apart
2. Place related entities adjacent to each other
3. Minimize line crossings
4. FK relationships: source entity has the FK column, target entity has the PK
5. Junction tables (M:N): place between the two entities they connect

---

## Complete Example — Blog Database Schema

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="er-1" name="Blog Schema">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- User table -->
        <mxCell id="tbl-user" value="users"
          style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="80" y="80" width="200" height="134" as="geometry" />
        </mxCell>
        <mxCell id="col-user-id" value="🔑 id : SERIAL"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontStyle=5;fontColor=#333333;"
          vertex="1" parent="tbl-user">
          <mxGeometry y="30" width="200" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-user-email" value="   email : VARCHAR(255)"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-user">
          <mxGeometry y="56" width="200" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-user-name" value="   display_name : VARCHAR(100)"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-user">
          <mxGeometry y="82" width="200" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-user-created" value="   created_at : TIMESTAMP"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-user">
          <mxGeometry y="108" width="200" height="26" as="geometry" />
        </mxCell>

        <!-- Post table -->
        <mxCell id="tbl-post" value="posts"
          style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="420" y="80" width="220" height="186" as="geometry" />
        </mxCell>
        <mxCell id="col-post-id" value="🔑 id : SERIAL"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontStyle=5;fontColor=#333333;"
          vertex="1" parent="tbl-post">
          <mxGeometry y="30" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-post-author" value="🔗 author_id : INTEGER"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontStyle=2;fontColor=#6C8EBF;"
          vertex="1" parent="tbl-post">
          <mxGeometry y="56" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-post-title" value="   title : VARCHAR(255)"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-post">
          <mxGeometry y="82" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-post-body" value="   body : TEXT"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-post">
          <mxGeometry y="108" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-post-status" value="   status : VARCHAR(20)"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-post">
          <mxGeometry y="134" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-post-created" value="   created_at : TIMESTAMP"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-post">
          <mxGeometry y="160" width="220" height="26" as="geometry" />
        </mxCell>

        <!-- Comment table -->
        <mxCell id="tbl-comment" value="comments"
          style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=13;"
          vertex="1" parent="1">
          <mxGeometry x="420" y="340" width="220" height="160" as="geometry" />
        </mxCell>
        <mxCell id="col-comment-id" value="🔑 id : SERIAL"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontStyle=5;fontColor=#333333;"
          vertex="1" parent="tbl-comment">
          <mxGeometry y="30" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-comment-post" value="🔗 post_id : INTEGER"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontStyle=2;fontColor=#6C8EBF;"
          vertex="1" parent="tbl-comment">
          <mxGeometry y="56" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-comment-author" value="🔗 author_id : INTEGER"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontStyle=2;fontColor=#6C8EBF;"
          vertex="1" parent="tbl-comment">
          <mxGeometry y="82" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-comment-body" value="   body : TEXT"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-comment">
          <mxGeometry y="108" width="220" height="26" as="geometry" />
        </mxCell>
        <mxCell id="col-comment-created" value="   created_at : TIMESTAMP"
          style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontColor=#333333;"
          vertex="1" parent="tbl-comment">
          <mxGeometry y="134" width="220" height="26" as="geometry" />
        </mxCell>

        <!-- Relationships -->
        <!-- User 1:N Post -->
        <mxCell id="rel-user-post" value=""
          style="endArrow=ERmany;startArrow=ERone;endFill=0;startFill=0;strokeColor=#333333;"
          edge="1" parent="1" source="col-user-id" target="col-post-author">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Post 1:N Comment -->
        <mxCell id="rel-post-comment" value=""
          style="endArrow=ERmany;startArrow=ERone;endFill=0;startFill=0;strokeColor=#333333;"
          edge="1" parent="1" source="col-post-id" target="col-comment-post">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- User 1:N Comment -->
        <mxCell id="rel-user-comment" value=""
          style="endArrow=ERmany;startArrow=ERone;endFill=0;startFill=0;strokeColor=#333333;"
          edge="1" parent="1" source="col-user-id" target="col-comment-author">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

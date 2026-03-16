---
name: drawio-azure
description: >
  Generate production-ready Azure architecture diagrams as .drawio files using official Microsoft Azure
  icons. Use this skill whenever a user asks to create, design, draw, or visualize any Azure architecture,
  cloud infrastructure, solution design, or system topology in draw.io or diagrams.net format. Triggers:
  "draw an Azure architecture", "create a draw.io diagram", "design an Azure solution", "generate a
  .drawio file", "architecture diagram for Azure", "draw my Azure setup", "diagram this Azure
  infrastructure", or any request involving Azure services with a visual output. Also triggers when the
  user describes an Azure solution and wants it visualized — even without saying "draw.io" explicitly.
  Produces valid .drawio XML with official Azure icons, WAF-aligned zones, and professional layouts.
---

# Draw.io Azure Architecture Diagrams

Generate `.drawio` XML files with official Azure icons, WAF-aligned zones, swim-lanes, and canonical
layout patterns. The output opens directly in draw.io / diagrams.net — no manual assembly required.

## Icon Source: Official Microsoft Azure Icons

This skill uses the **official Azure Architecture Center icons** hosted on GitHub at
`code.benco.io/icon-collection/azure-icons/`. These are higher quality and actively maintained
compared to the legacy built-in `mxgraph.azure2` shapes.

### How Icons Are Embedded

Icons are referenced using the `shape=image` style with a direct SVG URL:

```xml
<mxCell id="vm-1" value="Virtual Machine"
  style="shape=image;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=https://code.benco.io/icon-collection/azure-icons/Virtual-Machine.svg;"
  vertex="1" parent="1">
  <mxGeometry x="200" y="300" width="50" height="50" as="geometry" />
</mxCell>
```

### Icon URL Pattern

```
https://code.benco.io/icon-collection/azure-icons/<Filename>.svg
```

Where `<Filename>` uses PascalCase with hyphens: `Virtual-Machine.svg`, `App-Services.svg`, etc.

**For the full icon catalog** → read `references/azure-icon-styles.md`

---

## .drawio XML Structure

Every diagram must follow this exact skeleton. Missing any part causes draw.io to reject the file.

```xml
<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z"
        agent="Claude" version="24.0.0" type="device">
  <diagram id="azure-arch" name="Azure Architecture">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1654" pageHeight="1169"
                  math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- All diagram content goes here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Critical Rules

1. The first two `<mxCell>` elements (`id="0"` and `id="1" parent="0"`) are **mandatory** — they are the root container and default layer
2. All diagram elements must have `parent="1"` (or the id of a group cell)
3. IDs must be **unique** within the diagram — use descriptive kebab-case like `vm-web-01`, `vnet-hub`
4. Vertices need `vertex="1"`, edges need `edge="1"` — mutually exclusive
5. Edges should reference `source` and `target` by cell ID
6. Always use **uncompressed XML** — never set `compressed="true"`
7. Style strings end with semicolons: `"rounded=1;whiteSpace=wrap;html=1;"`
8. Coordinates: origin `(0,0)` is top-left; x increases right, y increases down

---

## Element Types

### Azure Service Icons

```xml
<mxCell id="unique-id" value="Label"
  style="shape=image;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=https://code.benco.io/icon-collection/azure-icons/<Icon-Name>.svg;"
  vertex="1" parent="parent-id">
  <mxGeometry x="X" y="Y" width="50" height="50" as="geometry" />
</mxCell>
```

- **width/height**: Use `50×50` for standard icons, `40×40` for dense diagrams, `65×65` for hero/focal icons
- **verticalLabelPosition=bottom; verticalAlign=top**: Places the label below the icon
- **aspect=fixed; imageAspect=0**: Preserves icon proportions

### Zone / Group Containers (for subnets, resource groups, regions)

```xml
<!-- Group container -->
<mxCell id="zone-id" value="Zone Label" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#666666;dashed=1;verticalAlign=top;fontStyle=1;fontSize=14;spacingTop=5;container=1;collapsible=0;strokeWidth=2;" vertex="1" parent="1">
  <mxGeometry x="X" y="Y" width="W" height="H" as="geometry" />
</mxCell>

<!-- Child elements use the group as parent -->
<mxCell id="child-id" value="..." style="..." vertex="1" parent="zone-id">
  <mxGeometry x="20" y="40" width="50" height="50" as="geometry" />
</mxCell>
```

Zone children use **relative coordinates** (offset from top-left of the parent group).

### Connections (Edges)

```xml
<!-- Simple arrow -->
<mxCell id="edge-1" style="endArrow=block;endFill=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1" source="source-id" target="target-id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Labeled arrow -->
<mxCell id="edge-2" value="HTTPS" style="endArrow=block;endFill=1;strokeColor=#333333;strokeWidth=2;fontSize=11;" edge="1" parent="1" source="source-id" target="target-id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Dashed arrow (optional/async flow) -->
<mxCell id="edge-3" style="endArrow=block;endFill=1;dashed=1;strokeColor=#999999;" edge="1" parent="1" source="source-id" target="target-id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Text Labels and Annotations

```xml
<mxCell id="note-1" value="&lt;b&gt;Note:&lt;/b&gt; All traffic goes through Front Door" style="text;html=1;align=left;verticalAlign=top;fontSize=11;fontColor=#666666;" vertex="1" parent="1">
  <mxGeometry x="X" y="Y" width="200" height="30" as="geometry" />
</mxCell>
```

---

## Zone Color Palette (WAF-aligned)

Use these colors consistently for zone containers to visually distinguish architectural boundaries:

| Zone | fillColor | strokeColor | Use for |
|---|---|---|---|
| Azure Subscription | `#E6F3FF` | `#0078D4` | Top-level Azure subscription boundary |
| Resource Group | `#F0F0F0` | `#888888` | Resource group containers |
| Virtual Network | `#E8F5E9` | `#388E3C` | VNets, address spaces |
| Subnet | `#F1F8E9` | `#689F38` | Individual subnets within a VNet |
| Availability Zone | `#FFF3E0` | `#F57C00` | AZ boundaries |
| On-premises | `#EFEBE9` | `#795548` | On-prem / hybrid cloud |
| External / Internet | `#FCE4EC` | `#C62828` | External users, internet traffic |
| Security boundary | `#FFF8E1` | `#FFA000` | NSGs, firewalls, WAF |

### Zone Style Template

```
rounded=1;whiteSpace=wrap;html=1;fillColor=<fill>;strokeColor=<stroke>;dashed=<0|1>;verticalAlign=top;fontStyle=1;fontSize=14;spacingTop=5;container=1;collapsible=0;strokeWidth=2;fillOpacity=50;
```

---

## Layout Patterns

### Pattern 1: Left-to-Right Flow (most common)

```
Internet → Front Door → App Service → Database
  (x=50)    (x=250)      (x=500)      (x=750)
```

- Place icons at y-center of their zone
- Maintain **200px horizontal spacing** between tiers
- Keep all tiers at the same y-level when possible
- Flow reads left → right like a sentence

### Pattern 2: Hub-Spoke Network

```
         Spoke-VNet-1
              |
Spoke-VNet-2 — Hub-VNet — Spoke-VNet-3
              |
         Spoke-VNet-4
```

- Hub at center (`x=400, y=300`)
- Spokes at cardinal positions, **250px** from hub center
- VPN/ExpressRoute gateway in hub zone

### Pattern 3: Multi-Tier (Top-Down)

```
        Presentation Tier (y=50)
              |
         Logic Tier (y=300)
              |
         Data Tier (y=550)
```

- **250px vertical spacing** between tiers
- Each tier is a zone container

### Spacing Rules

| Element | Spacing |
|---|---|
| Icons within a zone | 100–120px apart |
| Zone containers | 30–50px gap between zones |
| Tier-to-tier (top-down) | 250px |
| Tier-to-tier (left-right) | 200px |
| Icon to zone edge padding | 20–30px |
| Label padding below icon | Built in via `verticalLabelPosition=bottom` |

---

## Diagram Generation Workflow

1. **Identify the Azure services** from the user's request
2. **Look up icon filenames** → read `references/azure-icon-styles.md` for the exact filename
3. **Choose a layout pattern** (left-to-right, hub-spoke, multi-tier) based on the architecture
4. **Define zones** — group resources by VNet, subnet, resource group, or logical tier
5. **Place icons** inside zones with consistent spacing
6. **Draw connections** between services with labeled edges showing protocol/data flow
7. **Add annotations** — title, legend, notes about key design decisions
8. **Generate the complete .drawio XML** as a single file
9. **Save the file** with a descriptive name: `<architecture-name>.drawio`

### Pre-flight Checklist

Before outputting XML, verify:
- [ ] Every `<mxCell>` has a unique `id`
- [ ] Root cells `id="0"` and `id="1"` are present
- [ ] All vertices have `vertex="1"`, all edges have `edge="1"`
- [ ] All edges have valid `source` and `target` IDs that reference existing cells
- [ ] Child elements reference their parent zone's ID in `parent="..."`
- [ ] Icon URLs use the exact filenames from `references/azure-icon-styles.md`
- [ ] No overlapping elements (check x, y, width, height)
- [ ] Zone containers are large enough to fit their children
- [ ] File has the complete `<mxfile>` → `<diagram>` → `<mxGraphModel>` → `<root>` wrapper

---

## Complete Example: 3-Tier Web App

```xml
<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z" agent="Claude" version="24.0.0" type="device">
  <diagram id="three-tier" name="3-Tier Web Application">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Title -->
        <mxCell id="title" value="&lt;b&gt;3-Tier Web Application&lt;/b&gt;" style="text;html=1;fontSize=18;fontColor=#333333;align=left;" vertex="1" parent="1">
          <mxGeometry x="50" y="20" width="400" height="30" as="geometry" />
        </mxCell>

        <!-- Internet zone -->
        <mxCell id="zone-internet" value="Internet" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FCE4EC;strokeColor=#C62828;dashed=1;verticalAlign=top;fontStyle=1;fontSize=14;spacingTop=5;container=1;collapsible=0;strokeWidth=2;fillOpacity=50;" vertex="1" parent="1">
          <mxGeometry x="50" y="80" width="160" height="200" as="geometry" />
        </mxCell>
        <mxCell id="users" value="Users" style="shape=image;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=https://code.benco.io/icon-collection/azure-icons/Users.svg;" vertex="1" parent="zone-internet">
          <mxGeometry x="55" y="60" width="50" height="50" as="geometry" />
        </mxCell>

        <!-- VNet zone -->
        <mxCell id="zone-vnet" value="Virtual Network (10.0.0.0/16)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#388E3C;verticalAlign=top;fontStyle=1;fontSize=14;spacingTop=5;container=1;collapsible=0;strokeWidth=2;fillOpacity=50;" vertex="1" parent="1">
          <mxGeometry x="280" y="60" width="700" height="260" as="geometry" />
        </mxCell>

        <!-- Web tier subnet -->
        <mxCell id="subnet-web" value="Web Subnet (10.0.1.0/24)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F1F8E9;strokeColor=#689F38;dashed=1;verticalAlign=top;fontSize=12;spacingTop=5;container=1;collapsible=0;" vertex="1" parent="zone-vnet">
          <mxGeometry x="20" y="40" width="200" height="190" as="geometry" />
        </mxCell>
        <mxCell id="appgw" value="Application&#xa;Gateway" style="shape=image;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=https://code.benco.io/icon-collection/azure-icons/Application-Gateways.svg;" vertex="1" parent="subnet-web">
          <mxGeometry x="75" y="50" width="50" height="50" as="geometry" />
        </mxCell>

        <!-- App tier subnet -->
        <mxCell id="subnet-app" value="App Subnet (10.0.2.0/24)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F1F8E9;strokeColor=#689F38;dashed=1;verticalAlign=top;fontSize=12;spacingTop=5;container=1;collapsible=0;" vertex="1" parent="zone-vnet">
          <mxGeometry x="250" y="40" width="200" height="190" as="geometry" />
        </mxCell>
        <mxCell id="app" value="App Service" style="shape=image;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=https://code.benco.io/icon-collection/azure-icons/App-Services.svg;" vertex="1" parent="subnet-app">
          <mxGeometry x="75" y="50" width="50" height="50" as="geometry" />
        </mxCell>

        <!-- Data tier subnet -->
        <mxCell id="subnet-data" value="Data Subnet (10.0.3.0/24)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F1F8E9;strokeColor=#689F38;dashed=1;verticalAlign=top;fontSize=12;spacingTop=5;container=1;collapsible=0;" vertex="1" parent="zone-vnet">
          <mxGeometry x="480" y="40" width="200" height="190" as="geometry" />
        </mxCell>
        <mxCell id="sqldb" value="SQL Database" style="shape=image;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=https://code.benco.io/icon-collection/azure-icons/SQL-Database.svg;" vertex="1" parent="subnet-data">
          <mxGeometry x="75" y="50" width="50" height="50" as="geometry" />
        </mxCell>

        <!-- Connections -->
        <mxCell id="e1" value="HTTPS" style="endArrow=block;endFill=1;strokeColor=#333333;strokeWidth=2;fontSize=11;" edge="1" parent="1" source="users" target="appgw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e2" value="" style="endArrow=block;endFill=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1" source="appgw" target="app">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e3" value="TDS" style="endArrow=block;endFill=1;strokeColor=#333333;strokeWidth=2;fontSize=11;" edge="1" parent="1" source="app" target="sqldb">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## Common Mistakes to Avoid

| Mistake | Why it breaks | Fix |
|---|---|---|
| Missing `id="0"` / `id="1"` root cells | draw.io refuses to load the file | Always include both mandatory cells |
| Using `mxgraph.azure2.*` shapes | Legacy, low-quality, many missing | Use `shape=image` with SVG URLs from the icon collection |
| `compressed="true"` | AI-generated compressed XML is invalid | Never compress — use plain XML |
| Duplicate IDs | Elements overwrite each other | Use unique descriptive IDs |
| Edge with non-existent source/target | Floating disconnected arrow | Verify all source/target IDs exist |
| Child uses absolute coords in a group | Elements render outside their zone | Children use relative coordinates (offset from parent origin) |
| Icon URL typo | Broken image in draw.io | Verify filename in `references/azure-icon-styles.md` |
| Zone container too small for children | Icons overflow visually | Calculate: children × spacing + padding |

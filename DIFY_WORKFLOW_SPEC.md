# Dify Workflow Design: Post-Slot Logic (Complete Specification)

**Version:** 1.0  
**Date:** 2025-11-12  
**Purpose:** Define the complete Dify workflow for handling post-slot-filling logic (routing, composition, output)

---

## 1. Workflow Diagram (Node List & Wiring)

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ INPUT NODE                                              │
│ ID: start                                               │
│ Variable: input.text                                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ HTTP NODE – Intent Recognizer                           │
│ ID: http_intent                                         │
│ Method: POST                                            │
│ URL: https://your-slot-api.com/recognize/simple        │
│ Body: {"query": "{{ input.text }}"}                    │
│ Output: http_intent.data                                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ IF/ELSE NODE – Domain Router                            │
│ ID: domain_router                                       │
│ ├─ Branch A: country_profile                            │
│ ├─ Branch B: legislation                                │
│ └─ Branch C: commitment                                 │
└─────┬──────────────┬──────────────┬─────────────────────┘
      │              │              │
      A              B              C
      │              │              │
      ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ IF/ELSE      │ │ CODE NODE    │ │ CODE NODE    │
│ Section      │ │ Legislation  │ │ Commitment   │
│ Sub-Router   │ │ Composer     │ │ Composer     │
│ ID:          │ │ ID:          │ │ ID:          │
│ section_     │ │ code_leg     │ │ code_cmt     │
│ router       │ └──────┬───────┘ └──────┬───────┘
│ ├─fires      │        │                │
│ ├─drought    │        │                │
│ ├─climate    │        │                │
│ └─default    │        │                │
└───┬──┬──┬──┬─┘        │                │
    │  │  │  │          │                │
    ▼  ▼  ▼  ▼          │                │
┌──────────────┐        │                │
│ CODE NODE    │        │                │
│ Country      │        │                │
│ Profile      │        │                │
│ Composer     │        │                │
│ ID: code_cp  │        │                │
└──────┬───────┘        │                │
       │                │                │
       └────────┬───────┴────────────────┘
                │
                ▼
       ┌────────────────┐
       │ (OPTIONAL)     │
       │ HTTP NODE      │
       │ Fetch Data     │
       │ ID: http_fetch │
       └────────┬───────┘
                │
                ▼
       ┌────────────────┐
       │ OUTPUT NODE    │
       │ ID: output_json│
       └────────────────┘
                │
                ▼
              END
```

**Node Count:** 7 nodes (8 if optional HTTP fetch included)

**Wiring Summary:**
1. `start` → `http_intent`
2. `http_intent` → `domain_router`
3. `domain_router` → Branch A: `section_router` | Branch B: `code_leg` | Branch C: `code_cmt`
4. `section_router` → `code_cp` (all sub-branches)
5. `code_cp`, `code_leg`, `code_cmt` → `http_fetch` (optional) → `output_json`

---

## 2. If/Else Conditions (Copy-Ready for Dify)

### 2.1 Domain Router (Primary Branch)

**Node ID:** `domain_router`

**Branch A – Country Profile:**
```
{{ http_intent.data.domain }} == "country_profile"
```

**Branch B – Legislation:**
```
{{ http_intent.data.domain }} == "legislation"
```

**Branch C – Commitment:**
```
{{ http_intent.data.domain }} == "commitment"
```

---

### 2.2 Section Sub-Router (Country Profile Only)

**Node ID:** `section_router`

**Branch A1 – Fires:**
```
{{ (http_intent.data.section_hint or '') contains 'fires' }}
```

**Branch A2 – Drought:**
```
{{ (http_intent.data.section_hint or '') contains 'drought' }}
```

**Branch A3 – Climate Hazards:**
```
{{ (http_intent.data.section_hint or '') contains 'climate_hazards' }}
```

**Branch A4 – Default (All Other Sections):**
```
{{ true }}
```

---

## 3. Code Templates (Python)

### 3.1 Country Profile Composer

**Node ID:** `code_cp`

**Input Variables:**
- `targets` ← `{{ http_intent.data.targets }}`
- `iso3_codes` ← `{{ http_intent.data.iso3_codes }}`
- `domain` ← `{{ http_intent.data.domain }}`
- `section_hint` ← `{{ http_intent.data.section_hint }}`
- `raw_query` ← `{{ http_intent.data.query }}`

**Python Code:**
```python
def main(targets, iso3_codes, domain, section_hint, raw_query):
    # Normalize inputs
    country = targets[0] if targets else "Unknown"
    iso3 = iso3_codes[0] if iso3_codes else ""
    section = section_hint or "overview"
    
    # Parse section parts
    section_parts = section.split('/')
    top_section = section_parts[0] if len(section_parts) > 0 else "overview"
    sub_section = section_parts[1] if len(section_parts) > 1 else ""
    
    # Build normalized payload
    payload = {
        "type": "country_profile",
        "iso3": [iso3],
        "country": country,
        "query": raw_query,
        "filters": {
            "section": top_section,
            "subsection": sub_section
        }
    }
    
    # Build frontend table
    table = {
        "columns": [
            {"key": "field", "title": "Field"},
            {"key": "value", "title": "Value"}
        ],
        "rows": [
            {"field": "Country", "value": country},
            {"field": "ISO3", "value": iso3},
            {"field": "Section", "value": top_section.replace('_', ' ').title()},
            {"field": "Subsection", "value": sub_section.replace('_', ' ').title() if sub_section else "All"},
            {"field": "Query", "value": raw_query}
        ]
    }
    
    return {
        "payload": payload,
        "table": table
    }
```

---

### 3.2 Legislation Composer

**Node ID:** `code_leg`

**Input Variables:**
- `targets` ← `{{ http_intent.data.targets }}`
- `iso3_codes` ← `{{ http_intent.data.iso3_codes }}`
- `domain` ← `{{ http_intent.data.domain }}`
- `section_hint` ← `{{ http_intent.data.section_hint }}`
- `raw_query` ← `{{ http_intent.data.query }}`

**Python Code:**
```python
def main(targets, iso3_codes, domain, section_hint, raw_query):
    # Normalize inputs
    country = targets[0] if targets else "Unknown"
    iso3 = iso3_codes[0] if iso3_codes else ""
    
    # Extract potential law keywords
    query_lower = raw_query.lower()
    law_type = "general"
    if "forest" in query_lower or "logging" in query_lower:
        law_type = "forestry"
    elif "land" in query_lower or "soil" in query_lower:
        law_type = "land_management"
    elif "water" in query_lower:
        law_type = "water_resources"
    
    # Build normalized payload
    payload = {
        "type": "legislation",
        "iso3": [iso3],
        "country": country,
        "query": raw_query,
        "filters": {
            "law_type": law_type,
            "keywords": [w for w in query_lower.split() if len(w) > 3][:5]
        }
    }
    
    # Build frontend table
    table = {
        "columns": [
            {"key": "field", "title": "Field"},
            {"key": "value", "title": "Value"}
        ],
        "rows": [
            {"field": "Country", "value": country},
            {"field": "ISO3", "value": iso3},
            {"field": "Law Type", "value": law_type.replace('_', ' ').title()},
            {"field": "Search Query", "value": raw_query}
        ]
    }
    
    return {
        "payload": payload,
        "table": table
    }
```

---

### 3.3 Commitment Composer

**Node ID:** `code_cmt`

**Input Variables:**
- `targets` ← `{{ http_intent.data.targets }}`
- `iso3_codes` ← `{{ http_intent.data.iso3_codes }}`
- `domain` ← `{{ http_intent.data.domain }}`
- `section_hint` ← `{{ http_intent.data.section_hint }}`
- `raw_query` ← `{{ http_intent.data.query }}`

**Python Code:**
```python
def main(targets, iso3_codes, domain, section_hint, raw_query):
    # Normalize inputs
    target = targets[0] if targets else "Unknown"
    
    # Detect if target is region or country
    region_keywords = ["mena", "ssa", "asia", "africa", "europe", "americas"]
    is_region = any(rk in target.lower() for rk in region_keywords)
    
    # Extract commitment type
    query_lower = raw_query.lower()
    commitment_type = "general"
    if "ndc" in query_lower or "nationally determined" in query_lower:
        commitment_type = "ndc"
    elif "restore" in query_lower or "restoration" in query_lower:
        commitment_type = "restoration"
    elif "sdg" in query_lower:
        commitment_type = "sdg"
    
    # Build normalized payload
    payload = {
        "type": "commitment",
        "scope": "region" if is_region else "country",
        "target": target,
        "iso3": iso3_codes if not is_region else [],
        "query": raw_query,
        "filters": {
            "commitment_type": commitment_type
        }
    }
    
    # Build frontend table
    table = {
        "columns": [
            {"key": "field", "title": "Field"},
            {"key": "value", "title": "Value"}
        ],
        "rows": [
            {"field": "Scope", "value": "Region" if is_region else "Country"},
            {"field": "Target", "value": target.title()},
            {"field": "ISO3", "value": ", ".join(iso3_codes) if iso3_codes else "N/A"},
            {"field": "Commitment Type", "value": commitment_type.upper()},
            {"field": "Query", "value": raw_query}
        ]
    }
    
    return {
        "payload": payload,
        "table": table
    }
```

---

## 4. Output JSON Schema

### 4.1 Stable Schema Definition

```json
{
  "title": "string",
  "meta": {
    "domain": "string",
    "section_hint": "string|null",
    "iso3": "string"
  },
  "table": {
    "columns": [
      {"key": "string", "title": "string"}
    ],
    "rows": [
      {"<column-key>": "any"}
    ]
  },
  "debug": {
    "payload": {}
  }
}
```

---

### 4.2 Example 1: Country Profile (Fires)

```json
{
  "title": "Country Profile: Saudi Arabia - Fires",
  "meta": {
    "domain": "country_profile",
    "section_hint": "stressors/fires",
    "iso3": "SAU"
  },
  "table": {
    "columns": [
      {"key": "field", "title": "Field"},
      {"key": "value", "title": "Value"}
    ],
    "rows": [
      {"field": "Country", "value": "saudi arabia"},
      {"field": "ISO3", "value": "SAU"},
      {"field": "Section", "value": "Stressors"},
      {"field": "Subsection", "value": "Fires"},
      {"field": "Query", "value": "Saudi Arabia wildfires"}
    ]
  },
  "debug": {
    "payload": {
      "type": "country_profile",
      "iso3": ["SAU"],
      "country": "saudi arabia",
      "query": "Saudi Arabia wildfires",
      "filters": {
        "section": "stressors",
        "subsection": "fires"
      }
    }
  }
}
```

---

### 4.3 Example 2: Legislation

```json
{
  "title": "Legislation: Ghana - Forestry",
  "meta": {
    "domain": "legislation",
    "section_hint": null,
    "iso3": "GHA"
  },
  "table": {
    "columns": [
      {"key": "field", "title": "Field"},
      {"key": "value", "title": "Value"}
    ],
    "rows": [
      {"field": "Country", "value": "ghana"},
      {"field": "ISO3", "value": "GHA"},
      {"field": "Law Type", "value": "Forestry"},
      {"field": "Search Query", "value": "Ghana logging law 2020"}
    ]
  },
  "debug": {
    "payload": {
      "type": "legislation",
      "iso3": ["GHA"],
      "country": "ghana",
      "query": "Ghana logging law 2020",
      "filters": {
        "law_type": "forestry",
        "keywords": ["ghana", "logging", "2020"]
      }
    }
  }
}
```

---

### 4.4 Example 3: Commitment (Region)

```json
{
  "title": "Commitment: MENA - Restoration",
  "meta": {
    "domain": "commitment",
    "section_hint": null,
    "iso3": ""
  },
  "table": {
    "columns": [
      {"key": "field", "title": "Field"},
      {"key": "value", "title": "Value"}
    ],
    "rows": [
      {"field": "Scope", "value": "Region"},
      {"field": "Target", "value": "Mena-Mena"},
      {"field": "ISO3", "value": "N/A"},
      {"field": "Commitment Type", "value": "RESTORATION"},
      {"field": "Query", "value": "MENA restoration commitments"}
    ]
  },
  "debug": {
    "payload": {
      "type": "commitment",
      "scope": "region",
      "target": "mena-mena",
      "iso3": [],
      "query": "MENA restoration commitments",
      "filters": {
        "commitment_type": "restoration"
      }
    }
  }
}
```

---

## 5. Variable Path Map (Copy-Ready)

### 5.1 HTTP Intent → Code Composer Inputs

| Code Input Variable | Dify Expression |
|---------------------|-----------------|
| `targets` | `{{ http_intent.data.targets }}` |
| `iso3_codes` | `{{ http_intent.data.iso3_codes }}` |
| `domain` | `{{ http_intent.data.domain }}` |
| `section_hint` | `{{ http_intent.data.section_hint }}` |
| `raw_query` | `{{ http_intent.data.query }}` |

---

### 5.2 Code Composer → Output JSON

| Output Field | Dify Expression (Country Profile) | Dify Expression (Legislation) | Dify Expression (Commitment) |
|--------------|-----------------------------------|-------------------------------|------------------------------|
| `title` | `Country Profile: {{ code_cp.data.payload.country }} - {{ code_cp.data.payload.filters.subsection }}` | `Legislation: {{ code_leg.data.payload.country }} - {{ code_leg.data.payload.filters.law_type }}` | `Commitment: {{ code_cmt.data.payload.target }} - {{ code_cmt.data.payload.filters.commitment_type }}` |
| `meta.domain` | `{{ http_intent.data.domain }}` | `{{ http_intent.data.domain }}` | `{{ http_intent.data.domain }}` |
| `meta.section_hint` | `{{ http_intent.data.section_hint }}` | `{{ http_intent.data.section_hint }}` | `{{ http_intent.data.section_hint }}` |
| `meta.iso3` | `{{ code_cp.data.payload.iso3[0] }}` | `{{ code_leg.data.payload.iso3[0] }}` | `{{ code_cmt.data.payload.iso3 | join(',') }}` |
| `table` | `{{ code_cp.data.table }}` | `{{ code_leg.data.table }}` | `{{ code_cmt.data.table }}` |
| `debug.payload` | `{{ code_cp.data.payload }}` | `{{ code_leg.data.payload }}` | `{{ code_cmt.data.payload }}` |

---

## 6. Optional HTTP Fetch Node

**Node ID:** `http_fetch`

**When to Use:** If you need to fetch additional data from an external API based on the composed payload.

**Method:** POST

**URL:** `https://your-data-api.com/fetch`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body (JSON - No Extra Quotes for Objects/Arrays):**

For Country Profile:
```json
{
  "type": "{{ code_cp.data.payload.type }}",
  "iso3": {{ code_cp.data.payload.iso3 }},
  "query": "{{ code_cp.data.payload.query }}",
  "filters": {{ code_cp.data.payload.filters }}
}
```

For Legislation:
```json
{
  "type": "{{ code_leg.data.payload.type }}",
  "iso3": {{ code_leg.data.payload.iso3 }},
  "query": "{{ code_leg.data.payload.query }}",
  "filters": {{ code_leg.data.payload.filters }}
}
```

For Commitment:
```json
{
  "type": "{{ code_cmt.data.payload.type }}",
  "scope": "{{ code_cmt.data.payload.scope }}",
  "target": "{{ code_cmt.data.payload.target }}",
  "iso3": {{ code_cmt.data.payload.iso3 }},
  "query": "{{ code_cmt.data.payload.query }}",
  "filters": {{ code_cmt.data.payload.filters }}
}
```

**Important:** Use `{{ ... }}` for arrays/objects directly without quotes to avoid double-serialization.

---

## 7. Acceptance Tests (End-to-End)

### Test 1: Saudi Arabia Wildfires

**Input:**
```
"Saudi Arabia wildfires"
```

**Slot Response (`/recognize/simple`):**
```json
{
  "targets": ["saudi arabia"],
  "domain": "country_profile",
  "section_hint": "stressors/fires",
  "iso3_codes": ["SAU"],
  "query": "Saudi Arabia wildfires"
}
```

**Branch Taken:**
- Domain Router → A (country_profile)
- Section Router → A1 (fires)

**Composer Output (`code_cp`):**
```json
{
  "payload": {
    "type": "country_profile",
    "iso3": ["SAU"],
    "country": "saudi arabia",
    "query": "Saudi Arabia wildfires",
    "filters": {
      "section": "stressors",
      "subsection": "fires"
    }
  },
  "table": {
    "columns": [
      {"key": "field", "title": "Field"},
      {"key": "value", "title": "Value"}
    ],
    "rows": [
      {"field": "Country", "value": "saudi arabia"},
      {"field": "ISO3", "value": "SAU"}
    ]
  }
}
```

**Final Output JSON:**
```json
{
  "title": "Country Profile: Saudi Arabia - Fires",
  "meta": {
    "domain": "country_profile",
    "section_hint": "stressors/fires",
    "iso3": "SAU"
  },
  "table": {
    "columns": [{"key": "field", "title": "Field"}, {"key": "value", "title": "Value"}],
    "rows": [
      {"field": "Country", "value": "saudi arabia"},
      {"field": "ISO3", "value": "SAU"},
      {"field": "Section", "value": "Stressors"},
      {"field": "Subsection", "value": "Fires"},
      {"field": "Query", "value": "Saudi Arabia wildfires"}
    ]
  },
  "debug": {"payload": {...}}
}
```

---

### Test 2: China Drought Trends

**Input:**
```
"China drought trends"
```

**Slot Response:**
```json
{
  "targets": ["china"],
  "domain": "country_profile",
  "section_hint": "stressors/climate_hazards",
  "iso3_codes": ["CHN"],
  "query": "China drought trends"
}
```

**Branch Taken:**
- Domain Router → A (country_profile)
- Section Router → A3 (climate_hazards)

**Composer Output:**
```json
{
  "payload": {
    "type": "country_profile",
    "iso3": ["CHN"],
    "country": "china",
    "query": "China drought trends",
    "filters": {
      "section": "stressors",
      "subsection": "climate_hazards"
    }
  },
  "table": {
    "rows": [
      {"field": "Country", "value": "china"},
      {"field": "ISO3", "value": "CHN"}
    ]
  }
}
```

**Final Output JSON:**
```json
{
  "title": "Country Profile: China - Climate Hazards",
  "meta": {"domain": "country_profile", "section_hint": "stressors/climate_hazards", "iso3": "CHN"},
  "table": {...},
  "debug": {...}
}
```

---

### Test 3: Ghana Logging Law 2020

**Input:**
```
"Ghana logging law 2020"
```

**Slot Response:**
```json
{
  "targets": ["ghana"],
  "domain": "legislation",
  "section_hint": null,
  "iso3_codes": ["GHA"],
  "query": "Ghana logging law 2020"
}
```

**Branch Taken:**
- Domain Router → B (legislation)

**Composer Output (`code_leg`):**
```json
{
  "payload": {
    "type": "legislation",
    "iso3": ["GHA"],
    "country": "ghana",
    "query": "Ghana logging law 2020",
    "filters": {
      "law_type": "forestry",
      "keywords": ["ghana", "logging", "2020"]
    }
  },
  "table": {
    "rows": [
      {"field": "Country", "value": "ghana"},
      {"field": "Law Type", "value": "Forestry"}
    ]
  }
}
```

**Final Output JSON:**
```json
{
  "title": "Legislation: Ghana - Forestry",
  "meta": {"domain": "legislation", "section_hint": null, "iso3": "GHA"},
  "table": {...},
  "debug": {...}
}
```

---

### Test 4: MENA Restoration Commitments

**Input:**
```
"MENA restoration commitments"
```

**Slot Response:**
```json
{
  "targets": ["mena-mena"],
  "domain": "commitment",
  "section_hint": null,
  "iso3_codes": [],
  "query": "MENA restoration commitments"
}
```

**Branch Taken:**
- Domain Router → C (commitment)

**Composer Output (`code_cmt`):**
```json
{
  "payload": {
    "type": "commitment",
    "scope": "region",
    "target": "mena-mena",
    "iso3": [],
    "query": "MENA restoration commitments",
    "filters": {
      "commitment_type": "restoration"
    }
  },
  "table": {
    "rows": [
      {"field": "Scope", "value": "Region"},
      {"field": "Target", "value": "Mena-Mena"},
      {"field": "Commitment Type", "value": "RESTORATION"}
    ]
  }
}
```

**Final Output JSON:**
```json
{
  "title": "Commitment: MENA - Restoration",
  "meta": {"domain": "commitment", "section_hint": null, "iso3": ""},
  "table": {...},
  "debug": {...}
}
```

---

## 8. Implementation Checklist

- [ ] Create Dify workflow with 7-8 nodes as diagrammed
- [ ] Configure HTTP Intent node with correct API endpoint
- [ ] Set up Domain Router with 3 branches (exact conditions from Section 2.1)
- [ ] Set up Section Sub-Router with 4 branches (exact conditions from Section 2.2)
- [ ] Create 3 Code nodes with templates from Section 3
- [ ] Configure variable mappings from Section 5
- [ ] Add optional HTTP Fetch node if external data needed
- [ ] Configure Output node with schema from Section 4
- [ ] Test all 4 acceptance test cases
- [ ] Verify JSON output matches expected schema

---

## 9. Notes & Constraints

1. **Do NOT modify slot filling logic** - Treat `/recognize/simple` as authoritative
2. **Keep code concise** - All templates ≤ 40 lines
3. **Use deterministic rules** - No LLM prompting in Code nodes
4. **JSON serialization** - Ensure all outputs are valid JSON
5. **Variable paths** - Copy expressions exactly as shown in Section 5
6. **Branch conditions** - Copy If/Else expressions exactly as shown in Section 2

---

**End of Specification**

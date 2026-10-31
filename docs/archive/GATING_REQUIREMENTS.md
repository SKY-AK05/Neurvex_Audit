# Gating Questions & N/A Requirements

## Status Summary

### ✅ COMPLETED
1. **Vertical segment numbering** - Instructions screen already shows segments in single column

### ⏳ TODO

#### 2. Gating Questions for Sections 4 & 8

**Section 4: Built Environment & Sensory**
- Gate question: "Does your organisation have physical workplace environments (e.g., offices, facilities, or on-site workspaces)?"
- Options: Yes / No
- Logic: If No → skip entire section, mark as N/A

**Section 8: Suppliers & Procurement** 
- Gate question: "Does your organisation have recurring engagement with external vendors, consultants, or partners?"
- Options: Yes / No
- Logic: If No → skip entire section, mark as N/A

**Implementation approach:**
```js
// Add to sections[3] and sections[7]:
{
  gatingQuestion: "Does your organisation have physical workplace environments...",
  gatingField: "has_physical_workspace", // or "has_supplier_engagement"
  questions: [...]
}

// In form reactive state:
has_physical_workspace: "",
has_supplier_engagement: "",

// In template - show gating question first, then questions only if gate = "Yes"
// Track skipped sections in Set for backend
const skippedSections = ref(new Set());
```

#### 3. Section 7 Q37 - Add "N/A" option

**Question 37 (q37)**: "Physical customer environments are designed or adapted to reduce sensory overload..."

Change options from `["Yes", "Partially", "No", "Not Sure"]` to `["Yes", "Partially", "No", "Not Sure", "N/A"]`

**Implementation**: Add `allowNA: true` flag to q37, check in template and show 5 options instead of 4.

#### 4. Section 8 Header Text

Add before Section 8 questions:

> **Suppliers refer to any external individuals or organisations your organisation engages with, including consultants, freelancers, technology providers, agencies, partners, service providers and contractors.**

Style: Light grey background banner with italic text

#### 5. Backend Scoring Logic (comments only)

```js
// In submit():
// - Sections in skippedSections Set should be marked "Not Applicable"
// - Section 7: if q37 = "N/A", rescale from /16 to /20
//   Example: if score = 10/16, final = (10/16) * 20 = 12.5/20
```

## Files to Modify

1. `frontend/src/views/AuditForm.vue` - Add gating logic, N/A option, section header
2. `app/services/scoring_service.py` - Handle N/A rescaling logic
3. `app/models/audit.py` - Store skipped sections metadata

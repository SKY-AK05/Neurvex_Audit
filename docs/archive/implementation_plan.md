# "Not Sure" Interpretation Logic

This plan outlines how we will update the system so that answering "Not Sure" flags an awareness gap rather than just scoring zero like a "Not Done" answer.

## Proposed Changes

### 1. Backend Scoring Logic (`app/services/scoring_service.py`)
- **Count "Not Sure" Answers:** When calculating the score for a section, the system will count how many times the user answered "Not Sure".
- **Determine Majority:** If the majority of answers (e.g., 3 out of 5) in a section are "Not Sure", the section will be flagged internally as a **"Low Visibility Area"**.
- **Return Internal Flag:** The final API response will include a new list of `low_visibility_sections` that consultants can see in the admin dashboard later.

### 2. Email Report Generation (`app/services/scoring_service.py`)
- **Override Commentary:** If a section is flagged as "Low Visibility", the email report will ignore the standard score-based commentary (like "Foundational" or "Early Progress"). 
- Instead, it will display your custom text: *"Responses in some areas indicate limited visibility into practices, which may suggest the need for greater communication or cross-functional awareness."*
- **Update Badge:** The section badge in the email will say **"LOW VISIBILITY"** in a neutral gray color to clearly distinguish it from a poor performance score.

## Open Questions
> [!IMPORTANT]
> - Is "majority" defined as strictly more than half (e.g., 3 out of 5 questions)? 
> - If a section is flagged as "Low Visibility", should we still show them their numerical score out of 20 for that section, or should we hide the score for that specific section?

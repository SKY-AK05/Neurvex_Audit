# NIWI Founder-Approved Feedback — Problem & Suggested Solution Review

## Purpose

This document consolidates the **14 straightforward, founder-approved feedback items** identified from the NIWI feedback/action register. It is intended for a coding agent to **investigate the current implementation and propose solutions only**.

### Workflow / guardrails
1. Locate and understand each item in the current codebase.
2. Verify the reported problem and identify the exact relevant UI, question, component, data, or flow.
3. Recommend a solution for each item, including files/components likely affected, risks, and verification steps.
4. **Do not change code, files, database records, migrations, configuration, or production behavior.**
5. Return the findings in chat, item by item. We will review and approve the proposed solutions before asking for implementation.

---

## 1. NIWI-001 — Add a source for the neurodivergence statistic

**Initial user problem / observation**  
The landing page shows a statistic about neurodivergence without a visible source or publication year. Users may question its credibility or want to verify it.

**Initial user suggestion**  
Add a short source citation or clickable reference alongside the statistic.

**Founder-approved suggestion / exact content**  
Revise the intro to:

> An estimated 15–20% of people are neurodivergent, including people with autism, ADHD, dyslexia and other neurological differences.

Immediately underneath, in smaller text:

> Source: Doyle, N. (2020), British Medical Bulletin.

**Agent investigation request**  
Find where this statistic and introduction are rendered. Recommend the cleanest accessible way to add the source line, including mobile layout and link/citation treatment (if a URL is available and verified). Do not invent a source URL.

---

## 2. NIWI-011 — Clarify that neurodivergence can be diagnosed or self-identified

**Initial user problem / observation**  
The demographic question does not clearly indicate whether a formal diagnosis is required. This may make people who self-identify unsure whether they can answer.

**Initial user suggestion**  
Add brief helper text explaining that a formal diagnosis is not required.

**Founder-approved suggestion / exact content**  
Revise the line to:

> Neurodivergent may include ADHD, autism, dyslexia, dyspraxia, and other cognitive or neurological differences, whether formally diagnosed or self-identified.

**Agent investigation request**  
Locate the exact question/helper text and identify the safest place to replace or add this wording. Check for consistency with the form's existing wording and avoid changing unrelated demographic logic.

---

## 3. NIWI-012 — Make the underrepresented-community question clearer

**Initial user problem / observation**  
The question is broad and combines several concepts. Participants may be unsure which communities are included or how to interpret it.

**Initial user suggestion**  
Make the question more direct and provide one or two brief examples. Avoid a long list of communities.

**Founder-approved suggestion / exact content**  
Revise the question to:

> Do you identify as belonging to a community that has historically experienced underrepresentation or exclusion?*

Then add:

> This may relate to socioeconomic background, ethnicity, religion, caste, sexual orientation, gender identity, or other aspects of identity or background.

**Agent investigation request**  
Locate this question and its supporting text. Recommend how to present the question and explanation so it remains readable, clear, and consistent with the form's privacy/demographic conventions.

---

## 4. NIWI-013 — Make consent wording accurately describe collected information

**Initial user problem / observation**  
The consent statement refers to organisational data, while the form also collects personal and demographic information. The wording may not clearly explain what the participant is consenting to.

**Initial user suggestion**  
Use wording that clearly reflects the information entered in the form rather than referring only to organisational data.

**Founder-approved suggestion / exact content**  
Revise the consent statement to:

> I consent to the collection and processing of the information I provide as part of the NIWI assessment, in accordance with the Privacy Policy.*

**Agent investigation request**  
Locate the consent statement and related Privacy Policy reference. Recommend the exact text placement and check that the consent interaction remains unchanged unless a change is explicitly proposed and approved.

---

## 5. NIWI-016 — Add “How to respond” guidance before the audit

**Initial user problem / observation**  
Participants may not know how to interpret the Yes, Partially, No, and Not sure response options.

**Initial user suggestion**  
Provide brief explanation/help text for how to choose each response.

**Founder-approved suggestion / exact content**  
Add this guidance where the different response options are explained before the audit starts:

> **How to respond**  
> For each statement, select the option that best reflects your organisation today:
>
> **Yes:** All or most aspects are consistently in place.  
> **Partially:** Some aspects are in place, or they are not consistently applied.  
> **No:** Few or none of the aspects are in place.  
> **Not sure:** I don't have enough visibility to assess this.

**Agent investigation request**  
Find the pre-assessment explanation/instructions area. Recommend a clear, accessible presentation for the guidance, without duplicating it unnecessarily across every question or changing scoring.

---

## 6. NIWI-026 — Clarify physical-workplace eligibility

**Initial user problem / observation**  
The eligibility wording may be unclear about whether an organisation must simply have physical workplaces or provide/manage spaces where employees regularly work.

**Initial user suggestion**  
Revise the eligibility question so the intended scope is clearer.

**Founder-approved suggestion / exact content**  
Replace:

> Does your organisation have physical workplace environments (e.g., offices, facilities, or on-site workspaces)?

With:

> Does your organisation provide or manage physical workplace environments where employees regularly work (e.g., offices, facilities, or on-site workspaces)?

**Agent investigation request**  
Locate the Section 4 eligibility question and its gating logic. Recommend a text-only update and confirm that the existing eligibility/gating behavior should remain intact.

---

## 7. NIWI-028 — Clarify the sensory-barriers question (Q20)

**Initial user problem / observation**  
The current wording may suggest that remote or hybrid work is the main solution to sensory inclusion, rather than addressing sensory barriers in physical workplaces.

**Initial user suggestion**  
Make it clear that the organisation should address sensory barriers within physical workplaces.

**Founder-approved suggestion / exact content**  
Revise Section 4, Q20 to:

> Our organisation addresses sensory barriers within physical workplaces rather than relying on remote or hybrid work as the primary solution for inclusion.

**Agent investigation request**  
Find Q20 and determine where the wording is defined/rendered. Recommend the minimal change and check whether question IDs, answer options, scoring, or stored responses are affected.

---

## 8. NIWI-029 — Clarify inclusive leadership behavior (Q21)

**Initial user problem / observation**  
The question should assess managers' inclusive leadership training and day-to-day application more clearly.

**Initial user suggestion**  
Reword it to focus on trained managers/team leads applying inclusive leadership in daily management.

**Founder-approved suggestion / exact content**  
Revise Section 5, Q21 to:

> Managers and team leads are trained on inclusive leadership practices and apply them in their day-to-day management.

**Agent investigation request**  
Locate Q21 and recommend the minimal wording update. Check for impact on question identity, scoring, stored answers, reports, or evaluation logic.

---

## 9. NIWI-032 — Clarify feedback collection and action (Q30)

**Initial user problem / observation**  
The existing question may not clearly describe structured feedback collection, review, and action across employees and external stakeholders.

**Initial user suggestion**  
Make the question explicitly cover collecting, reviewing, and acting on feedback.

**Founder-approved suggestion / exact content**  
Revise Q30 to:

> Our organisation has structured mechanisms to collect, review and act on feedback from employees and external stakeholders on communication and accessibility.

**Agent investigation request**  
Locate Q30. Recommend the wording change and verify that the question's scoring, ID, response schema, and downstream reporting are unaffected.

---

## 10. NIWI-033 — Clarify neuro-inclusive design across products/services/channels (Q31)

**Initial user problem / observation**  
The existing question may be interpreted too narrowly or ambiguously. It should clearly include the organisation's products, services, and customer communication channels.

**Initial user suggestion**  
Simplify and clarify the wording while explicitly naming the range of channels.

**Founder-approved suggestion / exact content**  
Revise Q31 to:

> The organisation applies clear, structured and neuro-inclusive design principles across all its products, services and customer communication channels, including websites, digital platforms, social media and physical materials.

**Agent investigation request**  
Locate Q31 and recommend the minimal text change. Identify any possible effects on the question's ID, scoring, stored answers, reports, or validation.

---

## 11. NIWI-036 — Clarify supplier eligibility and definition

**Initial user problem / observation**  
The eligibility question refers to recurring engagement, while the supporting instruction says even occasional engagement makes the section applicable. These statements provide different criteria.

**Initial user suggestion**  
Make the eligibility question and supporting instruction consistent; broaden it to include occasional engagement if that is the intended scope.

**Founder-approved suggestion / exact content**  
For Section 8 eligibility, revise the question/instruction as follows:

> Does your organisation engage with external suppliers?

Below it, add:

> Suppliers refer to external individuals or organisations that provide products or services to your organisation, including consultants, freelancers, technology providers, agencies, service providers and contractors.

**Agent investigation request**  
Find Section 8's eligibility question, helper text, and supplier section gating logic. Recommend the minimal text update and verify that the gating behavior remains unchanged.

---

## 12. Roshan — Recommendation 1: Manager/HR training and tailored workplace adjustments (Q13)

**Initial user problem / observation**  
The assessment should better recognize individual differences and whether accommodations are tailored to individual needs, rather than assuming one-size-fits-all support.

**Initial user suggestion**  
Review whether managers, HR, and people teams receive training and are equipped to identify, discuss, and implement workplace adjustments based on individual needs.

**Founder-approved suggestion / exact content**  
Revise Q13 to:

> Managers, HR, and people teams receive training on neurodiversity and are equipped to identify, discuss, and implement workplace adjustments tailored to individual needs.

**Agent investigation request**  
Locate the referenced Q13 and recommend the minimal wording update. Confirm the exact question reference/section in the code and flag any mismatch before proposing a change. Check downstream scoring/report effects.

---

## 13. Roshan — Recommendation 2: Structured communication and clarity (Q27)

**Initial user problem / observation**  
Instructions, expectations, feedback, and deadlines may not be communicated clearly, consistently, and in a structured way. This can create ambiguity for employees.

**Initial user suggestion**  
Assess whether workplace communication is clear, consistent, and structured.

**Founder-approved suggestion / exact content**  
Revise Q27 to:

> Instructions, expectations, feedback and deadlines are communicated clearly, consistently and in a structured way to reduce ambiguity and support different information-processing needs.

**Agent investigation request**  
Locate Q27 and recommend the minimal wording update. Check for question identity, scoring, answer storage, and report impact.

---

## 14. Roshan — Recommendation 4: Psychological safety (Q5)

**Initial user problem / observation**  
The assessment should capture whether employees feel safe raising concerns, discussing needs, asking for support, and making mistakes without fear of negative consequences.

**Initial user suggestion**  
Include psychological safety as a workplace inclusion dimension.

**Founder-approved suggestion / exact content**  
Revise Section 1, Q5 to:

> Employees feel safe to raise concerns, discuss their needs and ask for support without fear of negative consequences.

**Agent investigation request**  
Locate Section 1, Q5 and recommend the minimal wording update. Check for scoring, IDs, answer persistence, and report implications.

---

# Expected agent response format

For each of the 14 items, return:

1. **Current implementation found** — exact file/component/question and current text or behavior.
2. **Problem confirmed?** — yes/no/partially, with evidence.
3. **Recommended solution** — concise and specific.
4. **Impact/risk** — frontend, database/migration, scoring, validation, reporting, accessibility, or none.
5. **Verification plan** — how the change would be tested.
6. **Unknowns / questions** — anything that must be clarified before implementation.

## Final constraint

**This is a research/review task only. Do not implement any changes. Do not modify the codebase. Do not create migrations. Do not change question data. Report all recommendations in chat and wait for approval.**

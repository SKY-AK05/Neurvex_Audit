# Design system

| Setting | Value |
| --- | --- |
| Mode | `preserve` |
| Level | `complex` |
| Fidelity | `embed` |
| Generated with | `reconstruct@2.29.16` |

The Neuro-Inclusive Workplace Index design system embodies clarity, calming sensory balance, and high accessibility. The palette utilizes grounding deep navy, calming teal accents, and warm cream surfaces designed to reduce visual fatigue for neurodivergent respondents.

## Design-system source files

- `frontend/src/style.css`

## Design tokens

### Core Color Palette

| Token | CSS Variable | Hex / Value | RGB Equivalent | Purpose |
| --- | --- | --- | --- | --- |
| Primary Deep Navy | `--primary` | `#161057` | `22, 16, 87` | Brand anchor, headings, main contrast |
| Primary Dark Hover | `--primary-hover` | `#0F0A42` | `15, 10, 66` | Pressed & hover states on primary elements |
| Accent Teal | `--accent` | `#04907C` | `4, 144, 124` | Primary CTAs, active selections, focus rings |
| Accent Hover | `--accent-hover` | `#037A69` | `3, 122, 105` | Button hover state |
| Accent Soft | `--accent-soft` | `rgba(4, 144, 124, 0.08)` | — | Badge fills, active radio backgrounds |
| Danger Coral | `--danger` | `#E05A47` | `224, 90, 71` | Destructive actions, validation errors |
| Danger Hover | `--danger-hover` | `#C53030` | `197, 48, 48` | Danger button hover |
| Danger Soft | `--danger-soft` | `#FEE2E2` | — | Error alerts and input invalid backgrounds |
| Warning Amber | `--warning` | `#D97706` | `217, 119, 6` | Attention banners, dead-letter warnings |
| Warning Soft | `--warning-soft` | `#FEF3C7` | — | Warning alert containers |
| Success Emerald | `--success` | `#059669` | `5, 150, 105` | Form completion, confirmed statuses |
| Success Soft | `--success-soft` | `#D1FAE5` | — | Success badges, toast backgrounds |
| Canvas Background | `--bg` | `#FAFAF8` | — | Calming, warm off-white canvas |
| Cream Accent BG | `--bg-cream` | `#FAF9F5` | — | Survey card background |
| Surface White | `--surface` | `#FFFFFF` | — | Card surfaces, modal sheets |
| Surface Subtle | `--surface-alt` | `#F8FAFC` | — | Table headers, secondary containers |
| Border Standard | `--border` | `rgba(22, 16, 87, 0.10)` | — | Default card and input borders |
| Border Strong | `--border-strong` | `rgba(22, 16, 87, 0.20)` | — | Hover borders, active dividers |
| Border Light | `--border-light` | `#E2E8F0` | — | Table row dividers |
| Text Primary | `--text-main` | `#1E293B` | — | High-contrast body text (meets AAA) |
| Text Muted | `--text-muted` | `#64748B` | — | Helper text, secondary labels |
| Text Subtle | `--text-subtle` | `#94A3B8` | — | Disabled labels, placeholder text |

### Elevation & Shadows

- `--shadow-sm`: `0 1px 3px rgba(22, 16, 87, 0.04)` (subtle cards, pills)
- `--shadow-md`: `0 4px 14px rgba(22, 16, 87, 0.06)` (interactive cards, dropdown menus)
- `--shadow-lg`: `0 8px 24px rgba(22, 16, 87, 0.09)` (modals, floating drawers)
- `--shadow-card`: `0 2px 10px rgba(22, 16, 87, 0.03)` (survey question cards)

### Radii

- `--radius-sm`: `6px` (buttons, inputs, badges)
- `--radius-md`: `10px` (cards, containers)
- `--radius-lg`: `14px` (survey sections, banners)
- `--radius-xl`: `18px` (modal dialogs)
- `--radius-full`: `9999px` (circular pills, avatars)

## Theming

- Default mode is **Warm Light Canvas** (`:root` scoped in `frontend/src/style.css`).
- High-contrast mode activates automatically via standard CSS variables when `@media (forced-colors: active)` is detected.
- All colors are expressed as semantic CSS variables (`var(--primary)`, `var(--accent)`, `var(--bg)`), allowing client white-labeling and dark mode customization by overriding `:root` or setting `data-theme="dark"`.

## Typography

- **Headings Font:** `'Fraunces', Georgia, serif`
  - Font weight: 700 (Bold)
  - Letter spacing: `-0.015em`
  - Usage: H1 page headers, section titles, maturity score numbers
- **Body Font:** `'Geist', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
  - Font weights: 400 (Regular), 500 (Medium), 600 (Semi-bold)
  - Line height: `1.5` (optimal for readability and cognitive ease)
  - Usage: Survey questions, instructions, table text, form inputs
- **Monospace Font:** `'Geist Mono', 'SFMono-Regular', Consolas, monospace`
  - Usage: Tokens, IDs, API payloads, timestamps

## Breakpoints & responsive

- Mobile viewport: `< 640px` (stacked questions, full-width buttons, collapsible side drawer)
- Tablet viewport: `640px – 1023px` (2-column layout, compact charts)
- Desktop viewport: `1024px – 1279px` (standard desktop container max-width: 1200px)
- Wide Desktop viewport: `>= 1280px` (centered dashboard with persistent sidebar)

## Iconography

- Icon Library: `lucide-vue-next` (Lucide Icons).
- Stroke convention: `2px` stroke width, geometric line style.
- Sizing scale: `16px` (inline button), `20px` (navigation, inputs), `24px` (header, cards).

## Motion & animation

- Transitions: `all 0.2s cubic-bezier(0.16, 1, 0.3, 1)` (smooth, natural deceleration curve without abrupt snapping).
- Prefers Reduced Motion:
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  ```

## Component library

| Component | Source | Variants | States |
| --- | --- | --- | --- |
| **Button** | `.btn` in `style.css` | `.btn-primary`, `.btn-outline`, `.btn-danger`, `.btn-secondary` | default, hover, focus-visible, active, disabled, loading |
| **LikertRadioGroup** | `AuditForm.vue` | 5-point scale (1: Strongly Disagree to 5: Strongly Agree) | default, checked, hover, focus, disabled |
| **QuestionCard** | `AuditForm.vue` | Standard question, demographic input, optional comment | default, answered, active, error |
| **RadarChart** | `Analytics.vue` | 8-pillar organizational radar chart (0–20 scale) | default, hover tooltip, animated render |
| **ProgressBar** | `AuditForm.vue` | Linear progress percentage bar (0–100%) | active, completed |
| **ToastNotification**| `App.vue` | Info, Success, Warning, Error | enter, visible, exit |
| **ModalDialog** | `AdminLogin.vue` | Centered confirmation modal, full-screen mobile sheet | hidden, open, focus-trapped |
| **DataTable** | `Submissions.vue` | Sortable, paginated audit submissions table | loading skeleton, populated, empty state |

## Accessibility

- **Target:** WCAG 2.1 Level AA conformance.
- **Color Contrast:** All body text (`#1E293B`) against canvas (`#FAFAF8`) exceeds 7:1 contrast ratio (AAA standard).
- **Keyboard Navigation:** Full survey can be completed using only the keyboard:
  - `Tab` / `Shift+Tab`: Navigate between question inputs and action buttons.
  - `Arrow Left` / `Arrow Right`: Toggle Likert scale ratings (1 to 5).
  - `Enter` / `Space`: Confirm selection and advance stepper.
- **Focus Management:** Distinct focus indicator: `outline: 2px solid var(--accent); outline-offset: 2px;`.
- **Screen Reader Support:** Accessible ARIA attributes: `role="radiogroup"`, `aria-checked`, `aria-required="true"`, `aria-describedby` linking helper instructions to inputs.

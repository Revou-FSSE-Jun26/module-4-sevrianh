# Sevy — Product & Web UI Design Guidelines

> **Purpose:** Define how Sevy's product interface and public-facing webpages should look, feel, and behave. This document describes the experience and page-level design decisions. The canonical values and component specifications live in [`design-system-sevy.md`](./design-system-sevy.md).

---

## 1. Product Design Direction

### Product character

Sevy is a visual team task-management product. Its interface should make shared work easy to understand: teams organize work on boards, columns, and cards, then move work forward with minimal friction.

The visual identity is **calm, clear, friendly, and quietly expressive**. It should feel like a considered productivity tool rather than a playful toy or a heavy enterprise suite.

### Experience principles

- **Board-first clarity:** Boards, columns, and cards are the primary product metaphors. Preserve their visual hierarchy.
- **Calm productivity:** Use generous spacing, restrained color, and clear typography to reduce cognitive load.
- **One clear next action:** Use the primary color sparingly so the most important action is immediately recognizable.
- **Flat by default:** Separate resting surfaces with background tone and borders. Reserve shadows for elements that float above the page.
- **Friendly, not decorative:** Use the Sevy gradient as a brand accent, not as a replacement for readable surfaces or functional state colors.
- **Consistent interaction:** Hover, focus, active, selected, disabled, loading, and error states must be predictable across the product.

### Mood

- Calm and optimistic
- Organized and approachable
- Modern, light, and quietly colorful
- Efficient without feeling sterile
- Confident without enterprise heaviness

### Density

Use **medium-to-compact application density**. Task boards need enough information to support scanning, but cards, controls, and metadata must remain legible. Public marketing pages may use more generous spacing and larger typography than the in-product workspace.

---

## 2. Brand Color Direction

### Palette concept

The supplied Sevy palette image moves from periwinkle and cornflower blue through cool sky blue, cyan, pale mint, and near-white. It communicates clarity, momentum, and a calm sense of progress.

Use this gradient as a **brand atmosphere** in limited, intentional places:
- Marketing hero backgrounds and selected promotional sections
- Small decorative glows or ambient background treatments
- Brand illustrations and visual storytelling
- Optional, restrained accent treatments around product previews

Do not use the gradient as the default background for the application, task cards, forms, menus, or data-heavy regions.

### Functional color hierarchy

The Sevy HTML design system is the implementation source of truth for named color tokens and exact values.

| Role | Direction | Application |
|---|---|---|
| Primary action | Cornflower blue `#6D7BEC` | Main CTA, selected controls, active navigation, focus |
| Primary hover | Vibrant blue `#5876EC` | Hover state for primary controls |
| Primary active | Deep blue `#455BCA` | Pressed/active state |
| Soft primary | Ice/periwinkle tints | Selected cards, subtle information backgrounds |
| Canvas | Warm alabaster `#F1EFEB` | Main application page background |
| Surface | White `#FFFFFF` | Cards, inputs, navigation, dialogs |
| Inset surface | Off-white mint `#F2FAF5` | Columns, subdued regions, control backgrounds |
| Text | Deep charcoal `#1F2430` | Primary text |
| Secondary text | `#4F586A` | Supporting copy and metadata |
| Borders | Warm neutral `#E5E1DA` | Card boundaries, separators |
| Semantic colors | Green, amber, red | Success, warning, and destructive/error feedback |

### Color rules

1. Use one dominant primary action in each local region.
2. Keep body text on neutral or white surfaces; do not place long copy over saturated gradients.
3. Use pastel label backgrounds with darker paired foreground colors.
4. Never communicate status through color alone. Include text, an icon, or another clear cue.
5. Preserve semantic meaning: green for success, amber for warning, and red for destructive/error states.
6. Avoid introducing Trello blue, Trello purple, or unrelated palette values as alternate brand colors.
7. Do not invent new color tokens in page-level CSS. Add or change tokens only in `design-system-sevy.md` and keep both documents synchronized.

---

## 3. Typography & Content

### Typography

Use **Inter** throughout the product, with weights 400, 500, and 600. Keep typography compact and highly legible.

| Use | Size / line height | Weight |
|---|---:|---:|
| Marketing display | 30 / 36 px | 600 |
| Page title (H1) | 24 / 32 px | 600 |
| Section title (H2) | 20 / 28 px | 600 |
| Subsection / card heading (H3) | 16 / 24 px | 600 |
| Body and controls | 14 / 20 px | 400 |
| Strong body / labels | 14 / 20 px | 500 |
| Caption / metadata | 12 / 16 px | 400 |

The marketing website may use larger display typography when the layout needs a stronger hero hierarchy, but it must remain consistent with Inter and the same restrained typographic character. Do not import a separate display font without updating the canonical system.

### Writing style

- Use sentence case for headings, labels, buttons, and navigation.
- Prefer concise, action-oriented language.
- Use verbs for buttons: “Create board”, “Add card”, “Save changes”.
- Keep labels and helper text specific.
- Explain errors in plain language and include a recovery action when possible.
- Avoid unnecessary all-caps labels, decorative copy, and vague actions such as “Submit” when a more specific verb is available.

---

## 4. Webpage & Application Layout

### Application shell

- Use a compact top navigation bar with a standard height of **56px**.
- Keep the main workspace aligned to a clear content grid.
- Use a warm-alabaster canvas with white surfaces and subtle inset regions.
- Preserve clear separation between global navigation, page context, board content, and overlays.
- Avoid adding decorative sections that compete with the task-management workflow.

### Board layout

- Use horizontal board scrolling when columns exceed the available viewport.
- The board itself scrolls horizontally; the page should not become an accidental horizontal-scrolling surface.
- Standard column width: **288px**.
- Standard gap between columns: **16px**.
- Use the inset surface for column backgrounds and white bordered surfaces for task cards.
- Keep column headings, card counts, card actions, and add-card affordances easy to scan.
- Preserve drag-and-drop affordances and a clear drop placeholder.

### Marketing and informational webpages

Public-facing pages may be more expressive than the application workspace while remaining recognizably Sevy.

- Use the supplied gradient as a restrained hero or section atmosphere.
- Keep headline and body copy on high-contrast, readable areas.
- Use white or neutral content surfaces for feature explanations, screenshots, and product demonstrations.
- Present the product through real board, column, and card metaphors rather than generic abstract business illustrations.
- Use a clear page hierarchy: hero, product proof/demo, feature explanation, supporting details, and a focused CTA.
- Keep navigation and primary CTA visually obvious.
- Do not turn every section into a gradient panel or floating card.

### Spacing

Use a **4px spacing grid**. The canonical spacing scale is defined in `design-system-sevy.md`. Use 8px for compact internal gaps, 16px for standard component spacing, 24px for card padding/related groups, and 32–48px for larger module separation.

Whitespace should support scanning and task focus, not create unnecessary empty space inside dense work surfaces.

---

## 5. Components & Interaction Patterns

Use the component specifications in [`design-system-sevy.md`](./design-system-sevy.md). The following rules describe how components work together.

### Buttons

- One primary button per local action region.
- Primary buttons use the Sevy primary color.
- Secondary buttons use a white surface and visible neutral border.
- Ghost buttons are for low-emphasis actions.
- Destructive buttons use the semantic danger color.
- Use clear verbs and provide accessible names for icon-only buttons.
- Support small, medium, and large sizes as defined by the system.

### Forms

- Place labels above their controls.
- Use consistent field heights, border radii, and spacing.
- Provide helper text where clarification is needed.
- Show errors with both a semantic border/color and explanatory text; never rely on color alone.
- Focus must be clearly visible and keyboard accessible.
- Disabled controls must look disabled and must not imply that they are interactive.

### Labels, badges, and avatars

- Use soft pastel label pairs for categories and task classification.
- Use status badges for workflow state, with readable text and optional status dots.
- Keep badge and label colors consistent with their semantic mapping.
- Avatars should support the standard 24px, 32px, and 40px sizes and stacked groups.

### Task cards

- Resting cards use a white surface, 1px border, and 8px radius.
- Hover changes the border, not the entire visual language.
- Selected cards use a subtle primary tint and primary border.
- Dragging may use a slight tilt and overlay shadow; this is the deliberate exception to the flat resting-card rule.
- Keep labels, due dates, assignees, comments, and checklist metadata compact and scannable.

### Overlays and feedback

- Modals, menus, and toasts float above the page and may use the defined overlay shadow.
- Modal backdrops use a solid ink tint; do not add backdrop blur by default.
- Menus and popovers must have clear boundaries and keyboard/focus behavior.
- Banners and toasts must communicate success, information, warning, or error through text as well as color.

---

## 6. Elevation & Surface Hierarchy

Sevy is **flat by default**.

1. **Canvas:** warm neutral page background.
2. **Inset:** subdued mint-tinted regions such as board columns.
3. **Surface:** white cards, controls, navigation, and content panels separated by a 1px border.
4. **Overlay:** menus, dialogs, and toasts above the page; use the canonical overlay shadow.

Do not add persistent shadows to ordinary cards, columns, or panels. Do not use gradients as a substitute for elevation or hierarchy.

---

## 7. Responsive Behavior

Use the breakpoints and component-specific behavior in `design-system-sevy.md`.

- **Wide desktop:** Show the full workspace and board columns; keep content aligned and avoid excessive page width.
- **Tablet:** Reduce multi-column marketing layouts and keep board previews compact. Board columns may continue to scroll horizontally.
- **Mobile:** Stack page sections, use full-width content, and preserve usable controls. Keep the board horizontally scrollable rather than squeezing columns until cards become unreadable.
- Hide or collapse secondary navigation and search when space is constrained, while keeping core navigation and primary actions accessible.
- Avoid tiny compressed board previews; prefer horizontal scrolling or a focused single-column view.
- Respect `prefers-reduced-motion`.

---

## 8. Accessibility & Usability

- Maintain readable contrast for text, controls, labels, and focus indicators.
- Ensure every interactive control is keyboard reachable and has a visible focus state.
- Provide accessible names for icon-only buttons and meaningful labels for form controls.
- Pair color with text or icons for status and validation.
- Preserve logical heading order and semantic page landmarks.
- Make hover-only information available through focus or another accessible interaction.
- Keep touch targets comfortable and avoid relying on precision gestures alone.
- Honor reduced-motion preferences.

---

## 9. Do / Don't

### Do

- Use the Sevy blue-to-mint palette with restraint.
- Keep functional UI surfaces neutral, bordered, and flat.
- Make boards, columns, and cards visually obvious.
- Use one primary action per region.
- Use semantic pastel label pairs with dark, readable text.
- Reserve shadows for overlays and the dragging state.
- Keep responsive boards horizontally scrollable.

### Don't

- Do not retain Trello-specific branding, colors, typography, or visual language.
- Do not use the gradient as the default app background or for every CTA.
- Do not add shadows to resting cards and columns.
- Do not introduce competing primary buttons.
- Do not use saturated label fills or gradients for task status.
- Do not compress board columns to fit a small screen.
- Do not create one-off component styles that conflict with the canonical design system.

---

## 10. Implementation Contract

- `design-system-sevy.md` is the **single source of truth** for tokens, component dimensions, states, and responsive breakpoints.
- This `DESIGN.md` is the **experience and page-layout guide**. It must not redefine token values.
- If a component or token changes, update the design system first, then update any affected guidance here.
- Use the existing CSS custom properties rather than hard-coded color values.
- Keep design decisions consistent across the marketing website, authentication screens, workspace, boards, and dialogs.
- When a requirement is not defined in either document, choose the simplest accessible solution that preserves Sevy's calm, flat, board-first visual language.

# 04 — HTML, CSS/SASS/LESS and Browser Rendering

> **How to use this file:** the spec lists "HTML/CSS/SASS/LESS + browser rendering". For someone who owns a shared component library and holds Design Authority, interviewers will probe three things: (1) **accessibility and semantics** — can your library be trusted to be accessible by default; (2) **CSS architecture at scale** — specificity, encapsulation, theming, how consumers customise components without `::ng-deep` and `!important` wars; (3) **rendering performance** — can you explain *why* something is slow (layout, paint, long tasks) and connect it to Core Web Vitals. Lead with the mechanism, then "in our library we…". Short answers here should still name the trade-off.

---

## A. Most commonly asked questions

### Q1. Why does semantic HTML matter, and what are the landmarks you use?

**Answer (1–2 min):**
- Semantics give the browser and assistive tech **meaning for free**: roles, names, states, keyboard behaviour, focusability, form submission, reader mode, SEO.
- **Landmarks:** `<header>` (banner, when top-level), `<nav>`, `<main>` (one per page), `<aside>` (complementary), `<footer>` (contentinfo, when top-level), `<form>`/`<section>` become landmarks only when they have an accessible name (`aria-labelledby`). Screen-reader users jump between landmarks — it's their table of contents.
- **Headings:** one logical outline — `h1` for the page/view title, don't skip levels for styling (style with classes). Screen-reader users navigate by headings more than anything else. In a component library, a card/dialog component shouldn't hard-code `<h2>` — let the consumer set the level (e.g. a `headingLevel` input) because the component doesn't know where it sits in the outline.
- **`<button>` vs `<div (click)>`:** a button is focusable, activates on Enter **and** Space, exposes `role=button`, supports `disabled`, and submits forms (`type="submit"` is the default inside a form — set `type="button"` explicitly in library components). A `div` needs `role`, `tabindex="0"`, key handlers for Enter/Space and disabled logic to approach that — and usually gets something wrong. Links (`<a href>`) navigate; buttons act.
- **Forms:** every control needs a programmatic label — `<label for>` or wrapping `<label>`; placeholder is not a label. Group related controls with `<fieldset>`/`<legend>` (radio groups). Link help and error text with `aria-describedby`; mark errors with `aria-invalid="true"`; use correct `type` and `autocomplete` attributes (WCAG 1.3.5, and mobile keyboards).

### Q2. What does WCAG 2.2 AA require in practice, and how do you test it?

**Answer:**
- WCAG 2.2 (W3C Recommendation, Oct 2023) keeps the POUR principles — **Perceivable, Operable, Understandable, Robust** — and AA is the usual legal/contractual target (e.g. public sector, and the European Accessibility Act in force since June 2025).
- Everyday AA requirements I check in components:
  - **Contrast:** 4.5:1 for normal text, 3:1 for large text (≈24px, or ≈18.66px bold), **3:1 for UI components and focus indicators** against adjacent colours (1.4.11 Non-text Contrast).
  - **Keyboard:** everything operable by keyboard, no keyboard traps, logical focus order, **visible focus**.
  - **Don't rely on colour alone** (error state = colour + icon + text).
  - **Reflow/resize:** usable at 320 CSS px width and 200% zoom; text spacing overrides don't break layout.
  - **Name, Role, Value** (4.1.2): custom widgets expose correct role, accessible name and states.
  - **Status messages** (4.1.3) announced without moving focus → live regions.
- **New in 2.2** that affects component libraries: **Focus Not Obscured** (focused element not hidden by sticky headers/cookie banners), **Target Size (Minimum)** 24×24 CSS px, **Dragging Movements** (a single-pointer alternative for drag-and-drop, e.g. move up/down buttons), **Accessible Authentication** (no cognitive tests; allow paste and password managers), plus Consistent Help and Redundant Entry (level A). 4.1.1 Parsing was removed.
- **Testing** — layered, because automated tools catch only a portion of issues:
  - Lint: Angular ESLint template accessibility rules (`@angular-eslint/template/...` — alt text, label association, click-events-have-key-events, etc.).
  - Unit/component: `axe-core` via `vitest-axe`/`jest-axe`-style matchers, and Testing Library queries by role/label (`getByRole('button', { name: 'Save' })`) — if you can't query it by role, a screen reader can't find it either.
  - E2E: `@axe-core/playwright` scans on key pages and every component story (Storybook a11y addon).
  - Manual: keyboard-only pass, screen readers (NVDA + Firefox/Chrome, JAWS, VoiceOver on macOS/iOS, TalkBack), 200%/400% zoom, forced colours/high contrast mode, `prefers-reduced-motion`.
- Sound bite: "For the library I treat a11y as part of the component contract — each component has a documented keyboard model and an axe check in CI, so product teams get it by default."

### Q3. What are the rules of ARIA?

**Answer:**
- **Rule 1: don't use ARIA if a native element or attribute does the job.** `<button>` over `role="button"`, `<input type="checkbox">` over `role="checkbox"`, `disabled` over `aria-disabled` unless you deliberately want it focusable.
- **Rule 2:** don't change native semantics unless you must (`<h2 role="tab">` — wrap instead).
- **Rule 3:** every interactive ARIA control must be keyboard-operable — ARIA changes what's *announced*, not what the element *does*. `role="button"` adds no Enter/Space handling.
- **Rule 4:** don't put `aria-hidden="true"` or `role="presentation"` on focusable elements (focus lands on "nothing").
- **Rule 5:** interactive elements need an accessible name.
- "No ARIA is better than bad ARIA" — a wrong role actively lies to the user.
- When ARIA *is* needed: composite widgets without native equivalents (tabs, tree, combobox, listbox, menu, grid) — follow the **ARIA Authoring Practices Guide (APG)** patterns for roles, states and the keyboard model (roving `tabindex` or `aria-activedescendant`).
- Common states/properties: `aria-expanded`, `aria-controls`, `aria-selected`, `aria-checked`, `aria-current="page"`, `aria-describedby`, `aria-labelledby` (prefer over `aria-label` when visible text exists — it stays in sync and gets translated), `aria-live`.

### Q4. How do you manage focus in an SPA, especially on route change?

**Answer:**
- In a full page load the browser resets focus to the document and screen readers announce the new title. In an SPA **nothing happens** — focus stays on the clicked link (or on `body` if that link was removed), and screen-reader users don't know the content changed.
- Pattern:
  1. Update `document.title` per route — Angular's route `title` property / a custom `TitleStrategy`.
  2. After navigation, move focus to the main heading (`<h1 tabindex="-1">`) or the `<main>` container, **or** announce the change via a live region. Pick one consistently.
  3. Provide a **skip link** ("Skip to main content") as the first focusable element.
- Also: dialogs must **trap focus** while open, move focus into the dialog on open and **restore focus** to the trigger on close; deleting a list item must move focus somewhere sensible (next item or the list heading), not drop it on `body`.

```ts
// app.config.ts — focus the view's h1 after each successful navigation
export function provideRouteFocus() {
  return provideAppInitializer(() => {
    const router = inject(Router);
    const doc = inject(DOCUMENT);
    const injector = inject(Injector);
    router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe(() => {
        afterNextRender(() => {
          doc.querySelector<HTMLElement>('main h1')?.focus();   // h1 has tabindex="-1"
        }, { injector });
      });
  });
}
```

(Skip on initial load and when only query params change, otherwise you fight the user's position.)

### Q5. Keyboard navigation, live regions — and what Angular gives you.

**Answer:**
- **Keyboard model:** Tab moves *between* widgets; arrow keys move *within* a composite widget (tabs, menu, listbox, grid) — one tab stop per widget via **roving `tabindex`** (active item `0`, others `-1`) or `aria-activedescendant` (focus stays on the container, e.g. combobox input). Escape closes overlays; Home/End jump.
- **Live regions:** `aria-live="polite"` (announce when idle) / `"assertive"` (interrupt — use rarely), or `role="status"` / `role="alert"`. The region must **exist in the DOM before** content changes — injecting a node that already contains text is often not announced. Use for toasts, "3 results found", async form save status.
- **Angular CDK a11y** (`@angular/cdk/a11y`): `FocusTrap` (`cdkTrapFocus`), `LiveAnnouncer`, `FocusMonitor` (knows keyboard vs mouse focus → show focus rings only for keyboard, like `:focus-visible`), `ListKeyManager` / `FocusKeyManager` / `ActiveDescendantKeyManager` (arrow-key navigation logic), `InteractivityChecker`, and `cdk-visually-hidden`. CDK Overlay/Dialog handle focus trapping and restoration.
- **Angular ARIA** (stable in v22) — headless, accessible primitives that implement the APG interaction patterns without styling. For a design-system team this is attractive: you own the visuals and tokens; the keyboard/ARIA behaviour comes from a maintained, tested package. I'd evaluate it against our existing CDK-based implementations component by component rather than rewrite everything.

### Q6. Box model and `box-sizing`.

**Answer:**
- Every box: **content → padding → border → margin**.
- `box-sizing: content-box` (default): `width` = content only, so padding/border add to the rendered width (a `width: 100%` element with padding overflows).
- `box-sizing: border-box`: `width` includes padding and border — predictable; standard reset: `*, *::before, *::after { box-sizing: border-box; }`.
- Margins are outside the border, never include background, can be negative, and **vertical margins between blocks can collapse** (T2).
- Inline elements ignore `width`/`height` and vertical margins; `inline-block`/`inline-flex` respect them.
- Modern extras: logical properties (`margin-inline`, `padding-block`, `inset-inline-start`) — use them in a library to support RTL for free; `aspect-ratio` to reserve space (helps CLS).

### Q7. How is specificity calculated? Where do `:is()`, `:where()` and `@layer` fit?

**Answer:**
- Specificity is a tuple **(A, B, C)** compared left to right:
  - A: ID selectors,
  - B: classes, attribute selectors, pseudo-classes,
  - C: type selectors and pseudo-elements.
  - `*`, combinators and `:where()` add nothing. Inline `style=""` beats any selector; `!important` flips into a separate, higher-priority tier.
  - Example: `#nav .item a:hover` → (1, 2, 1).
- `:is()`, `:not()`, `:has()` take the specificity of their **most specific argument**. `:is(#id, .a) span` → (1, 0, 1), even when matched via `.a`.
- **`:where()` always has zero specificity** — perfect for library defaults and resets that consumers should override with a single class.
- **Cascade layers** (`@layer`, Baseline since 2022): the cascade compares **layer order before specificity**. Later-declared layers win over earlier ones regardless of selector specificity; **unlayered styles beat all layered styles**. For `!important` the order reverses (earlier layers' important declarations win).
- The actual cascade order: origin & importance → encapsulation context (shadow DOM) → inline style → **layer** → **specificity** → source order.

```scss
// Design system entry point — declare the order once
@layer reset, tokens, base, components, utilities, overrides;

@layer components {
  :where(.ds-button) { padding: var(--ds-button-padding, 0.5rem 1rem); }
}
// Consumer's unlayered CSS (or their `overrides` layer) wins without !important or ID hacks.
```

- Sound bite: "In a design system, `@layer` + `:where()` turn specificity from a war into a contract: the library stays low-specificity, consumers override predictably."
- Caveat with Angular Emulated encapsulation: component styles get attribute selectors (`[_ngcontent-…]`) added, which raises their specificity; and layer order depends on the order stylesheets are inserted — declare the layer order statement in the global stylesheet that loads first.

### Q8. Flexbox vs Grid — when do you use which? What's subgrid?

**Answer:**
- **Flexbox is one-dimensional** — lays items along a single axis (row *or* column), with wrapping as an afterthought; sizing is **content-out** (items' content drives distribution via `flex-grow/shrink/basis`). Best for: toolbars, button groups, nav bars, aligning an icon with text, "push last item right" (`margin-left: auto`), components where item count/size varies.
- **Grid is two-dimensional** — rows **and** columns at once; sizing is **layout-in** (the container defines tracks, items are placed into them). Best for: page layouts, card grids, forms with aligned labels, dashboards, overlapping items (same grid area) without absolute positioning.
- Rules of thumb: "do the items need to line up in both directions?" → Grid. "Is it a line of things that should size to their content?" → Flex. They nest fine — grid for the page, flex inside a cell.
- Useful grid tricks: `repeat(auto-fill, minmax(16rem, 1fr))` for responsive cards without media queries; `grid-template-areas` for readable layouts; `gap` works in both flex and grid.
- **Subgrid** (`grid-template-columns: subgrid`; supported in all major browsers since 2023): a nested grid adopts the parent's tracks, so e.g. titles, bodies and footers of cards in a row align with each other even though each card is its own component. Very relevant for a card component in a library.
- **A11y caveat:** `order`, `flex-direction: row-reverse` and grid placement change *visual* order but not DOM/focus/reading order — can fail WCAG "Meaningful Sequence"/"Focus Order". Keep DOM order logical.

### Q9. BEM — and how does it relate to Angular's `ViewEncapsulation`?

**Answer:**
- **BEM** — Block, Element, Modifier: `.card`, `.card__title`, `.card--featured`. Flat, single-class selectors (low, uniform specificity), self-documenting, no dependence on DOM nesting. It exists to solve **global namespace collisions** in CSS by convention.
- **Angular `ViewEncapsulation`:**
  - **`Emulated`** (default): the compiler rewrites component CSS with attribute selectors (`.title[_ngcontent-abc]`) and stamps those attributes on the template's elements. Styles don't leak out; global styles still leak in.
  - **`ShadowDom`**: real Shadow DOM — full isolation both ways, except inherited properties (`color`, `font`) and **CSS custom properties**, which pierce the boundary. Consumers style internals only via `::part()` or custom properties. Trade-offs: global styles/typography/icon fonts don't apply inside; some third-party libs (overlays, a11y tools) behave differently.
  - **`None`**: styles become global — needed for styling projected/overlay content in some cases, but then you're back to needing a naming convention.
- So with `Emulated`, BEM isn't *needed* to prevent collisions inside a component — but I still like a light BEM-ish naming for **global/`None` styles, overlay panels and the public class API** of a library (`ds-button--primary`), because consumers and tests see those class names.
- **`:host`** styles the component's host element (`:host { display: block; }` — custom elements are `inline` by default, a common bug). `:host(.compact)` / `:host([disabled])` for host-state variants.
- **`:host-context(.theme-dark)`** matches when an ancestor has a class. Angular emulates it in `Emulated` mode; native Shadow DOM support for it is limited across browsers, and custom properties are the cleaner theming mechanism anyway.
- **`::ng-deep`** disables encapsulation for the rest of the selector. It's **deprecated** (kept for compatibility, no replacement planned — the guidance is "avoid"). Without a `:host` prefix it leaks globally. It's a smell in a library consumer's code because it couples them to the library's **private DOM structure** — any internal refactor breaks them.
- **Theming API for a library = CSS custom properties** (design tokens): they cascade, inherit, cross Shadow DOM boundaries, change at runtime (dark mode, brand switching, density) without recompiling, and form a documented public contract.

```scss
// button.component.scss — the component reads tokens with sensible fallbacks
:host {
  display: inline-flex;
  --_bg: var(--ds-button-bg, var(--ds-color-primary));
  --_fg: var(--ds-button-fg, var(--ds-color-on-primary));
}
.ds-button {
  background: var(--_bg);
  color: var(--_fg);
  border-radius: var(--ds-radius-md, 4px);
}
.ds-button:focus-visible { outline: 2px solid var(--ds-color-focus); outline-offset: 2px; }
```

```scss
// consumer — no ::ng-deep, no !important
.checkout ds-button { --ds-button-bg: var(--brand-accent); }
```

### Q10. What SASS features do you rely on, and what are the pitfalls?

**Answer:**
- **Variables** (`$space-md`) — compile-time; use them to *generate* CSS custom properties, not as the runtime theming API (Sass variables can't change at runtime).
- **Nesting** — keep it shallow (≤3 levels); deep nesting creates over-specific selectors coupled to DOM structure. `&` for modifiers (`&--primary`, `&:hover`). Note native CSS nesting now exists in all modern browsers.
- **Mixins** (`@mixin`/`@include`) — emit declarations, can take arguments and `@content` blocks: breakpoints, focus-ring, visually-hidden, typography scales.
- **Functions** (`@function`/`@return`) — compute values (`rem()` conversion, spacing scale).
- **Maps** — token tables (`$colors: (primary: …, danger: …)`) looped with `@each` to generate utilities or custom properties.
- **Placeholders + `@extend`** — `%visually-hidden` + `@extend` merges selectors instead of duplicating declarations. Pitfalls: it **moves your selector to wherever the placeholder is defined** (surprising source order), can generate huge selector lists, **can't extend across `@media`**, and with Angular component styles each component compiles separately, so there's little dedup benefit. I prefer mixins.
- **Modules — `@use` vs `@import`:**
  - `@import` puts everything into one global namespace, re-evaluates (and re-emits CSS) each time it's imported, and makes it impossible to tell where a variable came from. It's **deprecated in Dart Sass (since 1.80) and will be removed in Dart Sass 3.0**, along with global built-ins like `darken()`/`map-get()`.
  - `@use 'tokens'` — **namespaced** (`tokens.$primary`, or `as t`), each module **loaded and evaluated once** per compilation, private members with `-`/`_` prefix, configurable via `@use 'lib' with ($primary: …)` for `!default` variables.
  - `@forward` — re-export a module's members from an index file (the library's public Sass API), with `show`/`hide` and `as prefix-*`.
  - Built-in modules: `@use 'sass:math'` (`math.div` — slash division is deprecated), `sass:color` (`color.adjust`, `color.scale`), `sass:map` (`map.get`, `map.merge`).
  - Migration: the official `sass-migrator` tool automates most of the `@import` → `@use` move.

```scss
// libs/ds/styles/_index.scss — the library's public Sass entry
@forward 'tokens' show $breakpoints, $spacing;
@forward 'mixins' show focus-ring, breakpoint-up, visually-hidden;

// libs/ds/styles/_mixins.scss
@use 'sass:map';
@use 'tokens';

@mixin breakpoint-up($name) {
  @media (min-width: map.get(tokens.$breakpoints, $name)) { @content; }
}

// in an app/component
@use '@acme/ds/styles' as ds;
.panel { padding: ds.$spacing-md; @include ds.breakpoint-up(md) { padding: ds.$spacing-lg; } }
```

### Q11. How does LESS compare?

**Answer:**
- Same broad feature set: variables, nesting, mixins, operations, functions, imports.
- Differences worth naming:
  - Variables use `@` and are **lazily evaluated** with "last definition wins" within a scope (you can override a variable after it's used and affect earlier uses) — handy for theming, confusing for debugging.
  - Mixins are just classes: `.rounded();` (any class can be mixed in); conditionals via **guards** (`when (@mode = dark)`) rather than `@if`; `:extend()` instead of `@extend`.
  - Implemented in JavaScript (can even run in the browser); no module system comparable to `@use`.
- Ecosystem: Sass (Dart Sass) is the industry default and Angular CLI's first-class choice; Bootstrap moved from Less to Sass in v4; Ant Design's CSS moved to CSS-in-JS. The Angular CLI still supports `.less` files.
- Sound bite: "I'm comfortable in both; if I inherited a Less codebase I wouldn't rewrite it for its own sake — I'd move tokens to CSS custom properties, which makes the preprocessor choice mostly irrelevant for theming."

### Q12. Walk me through the critical rendering path.

**Answer:**
1. **HTML → DOM** — parsed incrementally as bytes arrive.
2. **CSS → CSSOM** — CSS is **render-blocking**: the browser won't render until the CSSOM for blocking stylesheets is built (to avoid a flash of unstyled content).
3. **JS** — a classic `<script>` is **parser-blocking**: parsing stops, the script downloads and executes; and a script may wait for pending CSS (it could query styles).
4. **Render tree** — DOM + CSSOM, visible nodes only (`display: none` excluded).
5. **Layout (reflow)** — compute geometry: sizes and positions.
6. **Paint** — fill pixels (text, colours, borders, shadows, images) into layers.
7. **Composite** — the compositor (GPU) combines layers in the right order and applies transforms/opacity.

Optimising it:
- **`defer`** — download in parallel, execute **in order after parsing**, before `DOMContentLoaded`. **`async`** — download in parallel, execute **as soon as ready**, in any order (analytics, independent widgets). `type="module"` scripts are deferred by default (the Angular CLI emits module scripts).
- **`<link rel="preload">`** for late-discovered critical resources (fonts, LCP hero image, above-the-fold CSS); `preconnect` for critical third-party origins; `fetchpriority="high"` on the LCP image.
- **Inline critical CSS**, load the rest non-blocking — the Angular CLI inlines critical CSS for production builds by default.
- Split CSS with `media` attributes (`media="print"` isn't render-blocking for screen).
- Fonts: `font-display: swap`/`optional`, preload the main font, subset, `size-adjust` fallback metrics to reduce layout shift.
- Reduce JS on the critical path: lazy routes, `@defer`, SSR so HTML arrives with content.

### Q13. Reflow vs repaint vs composite — what triggers each? What is layout thrashing?

**Answer:**
- **Layout / reflow** — geometry changes: `width`/`height`, `padding`/`margin`, `top`/`left`, font size, adding/removing DOM, changing text content, window resize, `display`. Can cascade to ancestors/siblings/children — the most expensive step.
- **Paint / repaint** — visual changes without geometry: `color`, `background`, `box-shadow`, `border-color`, `visibility`, `outline`.
- **Composite only** — `transform` and `opacity` (and often `filter`) on an element that has its own layer: no layout, no paint, handled by the compositor thread — smooth even if the main thread is busy.
- **Forced synchronous layout:** reading layout properties (`offsetHeight`, `offsetTop`, `clientWidth`, `scrollTop`, `getBoundingClientRect()`, `getComputedStyle()`) **after a write** forces the browser to run layout immediately to give an accurate answer.
- **Layout thrashing:** doing that in a loop — write, read, write, read — forcing N layouts per frame.

```ts
// Thrashing: each iteration reads (forces layout) after the previous write
for (const el of items) {
  el.style.width = `${el.parentElement!.offsetWidth / 2}px`;
}

// Batched: all reads, then all writes → one layout
const widths = items.map(el => el.parentElement!.offsetWidth);
items.forEach((el, i) => (el.style.width = `${widths[i] / 2}px`));
```

- Tools: Chrome DevTools Performance panel shows purple "Layout" blocks with a "Forced reflow" warning and the offending stack. Batch with `requestAnimationFrame` (or a read/write scheduler like fastdom). In Angular, `afterNextRender`/`afterRenderEffect` have `earlyRead`/`write`/`mixedReadWrite`/`read` phases specifically to order DOM reads and writes and avoid thrashing across components.
- Prefer `ResizeObserver`/`IntersectionObserver` over polling `getBoundingClientRect` on scroll.

### Q14. Compositing, layers and `will-change`.

**Answer:**
- The browser can promote elements to their own **compositor layer** (a GPU texture). Moving/fading a layer with `transform`/`opacity` is just recompositing — no layout/paint. Layers are created for: 3D transforms, `will-change: transform|opacity`, video/canvas, fixed-position elements in some cases, active transform/opacity animations, and elements that must overlap an existing layer ("implicit" promotion).
- **Animate `transform` and `opacity`**, not `top/left/width/height/margin` (T4).
- **`will-change`** hints that a property will change so the browser can prepare a layer ahead of time. Use **sparingly**:
  - every layer costs GPU memory (width × height × 4 bytes, more on high-DPI), and many layers make compositing itself slow — especially on low-end mobile;
  - it creates a **stacking context** and a containing block, which can break `z-index` and `position: fixed` children;
  - add it just before an animation (e.g. on hover of the parent, or from JS) and remove it afterwards; never `* { will-change: transform }`.
- Respect `prefers-reduced-motion` in library animations.

### Q15. Core Web Vitals — what are they, and how do you improve them in Angular?

**Answer:**
| Metric | Measures | Good | Poor |
|---|---|---|---|
| **LCP** — Largest Contentful Paint | loading: when the main content is visible | ≤ 2.5 s | > 4 s |
| **INP** — Interaction to Next Paint | responsiveness: latency of interactions across the visit (roughly the worst) | ≤ 200 ms | > 500 ms |
| **CLS** — Cumulative Layout Shift | visual stability | ≤ 0.1 | > 0.25 |

- Measured at the **75th percentile** of real-user (field) data (CrUX / RUM with the `web-vitals` library). Lighthouse is lab data — useful but not the score Google uses; lab can't measure INP (use TBT as a proxy).
- **INP replaced FID in March 2024.** FID only measured the *input delay* of the *first* interaction; INP measures input delay + processing + presentation delay for **all** interactions — so SPAs with heavy click handlers or big change-detection passes after load now show up.

**Improving them in Angular:**
- **LCP:**
  - `NgOptimizedImage` (`ngSrc`) with **`priority`** on the LCP image → eager loading + `fetchpriority="high"`, and dev-mode warnings (missing `priority` on the LCP element, missing preconnect); responsive `srcset` via an image loader.
  - **SSR/SSG + hydration** so meaningful HTML arrives in the first response instead of after the JS bundle boots; incremental hydration is the default behaviour for hydrated SSR apps since v22.
  - Smaller initial bundle: lazy routes (`loadComponent`/`loadChildren`), `@defer` for below-the-fold/heavy widgets, budgets in `angular.json`, check for CommonJS/unused dependencies.
  - Critical CSS inlining, font preload, preconnect to the API/CDN.
- **INP:**
  - Avoid **long tasks** (> 50 ms): split work (yield to the main thread with `setTimeout`/`scheduler.yield()` where supported), move heavy computation to a Web Worker, virtualise long lists (CDK `ScrollingModule`).
  - Make change detection cheap: `OnPush` (the default for components without explicit `changeDetection` since v22; before v22 you had to opt in), signals so only affected views update, zoneless (default for new apps since v21), `track` in `@for` to avoid re-creating DOM.
  - Give **immediate visual feedback** (pressed state, spinner) before expensive work; debounce input-driven work.
  - With SSR, event replay captures clicks made before hydration so they aren't lost.
- **CLS:**
  - Always reserve space: `width`/`height` or `aspect-ratio` on images and embeds (`NgOptimizedImage` requires dimensions or `fill`), skeletons with the final size, `@defer` `@placeholder` with the same dimensions as the loaded content.
  - Don't insert banners above existing content; animate with `transform`, not layout properties.
  - Fonts: `size-adjust`/metric-compatible fallbacks, `font-display: optional` for non-critical fonts.
  - Avoid hydration mismatches that re-render and shift content.

### Q16. `content-visibility`, containment, and container queries.

**Answer:**
- **`contain`** tells the browser a subtree is independent, so it can scope work: `contain: layout` (inner layout doesn't affect outside), `paint` (nothing paints outside its box; also creates a stacking context), `size` / `inline-size` (size doesn't depend on children), `style`. `contain: content` = layout + paint + style. Good for widgets like cards, table cells, chat messages.
- **`content-visibility: auto`** — skips style/layout/paint for off-screen subtrees until they approach the viewport; big wins for long pages/documents. Pair with **`contain-intrinsic-size: auto 500px`** so skipped sections have a placeholder size (otherwise the scrollbar jumps — CLS-like effects). Content stays in the DOM and accessibility tree and is findable with find-in-page — unlike virtual scrolling. `content-visibility: hidden` is like `display: none` but keeps rendering state (cheap to show again).
- **Container queries** — style a component based on **its container's** size, not the viewport:

```scss
:host { display: block; container: card / inline-size; }

.card { display: grid; gap: 1rem; }
@container card (min-width: 30rem) {
  .card { grid-template-columns: 10rem 1fr; }   // side-by-side when the slot is wide
}
```

- This is *the* feature for a component library: a card doesn't know if it's in a sidebar or main column — media queries can't answer that, container queries can. Container units (`cqi`, `cqb`) for fluid type inside components. Size container queries are supported in all modern browsers (since 2023); style queries on custom properties have narrower support — check before relying on them.

---

## B. Tricky / trap questions

### T1. "I set `z-index: 9999` and it's still behind the header."

**The trap:** "increase it to 99999" or "z-index is global".

**Strong answer includes:**
- `z-index` only compares elements **within the same stacking context**. If the element's ancestor forms a stacking context with a lower z-index than the header's, no child value can escape it.
- Stacking contexts are created by: root; `position` (relative/absolute) **with** a `z-index` other than `auto`; `position: fixed`/`sticky`; flex/grid items with `z-index`; `opacity < 1`; `transform`, `filter`, `perspective`, `clip-path`, `mask`; `isolation: isolate`; `mix-blend-mode`; `will-change` of any of those; `contain: paint|layout`.
- `z-index` has no effect on a non-positioned element (unless it's a flex/grid item).
- Fixes: find the ancestor creating the context (DevTools layers panel), restructure, or render overlays at the document root — which is exactly why Angular CDK Overlay (and dialogs/menus/tooltips) attach to an overlay container on `body`. In a library, define a documented **z-index scale as tokens** (`--ds-z-dropdown`, `--ds-z-modal`, `--ds-z-toast`) instead of magic numbers.
- Also mention the native top layer: `<dialog>` with `showModal()` and the Popover API render above everything without z-index.

### T2. "Why is there a gap above my component?" — margin collapse

**The trap:** not recognising margin collapse, adding `padding: 1px` hacks without understanding them.

**Strong answer includes:**
- Adjacent **vertical** margins of block-level boxes in normal flow collapse to the larger one (not summed). Three cases: siblings; a parent and its first/last child (child's margin "escapes" the parent when there's no border, padding, inline content or height separating them); empty blocks.
- Doesn't happen: horizontally, inside **flex or grid** containers, with floats/absolutely positioned elements, or when the parent establishes a new **block formatting context**.
- Fixes: `display: flow-root` on the parent (clean BFC, no side effects), padding/border, or use flex/grid with `gap`.
- Library angle: components shouldn't set outer margins on their host at all — spacing between components is the **layout's** job (`gap`, stack/layout primitives). That avoids both collapse surprises and consumers fighting your margins.

### T3. Specificity war with `!important` in a component library

**The trap:** "just add `!important`" — or "consumers should use `::ng-deep`".

**Strong answer includes:**
- `!important` in a library forces consumers to use `!important` too (with higher specificity), and it escalates. Inline styles and `!important` are the hardest to override.
- Root cause is usually: library selectors too specific (nested Sass, Emulated attributes), and no public customisation API.
- Fix at the library level:
  - Keep library selectors low-specificity: single classes, `:where()` for defaults.
  - Put library CSS in a **cascade layer** (`@layer ds`) so any unlayered consumer CSS wins without specificity tricks.
  - Expose **CSS custom properties** (tokens) and, if using Shadow DOM, `::part()`, as the supported override API; document them per component.
  - Offer inputs for real variants (`variant`, `size`, `density`) rather than letting consumers restyle internals.
  - Legit `!important` use: utility classes that must always win, and `prefers-reduced-motion` overrides.
- Governance (Design Authority): lint rule/stylelint against `!important` and `::ng-deep` in app code, and a process for requesting new tokens.

### T4. "Why is animating `top/left` janky while `transform` is smooth?"

**The trap:** "transform uses the GPU" — true-ish but incomplete.

**Strong answer includes:**
- `top/left/width/height/margin` change geometry → **layout + paint every frame** on the **main thread**; if JS or change detection is busy, frames drop.
- `transform` and `opacity` can be handled by the **compositor thread** on an already-painted layer — no layout, no paint; animations keep running even while the main thread is blocked (for CSS animations/transitions and Web Animations API).
- Use `transform: translate()/scale()` for movement and size effects, `opacity` for fades; FLIP technique (First, Last, Invert, Play) to animate layout changes via transforms. Angular's newer `animate.enter`/`animate.leave` approach (native CSS animations) and View Transitions follow the same principle.
- Caveats: scaling text can blur; animating `width` of a small element occasionally is fine — measure in the Performance panel rather than dogma.

### T5. "Just add `will-change: transform` to everything for performance."

**The trap:** agreeing.

**Strong answer includes:**
- Each promoted layer consumes GPU memory; hundreds of layers → memory pressure, slower compositing, crashes on low-end devices.
- It creates stacking contexts and containing blocks → broken `z-index` and `position: fixed` descendants.
- Browsers already promote elements during active transform/opacity animations.
- Use it as a targeted, temporary hint for a known expensive animation, verified with DevTools (Layers panel, rendering → "Layer borders"), then remove.

### T6. `display: none` vs `visibility: hidden` vs `opacity: 0` (and visually-hidden)

**The trap:** treating them as interchangeable "hide" options.

**Strong answer includes:**
| | Takes up space | In a11y tree / read by SR | Focusable / clickable | Transitions |
|---|---|---|---|---|
| `display: none` | no | no | no | not animatable (newer `transition-behavior: allow-discrete` helps) |
| `visibility: hidden` | yes | no | no | can be transitioned (discrete) |
| `opacity: 0` | yes | **yes** | **yes** — still receives clicks and focus | yes |
| `hidden` attribute | no (it's `display: none` by UA style — can be overridden by author CSS `display`!) | no | no | — |
| visually-hidden class (clip + 1px) | no (visually) | **yes** | yes if focusable | — |

- `opacity: 0` on a closed menu leaves invisible focusable items → keyboard users tab into nothing (fails focus order / focus visible). Combine with `visibility: hidden` or `inert` when closed.
- `aria-hidden="true"` hides from SR but **not** from keyboard — never on focusable content. The `inert` attribute removes both interaction and a11y exposure (great for background content behind a modal).
- For "screen-reader-only" text (icon button labels, table captions), use a visually-hidden utility (CDK's `cdk-visually-hidden`), not `display: none`.

### T7. "I put `aria-label` on the `div` — why doesn't the screen reader read it?"

**The trap:** thinking `aria-label` works on any element.

**Strong answer includes:**
- `aria-label` names an element **that has a role that supports naming**. A plain `div`/`span` has the `generic` role, on which naming is prohibited — screen readers ignore it inconsistently.
- If it's interactive, it should be a `<button>` (native) — then `aria-label` works (and prefer visible text or `aria-labelledby`).
- If it's a region, use a landmark/`section` with `aria-labelledby` pointing at a visible heading.
- If you just want text read, put real text in the DOM (visually hidden if needed).
- Also: `aria-label` overrides the element's content as the name — putting it on a button with visible text "Save" as `aria-label="Submit form"` breaks voice control users ("click Save") — WCAG 2.5.3 Label in Name.
- Many translation tools skip attribute values — another reason to prefer visible text references.

### T8. "How do I style the inside of a third-party/library component — `::ng-deep`?"

**The trap:** "`::ng-deep` is fine, everyone uses it" — or "it's removed, so `ViewEncapsulation.None`".

**Strong answer includes:**
- `::ng-deep` is deprecated (still works, discouraged). If used at all, **always scope it**: `:host ::ng-deep .mat-x { … }` — otherwise it becomes a global rule that affects every matching element app-wide for as long as that component's styles are in the document.
- `ViewEncapsulation.None` has the same global-leak problem, just more of it.
- The better order of preference: (1) the component's **inputs/variants**; (2) its **CSS custom properties/tokens** (e.g. Angular Material exposes system tokens and `mat.<component>-overrides()` Sass mixins); (3) global stylesheet targeting its **documented** public classes; (4) scoped `:host ::ng-deep` with a comment and a ticket to ask the library owner for a proper API.
- As a library owner: every `::ng-deep` in consumer code is a **missing feature request** — track them and turn them into tokens/inputs.

---

## C. Code examples

### Accessible disclosure (native first) vs the minimum custom-ARIA version

```html
<!-- Native: zero JS, keyboard + SR support built in -->
<details>
  <summary>Shipping details</summary>
  <p>Delivered in 3–5 working days.</p>
</details>
```

```ts
@Component({
  selector: 'ds-disclosure',
  template: `
    <button type="button"
            [attr.aria-expanded]="open()"
            [attr.aria-controls]="panelId"
            (click)="open.set(!open())">
      <ng-content select="[dsDisclosureTitle]" />
    </button>
    <div [id]="panelId" [hidden]="!open()">
      <ng-content />
    </div>
  `,
  styles: `:host { display: block; }`,
})
export class DisclosureComponent {
  readonly open = model(false);
  private static nextId = 0;
  protected readonly panelId = `ds-disclosure-panel-${DisclosureComponent.nextId++}`;
}
```

### Live-region announcement with the CDK

```ts
@Component({
  selector: 'app-cart-actions',
  template: `<button type="button" (click)="add()">Add to basket</button>`,
})
export class CartActionsComponent {
  private readonly announcer = inject(LiveAnnouncer);
  private readonly cart = inject(CartStore);

  add() {
    this.cart.addItem();
    this.announcer.announce(`Added. ${this.cart.count()} items in basket.`, 'polite');
  }
}
```

### Library stylesheet skeleton: layers, `:where()`, tokens, reduced motion

```scss
@use 'sass:map';

@layer ds.reset, ds.tokens, ds.components;

@layer ds.tokens {
  :root {
    --ds-color-primary: #0b5fff;
    --ds-color-on-primary: #fff;
    --ds-color-focus: #1a1a1a;
    --ds-radius-md: 6px;
    --ds-z-dropdown: 1000;
    --ds-z-modal: 1100;
  }
  :root[data-theme='dark'] {
    --ds-color-primary: #7aa7ff;
    --ds-color-on-primary: #0a0a0a;
    --ds-color-focus: #fff;
  }
}

@layer ds.components {
  :where(.ds-chip) {
    display: inline-flex;
    align-items: center;
    min-block-size: 24px;               // WCAG 2.2 target size (minimum)
    padding-inline: 0.75rem;
    border-radius: var(--ds-radius-md);
    transition: transform 150ms ease;
  }
  :where(.ds-chip:hover) { transform: translateY(-1px); }

  @media (prefers-reduced-motion: reduce) {
    :where(.ds-chip) { transition: none; }
  }
}
```

### Deferring a heavy, below-the-fold widget without layout shift

```html
<section class="reviews" aria-labelledby="reviews-title">
  <h2 id="reviews-title">Customer reviews</h2>
  @defer (on viewport; prefetch on idle) {
    <app-reviews-chart [productId]="productId()" />
  } @placeholder (minimum 300ms) {
    <div class="reviews__skeleton" style="block-size: 320px"></div>
  } @loading (after 100ms; minimum 500ms) {
    <div class="reviews__skeleton" style="block-size: 320px" aria-busy="true"></div>
  } @error {
    <p>Reviews couldn't be loaded.</p>
  }
</section>
```

---

## D. Red flags

- "I use `div`s with click handlers and add ARIA later." — *Say instead:* "Native elements first; ARIA only for patterns HTML doesn't cover, following the APG keyboard model."
- "Accessibility is QA's job / we run Lighthouse." — *Say instead:* "Automated checks catch only part of it; our components have a keyboard spec, axe in CI, and manual screen-reader passes on release."
- "`outline: none` because designers don't like the focus ring." — *Say instead:* "I use `:focus-visible` with a branded, 3:1-contrast focus style — removing focus is a WCAG failure."
- "`z-index` isn't working, so I bumped it to 99999." — *Say instead:* "It's a stacking-context problem; I find the ancestor creating it or render the overlay at the root."
- "We use `::ng-deep` to theme library components." — *Say instead:* "Theming goes through CSS custom properties/tokens; `::ng-deep` is deprecated and couples consumers to private DOM."
- "`!important` fixes specificity issues." — *Say instead:* "Low-specificity library CSS, `:where()`, and `@layer` so overrides are predictable."
- "Sass variables are our theming system." — *Say instead:* "Sass generates tokens at build time; CSS custom properties are the runtime theming API."
- "`@import` is fine." — *Say instead:* "`@import` is deprecated in Dart Sass and will be removed in 3.0; we use `@use`/`@forward`."
- "Grid replaces flexbox." — *Say instead:* "Grid for two-dimensional layout, flex for one-dimensional distribution — they complement each other."
- "I animate with `top`/`left` and add `will-change` everywhere." — *Say instead:* "`transform`/`opacity` on the compositor; `will-change` only as a temporary, measured hint."
- "FID is our responsiveness metric." — *Say instead:* "INP replaced FID in March 2024; good is ≤ 200 ms at p75 of field data."
- "Performance = Lighthouse score." — *Say instead:* "Lighthouse is lab data; I track field Core Web Vitals via RUM, and use lab tools to diagnose."
- "Media queries handle our component responsiveness." — *Say instead:* "Components use container queries, because they don't know the viewport slot they're placed in."

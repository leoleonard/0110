# 09 — Design Patterns, Code Quality & Architecture

> **How to use this file.** Senior interviews rarely ask "what is the Strategy pattern?". They ask "how would you structure X so that Y can change without touching Z?", and they listen for *judgement*: do you reach for a pattern because it solves a real change axis, or because it looks clever? Everything here is framed the way you would say it out loud: principle, then an Angular example, then the trade-off and when *not* to do it. As Design Authority and owner of a shared component library, you are expected to talk about **standards you set and enforce** (lint rules, ADRs, review guidelines, deprecation policy), not only code you wrote. Keep a "we did this, it cost that, we measured this" story ready for each section.
>
> Version notes you should know (details in FACTS): since **v22** components are **OnPush by default** (`ChangeDetectionStrategy.Eager` replaces the deprecated `Default`); **zoneless** is the default for new apps since **v21**; **Vitest** is the default test runner since **v21**; v22 adds the **`@Service()`** decorator (auto-provided in root by default), and `@Injectable({ providedIn: 'root' })` still works.

---

## A. Most commonly asked questions

### Q1. Walk me through SOLID with Angular examples.

**Answer (1–2 min):** SOLID is about managing *reasons to change*, not about creating interfaces. In Angular terms:

- **S — Single Responsibility.** A component renders and handles user intent; a service owns data access; a store owns state transitions. The smell is a `UserService` that fetches, caches, formats dates, shows toasts and navigates. Split by *reason to change*: API contract changes, caching policy changes, UX copy changes.
- **O — Open/Closed.** Extend behaviour without editing the core. Angular's DI is the main tool: add a new `ExportStrategy` via a multi-provider rather than adding another `case` to a switch; add a new HTTP concern via another functional interceptor rather than editing the existing one. In a component library: content projection and `ng-template` slots let consumers extend a `<ui-table>` without us adding a boolean input per use case.
- **L — Liskov Substitution.** Anything provided under a token must honour the contract. If a `MockPaymentGateway` resolves instantly but the real one can throw `3DS_REQUIRED`, tests pass and prod breaks. For component libraries: a custom form control must behave like a form control (value, touched, disabled) or it breaks forms that consume it.
- **I — Interface Segregation.** Small, role-focused contracts. A component should not inject a 40-method `ApiService` to call one endpoint. For inputs: prefer a few meaningful inputs over a giant `config` object whose fields most consumers ignore.
- **D — Dependency Inversion.** High-level feature code depends on an abstraction (`InjectionToken` or abstract class), low-level adapters are plugged in at the composition root (`app.config.ts`, route `providers`).

"SOLID in Angular is mostly SRP plus DI. The DI container gives me O, L and D almost for free if I define the right tokens."

**Go deeper:**
- SRP applies to templates too: a 400-line template usually hides 3–4 presentational components.
- Don't over-apply: one implementation today and no realistic second one means you don't need an abstraction yet (YAGNI). An abstract class can be introduced later with a small refactor.

```typescript
// D + O: feature depends on an abstraction; implementations are swapped at composition root
export abstract class AnalyticsTracker {
  abstract track(event: string, props?: Record<string, unknown>): void;
}

@Injectable()
export class SegmentTracker implements AnalyticsTracker {
  track(event: string, props?: Record<string, unknown>) { /* 3rd-party SDK call */ }
}

@Injectable()
export class NoopTracker implements AnalyticsTracker {
  track() {}
}

// app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [
    { provide: AnalyticsTracker, useClass: environment.production ? SegmentTracker : NoopTracker },
  ],
};

// feature code
export class CheckoutComponent {
  private readonly tracker = inject(AnalyticsTracker);
}
```

---

### Q2. Smart vs dumb (container vs presentational) components — still relevant with signals?

**Answer:** Yes, but the boundary moved.

- **Container (smart):** knows *where* data comes from (store, facade, `httpResource`, router), orchestrates side effects, maps domain state to view models. Usually routed or feature-level.
- **Presentational (dumb):** pure function of inputs → DOM + outputs. No injected data services. Trivially testable, reusable, and the natural shape of every component in a shared library.

**What signals change:**
- `input()`, `model()`, `output()` and `computed()` make presentational components cleaner: derived view state lives in `computed()` rather than `ngOnChanges`.
- Because OnPush is the default in v22 and signals give fine-grained reactivity, the old *performance* argument ("dumb components with OnPush are faster") is weaker — everything is OnPush now. The remaining argument is **testability, reuse and clear ownership of side effects**.
- A signal store (`@ngrx/signals`) or `httpResource` injected into a component blurs the line. I allow a presentational component to inject *UI-only* services (e.g. `LiveAnnouncer`, a tooltip overlay service) but not data sources.
- Don't create a container for every leaf — "container for a route or a meaningful feature slice, presentational below it" is a good default. Prop-drilling through five levels is a signal to introduce a scoped store/provider at the feature level.

```typescript
// Presentational — shared-lib style
@Component({
  selector: 'ui-order-summary',
  template: `
    <h3>{{ title() }}</h3>
    @for (line of lines(); track line.id) {
      <div class="line">{{ line.name }} — {{ line.total | currency: currency() }}</div>
    } @empty {
      <p>No items</p>
    }
    <strong>{{ grandTotal() | currency: currency() }}</strong>
    <button (click)="checkout.emit()" [disabled]="lines().length === 0">Checkout</button>
  `,
  imports: [CurrencyPipe],
})
export class OrderSummaryComponent {
  readonly title = input('Your order');
  readonly lines = input.required<readonly OrderLineVm[]>();
  readonly currency = input('EUR');
  readonly checkout = output<void>();
  protected readonly grandTotal = computed(() => this.lines().reduce((s, l) => s + l.total, 0));
}

// Container — owns data and side effects
@Component({
  selector: 'app-cart-page',
  template: `<ui-order-summary [lines]="cart.lines()" (checkout)="cart.checkout()" />`,
  imports: [OrderSummaryComponent],
})
export class CartPageComponent {
  protected readonly cart = inject(CartFacade);
}
```

---

### Q3. What is a facade and when would you (not) use one?

**Answer:** A facade is a feature-level service exposing a **small, intention-revealing API** (`cart.lines()`, `cart.addItem(id)`) and hiding *how* state is managed — NgRx store, SignalStore, plain signals in a service, or HTTP calls.

**Pros**
- Components don't know about actions/selectors; you can migrate from classic NgRx to SignalStore (or to plain signals) behind a stable API — very useful during a v-to-v migration.
- One place for orchestration ("add item → refresh totals → track analytics").
- Easy to mock in component tests.

**Cons**
- Another layer. If it is a 1:1 pass-through of store methods it adds indirection with zero value.
- It can hide the Redux event log's intent: with classic NgRx, facades that dispatch many actions from one method encourage "command" style actions instead of "event" style (`[Cart Page] Checkout Clicked`), which weakens DevTools/debugging.
- Facades that grow into god services (every feature's API in one class).

"I use a facade at a feature boundary when the state implementation is likely to change or is complex. I don't wrap every service in a facade — `HttpClient` wrapped in `UserApi` wrapped in `UserFacade` wrapped in `UserStore` is three layers doing one thing."

```typescript
@Service()
export class CartFacade {
  private readonly store = inject(CartStore);      // SignalStore today, could be anything tomorrow
  private readonly tracker = inject(AnalyticsTracker);

  readonly lines = this.store.lines;               // Signal<readonly OrderLineVm[]>
  readonly isEmpty = computed(() => this.lines().length === 0);

  addItem(productId: string) {
    this.store.add(productId);
    this.tracker.track('cart_item_added', { productId });
  }
  checkout() { this.store.checkout(); }
}
```

**Go deeper:** In the NgRx world, some teams dislike facades precisely because they encourage command-style actions. Show you know the debate; a good compromise is facades that dispatch *event* actions (`cartPageEvents.checkoutClicked()`).

---

### Q4. Adapter pattern — where do you use it in a frontend?

**Answer:** Two main places:

1. **API DTO → domain model mapping.** The backend's shape (snake_case, ISO strings, nullable everything, version drift, a 3rd-party partner's quirks) should not leak into components. An adapter (a pure mapping function or a small class) converts DTOs to domain models at the edge — ideally in the data-access layer. Benefits: one place to change when the partner API changes; domain types can be strict (`Date`, enums, non-null) so templates don't do `?.` everywhere; mapping is trivially unit-testable.
2. **Wrapping 3rd-party libraries** (charting, maps, date libs, analytics SDKs, payment widgets). The rest of the app depends on *our* interface. Upgrading or replacing the library touches one folder. It also gives you a seam for SSR safety (don't touch `window` on the server) and zoneless-friendly change notification.

```typescript
// DTO as delivered by a partner API (generated from Swagger/OpenAPI ideally)
interface OrderDto {
  order_id: string;
  created_at: string;           // ISO
  status: 'N' | 'P' | 'S' | 'C';
  total_cents: number | null;
}

// Domain model used by the app
export interface Order {
  id: string;
  createdAt: Date;
  status: 'new' | 'paid' | 'shipped' | 'cancelled';
  total: number;
}

const STATUS: Record<OrderDto['status'], Order['status']> = {
  N: 'new', P: 'paid', S: 'shipped', C: 'cancelled',
};

export function toOrder(dto: OrderDto): Order {
  return {
    id: dto.order_id,
    createdAt: new Date(dto.created_at),
    status: STATUS[dto.status],
    total: (dto.total_cents ?? 0) / 100,
  };
}

@Service()
export class OrdersApi {
  private readonly http = inject(HttpClient);
  list() {
    return this.http.get<OrderDto[]>('/api/orders').pipe(map((dtos) => dtos.map(toOrder)));
  }
}
```

**Go deeper:**
- Generate DTO types from the OpenAPI/Swagger spec (e.g. openapi-generator, orval) so drift is a compile error, and keep the mapping hand-written.
- For untrusted partner APIs, validate at runtime at the edge (e.g. a schema library such as zod/valibot) — TypeScript types are erased and `http.get<T>` is a cast, not a check.

---

### Q5. Strategy pattern in Angular — show me.

**Answer:** Strategy = interchangeable algorithms behind one interface, selected at runtime. Angular DI with **multi-providers on an `InjectionToken`** is the idiomatic registry: new strategies are *added* without editing the consumer (Open/Closed).

```typescript
export interface ExportStrategy {
  readonly format: 'csv' | 'xlsx' | 'pdf';
  readonly label: string;
  export(rows: readonly Record<string, unknown>[]): Promise<Blob>;
}

export const EXPORT_STRATEGIES = new InjectionToken<readonly ExportStrategy[]>('EXPORT_STRATEGIES');

@Injectable()
export class CsvExport implements ExportStrategy {
  readonly format = 'csv' as const;
  readonly label = 'CSV';
  async export(rows: readonly Record<string, unknown>[]) {
    const header = Object.keys(rows[0] ?? {}).join(',');
    const body = rows.map((r) => Object.values(r).join(',')).join('\n');
    return new Blob([header + '\n' + body], { type: 'text/csv' });
  }
}

// Heavy lib loaded lazily, only when the strategy is used
@Injectable()
export class XlsxExport implements ExportStrategy {
  readonly format = 'xlsx' as const;
  readonly label = 'Excel';
  async export(rows: readonly Record<string, unknown>[]) {
    const { toXlsx } = await import('./xlsx-writer');
    return toXlsx(rows);
  }
}

export function provideExports(...strategies: Type<ExportStrategy>[]): Provider[] {
  return strategies.map((s) => ({ provide: EXPORT_STRATEGIES, useClass: s, multi: true }));
}

// Consumer
@Service()
export class ExportService {
  private readonly strategies = inject(EXPORT_STRATEGIES);
  readonly formats = this.strategies.map((s) => ({ format: s.format, label: s.label }));

  run(format: ExportStrategy['format'], rows: readonly Record<string, unknown>[]) {
    const s = this.strategies.find((x) => x.format === format);
    if (!s) throw new Error(`No export strategy for ${format}`);
    return s.export(rows);
  }
}

// route or app config
providers: [provideExports(CsvExport, XlsxExport)]
```

Same shape works for **payment providers** (card, PayPal, bank transfer — each partner SDK behind one interface), **validation rules per market**, or **feature-flag-driven UI variants**.

**When not to:** two branches that will never grow → an `if` is fine. Strategies are worth it when the set of variants is open-ended or owned by different teams.

---

### Q6. Observer pattern — RxJS vs signals: which, when?

**Answer:** Both are observer implementations with different semantics.

- **Signals:** synchronous, always have a current value, glitch-free derived state (`computed`), automatic dependency tracking, integrate with change detection (the reason zoneless works). Best for **state** and derived view state.
- **RxJS Observables:** push-based streams over *time*, lazy, cancellable, with operators for concurrency (`switchMap`, `exhaustMap`, `debounceTime`, `retry`). Best for **events and async orchestration**: typeahead, websockets, polling, race conditions, retries.
- Bridge with `toSignal` / `toObservable`, `rxResource({ params, stream })`, and `takeUntilDestroyed()` for cleanup.

"State in signals, events and async coordination in RxJS, and convert at the boundary. I don't rewrite a well-tested `switchMap` pipeline to `effect()` just to be fashionable."

```typescript
export class ProductSearchComponent {
  private readonly api = inject(ProductsApi);
  protected readonly query = signal('');

  protected readonly results = toSignal(
    toObservable(this.query).pipe(
      debounceTime(250),
      distinctUntilChanged(),
      switchMap((q) => (q.length < 2 ? of([]) : this.api.search(q))),
    ),
    { initialValue: [] },
  );
}
```

**Go deeper:** `effect()` is for *side effects to the outside world* (logging, localStorage, imperative 3rd-party APIs), not for propagating state between signals — use `computed()` or `linkedSignal()` for that.

---

### Q7. How do you apply Dependency Inversion in Angular — `InjectionToken` or abstract class?

**Answer:**

| | Abstract class as token | `InjectionToken<T>` |
|---|---|---|
| Works for | class-shaped services | anything: config objects, functions, primitives, arrays (multi) |
| Runtime artefact | yes (the class) | yes (the token) |
| Default impl | `@Injectable({ providedIn: 'root', useClass: X })` or `@Service({ factory })` | `new InjectionToken('x', { factory: () => ... })` |
| Type safety | via class | via generic |

TypeScript `interface`s can't be tokens (erased at runtime) — that's why we need one of the two.

```typescript
export interface FeatureFlags { isOn(flag: string): boolean; }

export const FEATURE_FLAGS = new InjectionToken<FeatureFlags>('FEATURE_FLAGS', {
  providedIn: 'root',
  factory: () => ({ isOn: () => false }), // safe default: everything off
});

// Library config pattern — very common in shared component libraries
export interface UiLibConfig { density: 'comfortable' | 'compact'; dateFormat: string; }
export const UI_LIB_CONFIG = new InjectionToken<UiLibConfig>('UI_LIB_CONFIG', {
  providedIn: 'root',
  factory: () => ({ density: 'comfortable', dateFormat: 'dd/MM/yyyy' }),
});
export function provideUiLib(config: Partial<UiLibConfig>): Provider {
  return { provide: UI_LIB_CONFIG, useValue: { density: 'comfortable', dateFormat: 'dd/MM/yyyy', ...config } };
}
```

"For a library I expose `provideXxx()` functions and tokens with safe defaults, so consumers configure the lib at their composition root and never import internals."

---

### Q8. Decorator / composition — how do you share behaviour between components without inheritance?

**Answer:** Composition over inheritance, using Angular primitives:

- **`hostDirectives`** (since v15): compose reusable behaviour directives onto a component's host, optionally re-exposing selected inputs/outputs. Perfect for a component library: `uiFocusRing`, `uiTooltip`, `uiDisabled`, `uiTrackClick`.
- **Plain functions using `inject()`** ("composables"): `injectQueryParam('page')`, `injectBreakpoint()`. Reusable, tree-shakable, testable, no base class.
- **Content projection / templates** for structural variation.
- **`signalStoreFeature`** to compose store capabilities (loading state, pagination) in NgRx SignalStore.

```typescript
@Directive({
  selector: '[uiDisabled]',
  host: {
    '[attr.aria-disabled]': 'disabled()',
    '[class.is-disabled]': 'disabled()',
    '(click)': 'guard($event)',
  },
})
export class DisabledDirective {
  readonly disabled = input(false, { alias: 'uiDisabled', transform: booleanAttribute });
  guard(e: Event) { if (this.disabled()) { e.preventDefault(); e.stopImmediatePropagation(); } }
}

@Component({
  selector: 'ui-button',
  hostDirectives: [{ directive: DisabledDirective, inputs: ['uiDisabled: disabled'] }],
  template: `<ng-content />`,
})
export class ButtonComponent {}

// composable function
export function injectQueryParam(name: string): Signal<string | null> {
  const route = inject(ActivatedRoute);
  return toSignal(route.queryParamMap.pipe(map((p) => p.get(name))), { initialValue: null });
}
```

**Go deeper:** host directives are instantiated per host and run before the host component; they cannot be applied conditionally. Keep them small and side-effect-light.

---

### Q9. Why avoid the Template Method pattern / `BaseComponent` inheritance?

**Answer:** The classic `BaseListComponent<T>` with abstract `load()` and `ngOnInit` in the base:

- Couples every subclass to the base's lifecycle, constructor dependencies, and change detection assumptions. Changing the base is a breaking change across the app.
- Hidden behaviour: reading the subclass doesn't tell you what runs.
- Angular-specific pain: decorator metadata is not fully inherited (inputs/host bindings historically confusing), `super()` constructor chains with DI (mostly solved by `inject()`, but the coupling remains), and a "`destroy$` subject in the base class" pattern that is now obsolete with `takeUntilDestroyed()`/`DestroyRef`.
- It encourages "god base classes" that every component extends "just in case".

Replace with composition: a `injectListState(loader)` function, a SignalStore feature, host directives, or a presentational `<ui-data-list>` component with slots.

"Inheritance for *domain types* is sometimes OK. Inheritance for *component reuse* is the thing I push back on in review."

---

### Q10. What does clean code mean to you in an Angular codebase?

**Answer:** Code the next person can change safely. Concretely:

- **Naming:** intention-revealing (`isCheckoutDisabled` not `flag2`), consistent suffixes (`*.api.ts`, `*.store.ts`, `*.facade.ts`), event outputs named as past-tense events (`saved`, `selectionChange`), not `onSave`.
- **Small, pure functions:** mapping, formatting, validation and business rules as pure functions outside classes — testable without TestBed.
- **Explicit data flow:** inputs down, outputs up; state changes in one place; no hidden mutation of input objects (readonly types).
- **No god services:** a `SharedService`/`UtilsService`/`CommonService` with 60 methods is a dependency magnet. Split by domain.
- **No `SharedModule` dumping ground:** with standalone components each component imports exactly what it uses; a shared barrel that re-exports 80 things breaks tree-shaking intuitions and creates coupling.
- **Types that make illegal states unrepresentable:** discriminated unions for request state (`{ status: 'loading' } | { status: 'error'; error } | { status: 'ok'; data }`).
- **Comments explain why, not what.**

```typescript
type Loadable<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; error: string }
  | { status: 'ok'; data: T };
```

---

### Q11. How do you set up linting and formatting for a large Angular codebase?

**Answer:** Layered, automated, and non-negotiable in CI:

- **angular-eslint** (flat config): TS rules (e.g. `prefer-standalone`, `prefer-on-push-component-change-detection` — largely redundant once you're on v22 where OnPush is default, `no-output-on-prefix`, `use-lifecycle-interface`) and **template rules** (`prefer-control-flow`, accessibility rules like `alt-text`, `label-has-associated-control`, `interactive-supports-focus`).
- **typescript-eslint `strictTypeChecked`** (+ `stylisticTypeChecked`): catches floating promises, unsafe `any`, unnecessary conditions.
- **Prettier** for formatting — no formatting debates in code review. ESLint does correctness, Prettier does style.
- **Stylelint** for SCSS: `stylelint-config-standard-scss`, ban hard-coded colours in favour of design tokens, ban `@import` (deprecated in Dart Sass — use `@use`/`@forward`), limit selector specificity / nesting depth, forbid `::ng-deep` outside an allow-list.
- **Architecture rules:** Nx `@nx/enforce-module-boundaries` with tags (`type:feature`, `type:ui`, `type:data-access`, `type:util`, `scope:orders`), or `eslint-plugin-boundaries` in non-Nx repos; `no-restricted-imports` to ban deep imports into a library's internals.
- **Custom rules** where the team keeps making the same review comment (e.g. "no `HttpClient` in components", "no direct import of the charting lib outside `ui-charts`").
- Run in pre-commit (lint-staged) for speed and in CI for enforcement; use `--max-warnings 0` on new code and a baseline/ratchet for legacy.

```js
// eslint.config.js (sketch)
const tseslint = require('typescript-eslint');
const angular = require('angular-eslint');

module.exports = tseslint.config(
  {
    files: ['**/*.ts'],
    extends: [...tseslint.configs.strictTypeChecked, ...angular.configs.tsRecommended],
    processor: angular.processInlineTemplates,
    rules: {
      '@angular-eslint/prefer-standalone': 'error',
      'no-restricted-imports': ['error', {
        patterns: [{ group: ['@acme/ui/*/src/*'], message: 'Import from the public API (@acme/ui/<entry>) only.' }],
      }],
    },
  },
  {
    files: ['**/*.html'],
    extends: [...angular.configs.templateRecommended, ...angular.configs.templateAccessibility],
    rules: { '@angular-eslint/template/prefer-control-flow': 'error' },
  },
);
```

```json
// Nx: .eslintrc / eslint.config — module boundary constraints
"@nx/enforce-module-boundaries": ["error", {
  "depConstraints": [
    { "sourceTag": "type:feature",     "onlyDependOnLibsWithTags": ["type:feature", "type:ui", "type:data-access", "type:util"] },
    { "sourceTag": "type:ui",          "onlyDependOnLibsWithTags": ["type:ui", "type:util"] },
    { "sourceTag": "type:data-access", "onlyDependOnLibsWithTags": ["type:data-access", "type:util"] },
    { "sourceTag": "scope:orders",     "onlyDependOnLibsWithTags": ["scope:orders", "scope:shared"] }
  ]
}]
```

---

### Q12. Strict TypeScript and `strictTemplates` — worth the migration pain?

**Answer:** Yes; it's the cheapest bug prevention you can buy.

- `tsconfig`: `"strict": true` plus `noUncheckedIndexedAccess`, `noImplicitOverride`, `noPropertyAccessFromIndexSignature`, `noImplicitReturns`, `noFallthroughCasesInSwitch`; `exactOptionalPropertyTypes` if the team can take it.
- `angularCompilerOptions`: `strictTemplates: true`, `strictInjectionParameters`, `strictInputAccessModifiers`, and `extendedDiagnostics` (v22 enables `nullishCoalescingNotNullable`/`optionalChainNotNullable` diagnostics, which catch pointless `?.`/`??` in templates).
- Signal inputs (`input.required<T>()`) give strict typing of bindings end to end.

**Migrating a legacy codebase:** enable per-project (or per-library in a monorepo), start with the shared libs (highest leverage — their types flow into every consumer), use `// @ts-expect-error` with a ticket reference sparingly, track the count as a debt metric that only goes down.

```json
{
  "compilerOptions": { "strict": true, "noUncheckedIndexedAccess": true, "noImplicitOverride": true },
  "angularCompilerOptions": {
    "strictTemplates": true,
    "strictInjectionParameters": true,
    "strictInputAccessModifiers": true,
    "extendedDiagnostics": { "defaultCategory": "error" }
  }
}
```

---

### Q13. Describe your testing strategy — pyramid or trophy?

**Answer:** "It depends on where the risk is." For an Angular product app I lean to the **testing trophy**: static analysis at the base (strict TS, lint), a large layer of **integration-style component tests** (component + real child components + mocked HTTP), a thinner layer of pure unit tests for business logic, and a small number of **E2E** journeys on critical paths.

Rough ratio I'd propose (by count, not effort): ~50% component/integration, ~35% unit (pure functions, stores, mappers), ~10% E2E (critical user journeys: login, checkout, payment), ~5% contract/visual. Adjust per risk.

**What to test where:**
- **Services / stores / mappers:** pure logic, state transitions, error handling. No TestBed needed for pure functions; `TestBed.inject` + `provideHttpClientTesting()` for data services.
- **Components:** test *behaviour through the DOM* as a user would (Testing Library or **component harnesses**), not private methods or signal internals. Inputs in → rendered output and emitted outputs.
- **Shared component library:** ship **harnesses** (`ComponentHarness`) so consumers' tests don't break when internal DOM changes; add **visual regression** (Storybook + Chromatic/Playwright screenshots) and automated a11y checks (axe) per component story.
- **Contract tests** between frontend and backend/partner APIs (consumer-driven contracts, e.g. Pact, or schema validation against the OpenAPI spec in CI) — catches "partner renamed a field" before prod.
- **E2E:** Playwright (or Cypress) on a few critical paths, run against a stable environment, with test data you control.

Tooling note: **Vitest is the default runner since v21**; Karma is legacy. Jest was experimental, not the recommended path.

```typescript
// Library ships a harness
export class UiButtonHarness extends ComponentHarness {
  static hostSelector = 'ui-button';
  async click() { return (await this.host()).click(); }
  async isDisabled() { return (await (await this.host()).getAttribute('aria-disabled')) === 'true'; }
}

// Consumer test (Vitest)
it('disables submit until the form is valid', async () => {
  const fixture = TestBed.createComponent(SignupComponent);
  const loader = TestbedHarnessEnvironment.loader(fixture);
  const submit = await loader.getHarness(UiButtonHarness);
  expect(await submit.isDisabled()).toBe(true);
});
```

---

### Q14. How do you manage technical debt?

**Answer:** Treat it like a product backlog, not a guilty secret.

1. **Classify:** deliberate vs accidental; by type — architectural (wrong boundaries), code (duplication, god services), dependency (Angular two majors behind, deprecated APIs like `*ngIf`, `ComponentFactoryResolver` removed in v22), test debt, tooling/CI, UX/a11y debt.
2. **Quantify:** impact × likelihood × cost-of-delay. Evidence: lead time for changes in that area, defect density, incident count, build time, bundle size, number of `@ts-expect-error`, lint baseline size, % components still Eager/zone-dependent.
3. **Make it visible:** a debt register (labelled issues), a dashboard trended over time, ADRs recording deliberate debt with an exit condition.
4. **Tie to business metrics:** "This area takes 3x longer to change and caused 4 of last quarter's 9 incidents" beats "the code is ugly". Link to delivery speed, conversion, error rate, Core Web Vitals.
5. **Pay continuously:** a fixed capacity share (e.g. 15–20%), the **boy-scout rule** in PRs touching the area, and bundling debt work with feature work in the same area.
6. **For a shared library:** a **deprecation policy** (mark `@deprecated` with replacement → at least one major of overlap → remove), semver discipline, changelog with migration notes, and **`ng update` schematics / migrations** so consumers upgrade mechanically.

"I don't believe in hardening sprints as the debt strategy — debt paid in a big batch is debt that was invisible for months."

---

### Q15. How would you structure a large Angular app (folders, layers, public APIs)?

**Answer:** Organise by **domain first, then by type** (feature-sliced / domain folders), with enforced layering:

```
apps/shop/
libs/
  orders/
    feature-order-list/     # routed containers (type:feature)
    feature-order-detail/
    data-access/            # api clients, adapters, stores, facades (type:data-access)
    ui/                     # presentational components specific to orders (type:ui)
    util/                   # pure functions, types (type:util)
  shared/
    ui/                     # the design system / component library
    util-http/              # interceptors, error mapping
```

- **Layering:** `feature → ui, data-access, util`; `ui → util` only; `data-access → util`. No feature-to-feature imports; cross-domain communication through a shared data-access or routing.
- **Public API barrels:** each lib has one `index.ts` exporting the supported surface; deep imports banned by lint. For a published lib, use **secondary entry points** (`@acme/ui/button`, `@acme/ui/table`) so consumers only pull what they use and your internal refactors don't break anyone.
- Barrels inside an app (every folder with `index.ts`) cause circular import risks and slower tooling — use them at library boundaries, not everywhere.
- Lazy load by route with `loadComponent`/`loadChildren`; each feature brings its own `providers` in the route config.

---

### Q16. What are your code review standards?

**Answer:**
- **Automate the trivial:** formatting, lint, types, tests, bundle budget, affected-only builds run in CI; reviewers don't comment on style.
- **Review for:** correctness and edge cases, design fit (does it follow the ADRs / boundaries?), public API changes (in the lib: is this a breaking change? documented? migration?), accessibility, performance hotspots (unbounded lists without `track`, effects that write signals), security (`bypassSecurityTrust*`, `innerHTML`), test quality (behavioural, not snapshot spam).
- **Small PRs** (< ~400 lines changed) and a clear description with "why" and screenshots/stories for UI.
- **Conventional comments** (`nit:`, `suggestion:`, `issue:`, `question:`) to signal severity; blocking only for real issues.
- **Response SLA** (e.g. first review within one working day) — review latency is a delivery metric.
- As Design Authority: a checklist in the PR template and CODEOWNERS for the shared lib, so API changes get the right eyes without me being a bottleneck.

---

### Q17. What are ADRs and how do you run them as Design Authority?

**Answer:** Architecture Decision Records: short markdown docs in the repo capturing **context, decision, alternatives considered, consequences**, and status (proposed/accepted/superseded). They answer "why is it like this?" a year later and stop re-litigating decisions.

How I run them:
- Anyone can propose; template in `docs/adr/NNNN-title.md`; reviewed in a PR with a time box (e.g. one week), async first, a short sync only if contested.
- Decisions are reversible or not — spend effort proportional to that ("one-way vs two-way doors").
- Include an **exit/revisit condition** ("revisit if SignalStore events plugin becomes stable enough" / "when we reach v22").
- Link ADRs from lint rules and review comments so the rule has a rationale.
- Superseded, not deleted.

```markdown
# ADR-0012: Use NgRx SignalStore for feature state
Status: Accepted (2026-03-04)
Context: Mixed classic NgRx + ad-hoc BehaviorSubject services; onboarding cost; v21 zoneless migration.
Decision: New feature state uses @ngrx/signals signalStore behind a feature facade. Global cross-cutting state stays in classic Store.
Alternatives: Classic NgRx everywhere; plain signal services; TanStack Query.
Consequences: + less boilerplate, signal-native; - two patterns co-exist for ~2 quarters; migration guide in /docs.
Revisit: when <50% of features remain on classic store.
```

---

## B. Tricky / trap questions

### T1. "SOLID means you should have an interface for every service, right?"

**The trap:** Equating SOLID with ceremony — `IUserService` + `UserService` + `UserServiceImpl` for everything.

**Strong answer includes:**
- Abstractions pay off at **real seams**: 3rd-party integrations, environment-specific behaviour, multiple implementations, library extension points.
- In Angular, any class is already mockable in tests via `{ provide: UserService, useValue: mock }` — you don't need an interface to test.
- Interfaces in TS are erased; you'd need tokens anyway. Add an abstract class/token when the second implementation appears or when the dependency crosses a boundary you don't own.
- "SOLID is a tool for managing change, not a quota of interfaces."

### T2. "Should every feature service go behind a facade?"

**The trap:** Blanket facades — pass-through layers that double the code and hide nothing.

**Strong answer includes:**
- Use a facade where there's **complexity or likely change** behind it (store implementation, multi-source orchestration, a migration in progress).
- A simple CRUD service used by one component doesn't need one.
- Watch for facades becoming god objects; one facade per feature/bounded context.
- With classic NgRx, beware command-style actions via facades; dispatch events.

### T3. "We have a `BaseComponent` with common inputs, a `destroy$` subject and helper methods. Good idea?"

**The trap:** Defending inheritance for reuse.

**Strong answer includes:**
- `destroy$` is obsolete: `takeUntilDestroyed()` / `DestroyRef`.
- Common inputs → a host directive; helpers → pure functions or `inject()`-based composables.
- Base classes create hidden coupling and make lifecycle order surprising; changing them is an app-wide breaking change.
- Migration plan: stop extending for new code (lint rule / review), extract behaviours one by one, delete the base when the count hits zero.

### T4. "What's your code coverage target? 100%?"

**The trap:** Treating coverage as a quality goal.

**Strong answer includes:**
- Coverage measures what was *executed*, not what was *verified*. 100% targets produce assertion-free tests and tests coupled to implementation.
- Use coverage as a **floor and a diff signal**: e.g. no decrease on changed lines, ~80% on shared lib logic, higher for pure business rules, lower for glue code.
- Better quality signals: escaped defects, mutation score (e.g. Stryker) on critical logic, flaky-test rate, time to diagnose a failing test.
- "I'd rather have 70% coverage of meaningful behaviour than 100% of getters."

### T5. "We'll fix the tech debt in a hardening sprint before release."

**The trap:** Accepting batch debt repayment.

**Strong answer includes:**
- Hardening sprints get cut when deadlines slip, and they hide debt until then.
- Debt should be continuous capacity + boy-scout rule + tied to feature work in the same area.
- Make debt visible with metrics so product can prioritise it like any other work.
- A time-boxed "upgrade week" for a big Angular major can be fine — but it's planned, scoped, and has an outcome, not a dumping ground.

### T6. "Let's put common stuff in a `SharedModule` so every feature can import it."

**The trap:** The shared-module dumping ground.

**Strong answer includes:**
- With standalone (default since v19), there's no need; each component imports what it uses — precise dependencies and better tree-shaking.
- A `SharedModule` becomes a coupling magnet: every feature depends on everything; changing it triggers rebuilds/tests everywhere; circular dependencies.
- Replace with small, purpose-named libs (`shared/ui-button`, `shared/util-date`) with public APIs and boundary rules.
- Migration: Angular's standalone migration schematic, then delete the module.

### T7. "Isn't the Singleton pattern bad? Angular services are singletons."

**The trap:** Saying "all Angular services are singletons".

**Strong answer includes:**
- Only root-provided (`providedIn: 'root'` / `@Service()` default) services are app-wide singletons. Services provided in a route's `providers`, a component's `providers`, or an `EnvironmentInjector` are scoped — one per injector.
- Scoping is a design tool: a per-route store resets when the user leaves the feature; a per-component store gives each instance of a widget its own state.
- The "global mutable singleton" problem is about *mutable global state* with unclear ownership, which is a state-management design issue, not DI.

### T8. "Design patterns are Java stuff — do they matter in a frontend?"

**The trap:** Dismissing patterns, or reciting the GoF list.

**Strong answer includes:**
- Many GoF patterns are built into the platform: Observer (RxJS/signals), Decorator/Composition (host directives, interceptors as a chain of responsibility), Strategy (DI multi-providers), Adapter (DTO mappers), Facade, Factory (`useFactory`), Proxy (interceptors).
- What matters is the vocabulary for design discussion and recognising the *change axis* each one addresses.

---

## C. Code examples

### Chain of responsibility: functional interceptors

```typescript
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthStore).token();
  return next(token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req);
};

export const partnerErrorInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(
    catchError((err: HttpErrorResponse) => throwError(() => toAppError(err))), // adapter for errors
  );

export const appConfig: ApplicationConfig = {
  providers: [provideHttpClient(withInterceptors([authInterceptor, partnerErrorInterceptor]))],
};
```

Note: since **v22** `HttpClient` uses `FetchBackend` by default and `withFetch()` is a deprecated no-op; use `withXhr()` only if you need upload progress events.

### Composable instead of base class

```typescript
export function injectPagedList<T>(loader: (page: number) => Observable<readonly T[]>) {
  const page = signal(1);
  const items = rxResource({ params: () => page(), stream: ({ params }) => loader(params) });
  return {
    page: page.asReadonly(),
    items,
    next: () => page.update((p) => p + 1),
    prev: () => page.update((p) => Math.max(1, p - 1)),
  };
}

@Component({ /* ... */ })
export class OrdersPageComponent {
  private readonly api = inject(OrdersApi);
  protected readonly list = injectPagedList((p) => this.api.page(p));
}
```

### Deprecation in a shared library

```typescript
export class TableComponent {
  /** @deprecated since 8.2 — use `density="compact"`. Will be removed in 10.0. Migration: `ng update @acme/ui`. */
  readonly compact = input(false, { transform: booleanAttribute });
  readonly density = input<'comfortable' | 'compact'>('comfortable');
  protected readonly effectiveDensity = computed(() => (this.compact() ? 'compact' : this.density()));
}
```

Pair this with an `ng update` migration schematic (registered in the package's `migrations.json`) that rewrites `[compact]="true"` to `density="compact"` in consumer templates, and a lint rule (`@typescript-eslint/no-deprecated`) so consumers see it in their editor.

---

## D. Red flags

- "SOLID means lots of interfaces." → *Say instead:* "SOLID is about isolating reasons to change; I add abstractions at real seams."
- "We put a facade over every service." → "Facades at feature boundaries where they hide real complexity or a migration."
- "All our components extend `BaseComponent`." → "We share behaviour via host directives, `inject()`-based functions and composition."
- "Our target is 100% coverage." → "Coverage is a floor on changed code; I care about escaped defects and meaningful behavioural tests."
- "We'll clean it up in a hardening sprint." → "Debt is continuous capacity, visible on a register, tied to delivery and incident metrics."
- "Everything common goes in `SharedModule`." → "Small purpose-named libraries with public APIs and enforced boundaries."
- "Linting is personal preference." → "Lint encodes team decisions and architecture; formatting is automated so reviews focus on design."
- "We turned off `strictTemplates`, it was too noisy." → "We enabled it incrementally, starting with shared libs, and ratcheted the error count down."
- "I test private methods to get coverage." → "I test behaviour through the public surface — DOM, inputs, outputs, harnesses."
- "Patterns don't matter in frontend." → "Angular bakes most patterns into DI, RxJS/signals and interceptors; naming them helps design discussions."
- "I make architecture decisions and the team follows." → "I facilitate decisions via ADRs, make trade-offs explicit, and enforce the outcome with tooling rather than policing."
- "We break the component library API whenever needed; consumers adapt." → "Semver, deprecation with overlap, changelogs and `ng update` migrations."

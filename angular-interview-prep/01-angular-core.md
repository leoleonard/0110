# 01 — Angular Core

> **How to use this file:** read section A out loud. Each answer is sized for about 1–2 minutes of speaking. Use the "Go deeper" bullets only when the interviewer asks a follow-up. Section B covers trap questions, where the obvious answer is the mid-level one. Section C has longer code you should be able to write on a whiteboard, and section D lists phrases to avoid.
>
> **What senior-level interviewers are really probing:** whether you know *why* Angular works the way it does, not just the API. Can you explain how change detection is scheduled and what changed in recent versions (zoneless default in v21, OnPush default in v22)? Can you design a DI setup that keeps state correctly scoped? Can you pick signals or RxJS for the right reasons? Can you build reusable components (CVA, content projection, library entry points) that other teams can't misuse? They also check whether your knowledge is current, because many codebases still run v17–v20. Say which version a behaviour belongs to: "since v21…" or "before v22 the default was…". That shows you have done real migrations.

**Version anchor (Sept 2026):** Angular 22.2 is current. Key changes: v20 made zoneless stable. v21 made zoneless the default for new apps, made Vitest the default test runner and added experimental Signal Forms. v22 made OnPush the default, added `ChangeDetectionStrategy.Eager`, made Signal Forms stable, switched HttpClient to `FetchBackend` by default, added `@Service()` and made incremental hydration the default.

---

## A. Most commonly asked questions

### Q1. How do you design a reusable component? Talk about inputs, outputs, `model()` and content projection.

**Answer (1–2 min):**
- **The public API is a contract.** In a shared library, every input is something you will have to support. I keep the surface small, typed and hard to misuse. Required inputs use `input.required<T>()`. Optional inputs get sensible defaults. I use `transform` (e.g. `booleanAttribute`, `numberAttribute`) so `<lib-button disabled>` works like native HTML.
- **Signal-based APIs:** `input()` returns a read-only signal, `output()` returns an `OutputEmitterRef`, and `model()` gives a writable signal plus an automatic `xChange` output, which enables `[(x)]` two-way binding. I use `model()` only when the component genuinely owns and changes that state (e.g. `expanded`, `value`). Everything else is input down, output up.
- **Content projection over configuration.** Once a component needs a `headerText`, `headerIcon` and `headerTemplate` input, I switch to projection: `<ng-content select="[libCardHeader]">`. For repeated or context-dependent rendering (table cells, list items), I accept an `ng-template` via `contentChild(TemplateRef)` or a marker directive and render it with `ngTemplateOutlet` and a typed context.
- **Presentational vs container.** Library components are presentational: no HTTP, no store, only inputs and outputs. Feature containers handle data. This keeps the library testable and framework-state-agnostic.
- **Styling:** use CSS custom properties as the theming API, not `::ng-deep`. Keep default `ViewEncapsulation.Emulated`. Use `:host` for layout-level styles.
- Sound bite: *"In our component library the rule was: if a consumer needs `::ng-deep` or a fourth `xTemplate` input, the API is wrong, not the consumer."*

```typescript
@Component({
  selector: 'lib-disclosure',
  template: `
    <button type="button" (click)="expanded.set(!expanded())" [attr.aria-expanded]="expanded()">
      <ng-content select="[libDisclosureTitle]" />
    </button>
    @if (expanded()) {
      <div role="region"><ng-content /></div>
    }
  `,
  host: { '[class.is-disabled]': 'disabled()' },
})
export class DisclosureComponent {
  readonly expanded = model(false);                             // [(expanded)]
  readonly disabled = input(false, { transform: booleanAttribute });
  readonly toggled = output<boolean>();
}
```

**Go deeper:**
- `ng-content` is always instantiated, even when it sits inside a false `@if`. The *parent* creates projected content. For lazy or conditional content, take an `ng-template` instead.
- Signal queries (`viewChild`, `contentChildren`) return signals, so you can react to them with `computed` without `ngAfterViewInit` timing hacks.
- Templates can bind `protected` members, and private members since 22.1. Keep template-only state `protected` so it is not part of the public TS API.

---

### Q2. Walk me through the lifecycle hooks. How do signal inputs change things, and what are `afterNextRender` / `afterRenderEffect` for?

**Answer (1–2 min):**
- **Order:** `constructor` → `ngOnChanges` (only if the component has inputs bound) → `ngOnInit` → `ngDoCheck` → `ngAfterContentInit` → `ngAfterContentChecked` → `ngAfterViewInit` → `ngAfterViewChecked`. On later checks you get `ngOnChanges`, then `ngDoCheck`, then the `*Checked` hooks. On teardown, `ngOnDestroy` runs (or use `DestroyRef.onDestroy`).
- **Constructor vs `ngOnInit`:** input values are not set in the constructor. The constructor is for `inject()` and wiring. `ngOnInit` is the first point where decorator-based inputs are available.
- **With signal inputs, most hooks become unnecessary:**
  - `ngOnChanges` for derived values → `computed(() => ...)`.
  - `ngOnChanges` for side effects on change → `effect()`, or a `resource` whose `params` read the input.
  - `ngAfterViewInit` for a `@ViewChild` → `viewChild()` signal plus `computed` or `afterRenderEffect`.
  - Teardown → `inject(DestroyRef)` / `takeUntilDestroyed()`.
  - `ngOnChanges` still fires for signal inputs, but I rarely need it.
- **Render hooks:** `afterNextRender` runs once after the next render. `afterRender`-style effects run after every render. Use them for DOM work that must happen after Angular has updated the DOM: measuring, third-party widgets (charts, maps) or focus management. They run **only in the browser**, never during SSR. That makes them the correct replacement for `if (isPlatformBrowser) { ... }` in `ngAfterViewInit`.
- `afterRenderEffect` is a signal-aware version. It re-runs after render only when the signals it reads change. It supports phases (`earlyRead`, `write`, `mixedReadWrite`, `read`) so Angular can batch DOM reads and writes and avoid layout thrashing.

```typescript
export class ChartComponent {
  readonly data = input.required<Point[]>();
  private readonly canvas = viewChild.required<ElementRef<HTMLCanvasElement>>('canvas');
  private chart?: ThirdPartyChart;

  constructor() {
    afterNextRender(() => { this.chart = new ThirdPartyChart(this.canvas().nativeElement); });
    afterRenderEffect(() => { this.chart?.update(this.data()); }); // re-runs when data() changes
    inject(DestroyRef).onDestroy(() => this.chart?.destroy());
  }
}
```

**Go deeper:**
- Reading a *required* signal input in the constructor throws (NG0950): the value does not exist yet. A non-required one silently returns the default. That is the subtler bug (see T4).
- `ngDoCheck` runs on every CD pass for that component, so keep it cheap or avoid it.
- In zoneless apps, render hooks still run after each CD pass. They do not *schedule* a CD pass.

---

### Q3. Standalone vs NgModules. How would you migrate a large app?

**Answer (1–2 min):**
- **Standalone is the default** (`standalone: true` is implied since v19). Each component declares its own `imports`. This gives explicit dependencies, better tree-shaking, lazy-loading of a single component via `loadComponent`, and a much simpler mental model. There is no "which module declares this?" hunt and no `SharedModule` that pulls in everything.
- **NgModules still work.** They are not deprecated for existing code. You mainly meet them in legacy apps and in third-party libraries. You can mix them: standalone components can import NgModules, and module-based components can import standalone ones.
- **Bootstrap:** `bootstrapApplication(AppComponent, appConfig)`, where `appConfig.providers` uses `provideRouter`, `provideHttpClient(withInterceptors([...]))` and similar. `forRoot()` patterns become `provideX()` functions.
- **Migration story (what I would actually do):**
  1. Run `ng generate @angular/core:standalone`. It works in three passes: convert declarations to standalone, remove unnecessary NgModules, and switch to standalone bootstrap. Commit after each pass.
  2. Migrate leaf and shared UI components first. In a component library, standalone components are a big win for consumers because they import exactly what they use.
  3. Replace `RouterModule.forChild` lazy modules with `loadChildren: () => import('./routes')` exporting `Routes`, and with `loadComponent`.
  4. Replace `SharedModule`. Watch for providers that lived in a module: they now need a home (`providedIn: 'root'`/`@Service()`, route `providers`, or `bootstrapApplication` providers).
  5. Pair the work with the v21 migrations for `CommonModule` → direct imports and control-flow migration (`*ngIf` → `@if`).

**Go deeper:** the risky part is **provider scope, not declarations**. A service provided in a lazy NgModule had its own instance per lazy module. When you move it to a route's `providers`, the scoping is similar. When you move it to root, it becomes a singleton, which can change behaviour (see T6).

---

### Q4. Explain Angular's DI hierarchy and provider scopes.

**Answer (1–2 min):** there are **two hierarchies**:

- **Environment injectors:** the `platform` injector sits above the `root` injector (created by `bootstrapApplication`). Below root are child environment injectors created by **lazy-loaded routes** or route-level `providers`, or by `createEnvironmentInjector`.
- **Element (node) injectors:** created by the `providers`/`viewProviders` of components and directives, following the DOM/view tree.
- **Resolution order:** Angular walks the element injectors up the view tree first. If nothing matches, it walks the environment injectors: route → root → platform → `NullInjector` (error, unless the dependency is optional).

**Scopes I choose deliberately:**

| Where | Lifetime / sharing | Use for |
|---|---|---|
| `providedIn: 'root'` / `@Service()` | App singleton, tree-shakable | Stateless API clients, app-wide state |
| `providedIn: 'platform'` | Shared across multiple apps on the page | Rare: micro-frontends |
| Route `providers: [...]` | One instance per route environment injector, lazy | Feature-scoped state / feature store |
| Component `providers` | One instance per component instance, destroyed with it | Per-widget state (e.g. a store per table) |
| Component `viewProviders` | Like `providers`, but invisible to projected content | Hiding internals from `ng-content` children (T3) |

- **`InjectionToken<T>`** is for non-class dependencies (config, feature flags, strategies). Give it a `factory` so it is tree-shakable and has a default.
- **`multi: true`** collects several providers into an array. Examples: `HTTP_INTERCEPTORS` (legacy), `NG_VALUE_ACCESSOR`, or your own plugin tokens.
- **Resolution modifiers:** `inject(X, { optional: true, self: true, skipSelf: true, host: true })`.
  - `self`: only this element's injector.
  - `skipSelf`: start at the parent. This is the classic pattern for nested components finding a parent of the same type, e.g. a nested menu.
  - `host`: stop at the host component boundary.
  - `optional`: return `null` instead of throwing.
- **`inject()` vs constructor injection:** `inject()` is the recommended style. It works in functions (guards, interceptors, resolvers), avoids constructor boilerplate with inheritance, and works with field initialisers and ES decorators semantics. It must run in an **injection context**: field initialisers, the constructor, factory functions, or `runInInjectionContext`.
- **v22 `@Service()`:** a stable decorator that marks a class as a service and **auto-provides it in root by default**, like `@Injectable({ providedIn: 'root' })` but with clearer intent. Use `@Service({ autoProvided: false })` when you want to provide it manually (e.g. per route or per component), and `@Service({ factory: () => ... })` for a custom factory. `@Injectable` still works, and 22.2 ships an "injectable to service" migration.

```typescript
export interface LibConfig { density: 'compact' | 'comfortable'; }
export const LIB_CONFIG = new InjectionToken<LibConfig>('LIB_CONFIG', {
  factory: () => ({ density: 'comfortable' }),          // tree-shakable default
});
export function provideLibConfig(config: Partial<LibConfig>): Provider {
  return { provide: LIB_CONFIG, useValue: { density: 'comfortable', ...config } };
}

// Nested tree item finding its parent (not itself)
export class TreeItemComponent {
  readonly parent = inject(TreeItemComponent, { skipSelf: true, optional: true });
}
```

**Go deeper:**
- `useClass` / `useExisting` / `useValue` / `useFactory`: `useExisting` creates an alias, so there is **one** instance under two tokens. `useClass` creates a new instance.
- v22 added `injectAsync(() => import('./heavy').then(m => m.HeavyService))` to lazy-load an injectable's code on demand.
- Library pattern: expose `provideMyLib(options)` returning `EnvironmentProviders` via `makeEnvironmentProviders`. This makes it impossible to add those providers to a component's `providers` by mistake.

---

### Q5. Signals vs RxJS: when do you use which, and how do they interoperate?

**Answer (1–2 min):**
- **Signals are for state:** synchronous values that change over time and that the UI reads. They are glitch-free and fine-grained, and Angular's CD knows exactly which views read them. `signal` holds a value, `computed` derives one (memoised and lazy), and `effect` runs side effects out to non-signal APIs (logging, `localStorage`, imperative DOM or 3rd-party).
- **RxJS is for events and async orchestration over time:** debounce, `switchMap` cancellation, retry and backoff, websockets, merging streams, and anything where *time* or *cancellation semantics* matter.
- **The newer primitives:**
  - `linkedSignal`: writable state that **resets when a source changes**. Example: the selected item resets when the list changes, but the user can still pick one.
  - `resource({ params, loader })`: async data driven by signals. It exposes `value()`, `status()`, `isLoading()`, `error()`, `hasValue()` and `reload()`, and it aborts stale requests via `abortSignal`. The option is **`params`**; it was `request` in earlier previews.
  - `httpResource(() => url)`: the same thing, built on HttpClient, so interceptors apply.
  - `rxResource({ params, stream })`: when the loader is an Observable (the option is `stream`, formerly `loader`).
- **Interop (`@angular/core/rxjs-interop`):** `toSignal(obs$, { initialValue })` (auto-unsubscribes via `DestroyRef`, needs an injection context), `toObservable(sig)`, `takeUntilDestroyed()`, and `outputFromObservable`.
- **How I decide:** *"State that the template reads → signal. Events and async pipelines → RxJS, converted to a signal at the edge with `toSignal`. A simple 'fetch when X changes' → `httpResource`, no RxJS needed."*

```typescript
export class UserSearchComponent {
  private readonly http = inject(HttpClient);
  readonly query = signal('');

  // RxJS where time/cancellation matter, signal at the edge
  readonly results = toSignal(
    toObservable(this.query).pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => q.length < 2 ? of([]) : this.http.get<User[]>('/api/users', { params: { q } })),
    ),
    { initialValue: [] as User[] },
  );

  // Simple "load when id changes": no RxJS
  readonly userId = input.required<string>();
  readonly user = httpResource<User>(() => `/api/users/${this.userId()}`);

  // Resets to first option whenever options change, still user-writable
  readonly options = input.required<Option[]>();
  readonly selected = linkedSignal(() => this.options()[0]);
}
```

**Go deeper:**
- `computed` must stay pure. It must not write signals or make HTTP calls.
- `effect` is the last resort, not a `watch()` (see T2).
- NgRx 22: SignalStore (`@ngrx/signals`) is the recommended default for new feature state. Classic Store still fits large event-driven apps that want Redux DevTools and strict unidirectional flow, and `store.selectSignal()` bridges it to signals.

---

### Q6. zone.js vs zoneless: how is change detection scheduled in each?

**Answer (1–2 min):**
- **With zone.js:** zone.js monkey-patches every async API (`setTimeout`, promises, DOM events, XHR). When a task finishes, `NgZone.onMicrotaskEmpty` fires and Angular runs `ApplicationRef.tick()` from the root. It is "magic": you mutate anything anywhere and the UI updates. The costs are that CD runs far more often than needed, zone.js adds bundle weight and startup cost, async stack traces are noisy, and native `async/await` has to be downlevelled.
- **Zoneless:** stable in v20, and the **default for new apps since v21** (zone.js not included; opt back in with `provideZoneChangeDetection()`). Angular schedules CD only when it is **notified**:
  - a signal read in a template changes (`set`/`update`);
  - `ChangeDetectorRef.markForCheck()` is called (the `AsyncPipe` does this for you);
  - a bound template or host event listener fires;
  - `ComponentRef.setInput()` is called, or a view is attached or removed.
- **What does *not* trigger it:** mutating a plain field in `setTimeout`, a promise `.then`, a raw `addEventListener`, or a third-party callback (see T7).
- **Migration of an older app:** add `provideZonelessChangeDetection()` and remove `zone.js` from `polyfills` (in angular.json and the test config). Make components OnPush-compatible first: if it works with OnPush + signals/async pipe, it works zoneless. Replace `NgZone.onStable`/`onMicrotaskEmpty` usage with `afterNextRender`. `NgZone.run`/`runOutsideAngular` become no-ops in effect.
- **SSR:** without zones, Angular cannot know when the app is "stable". Use the `PendingTasks` service (`pendingTasks.run(async () => ...)`) for async work that must finish before serialisation. HttpClient and the router already register their own tasks.

**Go deeper:** in tests, `fakeAsync`/`tick` require zone.js. In zoneless tests, use `await fixture.whenStable()` or Vitest fake timers (`vi.useFakeTimers()`) instead (see Q15).

---

### Q7. Default/Eager vs OnPush change detection. What changed in v22?

**Answer (1–2 min):**
- **v22 breaking change:** components with no explicit `changeDetection` are now **OnPush by default**. The old `ChangeDetectionStrategy.Default` is deprecated and aliased by the new **`ChangeDetectionStrategy.Eager`**. `ng update` adds `Eager` to components that relied on the old behaviour. Before v22, the default was check-always, and teams added `OnPush` by lint rule.
- **Eager:** checked on every CD pass that reaches it.
- **OnPush:** the view is checked only when it is marked dirty:
  1. an input's **reference** changes (`===`);
  2. an event handler bound in its template or host (or in a child's) fires;
  3. a **signal read in its template** changes (this marks only that view for refresh, so ancestors are not re-checked unnecessarily);
  4. the `async` pipe receives a value (it calls `markForCheck`);
  5. `markForCheck()` is called explicitly.
- **`markForCheck()` vs `detectChanges()`:**
  - `markForCheck()` marks this view *and its ancestors* dirty so the **next scheduled** CD pass checks them. It is cheap and correct in almost all cases.
  - `detectChanges()` **synchronously** checks this view and its children right now. Use it for rare cases like a detached view or 3rd-party callbacks that need an immediate DOM update.
- **Immutability is the contract:** `this.items = [...this.items, x]`, not `this.items.push(x)` (T1). With signals, `items.update(xs => [...xs, x])`. Signals use `Object.is` equality, so mutating in place and calling `set` with the same reference does nothing.
- Sound bite: *"OnPush + signals is effectively 'Angular tracks dependencies for me'. The v22 default makes explicit what well-run codebases already enforced."*

**Go deeper:**
- `ChangeDetectorRef.checkNoChanges` was removed in v22.
- `detach()`/`reattach()` still exist for extreme cases (e.g. a live-ticker grid you refresh on your own schedule).
- When upgrading an old enterprise app to v22, audit the components where `ng update` added `Eager`. Each one is tech debt telling you that component mutates state or relies on global CD.

---

### Q8. Explain the built-in control flow and `@defer`. Why does `track` matter?

**Answer (1–2 min):**
- **Control flow blocks:** `@if / @else if / @else`, `@for (...; track ...) { } @empty { }`, `@switch / @case / @default`, and `@let` for template-local variables. They are built into the compiler, so no `CommonModule` import is needed, type narrowing is better (`@if (user(); as u)`), and they are faster than the structural directives. `*ngIf`/`*ngFor`/`*ngSwitch` have been deprecated since v20. Migrate with `ng generate @angular/core:control-flow`.
- **`track` is mandatory in `@for`**. Angular uses the key to match old items to new DOM nodes.
  - Track by a stable identity (`track item.id`): when the array is replaced by a fresh API response, existing rows keep their DOM, component state, focus and animations. Only the differences are applied.
  - `track $index` is fine for static lists but wrong for lists that reorder or insert.
  - `track item` (object identity) recreates every row whenever objects are re-fetched or cloned, which can be costly and loses input focus or child state.
  - `@for` also exposes `$index`, `$first`, `$last`, `$even`, `$odd` and `$count`.
- **`@defer`** lazy-loads a template section *and its standalone dependencies* into a separate chunk:
  - Triggers: `on idle` (default; v22 adds a timeout option), `on viewport`, `on interaction`, `on hover`, `on immediate`, `on timer(2s)`, and `when condition`.
  - `prefetch on ...` downloads the chunk early without rendering.
  - Sub-blocks: `@placeholder (minimum 500ms)`, `@loading (after 100ms; minimum 1s)` (the timings avoid flicker) and `@error`.
- **With SSR,** `hydrate on ...` enables **incremental hydration**, which is the default behaviour in v22 hydrated apps (see Q13).

```html
@let user = currentUser();
@if (user) {
  <h2>{{ user.name }}</h2>
} @else {
  <app-login-prompt />
}

@for (order of orders(); track order.id) {
  <app-order-row [order]="order" />
} @empty {
  <p>No orders yet.</p>
}

@defer (on viewport; prefetch on idle) {
  <app-analytics-chart [data]="stats()" />
} @placeholder (minimum 300ms) {
  <div class="chart-skeleton"></div>
} @loading (after 150ms; minimum 500ms) {
  <lib-spinner />
} @error {
  <p>Chart failed to load.</p>
}
```

**Go deeper:**
- Deferred dependencies must be standalone and **not referenced elsewhere** in the same file (e.g. in a `viewChild` type used as a value). Otherwise they get pulled back into the eager bundle. Check the build output for the lazy chunk.
- `on viewport` needs a single root element in `@placeholder` (or an explicit template ref trigger).
- Put `@defer` below the fold, not around the LCP element.

---

### Q9. How do you structure routing: guards, resolvers, lazy loading?

**Answer (1–2 min):**
- **Functional guards and resolvers** (`CanActivateFn`, `CanMatchFn`, `CanDeactivateFn`, `ResolveFn`) use `inject()` inside. Class-based guards are deprecated in style and much more boilerplate.
- **`canMatch` vs `canActivate`:**
  - `canMatch` runs *during matching*. If it returns false, the router **tries the next matching route**, and a lazy route's code **is not downloaded**. Use it for role- or feature-flag-based variants of the same path, and to avoid shipping admin code to non-admins.
  - `canActivate` runs after the route matched. It blocks or redirects, but the lazy chunk has already loaded.
  - In v22, `CanMatchFn` also receives the current snapshot as a third argument.
- **Redirects:** return a `UrlTree` or a `RedirectCommand` (lets you pass navigation extras such as `skipLocationChange`). Since 22.1 you can also *throw* a `RedirectCommand`. Never call `router.navigate()` inside a guard and then return false.
- **Lazy loading:** `loadComponent: () => import('./x.component')` (default export supported) for single pages, and `loadChildren: () => import('./admin.routes')` for feature route files. Route-level `providers` create a feature-scoped environment injector.
- **Preloading:** `withPreloading(PreloadAllModules)` for small apps. For large ones, use a custom `PreloadingStrategy` (e.g. preload routes flagged `data: { preload: true }`, or skip on slow connections via `navigator.connection`). Quicklink-style viewport preloading is also an option.
- **`withComponentInputBinding()`** binds route params, query params, `data` and resolver results straight to `input()`s. Components stop depending on `ActivatedRoute`, which makes them easier to test and reuse.
- **Resolvers:** use them sparingly. They block navigation, so the user sees nothing happen. I usually prefer navigating immediately and showing a skeleton with `httpResource`. Resolvers fit data the page genuinely can't render without, like an entity for an edit form.

```typescript
export const adminOnly: CanMatchFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.hasRole('admin') ? true : new RedirectCommand(router.parseUrl('/forbidden'));
};

export const routes: Routes = [
  { path: 'admin', canMatch: [adminOnly], loadChildren: () => import('./admin/admin.routes') },
  {
    path: 'orders/:id',
    loadComponent: () => import('./orders/order-detail.component'),
    resolve: { order: (route: ActivatedRouteSnapshot) => inject(OrderApi).get(route.paramMap.get('id')!) },
    providers: [OrderDetailStore],                         // route-scoped instance
  },
];

// app.config.ts
provideRouter(routes, withComponentInputBinding(), withPreloading(PreloadAllModules));

// order-detail.component.ts: params/resolved data arrive as inputs
export default class OrderDetailComponent {
  readonly id = input.required<string>();
  readonly order = input.required<Order>();
}
```

**Go deeper:** v22 changed the default `paramsInheritanceStrategy` to `'always'`, so child routes see parent params. Also in v22, `provideRoutes()` was removed, and the router's `lastSuccessfulNavigation` has been a signal since v21.

---

### Q10. Reactive forms vs template-driven vs Signal Forms. Which would you pick today?

**Answer (1–2 min):**
- **Template-driven (`ngModel`):** simple forms, logic in the template. It is hard to unit-test and to handle dynamic structure.
- **Reactive forms (`FormGroup`/`FormControl`):** explicit model in TS, observable `valueChanges`, dynamic arrays, and **strictly typed since v14**. Use `fb.nonNullable.group(...)` (or `nonNullable: true`) so `reset()` goes back to the initial value, not `null`. `getRawValue()` includes disabled controls, while `value` omits them. This is the mature, battle-tested option and what most enterprise codebases run.
- **Signal Forms (`@angular/forms/signals`):** experimental in v21, **stable in v22**. You own a signal model, and `form(model, schema)` builds a field tree over it. Validation is declared in a schema function (`required`, `email`, `min`/`max`, `minLength`/`maxLength`, `pattern`, `validate`, `validateAsync`, `validateHttp`, `debounce`, and conditional logic via `applyWhen`, `disabled`, `hidden`, `readonly`). You bind with `[formField]`. Each field exposes signals: `value()`, `valid()`, `touched()`, `dirty()`, `errors()` and `pending()`. `submit(form, action)` handles submit state.
- **How I'd decide:**
  - Greenfield on v22 → Signal Forms. They fit OnPush/zoneless naturally, need no `valueChanges` subscriptions, and keep the model as the single source of truth.
  - Existing large reactive-forms estate → keep it and migrate opportunistically. The two coexist, and Signal Forms can shim existing CVAs.
  - Tiny forms → either works.

```typescript
import { form, required, email, minLength, submit, FormField } from '@angular/forms/signals';

@Component({
  selector: 'app-signup',
  imports: [FormField],
  template: `
    <form (submit)="onSubmit($event)">
      <input type="email" [formField]="f.email" />
      @if (f.email().touched() && f.email().invalid()) {
        <span class="error">Enter a valid email</span>
      }
      <input type="password" [formField]="f.password" />
      <button [disabled]="f().invalid() || f().pending()">Sign up</button>
    </form>
  `,
})
export class SignupComponent {
  private readonly api = inject(AuthApi);
  readonly model = signal({ email: '', password: '' });
  readonly f = form(this.model, p => {
    required(p.email);
    email(p.email);
    required(p.password);
    minLength(p.password, 12);
  });

  onSubmit(e: Event) {
    e.preventDefault();
    submit(this.f, async () => { await this.api.signup(this.model()); });
  }
}
```

**Reactive forms, typed, with custom sync + async validators:**

```typescript
export const noWhitespace: ValidatorFn = c =>
  typeof c.value === 'string' && c.value.trim() !== c.value ? { whitespace: true } : null;

export function usernameTaken(api: UserApi): AsyncValidatorFn {
  return c => timer(300).pipe(                      // debounce: re-subscription cancels previous timer
    switchMap(() => api.exists(c.value)),
    map(exists => (exists ? { taken: true } : null)),
    catchError(() => of(null)),                     // don't block the form on a network error
  );
}

export class ProfileFormComponent {
  private readonly fb = inject(FormBuilder).nonNullable;
  readonly form = this.fb.group({
    username: this.fb.control('', {
      validators: [Validators.required, noWhitespace],
      asyncValidators: [usernameTaken(inject(UserApi))],
      updateOn: 'blur',
    }),
    tags: this.fb.array<string>([]),
  });
  // this.form.getRawValue() is typed { username: string; tags: string[] }
}
```

**Go deeper:**
- Async validators only run once the sync validators pass, and the control is `PENDING` meanwhile.
- Cross-field validators go on the group.
- Don't forget `updateOn: 'blur'` for expensive checks.

---

### Q11. How do you set up HttpClient and interceptors in a modern app?

**Answer (1–2 min):**
- `provideHttpClient(withInterceptors([authInterceptor, errorInterceptor]))`. **Functional interceptors** (`HttpInterceptorFn`) run in registration order on the way out and in reverse on the way back. Class-based interceptors need `withInterceptorsFromDi()` and are legacy.
- **v22: `FetchBackend` is the default.** `withFetch()` is deprecated (a no-op). Fetch cannot report **upload** progress. If you need an upload progress bar, use `provideHttpClient(withXhr())`, which puts back `HttpXhrBackend`. The `reportProgress` option is deprecated in favour of `reportUploadProgress` / `reportDownloadProgress`. Since v21 HttpClient is provided in root, but you still call `provideHttpClient(...)` to configure interceptors and the backend.
- **`HttpContextToken`s** pass per-request metadata to interceptors, e.g. `SKIP_AUTH`, `CACHE_TTL` or `RETRY_COUNT`. This avoids magic headers or URL matching.
- **Typical interceptor stack:**
  1. base URL / API version;
  2. auth token + 401 refresh (single in-flight refresh shared by concurrent requests; full example in section C);
  3. retry with backoff **only for idempotent requests** (GET) and only for network or 5xx errors, never for 4xx;
  4. central error mapping to a typed domain error plus user notification;
  5. loading indicator / correlation-ID header.
- Keep UI concerns (toasts) out of feature services, but let callers opt out through context tokens.

```typescript
export const RETRYABLE = new HttpContextToken<boolean>(() => true);

export const retryInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.method !== 'GET' || !req.context.get(RETRYABLE)) return next(req);
  return next(req).pipe(
    retry({
      count: 2,
      delay: (err: unknown, attempt) =>
        err instanceof HttpErrorResponse && (err.status === 0 || err.status >= 500)
          ? timer(2 ** attempt * 300)
          : throwError(() => err),                 // don't retry 4xx
    }),
  );
};

// Opt out per call
this.http.get('/api/report', { context: new HttpContext().set(RETRYABLE, false) });
```

**Go deeper:**
- Interceptors also apply to `httpResource`, since it is built on HttpClient.
- `HttpClient.jsonp` is deprecated since 22.2.
- For Swagger/OpenAPI-backed REST APIs, I generate typed clients (e.g. openapi-generator) and keep the interceptors generic.

---

### Q12. Where do you use `effect()` versus `computed()` in a component library context?

**Answer (1–2 min):**
- `computed()` handles *everything derived*: CSS classes from inputs, filtered or sorted lists, ARIA attributes, "is this the selected item". It is lazy, memoised and pure.
- `effect()` synchronises signal state with a non-signal world: `localStorage`, analytics, imperatively driving a 3rd-party widget, or logging. In a library it is rare. If I see an effect in a PR, my first question is "could this be `computed`, `linkedSignal`, or `resource`?"
- `effect` runs asynchronously during change detection, so it is not a synchronous watcher. DOM-touching work belongs in `afterRenderEffect`.
- Since v19, writing signals inside an effect is allowed (no more `allowSignalWrites`). *Allowed* doesn't mean *advisable*, though: it creates hidden data flow and extra CD cycles (T2).
- Effects created in a component/service are cleaned up with it. Created elsewhere, they need `{ injector }`. Use `onCleanup` inside for timers and subscriptions.

---

### Q13. Explain SSR and hydration: full vs incremental, event replay, transfer state.

**Answer (1–2 min):**
- **SSR** renders HTML on the server (`@angular/ssr`, `ng add @angular/ssr`, with per-route render modes: server, prerender or client). This gives better LCP/SEO and a faster first paint.
- **Hydration** (`provideClientHydration()`) reuses the server DOM instead of destroying and re-rendering it. That avoids flicker and CLS.
- **Full hydration** hydrates the whole app at bootstrap. **Incremental hydration** keeps `@defer (hydrate on viewport | interaction | idle | ... | never)` sections dehydrated (server HTML shown, JS not downloaded) until the trigger fires. It is the **default behaviour in v22**; before that you opted in with `withIncrementalHydration()`.
- **Event replay** captures user clicks that happen before hydration finishes and replays them afterwards, so early interactions are not lost (`provideClientHydration(withEventReplay())`; the CLI adds it to new SSR projects, but check older apps where it has to be enabled explicitly).
- **Transfer cache:** GET/HEAD requests made during SSR are serialised into the page and reused on the client, so the API is not called twice. It is on by default with hydration and configurable via `withHttpTransferCacheOptions`. For non-HTTP data, use `TransferState` with a `makeStateKey`.
- **Browser-only APIs:** `window`, `document`, `localStorage` and `IntersectionObserver` do not exist on the server.
  - Put DOM work in `afterNextRender`/`afterRenderEffect`, which never run on the server.
  - Inject `DOCUMENT` rather than using the global.
  - Guard truly platform-specific services with `isPlatformBrowser(inject(PLATFORM_ID))` or provide a server implementation.
- **Hydration mismatch:** the client DOM must match the server DOM (see T8). Common causes are invalid HTML nesting, direct DOM manipulation, and time- or random-dependent rendering.

---

### Q14. How do you approach Angular performance problems?

**Answer (1–2 min):** measure first, then fix the category that is actually slow.

- **Measure:** Lighthouse and field Core Web Vitals (LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1), Chrome Performance panel, and the **Angular DevTools profiler**, which shows which components' CD took how long and what triggered it. Use bundle analysis with `ng build --stats-json` plus esbuild's analyzer or source-map-explorer.
- **Runtime / change detection:**
  - OnPush everywhere (the default since v22) + signals, so only views that read a changed signal refresh.
  - Stable `track` in `@for`.
  - Memoise with `computed` or **pure pipes** instead of calling methods in templates. A method call in the template runs on every check.
  - Before zoneless: `NgZone.runOutsideAngular` for high-frequency events (scroll, mousemove, rAF loops, websockets) and re-enter only to update state.
- **Large lists:** CDK virtual scrolling (`cdk-virtual-scroll-viewport`), pagination, or `@defer` for below-the-fold sections.
- **Loading:** lazy routes (`loadComponent`/`loadChildren`), `@defer`, preloading strategy, SSR + incremental hydration, and **bundle budgets** in `angular.json` to catch regressions in CI.
- **Images:** `NgOptimizedImage` (`ngSrc`) enforces width/height (prevents CLS), lazy-loads by default, adds `fetchpriority=high` for `priority` images (LCP), generates `srcset` with a loader, and warns in dev about common mistakes.
- **INP:** keep event handlers light. Break long tasks up (yield, or `scheduler.yield()` where supported). Debounce input-driven work.
- Tie it to impact: *"I'd report it as 'LCP p75 on the dashboard went from 3.4s to 2.1s after deferring the charts and fixing the hero image', not 'I added OnPush'."*

**Go deeper:**
- Pure pipe: runs only when the input reference changes (default `pure: true`).
- Impure pipe: runs on every CD pass. `AsyncPipe` is impure by necessity. Avoid writing impure pipes; use `computed` instead.

---

### Q15. How do you test Angular apps today?

**Answer (1–2 min):**
- **Runner:** **Vitest has been the default for new projects since v21.** Karma is legacy/deprecated, and Jest support was experimental and isn't the recommended path. Existing Jest setups (e.g. via community builders) keep working, but I would move new work to Vitest.
- **Pyramid:** lots of fast unit tests for services, pure functions and signal stores. Component tests through TestBed. A few e2e tests (Playwright/Cypress) for critical journeys.
- **Component test philosophy (Testing Library style):** test what the user sees and does (roles, labels, text), not private fields. It survives refactors. In a component library, add **CDK component harnesses** (`ComponentHarness`), shipped as a secondary entry point (`@acme/ui/button/testing`) so consuming teams test against a stable API instead of your DOM structure. Angular Material does the same.
- **OnPush/signals:** set inputs with `fixture.componentRef.setInput('name', value)` (it marks the view dirty correctly; assigning `component.name = x` does not work for signal inputs or OnPush), then `await fixture.whenStable()`.
- **HTTP:** `provideHttpClient()` + `provideHttpClientTesting()`, then `HttpTestingController.expectOne(...).flush(...)` and `verify()` in `afterEach`.
- **Zoneless caveat:** `fakeAsync`/`tick`/`flush` need zone.js. In a zoneless project, use `await fixture.whenStable()`, `vi.useFakeTimers()` + `vi.advanceTimersByTime()`, or real async. `fixture.autoDetectChanges()` helps component tests behave like the running app.

```typescript
describe('UserCardComponent', () => {
  it('shows the name and emits on select', async () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('user', { id: '1', name: 'Ada' });
    const selected = vi.fn();
    fixture.componentInstance.selected.subscribe(selected);
    await fixture.whenStable();

    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    expect(button.textContent).toContain('Ada');
    button.click();
    expect(selected).toHaveBeenCalledWith('1');
  });
});

describe('UserApi', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());

  it('loads users', async () => {
    const promise = firstValueFrom(TestBed.inject(UserApi).list());
    http.expectOne('/api/users').flush([{ id: '1', name: 'Ada' }]);
    expect(await promise).toHaveLength(1);
  });
});
```

**Go deeper:**
- Use harnesses where they exist (Material, CDK, your own lib): `TestbedHarnessEnvironment.loader(fixture).getHarness(MatButtonHarness.with({ text: 'Save' }))`.
- v22 adds `TestBed.getLastFixture()`.

---

### Q16 (bonus, library owners). How is an Angular app and library built? Budgets, environments, secondary entry points?

**Answer (1–2 min):**
- **Application builder:** `@angular/build:application` uses esbuild for builds and a Vite-based dev server. It has been the default since v17/v18 and replaces the webpack `browser` builder. It is much faster and handles SSR/prerender in the same builder. Migrate older apps with `ng update`'s builder migration.
- **Budgets:** `initial`, `anyComponentStyle`, `anyScript` and similar, with warning and error thresholds in `angular.json`. They fail CI on bundle regressions. That makes performance measurable, which matters for "customer-focused, measurable improvements".
- **Source maps:** enable them in production only if you upload them to your error tracker (Sentry etc.) and don't serve them publicly (`"sourceMap": { "scripts": true, "hidden": true }`).
- **Environments:** `fileReplacements` bakes values in at **build time**, one artefact per environment. For "build once, deploy many" (Docker/K8s), load `config.json` at **runtime** via `provideAppInitializer(() => inject(ConfigService).load())` and expose it through an `InjectionToken`. I prefer runtime config in enterprise pipelines.
- **Libraries:** `ng generate library` → built with **ng-packagr** into the Angular Package Format (partial-Ivy compiled, FESM bundles).
  - **Secondary entry points** (`@acme/ui/button`, `@acme/ui/table`) each have their own `ng-package.json` and `public-api.ts`. Consumers import only what they use, entry points can have different peer deps, and CDK-style `/testing` harness entry points are possible.
  - Declare `@angular/*` as `peerDependencies` (never `dependencies`) and export only the public API.
  - Version with semver, and ship `ng update` schematics for breaking changes if the lib is widely used.

```json
// angular.json (excerpt)
"budgets": [
  { "type": "initial", "maximumWarning": "500kB", "maximumError": "1MB" },
  { "type": "anyComponentStyle", "maximumWarning": "4kB", "maximumError": "8kB" }
]
```

```text
projects/ui/
  ng-package.json            -> primary entry: @acme/ui
  src/public-api.ts
  button/
    ng-package.json          -> { "lib": { "entryFile": "public-api.ts" } }  => @acme/ui/button
    public-api.ts
    testing/                 -> @acme/ui/button/testing (harnesses)
      ng-package.json
      public-api.ts
  table/ ...                 -> @acme/ui/table
```

**Go deeper:**
- Secondary entry points must not import each other through relative paths. Use the package path (`@acme/ui/core`), or ng-packagr will complain and duplicate code.
- Watch for circular entry-point dependencies.

---

## B. Tricky / trap questions

### T1. "My OnPush component doesn't update when I push an item into the array input. Why?"

**The trap:** "Call `detectChanges()`" or "switch to Default". Both hide the design problem.

**Strong answer includes:**
- OnPush compares input **references** with `===`. `push()` mutates the same array, so the reference is unchanged and the child is not marked dirty.
- The fix is immutable updates at the source: `items = [...items, x]`, or with signals `items.update(xs => [...xs, x])`. Signals also use `Object.is`, so `items().push(x); items.set(items())` does not notify either.
- `markForCheck()` would work but spreads the "mutation" pattern. Use it only when you *can't* control the source (e.g. a 3rd-party callback).
- In v22 this bites more teams, because OnPush is now the default and code that relied on the old default mutates everywhere. `ng update` sets `Eager` on those components. Plan to remove it.
- Mention `track` too: with an immutable new array and `track item.id`, `@for` still reuses the existing row DOM, so immutability does not cost DOM churn.

```typescript
// Bad
addTodo(t: Todo) { this.todos.push(t); }
// Good
readonly todos = signal<Todo[]>([]);
addTodo(t: Todo) { this.todos.update(list => [...list, t]); }
```

---

### T2. "Is there anything wrong with using `effect()` to keep two signals in sync?"

**The trap:** "No, effects can write signals since v19." That's technically allowed, but it's the wrong tool.

**Strong answer includes:**
- Deriving state in an effect creates an **extra async hop**. The effect runs later in the CD cycle, so for a moment the UI can show stale or inconsistent state, and it triggers another refresh. Data flow becomes implicit, and loops (`a` → effect → `b` → effect → `a`) are easy to create.
- Use the right primitive instead:
  - derived and read-only → `computed`;
  - derived but user-overridable (reset on source change) → `linkedSignal`;
  - async derived → `resource`/`httpResource`/`rxResource`;
  - DOM after render → `afterRenderEffect`.
- Effects are for **leaving** the signal graph: persistence, logging, analytics, imperative 3rd-party APIs.
- If you must read a signal without tracking it, use `untracked()`.

```typescript
// Wrong: effect as a watcher
constructor() { effect(() => this.filtered.set(this.items().filter(i => i.active))); }
// Right
readonly filtered = computed(() => this.items().filter(i => i.active));
// Right, when the user can override but it resets on source change
readonly selected = linkedSignal(() => this.filtered()[0] ?? null);
```

---

### T3. "What's the difference between `providers` and `viewProviders`?"

**The trap:** "Nothing, `viewProviders` is old syntax."

**Strong answer includes:**
- Both create a per-component-instance provider on the element injector.
- `providers` are visible to the component's own view **and to content projected into it** (`<ng-content>` children).
- `viewProviders` are visible **only to the component's view**. Projected content does not see them. It resolves against the injectors where it was *declared* (the parent's template).
- Library use cases:
  - Prevent a consumer's projected component from accidentally grabbing your internal service instance.
  - Conversely, use `providers` when you *want* projected children to find you. Example: a `lib-tabs` providing a `TabsState` that projected `lib-tab` components inject. That is the compound-component pattern.

```typescript
@Component({
  selector: 'lib-tabs',
  providers: [TabsState],          // <lib-tab> children in ng-content CAN inject this
  viewProviders: [InternalAnim],   // only lib-tabs' own template can
  template: `<nav>...</nav><ng-content />`,
})
export class TabsComponent {}
```

---

### T4. "I read my signal input in the constructor and always get the default value. And my `ngOnInit` logic doesn't re-run when the input changes. What's wrong?"

**The trap:** "Move it to `ngOnInit`." That fixes the first part and misses the point.

**Strong answer includes:**
- Inputs are set after construction. A required signal input read in the constructor **throws** (NG0950). An optional one returns the default, which is a silent bug.
- `ngOnInit` sees the first value but runs **once**. If the input changes later (e.g. the route param changes while the component is reused), logic in `ngOnInit` goes stale. That was the classic bug with `ActivatedRoute.snapshot`.
- The signal-era answer: don't *read once*, **derive**. Use `computed(() => ...this.id())`, or `httpResource(() => \`/api/x/${this.id()}\`)`, which re-fetches whenever `id` changes and cancels the stale request. Both can be declared as field initialisers, because they read lazily.
- With `withComponentInputBinding()` the route param is itself an input, so the same pattern handles param changes.

```typescript
export class OrderComponent {
  readonly id = input.required<string>();
  // Declared at construction, evaluated lazily when inputs exist, re-runs on change
  readonly order = httpResource<Order>(() => `/api/orders/${this.id()}`);
  readonly title = computed(() => `Order #${this.id()}`);
}
```

---

### T5. "What causes `ExpressionChangedAfterItHasBeenCheckedError`, and how do you fix it properly?"

**The trap:** "Wrap it in `setTimeout`", or "call `detectChanges()`". Both hide a unidirectional-data-flow violation and cause flicker or an extra CD cycle.

**Strong answer includes:**
- In dev mode, Angular runs a second verification pass after CD. If a bound value differs, something changed state *during* the check. Typical causes:
  - a child modifies parent state in `ngOnInit`/`ngAfterViewInit` (e.g. via a shared service or an output emitted synchronously);
  - a getter that returns a new object or array, or `Math.random()`/`Date.now()`, on each call;
  - updating a value in `ngAfterViewInit` based on a `@ViewChild` measurement.
- Real fixes:
  - Make the data flow one-way: the parent owns the state, and the child emits events in response to user actions, not during init.
  - Compute the value earlier (constructor, `computed`) instead of in a later hook.
  - Make getters stable (`computed` memoises).
  - For DOM-measurement-driven state, use `afterNextRender`/`afterRenderEffect` and write to a signal. Signals written after render schedule a new, legitimate pass instead of mutating mid-check.
- It is a **dev-only** error. Production doesn't throw, but the bug (stale UI) is still there.

---

### T6. "A service in our lazy-loaded feature has a different instance from the one the header uses. Why?"

**The trap:** "Angular bug", or "make everything `providedIn: 'root'`" without understanding scope.

**Strong answer includes:**
- Lazy-loaded routes (and route-level `providers`) create a **child environment injector**. If the service is listed in the lazy module's `providers` (or the route's `providers`), or a lazy module imports a module that provides it (the classic `SharedModule` with providers, or calling `forRoot()` in a lazy module), the lazy area gets **its own instance**. The eagerly loaded header resolves from root and gets another.
- Fix by deciding the intended scope:
  - app-wide singleton → `providedIn: 'root'` / `@Service()`, and remove it from any module or route `providers`;
  - intentionally feature-scoped → keep it in route `providers`, and don't inject it outside that feature.
- The legacy guard pattern was `constructor(@Optional() @SkipSelf() parent: CoreModule)`, which throws if the module is imported twice. In standalone apps, use `provideX()` functions returning `EnvironmentProviders`, and call them once in `app.config.ts`.
- Debug with Angular DevTools' injector tree view.

---

### T7. "We went zoneless and a banner that hides after a `setTimeout` stopped disappearing. Why?"

**The trap:** "Zoneless is buggy, add `detectChanges()`", or "re-add zone.js".

**Strong answer includes:**
- Without zone.js, nothing tells Angular a timer ran. Mutating a plain field (`this.visible = false`) does not schedule CD.
- With zone.js the same code "worked" because every async task triggered an app-wide tick. OnPush components would have had the same bug even with zones, unless something else triggered a check.
- Fix: make it reactive state (`visible = signal(true)` → `visible.set(false)`), which notifies the scheduler and marks exactly that view. Use `markForCheck()` only for legacy code you can't convert yet.
- The same applies to promise `.then`, raw `addEventListener`, websocket callbacks and 3rd-party library callbacks.
- Migration checklist: search for field assignments inside async callbacks, `NgZone.onStable`/`onMicrotaskEmpty` subscriptions, `ApplicationRef.isStable`-based logic, and tests using `fakeAsync`.

```typescript
export class BannerComponent {
  readonly visible = signal(true);
  constructor() {
    const id = setTimeout(() => this.visible.set(false), 5000);
    inject(DestroyRef).onDestroy(() => clearTimeout(id));
  }
}
```

---

### T8. "After enabling SSR we get hydration mismatch errors (NG0500-series). What are the usual causes?"

**The trap:** "Add `ngSkipHydration` everywhere", or "disable SSR for that page".

**Strong answer includes:**
- Hydration expects the client's first render to produce **the same DOM** the server produced. Common causes:
  1. **Invalid HTML nesting.** For example `<div>` inside `<p>`, a `<table>` without `<tbody>`, or `<a>` inside `<a>`. The browser parser "fixes" the markup, so the DOM no longer matches.
  2. **Direct DOM manipulation** via `nativeElement.innerHTML`, `appendChild` or jQuery-era 3rd-party widgets, which Angular cannot reconcile.
  3. **Non-deterministic rendering**: `Date.now()`, random IDs, timezone/locale differences between server and client, or `window.innerWidth`-based `@if`s.
  4. **Different data on each side**, e.g. an HTTP call not in the transfer cache (POST, or excluded headers) or user-specific data read from `localStorage` only on the client.
- Fixes:
  - Valid HTML.
  - Move DOM work into `afterNextRender`.
  - Deterministic IDs (a counter via a service, not `Math.random`).
  - Transfer state or the HTTP transfer cache for data.
  - Render client-only bits inside `@defer` (which renders its placeholder on the server) or behind a browser-only branch that runs *after* hydration.
- `ngSkipHydration` on a component is an **escape hatch** for a 3rd-party widget you can't fix, not a strategy. It also disables the hydration benefits for that subtree.

---

## C. Code examples

### C1. Custom `ControlValueAccessor` (classic forms) — full, OnPush/zoneless-safe

Interviewers ask for this a lot, and it is core to owning a component library. Key points to say out loud:
- `NG_VALUE_ACCESSOR` is a **multi** provider.
- `forwardRef` is needed because the class is referenced inside its own decorator metadata.
- **`writeValue` is called from outside the component** (e.g. `form.patchValue`). No template event fires, so under OnPush/zoneless a plain field would not re-render. Store the state in signals.
- Call `onTouched` on blur, not on every change, so `touched`-based error display behaves like native inputs.
- Implement `setDisabledState` so `control.disable()` works. Note that `[disabled]` on a reactive-form control is discouraged.

```typescript
import { Component, forwardRef, signal } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'lib-rating',
  template: `
    <div role="radiogroup" aria-label="Rating">
      @for (star of stars; track star) {
        <button
          type="button"
          role="radio"
          [attr.aria-checked]="star === value()"
          [class.filled]="star <= value()"
          [disabled]="disabled()"
          (click)="select(star)"
          (blur)="onTouched()"
        >★</button>
      }
    </div>
  `,
  providers: [
    { provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => RatingComponent), multi: true },
  ],
})
export class RatingComponent implements ControlValueAccessor {
  protected readonly stars = [1, 2, 3, 4, 5];
  protected readonly value = signal(0);
  protected readonly disabled = signal(false);

  private onChange: (value: number) => void = () => {};
  protected onTouched: () => void = () => {};

  writeValue(value: number | null): void {         // model -> view
    this.value.set(value ?? 0);
  }
  registerOnChange(fn: (value: number) => void): void { this.onChange = fn; }
  registerOnTouched(fn: () => void): void { this.onTouched = fn; }
  setDisabledState(isDisabled: boolean): void { this.disabled.set(isDisabled); }

  protected select(star: number): void {            // view -> model
    if (this.disabled()) return;
    this.value.set(star);
    this.onChange(star);
  }
}

// Usage: <lib-rating formControlName="score" />  or  <lib-rating [(ngModel)]="score" />
```

**Validation from inside the control:** also provide `NG_VALIDATORS` (multi) and implement `Validator.validate()`. To read the parent control's state (e.g. to show errors), inject `NgControl` with `{ self: true, optional: true }` and set `ngControl.valueAccessor = this` instead of providing `NG_VALUE_ACCESSOR`. Doing both causes a circular dependency.

### C2. The Signal Forms alternative: `FormValueControl` (v22 stable)

With Signal Forms, a custom control needs no CVA plumbing. It exposes a `value` **model** (or a `checked` model via `FormCheckboxControl`). `[formField]` binds to it, and it can also bind optional state properties such as disabled or touched if the control declares them.

```typescript
import { Component, input, model } from '@angular/core';
import { FormValueControl } from '@angular/forms/signals';

@Component({
  selector: 'lib-rating',
  template: `
    @for (star of stars; track star) {
      <button type="button" [disabled]="disabled()" [class.filled]="star <= value()"
              (click)="value.set(star)" (blur)="touched.set(true)">★</button>
    }
  `,
})
export class RatingComponent implements FormValueControl<number> {
  protected readonly stars = [1, 2, 3, 4, 5];
  readonly value = model(0);               // the only required member
  readonly disabled = input(false);        // optional: bound from field state
  readonly touched = model(false);         // optional: reports touch back
}

// Usage: <lib-rating [formField]="f.score" />
```

Library migration angle: *"Existing CVA-based controls keep working inside Signal Forms through the interop shim, so I don't have to rewrite the library in one go. For new controls I'd implement `FormValueControl`, and for widely used ones possibly both during a transition."*

### C3. Auth interceptor with single-flight 401 refresh

```typescript
export const SKIP_AUTH = new HttpContextToken<boolean>(() => false);

@Service()
export class AuthService {
  private readonly http = inject(HttpClient);
  readonly accessToken = signal<string | null>(null);
  private refresh$: Observable<string> | null = null;

  /** Concurrent 401s share one refresh request. */
  refresh(): Observable<string> {
    this.refresh$ ??= this.http
      .post<{ accessToken: string }>('/api/auth/refresh', null, {
        withCredentials: true,                                    // refresh token in httpOnly cookie
        context: new HttpContext().set(SKIP_AUTH, true),
      })
      .pipe(
        map(r => r.accessToken),
        tap(token => this.accessToken.set(token)),
        finalize(() => (this.refresh$ = null)),
        shareReplay({ bufferSize: 1, refCount: false }),
      );
    return this.refresh$;
  }

  logout(): void { this.accessToken.set(null); /* navigate to login, clear state */ }
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.context.get(SKIP_AUTH)) return next(req);
  const auth = inject(AuthService);                               // inject() at top level of the fn

  const withToken = (token: string | null) =>
    token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(withToken(auth.accessToken())).pipe(
    catchError((err: unknown) => {
      if (!(err instanceof HttpErrorResponse) || err.status !== 401) return throwError(() => err);
      return auth.refresh().pipe(
        // next() forwards only to downstream interceptors, so a second 401 can't loop here
        switchMap(token => next(withToken(token))),
        catchError(refreshErr => {
          auth.logout();
          return throwError(() => refreshErr);
        }),
      );
    }),
  );
};

// app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor, retryInterceptor, errorInterceptor])),
    // provideHttpClient(withXhr(), ...) if you need upload progress (v22 defaults to FetchBackend)
  ],
};
```

Points to mention:
- The access token lives in memory and the refresh token in an httpOnly cookie, which limits XSS exposure.
- Don't attach the token to third-party domains: check `req.url` against your API origin.
- Order matters. Auth runs before retry, so a retried request is re-signed.

### C4. Compound component with content queries (library pattern)

```typescript
@Component({
  selector: 'lib-tab',
  template: `@if (active()) { <ng-content /> }`,
})
export class TabComponent {
  readonly label = input.required<string>();
  readonly active = signal(false);
}

@Component({
  selector: 'lib-tabs',
  template: `
    <div role="tablist">
      @for (tab of tabs(); track tab.label(); let i = $index) {
        <button role="tab" [attr.aria-selected]="i === selectedIndex()" (click)="selectedIndex.set(i)">
          {{ tab.label() }}
        </button>
      }
    </div>
    <ng-content />
  `,
})
export class TabsComponent {
  readonly tabs = contentChildren(TabComponent);
  readonly selectedIndex = model(0);

  constructor() {
    // Legit effect: pushes state into child instances (leaving the pure derivation graph)
    effect(() => {
      const selected = this.selectedIndex();
      this.tabs().forEach((t, i) => t.active.set(i === selected));
    });
  }
}
```

Trade-off to mention: `<ng-content>` inside `@if` still *instantiates* the projected content eagerly. For heavy tab bodies, accept `<ng-template>` in each tab and render the active one with `ngTemplateOutlet`, so inactive tabs are never created.

---

## D. Red flags

- **"I use `setTimeout` to fix ExpressionChanged errors."** → Say instead: "It signals a data-flow violation. I move the state change earlier or into `computed`/`afterNextRender`."
- **"OnPush is an optimisation we add later."** → "Since v22 it's the default. I design for immutability and signals from the start, and treat `Eager` as tech debt."
- **"I subscribe in the component and assign to a field."** (manual subscriptions everywhere, no teardown) → "I use `toSignal`, the `async` pipe or `httpResource`. If I must subscribe, I add `takeUntilDestroyed()`."
- **"`effect()` is like a watcher, I use it to update other signals."** → "Derived state is `computed` or `linkedSignal`. Effects are for side effects leaving the signal graph."
- **"Zoneless just means removing zone.js."** → "Zoneless means CD runs only on notifications (signals, markForCheck, template events), so the code must be reactive first."
- **"NgModules are deprecated."** → "Standalone is the default and recommended style. NgModules still work, and I migrate incrementally with the schematic."
- **"I put all services in a SharedModule."** → "Singletons use `providedIn: 'root'`/`@Service()`. Feature state goes in route providers. Per-instance state goes in component providers."
- **"`track $index` is fine everywhere."** / omitting stable identity → "I track a stable ID so DOM and component state survive re-fetches."
- **"I use `ngOnChanges` to recompute derived values."** → "With signal inputs that's `computed`. It's memoised and has no timing issues."
- **"I call methods in templates, it's fine."** → "In large lists that runs on every check. I use `computed` or a pure pipe."
- **"`fakeAsync` for everything."** → "In zoneless projects `fakeAsync` needs zone.js. I use `whenStable()` or Vitest fake timers."
- **"`withFetch()` to enable fetch."** → "Since v22 fetch is the default and `withFetch()` is a no-op. I'd add `withXhr()` only if we need upload progress."
- **"Karma/Jasmine is the Angular testing stack."** → "Vitest has been the default since v21. Karma is legacy, and I'd plan a migration."
- **"I use `::ng-deep` to style library components."** → "The library exposes CSS custom properties and projection slots. `::ng-deep` means the API is missing something."
- **"Resolvers for every page."** → "Resolvers block navigation. I prefer instant navigation plus skeletons with `httpResource`, and I use resolvers only when the page can't render without the data."
- **"`canActivate` protects lazy code from being downloaded."** → "That's `canMatch`. `canActivate` runs after the chunk has loaded."
- **"Environment files for each deployment."** → "For build-once-deploy-many I load runtime config via `provideAppInitializer`. `fileReplacements` is build-time."
- **Talking about Angular as if it's still v12** (`ComponentFactoryResolver`, `entryComponents`, class guards) → "`ViewContainerRef.createComponent(Cmp)` takes the class directly. `ComponentFactoryResolver` was removed in v22."

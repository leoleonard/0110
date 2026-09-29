# 12 — One-hour-before cheatsheet

> Read top to bottom once. Don't learn anything new now; this is for recall. Facts checked against the Angular changelog and npm on 2026-09-29.

## 0. Version snapshot (say these with confidence)
| Thing | Current fact |
|---|---|
| Angular | **22.x** (22.0 released Jun 2026; 22.2 is the latest). v20 and v21 are LTS. Majors come out about every 6 months. |
| v20 | Zoneless, `effect`, `linkedSignal` and `toSignal` went **stable**. Incremental hydration stable. `*ngIf`/`*ngFor` deprecated. |
| v21 | **Zoneless is the default** for new apps. **Vitest is the default** test runner (Karma is legacy). Signal Forms experimental. |
| v22 | **OnPush is the default** when `changeDetection` isn't set. `ChangeDetectionStrategy.Default` is deprecated; its new name is **`Eager`**. **Signal Forms stable** (`form()`, `[formField]`). **FetchBackend is the default** for HttpClient (`withFetch()` deprecated; use `withXhr()` if you need upload progress). New `@Service()` decorator. Incremental hydration is on by default. Router `paramsInheritanceStrategy` defaults to `'always'`. `ComponentFactoryResolver` removed. |
| RxJS | 7.8.x. There is **no RxJS 8**. |
| NgRx | 22.x. **SignalStore** (`@ngrx/signals`) is recommended for new code. Classic Store is still first-class. |
| TypeScript | Angular 22 needs TS ≥ 6.0. |

Sound bite: *"Our code base is on vX. I track the release notes, and the last two majors changed the defaults (zoneless in 21, OnPush in 22), so the direction is signals-first. That's how I'd plan migrations."*

## 1. Angular core: the ten facts that come up most
1. **Change detection.** OnPush checks a component only when: an input reference changes, an event fires from its template, `async` pipe emits, a **signal read in the template changes**, or `markForCheck()` is called. Mutating an array passed as an input does **not** trigger a check.
2. **Zoneless.** Nothing monkey-patches `setTimeout` or Promises any more. CD is scheduled by signal writes, template events, `markForCheck`, the `async` pipe and `ComponentRef.setInput`. So a plain field changed inside `setTimeout` won't render. Make it a signal.
3. **Signals vs RxJS.** Signals hold synchronous **state** (glitch-free, derive with `computed`). RxJS handles **events over time**: cancellation, debounce, combining streams. Bridge the two with `toSignal` and `toObservable`. For async reads, use `resource({params, loader})`, `rxResource({params, stream})` or `httpResource(() => url)`.
4. **`effect()`** is for side effects that leave Angular (logging, localStorage, a third-party DOM library). Don't use it to sync one signal into another; use `computed` or `linkedSignal` for that.
5. **DI hierarchy.** Element injectors (component/directive `providers`/`viewProviders`) come first, then environment injectors (route `providers` → root → platform) → null injector. A provider on a lazy route gives that route its **own instance**. Modifiers: `{optional, self, skipSelf, host}`. `viewProviders` are hidden from projected content.
6. **Control flow.** `@for (x of xs; track x.id)`: `track` is mandatory. Track by `$index` only for static lists. `@let` declares a template variable. `@defer (on viewport; prefetch on idle)` with `@placeholder`/`@loading`/`@error` splits code by template region.
7. **Routing.** Guards and resolvers are functions that use `inject()`. `canMatch` stops a lazy chunk from loading at all. `canActivate` runs after the route matches. Use `withComponentInputBinding()` to get route params as inputs. A guard can return a `UrlTree`/`RedirectCommand` to redirect.
8. **Forms.** Reactive forms are typed (`nonNullable`). Template-driven works for simple cases. **Signal Forms** (v22 stable) builds the form from a model signal plus a schema function; custom controls implement `FormValueControl` (`value = model()`) instead of a CVA. A CVA needs `NG_VALUE_ACCESSOR` + `forwardRef` + `writeValue`, `registerOnChange`, `registerOnTouched` and `setDisabledState`.
9. **HTTP.** Write functional `HttpInterceptorFn` and register them with `provideHttpClient(withInterceptors([...]))`. Use `HttpContextToken` for per-request flags. For a 401 refresh, queue concurrent requests behind one refresh call.
10. **SSR.** Hydration reuses the server DOM. Incremental hydration uses `@defer` + `hydrate on ...`. Event replay catches clicks made before hydration finishes. Mismatches come from browser-only APIs and invalid HTML. `HttpTransferCache` stops the client from repeating GETs the server already made.

## 2. RxJS in 60 seconds
| Operator | Behaviour | Use for | Wrong choice bites |
|---|---|---|---|
| `switchMap` | cancels previous | typeahead, route param → load | **saves** (drops writes) |
| `concatMap` | queues in order | ordered writes, autosave | slow typeahead |
| `mergeMap` | parallel | independent fire-and-forget, bulk | race conditions / order |
| `exhaustMap` | ignores while busy | login/submit button, refresh token | lost user intent |

- `forkJoin` emits once, after **all complete**. It never emits if any source is infinite, and emits nothing if one completes empty. `combineLatest` needs each source to emit at least once, then emits on every change. `zip` pairs values by index. `withLatestFrom` takes a snapshot of the other stream and doesn't trigger on it.
- Put `catchError` **inside** the inner observable, or the outer stream (e.g. the typeahead) dies on the first error.
- Use `shareReplay({bufferSize: 1, refCount: true})`. Without `refCount` the source subscription can leak.
- Unsubscribe with the `async` pipe or `toSignal` first, then `takeUntilDestroyed()` (needs an injection context or a `DestroyRef`). Never nest `subscribe` calls.
- Subjects: `Subject` (no replay), `BehaviorSubject` (current value, needs an initial value), `ReplaySubject(n)` (last n values), `AsyncSubject` (last value on complete).

## 3. JavaScript (ES5 → ES8)
- **Event loop:** run sync code → **drain all microtasks** (Promise callbacks, `queueMicrotask`, `await` continuations) → maybe render (rAF) → run one macrotask (`setTimeout`, I/O, events) → repeat.
- Output order: `sync → microtasks → setTimeout`. Everything after an `await` runs as a microtask.
- **`this`:** depends on the call site. The rules, in priority order: `new` > explicit (`call`/`apply`/`bind`) > implicit (`obj.fn()`) > default (undefined in strict mode). Arrow functions take `this` from the enclosing scope.
- `var` is function-scoped and hoisted as `undefined`. `let`/`const` are block-scoped and sit in the TDZ until declared. `const` stops rebinding, not mutation.
- ES2016: `**`, `includes`. ES2017 (ES8): `async/await`, `Object.values/entries`, `padStart/padEnd`, `getOwnPropertyDescriptors`, trailing commas.
- `===` has no coercion. `Object.is(NaN, NaN)` is true and `Object.is(0, -0)` is false. `typeof null === 'object'`. `[10, 9, 1].sort()` sorts as strings, giving `[1, 10, 9]`.
- Copying: spread and `Object.assign` are shallow. `JSON.parse(JSON.stringify())` loses Dates, undefined, Map/Set and functions, and fails on cycles. `structuredClone` handles cycles, Map/Set and Date, but not functions, DOM nodes or class prototypes.
- `await` inside `forEach` doesn't wait. Use `for...of` to run in sequence or `Promise.all(map)` to run in parallel.
- **Debounce** runs only after quiet time (search input). **Throttle** runs at most once per interval (scroll, resize).

## 4. HTML / CSS / rendering
- **Pipeline:** DOM + CSSOM → render tree → **layout (reflow)** → **paint** → **composite**. Animate only `transform`/`opacity`, which stay on the compositor. Use `will-change` sparingly and temporarily.
- **Layout thrashing:** alternating reads (`offsetHeight`) and writes. Batch all reads, then all writes (or use `afterNextRender` phases).
- **Specificity:** (ids, classes/attributes/pseudo-classes, elements). `:where()` adds 0. `:is()` takes its most specific argument. **`@layer`** puts library styles in a lower-priority layer, so consumers win without `!important`.
- **Flex** lays things out in one dimension, driven by content. **Grid** is two-dimensional and layout-first, with `subgrid` and container queries for components.
- **Stacking contexts:** `transform`, `opacity < 1`, `position` + `z-index`, `isolation: isolate`. That's why a `z-index: 9999` sometimes "doesn't work".
- **Sass:** `@use`/`@forward` give namespaced modules evaluated once. **`@import` is deprecated** and will be removed in Dart Sass 3. Prefer module functions like `map.get` and `color.adjust`.
- **Angular styles:** encapsulation is Emulated by default. `::ng-deep` is deprecated, so theme with **CSS custom properties** as the public styling API of a component library.
- **A11y:** use native elements first (the first rule of ARIA). Every input needs a label. Keep focus visible. Move focus on route change. Use `aria-live` for async updates. Target WCAG 2.2 AA with 4.5:1 text contrast. `display:none` hides from screen readers; `opacity:0` does not.
- **Core Web Vitals:** **LCP ≤ 2.5 s**, **INP ≤ 200 ms** (it replaced FID in March 2024), **CLS ≤ 0.1**. Angular levers: `NgOptimizedImage` with `priority`, SSR/hydration, `@defer`, lazy routes, breaking up long tasks, reserving space for images and ads.

## 5. State management
- **Redux principles:** a single source of truth, read-only state (change it by dispatching actions), pure reducers. Data flows one way: action → reducer → store → selector → view → action.
- Actions are **events, not commands** (`[Product Page] Opened`, not `loadProducts`). Use `createActionGroup` and `createFeature`.
- `createSelector` memoizes on input references. A projector that returns a new array every time defeats OnPush. **Normalize** data as `{ids, entities}` with `@ngrx/entity` and denormalize in selectors.
- In effects, choose the flattening operator on purpose and `catchError` inside the inner observable.
- **SignalStore:** `signalStore(withState, withComputed, withMethods, withHooks, withProps)`, `patchState`, `rxMethod`, `withEntities`, and `signalStoreFeature` for reuse.
- **When not to use NgRx:** state local to one feature, mostly server cache, a small team, no need for devtools or event auditing. Use a service with signals, or a server-state library, instead.

## 6. REST and tools
- Safe methods: GET, HEAD, OPTIONS. Idempotent: those plus **PUT and DELETE**. POST isn't idempotent (use an `Idempotency-Key` header). PATCH isn't guaranteed to be.
- **401** means not authenticated (refresh the token or log in). **403** means authenticated but not allowed (don't retry). **409** is a conflict or version clash. **412** means an ETag precondition failed. **422** is a validation error. **429** means back off (check `Retry-After`). 502, 503 and 504 are retryable for idempotent requests only.
- **CORS** is enforced by the browser and fixed **on the server**. Preflight is an OPTIONS request, sent for non-simple methods, headers or content types. In dev, use the Angular `proxy.conf.json`.
- **Auth:** use OAuth2/OIDC **Authorization Code + PKCE** (the implicit flow is deprecated). Tokens are safest in memory or behind a BFF with an httpOnly SameSite cookie; localStorage is exposed to XSS. Rotate refresh tokens.
- **Caching:** hashed bundles get `Cache-Control: max-age=31536000, immutable`. `index.html` gets `no-cache`. ETag + `If-None-Match` returns a 304.
- **Pagination:** offset is simple but drifts when data changes. Cursor pagination is stable and scales, but you can't jump to an arbitrary page.
- **Postman:** collections, environments and variables, pre-request scripts, tests, Newman in CI, and mock servers for a third party that isn't ready. **OpenAPI:** design the contract first, generate a typed Angular client, and catch breaking changes in CI.

## 7. Git and CI
- **Rebase** gives linear history but rewrites commits. Never rebase a shared branch, and if you must force-push use `--force-with-lease`. **Merge** keeps the true history. **Squash** gives one commit per PR, which is clean and easy to revert but loses granularity.
- To recover: `git reflog` → `git reset --hard HEAD@{n}` or `git branch rescue <sha>`. To undo something already public, use `revert`, not `reset`.
- Use `cherry-pick -x` for hotfix backports and `bisect` to find a regression.
- **Trunk-based development** means short-lived branches, feature flags and continuous integration, and it's what DORA research favours. GitFlow suits versioned or shipped products; a component library can use release branches.
- **Pipeline:** `npm ci` (cached) → lint → unit tests → build (with budgets) → e2e → deploy preview → prod. Add protected branches, CODEOWNERS, and conventional commits with semantic release for the library.

## 8. Agile
- **Scrum:** accountabilities are PO, SM and Developers. Events are the Sprint, Planning, Daily, Review and Retro. Each artifact has a commitment: Product Goal, Sprint Goal and **DoD**.
- **Kanban:** WIP limits expose bottlenecks. Measure cycle time, throughput and the CFD. **Little's Law:** lead time = WIP / throughput.
- **Waterfall** is justified for fixed-scope, contractual or regulated work and hardware or third-party dependencies.
- Velocity is for the team's own forecasting. **Never compare velocity across teams or use it as a performance metric.**
- A frontend DoD covers: acceptance criteria met, tests, a11y check, responsive, i18n, analytics events, docs or Storybook updated, no new lint errors, reviewed and deployed to staging.

## 9. Patterns and quality
- **SOLID in Angular:** SRP means thin components with logic in services. OCP means extending through DI tokens or strategies. LSP applies to abstract-class providers. ISP means small inputs APIs. DIP means depending on an `InjectionToken`/abstract class, not a concrete HTTP service.
- **Smart/dumb components:** containers inject state; presentational components use `input()`/`output()` and OnPush and are easy to test and document.
- **Facade:** hides the store or services behind an intent-based API. It's worth it at feature boundaries, not in front of every service.
- **Adapter:** map DTOs to domain models at the edge. **Strategy:** multi-providers or a token map.
- **Testing trophy:** mostly integration-style component tests (Testing Library or harnesses), unit tests for pure logic, a few e2e tests for critical journeys, and visual regression for the component library. Track coverage as a signal, not a target.
- **Tech debt:** write it down (ADR or ticket), quantify it (time lost, incidents, lead time), tie it to a business outcome, and pay it continuously (around 15–20% capacity), not in "hardening sprints".

## 10. Behavioural (STAR+L)
- **S**ituation (1 line) → **T**ask (your responsibility) → **A**ction (the most time, and say "I", not "we") → **R**esult (**a number**) → **L**earning.
- Have ready: a conflict, a mistake, mentoring, the design system you own, a measurable improvement, a stakeholder or third-party story, a disagree-and-commit.
- Every story should show **scope** beyond your own ticket, **influence without authority**, and **a metric**.

## 11. Three sentences to have ready
- *"I decide based on who owns the state and how long it lives: local UI state goes in component signals, shared client state in a signal store, server cache in a resource or query layer, and cross-cutting audited flows in NgRx with events."*
- *"For performance I measure first (field data for Core Web Vitals, then DevTools and Angular DevTools profiling), fix the biggest bottleneck, and put a budget in CI so it can't regress."*
- *"As the owner of a shared library, my rule is that the public API is a contract: semver, deprecations with a migration path (schematics), a11y built in, and theming through CSS custom properties."*

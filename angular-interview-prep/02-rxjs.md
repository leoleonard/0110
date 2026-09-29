# 02 — RxJS in Angular

> **How to use this file:** read section A out loud. Each answer should take one or two minutes to say. Section B is the set of "gotcha" questions interviewers use to separate people who have *used* RxJS from people who have *debugged* it in production. At senior level the interviewer is not checking whether you know that `switchMap` exists. They want to know whether you can **pick the right operator and explain the bug you get with the wrong one**, whether you understand **subscription lifetime** (leaks, `shareReplay`, `takeUntil` ordering), whether you can **keep a stream alive after an error**, and whether you know **where RxJS still earns its place now that Angular is signal-first**. Version context: RxJS **7.8.x** is current and there is no RxJS 8 release. Use RxJS 7 APIs: `retry({ count, delay })`, `firstValueFrom`/`lastValueFrom`, `share({ connector, resetOnRefCountZero })`. `toPromise()` is deprecated. Angular 22 is zoneless by default for new apps (since v21) and makes components OnPush by default (v22), so *how* stream values reach the template matters more than it used to.

---

## A. Most commonly asked questions

### Q1. Explain `switchMap`, `mergeMap`, `concatMap` and `exhaustMap`. When do you use each?

**Answer (1–2 min):** All four are higher-order mapping operators. Each maps an outer value to an inner observable and flattens it. They differ only in **what happens when a new outer value arrives while an inner observable is still running**:

| Operator | On new outer value while inner is active | Canonical use case | Bug if you pick it wrongly |
|---|---|---|---|
| `switchMap` | **Cancels** the previous inner and switches to the new one | Typeahead search, route-param-driven loads, "latest wins" reads | Used for writes (POST/PUT), it cancels in-flight saves on the client. The server may or may not have processed them, so you get **lost or unacknowledged writes** |
| `mergeMap` | Runs all inners **concurrently** (optional `concurrent` limit) | Independent parallel work: delete N selected rows, upload several files, fire-and-forget analytics | Used for search, responses **arrive out of order** and a stale result overwrites a fresh one. Can also flood the backend |
| `concatMap` | **Queues**, starting the next inner only when the previous completes | Ordered writes: autosave of a form, sequential commands where order matters | Used for typeahead, the user waits for every obsolete request to finish. It lags, and if an inner never completes the queue is **stuck forever** |
| `exhaustMap` | **Ignores** new outer values while an inner is active | Login/submit button, "refresh" button, polling tick when the previous poll is still running | Used for search, the user's **latest input is dropped** and the results don't match what's in the box |

Sound bite: *"Reads are usually `switchMap`, ordered writes are `concatMap`, parallel independent writes are `mergeMap`, and 'don't let the user double-submit' is `exhaustMap`."*

**Go deeper:**
- `switchMap` unsubscribes the inner `HttpClient` observable, which aborts the request (XHR abort, or `AbortController` with the `FetchBackend` that is default since v22). That does **not** roll back anything the server already did. This is why switchMap-on-save is dangerous.
- `mergeMap(fn, 3)` limits concurrency, which is a cheap throttle for bulk uploads.
- `concatMap` with an inner that never completes (for example a websocket) blocks everything behind it.
- In NgRx effects the same decision applies. See `05-state-management.md`.

```ts
// Typeahead: latest wins, errors isolated per request
results$ = this.query$.pipe(
  debounceTime(300),
  distinctUntilChanged(),
  switchMap(q => this.api.search(q).pipe(
    catchError(() => of([] as Result[])),
  )),
);

// Save button: ignore clicks while a save is in flight
save$ = this.saveClicks$.pipe(
  exhaustMap(() => this.api.save(this.form.value)),
);

// Autosave: every change persisted, in order
autosave$ = this.changes$.pipe(
  debounceTime(1000),
  concatMap(draft => this.api.saveDraft(draft)),
);
```

---

### Q2. What's the difference between hot and cold observables?

**Answer:**
- **Cold:** the producer is created **per subscriber**. Each `subscribe()` runs the producer again. `HttpClient` calls, `of`, `from`, `interval`, and `defer` are cold. Two `async` pipes on the same `http.get()` observable make **two HTTP requests**.
- **Hot:** the producer exists independently and subscribers **share** it. Subjects, DOM events via a shared source, websockets wrapped in a subject, and the NgRx store all work this way. Late subscribers miss earlier values unless something replays them.
- You make a cold observable hot (multicast) with `share()` or `shareReplay()`.

**Go deeper:**
- "Warm" is informal slang for a refcounted shared source. It starts on the first subscriber and stops on the last.
- The classic senior bug is a template with `@if (user$ | async; as user)` in one place and `(user$ | async)?.name` in another, which produces duplicate requests. Fix it with one subscription (`@let user = user$ | async;` or `toSignal`) or with `shareReplay`.

---

### Q3. `share()` vs `shareReplay()`, and why `shareReplay({ bufferSize: 1, refCount: true })`?

**Answer:**
- `share()` multicasts through a plain `Subject`. It has no replay, so late subscribers get only future values. By default it **resets** when the ref count drops to zero, on complete, and on error. For an HTTP call this means a subscriber arriving after the response has completed **triggers a new request**.
- `shareReplay(1)` multicasts through a `ReplaySubject(1)`. Late subscribers get the last value. The default is `refCount: false`: once subscribed, the **source subscription is kept alive forever**, even after every subscriber has gone.
- `shareReplay({ bufferSize: 1, refCount: true })` unsubscribes from the source when the last subscriber leaves. A later subscriber re-subscribes to the source.

How I decide:
- **Finite source you want cached for the app lifetime** (config, feature flags, a lookup table from HTTP): `shareReplay(1)` is fine and intentional. The source completes, so nothing leaks except the cached value, which is the whole point.
- **Infinite or long-lived source** (websocket, `interval`, `store.select`, `valueChanges`, router events): use `refCount: true`. Otherwise the source keeps running after the component is gone. That is a leak, and possibly repeated side effects.

**Go deeper (RxJS 7):** `share` is configurable, and `shareReplay` is essentially a preset of it:

```ts
// Equivalent-ish to shareReplay({ bufferSize: 1, refCount: true })
const shared$ = source$.pipe(
  share({
    connector: () => new ReplaySubject(1),
    resetOnError: true,
    resetOnComplete: false,
    resetOnRefCountZero: true,
  }),
);

// Keep a cache warm for 5s after the last subscriber leaves (avoids refetch on quick route flips)
const cachedWithGrace$ = source$.pipe(
  share({
    connector: () => new ReplaySubject(1),
    resetOnRefCountZero: () => timer(5000),
  }),
);
```

- `resetOnRefCountZero` (and the other `reset*` options) can take a **notifier factory** as well as a boolean. That is how you get a grace period.
- `shareReplay` with an error resets, so the next subscriber retries. A completed source is *not* reset, so its value stays cached.

---

### Q4. Subject vs BehaviorSubject vs ReplaySubject vs AsyncSubject?

**Answer:**
- **`Subject`**: multicast, no initial value, no replay. Late subscribers get nothing from the past. Use it for **events** (clicks, "refresh requested", a `destroy$` notifier).
- **`BehaviorSubject<T>(initial)`**: always has a current value and emits it immediately on subscribe. Use it for **state** ("current user", "selected tab"). Before signals, this was the go-to "service with state" primitive.
- **`ReplaySubject<T>(bufferSize, windowTime?)`**: replays the last *n* values, optionally within a time window, with no initial value required. Use it when "no value yet" is meaningful and you don't want a fake initial `null`, or when you need history.
- **`AsyncSubject<T>`**: emits **only the last value, and only on complete**. It is rare in app code and mirrors how a Promise resolves.

**Go deeper:**
- In a service, expose `asObservable()` (or a readonly type) and keep the subject private. That makes the service the only writer, which is a unidirectional-flow principle.
- For new synchronous state in Angular 20+ I reach for `signal()` rather than `BehaviorSubject`. I keep subjects for event streams that need time-based operators. See Q12.
- A `BehaviorSubject` that has errored throws when you call `.value` or `getValue()`.

---

### Q5. What are the ways to unsubscribe in Angular, and which do you prefer?

**Answer:** in order of preference:

1. **Don't subscribe manually.** Use the `async` pipe or `toSignal()`. The framework owns the lifetime.
2. **`takeUntilDestroyed()`** from `@angular/core/rxjs-interop`, used when you must subscribe for side effects in a component, directive or service.
3. **`DestroyRef.onDestroy(cb)`** for non-RxJS cleanup: third-party widgets, `ResizeObserver`, and unlisten functions from `Renderer2.listen`.
4. **`take(1)` / `first()`** when you genuinely want one value. Note the difference: `first()` errors with `EmptyError` if the source completes without emitting, and `take(1)` just completes.
5. **`takeUntil(this.destroy$)` + `ngOnDestroy`**: the legacy pattern. It still works and you will see it in older codebases. Know the ordering rule (Q6).
6. Store a `Subscription` and call `unsubscribe()` in `ngOnDestroy`: fine for one-offs, but it gets verbose.

```ts
@Component({ /* ... */ })
export class PriceTickerComponent {
  private readonly prices = inject(PriceService);
  private readonly destroyRef = inject(DestroyRef);

  // Preferred: no manual subscription at all
  readonly price = toSignal(this.prices.ticker$, { initialValue: 0 });

  constructor() {
    // Side effect that must happen: injection context, so no argument needed
    this.prices.alerts$
      .pipe(takeUntilDestroyed())
      .subscribe(a => this.notify(a));

    // Non-RxJS cleanup
    const ro = new ResizeObserver(() => { /* ... */ });
    this.destroyRef.onDestroy(() => ro.disconnect());
  }
}
```

**Go deeper:** do HTTP calls need unsubscribing? They complete, so they don't leak in the memory sense. But the callback **still runs after the component is destroyed**, which can navigate, show a toast, or write to a store. That is why I still tie them to the component lifetime.

---

### Q6. Why must `takeUntil` be the last operator?

**Answer:** `takeUntil(notifier$)` only unsubscribes from what is **upstream** of it. If an operator that subscribes to other observables comes after it (`switchMap`, `mergeMap`, `combineLatestWith`, `shareReplay`, and so on), that operator's inner subscriptions are not torn down by the notifier, so they leak.

```ts
// Leaks: the inner interval keeps running after destroy$
source$.pipe(
  takeUntil(this.destroy$),
  switchMap(() => interval(1000)),
).subscribe();

// Correct
source$.pipe(
  switchMap(() => interval(1000)),
  takeUntil(this.destroy$),
).subscribe();
```

- There is a lint rule for this: **`rxjs/no-unsafe-takeuntil`** (from `eslint-plugin-rxjs`, also available in its maintained fork `eslint-plugin-rxjs-x`). The rule allows a small allow-list of operators after `takeUntil`. In a design-authority role I'd enforce it in the shared ESLint config.
- The same reasoning applies to `takeUntilDestroyed()`: put it last.
- A `shareReplay` placed *after* `takeUntil` is a classic hidden leak. So is `shareReplay` without `refCount` placed before it, because the shared source subscription outlives the consumer anyway.

---

### Q7. `takeUntilDestroyed()` throws "NG0203 … can only be used within an injection context". Why?

**Answer:** Without an argument, `takeUntilDestroyed()` calls `inject(DestroyRef)` internally, so it only works in an **injection context**: constructor, field initialisers, factory functions, or inside `runInInjectionContext`. If you call it in `ngOnInit`, in an event handler, or in a method, there's no active injector.

Fix: inject `DestroyRef` once and pass it in.

```ts
export class SearchComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  ngOnInit() {
    this.form.controls.q.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(/* ... */);
  }
}
```

**Go deeper:** `toSignal`, `toObservable`, `effect` and `inject` all have the same constraint. They accept an `injector` option (or `DestroyRef` for `takeUntilDestroyed`) when you need them outside the constructor. In a **root service** the `DestroyRef` is the root injector's, so the subscription effectively lives for the app lifetime.

---

### Q8. Why is the `async` pipe the default recommendation? Any downsides?

**Answer:**
- It subscribes on render and unsubscribes on destroy, and it **handles swapping to a new observable instance** by unsubscribing from the old one.
- It calls `markForCheck()` on every emission. That makes it correct under OnPush (the default for components since v22) and under **zoneless** (the default for new apps since v21). In a zoneless app, `subscribe(v => this.x = v)` on a plain field **will not update the view** unless something schedules change detection. `async` and signals do.

Downsides and trade-offs:
- Each `| async` is its own subscription, so the same cold observable used twice runs twice. Fix with `@let`, one `@if (x$ | async; as x)`, `shareReplay`, or `toSignal`.
- Its initial value is `null` before the first emission, which adds `null` to the type in strict templates.
- In new code I often prefer `toSignal()` in the class. It gives one subscription, a typed value, it composes with `computed()`, and the template reads `price()`.

---

### Q9. What are the most common RxJS memory leaks you've seen in Angular?

**Answer:**
1. **Nested subscribes.** Inner subscriptions are never cleaned up, errors aren't propagated, and there's no cancellation. Use a flattening operator instead.
2. **`shareReplay(1)` on a long-lived source without `refCount: true`.** The source subscription (store select, websocket, `interval`) outlives every consumer.
3. **Subscribing inside services with a longer lifetime than the consumer.** A root service subscribes to something on behalf of a component, or a component subscribes to a root-service stream and never unsubscribes. The service keeps the closure, and the closure keeps the component.
4. **Manual DOM/event listeners.** `addEventListener` on `window`/`document`, or `fromEvent(window, 'resize')`, without teardown. `@HostListener`, `host: { '(window:resize)': ... }` and `Renderer2.listen` (if you keep and call the returned unlisten function) are cleaned up. Raw listeners are not.
5. **`interval`/`timer` polling** started in `ngOnInit` with no `takeUntilDestroyed`.
6. **`valueChanges` subscriptions on reactive forms** in components that are created and destroyed often (dialogs, table rows).
7. **Subscriptions in `@for` row components** in big lists: a small leak multiplied by 1000 rows.

How I find them: heap snapshots in Chrome DevTools (detached DOM nodes and retained component instances after navigating away and back), plus the lint rules (`no-unsafe-takeuntil`, `no-nested-subscribe`, `no-ignored-subscription`).

---

### Q10. How do you handle errors in a stream without killing it?

**Answer:** an error notification is **terminal**: once a stream errors it is dead, and no further values arrive. So **where** you put `catchError` decides what dies.

- `catchError` on the **outer** stream replaces the whole source with the fallback. The typeahead stops responding after the first failed request.
- `catchError` **inside the inner observable** (inside `switchMap`/`mergeMap`/etc.) replaces only that one request. The outer stream survives.

```ts
// Wrong: first HTTP error completes the whole search stream
results$ = this.query$.pipe(
  switchMap(q => this.api.search(q)),
  catchError(() => of([])),   // outer: stream now completes after emitting []
);

// Right: error handled per request; the outer stream stays alive
results$ = this.query$.pipe(
  switchMap(q => this.api.search(q).pipe(
    retry({ count: 2, delay: (_err, attempt) => timer(attempt * 500) }),
    map(items => ({ items, error: null as string | null })),
    catchError(err => of({ items: [], error: toMessage(err) })),
  )),
);
```

**Go deeper:**
- **`retry({ count, delay, resetOnSuccess })`** is the RxJS 7 API. `delay` can be a number or a function `(error, retryCount) => ObservableInput`, which is how you do exponential backoff or skip retrying 4xx errors. `retryWhen` is deprecated.
- Only retry **idempotent** requests (GET). Retrying a non-idempotent POST can create duplicates.
- **`EMPTY` vs `throwError`:** `catchError(() => EMPTY)` swallows the error and **completes silently**. Downstream `forkJoin` then never emits, and loaders never turn off. `throwError(() => err)` re-throws, after logging or mapping, for someone further out to handle. Always use the factory form, because `throwError(err)` with a raw value is deprecated.
- Model errors as **data** (`{ status: 'error', error }`) when the UI needs to render them. Keep the stream alive and let the template decide.
- A cross-cutting HTTP error policy (401 → refresh or redirect, toast on 5xx) belongs in a functional `HttpInterceptorFn`, not in every component.

---

### Q11. `combineLatest` vs `forkJoin` vs `zip` vs `withLatestFrom`?

**Answer:**

| Operator | Emits when | Completes when | Typical use |
|---|---|---|---|
| `combineLatest([a$, b$])` | **Any** source emits, **after every source has emitted at least once** | All complete | Derived view state from several live sources (filters + data + page) |
| `forkJoin([a$, b$])` | **Once**, with the last value of each, **when all complete** | Right after emitting | Parallel one-shot HTTP calls ("load page data") |
| `zip(a$, b$)` | Pairs values **by index** (1st with 1st, 2nd with 2nd) | Any completes and its buffer drains | Rare: pairing request/response, correlating two sequences |
| `a$.pipe(withLatestFrom(b$))` | **Only when `a$` emits**, sampling b$'s latest | a$ completes | "On save click, grab the current form/state". b$ is context, not a trigger |

**Go deeper:**
- `combineLatest` has an initial-emission requirement: if one source never emits (for example a `Subject` with no value yet), nothing ever emits. Fix with `startWith(...)`, a `BehaviorSubject`, or a source that replays.
- `forkJoin` never emits if any source never completes (a store select, `valueChanges`, an `interval`). It **completes without emitting** if any source completes without a value (`EMPTY`, or an inner `catchError(() => EMPTY)`). `forkJoin([])` completes immediately.
- `withLatestFrom` also drops values until b$ has emitted once. That is a silent source of "my click did nothing".
- The dictionary form (`combineLatest({ user: user$, prefs: prefs$ })`) gives named results, which is more readable than tuple destructuring.
- The pipeable versions in RxJS 7 are `combineLatestWith` and `zipWith`. The old `combineLatest` operator form is deprecated.

---

### Q12. RxJS vs signals: when do you use which, and how do they interoperate?

**Answer:** signals are for **state**, meaning a value that exists now and changes: synchronous, glitch-free, fine-grained. RxJS is for **events over time and async orchestration**. They complement each other.

RxJS still wins when you need:
- **Time**: `debounceTime`, `throttleTime`, `auditTime`, `bufferTime`, `delay`, windows.
- **Cancellation and concurrency policy**: `switchMap`/`concatMap`/`exhaustMap`/`mergeMap(fn, n)`.
- **Backpressure-like control** (throttle, sample, buffer, drop while busy) for high-frequency sources such as websockets, scroll, pointer moves.
- **Retry/backoff**, multicast control, and composing many async sources.
- **Discrete events**, where two identical values in a row both matter. Signals dedupe by equality, and a signal represents "latest value", not "each occurrence".

Interop (`@angular/core/rxjs-interop`):
- **`toSignal(obs$, { initialValue })`** subscribes immediately (in an injection context) and unsubscribes on destroy. Without `initialValue` the type is `T | undefined`. `{ requireSync: true }` is for sources that emit synchronously, like a `BehaviorSubject`, and throws if they don't. An error in the observable is **rethrown when the signal is read**.
- **`toObservable(sig)`** is backed by an `effect`, so emissions are **asynchronous** and only the **settled latest** value comes through. Intermediate synchronous sets are coalesced. It also needs an injection context.
- **`rxResource({ params, stream })`** (option names since the resource API rename: `params` was `request`, `stream` was `loader`) bridges signal inputs to an observable loader with `value()`, `isLoading()` and `error()` signals. It cancels the previous stream when params change, giving switchMap semantics.
- `outputFromObservable` / `outputToObservable` connect component outputs.

```ts
@Component({
  selector: 'app-user-search',
  template: `
    <input [value]="query()" (input)="query.set($any($event.target).value)" />
    @for (u of results(); track u.id) { <app-user-row [user]="u" /> }
  `,
})
export class UserSearchComponent {
  private readonly api = inject(UserApi);
  readonly query = signal('');

  // signal -> RxJS for time + cancellation -> back to signal for the template
  readonly results = toSignal(
    toObservable(this.query).pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => this.api.search(q).pipe(catchError(() => of([])))),
    ),
    { initialValue: [] as User[] },
  );
}
```

Sound bite: *"Signals for what the template reads, RxJS for how events turn into state over time."*

---

### Q13. `firstValueFrom` / `lastValueFrom` vs `toPromise()`?

**Answer:** `toPromise()` is deprecated in RxJS 7 and slated for removal. Its problem is that a source completing without emitting resolved to `undefined`, which is silently ambiguous. Use:
- `firstValueFrom(obs$)`, which resolves on the first value **and unsubscribes**. Good for `store.select` or anything infinite.
- `lastValueFrom(obs$)`, which waits for **completion**. It never resolves on an infinite stream.
- Both **reject with `EmptyError`** if the source completes with no value, unless you pass `{ defaultValue }`.

Use them at `async/await` boundaries: guards, `APP_INITIALIZER`-style setup (`provideAppInitializer` in modern Angular), and tests. Inside components I keep things reactive.

---

### Q14. What's wrong with subscribe-inside-subscribe?

**Answer:** you lose **cancellation** (a new outer value doesn't cancel the old inner one), you lose **error propagation** (the inner error isn't seen by the outer handler), you get **leaks** (the inner subscription isn't tracked), and you can't compose or test it. Replace it with the flattening operator whose concurrency policy you actually want (Q1). This is the single most common thing I flag in code review.

```ts
// Anti-pattern
this.route.paramMap.subscribe(p => {
  this.api.getOrder(p.get('id')!).subscribe(o => this.order = o);
});

// Better (and zoneless/OnPush-safe)
readonly order = toSignal(
  this.route.paramMap.pipe(
    map(p => p.get('id')!),
    switchMap(id => this.api.getOrder(id)),
  ),
);
// Or, with withComponentInputBinding(): id = input.required<string>() + rxResource/httpResource
```

---

## B. Tricky / trap questions

### T1. "I use `forkJoin` to combine the current user from the store with an HTTP call, and it never emits. Why?"

**The trap:** thinking `forkJoin` is "combineLatest but once".
**Strong answer includes:**
- `forkJoin` waits for **every source to complete**. `store.select(...)` never completes, so it never emits.
- Fix by taking one value from the infinite source (`store.select(selectUser).pipe(take(1))`) or by using `combineLatest` or `withLatestFrom`, depending on intent.
- The mirror trap: if any source **completes without emitting**, for example an inner `catchError(() => EMPTY)`, `forkJoin` **completes without emitting**. The spinner never stops. If you need a partial result, handle errors per source with `catchError(() => of(null))`.

### T2. "Our typeahead works until the API returns a 500, then it stops responding. What happened?"

**The trap:** "Add a `catchError`" without saying *where*.
**Strong answer includes:**
- The `catchError` (or no handler at all) is on the outer stream. The error terminated the stream, and `catchError` replaced it with a one-off fallback that completed.
- Move `catchError` **inside** the `switchMap` projection so only that request is replaced (Q10 code).
- Optionally add `retry({ count, delay })` inside too, and expose an error state to the UI rather than an empty list that looks like "no results".

### T3. "Is `shareReplay(1)` a memory leak?"

**The trap:** answering yes or no flatly.
**Strong answer includes:**
- It depends on the source. With the default `refCount: false`, the source subscription is **never** torn down, even when all subscribers leave.
- For a **completing** source (HTTP), that's a deliberate cache. The only "leak" is the cached value, and the replay lives as long as the observable instance does. That's fine for a root-service config cache and wrong for per-entity data you never evict.
- For an **infinite** source (websocket, `interval`, store, `valueChanges`) it keeps running forever. Use `shareReplay({ bufferSize: 1, refCount: true })` or `share({ connector: () => new ReplaySubject(1), resetOnRefCountZero: true })`.
- Nuance: with `refCount: true`, a resubscribe after zero **re-executes** the source and does not replay the stale value. If you want a short grace period, use `resetOnRefCountZero: () => timer(ms)`.

### T4. "Why not `switchMap` for the save button? It stops double-submits."

**The trap:** confusing "cancels the previous" with "prevents duplicates".
**Strong answer includes:**
- `switchMap` **cancels the client-side subscription**. The first POST may already have reached the server, so you get two writes and only the second response is handled. Or the user's first change is lost and the UI and server disagree.
- For "ignore clicks while saving" use **`exhaustMap`**. For "every change must be saved in order" use **`concatMap`**. Also disable the button from a `saving` signal, because UX and the stream should agree.
- Cancelling a write needs a server-side notion: idempotency keys, or optimistic concurrency with ETags or versions.

### T5. "What's wrong with reading `BehaviorSubject.value` everywhere?"

**The trap:** it's convenient, so it must be fine.
**Strong answer includes:**
- It's an imperative snapshot. Code that reads `.value` doesn't react to later changes, which leads to stale UI and "works on first load" bugs.
- It spreads write access. A public `BehaviorSubject` lets any consumer call `.next()`, which breaks unidirectional flow. Expose `asObservable()` and methods instead.
- It hides dependencies, so you can't see from the pipe what a stream depends on. Prefer `withLatestFrom`, `combineLatest`, or a `computed()` signal.
- Legitimate uses: inside the owning service to compute the next state (`this.state$.next({ ...this.state$.value, x })`) and in tests. For new code, a `signal` gives you a synchronous read that *is* tracked when read in a reactive context.

### T6. "`combineLatest([filters$, page$, data$])` doesn't emit on first load. Why?"

**The trap:** assuming it emits as soon as anything emits.
**Strong answer includes:**
- It waits until **every** source has emitted at least once. A plain `Subject` for `page$` that nobody has nexted blocks everything.
- Fix with `startWith(initial)`, a `BehaviorSubject`, or signals plus `computed`, which always have a value.
- Also watch for **glitches**: if `filters$` and `page$` both change due to one user action, `combineLatest` can emit an intermediate inconsistent combination, possibly firing an extra HTTP request. Fix with `debounceTime(0)`/`auditTime(0)`, by modelling the change as one state object, or with signals, where `computed` is glitch-free.

### T7. "`distinctUntilChanged()` isn't working on my filter object."

**The trap:** expecting a deep compare.
**Strong answer includes:**
- The default comparison is `===`, so a newly built object is always "distinct".
- Use `distinctUntilChanged((a, b) => a.q === b.q && a.page === b.page)`, `distinctUntilKeyChanged('q')`, or map to a primitive first.
- Avoid `JSON.stringify` compares on hot paths: they are order-sensitive and slow.
- The same applies to signals: `signal`/`computed` use `Object.is` by default, and you can pass `{ equal }`.

### T8. "Is it OK to subscribe in a service?"

**The trap:** "Never" or "Always fine".
**Strong answer includes:**
- A **root** service subscribing to an app-lifetime source (for example, syncing auth state to storage) is fine and intentional. Its lifetime is the app.
- It's a leak when the service **outlives** what it subscribed on behalf of (per-component or per-route data held by a root service), or when a component subscribes to a root-service stream without teardown. The service's subject then holds the component's closure.
- Better: services **return** observables or expose signals and let consumers own the subscription. Where a service must subscribe, give it the right scope (provide it in the component's or route's `providers`) and use `takeUntilDestroyed(inject(DestroyRef))`.

---

## C. Code examples

### Polling that doesn't overlap, pauses when the tab is hidden, and cleans up

```ts
@Component({ selector: 'app-job-status', template: `{{ status()?.state }}` })
export class JobStatusComponent {
  private readonly api = inject(JobApi);
  readonly jobId = input.required<string>();

  private readonly visible$ = fromEvent(document, 'visibilitychange').pipe(
    map(() => document.visibilityState === 'visible'),
    startWith(document.visibilityState === 'visible'),
  );

  readonly status = toSignal(
    combineLatest([toObservable(this.jobId), this.visible$]).pipe(
      switchMap(([id, visible]) => !visible ? EMPTY : timer(0, 5000).pipe(
        exhaustMap(() => this.api.status(id).pipe(   // skip a tick if the last poll is still running
          catchError(() => EMPTY),                   // one failed poll doesn't kill polling
        )),
        takeWhile(s => s.state !== 'done', true),
      )),
    ),
  );
  // toSignal owns the subscription, so it is torn down on destroy. No manual unsubscribe.
}
```

### A small "store-lite" service with RxJS (legacy style) vs signals (current style)

```ts
// Legacy but valid: BehaviorSubject service
@Injectable({ providedIn: 'root' })
export class CartStoreRx {
  private readonly state = new BehaviorSubject<CartState>({ items: [] });
  readonly items$ = this.state.pipe(map(s => s.items), distinctUntilChanged());
  add(item: Item) {
    const s = this.state.value;
    this.state.next({ ...s, items: [...s.items, item] });
  }
}

// Current: signals for state; RxJS only where time or cancellation matters
@Injectable({ providedIn: 'root' })
export class CartStore {
  private readonly _items = signal<Item[]>([]);
  readonly items = this._items.asReadonly();
  readonly total = computed(() => this._items().reduce((t, i) => t + i.price, 0));
  add(item: Item) { this._items.update(items => [...items, item]); }
}
```

(In v22 you can also mark a service with `@Service()`, which is provided in root by default. `@Injectable({ providedIn: 'root' })` still works and is what most existing codebases use.)

### Custom operator (shared-library friendly)

```ts
export function withLoading<T>(loading: WritableSignal<boolean>): MonoTypeOperatorFunction<T> {
  return source => defer(() => {
    loading.set(true);
    return source.pipe(finalize(() => loading.set(false)));
  });
}

// usage: this.api.load().pipe(withLoading(this.loading))
```

`defer` makes the side effect happen per subscription rather than at pipe-construction time. `finalize` runs on complete, error, **and** unsubscribe (cancellation), which is the case people forget.

---

## D. Red flags

- **"I always use `switchMap`."** Say instead: "I pick by concurrency policy: switch for latest-wins reads, concat for ordered writes, exhaust for submit buttons, merge for independent parallel work."
- **"I put `catchError` at the end of the pipe."** Say instead: "It goes inside the inner observable if the outer stream must survive. The outer level is only for when I want the stream to end."
- **"`shareReplay(1)` everywhere for caching."** Say instead: "`shareReplay(1)` for finite, app-lifetime caches. `refCount: true`, or `share` with a reset policy, for long-lived sources."
- **"I unsubscribe in every `ngOnDestroy` with a `subs` array."** Say instead: "I avoid manual subscriptions with `async` and `toSignal`, and use `takeUntilDestroyed` when I must subscribe."
- **"HTTP observables complete, so I never care about unsubscribing."** Say instead: "They don't leak memory, but their callbacks still run after destroy, so I tie them to lifetime or make them cancellable."
- **Nested `subscribe()` in examples.** Say instead: "Flatten with the operator matching the concurrency I need."
- **"Signals replace RxJS."** Say instead: "Signals replace RxJS for synchronous state. RxJS stays for events over time, cancellation and orchestration, and the interop functions connect the two."
- **"`toPromise()`"**. Say instead: "`firstValueFrom`/`lastValueFrom`, knowing they reject with `EmptyError` on empty completion."
- **"RxJS 8 changed X"**. Say instead: "We're on RxJS 7.8. The v7 APIs are `retry` config objects, `share` config, and `firstValueFrom`."
- **"`forkJoin` combines streams."** Say instead: "`forkJoin` waits for completion, so it's for one-shot parallel calls. `combineLatest` is for live sources."
- **Setting a plain field in `subscribe()` and wondering why the view doesn't update** (under zoneless or OnPush). Say instead: "Push values through `async`, a signal, or `toSignal` so change detection is scheduled correctly."

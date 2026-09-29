# 05 — State Management (Flux, Redux, NgRx, SignalStore, services with signals)

> **How to use this file:** the job spec says "Flux/Redux state management". Expect a mix of *principles* questions (why unidirectional flow, why immutability, why pure reducers) and *judgement* questions (when would you **not** use NgRx? What belongs in a global store?). At senior level, and especially with a design-authority background, the interviewer is probing whether you can **pick the lightest tool that fits**, **structure a feature slice cleanly** (actions as events, normalized state, memoized selectors, effects with correct flattening and error handling), and **talk about the modern options** (NgRx SignalStore, services with signals, resource APIs for server state) without treating any of them as a religion. Versions: NgRx **22.x** is current and aligned with Angular 22. `@ngrx/signals` (SignalStore) is the recommended default for new local and feature state. Classic `@ngrx/store` is fully supported. `@ngrx/component-store` still exists, but SignalStore is recommended for new code. Section C has one end-to-end classic NgRx slice and one SignalStore equivalent.

---

## A. Most commonly asked questions

### Q1. Explain Flux and the core Redux principles.

**Answer (1–2 min):**
- **Flux** (Facebook, around 2014) is an architecture for **unidirectional data flow**: *View → Action → Dispatcher → Store(s) → View*. Views never mutate stores directly. They dispatch actions. A single **dispatcher** broadcasts each action to every **store**, stores update themselves and emit change, and views re-render. The motivation was two-way binding and model-to-model cascades making it impossible to reason about "why did this change?"
- **Redux** simplified Flux into three principles:
  1. **Single source of truth**: one state tree, in one store.
  2. **State is read-only**: the only way to change it is to dispatch an **action** (a plain object describing what happened).
  3. **Changes are made with pure functions**: `reducer(state, action) => newState`. No side effects, no mutation, deterministic.
- Side effects (HTTP, storage, navigation) live outside reducers: Redux middleware, NgRx **effects**, or SignalStore methods and event handlers.
- What you gain: predictability, traceability (the action log *is* the audit trail), time-travel debugging, easy testing (reducers and selectors are pure functions), and cheap change detection (a reference compare tells you whether something changed).
- The cost is ceremony and indirection. For a lot of apps that cost isn't worth paying. See Q9.

**Go deeper:** NgRx = Redux + RxJS + Angular DI. Its `Store` is an observable of state, `Actions` is an observable of actions, and effects are RxJS pipelines from actions to actions.

---

### Q2. What does good action design look like in NgRx? What is "events, not commands"?

**Answer:**
- An action should describe **what happened and where**, not **what to do**. Prefer `[Books Page] Opened` or `[Books API] Books Loaded Success` over `[Books] Load Books` or `[Books] Set Books`.
- Why: an event keeps the component ignorant of consequences. Reducers and effects decide what happens, and several of them can react to one event. Command-style actions like `setX` turn the store into a remote-controlled setter bag, which is a service with extra steps.
- **One action per source.** Don't reuse `loadBooks` from the page, the sidebar and a resolver. Unique sources make DevTools traces readable and let you change behaviour per source.
- **Don't dispatch several actions in a row** from a component (`dispatch(a); dispatch(b)`). That usually means one event is being modelled as several commands. The NgRx ESLint plugin flags it (`avoid-dispatching-multiple-actions-sequentially`), and has a `good-action-hygiene` rule.
- Use **`createActionGroup`**: one source, event names in Title Case, and camelCased creators are generated for you.

```ts
export const BooksPageActions = createActionGroup({
  source: 'Books Page',
  events: {
    'Opened': emptyProps(),
    'Search Changed': props<{ query: string }>(),
    'Book Selected': props<{ id: string }>(),
  },
});
// BooksPageActions.opened(), BooksPageActions.searchChanged({ query }), ...

export const BooksApiActions = createActionGroup({
  source: 'Books API',
  events: {
    'Books Loaded Success': props<{ books: Book[] }>(),
    'Books Loaded Failure': props<{ error: string }>(),
  },
});
```

---

### Q3. Reducers: `createReducer`/`on` and `createFeature`. What are the rules?

**Answer:**
- A reducer is a **pure** function. It creates no IDs, does no `Date.now()` or HTTP, and **never mutates**. It returns the same reference when nothing changed and a new reference along the changed path when something did.
- `createReducer(initialState, on(action1, action2, (state, action) => newState), ...)`. The `on` handler is typed from the action creator.
- **`createFeature({ name, reducer, extraSelectors? })`** removes boilerplate. It generates a feature selector (`selectBooksState`) and one selector per top-level state property (`selectQuery`, `selectStatus`, ...). `extraSelectors` is where derived selectors go, co-located with the feature.
- Register it with `provideState(booksFeature)`, typically in **route `providers`** for a lazy-loaded feature, and `provideStore()` at the root.

**Go deeper:** non-deterministic values (UUIDs, timestamps) are generated where the action is created (component, effect, or a `props` factory) and carried *in* the action, so the reducer stays replayable.

---

### Q4. Selectors: memoization, parameterized selectors, `selectSignal`.

**Answer:**
- `createSelector(...inputSelectors, projector)` is **memoized**. The projector reruns only when an input selector's result changes **by reference**. When it doesn't rerun, you get the **same output reference**, which is what makes OnPush, `distinctUntilChanged` and `@for` tracking cheap.
- Selectors compose: build small ones (`selectEntities`, `selectSelectedId`) and derive bigger ones (`selectSelectedBook`). **Derived data belongs in selectors, not in state** (see T5).
- **Parameterized selectors: use a factory.** Selectors with `props` are **deprecated**.

```ts
export const selectBookById = (id: string) =>
  createSelector(booksFeature.selectEntities, entities => entities[id]);
```

  Each factory call creates a **new selector with its own memo cache**. Call it once per id (in a field initialiser, or cached), not in a template expression or getter that runs on every change-detection pass.
- **`store.selectSignal(selector)`** returns a `Signal`, which is my default in components now. It gives a typed value, no `async` pipe and no `null` initial, and it composes with `computed`. `store.select()` still returns an Observable, which is useful when you need RxJS operators.
- For a dynamic id from an `input()`, I often select the entity map once and derive with `computed(() => this.entities()[this.id()])`, rather than recreating selectors.

---

### Q5. Effects: what are they, how do you write them, and which flattening operator?

**Answer:**
- Effects listen to the action stream, perform side effects, and (usually) map the result to new actions. Reducers stay pure. Components stay ignorant of HTTP.
- In modern code I write **functional effects**: `createEffect((actions$ = inject(Actions), api = inject(BooksApi)) => ..., { functional: true })`, registered with `provideEffects(...)`. There's no class, and they are easy to test by passing mocks as arguments.
- **Error handling goes inside the inner pipe.** If an error reaches the outer `actions$` pipe, the effect's stream dies. NgRx resubscribes effects after errors (up to a limit, 10 by default), but relying on that is a bug-masking mechanism, not a design. Map errors to a failure action inside the `switchMap`/`concatMap`/etc.
- Choose the flattening operator by concurrency policy (same as `02-rxjs.md` Q1):
  - `switchMap`: **reads** where the latest wins (search, load on route change).
  - `concatMap`: **writes** that must all happen in order (update, reorder).
  - `mergeMap`: independent writes that can run in parallel (delete item X and Y).
  - `exhaustMap`: ignore repeats while busy (login, "Opened" re-fired, refresh).
  - `switchMap` on a write can cancel a save on the client after the server has already applied it. That's a classic review comment.
- Non-dispatching effects (navigation, toasts, analytics) need `{ dispatch: false }`. See T3 for what happens if you forget.

```ts
export const loadBooks = createEffect(
  (actions$ = inject(Actions), api = inject(BooksApi)) =>
    actions$.pipe(
      ofType(BooksPageActions.opened),
      exhaustMap(() =>
        api.getAll().pipe(
          map(books => BooksApiActions.booksLoadedSuccess({ books })),
          catchError((err: unknown) =>
            of(BooksApiActions.booksLoadedFailure({ error: toMessage(err) }))),
        ),
      ),
    ),
  { functional: true },
);
```

**Go deeper:** `concatLatestFrom(() => store.select(x))` (from `@ngrx/operators`) is the lazy alternative to `withLatestFrom` for reading state in an effect. It evaluates the selector only when the action arrives. `tapResponse` and `mapResponse` (also in `@ngrx/operators`) package the "handle the error inside" pattern.

---

### Q6. What is `@ngrx/entity` and why normalize state?

**Answer:**
- **Normalized state** stores collections as `{ ids: string[]; entities: Record<string, T> }` instead of `T[]`, and references other entities **by id** instead of nesting them.
- Why:
  - **O(1) lookups and updates** by id.
  - **One copy of each entity.** Nested duplicates drift out of sync when one copy gets updated.
  - **Smaller, cheaper immutable updates.** Updating one book creates a new `entities` object and a new book, and every other book keeps its reference, so OnPush rows for other books don't re-render.
  - It works cleanly with memoized selectors.
- `@ngrx/entity` gives you an adapter so you don't hand-write that logic:

```ts
export const booksAdapter = createEntityAdapter<Book>({
  selectId: b => b.id,                                  // default is `id`
  sortComparer: (a, b) => a.title.localeCompare(b.title), // or false for insertion order
});

const initialState = booksAdapter.getInitialState({ status: 'idle' as Status, error: null as string | null });

// in reducer handlers
booksAdapter.setAll(books, state);
booksAdapter.upsertOne(book, state);
booksAdapter.updateOne({ id, changes: { title } }, state);
booksAdapter.removeOne(id, state);

// selectors
const { selectAll, selectEntities, selectIds, selectTotal } = booksAdapter.getSelectors();
```

- **Denormalize in selectors** when the view needs a joined shape (book plus author objects), so the join is memoized and computed once.

---

### Q7. What's NgRx SignalStore and how does it compare with classic NgRx?

**Answer:** `signalStore(...)` from `@ngrx/signals` builds an injectable store out of composable **features**:
- **`withState(initial)`** makes each top-level property a (deep) signal: `store.books()`, `store.filter.query()`.
- **`withComputed(store => ({ ... computed(...) }))`** holds derived state.
- **`withMethods(store => ({ ... }))`** holds public API and state updates via **`patchState(store, partial | updaterFn)`**. `patchState` only works inside the store by default, because state is protected from outside writes.
- **`rxMethod<T>(pipe(...))`** gives you an RxJS pipeline as a method. You can call it with a value, a signal, or an observable. This is where debounce, `switchMap` and cancellation live.
- **`withHooks({ onInit, onDestroy })`** holds lifecycle logic, such as loading on init.
- **`withProps`** adds non-state properties (injected services, observables, resources) to share across features. Members prefixed with `_` are private to the store.
- **`withEntities<T>()`** from `@ngrx/signals/entities` adds `ids`, `entityMap` and `entities` signals plus updaters (`setAll`, `addEntity`, `updateEntity`, `removeEntity`, ...) used with `patchState`. Named collections are supported for multiple entity types in one store.
- **`signalStoreFeature(...)`** builds **custom reusable features**, for example a `withRequestStatus()` that adds `status`/`error` state and `isLoading` computed. This is where a shared-library owner adds value: one standard feature used across teams.
- `withLinkedState` exists for state derived from other state that can still be overridden locally (the SignalStore counterpart of `linkedSignal`).
- **Events plugin** (`@ngrx/signals/events`): `eventGroup`, `withReducer(on(...))` and `withEventHandlers(...)` give you Redux-style **events-not-commands** on top of SignalStore when you want the decoupling without the global store. It is the newer part of the library, so I'd confirm the exact API against the installed version.

Scope: `signalStore({ providedIn: 'root' }, ...)` for global state, or no `providedIn` plus `providers: [BooksStore]` on a component or route, so the store's lifetime **equals the feature's lifetime** and it gets destroyed with it. That scoping is a big design advantage over one global tree.

Comparison sound bite: *"Classic NgRx gives you a global event log, strict separation and DevTools time travel, and you pay in ceremony. SignalStore gives you most of the structure with a fraction of the code, and it's scoped by DI. For new feature state I default to SignalStore. I reach for the global store when many features react to the same events, or when the action log itself has value."*

---

### Q8. What about ComponentStore?

**Answer:** `@ngrx/component-store` was the RxJS-based local store: `select`, `updater`, `effect`, provided at component level. It is **still maintained and valid** in existing code, but SignalStore is its successor for new code. It is lighter, signal-native, and composes better through features. In an enterprise codebase I wouldn't rewrite working ComponentStores for the sake of it. I'd migrate opportunistically when a feature is being reworked anyway.

---

### Q9. When would you NOT use NgRx? How do you decide?

**Answer:** first I split **server state** from **client state**:
- **Server state** (lists, entities, details fetched over REST) is really a **cache** with loading/error/staleness/refetch concerns. Putting it in Redux makes you hand-roll a cache. Options: `httpResource`/`rxResource`, a small service with signals, or a dedicated server-cache library (TanStack Query has an Angular adapter; I'd check its current maturity before adopting).
- **Client state** splits into:
  - **Local UI state** (open panels, form state, hover, pagination of one table) belongs in the component: `signal`s, Signal Forms or reactive forms.
  - **Feature state** shared by a few components in one route belongs in a **service with signals** or a **component/route-scoped SignalStore**.
  - **Global cross-feature state** (auth/session, permissions, cart, feature flags, notifications) is a candidate for a root SignalStore or classic NgRx.

Then the decision factors:

| Factor | Pushes toward classic NgRx | Pushes toward SignalStore / services |
|---|---|---|
| Many features reacting to the same events | Yes | Few consumers |
| Need an audit/action log, DevTools time travel, replay | Yes | Not needed |
| Team size and turnover | Large, many teams (a strict pattern helps consistency) | Small team, strong conventions |
| Complex async orchestration (sagas, cancellations across features) | Effects shine | Simple CRUD |
| Mostly server data with light client logic | No | Yes (+ resource APIs or a query library) |
| Existing codebase already on NgRx | Stay consistent | New isolated app |

Sound bite: *"The question isn't NgRx vs services. It's what kind of state this is, who needs it, and how long it lives. Most enterprise screens are server cache plus local UI state. The genuinely global, event-driven part is usually small."*

---

### Q10. What's the "service with signals" pattern?

**Answer:** a plain injectable holding **private writable signals**, exposing **readonly signals and computeds**, and offering **methods** as the only write path. It is unidirectional flow with no library.

```ts
@Injectable({ providedIn: 'root' }) // or @Service() in v22+
export class CartService {
  private readonly api = inject(CartApi);
  private readonly _items = signal<CartItem[]>([]);
  private readonly _status = signal<'idle' | 'saving' | 'error'>('idle');

  readonly items = this._items.asReadonly();
  readonly status = this._status.asReadonly();
  readonly total = computed(() => this._items().reduce((t, i) => t + i.price * i.qty, 0));

  add(item: CartItem) {
    this._items.update(items => [...items, item]); // immutable update
  }
}
```

- It is perfect for small-to-medium shared state.
- It degrades when a few conditions pile up: async orchestration grows, several services start calling each other, or you want consistent patterns across teams. That's the point where I'd move to SignalStore, which is basically this pattern with structure, entities, `rxMethod` and reusable features.
- For shared-library consumers I'd expose signals (`Signal<T>`), not `WritableSignal`s.

---

### Q11. Why immutability? What are the pitfalls?

**Answer:**
- **Change detection by reference.** OnPush (the component default since v22), memoized selectors, `distinctUntilChanged` and signal equality (`Object.is`) all assume "new reference means changed, same reference means unchanged". Mutation breaks that silently: the data changed, the reference didn't, so the UI doesn't update, or a memoized selector returns stale output.
- **Predictability and debugging.** Time travel and action replay need past states to stay intact.
- **Structural sharing.** An immutable update copies only the path to the change, and everything else keeps its reference. It's cheap and it's what makes fine-grained re-rendering possible.

Pitfalls:
- **Spread is shallow.** `{ ...state, user: state.user }` followed by `state.user.address.city = 'X'` is still a mutation.
- **Mutating array methods**: `push`, `splice`, `sort`, `reverse`, and `Object.assign(target, ...)` on existing state. Use the non-mutating ES2023 methods (`toSorted`, `toSpliced`, `with`) or spread first.
- **Deep spreads get unreadable.** At three or more levels, normalize the state or use a helper.
- **Over-copying.** Returning a new object when nothing changed defeats memoization.

Tooling:
- **NgRx runtime checks**: `strictStateImmutability` and `strictActionImmutability` are on by default in development and freeze state and actions, so a mutation throws immediately. Serializability and action-type-uniqueness checks are opt-in via `provideStore(reducers, { runtimeChecks: { ... } })`.
- **Immer** (via a community NgRx integration) lets you write mutable-looking code that produces immutable updates. It's useful for deeply nested updates, but it adds a dependency.
- In SignalStore, `patchState` expects new references. In development, state is frozen too, so mutation shows up early.

---

### Q12. Why does a selector that returns a new array break OnPush benefits?

**Answer:**
- If a selector (or `computed`) builds a new array or object **every time it runs**, even with identical contents, every consumer sees a "new" value. `@for` re-diffs, OnPush children receiving it as an `input()` get marked dirty, and downstream `computed`s rerun.
- Memoized `createSelector` protects you only when **its inputs** haven't changed by reference. So:
  - Keep input selectors narrow. Select `state.books.entities`, not `state`, so unrelated state changes don't rerun the projector.
  - Never pass an **unmemoized inline function** (`store.select(s => s.books.filter(...))`) for derived data. It runs and returns a new array on every state change.
  - Don't `map` entities into new view-model objects when you could pass the originals. If you must, accept the cost at a low level of the tree, or give the consumer a custom `equal`.
- `selectSignal(selector, { equal })` and `computed(fn, { equal })` accept custom equality as an escape hatch. It's better to fix the reference churn at the source.

---

### Q13. How do you structure a feature slice in a large codebase?

**Answer:**
- Colocate by feature: `books/state/{books.actions.ts, books.feature.ts (reducer + selectors), books.effects.ts}`, or `books.store.ts` for SignalStore.
- Register lazily in route `providers` (`provideState`, `provideEffects`, or the store class), so feature state loads with the route.
- Components talk to state through **selectors/signals and events** only. Some teams add a **facade** service. That is useful in a component library or for migrations, because it hides whether the backing is NgRx or SignalStore. The trade-off is that it can end up re-inventing commands (`facade.loadBooks()`), so keep facade methods named as events.
- Enforce the patterns with the NgRx ESLint plugin in the shared lint config, plus a short ADR on "what goes where". That's the design-authority lever.

---

## B. Tricky / trap questions

### T1. "The reducer updates the list but the OnPush list component doesn't re-render. Why?"

**The trap:** "Call `markForCheck()`" or "switch to Default/Eager change detection".
**Strong answer includes:**
- The reducer **mutated** state (`state.items.push(x); return state;` or `return { ...state }` with a mutated nested array). The input reference didn't change, so OnPush saw no change, and a memoized selector returned its cached output.
- Fix the reducer: `return { ...state, items: [...state.items, x] }` or `adapter.addOne(x, state)`.
- Prevent it: runtime immutability checks (on by default in dev) throw on mutation. That is why they must not be disabled "because they were annoying".
- Context: since v22, components without an explicit strategy are OnPush by default (`ChangeDetectionStrategy.Default` is deprecated in favour of `Eager`), so mutation bugs that used to be masked by default change detection now show up.

### T2. "We put everything in the store: form values, which accordion is open, table sort, modal visibility. Good idea?"

**The trap:** "Single source of truth means everything."
**Strong answer includes:**
- "Single source of truth" means one owner **per piece of state**, not one tree for all state.
- Ephemeral UI state (open panels, hover, in-progress form input) is local. Putting it in the global store adds boilerplate, noise in DevTools, cross-feature coupling, and bugs when the component is re-instantiated but the state lingers.
- Put state in the store if it must **survive navigation**, be **shared across features**, or be **reacted to by effects**. For example, persisted table preferences or the "last search" if the business wants it restored.
- Form state belongs to the form (Signal Forms/reactive forms). Dispatch an event on submit, not on every keystroke.

### T3. "An effect is spinning the browser into an infinite loop. What are the usual causes?"

**The trap:** blaming NgRx.
**Strong answer includes:**
- A non-dispatching effect without `{ dispatch: false }`. `tap(() => router.navigate(...))` passes the **incoming action back out**, it gets re-dispatched, the same effect catches it, and so on forever.
- An effect that maps action A to action A, or A to B while another effect maps B back to A. This is often caused by command-style actions like `loadX` being dispatched from several places.
- An effect reacting to a store change (via `store.select`) that dispatches an action that changes the same slice.
- Fixes: `{ dispatch: false }` for side-effect-only effects; events named by source so cycles are visible; avoid effects triggered by state rather than by events where possible.

### T4. "How do you pass a parameter to a selector?"

**The trap:** `store.select(selectBook, { id })` (selectors with props), which is **deprecated**.
**Strong answer includes:**
- Use a factory selector: `selectBookById = (id) => createSelector(...)`.
- Memoization is per selector instance, so create it once per id and don't recreate it on every render.
- Alternative: select the entity map once and derive with `computed()` from an `input()` signal. That's often simplest in signal-based components.

### T5. "We store `filteredBooks` and `totalPrice` in state alongside `books` so they're fast to read. OK?"

**The trap:** caching derived data in state.
**Strong answer includes:**
- Derived data in state is **duplicated state**. Every reducer that touches `books` must remember to update `filteredBooks`, and one day one won't.
- Store the **minimal** state (`books`, `filter`) and derive with memoized selectors or `computed()`. They are already cached and recompute only when inputs change.
- Exception: very expensive derivations that must survive across sessions, and even then it's a deliberate, documented cache.

### T6. "NgRx or services? Which camp are you in?"

**The trap:** picking a side dogmatically, either "NgRx is boilerplate hell" or "Always NgRx in enterprise".
**Strong answer includes:**
- There is no camp. Use the decision framework (Q9): kind of state, number of consumers, lifetime, async complexity, team size, existing conventions.
- All of these options implement the same idea: unidirectional flow, a single writer per state, immutable updates, derived state via memoized functions. SignalStore and a well-written signal service are on the same spectrum as NgRx.
- As a design authority: "What I care about is consistency. One documented default per state category, with an escape hatch and an ADR, beats every team choosing freshly."

### T7. "Our store holds all API responses, with loading flags and TTLs we built by hand. Problem?"

**The trap:** not recognising that you built a server cache inside Redux.
**Strong answer includes:**
- Server state has different concerns: staleness, background refetch, deduping concurrent requests, invalidation after mutations, retry, pagination. Hand-rolled `loading/loaded/error/lastFetched` per slice is error-prone boilerplate.
- Options: Angular `resource`/`httpResource`/`rxResource` for component- or feature-scoped fetching, a server-cache library such as TanStack Query's Angular adapter, or at least a shared `withRequestStatus`/caching SignalStore feature so it's done once.
- Keep the store for **client** state and for cross-feature events. Don't abandon NgRx if the app is already built on it. Introduce the split for new features.

### T8. "Should `catchError` go at the end of the effect?"

**The trap:** yes, in the outer pipe.
**Strong answer includes:**
- No. Inside the inner observable, mapped to a failure action. An outer error completes the effect stream. NgRx's default error handler resubscribes a limited number of times, which hides the bug until it stops working.
- Also check the flattening operator (Q5): error handling doesn't help if `switchMap` is cancelling saves.

---

## C. Code examples

### C1. Classic NgRx: an end-to-end feature slice

```ts
// books.actions.ts
export const BooksPageActions = createActionGroup({
  source: 'Books Page',
  events: {
    'Opened': emptyProps(),
    'Search Changed': props<{ query: string }>(),
  },
});

export const BooksApiActions = createActionGroup({
  source: 'Books API',
  events: {
    'Books Loaded Success': props<{ books: Book[] }>(),
    'Books Loaded Failure': props<{ error: string }>(),
  },
});
```

```ts
// books.feature.ts
export interface BooksState extends EntityState<Book> {
  query: string;
  status: 'idle' | 'loading' | 'loaded' | 'error';
  error: string | null;
}

const adapter = createEntityAdapter<Book>({
  sortComparer: (a, b) => a.title.localeCompare(b.title),
});

const initialState: BooksState = adapter.getInitialState({
  query: '',
  status: 'idle',
  error: null,
});

export const booksFeature = createFeature({
  name: 'books',
  reducer: createReducer(
    initialState,
    on(BooksPageActions.opened, (state): BooksState => ({ ...state, status: 'loading', error: null })),
    on(BooksPageActions.searchChanged, (state, { query }): BooksState => ({ ...state, query })),
    on(BooksApiActions.booksLoadedSuccess, (state, { books }): BooksState =>
      adapter.setAll(books, { ...state, status: 'loaded' })),
    on(BooksApiActions.booksLoadedFailure, (state, { error }): BooksState =>
      ({ ...state, status: 'error', error })),
  ),
  extraSelectors: ({ selectBooksState, selectQuery, selectStatus }) => {
    const { selectAll } = adapter.getSelectors(selectBooksState);
    const selectFilteredBooks = createSelector(selectAll, selectQuery, (books, query) => {
      const q = query.trim().toLowerCase();
      return q ? books.filter(b => b.title.toLowerCase().includes(q)) : books; // same ref when no filter
    });
    const selectIsLoading = createSelector(selectStatus, s => s === 'loading');
    return { selectAllBooks: selectAll, selectFilteredBooks, selectIsLoading };
  },
});
```

```ts
// books.effects.ts
export const loadBooks = createEffect(
  (actions$ = inject(Actions), api = inject(BooksApi)) =>
    actions$.pipe(
      ofType(BooksPageActions.opened),
      exhaustMap(() =>                 // re-opening while loading shouldn't fire a second request
        api.getAll().pipe(
          map(books => BooksApiActions.booksLoadedSuccess({ books })),
          catchError((err: unknown) =>
            of(BooksApiActions.booksLoadedFailure({ error: toMessage(err) }))),
        ),
      ),
    ),
  { functional: true },
);

export const notifyLoadFailure = createEffect(
  (actions$ = inject(Actions), toast = inject(ToastService)) =>
    actions$.pipe(
      ofType(BooksApiActions.booksLoadedFailure),
      tap(({ error }) => toast.error(error)),
    ),
  { functional: true, dispatch: false },   // without this: infinite loop
);
```

```ts
// books.routes.ts
import * as booksEffects from './state/books.effects';

export const BOOKS_ROUTES: Routes = [{
  path: '',
  providers: [provideState(booksFeature), provideEffects(booksEffects)],
  loadComponent: () => import('./books-page.component').then(m => m.BooksPageComponent),
}];
```

```ts
// books-page.component.ts (OnPush is the default in v22; explicit here for older versions)
@Component({
  selector: 'app-books-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [BookRowComponent],
  template: `
    <input [value]="query()" (input)="onSearch($any($event.target).value)" placeholder="Search" />
    @if (isLoading()) { <app-spinner /> }
    @for (book of books(); track book.id) {
      <app-book-row [book]="book" />
    } @empty {
      <p>No books.</p>
    }
  `,
})
export class BooksPageComponent {
  private readonly store = inject(Store);
  readonly books = this.store.selectSignal(booksFeature.selectFilteredBooks);
  readonly isLoading = this.store.selectSignal(booksFeature.selectIsLoading);
  readonly query = this.store.selectSignal(booksFeature.selectQuery);

  constructor() {
    this.store.dispatch(BooksPageActions.opened());
  }

  onSearch(query: string) {
    this.store.dispatch(BooksPageActions.searchChanged({ query }));
  }
}
```

Testing notes: reducers and selectors are pure, so you can test them without TestBed (`selectFilteredBooks.projector(books, 'ang')`). Test functional effects by calling them with `of(action)` and mock services as arguments. Use `provideMockStore` for components.

### C2. The same feature as a SignalStore (with a reusable custom feature)

```ts
// shared/with-request-status.ts: a reusable feature for the component library / shared lib
export type RequestStatus = 'idle' | 'loading' | 'loaded' | { error: string };

export function withRequestStatus() {
  return signalStoreFeature(
    withState<{ requestStatus: RequestStatus }>({ requestStatus: 'idle' }),
    withComputed(({ requestStatus }) => ({
      isLoading: computed(() => requestStatus() === 'loading'),
      error: computed(() => {
        const s = requestStatus();
        return typeof s === 'object' ? s.error : null;
      }),
    })),
  );
}
export const setLoading = () => ({ requestStatus: 'loading' as const });
export const setLoaded = () => ({ requestStatus: 'loaded' as const });
export const setError = (error: string) => ({ requestStatus: { error } });
```

```ts
// books.store.ts
export const BooksStore = signalStore(
  // no providedIn: provided on the route/component, so it lives and dies with the feature
  withEntities<Book>(),
  withState({ query: '' }),
  withRequestStatus(),
  withComputed(({ entities, query }) => ({
    filteredBooks: computed(() => {
      const q = query().trim().toLowerCase();
      return q ? entities().filter(b => b.title.toLowerCase().includes(q)) : entities();
    }),
  })),
  withMethods((store, api = inject(BooksApi)) => ({
    setQuery(query: string) {
      patchState(store, { query });
    },
    load: rxMethod<void>(
      pipe(
        tap(() => patchState(store, setLoading())),
        exhaustMap(() =>
          api.getAll().pipe(
            tapResponse({
              next: books => patchState(store, setAllEntities(books), setLoaded()),
              error: (err: unknown) => patchState(store, setError(toMessage(err))),
            }),
          ),
        ),
      ),
    ),
    rename: rxMethod<{ id: string; title: string }>(
      pipe(
        concatMap(({ id, title }) =>        // writes: ordered, never cancelled
          api.update(id, { title }).pipe(
            tapResponse({
              next: book => patchState(store, updateEntity({ id, changes: book })),
              error: (err: unknown) => patchState(store, setError(toMessage(err))),
            }),
          ),
        ),
      ),
    ),
  })),
  withHooks({
    onInit(store) {
      store.load();
    },
  }),
);
```

```ts
@Component({
  selector: 'app-books-page',
  providers: [BooksStore],
  template: `
    <input [value]="store.query()" (input)="store.setQuery($any($event.target).value)" />
    @if (store.isLoading()) { <app-spinner /> }
    @if (store.error(); as error) { <app-error [message]="error" /> }
    @for (book of store.filteredBooks(); track book.id) {
      <app-book-row [book]="book" (renamed)="store.rename({ id: book.id, title: $event })" />
    }
  `,
})
export class BooksPageComponent {
  protected readonly store = inject(BooksStore);
}
```

(`tapResponse` is from `@ngrx/operators`. `setAllEntities` and `updateEntity` are from `@ngrx/signals/entities`. `patchState` accepts several updaters at once.)

What to say when comparing C1 and C2: *"Same unidirectional flow and the same immutability, but in C2 the lifetime is scoped to the route, there's no global action log, and there's roughly a third of the code. If other features had to react to 'books loaded', I'd either use the SignalStore events plugin or move to the global store."*

---

## D. Red flags

- **"Every app needs NgRx."** Say instead: "I classify the state first (server cache, local UI, feature, global) and pick the lightest tool per category."
- **"NgRx is just boilerplate."** Say instead: "It trades code for traceability and consistency. Worth it when many features react to shared events. Otherwise SignalStore or services."
- **Action names like `setBooks`, `loadBooks` reused everywhere.** Say instead: "Actions are events with a source, such as `[Books Page] Opened`. Reducers and effects decide the consequences."
- **Mutating in reducers, or disabling runtime checks.** Say instead: "Immutable updates with structural sharing. The runtime checks stay on in dev because they catch exactly the bugs OnPush exposes."
- **`catchError` in the outer effect pipe.** Say instead: "Errors are mapped to failure actions inside the inner observable."
- **`switchMap` for save/update effects.** Say instead: "`concatMap` or `exhaustMap` for writes, `switchMap` for reads."
- **Selectors with props.** Say instead: "Factory selectors, created once per parameter, or `computed` over the entity map."
- **Storing derived data (`filteredItems`, totals) in state.** Say instead: "Minimal state, with derived values in memoized selectors or `computed`."
- **Putting form input and UI toggles in the global store.** Say instead: "Local state stays local. The store gets what must be shared, persisted or reacted to."
- **"ComponentStore is dead, rewrite it all."** Say instead: "It's still supported. SignalStore is the default for new code, and I migrate when a feature is being reworked anyway."
- **Mixing `store.select` with manual `subscribe` in components.** Say instead: "`selectSignal` or `toSignal`, so the template reads signals and there's no subscription to leak."
- **"Redux is the single source of truth, so the store should mirror the backend."** Say instead: "Server data is a cache with its own concerns (staleness, refetch). I treat it separately from client state."

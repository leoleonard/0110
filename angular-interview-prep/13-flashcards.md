# 13 — Flashcards

> 264 cards, the same deck as the [flashcard app](flashcards/index.html). Topics marked **(weak area)** came out weakest in the mock interview, so do those first. Cover the answer, say yours out loud, then check.

## Versions

**Q: What is the current Angular version, and what did version 22 change by default?**

A: Angular 22, released in June 2026. Components without an explicit change detection setting are now OnPush by default, and the old Default strategy is deprecated and renamed Eager. Signal Forms became stable, and HttpClient uses the fetch backend by default.

**Q: What did Angular 21 change by default?**

A: New apps are zoneless by default, so zone.js is no longer included. Vitest replaced Karma as the default test runner. Signal Forms arrived as experimental.

**Q: What became stable in Angular 20?**

A: Zoneless change detection, effect, linkedSignal, toSignal, and incremental hydration. The structural directives ngIf, ngFor and ngSwitch were deprecated in favour of the built-in control flow blocks.

**Q: In Angular 22, how do you get upload progress with HttpClient?**

A: Fetch cannot report upload progress, so provide HttpClient with withXhr to use the XHR backend. withFetch is deprecated because fetch is already the default. reportProgress is deprecated in favour of reportUploadProgress and reportDownloadProgress.

**Q: What is the Service decorator in Angular 22?**

A: A new stable decorator that marks a class as a service and provides it in root automatically, like Injectable with providedIn root, but with clearer intent. You can opt out with autoProvided false, or pass a factory.

**Q: Is there an RxJS 8?**

A: No. RxJS 7.8 is current. Use RxJS 7 APIs such as firstValueFrom, lastValueFrom, and retry with a config object containing count and delay. toPromise is deprecated.

## Change detection (weak area)

**Q: When is an OnPush component checked?**

A: When an input reference changes, when an event fires in its template or a child's template, when an async pipe emits, when a signal read in its template changes, or when markForCheck is called. Otherwise Angular skips it and its whole subtree.

**Q: Why doesn't pushing to an array input update an OnPush child?**

A: OnPush compares inputs by reference. push mutates the same array, so the reference doesn't change and the child is never marked dirty. Fix it with an immutable update, such as spreading into a new array, or by using a signal.

**Q: What is the difference between markForCheck and detectChanges?**

A: markForCheck marks the component and all its ancestors dirty, so they are checked in the next scheduled cycle. It's the normal choice. detectChanges runs change detection synchronously on this view and its children right now. Use it in tests, in detached views, or when you need the DOM updated immediately.

**Q: When do you actually need markForCheck?**

A: When state changes through something Angular doesn't track for OnPush, such as a third-party library callback or a manual subscription that assigns a plain field. With signals you rarely need it, because a signal write marks its consumers dirty automatically.

**Q: With zone.js, an OnPush component assigns a field inside setTimeout. Why doesn't the view update?**

A: zone.js does run a tick after the timeout, but OnPush skips the component because nothing marked it dirty. A plain field assignment is not an input change or a template event. So it isn't late, it never updates. Fix it with a signal, the async pipe, or markForCheck.

**Q: What schedules change detection in a zoneless app?**

A: Writes to signals that templates read, markForCheck, template and host event listeners, the async pipe, and setting inputs through ComponentRef setInput. setTimeout, promises and plain field assignments schedule nothing.

**Q: Why did Angular move to zoneless?**

A: zone.js patches every async browser API and triggers an app-wide check after any async event, even irrelevant ones. Zoneless gives smaller bundles, better runtime performance, cleaner stack traces, and predictable updates driven by signals.

**Q: What causes ExpressionChangedAfterItHasBeenChecked, and what is the real fix?**

A: A value bound in the template changed during the same check, after Angular had already read it. A typical cause is a child setting parent state in ngAfterViewInit. It only appears in dev mode. The real fix is to restructure the data flow, for example by deriving the value with computed, not by wrapping it in setTimeout.

**Q: Why would a team use OnPush everywhere?**

A: The cost of change detection scales with what changed, not with the size of the app. It enforces immutable, one-way data flow and pairs naturally with signals and zoneless. Since version 22 it is the default anyway.

**Q: What is Eager change detection?**

A: The new name in version 22 for the old Default strategy, where a component is checked on every change detection cycle. It is the opt-out from the new OnPush default.

**Q: Explain how Angular change detection works, step by step.**

A: Angular keeps a tree of component views. In a change detection cycle it walks the tree from the root down. For each view it evaluates the template bindings, compares each value with the previous one, and updates only the DOM that changed. Data flows one way, from parent to child, once per cycle.

**Q: With zone.js, what triggers a change detection cycle?**

A: zone.js patches async browser APIs such as events, timers, promises and XHR. When an async task finishes and the zone has no more pending microtasks, Angular calls ApplicationRef tick, which checks the tree from the root.

**Q: Why does Angular check twice in development mode?**

A: After the normal pass, dev mode runs a second pass that only verifies nothing changed. If a binding returns a different value on the second pass, it throws ExpressionChangedAfterItHasBeenChecked. This enforces one-way data flow and doesn't run in production.

**Q: An Eager component sits inside an OnPush parent. When is the child checked?**

A: Only when the OnPush parent is checked, because Angular skips the parent's whole subtree when the parent isn't dirty. So an OnPush parent also shields its Eager children. A child can still be refreshed through its own signals or markForCheck.

**Q: How do signals make change detection more targeted?**

A: When a signal read in a template changes, Angular marks that specific view for refresh and flags its ancestors as having a child to refresh. OnPush ancestors are traversed but not re-checked, so only the component that read the signal is updated.

**Q: You call update on a signal holding an array, push an item, and return the same array. Why doesn't the view update?**

A: Signals compare the old and new value with Object.is. Returning the same array reference counts as no change, so nothing is notified. Return a new array, for example by spreading the old one and adding the item.

**Q: In a test you assign component.title equals something on an OnPush component and call detectChanges, but the DOM doesn't change. Why?**

A: Assigning the property directly doesn't mark an OnPush component dirty, the way a real input change from a parent would. Use fixture.componentRef.setInput, which marks it for check and works with signal inputs.

**Q: Does a click inside a deeply nested OnPush component cause its parents to be checked?**

A: Yes. A template event listener marks its own view and all its ancestors dirty, so the path from the root to that component is checked in the next cycle. That's why events work with OnPush without extra code.

**Q: How does the async pipe work with OnPush?**

A: It subscribes to the observable, stores the latest value, and calls markForCheck every time a new value arrives. It also unsubscribes automatically when the view is destroyed.

**Q: When would you use ChangeDetectorRef detach?**

A: When a component receives very frequent data, like a live chart or a ticker, and you want to render on your own schedule. Detach it from the tree, then call detectChanges when you choose, for example once per animation frame. Reattach to return to normal behaviour.

**Q: What is runOutsideAngular for?**

A: In zone.js apps, it runs code outside the Angular zone, so high-frequency events like mousemove, scroll or animation timers don't trigger an app-wide check on every event. Re-enter with run when you need to update the UI. In zoneless apps it's rarely needed.

**Q: Why are function calls in templates a performance problem?**

A: A method call in a binding runs on every change detection pass of that component, even when nothing changed. Use computed signals or pure pipes instead, which are memoized and only recalculate when their inputs change.

**Q: How do you find change detection performance problems?**

A: Use the Angular DevTools profiler. It records each change detection cycle, which components were checked, and how long each took. Look for components checked far more often than their data changes, and for expensive bindings.

**Q: What is hybrid change detection scheduling in zone.js apps?**

A: Since Angular 18, apps that still use zone.js also schedule change detection when a signal changes or markForCheck is called, even if that happens outside the Angular zone. It makes zone-based and zoneless behaviour more consistent.

**Q: How does Angular know an app is stable without zone.js, for example for SSR?**

A: Through PendingTasks. HttpClient and other Angular APIs register pending work, and the app is considered stable when no tasks are pending. You can add your own tasks for async work that SSR or tests must wait for.

**Q: What is the difference between ngAfterViewInit and afterNextRender?**

A: ngAfterViewInit runs after Angular has created the component's view, during change detection, and also runs on the server. afterNextRender runs once after the browser has rendered, only in the browser, which makes it the right place for DOM measurement and third-party DOM libraries.

**Q: What is your checklist for migrating an app to zoneless?**

A: Remove zone.js from the polyfills and use provideZonelessChangeDetection, the default since version 21. Make template state signals, or use the async pipe or markForCheck. Replace NgZone onStable and onMicrotaskEmpty logic. Move tests away from fakeAsync if they relied on zone.js. Then test areas that update from timers or third-party callbacks.

**Q: markForCheck or detectChanges: which do you reach for first, and why?**

A: markForCheck. It cooperates with Angular's scheduler and batches work into the next cycle. detectChanges forces a synchronous check right now, which can cause extra work and ordering bugs. I use detectChanges only in tests, detached views, or when I truly need the DOM updated immediately.

**Q: Give a one-minute explanation of OnPush, as you would in an interview.**

A: OnPush tells Angular to skip a component and its subtree unless it's marked dirty: an input reference changes, an event fires in its template, an async pipe emits, a signal it reads changes, or markForCheck is called. The classic bug is mutating an input array, because the reference doesn't change. It makes change detection cost scale with what changed, enforces one-way immutable data flow, and since version 22 it's the default.

**Q: What are the most common change detection mistakes?**

A: Mutating objects or arrays instead of replacing them. Assigning plain fields from timers or callbacks in OnPush or zoneless code. Calling detectChanges everywhere to force updates. Expensive function calls in templates. And fixing ExpressionChangedAfterItHasBeenChecked with setTimeout instead of fixing the data flow.

## Signals

**Q: What do signal, computed and effect each do?**

A: signal holds writable state. computed derives a read-only value lazily and memoizes it, recomputing only when its dependencies change. effect runs side effects when the signals it reads change.

**Q: When should you NOT use effect?**

A: Don't use effect to copy one signal into another. Use computed or linkedSignal for that. Effects are for syncing with the outside world: logging, local storage, analytics, or a third-party DOM library.

**Q: What is linkedSignal?**

A: A writable signal that resets from a source computation whenever the source changes, but which the user can still override. The classic example is a selected option that resets to the first item when the list of options changes.

**Q: What are resource, rxResource and httpResource?**

A: resource takes params and an async loader, and exposes value, status, error and isLoading as signals. It cancels and reloads when the params change. rxResource does the same with an Observable stream instead of a promise. httpResource wraps HttpClient: you pass a function that returns the URL, and it refetches reactively.

**Q: Signals or RxJS: which do you use for what?**

A: Signals for synchronous state and derived values that the template reads. RxJS for events over time: debouncing, cancellation, combining streams, retries, websockets. Bridge them with toSignal and toObservable.

**Q: What are the pitfalls of toSignal?**

A: It subscribes immediately and needs an injection context, so call it in a field initializer or the constructor. Give it an initialValue, or use requireSync for sources that emit synchronously. Otherwise the signal starts as undefined.

**Q: Explain input, input.required, model and output.**

A: input creates a read-only signal input, and input.required makes it mandatory. model is a two-way, writable input. output replaces EventEmitter. Read inputs in computed or effects, not in the constructor, because they are not set yet.

**Q: Why are signals called glitch-free?**

A: computed values are pulled lazily and recomputed only when read after a dependency changed, so you never observe an inconsistent intermediate state. Equality checks also stop propagation when a value hasn't actually changed.

## Dependency injection (weak area)

**Q: How does Angular resolve a dependency?**

A: It walks up the tree. First the element injectors: the component's own providers, then its parents'. Then the environment injectors: the lazy route's injector, then root, then platform, and finally the null injector, which throws. The first match wins.

**Q: A service is providedIn root and also listed in a lazy route's providers. What happens?**

A: You get two instances. The lazy route creates its own environment injector, so components under that route get a fresh instance, while the rest of the app uses root's. State appears to be lost. Remove it from the route providers.

**Q: When should you use route-level providers?**

A: For state that should be scoped to a feature and reset when you leave it, such as a checkout wizard's state. Not for app-wide singletons.

**Q: What is the difference between providers and viewProviders?**

A: providers are visible to the component's view and to content projected into it. viewProviders are visible only to the component's own view, not to projected content. In a component library this keeps internals private.

**Q: What do the resolution modifiers optional, self, skipSelf and host do?**

A: optional returns null instead of throwing. self looks only in the current injector. skipSelf starts looking from the parent. host stops at the host component. You pass them as options to inject.

**Q: Why prefer the inject function over constructor injection?**

A: inject works in field initializers and any injection context. It's well typed, works with inheritance without passing arguments to super, and enables functional guards, interceptors and reusable helper functions. It's the modern default.

**Q: Why use InjectionToken and multi providers?**

A: InjectionToken lets you inject values or abstractions that aren't classes, such as configuration or a strategy interface. multi true collects several providers into an array, which is how you build plugin or strategy registries.

**Q: How do you get a cleanup hook without implementing ngOnDestroy?**

A: Inject DestroyRef and call onDestroy with a callback. takeUntilDestroyed uses the same mechanism for RxJS. It also works in services and helper functions, not just components.

## Routing & templates

**Q: What is the difference between canMatch and canActivate?**

A: canMatch runs during route matching. If it returns false, the router tries other routes, and a lazy chunk is never downloaded. canActivate runs after the route matched, so the code may already be loaded. Use canMatch for feature flags and role-based route variants.

**Q: What are functional guards and resolvers?**

A: Plain functions typed as CanActivateFn, CanMatchFn or ResolveFn that use inject inside. They return a boolean, a UrlTree or RedirectCommand to redirect, or an Observable or Promise of those.

**Q: Why is track mandatory in a for block?**

A: It tells Angular how to identify items so it can reuse DOM nodes when the list changes. Track by a stable id. Tracking by object identity on refetched data recreates the DOM, loses focus and component state, and hurts performance.

**Q: What does a defer block do?**

A: It lazy-loads a region of the template and its dependencies as a separate chunk. Triggers include on viewport, idle, interaction, hover, timer, or a when condition, with optional prefetch, plus placeholder, loading and error blocks. With SSR, hydrate triggers enable incremental hydration.

**Q: What does withComponentInputBinding do?**

A: It binds route params, query params and resolved data directly to component inputs with the same name, so components don't need to inject ActivatedRoute.

**Q: What are preloading strategies?**

A: PreloadAllModules downloads all lazy routes once the app is idle. A custom strategy can preload only flagged or likely routes. A defer block with prefetch on idle gives similar control at the template level.

## Forms

**Q: Compare template-driven forms, reactive forms and Signal Forms.**

A: Template-driven forms are simple and defined in the template. Reactive forms are explicit, typed and testable, with the model in the class. Signal Forms, stable in version 22, build a field tree from a model signal and a schema of validation rules, and bind to inputs with the formField directive.

**Q: What does a ControlValueAccessor need?**

A: writeValue to receive the model value, registerOnChange and registerOnTouched to report changes back, and optionally setDisabledState. You register it with the NG_VALUE_ACCESSOR token, using forwardRef and multi true.

**Q: How do you build a custom control for Signal Forms?**

A: No ControlValueAccessor needed. The component implements FormValueControl with a value model signal. It can optionally declare inputs such as disabled, touched or errors, and a touch output. You bind it with the formField directive.

**Q: What are typed forms and nonNullable controls?**

A: Since Angular 14, reactive forms are typed. nonNullable controls reset to their initial value instead of null, which removes null checks everywhere. Use the NonNullableFormBuilder.

**Q: What are the pitfalls of async validators?**

A: Debounce them, cancel stale requests, and remember the control is pending while one runs. In Signal Forms, validateAsync and validateHttp have a debounce option.

## HTTP, SSR & testing

**Q: How does a functional HTTP interceptor work?**

A: An HttpInterceptorFn receives the request and next, and returns next called with a cloned request. Register it with provideHttpClient and withInterceptors. Requests are immutable, so you clone them to add headers.

**Q: How do you handle a 401 with refresh tokens?**

A: In an interceptor, on a 401 start exactly one refresh call, queue the other failing requests behind it, then retry them with the new token. If the refresh fails, log the user out. Never fire one refresh per failing request.

**Q: What is HttpContextToken for?**

A: A typed, per-request flag that interceptors can read, for example to skip authentication or disable retries for one call, without abusing headers.

**Q: What is hydration, and what breaks it?**

A: The client reuses the server-rendered DOM instead of rendering it again. Mismatches come from invalid HTML nesting, direct DOM manipulation, and browser-only APIs or random or time-based values that differ between server and client.

**Q: What are incremental hydration and event replay?**

A: Incremental hydration, on by default in version 22, keeps deferred parts dehydrated until a trigger such as viewport or interaction. Event replay records clicks made before hydration finishes and replays them afterwards.

**Q: What does Angular use for testing now?**

A: Vitest, the default since version 21. Karma is legacy. Prefer testing through the DOM the way a user would, with Testing Library or component harnesses, and use HttpTestingController for HTTP.

**Q: What are the top Angular performance levers?**

A: OnPush and signals, track in for blocks, lazy routes and defer blocks, NgOptimizedImage with priority for the LCP image, SSR with hydration, virtual scrolling for long lists, no heavy function calls in templates, and bundle budgets in CI.

**Q: How do you find a performance problem?**

A: Measure first: field data for Core Web Vitals, then the Chrome DevTools performance panel and the Angular DevTools profiler to see which components are checked and for how long. Fix the biggest cost, then add a budget so it can't regress.

## RxJS (weak area)

**Q: What does switchMap do, and when is it wrong?**

A: It cancels the previous inner observable when a new value arrives. Use it for typeahead and loading data from route params. It's wrong for saves: it cancels in the browser, but the server may already have processed the request, so writes get lost or duplicated.

**Q: What does mergeMap do, and when is it wrong?**

A: It runs inner observables in parallel. Use it for independent bulk work like parallel uploads, ideally with a concurrency limit as the second argument. It's wrong for search: race conditions let an old response overwrite a newer one.

**Q: What does concatMap do, and when is it wrong?**

A: It queues inner observables and runs them one at a time, in order. Use it for ordered writes or autosave. It's wrong for search: requests pile up and the UI lags. If an inner observable never completes, the queue blocks.

**Q: What does exhaustMap do, and when is it wrong?**

A: It ignores new values while the current inner observable is running. Use it for submit buttons, login and token refresh. It's wrong for filters: the user's latest choice is silently dropped.

**Q: What is the rule of thumb for flattening operators?**

A: Reads use switchMap. Writes use concatMap or exhaustMap. Independent bulk work uses mergeMap with a concurrency limit.

**Q: A user double-clicks Save, and the code uses switchMap. What happens?**

A: The first request is aborted in the browser, but the server probably processed both, so you may create two orders while the UI shows one. Use exhaustMap, disable the button while saving, and ask the backend for an idempotency key.

**Q: Where should catchError go?**

A: Inside the inner observable, inside the switchMap. At the outer level, an error completes the whole stream, so a typeahead stops working after the first failed request.

**Q: Compare forkJoin, combineLatest, zip and withLatestFrom.**

A: forkJoin emits once, when all sources complete, and never if one is infinite. combineLatest emits on every change once each source has emitted at least once. zip pairs values by index. withLatestFrom samples another stream only when the main stream emits.

**Q: What is the difference between hot and cold observables?**

A: A cold observable starts a new producer for each subscriber, like an HTTP call. A hot observable shares one producer that runs regardless, like DOM events or a Subject. share and shareReplay turn cold into hot.

**Q: What is the shareReplay pitfall?**

A: Without refCount true, shareReplay keeps the source subscription alive forever, even when nobody listens, which leaks for long-lived sources. Use shareReplay with bufferSize 1 and refCount true.

**Q: Explain Subject, BehaviorSubject, ReplaySubject and AsyncSubject.**

A: Subject has no current value and no replay. BehaviorSubject needs an initial value and replays the latest one to new subscribers. ReplaySubject replays the last n values. AsyncSubject emits only the last value, on completion.

**Q: What are the best unsubscription patterns?**

A: Prefer not subscribing at all: use the async pipe or toSignal. Otherwise use takeUntilDestroyed, which needs an injection context or a DestroyRef. Never nest subscribes; compose with operators instead.

**Q: How do you retry failed HTTP calls properly?**

A: Use retry with a count and a delay function for exponential backoff with jitter. Retry only network errors and 502, 503, 504 or 429, and only for idempotent requests. Never retry 4xx validation errors.

**Q: Why might distinctUntilChanged not stop duplicate emissions?**

A: By default it compares with triple equals, so new objects with the same content always count as different. Pass a comparator, or use distinctUntilKeyChanged for one property.

**Q: Why does combineLatest sometimes never emit?**

A: It waits until every source has emitted at least once. If one source hasn't emitted yet, nothing comes out. Add startWith to sources that may start empty.

## Event loop (weak area)

**Q: What is the event loop rule?**

A: Run one macrotask, and the script itself is the first one. Then drain all microtasks. Then maybe render. Then repeat. Microtasks are promise callbacks, code after await, and queueMicrotask. Macrotasks are setTimeout, events and I/O.

**Q: Does an async function run asynchronously from the start?**

A: No. Its body runs synchronously until the first await. Only the code after the await is queued as a microtask.

**Q: When exactly does the code after an await run?**

A: It's queued as a microtask at the moment the awaited promise settles. If the value is already resolved, that's immediately. If a timer resolves it, the code waits until that timer has fired.

**Q: Why does setTimeout with zero milliseconds run after promise callbacks?**

A: setTimeout is a macrotask, and the event loop always empties the microtask queue before taking the next macrotask. Zero milliseconds means as soon as possible, not immediately.

**Q: Puzzle: log 1, setTimeout logs 2, a resolved promise's then logs 3, an async function logs 4 then awaits null then logs 5, then log 6. What is the order?**

A: 1, 4, 6, 3, 5, 2. The async body up to the await runs synchronously, so 4 comes early. Then microtasks run first in, first out: 3, then 5. The timer runs last: 2.

**Q: Same puzzle, but the async function awaits a promise resolved by setTimeout. What is the order now?**

A: 1, 4, 6, 3, 2, 5. Nothing is queued for 5 until the second timer fires and resolves the promise. That timer was registered after the first one, so 2 prints before 5.

**Q: Why does event loop timing matter in Angular tests?**

A: Code after an await runs as a microtask, so a synchronous expect can run too early. Await fixture whenStable for microtasks. For timers like debounceTime, advance fake timers, for example with Vitest's advanceTimersByTime, or use fakeAsync with tick if you use zone testing.

## JavaScript

**Q: What is a closure?**

A: A function remembers the variables of the scope where it was created, even after that scope has returned. It's used for private state, factories, memoization and debounce.

**Q: Explain var, let and const.**

A: var is function-scoped and hoisted as undefined. let and const are block-scoped and sit in the temporal dead zone until declared. const prevents reassignment, not mutation.

**Q: What are the this binding rules?**

A: this depends on how a function is called. In priority order: new, then explicit call, apply or bind, then a method call on an object, then the default, which is undefined in strict mode. Arrow functions take this from the surrounding scope.

**Q: Why do you lose this when passing a method as a callback?**

A: Passing this dot method detaches the function from its object, so it's called with the default binding. Use an arrow function or bind. That's why a debounce uses a regular outer function and an arrow function inside the timeout.

**Q: What is the difference between a shallow and a deep copy?**

A: Spread and Object.assign copy only the top level. JSON stringify then parse loses dates, undefined, Map and Set, and fails on circular references. structuredClone handles cycles, dates, Map and Set, but not functions, DOM nodes or class prototypes.

**Q: What is the difference between triple equals and Object.is?**

A: Triple equals compares without type coercion. Object.is is the same, except it treats NaN as equal to NaN and distinguishes plus zero from minus zero.

**Q: What is the difference between debounce and throttle?**

A: Debounce runs only after a quiet period since the last call, for example search input or autosave. Throttle runs at most once per interval, for example scroll and resize handlers.

**Q: Which features came in ES2017, also called ES8?**

A: async and await, Object.values and Object.entries, padStart and padEnd, Object.getOwnPropertyDescriptors, and trailing commas in function parameters. Object spread came later, in ES2018.

**Q: Why doesn't await inside forEach work as expected?**

A: forEach ignores the promises its callback returns, so nothing waits. Use a for of loop to run in sequence, or Promise.all with map to run in parallel.

**Q: Compare Promise.all, allSettled, race and any.**

A: all rejects on the first rejection. allSettled waits for all and reports each result. race settles with whichever settles first. any resolves with the first fulfilment and rejects only if all of them reject.

**Q: What is the prototype chain?**

A: Objects delegate property lookups to their prototype, then its prototype, and so on. Class syntax is sugar over constructor functions and prototypes.

**Q: Map or a plain object, and what is WeakMap for?**

A: Map keeps insertion order, accepts any key type and has a size property, so it's better for dynamic dictionaries. WeakMap holds its keys weakly, so entries disappear when the key object is garbage collected, which is ideal for caching data per object without memory leaks.

**Q: What are generators and iterators?**

A: An iterator is an object with a next method that returns value and done. A generator function, written with an asterisk, produces an iterator and pauses at each yield. They power for of loops, lazy sequences and spreading.

**Q: What are the main memory leak sources in a frontend app?**

A: Subscriptions and event listeners that are never removed, timers and intervals that keep running, detached DOM nodes still referenced from JavaScript, and caches that grow forever. Find them with heap snapshots in Chrome DevTools.

## CSS & rendering

**Q: Why can an element with z-index 9999 still appear underneath another element?**

A: z-index only competes within the same stacking context. If an ancestor created a context that ranks below the other element, the child's 9999 is trapped inside it.

**Q: What creates a stacking context?**

A: position with a z-index, position fixed or sticky, opacity below one, transform, filter, will-change, contain paint, isolation isolate, and flex or grid children with a z-index.

**Q: How should a component library handle dropdown and modal layering?**

A: Render overlays outside the component tree, with the CDK Overlay or the browser's top layer using the popover attribute or a dialog element. That also escapes overflow hidden clipping. Use z-index tokens instead of raw numbers, enforced by lint.

**Q: What are the steps of the rendering pipeline?**

A: HTML builds the DOM and CSS builds the CSSOM. Together they form the render tree. Layout computes geometry, paint fills in pixels, and composite assembles the layers on the GPU.

**Q: What is the difference between reflow and repaint?**

A: Reflow, or layout, recalculates geometry and is expensive. It's triggered by changes to size, position or content. Repaint redraws pixels without changing geometry, like a color change. Animating transform and opacity can skip both and only composite.

**Q: What is layout thrashing?**

A: Alternating DOM reads, like offsetHeight, with writes forces the browser to recalculate layout again and again. Batch all reads, then all writes, or use requestAnimationFrame or the read and write phases of afterNextRender.

**Q: When should you use will-change?**

A: Sparingly and temporarily, just before an animation, to promote an element to its own layer. Overusing it wastes memory and creates stacking contexts.

**Q: What are the Core Web Vitals and their thresholds?**

A: LCP, largest contentful paint, is good at 2.5 seconds or less. INP, interaction to next paint, is good at 200 milliseconds or less, and it replaced FID in March 2024. CLS, cumulative layout shift, is good at 0.1 or less.

**Q: Explain specificity, the where and is selectors, and cascade layers.**

A: Specificity counts ids, then classes, attributes and pseudo-classes, then elements. where adds zero specificity, and is takes its most specific argument. Cascade layers let a library put its styles in a lower layer so consumers can override them without important.

**Q: When do you use flexbox, and when grid?**

A: Flexbox is one-dimensional and content-driven, good for rows of items. Grid is two-dimensional and layout-driven, good for page and card layouts. Subgrid aligns nested content to the parent grid.

**Q: What is the difference between Sass use and Sass import?**

A: use loads a module once, with a namespace and private members, and forward re-exports it. import is deprecated and will be removed in Dart Sass 3, because it puts everything into the global scope.

**Q: How should you theme a component library?**

A: Expose CSS custom properties as the public styling API, keep the default emulated encapsulation, avoid ng-deep, which is deprecated, and drive everything from design tokens.

**Q: Compare display none, visibility hidden and opacity zero.**

A: display none removes the element from layout and from the accessibility tree. visibility hidden keeps its space but hides it from screen readers. opacity zero keeps it visible to screen readers and still clickable.

**Q: What is the first rule of ARIA?**

A: Don't use ARIA if a native element does the job. A button element gives you focus, keyboard support and a role for free. A div with a click handler gives you none of that.

**Q: How do you make route changes accessible in a single-page app?**

A: Move focus to the new page's main heading or container and update the document title, so screen reader users know the page changed. Announce async updates with an aria-live region.

## State management (weak area)

**Q: What are the principles of Redux?**

A: A single source of truth. State is read-only and changes only by dispatching actions. Changes are made by pure reducer functions. Data flows one way.

**Q: Why should actions be events rather than commands?**

A: Name actions after what happened and where, like Product Page Opened, not commands like load products. That keeps actions reusable and the action log readable. Use createActionGroup.

**Q: How does selector memoization work, and how can you break it?**

A: createSelector recomputes only when its input selectors return new references. A projector that builds a new array on every call defeats memoization, and with it the benefit of OnPush.

**Q: What does normalizing state mean?**

A: Store entities in a dictionary keyed by id plus an array of ids, as the entity adapter does, instead of nested arrays. Updates become simple and there is one copy of each entity. Denormalize in selectors.

**Q: What are the common pitfalls of NgRx effects?**

A: Pick the flattening operator on purpose, and catch errors inside the inner pipe, otherwise the effect dies. By default NgRx resubscribes a failing effect up to ten times, which can hide the bug.

**Q: What is NgRx SignalStore?**

A: NgRx's signal-based store, from the ngrx signals package. You compose it with withState, withComputed, withMethods, withHooks and withProps, update it with patchState, use rxMethod for RxJS side effects, and withEntities for collections. It is still NgRx.

**Q: When is the classic NgRx Store the right choice?**

A: When there is a lot of cross-feature shared state, complex async orchestration, a need for an auditable event log or Redux DevTools, or several teams that benefit from one enforced pattern.

**Q: When should you NOT use the classic NgRx Store?**

A: When most of the state is server cache, when state is local or feature-scoped, or for a small app. Use component signals for local state, SignalStore or a signals service for shared client state, and httpResource or a query layer for server data.

**Q: How would you decide on state management for a new app?**

A: Classify state by owner and lifetime: local UI state, shared client state, server cache, and cross-cutting audited flows. Write an ADR with the criteria, spike one real feature both ways, and agree on a rule the team can apply.

## REST & HTTP (weak area)

**Q: What is the difference between safe and idempotent HTTP methods?**

A: Safe methods don't change state: GET, HEAD and OPTIONS. Idempotent means repeating the request has the same effect as sending it once: the safe methods plus PUT and DELETE. POST is not idempotent, and PATCH is not guaranteed to be.

**Q: What is an idempotency key?**

A: The client generates a unique key for each user action and sends it in an Idempotency-Key header. The server stores it and returns the original result for repeats, so retries and double clicks don't create duplicates.

**Q: What is the difference between 401 and 403?**

A: 401 means not authenticated: refresh the token or send the user to log in. 403 means authenticated but not allowed: show a permission message and don't retry.

**Q: How should the frontend handle 409, 412, 422, 429 and 503?**

A: 409 is a conflict, often a version clash. 412 is a failed precondition, like an ETag mismatch. 422 means validation errors, which you map onto form fields. 429 means too many requests: back off and respect Retry-After. 502, 503 and 504 can be retried, but only for idempotent requests.

**Q: What is CORS, and who fixes a CORS error?**

A: The browser enforces it, and the server fixes it by sending the Access-Control headers. Requests that aren't simple trigger a preflight OPTIONS request. In development you can use the Angular dev server proxy.

**Q: Where should you store auth tokens in an SPA?**

A: localStorage can be read by any XSS attack. Safer options are keeping tokens in memory, or a backend-for-frontend with httpOnly, Secure, SameSite cookies plus CSRF protection. Use the Authorization Code flow with PKCE; the implicit flow is deprecated.

**Q: How should caching headers be set for an Angular deployment?**

A: Hashed bundle files get a one-year max-age with immutable. index.html gets no-cache, so users pick up new bundle names. An ETag with If-None-Match lets the server answer 304 Not Modified.

**Q: Compare offset and cursor pagination.**

A: Offset is simple and lets you jump to any page, but it drifts and shows duplicates when data changes, and it's slow at large offsets. Cursor pagination is stable and scales, but you can't jump straight to page 50.

**Q: How do you use OpenAPI and Postman as a frontend developer?**

A: OpenAPI is the contract: generate a typed Angular client from it and detect breaking changes in CI. Postman collections with environments and tests document and verify the API, run in CI with Newman, and mock servers unblock you when a third party isn't ready.

## Git & CI

**Q: What is the difference between rebase and merge?**

A: Rebase replays your commits onto a new base for a linear history, so never rebase a shared branch. Merge keeps the true history with a merge commit. If you must force-push your own branch, use force-with-lease.

**Q: What is the trade-off of squash merging?**

A: One commit per pull request gives a clean history and easy reverts, but you lose the individual commits for bisecting and review.

**Q: How do you recover a lost commit?**

A: git reflog shows everywhere HEAD has been. Find the commit, then reset to it or create a branch from it.

**Q: What is the difference between revert and reset?**

A: Revert creates a new commit that undoes a change, so it's safe on shared branches. Reset moves the branch pointer and rewrites history, so use it only for local work.

**Q: Compare trunk-based development and GitFlow.**

A: Trunk-based development uses short-lived branches merged daily, with feature flags, which gives fast feedback, and it's what DORA research favours. GitFlow has long-lived develop and release branches and suits versioned releases.

**Q: When do you use cherry-pick?**

A: To apply a specific commit onto another branch, typically to backport a hotfix. Use the x flag to record the source commit in the message.

**Q: What does a good CI pipeline for an Angular app look like?**

A: npm ci with caching, lint, unit tests, a production build with budgets, end-to-end tests on critical journeys, a preview deployment, then production. Add protected branches and CODEOWNERS.

## Agile

**Q: What are Scrum's accountabilities, events and artifacts?**

A: Three accountabilities: Product Owner, Scrum Master and Developers. Five events: the Sprint, Sprint Planning, the Daily Scrum, Sprint Review and the Retrospective. Three artifacts, each with a commitment: the Product Backlog with the Product Goal, the Sprint Backlog with the Sprint Goal, and the Increment with the Definition of Done.

**Q: Why use WIP limits in Kanban?**

A: Limiting work in progress per column exposes bottlenecks and improves flow. Track cycle time, throughput and a cumulative flow diagram. Little's Law: lead time equals work in progress divided by throughput.

**Q: How is velocity misused?**

A: Velocity is for a team's own forecasting. Comparing teams by velocity or using it as a productivity target makes people inflate estimates.

**Q: What is the difference between the Definition of Done and acceptance criteria?**

A: Acceptance criteria are specific to one story. The Definition of Done applies to every item: tests, accessibility, code review, documentation, and deployed to staging.

**Q: When does Waterfall make sense?**

A: Fixed scope and contracts, regulated environments, and hardware or third-party dependencies with fixed integration dates.

**Q: How do you handle requirements changing mid-sprint?**

A: Talk to the Product Owner and make the trade-off visible: what comes out if this goes in. Protect the sprint goal, slice the work vertically, and use feature flags.

## Patterns & quality

**Q: How does SOLID apply in Angular?**

A: Single responsibility: thin components, logic in services. Open-closed: extend through DI tokens and strategies. Liskov: abstract-class providers that can be swapped. Interface segregation: small input APIs. Dependency inversion: depend on tokens or abstractions, not on concrete HTTP services.

**Q: What is the difference between smart and presentational components?**

A: Smart, or container, components inject services or stores and handle data. Presentational components only use inputs and outputs, use OnPush, are easy to test, and are reusable in a library.

**Q: When is a facade worth it?**

A: A facade hides a store or several services behind an intent-based API. It's worth it at feature boundaries. A facade over every service is just extra indirection.

**Q: What is the adapter pattern used for in a frontend?**

A: Mapping API DTOs to domain models at the edge of the app, so backend changes don't ripple through your components.

**Q: How do you implement the strategy pattern with DI?**

A: Register implementations with an InjectionToken, using multi providers or a map, and choose one at runtime. Examples are export formats or payment providers.

**Q: Why avoid inheritance for component reuse?**

A: BaseComponent hierarchies couple everything together and fight dependency injection. Prefer composition: services, directives, hostDirectives, and helper functions that use inject.

**Q: What does a healthy testing strategy look like?**

A: Mostly integration-style component tests through the DOM, unit tests for pure logic, a few end-to-end tests for critical journeys, and visual regression tests for a component library. Treat coverage as a signal, not a target.

**Q: How do you manage tech debt?**

A: Make it visible in tickets or ADRs, quantify its cost in time or incidents, tie it to business outcomes, and pay it down continuously with a steady share of capacity, instead of waiting for a hardening sprint.

## Answer technique (weak area)

**Q: How should you structure a technical answer at senior level?**

A: What, why, so what, fix, prevent. State the mechanism, explain why it happens, describe the consequence for users, give the fix, then a systemic prevention.

**Q: How do you handle a multi-part question?**

A: Count the parts out loud before answering, for example: there are three things here. Then answer each one in turn.

**Q: What does prevention mean in an answer?**

A: Prevention is not a stronger version of the quick fix. It's a system that stops the bug coming back: tooling, design tokens, lint rules, CI checks, ADRs or architecture changes.

**Q: What is the STAR plus L format?**

A: Situation in one or two sentences. Task: your responsibility. Action: most of the time, saying I, not we. Result: with a number. Learning: what you would do differently.

**Q: What is the playbook for influencing without authority?**

A: Evidence first. Understand why people do what they do. Prove it small on a real screen. Write an ADR. Make the right way the easy way with tooling. Negotiate an incremental rollout. Measure the outcome.

**Q: What is the routine for live coding?**

A: Clarify the requirements, write a simple working version, then trace one call out loud before saying you're done. Mention edge cases and how you'd test it.

## TypeScript

**Q: What is the difference between any, unknown and never?**

A: any switches off type checking. unknown accepts any value but forces you to narrow it before use, so it's the safe choice for untrusted input like API responses. never is the type of a value that can't exist, used for exhaustive checks and functions that always throw.

**Q: When do you use type, and when interface?**

A: Both describe object shapes. Interfaces can be extended and merged by declaration, which suits public library APIs. Type aliases also handle unions, mapped and conditional types. Pick one convention for object shapes and use type where you need its extra power.

**Q: Which built-in utility types do you use most?**

A: Partial, Required and Readonly change optionality and mutability. Pick and Omit select properties. Record builds a dictionary type. ReturnType, Parameters, Awaited and NonNullable extract types from functions, promises and nullable values.

**Q: How does type narrowing work?**

A: TypeScript narrows a union inside a branch based on checks: typeof, instanceof, the in operator, equality checks, and discriminated unions with a shared literal field like kind. A custom type predicate, a function returning value is Foo, lets you write your own checks.

**Q: How do you make a switch over a union exhaustive?**

A: In the default branch, assign the value to a variable of type never. If someone adds a new member to the union and forgets a case, the compiler reports an error there.

**Q: Enums or string literal unions?**

A: Prefer unions of string literals, or a const object with as const. They cost nothing at runtime and work well with narrowing. Enums emit runtime code and have quirks, especially numeric enums, which accept any number.

**Q: What does the satisfies operator do?**

A: It checks that a value matches a type without widening the value's inferred type. You get validation against the type and still keep precise literal types, which is useful for configuration objects and route maps.

**Q: What are generics with constraints?**

A: Generics let a function or class work with many types while keeping them linked, like a table of T that emits a T on row click. A constraint, T extends something, says what T must have, for example an id property.

**Q: What is structural typing, and what are branded types?**

A: TypeScript compares types by shape, not by name, so two interfaces with the same fields are interchangeable. A branded type adds a fake marker property, so you can't accidentally pass a CustomerId where an OrderId is expected.

**Q: What do strict mode and strictTemplates give you?**

A: strict enables strictNullChecks, noImplicitAny and related checks in TypeScript code. strictTemplates applies full type checking to Angular templates, including input types and nullability, so template bugs fail the build instead of production.

## Components & templates

**Q: What is the order of the lifecycle hooks?**

A: Constructor, then ngOnChanges if there are inputs, ngOnInit, ngDoCheck, ngAfterContentInit, ngAfterContentChecked, ngAfterViewInit, ngAfterViewChecked, and finally ngOnDestroy. For DOM work after rendering, use afterNextRender or afterEveryRender, which only run in the browser.

**Q: What replaces ngOnChanges when you use signal inputs?**

A: Derived values become computed signals, and reactions to input changes become effects or resources whose params read the input. ngOnChanges still works but is rarely needed.

**Q: How does content projection work?**

A: ng-content projects the parent's content into the component, and the select attribute creates named slots. Projected content is created by the parent, so it's instantiated even if the ng-content sits inside a false if block. For conditional or repeated projection, accept an ng-template and render it with ngTemplateOutlet.

**Q: What is the difference between view queries and content queries?**

A: viewChild and viewChildren find elements and components in the component's own template. contentChild and contentChildren find things projected into it by a parent. The signal-based versions return signals, so you read them in computed or effects instead of waiting for a lifecycle hook.

**Q: What is the difference between attribute and structural directives?**

A: Attribute directives change the look or behaviour of an existing element, like a tooltip or autofocus directive. Structural directives add or remove DOM by working with a template, though most of that is now done with the built-in control flow blocks.

**Q: What are hostDirectives?**

A: A way to compose directives onto a component or directive declaratively, and choose which inputs and outputs to expose. It's composition instead of inheritance, ideal for reusing behaviours like focus handling or tooltips in a component library.

**Q: How should you bind to the host element?**

A: Use the host property in the component or directive metadata for classes, attributes and event listeners. It's the recommended style over the HostBinding and HostListener decorators, and since version 21 host bindings are type checked by default.

**Q: What is the difference between pure and impure pipes?**

A: A pure pipe re-runs only when its input reference changes, so it works as cheap memoization. An impure pipe runs on every change detection cycle, which can be expensive. Prefer pure pipes or computed signals over calling methods in templates.

**Q: How do you create components dynamically?**

A: Call createComponent on a ViewContainerRef with the component class, then set inputs with setInput. Or use NgComponentOutlet in the template. Component factories and ComponentFactoryResolver were removed in version 22.

**Q: What are the view encapsulation options?**

A: Emulated, the default, scopes styles with generated attributes. ShadowDom uses the browser's native shadow DOM. None makes styles global. A component library usually keeps Emulated and exposes CSS custom properties for theming.

**Q: What are the ways components can communicate?**

A: Inputs and outputs for parent and child, model for two-way binding, a shared service or store with signals for siblings and distant components, and the router for state that belongs in the URL. Avoid reaching into children with viewChild to call their methods.

**Q: What is the let block in templates for?**

A: It declares a read-only local variable in the template, for example to read a signal or an async pipe once and reuse the result, instead of repeating the expression.

## Security

**Q: How does Angular protect against XSS?**

A: It treats all values as untrusted and sanitizes them by context, HTML, style, URL and resource URL, when you bind them. Interpolation is always escaped, and binding to innerHTML is sanitized. Template code itself is trusted, so never build templates from user input.

**Q: When is DomSanitizer bypassSecurityTrust dangerous?**

A: Always potentially. It switches off sanitization for that value. Only use it for content you fully control, like a constant SVG, never for anything that came from a user or an API. Writing to nativeElement innerHTML directly also bypasses Angular's protection.

**Q: How does Angular help with CSRF?**

A: HttpClient reads a token from the XSRF-TOKEN cookie and sends it in the X-XSRF-TOKEN header on mutating requests to relative URLs. The server must validate it. You can configure the names with withXsrfConfiguration. SameSite cookies add another layer.

**Q: What is a Content Security Policy, and how does it work with Angular?**

A: A response header that restricts where scripts, styles and other resources can load from, which limits the damage of XSS. Avoid inline scripts. Angular supports a nonce for its inline styles through the CSP_NONCE token or the ngCspNonce attribute.

**Q: Can you keep secrets in an Angular app?**

A: No. Everything shipped to the browser, including environment files, is public. API keys that must stay secret belong on a backend or a backend-for-frontend.

**Q: How do you manage dependency and supply-chain risk?**

A: Commit the lockfile and use npm ci in CI, run npm audit or a scanner, keep dependencies updated with Renovate or Dependabot, and review new packages before adding them.

**Q: What are Trusted Types?**

A: A browser feature that blocks passing plain strings to dangerous DOM sinks like innerHTML, unless they come from an approved policy. Angular supports Trusted Types, which makes XSS much harder.

## Component library

**Q: How do you version a shared component library?**

A: Semantic versioning: major for breaking changes, minor for new features, patch for fixes. Automate releases and changelogs with conventional commits or changesets, so consumers know exactly what each upgrade means.

**Q: How do you handle breaking changes and deprecations?**

A: Mark the old API as deprecated with a clear replacement, keep it for at least one major version, and ship an ng update migration schematic so consumers upgrade automatically. Announce it in the changelog and track remaining usage across apps.

**Q: What are secondary entry points, and why use them?**

A: Separate import paths in one package, like library slash button, built with ng-packagr. Consumers import only what they use, builds are faster, and boundaries between parts of the library are explicit.

**Q: What makes a good component API?**

A: A small, typed set of inputs with sensible defaults, composition through content projection and templates instead of dozens of flags, accessibility built in, and theming through CSS custom properties. Keep internals private behind the public API file.

**Q: How do you theme a component library?**

A: Define design tokens, such as color, spacing and typography, ideally generated from the design tool, and expose them as CSS custom properties. Components read the tokens, and apps override them per theme or brand without touching component code.

**Q: How do you document and test a component library?**

A: Storybook stories as living documentation, unit and interaction tests per component, component harnesses shipped for consumers' tests, visual regression tests for every story, and automated accessibility checks in CI.

**Q: How do you build accessibility into a library?**

A: Use native elements where possible, follow the ARIA authoring practices for widgets, and use the CDK a11y tools such as FocusTrap, LiveAnnouncer and the key managers for keyboard navigation. The Angular ARIA package provides headless accessible primitives. Test with axe, the keyboard and a screen reader.

**Q: How do you detect accidental breaking changes in a library's public API?**

A: Keep golden API report files, generated by a tool like API Extractor, and fail CI when the public surface changes without an intentional update. Add visual regression tests to catch breaking style changes.

**Q: How should a library declare its Angular dependency?**

A: As a peer dependency with a supported version range, so the app controls the single Angular version. Test against every major you claim to support.

**Q: How do you measure whether a design system is succeeding?**

A: Adoption across apps, the number of forked or duplicated components, time to build a new screen, accessibility issues found, design-to-development defects, and how long upgrades take.

## Architecture

**Q: How do you structure a large Angular codebase?**

A: By feature or domain, not by file type. Each feature has its routes, components, state and API layer, plus a small public API. Shared UI and utilities live in separate libraries, and lint rules enforce which layers may import which.

**Q: What does Nx add to an Angular monorepo?**

A: Affected commands that build and test only what changed, local and remote caching, code generators, and module boundary rules based on project tags, so a feature can't import another feature's internals.

**Q: When are micro-frontends worth it?**

A: When independent teams need to deploy independently and the organisation is large enough to justify the cost. The costs are duplicated or mismatched dependencies, UX inconsistency and performance overhead. Start with a modular monolith with lazy-loaded features, and split only when team autonomy demands it.

**Q: How do you implement micro-frontends in Angular?**

A: Usually with Module Federation or Native Federation, which load remote apps or routes at runtime and share dependencies like Angular. A shared design system and clear contracts between shells and remotes are essential.

**Q: What layers would you use inside a feature?**

A: Presentation, meaning components. Application, meaning facades or stores that coordinate use cases. Domain, meaning models and pure business rules. Infrastructure, meaning API clients and adapters. Dependencies point inwards.

**Q: Build-time environments or runtime configuration?**

A: Environment files bake values into each build. Runtime configuration, loaded at startup with provideAppInitializer, lets one build artifact be promoted through every environment, which is safer and simpler for CI/CD.

**Q: What are feature flags for?**

A: They decouple deployment from release. You merge unfinished work safely, roll out gradually, run A/B tests, and turn a feature off instantly without a redeploy. Remove old flags so they don't become tech debt.

**Q: What is an ADR?**

A: An Architecture Decision Record: a short document stating the context, the decision, the alternatives considered and the consequences. It makes decisions visible, reviewable and understandable later.

## Build & tooling

**Q: What is the Angular application builder?**

A: The default build system, based on esbuild with a Vite-powered dev server. It's much faster than the old webpack-based builder and supports SSR and prerendering in the same build.

**Q: What are bundle budgets?**

A: Size limits in angular.json that warn or fail the build when bundles or component styles grow beyond a threshold. They stop performance regressions in CI.

**Q: What breaks tree shaking?**

A: Modules with side effects on import, services registered in providers arrays instead of being tree-shakable with providedIn root, and broad barrel files that pull in more than you use.

**Q: How do you analyse bundle size?**

A: Build with stats output and inspect it with a bundle analyser or source-map-explorer, to find heavy dependencies and code that should be lazy-loaded.

**Q: Should you ship source maps to production?**

A: Generate hidden source maps and upload them to your error monitoring tool, so stack traces are readable, without serving the maps publicly.

**Q: How do you upgrade Angular safely?**

A: One major version at a time with ng update, which runs automatic migrations. Follow the official update guide, upgrade third-party libraries in step, and run the full test suite between steps.

**Q: What are schematics?**

A: Code generators and code transformers for the Angular CLI. ng generate uses them to create code, and ng add and ng update use them to install and migrate libraries. A component library can ship its own migrations.

## Testing

**Q: What should you test in a component?**

A: Its behaviour through the DOM: given inputs, it renders the right output, and user interactions emit the right outputs or call the right services. Don't test private methods or implementation details.

**Q: What are component harnesses?**

A: Testing APIs from the CDK that interact with a component the way a user would, like getting a select's options or clicking a button. Tests survive refactors of the component's internal DOM, and libraries like Angular Material ship them.

**Q: How do you test a service that makes HTTP calls?**

A: Provide provideHttpClient and provideHttpClientTesting, inject HttpTestingController, call the service, use expectOne to assert the request and flush a response, and call verify at the end to catch unexpected requests.

**Q: How do you set inputs in a test for a signal-based component?**

A: Use fixture.componentRef.setInput with the input name and value, which works with signal inputs and OnPush. Then await fixture.whenStable or call detectChanges before asserting.

**Q: What makes tests flaky, and how do you fix it?**

A: Timing assumptions, shared state between tests, real network calls, animations and test order dependence. Use fake timers, isolate state, mock the network, and wait for conditions instead of fixed sleeps.

**Q: How do you write good end-to-end tests?**

A: Use Playwright or Cypress for a few critical user journeys. Select elements by role or a dedicated test id, not by CSS structure. Wait for conditions rather than timeouts, and control test data through APIs.

**Q: How do you test dependencies you don't own?**

A: Wrap the third-party API in your own adapter service and mock the adapter in tests. Mocking someone else's complex API directly makes tests brittle and tells you little.

**Q: What is contract testing?**

A: Verifying that frontend and backend agree on an API's shape, for example with Pact or by validating against the OpenAPI schema in CI. It catches integration breaks earlier than end-to-end tests.

## Web platform

**Q: Compare cookies, localStorage, sessionStorage and IndexedDB.**

A: Cookies are small, sent with every request, and can be httpOnly. localStorage is synchronous, about 5 megabytes, and persists. sessionStorage is the same but per tab. IndexedDB is asynchronous, stores large structured data, and suits offline apps.

**Q: When do you use a web worker?**

A: For CPU-heavy work like parsing large files or complex calculations, to keep the main thread free for user interactions. Workers can't touch the DOM and communicate through postMessage. The Angular CLI can generate them.

**Q: What does the Angular service worker do?**

A: It caches the app shell and chosen API responses for offline use and faster repeat loads, and SwUpdate lets you detect and activate new versions. Getting the update flow right is the tricky part.

**Q: What are Angular Elements?**

A: Angular components packaged as standard custom elements with createCustomElement, so they can be used in non-Angular pages. Useful for gradual migrations or embedding widgets, at the cost of bundle size.

**Q: What are IntersectionObserver and ResizeObserver used for?**

A: IntersectionObserver reports when an element enters the viewport, for lazy loading, infinite scroll and analytics impressions. ResizeObserver reports element size changes, for responsive components. Both are far cheaper than scroll and resize listeners.

**Q: Why use requestAnimationFrame instead of setTimeout for animation?**

A: requestAnimationFrame runs right before the browser paints, in sync with the display refresh rate, and pauses in background tabs. setTimeout can fire mid-frame, causing jank and wasted work.

## Errors & monitoring

**Q: How do you handle errors globally in Angular?**

A: Provide a custom ErrorHandler to log and report uncaught errors. provideBrowserGlobalErrorListeners forwards uncaught errors and unhandled promise rejections to it. Handle HTTP errors centrally in an interceptor.

**Q: How should errors look to the user?**

A: Inline messages for field validation, a toast for transient problems with a retry option, and an error page for fatal failures. Never swallow errors silently, and never show raw technical messages.

**Q: What do you monitor in production?**

A: JavaScript errors with readable stack traces via source maps, failed API calls, Core Web Vitals from real users, and release tags so you can tie problems to a deployment. Tools like Sentry or Datadog do this.

**Q: What is a correlation id?**

A: A unique id attached to a request, often in a header, and logged on both frontend and backend, so you can trace one user action across all systems when debugging.

## i18n

**Q: Angular built-in i18n or a runtime library like Transloco?**

A: Built-in i18n translates at compile time: one build per locale, very fast, no runtime cost, but switching language reloads the app. Runtime libraries load translations on the fly with one build and instant switching, at some runtime cost.

**Q: How do you format dates, numbers and plurals for different locales?**

A: Use Angular's date, currency and number pipes with the right locale data, or the Intl APIs directly. Use ICU expressions for plurals and gender, because word order and plural rules differ between languages.

**Q: How do you prepare CSS for right-to-left languages?**

A: Use logical properties like margin-inline-start instead of margin-left, set the dir attribute, and test with a real RTL locale.

## Accessibility

**Q: What are the WCAG levels, and which do you target?**

A: Levels A, AA and AAA. AA is the usual legal and business target. The principles are perceivable, operable, understandable and robust. WCAG 2.2 is the current version.

**Q: What are the keyboard accessibility basics?**

A: Every interactive element can be reached and used with the keyboard, focus is always visible, the tab order is logical, and nothing traps focus except a modal, which must close with Escape.

**Q: How do you make a modal dialog accessible?**

A: Use role dialog with aria-modal, or the native dialog element with showModal. Move focus into it when it opens, trap focus inside, close it with Escape, and return focus to the element that opened it.

**Q: How do you test accessibility?**

A: Automated checks with axe in unit or end-to-end tests catch only part of the problems. Add a keyboard-only pass, a screen reader check with NVDA or VoiceOver, and zoom to 200 and 400 percent to check reflow.

**Q: How do you make form errors accessible?**

A: Every field has a visible label. Link the error message to the field with aria-describedby, set aria-invalid, and don't rely on color alone. On submit, move focus to the first invalid field or an error summary.

## Product & stakeholders

**Q: How do you propose a measurable, customer-focused improvement?**

A: Start from a user problem and a baseline metric, state a hypothesis, make the smallest change that tests it, measure with analytics or an A/B test, and report the result in business terms. For example: reduce checkout abandonment by improving INP on the payment step.

**Q: Which metrics show frontend success?**

A: Core Web Vitals from real users, JavaScript error rate, conversion or task completion rate, time on task, accessibility issues, bundle size, and delivery metrics like lead time and change failure rate.

**Q: What makes an A/B test trustworthy?**

A: One clear change, a primary metric decided up front, enough traffic for statistical significance, guardrail metrics like errors and performance, and running it long enough to cover weekly patterns. Feature flags make it easy.

**Q: How do you work effectively with a third-party partner's API?**

A: Agree the contract early, ideally in OpenAPI, including the error format and versioning. Build against mocks or their sandbox, clarify SLAs and rate limits, keep decisions in writing, and agree an escalation path before you need it.

**Q: How do you explain tech debt to non-technical stakeholders?**

A: In their terms: risk, time and money. For example, every feature in this area takes twice as long and we had three incidents last quarter. Propose a small, measurable investment with an expected payoff.

**Q: How do you push back on scope or a deadline?**

A: Don't just say no. Offer options with their costs: what we can ship by the date, what it would take to ship everything, and the risks of each. Let the product owner choose with the trade-offs visible.

**Q: How do you work well with designers?**

A: Get involved early to flag feasibility and edge cases, share design tokens between design and code, review designs for accessibility and states like loading, empty and error, and keep components in sync between the design tool and the library.

**Q: How do you work well with QA?**

A: Shift left: agree testable acceptance criteria before development, add stable test ids, share test environments and data, and write bug reports with clear steps, expected and actual results.

## HTML & styles

**Q: What is semantic HTML, and why does it matter?**

A: Elements that describe their meaning: header, nav, main, aside, footer, article, a correct heading order, button for actions and links for navigation. Assistive technology, search engines and browsers rely on it.

**Q: What does box-sizing border-box change?**

A: The declared width and height include padding and border, so elements don't grow unexpectedly when you add padding. Most resets apply it to everything.

**Q: What is margin collapse?**

A: Vertical margins of adjacent block elements, or of a parent and its first or last child, combine into the larger one instead of adding up. It doesn't happen in flex or grid layouts, which is one reason to space items with gap.

**Q: What are container queries, and why do they matter for components?**

A: They style an element based on the size of its container instead of the viewport. A library component can adapt to wherever it's placed, like a narrow sidebar or a wide main area.

**Q: How do responsive images work?**

A: srcset lists image files at different widths and sizes tells the browser how wide the image will display, so it downloads the smallest suitable file. NgOptimizedImage generates srcset for you and warns about common mistakes.

**Q: What are Sass maps and loops good for?**

A: Maps store related values, like a spacing scale or theme colors, and each loops generate classes or custom properties from them, keeping a design system consistent.

**Q: Mixins or extend in Sass?**

A: Mixins copy declarations wherever they're included and can take arguments. extend merges selectors, which can produce unexpected selector bloat and doesn't work across media queries. Prefer mixins, or plain CSS custom properties.

**Q: How does LESS compare with Sass?**

A: Both add variables, nesting, mixins and functions. LESS uses the at sign for variables and treats classes as mixins. Sass has a more powerful module system, maps and control flow, and it's the standard choice in Angular projects.

**Q: What is BEM, and is it still useful with Angular?**

A: Block, element, modifier naming, like card, card double underscore title, card double dash active. Emulated encapsulation already scopes component styles, but BEM is still useful for global styles and for stable class names that a library exposes as theming hooks.

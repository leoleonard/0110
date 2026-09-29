# 03 — JavaScript (ES5 to ES2017/ES8, plus what's around it)

> **How to use this file:** the job spec says "JS ES5–ES8", so expect fundamentals, but at senior level the interviewer is not checking whether you can *recite* hoisting — they want to see that you understand the **runtime model** (scope, `this`, the event loop, promises) well enough to debug production issues and to explain them to a junior. Typical probes: "what does this print and why", "why is `this` undefined here", "why did this reducer not trigger a re-render", "write a debounce". Answer with the mechanism first, then the practical consequence in an Angular codebase. ES versions are labelled throughout — knowing that object spread is ES2018 (not ES6) or that `Promise.allSettled` is ES2020 signals precision.
>
> Quick version map: **ES5** (2009) · **ES2015/ES6** (let/const, classes, arrow fns, promises, modules, destructuring, Map/Set, Symbol, generators) · **ES2016/ES7** (`**`, `Array.prototype.includes`) · **ES2017/ES8** (async/await, `Object.values/entries`, `Object.getOwnPropertyDescriptors`, `padStart/padEnd`, trailing commas in parameter lists, SharedArrayBuffer/Atomics) · ES2018 (object rest/spread, async iteration, `Promise.prototype.finally`) · ES2020 (`?.`, `??`, `allSettled`, BigInt) · ES2021 (`Promise.any`, `??=`, WeakRef). `structuredClone`, `queueMicrotask`, `setTimeout` and `requestAnimationFrame` are **web/host APIs, not ECMAScript**.

---

## A. Most commonly asked questions

### Q1. What is a closure, and where do you actually use one?

**Answer (1–2 min):**
- A closure is a function together with the **lexical environment it was created in**. The function keeps access to variables of its outer scope even after that outer function has returned — the variables are kept alive by reference, not copied.
- Practical uses:
  - **Data privacy / encapsulation** — module pattern (pre-ES2015), factory functions, private state without classes.
  - **Function factories / partial application** — `const withPrefix = p => msg => \`${p}${msg}\``.
  - **Stateful utilities** — `debounce`, `throttle`, `once`, `memoize` all keep their timer/cache in a closure.
  - **Callbacks and handlers** that need context — every `subscribe(v => this.x = v)` and every Angular functional guard/interceptor is a closure over its injected dependencies.
- Cost: closures keep the captured scope alive. A long-lived callback (global event listener, un-torn-down subscription) capturing a component keeps the whole component tree in memory — a classic leak.

```ts
function createCounter() {
  let count = 0;                 // private, lives in the closure
  return {
    increment: () => ++count,
    get value() { return count; },
  };
}
const c = createCounter();
c.increment(); c.value; // 1 — `count` is not reachable any other way
```

**Go deeper:**
- Closures capture *variables* (bindings), not values — which is exactly what causes the loop bug (T3).
- In Angular, `inject()` inside a functional guard/interceptor works because the function runs in an injection context; the closure then holds the resolved service.

### Q2. Explain hoisting and the temporal dead zone (TDZ).

**Answer:**
- Before executing a scope, the engine creates bindings for every declaration in it. That's "hoisting" — it's about **creation of bindings**, not physically moving code.
- `var` — hoisted **and initialised to `undefined`**, function-scoped. Reading it before the assignment gives `undefined`.
- Function declarations — hoisted **with their body**, callable before the line they're declared on.
- `let` / `const` / `class` (ES2015) — hoisted but **uninitialised**. From the start of the block until the declaration executes, the binding is in the **TDZ**; accessing it throws `ReferenceError`.
- Function *expressions* and arrow functions assigned to `const` follow the `const` rule — not callable before the line.

```ts
console.log(a); // undefined
var a = 1;

console.log(b); // ReferenceError: Cannot access 'b' before initialization
let b = 2;

hello();        // works — function declaration hoisted with body
function hello() {}

let x = 'outer';
{
  console.log(x); // ReferenceError — inner `x` shadows and is in its TDZ
  let x = 'inner';
}
```

**Go deeper:** the TDZ is *temporal* (time-based), not positional: a function declared above a `let` can reference it, as long as it's *called* after the `let` line has run. `typeof` on a TDZ binding also throws (unlike `typeof undeclaredVar`, which returns `'undefined'`).

### Q3. `var` vs `let` vs `const`.

**Answer:**
| | `var` (ES5) | `let` (ES2015) | `const` (ES2015) |
|---|---|---|---|
| Scope | function | block | block |
| Hoisting | initialised to `undefined` | TDZ | TDZ |
| Re-assign | yes | yes | no |
| Re-declare in same scope | yes | no | no |
| Creates property on global object (top level, script) | yes (`window.x`) | no | no |
| Per-iteration binding in `for` | no | yes | yes (`for...of`) |

- `const` means the **binding** can't be reassigned — it does **not** make the value immutable. `const arr = []; arr.push(1)` is fine. For immutability use `Object.freeze` (shallow) or `readonly`/`ReadonlyArray` in TypeScript (compile time only).
- Default: `const` everywhere, `let` when you genuinely reassign, `var` never in new code.

### Q4. Explain the rules for `this`.

**Answer:** `this` is decided by **how a function is called**, not where it's defined (except arrow functions). In priority order:
1. **`new` binding** — `new Foo()`: `this` is the newly created object.
2. **Explicit binding** — `fn.call(obj, …)`, `fn.apply(obj, [...])`, `fn.bind(obj)` (bind creates a permanently bound function; a later `call` can't override it, though `new` can).
3. **Implicit binding** — `obj.fn()`: `this` is the object to the left of the dot *at call time*.
4. **Default binding** — plain `fn()`: `undefined` in strict mode (which includes all ES modules and class bodies — so all Angular code), the global object in sloppy mode.

- **Arrow functions** (ES2015) have no own `this`; they capture it **lexically** from the enclosing scope. `call/apply/bind` can't change it, and they can't be used with `new`.
- **Class methods** are ordinary functions on the prototype — they follow rules 1–4. Class bodies are strict, so a detached method gets `this === undefined`.

```ts
class Cart {
  items: string[] = [];
  add(item: string) { this.items.push(item); }
}
const cart = new Cart();
const add = cart.add;
add('x'); // TypeError: Cannot read properties of undefined (reading 'items')
```

**Angular relevance:** passing a method reference as a callback — `obs$.subscribe(this.handle)`, `array.map(this.format)`, `addEventListener('click', this.onClick)`, `setTimeout(this.tick, 100)` — loses `this`. Fixes: arrow wrapper `v => this.handle(v)`, class-field arrow `handle = (v) => {...}`, or `.bind(this)`. See T2 for the trade-offs.

### Q5. Prototypes and the prototype chain vs `class` syntax.

**Answer:**
- Every object has an internal `[[Prototype]]` link (`Object.getPrototypeOf(obj)`, legacy `__proto__`). Property lookup walks this chain until it finds the property or hits `null`.
- Functions have a `.prototype` property; `new F()` creates an object whose `[[Prototype]]` is `F.prototype`. That's how methods are shared across instances — one function object, not one per instance.
- `class` (ES2015) is **mostly syntax over the same prototype model**: methods go on `Foo.prototype`, `extends` sets up two chains (instance → `Child.prototype` → `Parent.prototype`, and `Child` → `Parent` for statics).
- But it's not *pure* sugar: classes are always strict, class constructors **throw if called without `new`**, methods are non-enumerable, `super` has proper semantics, and there's the TDZ. Newer additions (private `#fields`, ES2022; static blocks) have no ES5 equivalent.

```ts
// ES5
function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { return this.name + ' makes a sound'; };
function Dog(name) { Animal.call(this, name); }
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

// ES2015
class Animal2 { constructor(public name: string) {} speak() { return `${this.name} makes a sound`; } }
class Dog2 extends Animal2 {}
```

**Go deeper:**
- Class *fields* (`handle = () => {}`) are per-instance properties, **not** on the prototype — each instance gets its own function. Fine for components, wasteful for millions of small objects.
- `instanceof` checks the prototype chain; it breaks across realms (iframes) and for plain objects that are structurally "the same" — one reason to prefer discriminated unions over class hierarchies for state/DTOs.
- Prefer composition over deep inheritance; in Angular, `inject()` made base-class-for-DI-reasons patterns largely unnecessary.

### Q6. Explain the event loop.

**Answer:**
- JS runs on a **single thread** with one **call stack**. Long synchronous work blocks everything, including rendering and input.
- Async work is handed to the host (browser/Node). When it completes, a callback is queued:
  - **Task (macrotask) queue(s)** — `setTimeout`/`setInterval`, DOM events, `MessageChannel`, network callbacks, I/O.
  - **Microtask queue** — promise reactions (`.then/.catch/.finally`, continuation after `await`), `queueMicrotask`, `MutationObserver`.
- One loop iteration in a browser:
  1. Take **one** task from a task queue and run it to completion.
  2. **Drain the entire microtask queue** — including microtasks queued by microtasks.
  3. If it's time to render (~every 16.7 ms at 60 Hz, and only if something changed): run **`requestAnimationFrame` callbacks**, then style → layout → paint → composite.
  4. Repeat.
- Consequences:
  - A promise callback always runs before the next `setTimeout(…, 0)` — even if the timeout was scheduled first.
  - An infinite chain of microtasks **starves** rendering and tasks (the page freezes), whereas a recursive `setTimeout` doesn't.
  - `requestAnimationFrame` is the right place for visual updates; it runs right before paint and pauses in background tabs.
  - `setTimeout(fn, 0)` is not 0 ms — it's "next task, at least ~0–4 ms later" (nested timers are clamped to 4 ms).

**Angular relevance:** historically Zone.js patched all these async APIs to know "when to run change detection". Since v21 new apps are **zoneless by default** — change detection is scheduled by signal writes, `markForCheck()` (which `AsyncPipe` calls), and template event listeners, not by "any `setTimeout` finished". Understanding the event loop is exactly what lets you reason about *when* the UI updates in either model. In Angular, `afterNextRender`/`afterRenderEffect` are the framework-level equivalents of "after the DOM is updated" — prefer them over `setTimeout` hacks.

### Q7. Microtasks vs macrotasks — what does this print? (the classic puzzle)

**Answer:** walk it through out loud: sync first, then drain microtasks in FIFO order, then one macrotask, then drain microtasks again…

```ts
console.log('A');

setTimeout(() => {
  console.log('B');
  Promise.resolve().then(() => console.log('C'));
}, 0);

setTimeout(() => console.log('D'), 0);

Promise.resolve()
  .then(() => {
    console.log('E');
    setTimeout(() => console.log('F'), 0);
  })
  .then(() => console.log('G'));

queueMicrotask(() => console.log('H'));

(async () => {
  console.log('I');
  await null;
  console.log('J');
})();

console.log('K');
```

**Output:** `A I K E H J G B C D F` (verified in Node; same in browsers).

Reasoning:
1. **Sync:** `A`, then the async IIFE body runs synchronously up to the first `await` → `I`, then `K`.
2. **Microtask queue after sync:** `[E, H, J]` (in the order they were queued). Running `E` queues timeout `F` (macrotask) and the chained `G` (microtask, appended to the end). Queue drains: `E H J G`.
3. **Macrotasks in order:** `B` runs and queues microtask `C` → microtasks drain before the next task → `C`. Then `D`, then `F` (it was queued last, during step 2).

Key sound bite: *"`async` functions run synchronously until the first `await`; everything after an `await` is a microtask. And the microtask queue is drained completely between every macrotask."*

### Q8. Promises: `all`, `allSettled`, `race`, `any`.

**Answer:**
| Combinator | Version | Resolves when | Rejects when |
|---|---|---|---|
| `Promise.all` | ES2015 | **all** fulfil → array of values (input order) | **first** rejection (fail-fast) |
| `Promise.allSettled` | **ES2020** | all settle → `{status, value \| reason}[]` | never |
| `Promise.race` | ES2015 | first to **settle** (fulfil *or* reject) | first to settle is a rejection |
| `Promise.any` | **ES2021** | first to **fulfil** | all reject → `AggregateError` |

- `all` is fail-fast, but it **doesn't cancel** the others — promises aren't cancellable; the other requests keep running. For cancellation use `AbortController` (fetch) or RxJS (unsubscription cancels `HttpClient` requests).
- `allSettled` for "load a dashboard of independent widgets, show what succeeded".
- `race` for timeouts: `Promise.race([fetchData(), timeout(5000)])` — again, the loser isn't aborted.
- `any` for redundancy: first healthy mirror wins.
- Empty input: `all([])` and `allSettled([])` resolve immediately; `any([])` rejects with `AggregateError`; `race([])` stays **pending forever**.

**Go deeper:** a promise is settled once; `.then` always calls back asynchronously (microtask), even for already-resolved promises — that's why "Zalgo" (sometimes-sync, sometimes-async callbacks) doesn't happen with promises. `Promise.prototype.finally` is ES2018.

### Q9. async/await — error handling, and the sequential vs parallel pitfall.

**Answer:**
- `async` functions (ES2017) always return a promise; `await` pauses the function (not the thread) and resumes it in a microtask.
- **Errors:** a `throw` inside becomes a rejection; `await` on a rejected promise throws at that line, so `try/catch/finally` works naturally. Unhandled rejections surface via `unhandledrejection` — in Angular they reach the `ErrorHandler`.
- **The pitfall:** awaiting independent calls one after another serialises them.

```ts
// Sequential: total ≈ t(user) + t(orders) — only correct if orders depends on user
const user = await api.getUser(id);
const orders = await api.getOrders(id);

// Parallel: total ≈ max(t(user), t(orders))
const [user2, orders2] = await Promise.all([api.getUser(id), api.getOrders(id)]);

// Also parallel — start both, then await (but beware: if `o` rejects while
// awaiting `u`, it's briefly an unhandled rejection. Promise.all is cleaner.)
const u = api.getUser(id);
const o = api.getOrders(id);
```

- `return await` inside `try` matters: `return promise` inside a `try` does *not* catch that promise's rejection; `return await promise` does.
- Loops: `for...of` + `await` is sequential (sometimes wanted — e.g. rate-limited API); `await Promise.all(items.map(fn))` is parallel (maybe with a concurrency limit); `forEach` + `await` is **wrong** (T5).

**Angular relevance:** in Angular most async is RxJS (`HttpClient` returns Observables) or signals (`resource`, `httpResource`). I'd use `async/await` for one-shot imperative flows (e.g. a submit handler, `firstValueFrom` in a guard) and Observables where I need cancellation, retry, or combining streams — `switchMap` cancels the stale request, `await` can't.

### Q10. Destructuring, spread and rest.

**Answer:**
- **Destructuring** (ES2015): `const { id, name: label = 'n/a', ...rest } = obj; const [first, , third] = arr;` Defaults apply only for `undefined`, **not `null`**. Destructuring `null`/`undefined` throws.
- **Spread**: array spread and argument spread are ES2015; **object spread/rest is ES2018** (a common mislabel as "ES6").
- **Rest parameters** (ES2015) replace `arguments` — a real array, works in arrow functions (which have no `arguments`).
- Spread is a **shallow** copy — nested objects are shared (T6).
- Object spread copies own enumerable properties only — no prototype, getters are **invoked** and turned into plain values, later keys win (`{ ...defaults, ...overrides }`).

```ts
function configure({ retries = 3, timeout = 5000 }: Partial<Options> = {}) { /* … */ }
const merged = { ...defaults, ...userOptions };            // shallow merge
const withoutPassword = (({ password, ...safe }) => safe)(user); // omit a key
```

### Q11. `Object.entries/values` and `padStart/padEnd` (ES2017).

**Answer:**
- `Object.keys` (ES5) → own enumerable string keys. `Object.values` / `Object.entries` (ES2017) → values / `[key, value]` pairs, same order rules (integer-like keys ascending first, then string keys in insertion order; Symbols excluded).
- Pair with `Object.fromEntries` (ES2019) for transform pipelines:

```ts
const prices = { apple: 1.2, pear: 0.8 };
const withVat = Object.fromEntries(
  Object.entries(prices).map(([k, v]) => [k, +(v * 1.2).toFixed(2)]),
);
```

- `padStart/padEnd` (ES2017): `'7'.padStart(3, '0') // '007'` — formatting IDs, times, fixed-width columns. For user-facing numbers/dates, prefer `Intl.NumberFormat`/`Intl.DateTimeFormat` or Angular pipes — they handle locales.
- Other ES2017 bits worth naming: `Object.getOwnPropertyDescriptors` (proper cloning including getters: `Object.defineProperties({}, Object.getOwnPropertyDescriptors(src))`), trailing commas in parameter lists, SharedArrayBuffer/Atomics.

### Q12. Equality: `==` vs `===`, `Object.is`, `NaN`, `-0`.

**Answer:**
- `===` (strict): no coercion. `==` (loose): coerces types using the Abstract Equality algorithm — `null == undefined` is true (and they equal nothing else), otherwise it converts toward numbers/primitives.
- `NaN` is the only value not equal to itself: `NaN === NaN` is `false`. Use `Number.isNaN(x)` (ES2015) — not global `isNaN`, which coerces (`isNaN('abc') === true`).
- `+0 === -0` is `true`.
- `Object.is` (ES2015) is "SameValue": like `===` but `Object.is(NaN, NaN) === true` and `Object.is(0, -0) === false`.
- Array methods differ: `indexOf` uses `===` (can't find `NaN`), `includes` (ES2016) uses SameValueZero (finds `NaN`).
- **Angular relevance:** signals use `Object.is` as the default equality function, so setting the same primitive or the **same object reference** does not notify; mutating an object in place and calling `set(sameRef)` won't trigger updates. Same idea as `OnPush` input checks and `distinctUntilChanged()` (which uses `===`).
- Rule of thumb: always `===`; the one idiom some teams allow is `x == null` to check for both `null` and `undefined` (today `x ?? default` / `x?.y`, ES2020, usually reads better).

### Q13. Deep vs shallow copy.

**Answer:**
- **Shallow** — `{...obj}`, `[...arr]`, `Object.assign`, `arr.slice()`: new top-level container, nested references shared.
- **`JSON.parse(JSON.stringify(x))`** — deep, but lossy:
  - `Date` → ISO string (doesn't come back as a `Date`),
  - `undefined`, functions and Symbols are dropped (in arrays they become `null`),
  - `NaN`/`Infinity` → `null`,
  - `Map`/`Set` → `{}`,
  - class instances lose their prototype,
  - circular references **throw**, `BigInt` **throws**.
- **`structuredClone`** (web/Node API, not ES; broadly available since 2022) — handles `Date`, `Map`, `Set`, `RegExp`, typed arrays, `Blob`s, **circular references**. Limitations:
  - functions and DOM nodes **throw** `DataCloneError`,
  - **prototypes are lost** — a class instance comes back as a plain object,
  - getters/setters are not preserved (values are copied), property descriptors and Symbol-keyed properties are dropped.
- Senior take: **needing** a deep clone is often a smell. With immutable updates you copy only the path you change (structural sharing), which is also what makes reference equality checks (`OnPush`, memoised selectors, signal equality) cheap and correct.

```ts
// Immutable nested update — copy only the path that changes
const next = {
  ...state,
  user: { ...state.user, address: { ...state.user.address, city: 'Leeds' } },
};
```

### Q14. Implement `debounce` and `throttle` from scratch.

**Answer (what they are):**
- **Debounce** — wait until calls **stop** for `wait` ms, then run once. Search-as-you-type, resize-end, autosave.
  - *trailing* (default): run after the quiet period with the **last** args.
  - *leading*: run immediately on the first call, ignore the rest of the burst.
  - both: run at the start **and** at the end of a burst (only once if the burst was a single call).
- **Throttle** — run **at most once per `wait` ms** while calls keep coming. Scroll position, mousemove, drag, rate-limited analytics.
  - *leading*: fire on the first call of a window.
  - *trailing*: guarantee the **final** state is delivered after the burst — important for scroll/resize so the last position isn't lost.

```ts
type Fn<A extends unknown[]> = (...args: A) => void;

export function debounce<A extends unknown[]>(
  fn: Fn<A>,
  wait: number,
  { leading = false, trailing = true } = {},
) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let lastArgs: A | undefined;
  let lastThis: unknown;

  function debounced(this: unknown, ...args: A) {
    lastArgs = args;
    lastThis = this;
    const callNow = leading && timer === undefined; // first call of a burst

    clearTimeout(timer);                            // every call restarts the quiet period
    timer = setTimeout(() => {
      timer = undefined;
      if (trailing && lastArgs) fn.apply(lastThis, lastArgs);
      lastArgs = lastThis = undefined;
    }, wait);

    if (callNow) {
      lastArgs = lastThis = undefined;              // don't fire trailing for a single call
      fn.apply(this, args);
    }
  }

  debounced.cancel = () => {
    clearTimeout(timer);
    timer = lastArgs = lastThis = undefined;
  };
  return debounced;
}

export function throttle<A extends unknown[]>(
  fn: Fn<A>,
  wait: number,
  { leading = true, trailing = true } = {},
) {
  let lastRun = 0;                                  // 0 = "no window open"
  let timer: ReturnType<typeof setTimeout> | undefined;
  let pendingArgs: A | undefined;
  let pendingThis: unknown;

  const run = (time: number) => {
    lastRun = time;
    const args = pendingArgs!, ctx = pendingThis;
    pendingArgs = pendingThis = undefined;
    fn.apply(ctx, args);
  };

  function throttled(this: unknown, ...args: A) {
    const now = Date.now();
    if (lastRun === 0 && !leading) lastRun = now;   // open a window without firing
    pendingArgs = args;                             // always keep the latest args
    pendingThis = this;

    const remaining = wait - (now - lastRun);
    if (remaining <= 0) {
      clearTimeout(timer);
      timer = undefined;
      run(now);                                     // leading edge / window elapsed
    } else if (trailing && timer === undefined) {
      timer = setTimeout(() => {
        timer = undefined;
        if (pendingArgs) run(leading ? Date.now() : 0);
      }, remaining);                                // trailing edge of this window
    }
  }

  throttled.cancel = () => {
    clearTimeout(timer);
    timer = pendingArgs = pendingThis = undefined;
    lastRun = 0;
  };
  return throttled;
}
```

Points to say while writing it:
- Closures hold the timer/args; `this` is forwarded with a regular `function` + `apply` so it works as a method.
- Always pass the **latest** args on the trailing edge.
- Expose `cancel()` — in Angular call it in `DestroyRef.onDestroy` so a trailing call doesn't fire into a destroyed component.
- `leading: false, trailing: false` for throttle means it never fires — worth validating.
- For tests, use fake timers (`vi.useFakeTimers()` in Vitest, the default runner since v21) rather than real waits.
- In Angular I'd usually reach for RxJS instead: `debounceTime`, `throttleTime(ms, undefined, { leading, trailing })`, `auditTime` (trailing-only throttle), or the `debounce` rule in Signal Forms (v22) for async validation — and I'd write the vanilla version for non-reactive code or a framework-agnostic utils package.

### Q15. ES modules vs CommonJS.

**Answer:**
- **ESM** (ES2015 syntax; `import`/`export`): **static** structure, resolved before execution → enables tree-shaking and reliable bundling; **live bindings** (importers see updated exported values); async-capable loading; strict mode by default; top-level `await` (ES2022); `import()` dynamic import (ES2020) for code splitting — which is exactly what `loadComponent: () => import(...)` and `@defer` compile to.
- **CommonJS** (Node's original: `require`/`module.exports`): **dynamic**, synchronous, exports are a **copied value** snapshot of `module.exports`; poor tree-shaking.
- Angular angle: the Angular CLI warns about CommonJS dependencies because they bail out of optimisation; the Angular Package Format ships ESM. When choosing third-party libs for a shared component library I check for ESM builds and `sideEffects: false`.

### Q16. Briefly: getters/setters, Symbol, Map/Set/WeakMap, generators, `typeof null`, floating point.

**Answer:**
- **Getters/setters** (ES5 via object literals and `Object.defineProperty`; class accessors ES2015): computed/validated properties. Angular used setter-inputs for "react to input change"; with signal inputs (`input()`) I'd use `computed()` instead — setters run on every write and hide side-effects.
- **Symbol** (ES2015): unique, non-string keys — collision-free "hidden" properties, and well-known symbols to hook into the language (`Symbol.iterator`, `Symbol.asyncIterator`, `Symbol.toPrimitive`). Skipped by `JSON.stringify`, `Object.keys` and `for...in`.
- **Map/Set** (ES2015): any key type (including objects), insertion-ordered, `.size`, O(1) average lookups; better than plain objects for dynamic dictionaries (no prototype key collisions like `'__proto__'`).
- **WeakMap/WeakSet** (ES2015): keys must be objects and are **weakly held** — the entry doesn't prevent GC of the key. Not iterable, no `.size`. Use for per-object metadata/caches (e.g. caching per DOM node or per component instance) without leaks. `WeakRef`/`FinalizationRegistry` are ES2021 and rarely the right answer.
- **Generators/iterators** (ES2015): `function*` returns an iterator; `yield` pauses; the iterator protocol (`next() → {value, done}`) powers `for...of`, spread and destructuring. Useful for lazy sequences and custom iterable data structures; async generators + `for await` are ES2018. (Redux-Saga is built on generators; RxJS covers most of that ground in Angular.)
- **`typeof null === 'object'`** — a bug from the first JS implementation, kept for compatibility. Check with `x === null`. Also: `typeof function(){} === 'function'`, `typeof NaN === 'number'`, `typeof []  === 'object'` (use `Array.isArray`, ES5).
- **Floating point** — numbers are IEEE-754 doubles, so `0.1 + 0.2 === 0.30000000000000004`. Safe integers up to `Number.MAX_SAFE_INTEGER` (2^53 − 1). For money: integer minor units (pence/cents) or a decimal library; compare with a tolerance (`Math.abs(a - b) < Number.EPSILON`) only for small magnitudes; `BigInt` (ES2020) for large integers (IDs from a backend should often be strings for this reason).

---

## B. Tricky / trap questions

### T1. The output-ordering puzzle with `async` in the mix

```ts
async function first() {
  console.log('1');
  await second();
  console.log('2');
}
async function second() { console.log('3'); }

console.log('4');
setTimeout(() => console.log('5'), 0);
first();
new Promise<void>(resolve => { console.log('6'); resolve(); }).then(() => console.log('7'));
console.log('8');
```

**The trap:** thinking `await second()` pauses before `second` runs, or that the `Promise` executor is async.

**Strong answer includes:**
- Output: `4 1 3 6 8 2 7 5`.
- `first()` runs synchronously → `1`, calls `second()` synchronously → `3`, then the rest of `first` is a microtask.
- The **Promise executor runs synchronously** → `6`.
- Microtasks in order queued: continuation of `first` (`2`), then `.then` (`7`). Then the timeout (`5`).
- Sound bite: "the executor is sync, `.then` is a microtask, `setTimeout` is a task."

### T2. "Why is `this` undefined in my callback?"

```ts
@Component({ /* … */ })
export class OrdersComponent {
  private readonly api = inject(OrdersApi);
  protected readonly orders = signal<Order[]>([]);

  load() {
    this.api.list().subscribe(this.onLoaded);   // bug: `this` is undefined inside onLoaded
  }
  onLoaded(orders: Order[]) { this.orders.set(orders); }
}
```

**The trap:** "Angular broke `this`" or "use `var self = this`".

**Strong answer includes:**
- The method is passed as a bare function reference; RxJS calls it as a plain function → default binding → `undefined` (class bodies are strict).
- Fixes and trade-offs:
  - Arrow wrapper at call site: `.subscribe(o => this.onLoaded(o))` — clearest, my default.
  - Class-field arrow: `onLoaded = (o: Order[]) => {...}` — always bound, but it's per-instance (not on the prototype), so it's harder to spy on via the prototype and can't be called via `super`.
  - `.bind(this)` — works; creates a new function each time (matters for `removeEventListener`: you must keep the same reference).
- Same bug in `addEventListener`, `setTimeout(this.tick)`, `array.map(this.format)`, and when passing a method to a child component as an `input()` callback.
- Template bindings like `(click)="save()"` are fine — Angular calls them on the component instance.

### T3. Closure in a loop with `var`

```ts
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// prints 3, 3, 3
```

**The trap:** expecting `0 1 2`, or explaining it as "setTimeout is slow".

**Strong answer includes:**
- `var` is function-scoped: **one** `i` binding shared by all three closures; by the time the callbacks run (after the loop, as tasks), `i` is `3`.
- Fix: `let` (ES2015) creates a **fresh binding per iteration** → `0 1 2`.
- Pre-ES2015 fix: an IIFE to capture the value — `(function (j) { setTimeout(() => console.log(j)); })(i);` — or `setTimeout(console.log, 0, i)` passing args.
- Point: closures capture bindings, not values.

### T4. `[] == ![]` — true or false?

**The trap:** "an array can't equal its own negation, so false".

**Strong answer includes:**
- It's `true`. `![]` → `false` (every object is truthy). Now `[] == false`: boolean → number `0`; object → primitive via `toString` → `''`; `'' → 0`; `0 == 0` → `true`.
- Related gotchas: `null == 0` is `false` but `null >= 0` is `true` (relational comparison converts `null` to `0`, equality doesn't). `'' == 0` true, `'0' == false` true, `[0] == false` true.
- The actual senior answer: "I don't memorise the coercion table — I use `===` and a lint rule (`eqeqeq`), and I'd flag `==` in review."

### T5. `await` inside `forEach`

```ts
async function saveAll(items: Item[]) {
  items.forEach(async item => {
    await api.save(item);
  });
  console.log('all saved');   // lies — runs before any save completes
}
```

**The trap:** assuming `forEach` waits.

**Strong answer includes:**
- `forEach` ignores the callback's return value — it fires N async callbacks and returns synchronously. `'all saved'` logs immediately; rejections are **unhandled**; `saveAll`'s caller can't catch errors.
- Same with `map` unless you `await Promise.all(...)` the result; `filter`/`reduce` with async callbacks are also wrong (async `filter` returns promises, which are all truthy).
- Fix depends on intent: sequential → `for (const item of items) await api.save(item);`; parallel → `await Promise.all(items.map(i => api.save(i)))`; parallel with limit → a small pool or RxJS `mergeMap(fn, concurrency)`.
- Ideally the backend offers a bulk endpoint — N requests is often the real problem.

### T6. Shallow copy of a nested object in a reducer

```ts
on(updateCity, (state, { city }) => {
  const next = { ...state };
  next.user.address.city = city;   // mutates the previous state's nested object
  return next;
});
```

**The trap:** "I used spread, so it's immutable."

**Strong answer includes:**
- Spread copies only the top level; `next.user` **is** `state.user`. The old state is mutated — time-travel debugging lies, memoised selectors on `user`/`address` return stale results (their input reference didn't change), `OnPush` children receiving `user` don't update, and signal `set` with `Object.is` sees the same reference.
- In dev, NgRx runtime checks (`strictStateImmutability`, on by default) freeze state and throw on this mutation.
- Fix: copy each level along the path (Q13), or use a helper — NgRx `patchState` / entity adapters, or Immer (`produce`) if the team accepts the dependency.
- Same applies to `signal.update(s => { s.items.push(x); return s; })` — returns the same reference, no notification. Return a new array.

### T7. `0.1 + 0.2 === 0.3`, `typeof NaN`, and a default `sort`

```ts
0.1 + 0.2 === 0.3;           // false (0.30000000000000004)
typeof NaN;                  // 'number'
[10, 9, 1, 2].sort();        // [1, 10, 2, 9]
```

**The trap:** treating these as JS being "broken" rather than knowing the rules.

**Strong answer includes:**
- Floating point: IEEE-754 binary can't represent 0.1 exactly — same in Java/C#/Python. Money in integer minor units; display via `Intl.NumberFormat`/`CurrencyPipe`.
- `NaN` is a numeric value meaning "not a valid number" — its type is number. Test with `Number.isNaN`.
- `Array.prototype.sort` with no comparator converts elements to **strings** and compares UTF-16 code units → lexicographic. Always pass a comparator: `(a, b) => a - b`; for strings use `a.localeCompare(b)` or `Intl.Collator` (locale-aware, e.g. accents).
- `sort` **mutates in place** — sorting an `input()` array or state array directly is a bug; copy first (`[...arr].sort(...)`) or use `toSorted` (ES2023) where your target supports it.
- Sort has been guaranteed **stable** since ES2019.

### T8. "Is `const` immutable?" / "Does `Object.freeze` make it safe?"

**The trap:** yes to both.

**Strong answer includes:**
- `const` prevents rebinding, not mutation.
- `Object.freeze` is **shallow** — nested objects are still mutable; in non-strict code writes fail silently, in strict code they throw.
- TypeScript `readonly` / `Readonly<T>` / `as const` are compile-time only — zero runtime protection, but great for catching mistakes in a shared library's public API.

---

## C. Code examples

### `once` and `memoize` — closures as utilities

```ts
export function once<A extends unknown[], R>(fn: (...args: A) => R) {
  let called = false;
  let result: R;
  return (...args: A): R => {
    if (!called) { called = true; result = fn(...args); }
    return result;
  };
}

export function memoize<A, R>(fn: (arg: A) => R) {
  const cache = new Map<A, R>();          // use WeakMap if A is an object and you care about GC
  return (arg: A): R => {
    if (!cache.has(arg)) cache.set(arg, fn(arg));
    return cache.get(arg)!;
  };
}
```

### Promise timeout with real cancellation

```ts
export async function fetchWithTimeout(url: string, ms: number): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { signal: controller.signal });   // `return await` so `finally` runs after settle
  } finally {
    clearTimeout(timer);
  }
}
```

### Debounced input in Angular — RxJS vs the vanilla util

```ts
@Component({
  selector: 'app-search',
  template: `<input (input)="query.set($any($event.target).value)" />`,
})
export class SearchComponent {
  private readonly api = inject(SearchApi);
  protected readonly query = signal('');

  protected readonly results = toSignal(
    toObservable(this.query).pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => (q.length < 2 ? of([]) : this.api.search(q))),  // cancels stale requests
    ),
    { initialValue: [] },
  );
}
```

### A generator for lazy pagination

```ts
async function* pages<T>(load: (page: number) => Promise<T[]>) {   // async generators: ES2018
  for (let page = 1; ; page++) {
    const items = await load(page);
    if (items.length === 0) return;
    yield items;
  }
}

for await (const batch of pages(p => api.list(p))) {
  render(batch);
}
```

---

## D. Red flags

- "`let` and `const` aren't hoisted." — *Say instead:* "They are hoisted but uninitialised; accessing them before the declaration is a TDZ `ReferenceError`."
- "Arrow functions bind `this` to the object." — *Say instead:* "Arrows have no own `this`; they capture it lexically from where they're defined."
- "`class` is just syntactic sugar." — *Say instead:* "It's built on prototypes, but adds real semantics: strict mode, `new`-only constructors, `super`, private fields."
- "`setTimeout(fn, 0)` runs immediately / next." — *Say instead:* "It queues a task; all pending microtasks, and possibly a render, run first."
- "`async/await` makes code run in parallel / on another thread." — *Say instead:* "It's syntax over promises on the same thread; parallelism comes from starting operations before awaiting them."
- "`Promise.all` cancels the other requests when one fails." — *Say instead:* "It rejects fast but doesn't cancel; I use `AbortController` or RxJS unsubscription for that."
- "I deep-clone state with `JSON.parse(JSON.stringify())`." — *Say instead:* "I copy only the changed path; if I truly need a deep clone, `structuredClone`, knowing it drops prototypes and can't clone functions."
- "Object spread is ES6." — *Say instead:* "Array spread is ES2015; object spread/rest is ES2018."
- "I use `==` when I know the types." — *Say instead:* "`===` always, enforced by lint; `x == null` only if the team's style explicitly allows it."
- "`typeof` tells me if something is an array/null." — *Say instead:* "`Array.isArray` and `=== null`; `typeof null` is `'object'` for historical reasons."
- "Memory leaks don't happen in JS because of GC." — *Say instead:* "GC only frees unreachable objects; closures, listeners, timers and subscriptions keep things reachable — I clean up with `DestroyRef`/`takeUntilDestroyed`."
- "Zone.js runs change detection after every `setTimeout`, so I don't need to think about it." — *Say instead:* "That was the zone-based model; new apps have been zoneless by default since v21, so updates are driven by signals, `markForCheck` and template events."

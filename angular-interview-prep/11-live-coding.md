# 11 — Live Coding

> Ten tasks that come up in senior Angular live-coding rounds, each written up the way you would work it in the room: the prompt as the interviewer would say it, the clarifying questions to ask, a complete solution in current Angular 22 style, the reasoning behind it, edge cases and tests, likely follow-ups, and a time box. Don't memorise the code. Practise the **routine** until it's automatic, and use the solutions to check your own attempts. At senior level the interviewer already assumes you can write a component. What they're checking is whether you **scope the problem, deliver something working early, make trade-offs out loud, and think about tests, a11y, performance and API design** without being prompted. Treat that as the bar you're aiming for.
>
> Version note: all code targets **Angular 22.x** (standalone, `inject()`, signals, `input()/output()/model()`, `@if/@for` with `track`, zoneless by default since v21). Since v22, components with no `changeDetection` are OnPush by default. The solutions still write `ChangeDetectionStrategy.OnPush` explicitly. That makes the intent obvious to reviewers, it behaves the same when copied into a v20/v21 codebase (where the default was still `Default`, now called `Eager`), and interviewers like to hear you give that reason.

---

## How senior live-coding is assessed

What interviewers actually score (roughly in order of weight):

| Signal | What "strong" looks like | What "weak" looks like |
|---|---|---|
| **Problem framing** | 2–4 targeted clarifying questions, then state the assumptions out loud and write them as a comment at the top | Starts typing right away, or asks 15 questions and burns 10 minutes |
| **Incremental delivery** | Has a working (even ugly) version by the halfway mark, then improves it | Designs the perfect abstraction and has nothing running at the end |
| **Narrated trade-offs** | "I'll use `switchMap` because stale results are worse than wasted requests; `exhaustMap` would be right for a submit button." | Codes in silence, or narrates *what* ("now I type a map") instead of *why* |
| **Correctness under edge cases** | Names empty/error/loading, cancellation, destroy/cleanup, a11y, race conditions | Only the happy path |
| **Testing mindset** | Says what they'd test and writes one meaningful test if there's time | "I'd add tests later" |
| **Current idioms** | Signals, `inject()`, control flow, functional interceptors/effects. Knows what changed across versions | NgModules, `*ngFor` without trackBy, constructor-injection soup, `any` everywhere |
| **Collaboration** | Takes hints gracefully, checks in ("Does this API shape match what you had in mind?") | Defensive, or ignores the interviewer's nudges |
| **Time management** | Checks the clock, tells the interviewer what they're dropping ("I'll skip styling and do keyboard support instead") | Runs out of time mid-refactor with nothing working |

Sound bite to open with: *"Let me restate the problem, ask a couple of questions, then get a simple version working before I optimise. I'll talk as I go, so stop me if I'm heading somewhere you don't care about."*

### The 5-step routine

1. **Restate and clarify (2–4 min).** Repeat the task in one sentence. Ask about inputs/outputs, scale, error behaviour, and constraints like library, version and zoneless. Write the assumptions as a comment at the top of the file.
2. **Sketch the shape (2–3 min).** Say out loud, or type as comments, the public API (inputs/outputs/method signatures) and the data flow. For RxJS, name the operators before writing them. For components, name the state signals.
3. **Make it work (≈50% of the time box).** Happy path first, and get it running. Hard-code whatever isn't central. Say "I'm hard-coding X for now, I'll come back to it" so it doesn't look like a gap.
4. **Make it right (≈30%).** Error and loading states, cleanup, cancellation, a11y, typing, and one or two edge cases. Refactor names.
5. **Prove it and extend (≈20%).** Write or describe tests, walk through complexity and performance, and mention what you'd do with more time (follow-ups). Leave 2–3 minutes for their questions.

### Common failure modes

- **Silent coding.** The interviewer can't give you credit for reasoning they can't hear.
- **Gold-plating early.** Generic types, config objects and abstractions before anything renders.
- **Not running the code.** If there's a runnable environment, run it often. A red error you fix calmly counts in your favour.
- **Fighting the hint.** When the interviewer says "what if the user types fast?", they're pointing at a bug. Take it.
- **Legacy reflexes.** `@Input()` plus `ngOnChanges` plus manual `subscribe` plus `ngOnDestroy` everywhere. It's fine if their codebase is older, but say you know the modern equivalent.
- **Forgetting cleanup.** Subscriptions, timers, and listeners on `window`.
- **Ignoring a11y.** For a component-library owner this matters: roles, keyboard support, labels and focus management are expected.
- **Over-explaining basics / under-explaining decisions.** Skip "a component is a class". Do explain "why OnPush-safe" and "why `switchMap`".
- **No time check.** Say "I've got about 10 minutes left, so I'll prioritise X over Y."

---

## Task 1 — Debounced typeahead search

**Time box:** 25–30 min (RxJS version 15–20, signal alternative 5, test 5).

### Prompt

> "We have a user search box. As the user types, call `GET /api/users?q=...` and show matching names. Don't hammer the API, ignore very short input, and make sure results never show up out of order. Show loading and error states."

Starter:

```ts
export interface User { id: number; name: string; }
// GET /api/users?q=ang -> User[]
```

### Clarifying questions

- Minimum characters before searching? Debounce duration? (Assume 2 chars, 300 ms.)
- When the input is cleared or drops below the minimum, should results clear or stay? (Assume clear.)
- On error: show a message and keep the box usable? Retry? (Assume message, no auto-retry.)
- Keep previous results visible while loading, or show a spinner only? (Assume spinner, results cleared. Mention the alternative.)
- Reactive Forms or signals/Signal Forms in this codebase? (Show both.)

### Solution (RxJS + Reactive Forms)

```ts
// user-search.ts
import { ChangeDetectionStrategy, Component, Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import {
  Observable, catchError, debounceTime, distinctUntilChanged, map, of, startWith, switchMap,
} from 'rxjs';

export interface User { id: number; name: string; }

export type SearchState =
  | { status: 'idle'; results: User[] }
  | { status: 'loading'; results: User[] }
  | { status: 'success'; results: User[] }
  | { status: 'error'; results: User[]; message: string };

// In v22 `@Service()` also works; @Injectable({providedIn:'root'}) is still fine.
@Injectable({ providedIn: 'root' })
export class UserApi {
  private readonly http = inject(HttpClient);
  search(q: string): Observable<User[]> {
    return this.http.get<User[]>('/api/users', { params: { q } });
  }
}

export const MIN_CHARS = 2;
const IDLE: SearchState = { status: 'idle', results: [] };

/** Pure pipeline: easy to unit test without TestBed. */
export function searchPipeline(
  terms$: Observable<string>,
  search: (q: string) => Observable<User[]>,
  dueTime = 300,
): Observable<SearchState> {
  return terms$.pipe(
    map((t) => t.trim()),
    debounceTime(dueTime),
    distinctUntilChanged(),
    switchMap((q) =>
      q.length < MIN_CHARS
        ? of(IDLE) // not filter(): see walkthrough
        : search(q).pipe(
            map((results): SearchState => ({ status: 'success', results })),
            // catchError INSIDE switchMap: an error kills only this inner stream,
            // the outer valueChanges stream keeps working.
            catchError(() =>
              of<SearchState>({ status: 'error', results: [], message: 'Search failed' }),
            ),
            startWith<SearchState>({ status: 'loading', results: [] }),
          ),
    ),
  );
}

@Component({
  selector: 'app-user-search',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule],
  template: `
    <label for="user-search">Search users</label>
    <input id="user-search" type="search" autocomplete="off" [formControl]="query" />

    <p role="status" aria-live="polite">
      @switch (state().status) {
        @case ('loading') { Searching… }
        @case ('error') { Search failed. Please try again. }
        @case ('success') { {{ state().results.length }} results }
      }
    </p>

    <ul>
      @for (user of state().results; track user.id) {
        <li>{{ user.name }}</li>
      } @empty {
        @if (state().status === 'success') { <li>No matches</li> }
      }
    </ul>
  `,
})
export class UserSearch {
  private readonly api = inject(UserApi);
  protected readonly query = new FormControl('', { nonNullable: true });

  protected readonly state = toSignal(
    searchPipeline(this.query.valueChanges, (q) => this.api.search(q)),
    { initialValue: IDLE },
  );
}
```

### Walkthrough

- **Operator order.** Trim first so `"ang "` and `"ang"` count as the same term. `debounceTime` before `distinctUntilChanged`, so we compare the *settled* value: typing `ang` → `angu` → `ang` inside 300 ms produces no request.
- **`switchMap`**: "Stale results are worse than a wasted request, so I cancel the previous one. With HttpClient, unsubscribing aborts the request (FetchBackend is the default in v22 and uses an AbortController). `concatMap` would queue, `mergeMap` would race and show results out of order, and `exhaustMap` would ignore new terms. That's right for a submit button, wrong here."
- **Why not `filter(q => q.length >= 2)`?** It's what the prompt hints at, but it has two bugs. Clearing the input leaves the old results on screen, and a request already in flight for `"ang"` isn't cancelled when the user deletes back to `"a"`, so its results arrive after the box is cleared. Mapping short terms to `of(IDLE)` inside `switchMap` handles both. Say this out loud, because the interviewer is often fishing for exactly this point.
- **`catchError` placement**: inside the inner observable. Put it on the outer stream and the first 500 error completes the whole search box for good.
- **`toSignal`** subscribes in an injection context and unsubscribes on destroy, so there's no manual teardown. The template reads a signal, so OnPush and zoneless work without `markForCheck`.
- **Discriminated union state** instead of three separate booleans. It makes impossible combinations like "loading and error at once" unrepresentable.
- **a11y**: a real `<label>`, `type="search"`, and a live region that already exists in the DOM before its text changes, so screen readers announce the update.

### Signal-based alternative (mention, 3–5 min)

```ts
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { debounceTime, distinctUntilChanged, map } from 'rxjs';

@Component({
  selector: 'app-user-search-signals',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <label for="q">Search users</label>
    <input id="q" #box type="search" [value]="query()" (input)="query.set(box.value)" />
    @if (results.isLoading()) { <p role="status">Searching…</p> }
    @if (results.error()) {
      <p role="alert">Search failed.</p>
    } @else {
      <ul>
        @for (u of results.value(); track u.id) { <li>{{ u.name }}</li> }
      </ul>
    }
  `,
})
export class UserSearchSignals {
  protected readonly query = signal('');

  // Signals have no time dimension, so debounce through RxJS and come back.
  private readonly term = toSignal(
    toObservable(this.query).pipe(map((q) => q.trim()), debounceTime(300), distinctUntilChanged()),
    { initialValue: '' },
  );

  // Returning undefined = "no request" (idle). A new term aborts the previous request.
  protected readonly results = httpResource<User[]>(
    () => {
      const q = this.term();
      return q.length >= 2 ? { url: '/api/users', params: { q } } : undefined;
    },
    { defaultValue: [] },
  );
}
```

- Say this: *"httpResource gives me loading/error/value signals and cancellation for free. I branch on `error()` before reading `value()`, because reading `value()` on a resource in error state can throw."*
- `rxResource({ params: () => this.term() || undefined, stream: ({ params }) => this.api.search(params) })` does the same if the service returns Observables. Note the option names are `params` and `stream` (they were `request` and `loader` in earlier versions).
- Signal Forms (stable in v22) have a `debounce` rule for field-level debouncing. It's worth mentioning if the codebase uses them.

### Edge cases & tests

- Typing fast → one request. Backspacing to the same term → no request. Clearing the input → idle and in-flight request cancelled. Error → next term still works. Special characters → `params` URL-encodes them. Whitespace-only input → idle.

```ts
// user-search.spec.ts (Vitest)
import { Subject, of, throwError, delay } from 'rxjs';
import { searchPipeline, SearchState, User } from './user-search';

describe('searchPipeline', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('debounces and cancels stale requests', () => {
    const terms = new Subject<string>();
    const search = vi.fn((q: string) => of<User[]>([{ id: 1, name: q }]).pipe(delay(1000)));
    const states: SearchState[] = [];
    searchPipeline(terms, search).subscribe((s) => states.push(s));

    terms.next('a'); terms.next('an'); terms.next('ang');
    vi.advanceTimersByTime(300);
    expect(search).toHaveBeenCalledTimes(1);
    expect(search).toHaveBeenCalledWith('ang');

    terms.next('angu');              // 'ang' still in flight
    vi.advanceTimersByTime(300);     // 'angu' starts, 'ang' is cancelled
    vi.advanceTimersByTime(1000);

    expect(states.filter((s) => s.status === 'success')).toEqual([
      { status: 'success', results: [{ id: 1, name: 'angu' }] },
    ]);
  });

  it('survives an error', () => {
    const terms = new Subject<string>();
    const search = vi.fn()
      .mockReturnValueOnce(throwError(() => new Error('500')))
      .mockReturnValue(of([]));
    const states: string[] = [];
    searchPipeline(terms, search).subscribe((s) => states.push(s.status));

    terms.next('foo'); vi.advanceTimersByTime(300);
    terms.next('bar'); vi.advanceTimersByTime(300);
    expect(states).toEqual(['loading', 'error', 'loading', 'success']);
  });
});
```

### Likely follow-ups

- **"Keep old results while loading?"** Carry the previous results into the loading state with `scan`, or keep a separate `lastResults` signal and dim the list while loading.
- **"Cache results?"** Keep a `Map<string, User[]>` in the service with a TTL, and return `of(cached)` inside `switchMap`. With httpResource, lean on HTTP caching headers.
- **"Why not debounce in the service?"** Debounce belongs to the UI interaction. The service stays a plain function of the query, which keeps it reusable and testable.
- **"How would you test timing without fake timers?"** RxJS `TestScheduler` marble tests. Fine for pure pipelines, but awkward once HttpClient is involved.
- **"Accessibility of an autocomplete?"** Use the combobox pattern (`role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant`) plus arrow-key navigation. In a real library I'd build on CDK/Angular ARIA primitives rather than hand-roll it.

---

## Task 2 — Custom form control: star rating

**Time box:** 30 min (CVA 20, Signal Forms version 5–7, test 3–5).

### Prompt

> "Build a star rating input, 1 to 5, that works with Reactive Forms: `<app-star-rating formControlName="rating" />`. It must support disabled state and be keyboard accessible. Then: we're moving to Signal Forms. What changes?"

### Clarifying questions

- Is 0 ("no rating") a valid value, or should that be `null`? (Assume 0 means unset.)
- Half stars? (Assume no.)
- Is the number of stars configurable? (Yes, input.)
- When should the control be marked touched: on blur of the whole group or on each click? (Group blur, which matches native inputs.)
- Can the user clear a rating by clicking the selected star again? (Assume no. Mention it as an option.)

### Solution (ControlValueAccessor)

```ts
// star-rating.ts
import {
  ChangeDetectionStrategy, Component, ElementRef, computed, forwardRef, inject, input, signal, viewChildren,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-star-rating',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => StarRating), multi: true }],
  host: {
    role: 'radiogroup',
    '[attr.aria-label]': 'label()',
    '[attr.aria-disabled]': 'disabled() || null',
    '(focusout)': 'onFocusOut($event)',
  },
  template: `
    @for (star of stars(); track star) {
      <button #starBtn type="button" role="radio" class="star"
              [class.filled]="star <= value()"
              [attr.aria-checked]="star === value()"
              [attr.aria-label]="star + (star === 1 ? ' star' : ' stars')"
              [tabIndex]="star === focusStar() ? 0 : -1"
              [disabled]="disabled()"
              (click)="select(star)"
              (keydown)="onKeydown($event, star)">
        <span aria-hidden="true">★</span>
      </button>
    }
  `,
  styles: `
    :host { display: inline-flex; gap: 0.25rem; }
    .star { background: none; border: 0; font-size: 1.5rem; color: var(--star-empty, #bbb); cursor: pointer; }
    .star.filled { color: var(--star-filled, #f5a623); }
    .star:focus-visible { outline: 2px solid var(--focus-ring, #1a73e8); outline-offset: 2px; }
    .star:disabled { cursor: not-allowed; opacity: 0.5; }
  `,
})
export class StarRating implements ControlValueAccessor {
  readonly count = input(5);
  readonly label = input('Rating');

  protected readonly value = signal(0);
  protected readonly disabled = signal(false);
  protected readonly stars = computed(() => Array.from({ length: this.count() }, (_, i) => i + 1));
  // Roving tabindex: exactly one star is tabbable (the selected one, or the first).
  protected readonly focusStar = computed(() => this.value() || 1);

  private readonly buttons = viewChildren<ElementRef<HTMLButtonElement>>('starBtn');
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  private onChange: (value: number) => void = () => {};
  private onTouched: () => void = () => {};

  // --- ControlValueAccessor ---
  writeValue(value: number | null): void {
    // Model -> view. Must NOT call onChange (that would echo back and mark dirty).
    const v = value ?? 0;
    this.value.set(Math.min(Math.max(v, 0), this.count()));
  }
  registerOnChange(fn: (value: number) => void): void { this.onChange = fn; }
  registerOnTouched(fn: () => void): void { this.onTouched = fn; }
  setDisabledState(isDisabled: boolean): void { this.disabled.set(isDisabled); }

  // --- UI ---
  protected select(star: number): void {
    if (this.disabled() || star === this.value()) return;
    this.value.set(star);
    this.onChange(star); // View -> model
  }

  protected onKeydown(event: KeyboardEvent, star: number): void {
    const last = this.count();
    const moves: Record<string, number> = {
      ArrowRight: star + 1, ArrowUp: star + 1,
      ArrowLeft: star - 1, ArrowDown: star - 1,
      Home: 1, End: last,
    };
    const next = moves[event.key];
    if (next === undefined) return;       // Space/Enter handled natively by <button>
    event.preventDefault();               // stop page scroll on arrows
    const target = next > last ? 1 : next < 1 ? last : next; // wrap like native radios
    this.select(target);
    this.buttons()[target - 1]?.nativeElement.focus();
  }

  protected onFocusOut(event: FocusEvent): void {
    // Touched when focus leaves the whole group, not when moving between stars.
    if (!this.host.nativeElement.contains(event.relatedTarget as Node | null)) this.onTouched();
  }
}
```

### Walkthrough

- **The CVA contract**: `writeValue` means model → view, and it must not call `onChange`. `registerOnChange` and `registerOnTouched` store callbacks. `setDisabledState` is called for `control.disable()` and for the `[disabled]` binding.
- **Why internal state is signals**: under OnPush, `writeValue` is called from outside the template, by the forms directive. With a plain field I'd need `cdr.markForCheck()` in `writeValue`, which is a classic bug in older CVAs. Signals mark the view for me, and that also works zoneless.
- **`forwardRef`**: the provider references the class inside its own decorator.
- **a11y**: this follows the WAI-ARIA radio group pattern. `role="radiogroup"` has a label, each star is `role="radio"` with `aria-checked`, and roving tabindex means Tab enters and leaves the group in one stop. Arrows move *and* select, as with native radios. Home/End work and the focus ring is visible. The glyph is `aria-hidden` and each button has a text label. Using real `<button>`s gives focusability, Space/Enter and the disabled semantics for free.
- **Clamping** in `writeValue` guards against bad data from the server.
- The input is named `count`, not `max`, deliberately. See the Signal Forms note below.

### Signal Forms version (v22 stable)

With Signal Forms the control doesn't implement CVA. It implements `FormValueControl<T>` by exposing a `value` model. The `[formField]` directive binds to it, and it also binds optional state inputs such as `disabled` and `touched` when the control declares them; to report a touch back it exposes a `touch` output (per the v22 `FormUiControl` interface).

```ts
// star-rating-field.ts
import { ChangeDetectionStrategy, Component, computed, input, model, output } from '@angular/core';
import { FormValueControl } from '@angular/forms/signals';

@Component({
  selector: 'app-star-rating-field',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    role: 'radiogroup',
    '[attr.aria-label]': 'label()',
    '(focusout)': 'touch.emit()', // simplified; reuse the relatedTarget check above
  },
  template: `
    @for (star of stars(); track star) {
      <button type="button" role="radio"
              [attr.aria-checked]="star === value()"
              [attr.aria-label]="star + ' stars'"
              [tabIndex]="star === (value() || 1) ? 0 : -1"
              [disabled]="disabled()"
              (click)="value.set(star)">★</button>
    }
  `,
})
export class StarRatingField implements FormValueControl<number> {
  readonly value = model(0);        // the only required member
  readonly disabled = input(false); // optional: bound by [formField] from field state
  readonly touched = input(false);  // optional: current touched state from the field
  readonly touch = output<void>();   // optional: tell the field the user touched the control
  readonly count = input(5);
  readonly label = input('Rating');
  protected readonly stars = computed(() => Array.from({ length: this.count() }, (_, i) => i + 1));
}
```

```ts
// review-form.ts
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { FormField, form, min } from '@angular/forms/signals';
import { StarRatingField } from './star-rating-field';

@Component({
  selector: 'app-review-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormField, StarRatingField],
  template: `
    <app-star-rating-field [formField]="reviewForm.rating" label="Overall rating" />
    @if (reviewForm.rating().touched() && reviewForm.rating().invalid()) {
      <p role="alert">Please pick at least one star.</p>
    }
  `,
})
export class ReviewForm {
  protected readonly review = signal({ rating: 0, comment: '' });
  protected readonly reviewForm = form(this.review, (p) => {
    min(p.rating, 1);
  });
}
```

- **What changed**: no provider, no callbacks, no `setDisabledState`. The control only exposes signals, and the field owns validation and state. Sound bite: *"The two-way `model()` replaces the whole CVA callback dance."*
- **Why `count` and not `max`**: the form-control interface can also accept constraint inputs such as `min`/`max` that `[formField]` fills from the schema. An input named `max` meaning "number of stars" would collide with the field's validation max.
- **Migration**: Signal Forms can interoperate with existing CVAs, so a component library can migrate one control at a time. As library owner I'd ship both for a release or two.

### Edge cases & tests

- `writeValue(null)` gives 0. An out-of-range value is clamped. Disabled means no clicks and no keyboard changes. Touched is set only when focus leaves the group. Arrow keys wrap. In an RTL layout, Left/Right should flip (check `dir`).

```ts
// star-rating.spec.ts
import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { StarRating } from './star-rating';

@Component({
  imports: [ReactiveFormsModule, StarRating],
  template: `<app-star-rating [formControl]="ctrl" />`,
})
class Host { ctrl = new FormControl(3, { nonNullable: true }); }

it('writes, emits and disables', async () => {
  const fixture = TestBed.createComponent(Host);
  await fixture.whenStable();
  const radios: HTMLButtonElement[] = Array.from(fixture.nativeElement.querySelectorAll('[role=radio]'));

  expect(radios[2].getAttribute('aria-checked')).toBe('true');   // model -> view
  radios[4].click();
  expect(fixture.componentInstance.ctrl.value).toBe(5);           // view -> model

  fixture.componentInstance.ctrl.disable();
  await fixture.whenStable();
  expect(radios.every((r) => r.disabled)).toBe(true);
});
```

### Likely follow-ups

- **"Validation inside the control?"** Implement `Validator` via `NG_VALIDATORS`, for example "required means > 0". I usually prefer validators on the form, because the control shouldn't own business rules.
- **"Why not `@Input() value` + `@Output() valueChange`?"** That only gives two-way binding. It doesn't integrate with `FormControl` status, disabled or touched. The Signal Forms `model()` is effectively that pattern, formalised.
- **"Hover preview?"** Add a `hovered = signal<number | null>(null)` and a computed `display = hovered() ?? value()`. It's purely visual, so it never touches the model.
- **"How would you document this in a component library?"** A Storybook story for each state, an a11y checklist (axe in CI), and a note on keyboard behaviour. Show `formControlName` and `[formField]` usage side by side.

---

## Task 3 — OnPush bug hunt

**Time box:** 15–20 min.

### Prompt

> "This cart summary sometimes doesn't update: adding an item, renaming the customer, the status after load, and the total. Sometimes it 'fixes itself' when you click somewhere. Explain why and fix it."

```ts
// BUGGY
@Component({
  selector: 'app-cart-summary',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h2>{{ customer.name }}: {{ items.length }} items</h2>
    <p>Status: {{ status }}</p>
    <p>Total: {{ total }}</p>
    <button (click)="noop()">Refresh</button>
  `,
})
export class CartSummary implements OnInit {
  @Input() items: CartItem[] = [];
  @Input() customer!: Customer;
  status = 'loading';
  total = 0;
  private readonly pricing = inject(PricingService);

  ngOnInit() {
    setTimeout(() => (this.status = 'ready'), 500);
    this.pricing.total$.subscribe((t) => (this.total = t));
  }
  noop() {}
}

// Parent
addItem(item: CartItem) { this.items.push(item); }
rename(name: string) { this.customer.name = name; }
```

### Clarifying questions

- Is the app zone-based or zoneless? (It changes *why* the timer case fails.) Which Angular version?
- Does the parent own the state, or does a store?
- Can I change the parent, or only this component?

### Diagnosis (say this before fixing)

An OnPush component is re-checked only when it's **marked dirty**, which happens when:
1. An `@Input`/`input()` receives a **new reference** (compared with `Object.is`),
2. A template or host event handler runs in the component or a descendant,
3. A signal read in its template changes,
4. The `async` pipe receives a value, or code calls `markForCheck()`.

| Symptom | Why |
|---|---|
| `items.push` not shown | Same array reference, so the input binding doesn't change and the component isn't marked. |
| `customer.name = ...` not shown | Same object reference, so the same reason. |
| `status` after `setTimeout` | Plain field assignment marks nothing. **With zone.js**, the timer triggers an app tick, but this OnPush view isn't dirty, so it's skipped. **Zoneless** (the default for new apps since v21), nothing schedules change detection at all. |
| `total` from `subscribe` | Same as above: an assignment in a callback marks nothing. |
| "Fixes itself on click" | The `(click)` handler marks the view dirty, so the next check picks up *all* the stale values. That makes the bug look random. |

Version notes worth saying: *"Since v22, a component without `changeDetection` is OnPush by default, so this bug shows up after an upgrade even if nobody wrote OnPush. The `ng update` migration adds `ChangeDetectionStrategy.Eager` (the new name for the deprecated `Default`) to preserve the old behaviour. `Eager` isn't a real fix, though: in a zoneless app a field assigned in a `setTimeout` still won't render, because nothing notifies Angular."*

### Fix 1: minimal, works on any version

```ts
@Component({
  selector: 'app-cart-summary',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AsyncPipe],
  template: `
    <h2>{{ customer.name }}: {{ items.length }} items</h2>
    <p>Status: {{ status }}</p>
    <p>Total: {{ total$ | async }}</p>
  `,
})
export class CartSummary implements OnInit {
  @Input() items: readonly CartItem[] = [];
  @Input() customer!: Customer;
  status = 'loading';
  protected readonly total$ = inject(PricingService).total$; // async pipe marks for check + unsubscribes
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);

  ngOnInit() {
    const id = setTimeout(() => {
      this.status = 'ready';
      this.cdr.markForCheck();                        // explicit notification
    }, 500);
    this.destroyRef.onDestroy(() => clearTimeout(id));
  }
}

// Parent: immutable updates produce new references
addItem(item: CartItem) { this.items = [...this.items, item]; }
rename(name: string) { this.customer = { ...this.customer, name }; }
```

### Fix 2: signals (preferred for new code)

```ts
@Component({
  selector: 'app-cart-summary',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h2>{{ customer().name }}: {{ count() }} items</h2>
    <p>Status: {{ status() }}</p>
    <p>Total: {{ total() }}</p>
  `,
})
export class CartSummary {
  readonly items = input.required<readonly CartItem[]>();
  readonly customer = input.required<Customer>();
  protected readonly count = computed(() => this.items().length);
  protected readonly status = signal<'loading' | 'ready'>('loading');
  protected readonly total = toSignal(inject(PricingService).total$, { initialValue: 0 });

  constructor() {
    const id = setTimeout(() => this.status.set('ready'), 500);
    inject(DestroyRef).onDestroy(() => clearTimeout(id));
  }
}

// Parent
readonly items = signal<readonly CartItem[]>([]);
readonly customer = signal<Customer>({ id: 1, name: 'Ada' });
addItem(item: CartItem) { this.items.update((xs) => [...xs, item]); }
rename(name: string) { this.customer.update((c) => ({ ...c, name })); }
// template: <app-cart-summary [items]="items()" [customer]="customer()" />
```

### Walkthrough

- Fix 1 keeps the mental model of "notify Angular explicitly". Fix 2 makes notification automatic: any signal read in the template registers the view as a consumer, and that works zoneless.
- **Trap inside the signals fix**: `this.items.update(xs => { xs.push(i); return xs; })` still fails, because signals use `Object.is` equality too. Immutability still matters.
- Typing inputs as `readonly CartItem[]` makes accidental `push` a compile error. That's a cheap guardrail I'd add across a shared library.
- The timer cleanup isn't part of the bug, but it's a leak you'd be marked down for ignoring.

### Edge cases & tests

- A regression test for each symptom. For example, the parent adds an item and `await fixture.whenStable()`, and the count text updates. Run tests zoneless, the Vitest default for new projects, so this class of bug fails in CI rather than in production.

```ts
it('updates count when parent adds an item', async () => {
  const fixture = TestBed.createComponent(CartHost); // host with items signal + addItem()
  await fixture.whenStable();
  fixture.componentInstance.addItem({ id: 2, price: 10 });
  await fixture.whenStable();
  expect(fixture.nativeElement.textContent).toContain('2 items');
});
```

### Likely follow-ups

- **"Is `detectChanges()` a valid fix?"** It forces a synchronous check of this view. It's a smell in app code, fine in tests and some third-party integrations. `markForCheck()` schedules; `detectChanges()` runs immediately.
- **"Why OnPush at all?"** It skips whole subtrees that have no changed inputs or signals. At enterprise scale with big tables and dashboards, that's the difference between a 2 ms and a 40 ms check. It also enforces a unidirectional data flow.
- **"How do you roll this out in a large codebase?"** Enable OnPush per feature, add a lint rule for mutation (for example readonly types, or a rule against `push` on inputs), and use zoneless tests as the safety net.

---

## Task 4 — Fix the memory leaks

**Time box:** 20 min.

### Prompt

> "Users report the order dashboard gets slower the longer they navigate around. Here's the component. Find the problems and fix them. Then tell me how you'd prove the leak is gone."

```ts
// BUGGY
@Component({
  selector: 'app-order-dashboard',
  template: `<h1>{{ order?.id }}</h1><p>{{ user?.name }}</p>@if (isNarrow) { <p>Compact</p> }`,
})
export class OrderDashboard implements OnInit {
  private readonly api = inject(OrderApi);
  private readonly route = inject(ActivatedRoute);
  private readonly store = inject(Store);
  order?: Order;
  user?: User;
  isNarrow = false;

  ngOnInit() {
    interval(10_000).subscribe(() => this.api.ping().subscribe());
    this.route.paramMap.subscribe((params) => {
      this.api.getOrder(params.get('id')!).subscribe((o) => (this.order = o));
    });
    window.addEventListener('resize', () => (this.isNarrow = window.innerWidth < 768));
    this.store.select(selectCurrentUser).subscribe((u) => (this.user = u));
  }
}
```

### Clarifying questions

- Is it SSR-rendered? (`window` access matters.)
- Should polling pause when the tab is hidden?
- Zoneless? (Also explains why the fields don't render. See Task 3.)

### Problems

1. **`interval` never completes.** After navigating away it keeps firing, and its closure keeps `this` alive, so the component and its whole DOM tree stay in memory. Each visit adds another poller.
2. **Nested subscribe.** There's no cancellation when `id` changes, so a slow earlier response can overwrite a newer order (a race). There's also no error handling. Router-owned `ActivatedRoute` observables are cleaned up by the router, so the *outer* one isn't the leak, but the pattern is wrong anyway.
3. **Anonymous `window` listener.** It can't be removed. `window` lives forever, so it retains the closure, which retains the component: a classic *detached DOM* leak.
4. **`store.select` never completes.** The store is a root singleton holding a reference to our subscriber.

### Solution

```ts
import {
  ChangeDetectionStrategy, Component, DestroyRef, inject, signal,
} from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { Store } from '@ngrx/store';
import { distinctUntilChanged, interval, map, switchMap } from 'rxjs';

@Component({
  selector: 'app-order-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1>{{ order()?.id }}</h1>
    <p>{{ user()?.name }}</p>
    @if (isNarrow()) { <p>Compact</p> }
  `,
})
export class OrderDashboard {
  private readonly api = inject(OrderApi);
  private readonly route = inject(ActivatedRoute);
  private readonly store = inject(Store);
  private readonly destroyRef = inject(DestroyRef);

  // 4. Store: selectSignal owns the subscription lifecycle for us.
  protected readonly user = this.store.selectSignal(selectCurrentUser);

  // 2. Flatten with switchMap (cancels stale requests); toSignal unsubscribes on destroy.
  protected readonly order = toSignal(
    this.route.paramMap.pipe(
      map((p) => p.get('id')!),
      distinctUntilChanged(),
      switchMap((id) => this.api.getOrder(id)),
    ),
  );

  protected readonly isNarrow = signal(false);

  constructor() {
    // 1. takeUntilDestroyed() in an injection context; keep it LAST in the pipe.
    interval(10_000)
      .pipe(switchMap(() => this.api.ping()), takeUntilDestroyed())
      .subscribe();

    // 3. matchMedia beats resize (fires only at the breakpoint), guarded for SSR,
    //    and removed via DestroyRef.
    const win = inject(DOCUMENT).defaultView;
    if (win) {
      const mql = win.matchMedia('(max-width: 767px)');
      this.isNarrow.set(mql.matches);
      const onChange = (e: MediaQueryListEvent) => this.isNarrow.set(e.matches);
      mql.addEventListener('change', onChange);
      this.destroyRef.onDestroy(() => mql.removeEventListener('change', onChange));
    }
  }

  // Outside the constructor there is no injection context, so pass destroyRef explicitly.
  startExtraPolling() {
    interval(1000).pipe(takeUntilDestroyed(this.destroyRef)).subscribe();
  }
}
```

Alternatives to mention for the listener:

```ts
// a) Declarative host listener: Angular removes it on destroy
host: { '(window:resize)': 'onResize()' }

// b) Many listeners at once: one AbortController
const ac = new AbortController();
window.addEventListener('resize', onResize, { signal: ac.signal });
window.addEventListener('scroll', onScroll, { signal: ac.signal, passive: true });
inject(DestroyRef).onDestroy(() => ac.abort());
```

(CDK's `BreakpointObserver` is another good answer for breakpoints.)

### Walkthrough

- **Order of preference**: *declarative* first (async pipe, `toSignal`, `selectSignal`, host listeners), because the framework owns the lifecycle. Then `takeUntilDestroyed` for side-effect subscriptions. Then `DestroyRef.onDestroy` for non-RxJS resources like DOM listeners, third-party widgets, timers and observers (ResizeObserver, IntersectionObserver).
- **Why `takeUntilDestroyed` last**: an operator after it, such as a `switchMap` into a new inner stream, could open a subscription that the teardown doesn't cover.
- **Things that don't need unsubscribing**: a single HttpClient call (it completes), `ActivatedRoute` streams, `async`/`toSignal`. I'd still avoid nested subscribes for correctness reasons.
- **Zone note**: with zone.js, every `resize` event triggers an app-wide tick. `matchMedia` fires once per breakpoint crossing, which is a nice side win.

### How to detect and prove the leak

- **Reproduce**: navigate to the dashboard and away N times (say 10), force GC (the trash-can icon), then take a **heap snapshot**. Repeat, and use the **Comparison** view between snapshots. Growth in `OrderDashboard` instances or `Detached HTMLDivElement` counts that scales with N is the leak.
- **Detached DOM**: in the Memory panel, filter the snapshot by "Detached". The **Retainers** pane shows the chain, for example `window → listener → closure → OrderDashboard → host element`.
- **Performance monitor** (DevTools → More tools): watch *JS heap size*, *DOM Nodes* and *JS event listeners* while navigating. Leaks show up as a sawtooth that never returns to baseline.
- `getEventListeners(window)` in the DevTools console lists the attached listeners.
- **Automate**: a Playwright script that loops the navigation and asserts heap or listener counts, or Meta's `memlab` for leak detection in CI. For unit level, a test that destroys the fixture and asserts that the spy (`ping`) isn't called after advancing fake timers.

### Likely follow-ups

- **"Pause polling when the tab is hidden?"** Use `fromEvent(document, 'visibilitychange')` mapped to `document.visibilityState`, and `switchMap` to `interval` or `EMPTY`.
- **"takeUntil(destroy$) vs takeUntilDestroyed?"** Same idea, but `takeUntilDestroyed` removes the Subject and `ngOnDestroy` boilerplate and can't be forgotten in `ngOnDestroy`.
- **"Services leak too?"** Root services live for the app's lifetime, so subscriptions inside them are fine only if they're bounded. For services provided in a component or route, use `inject(DestroyRef)` there as well.

---

## Task 5 — NgRx feature slice: products

**Time box:** 35–40 min (store 25, component 5, SignalStore sketch 5).

### Prompt

> "Add a products feature to our NgRx store: load products from `GET /api/products` when the page opens, with loading and error states. Normalise the data. Show the list in a component."

### Clarifying questions

- Classic Store or SignalStore? Is the app already on classic Store? (Assume classic. Sketch SignalStore at the end.)
- Load every time the page opens, or cache? (Assume every time. Mention caching.)
- Is the feature lazily loaded? (Assume yes, so register state on the route.)
- What's the product id field, and do we need sorting? (`id: string`, sort by name.)

### Solution

```ts
// products.actions.ts
import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { Product } from './product.model';

export const ProductsPageActions = createActionGroup({
  source: 'Products Page',
  events: { Opened: emptyProps() },
});

export const ProductsApiActions = createActionGroup({
  source: 'Products API',
  events: {
    'Load Success': props<{ products: Product[] }>(),
    'Load Failure': props<{ error: string }>(),
  },
});
```

```ts
// products.feature.ts
import { createFeature, createReducer, createSelector, on } from '@ngrx/store';
import { EntityState, createEntityAdapter } from '@ngrx/entity';
import { Product } from './product.model';
import { ProductsApiActions, ProductsPageActions } from './products.actions';

type Status = 'idle' | 'loading' | 'loaded' | 'error';
interface ProductsState extends EntityState<Product> {
  status: Status;
  error: string | null;
}

const adapter = createEntityAdapter<Product>({
  sortComparer: (a, b) => a.name.localeCompare(b.name),
});

const initialState: ProductsState = adapter.getInitialState({ status: 'idle', error: null });

export const productsFeature = createFeature({
  name: 'products',
  reducer: createReducer(
    initialState,
    on(ProductsPageActions.opened, (s): ProductsState => ({ ...s, status: 'loading', error: null })),
    on(ProductsApiActions.loadSuccess, (s, { products }): ProductsState =>
      adapter.setAll(products, { ...s, status: 'loaded' })),
    on(ProductsApiActions.loadFailure, (s, { error }): ProductsState => ({ ...s, status: 'error', error })),
  ),
  extraSelectors: ({ selectProductsState, selectStatus }) => {
    const { selectAll, selectTotal } = adapter.getSelectors(selectProductsState);
    return {
      selectAllProducts: selectAll,     // renamed to avoid clashes across features
      selectProductCount: selectTotal,
      selectIsLoading: createSelector(selectStatus, (s) => s === 'loading'),
    };
  },
});
```

```ts
// products.effects.ts
import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, of, switchMap } from 'rxjs';
import { ProductsApi } from './products.api';
import { ProductsApiActions, ProductsPageActions } from './products.actions';

export const loadProducts = createEffect(
  (actions$ = inject(Actions), api = inject(ProductsApi)) =>
    actions$.pipe(
      ofType(ProductsPageActions.opened),
      switchMap(() =>
        api.getAll().pipe(
          map((products) => ProductsApiActions.loadSuccess({ products })),
          // Inside the inner stream, otherwise the effect dies on the first error.
          catchError((e: unknown) =>
            of(ProductsApiActions.loadFailure({ error: e instanceof Error ? e.message : 'Unknown error' })),
          ),
        ),
      ),
    ),
  { functional: true },
);
```

```ts
// products.routes.ts
import { Routes } from '@angular/router';
import { provideState } from '@ngrx/store';
import { provideEffects } from '@ngrx/effects';
import { productsFeature } from './products.feature';
import * as productsEffects from './products.effects';

export const PRODUCTS_ROUTES: Routes = [
  {
    path: '',
    providers: [provideState(productsFeature), provideEffects(productsEffects)],
    loadComponent: () => import('./product-list').then((m) => m.ProductList),
  },
];
// app.config.ts: provideStore(), provideEffects() at root (plus provideStoreDevtools in dev)
```

```ts
// product-list.ts
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { CurrencyPipe } from '@angular/common';
import { productsFeature } from './products.feature';
import { ProductsPageActions } from './products.actions';

@Component({
  selector: 'app-product-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CurrencyPipe],
  template: `
    @if (isLoading()) { <p role="status">Loading products…</p> }
    @if (error(); as error) { <p role="alert">{{ error }}</p> }
    <ul>
      @for (p of products(); track p.id) {
        <li>{{ p.name }}: {{ p.price | currency }}</li>
      } @empty {
        @if (!isLoading() && !error()) { <li>No products</li> }
      }
    </ul>
  `,
})
export class ProductList {
  private readonly store = inject(Store);
  protected readonly products = this.store.selectSignal(productsFeature.selectAllProducts);
  protected readonly isLoading = this.store.selectSignal(productsFeature.selectIsLoading);
  protected readonly error = this.store.selectSignal(productsFeature.selectError);

  constructor() {
    this.store.dispatch(ProductsPageActions.opened());
  }
}
```

### Walkthrough

- **Actions as events, not commands**: `[Products Page] Opened` describes what happened, and the effect decides what to do. That's good action hygiene: the source makes DevTools logs readable, and several reducers or effects can react to one event.
- **`createFeature`** generates `selectProductsState`, `selectStatus`, `selectError` and so on. `extraSelectors` adds the entity selectors and derived flags. Selectors are memoised.
- **Entity adapter**: normalised `ids`/`entities`, O(1) lookup by id, and `setAll`/`upsertMany`/`updateOne` without hand-written immutable spreads. `sortComparer` keeps `ids` sorted on write, so there's no need to sort on every read.
- **`switchMap` in the effect**: reopening the page cancels the previous load. For a "save" effect I'd use `concatMap` (ordering) or `exhaustMap` (ignore double-submit).
- **Functional effect** with `inject()` default parameters. That makes it trivially testable by passing fakes directly.
- **Route-level `provideState`**: the slice is registered only when the lazy route loads, which keeps the root store small.
- **`selectSignal`**: no async pipe, OnPush and zoneless friendly.

### Edge cases & tests

- Error message mapping, a double open (cancel the first), stale data on re-entry (show the cached list and refresh in the background?), and an empty list compared with an error.

```ts
// products.spec.ts
import { Actions } from '@ngrx/effects';
import { of, throwError } from 'rxjs';

it('reducer: success stores entities and status', () => {
  const state = productsFeature.reducer(undefined, ProductsApiActions.loadSuccess({
    products: [{ id: 'b', name: 'Bolt', price: 1 }, { id: 'a', name: 'Anvil', price: 9 }],
  }));
  expect(state.ids).toEqual(['a', 'b']); // sorted by name
  expect(state.status).toBe('loaded');
});

it('effect: maps API error to failure action', () => {
  const actions$ = new Actions(of(ProductsPageActions.opened()));
  const api = { getAll: () => throwError(() => new Error('boom')) } as unknown as ProductsApi;
  const emitted: unknown[] = [];
  loadProducts(actions$, api).subscribe((a) => emitted.push(a));
  expect(emitted).toEqual([ProductsApiActions.loadFailure({ error: 'boom' })]);
});
```

Selectors can be tested with `selector.projector(...)`. Components can use `provideMockStore({ selectors: [...] })`.

### SignalStore alternative (~20 lines)

```ts
import { computed, inject } from '@angular/core';
import { patchState, signalStore, withComputed, withHooks, withMethods, withState } from '@ngrx/signals';
import { setAllEntities, withEntities } from '@ngrx/signals/entities';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { tapResponse } from '@ngrx/operators';
import { pipe, switchMap, tap } from 'rxjs';

export const ProductsStore = signalStore(
  withEntities<Product>(),
  withState({ status: 'idle' as 'idle' | 'loading' | 'loaded' | 'error', error: null as string | null }),
  withComputed(({ status }) => ({ isLoading: computed(() => status() === 'loading') })),
  withMethods((store, api = inject(ProductsApi)) => ({
    load: rxMethod<void>(pipe(
      tap(() => patchState(store, { status: 'loading', error: null })),
      switchMap(() => api.getAll().pipe(tapResponse({
        next: (products) => patchState(store, setAllEntities(products), { status: 'loaded' }),
        error: (e: Error) => patchState(store, { status: 'error', error: e.message }),
      }))),
    )),
  })),
  withHooks({ onInit: (store) => store.load() }),
);
// Component: providers: [ProductsStore]; store = inject(ProductsStore); store.entities(), store.isLoading()
```

- How I'd choose: *"Global, cross-feature state with an audit trail, DevTools time travel and many event consumers means classic Store. Feature-local state that should die with the page means SignalStore: less ceremony and signals native. With NgRx 22, SignalStore's events plugin gives Redux-style events if we want that discipline without the global store."*

### Likely follow-ups

- **"Caching / don't refetch?"** Add a `loadedAt` field and have the effect check it with `concatLatestFrom(() => store.select(selectLoadedAt))` and `filter`. Or dispatch only when `status === 'idle'`.
- **"Optimistic update?"** Update the entity immediately. On failure, dispatch a rollback carrying the previous entity (keep it in the action payload).
- **"Where does derived data go?"** Selectors or `computed`, never stored state.
- **"Why is Redux worth it at all?"** Predictable single-direction flow, easy auditing and debugging, and decoupled features. The cost is boilerplate and indirection, so I don't put form state or ephemeral UI state in it.

---

## Task 6 — Generic reusable table component

**Time box:** 40 min (basic render 15, custom cells 10, sort 10, a11y and API talk 5).

### Prompt

> "You own the shared component library. Build a data table that works with any row type: configurable columns, optional custom cell templates, client-side sorting, and an empty state. Other teams will use it, so think about the API."

### Clarifying questions

- Client- or server-side sorting? (Client now. Design so server-side can plug in: sort state as a `model`.)
- Data size? (If over ~1–2k rows, we need virtualisation or pagination. See Task 7.)
- Selection, pagination, sticky headers? (Out of scope. Mention as extension points.)
- Are there design tokens or theming conventions to follow? (Use CSS custom properties.)
- Why not wrap `mat-table` / CDK table? (Good question to ask. The answer shows judgement: "if we already use CDK, I'd build on `CdkTable`; here I'll show the mechanics.")

### Solution

```ts
// data-table.ts
import {
  ChangeDetectionStrategy, Component, Directive, TemplateRef, computed, contentChildren, inject, input, model,
} from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';

export interface Column<T> {
  key: string;
  header: string;
  /** How to read the cell value; defaults to row[key]. */
  value?: (row: T) => unknown;
  sortable?: boolean;
  compare?: (a: T, b: T) => number;
}

export type SortDirection = 'asc' | 'desc';
export interface SortState { key: string; direction: SortDirection; }

export interface CellContext<T> { $implicit: T; value: unknown; }

/** <ng-template appCell="price" let-row let-value="value">…</ng-template> */
@Directive({ selector: 'ng-template[appCell]' })
export class CellDef<T = unknown> {
  readonly column = input.required<string>({ alias: 'appCell' });
  readonly template = inject<TemplateRef<CellContext<T>>>(TemplateRef);

  static ngTemplateContextGuard<T>(_dir: CellDef<T>, ctx: unknown): ctx is CellContext<T> {
    return true;
  }
}

const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });

function defaultCompare(a: unknown, b: unknown): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;               // nulls last
  if (b == null) return -1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  if (a instanceof Date && b instanceof Date) return a.getTime() - b.getTime();
  return collator.compare(String(a), String(b));
}

@Component({
  selector: 'app-data-table',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgTemplateOutlet],
  template: `
    <table class="dt">
      <caption [class.visually-hidden]="hideCaption()">{{ caption() }}</caption>
      <thead>
        <tr>
          @for (col of columns(); track col.key) {
            <th scope="col" [attr.aria-sort]="ariaSort(col.key)">
              @if (col.sortable) {
                <button type="button" class="dt-sort" (click)="toggleSort(col.key)">
                  {{ col.header }}
                  <span aria-hidden="true">{{ sortIcon(col.key) }}</span>
                </button>
              } @else {
                {{ col.header }}
              }
            </th>
          }
        </tr>
      </thead>
      <tbody>
        @for (row of sortedRows(); track rowKey()(row)) {
          <tr>
            @for (col of columns(); track col.key) {
              <td>
                @let tpl = cellTemplates().get(col.key);
                @if (tpl) {
                  <ng-container [ngTemplateOutlet]="tpl"
                                [ngTemplateOutletContext]="{ $implicit: row, value: cellValue(row, col) }" />
                } @else {
                  {{ cellValue(row, col) }}
                }
              </td>
            }
          </tr>
        } @empty {
          <tr>
            <td class="dt-empty" [attr.colspan]="columns().length">
              <ng-content select="[appTableEmpty]">No data</ng-content>
            </td>
          </tr>
        }
      </tbody>
    </table>
  `,
  styles: `
    .dt { width: 100%; border-collapse: collapse; }
    .dt th, .dt td { padding: var(--dt-cell-padding, 0.5rem); text-align: start; border-bottom: 1px solid var(--dt-border, #ddd); }
    .dt-sort { all: unset; cursor: pointer; font-weight: inherit; }
    .dt-sort:focus-visible { outline: 2px solid var(--focus-ring, #1a73e8); }
    .dt-empty { text-align: center; color: var(--dt-muted, #666); }
    .visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  `,
})
export class DataTable<T> {
  readonly rows = input.required<readonly T[]>();
  readonly columns = input.required<readonly Column<T>[]>();
  /** Stable identity per row: required on purpose (track). */
  readonly rowKey = input.required<(row: T) => string | number>();
  readonly caption = input.required<string>();
  readonly hideCaption = input(false);
  /** Two-way: parent can control or observe sort (e.g. for server-side sorting). */
  readonly sort = model<SortState | null>(null);
  /** Set false when the parent sorts on the server. */
  readonly clientSort = input(true);

  private readonly cellDefs = contentChildren(CellDef);
  protected readonly cellTemplates = computed(
    () => new Map(this.cellDefs().map((d) => [d.column(), d.template] as const)),
  );

  protected readonly sortedRows = computed(() => {
    const rows = this.rows();
    const sort = this.sort();
    if (!sort || !this.clientSort()) return rows;
    const col = this.columns().find((c) => c.key === sort.key);
    if (!col) return rows;
    const cmp = col.compare ?? ((a: T, b: T) => defaultCompare(this.cellValue(a, col), this.cellValue(b, col)));
    const dir = sort.direction === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => dir * cmp(a, b)); // copy: never mutate the input
  });

  protected cellValue(row: T, col: Column<T>): unknown {
    return col.value ? col.value(row) : (row as Record<string, unknown>)[col.key];
  }

  protected toggleSort(key: string): void {
    const cur = this.sort();
    // asc -> desc -> none
    this.sort.set(
      cur?.key !== key ? { key, direction: 'asc' }
      : cur.direction === 'asc' ? { key, direction: 'desc' }
      : null,
    );
  }

  protected ariaSort(key: string): 'ascending' | 'descending' | null {
    const s = this.sort();
    return s?.key === key ? (s.direction === 'asc' ? 'ascending' : 'descending') : null;
  }

  protected sortIcon(key: string): string {
    const s = this.sort();
    return s?.key !== key ? '↕' : s.direction === 'asc' ? '↑' : '↓';
  }
}
```

Usage:

```ts
@Component({
  selector: 'app-orders',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTable, CellDef, CurrencyPipe],
  template: `
    <app-data-table [rows]="orders()" [columns]="columns" [rowKey]="byId" caption="Recent orders" [(sort)]="sort">
      <ng-template appCell="total" let-row let-value="value">
        <strong>{{ $any(value) | currency: row.currency }}</strong>
      </ng-template>
      <p appTableEmpty>No orders yet. <a href="/orders/new">Create one</a></p>
    </app-data-table>
  `,
})
export class Orders {
  protected readonly orders = signal<Order[]>([]);
  protected readonly sort = signal<SortState | null>({ key: 'date', direction: 'desc' });
  protected readonly byId = (o: Order) => o.id;
  protected readonly columns: Column<Order>[] = [
    { key: 'id', header: 'Order #' },
    { key: 'customer', header: 'Customer', sortable: true, value: (o) => o.customer.name },
    { key: 'date', header: 'Date', sortable: true },
    { key: 'total', header: 'Total', sortable: true },
  ];
}
```

### Walkthrough

- **Generic `T`** is inferred from `[rows]`, so `columns` and `rowKey` are type-checked against the row type.
- **Cell templates via content projection**: a `ng-template[appCell]` directive collected with `contentChildren`. The consumer writes Angular markup in their own template (pipes, links, their components), and the table owns layout. That's the same pattern as CDK's `*cdkCellDef`. The `ngTemplateContextGuard` gives typed `let-` variables. Fully typing `row` needs the directive to know `T`; CDK solves that with an extra typing input, which I'd mention rather than build.
- **`rowKey` is required** because `track` needs stable identity. Tracking by index would re-bind rows on sort, and projected cell state such as focus or an open menu would jump rows.
- **`sort` as `model()`**: uncontrolled by default, controllable with `[(sort)]`, and combined with `clientSort=false` it enables server-side sorting without API changes. Designing for the next consumer is the "library owner" signal.
- **Sorting copies the array**: never mutate an input. `Intl.Collator` with `numeric: true` gives locale-aware, natural ordering ("item 2" < "item 10"). Nulls go last.
- **a11y**: `<caption>` is required as an input (it can be visually hidden), `scope="col"`, and `aria-sort` goes only on the sorted column, per the ARIA guidance. Sort controls are real `<button>`s inside `th`, so they're keyboard operable. The empty state spans all columns.
- **Theming**: CSS custom properties with fallbacks, not deep selectors. That's a stable styling API for consumers.

### Edge cases & tests

- Empty rows with custom empty content, unknown sort key, columns that change at runtime, nulls in the sort column, sort stability (Array.prototype.sort is stable since ES2019), and 10k rows (perf).

```ts
it('sorts and reflects aria-sort', async () => {
  const fixture = TestBed.createComponent(OrdersTestHost); // host with 3 rows
  await fixture.whenStable();
  const th: HTMLElement = fixture.nativeElement.querySelectorAll('th')[1];
  th.querySelector('button')!.click();
  await fixture.whenStable();
  expect(th.getAttribute('aria-sort')).toBe('ascending');
  const firstCell = fixture.nativeElement.querySelector('tbody tr td:nth-child(2)');
  expect(firstCell.textContent.trim()).toBe('Ada');
});
```

### Likely follow-ups

- **"Config array vs. declarative columns (`<app-column>` children)?"** Config is easier to generate dynamically and serialise (user-customisable views). Declarative is nicer to read and gives each column its template. Mature libraries support both. I'd start with config plus template overrides.
- **"Selection?"** Use a `model<ReadonlySet<Key>>()` with a checkbox column and `aria-selected` on rows. Keep selection by key, not object identity.
- **"Breaking-change policy?"** Semver. Deprecate with JSDoc `@deprecated` for one major and provide a migration schematic for big renames. Treat inputs and CSS variables as public API, and never change the default behaviour silently.
- **"How do you stop it becoming a god component?"** Composition through features (sorting, selection, pagination) as directives or hooks, a headless core with a styled wrapper, and a strict RFC process for new inputs.

---

## Task 7 — Virtual scroll: 100k rows

**Time box:** 30 min (CDK 5–7, hand-rolled 20, discussion 5).

### Prompt

> "We need to show a log of 100,000 lines. Rendering them all freezes the browser. Fix it using the CDK, then show me you understand how it works by writing a minimal version yourself."

### Clarifying questions

- Fixed row height? (Assume yes, 32 px. Variable heights are the follow-up.)
- Do users need browser find (Ctrl+F) or printing of the whole list? (It affects whether virtualisation is acceptable.)
- Is the data all in memory or paged from the server?
- Scroll-to-index or "jump to latest" required?

### Solution A: CDK

```ts
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { ScrollingModule } from '@angular/cdk/scrolling';

interface LogRow { id: number; message: string; }

@Component({
  selector: 'app-log-viewer',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ScrollingModule],
  template: `
    <cdk-virtual-scroll-viewport itemSize="32" minBufferPx="320" maxBufferPx="640" class="viewport">
      <div *cdkVirtualFor="let row of rows(); trackBy: trackById" class="row">
        {{ row.id }}: {{ row.message }}
      </div>
    </cdk-virtual-scroll-viewport>
  `,
  styles: `
    .viewport { height: 480px; }
    .row { height: 32px; box-sizing: border-box; line-height: 32px; }
  `,
})
export class LogViewer {
  protected readonly rows = signal<LogRow[]>(
    Array.from({ length: 100_000 }, (_, i) => ({ id: i, message: `Log line ${i}` })),
  );
  protected readonly trackById = (_: number, row: LogRow) => row.id;
}
```

- `itemSize` must match the real CSS row height, otherwise scrolling drifts. The buffers are how much extra content to render beyond the viewport, in px. `*cdkVirtualFor` is still a structural directive; there's no `@for` equivalent for virtual scrolling. The viewport also exposes `scrollToIndex()` and `renderedRangeStream`.

### Solution B: hand-rolled fixed-height virtual list with signals

```ts
// virtual-list.ts
import {
  ChangeDetectionStrategy, Component, TemplateRef, computed, contentChild, input, signal,
} from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';

/** Pure maths: easy to unit test. */
export function visibleRange(
  scrollTop: number, itemHeight: number, viewportHeight: number, count: number, overscan: number,
): { start: number; end: number } {
  const first = Math.floor(scrollTop / itemHeight);
  const visibleCount = Math.ceil(viewportHeight / itemHeight);
  const start = Math.max(0, first - overscan);
  const end = Math.min(count, first + visibleCount + overscan);
  return { start, end };
}

@Component({
  selector: 'app-virtual-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgTemplateOutlet],
  host: {
    role: 'list',
    '[attr.aria-label]': 'label()',
    '[style.height.px]': 'viewportHeight()',
    '(scroll)': 'onScroll($event)',
  },
  template: `
    <div class="spacer" [style.height.px]="totalHeight()">
      <div class="window" [style.transform]="'translateY(' + offsetY() + 'px)'">
        @for (item of visible(); track item.index) {
          <div class="row" role="listitem"
               [style.height.px]="itemHeight()"
               [attr.aria-setsize]="items().length"
               [attr.aria-posinset]="item.index + 1">
            <ng-container [ngTemplateOutlet]="rowTemplate()"
                          [ngTemplateOutletContext]="{ $implicit: item.value, index: item.index }" />
          </div>
        }
      </div>
    </div>
  `,
  styles: `
    :host { display: block; overflow-y: auto; contain: strict; }
    .window { will-change: transform; }
  `,
})
export class VirtualList<T> {
  readonly items = input.required<readonly T[]>();
  readonly itemHeight = input(32);
  readonly viewportHeight = input(480);
  readonly overscan = input(5);
  readonly label = input('Items');

  protected readonly rowTemplate = contentChild.required(TemplateRef);
  private readonly scrollTop = signal(0);

  private readonly range = computed(
    () => visibleRange(this.scrollTop(), this.itemHeight(), this.viewportHeight(), this.items().length, this.overscan()),
    { equal: (a, b) => a.start === b.start && a.end === b.end },
  );
  protected readonly totalHeight = computed(() => this.items().length * this.itemHeight());
  protected readonly offsetY = computed(() => this.range().start * this.itemHeight());
  protected readonly visible = computed(() => {
    const { start, end } = this.range();
    return this.items().slice(start, end).map((value, i) => ({ value, index: start + i }));
  });

  protected onScroll(event: Event): void {
    this.scrollTop.set((event.target as HTMLElement).scrollTop);
  }
}
```

```html
<!-- usage -->
<app-virtual-list [items]="rows()" label="Application log">
  <ng-template let-row let-i="index">{{ i }}: {{ row.message }}</ng-template>
</app-virtual-list>
```

### Walkthrough

- **The idea**: a tall spacer (`count × itemHeight`) gives the native scrollbar the right size and position. Only rows in `[start, end)` are rendered, translated down by `start × itemHeight`. DOM size is about 25 rows instead of 100k.
- **Signals as the scroll throttle**: `scrollTop` changes every pixel, but `range` has a custom `equal`, so `visible` recomputes (and the DOM changes) only when the index window actually moves, roughly once per row height. Sound bite: *"Signal equality gives me memoisation for free. Most scroll events end at the `range` computed and never touch the DOM."*
- **`transform` rather than `top`/padding**: compositor-friendly with no layout on the window element. `contain: strict` isolates layout and paint of the scroller from the rest of the page.
- **`track item.index`**: deliberately recycles DOM nodes, since row N+1 reuses row N's element. That's cheap for stateless rows. With stateful rows (inputs, expanded state) I'd track by a stable id and keep state in the model, not the DOM.
- **Overscan** hides blank flashes during fast scrolls. It's a trade-off against more DOM.
- **Zoneless**: each scroll event is a host listener, so it notifies the scheduler, which coalesces work into a frame. With zone.js I'd consider listening outside the zone and only setting the signal.

### Edge cases & tests

- The list shrinks while scrolled to the bottom (clamp: `end` uses `count`, and the browser clamps `scrollTop`). Viewport resize (measure with `ResizeObserver` instead of a fixed input). Zero items. `itemHeight` mismatched with CSS.

```ts
import { visibleRange } from './virtual-list';

describe('visibleRange', () => {
  it('computes window with overscan', () => {
    expect(visibleRange(0, 32, 480, 100_000, 5)).toEqual({ start: 0, end: 20 });
    expect(visibleRange(3200, 32, 480, 100_000, 5)).toEqual({ start: 95, end: 120 });
  });
  it('clamps at the end', () => {
    expect(visibleRange(32 * 99_990, 32, 480, 100_000, 5)).toEqual({ start: 99_985, end: 100_000 });
  });
});
```

### Likely follow-ups

- **"Variable heights?"** Measure rendered rows (ResizeObserver), store heights in an array, and keep a prefix-sum array (or a Fenwick tree for updates) of offsets. Binary-search `scrollTop` to find `start`, and estimate unmeasured rows with an average. Scroll anchoring gets tricky when measured heights differ from the estimates. CDK has an experimental `autosize` strategy; for serious needs I'd evaluate an existing library before writing my own.
- **"a11y problems?"** Screen readers and Ctrl+F only see rendered rows. Mitigate with `aria-setsize`/`aria-posinset` (lists) or `aria-rowcount`/`aria-rowindex` (grids), keep keyboard focus alive when the focused row scrolls out (move focus with the data, or don't virtualise the focused row), and offer search or filter in the UI.
- **"Alternatives?"** 
  - *Pagination*: best for accessibility and deep links. Often the right product answer ("does anyone read row 73,000?").
  - *Infinite scroll with server paging*: this still needs virtualisation eventually.
  - *CSS `content-visibility: auto` with `contain-intrinsic-size`*: the browser skips rendering off-screen rows while keeping them in the DOM, so find-in-page and a11y still work. Great for a few thousand rows, but 100k DOM nodes still cost memory and Angular creation time.
- **"Millions of rows?"** Browsers cap element height (on the order of tens of millions of px), so you'd scale the spacer and map positions. Also move filtering and sorting to a Web Worker or the server.

---

## Task 8 — HTTP retry interceptor

**Time box:** 30 min (interceptor 15, tests 15).

### Prompt

> "Our API gateway sometimes returns 502/503, and the rate limiter returns 429. Write an interceptor that retries transient failures with exponential backoff. Don't make things worse, and let specific calls opt out. Show me tests."

### Clarifying questions

- Max attempts and delay budget? (Assume 3 retries, base 300 ms, cap 10 s.)
- Which methods? (Only idempotent ones: GET, HEAD, OPTIONS, PUT, DELETE. POST and PATCH are not retried unless the backend supports idempotency keys.)
- Does the server send `Retry-After`? Is it exposed via CORS (`Access-Control-Expose-Headers`)?
- Should a user-visible indicator show during retries? (Out of scope.)
- Is there an existing error or auth interceptor? Order matters.

### Solution

```ts
// retry.interceptor.ts
import { HttpContextToken, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { InjectionToken, inject } from '@angular/core';
import { retry, throwError, timer } from 'rxjs';

export const NO_RETRY = new HttpContextToken<boolean>(() => false);

export interface RetryConfig { maxRetries: number; baseDelayMs: number; maxDelayMs: number; }
export const RETRY_CONFIG = new InjectionToken<RetryConfig>('RETRY_CONFIG', {
  factory: () => ({ maxRetries: 3, baseDelayMs: 300, maxDelayMs: 10_000 }),
});

const IDEMPOTENT = new Set(['GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE']);
const RETRYABLE_STATUS = new Set([0, 429, 502, 503, 504]);

export function parseRetryAfter(value: string | null, now = Date.now()): number | null {
  if (!value) return null;
  const seconds = Number(value);
  if (Number.isFinite(seconds)) return Math.max(0, seconds * 1000);
  const date = Date.parse(value); // HTTP-date form
  return Number.isNaN(date) ? null : Math.max(0, date - now);
}

export function backoffDelay(
  error: HttpErrorResponse, attempt: number, cfg: RetryConfig, random: () => number = Math.random,
): number {
  const retryAfter = parseRetryAfter(error.headers?.get('Retry-After') ?? null);
  if (retryAfter !== null) return Math.min(retryAfter, cfg.maxDelayMs);
  const ceiling = Math.min(cfg.maxDelayMs, cfg.baseDelayMs * 2 ** (attempt - 1));
  return Math.floor(random() * ceiling); // "full jitter"
}

export const retryInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.context.get(NO_RETRY) || !IDEMPOTENT.has(req.method)) return next(req);
  const cfg = inject(RETRY_CONFIG);

  return next(req).pipe(
    retry({
      count: cfg.maxRetries,
      delay: (error: unknown, attempt: number) => {
        if (!(error instanceof HttpErrorResponse) || !RETRYABLE_STATUS.has(error.status)) {
          return throwError(() => error); // not transient: fail fast
        }
        return timer(backoffDelay(error, attempt, cfg));
      },
    }),
  );
};

// app.config.ts
// provideHttpClient(withInterceptors([authInterceptor, retryInterceptor, loggingInterceptor]))
// Per-call opt-out:
// http.get('/api/report', { context: new HttpContext().set(NO_RETRY, true) })
```

### Walkthrough

- **Only idempotent methods**: retrying a POST after a 502 can create a duplicate order, because the gateway might have timed out *after* the backend committed. Sound bite: *"Retries are only safe when repeating the request is safe."*
- **Retryable statuses**: `0` is a network failure (offline, DNS, aborted, or also CORS, which a retry won't fix, hence the cap). `429` and `503` are "come back later", so honour `Retry-After` in both its seconds and HTTP-date forms. `502`/`504` are gateway problems. **Not** retried: 4xx client errors, `500` (often a deterministic bug; team decision), and `401` (the auth interceptor's job).
- **`retry({ count, delay })`** is the RxJS 7 API. `retryWhen` is deprecated. `delay` returns a notifier: emit to retry, error to give up. `attempt` starts at 1.
- **Exponential backoff with full jitter**: `random(0, min(cap, base·2^n))`. Without jitter, every client that failed together retries together (a thundering herd) and the gateway gets hammered again on the same beat.
- **`HttpContextToken`** gives a type-safe per-request flag with a default. It's better than magic headers, which leak to the server.
- **Config via `InjectionToken`** with a factory default. It's overridable in tests or per app, and `inject()` works because functional interceptors run in an injection context.
- **Interceptor order**: requests flow in array order, responses in reverse. Put retry *after* auth, so each retry goes through `next` again and carries the token. Put it *before* logging if you want each attempt logged.
- **Resubscribing** to `next(req)` sends a fresh request. HttpClient observables are cold.

### Tests (Vitest + HttpTestingController + fake timers)

```ts
// retry.interceptor.spec.ts
import { TestBed } from '@angular/core/testing';
import {
  HttpClient, HttpContext, HttpErrorResponse, provideHttpClient, withInterceptors,
} from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { NO_RETRY, RETRY_CONFIG, retryInterceptor } from './retry.interceptor';

describe('retryInterceptor', () => {
  let http: HttpClient;
  let ctrl: HttpTestingController;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(Math, 'random').mockReturnValue(0.999); // deterministic jitter ≈ ceiling
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([retryInterceptor])),
        provideHttpClientTesting(),
        { provide: RETRY_CONFIG, useValue: { maxRetries: 2, baseDelayMs: 100, maxDelayMs: 1000 } },
      ],
    });
    http = TestBed.inject(HttpClient);
    ctrl = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    ctrl.verify();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('retries GET on 503 with backoff, then succeeds', () => {
    let body: unknown;
    http.get('/api/x').subscribe((b) => (body = b));

    ctrl.expectOne('/api/x').flush(null, { status: 503, statusText: 'Unavailable' });
    vi.advanceTimersByTime(98);
    ctrl.expectNone('/api/x');                         // still waiting (~99 ms)
    vi.advanceTimersByTime(2);
    ctrl.expectOne('/api/x').flush({ ok: true });

    expect(body).toEqual({ ok: true });
  });

  it('gives up after maxRetries', () => {
    let error: HttpErrorResponse | undefined;
    http.get('/api/x').subscribe({ error: (e) => (error = e) });

    ctrl.expectOne('/api/x').flush(null, { status: 502, statusText: 'Bad Gateway' });
    vi.advanceTimersByTime(100);
    ctrl.expectOne('/api/x').flush(null, { status: 502, statusText: 'Bad Gateway' });
    vi.advanceTimersByTime(200);
    ctrl.expectOne('/api/x').flush(null, { status: 502, statusText: 'Bad Gateway' });

    expect(error?.status).toBe(502);                   // 1 call + 2 retries
  });

  it('honours Retry-After on 429', () => {
    http.get('/api/x').subscribe();
    ctrl.expectOne('/api/x').flush(null, {
      status: 429, statusText: 'Too Many Requests', headers: { 'Retry-After': '1' },
    });
    vi.advanceTimersByTime(999);
    ctrl.expectNone('/api/x');
    vi.advanceTimersByTime(1);
    ctrl.expectOne('/api/x').flush({});
  });

  it('does not retry POST, 404, or opted-out requests', () => {
    http.post('/api/x', {}).subscribe({ error: () => {} });
    ctrl.expectOne('/api/x').flush(null, { status: 503, statusText: 'x' });

    http.get('/api/y').subscribe({ error: () => {} });
    ctrl.expectOne('/api/y').flush(null, { status: 404, statusText: 'x' });

    http.get('/api/z', { context: new HttpContext().set(NO_RETRY, true) }).subscribe({ error: () => {} });
    ctrl.expectOne('/api/z').flush(null, { status: 503, statusText: 'x' });

    vi.advanceTimersByTime(10_000);
    ctrl.expectNone('/api/x');
    ctrl.expectNone('/api/y');
    ctrl.expectNone('/api/z');
  });
});
```

- `provideHttpClientTesting()` swaps the real backend (Fetch by default in v22) for the testing backend. Order it after `provideHttpClient`.
- Unit-test `parseRetryAfter` and `backoffDelay` directly too: seconds, HTTP-date, garbage, and the cap.

### Likely follow-ups

- **"Retry-After larger than the cap?"** Either cap it (as here) or give up and surface a "try again in N s" message. Hammering early violates the server's request.
- **"Circuit breaker?"** After N consecutive failures to a host, fail fast for a cool-down window. That shared state lives in a root service the interceptor injects.
- **"Offline?"** Combine with `navigator.onLine` or `online` events: wait for `online` instead of a timer when status is 0.
- **"POST with idempotency keys?"** Generate an `Idempotency-Key` header per logical operation, *outside* the retry loop so every attempt shares the key. Then POST becomes retryable.
- **"Where do you show errors?"** A separate error interceptor or global handler after retries are exhausted. Don't toast on every attempt.

---

## Task 9 — Deep clone in TypeScript

**Time box:** 20–25 min.

### Prompt

> "Implement `deepClone(value)` without libraries. It should handle primitives, arrays, plain objects, Dates, RegExps, Maps, Sets, and circular references. Then tell me when you'd just use `structuredClone`."

### Clarifying questions

- Should class instances keep their prototype, or become plain objects? (Make it an option.)
- Functions: copy by reference or throw? (By reference. Functions are immutable enough in practice.)
- Symbol keys, non-enumerable properties, getters? (Copy own keys including symbols, and keep descriptors so getters aren't invoked.)
- Typed arrays, Blobs, DOM nodes? (Out of scope. Mention them.)

### Solution

```ts
// deep-clone.ts
export interface CloneOptions { preservePrototype?: boolean; }

export function deepClone<T>(value: T, options: CloneOptions = {}): T {
  const seen = new WeakMap<object, unknown>();

  const clone = (input: unknown): unknown => {
    // Primitives (incl. bigint, symbol) and functions are returned as-is.
    if (input === null || typeof input !== 'object') return input;

    const cached = seen.get(input);
    if (cached !== undefined) return cached; // circular or shared reference

    if (input instanceof Date) return new Date(input.getTime());

    if (input instanceof RegExp) {
      const re = new RegExp(input.source, input.flags);
      re.lastIndex = input.lastIndex;
      return re;
    }

    if (input instanceof Map) {
      const out = new Map();
      seen.set(input, out);                // register BEFORE recursing
      input.forEach((v, k) => out.set(clone(k), clone(v)));
      return out;
    }

    if (input instanceof Set) {
      const out = new Set();
      seen.set(input, out);
      input.forEach((v) => out.add(clone(v)));
      return out;
    }

    if (Array.isArray(input)) {
      const out: unknown[] = new Array(input.length);
      seen.set(input, out);
      for (let i = 0; i < input.length; i++) {
        if (i in input) out[i] = clone(input[i]); // preserve holes
      }
      return out;
    }

    const proto = options.preservePrototype ? Object.getPrototypeOf(input) : Object.prototype;
    const out = Object.create(proto) as Record<PropertyKey, unknown>;
    seen.set(input, out);
    for (const key of Reflect.ownKeys(input)) {       // string + symbol keys
      const desc = Object.getOwnPropertyDescriptor(input, key)!;
      if ('value' in desc) desc.value = clone(desc.value);
      Object.defineProperty(out, key, desc);          // keeps getters/setters, writability
    }
    return out;
  };

  return clone(value) as T;
}
```

### Walkthrough

- **Circular references**: a `WeakMap` from original to clone, **registered before recursing into children**. Otherwise `a.self = a` recurses forever. `WeakMap` so the bookkeeping never keeps inputs alive. It also preserves *shared* references: if two fields point at the same object, the clone has two fields pointing at the same *cloned* object.
- **Order of checks**: special built-ins before the generic object branch, since `Date` or `Map` copied as plain objects would lose their internal slots and be empty. `instanceof` fails across realms (iframes). `Object.prototype.toString.call(x)` tags are more robust if that matters.
- **Descriptors**: `Object.getOwnPropertyDescriptor(s)` (ES2017, in the ES8 set from the job spec) keeps getters as getters instead of invoking them and freezing their current value. The simpler `for...in` or `Object.keys` version loses symbols, non-enumerables and accessors. That's fine to write first and then say "upgrade: descriptors".
- **Prototype option**: plain objects by default avoid surprises such as running constructors or private `#fields` (which can't be copied from outside; methods touching them on the clone would throw). `preservePrototype` keeps `instanceof` and methods for simple classes.
- **Map keys are cloned too**, which matches `structuredClone`. If callers look up by original object keys, that breaks, so call it out.
- **Complexity**: O(n) in the number of reachable nodes, plus O(n) memory for the map. The recursion depth equals the nesting depth, so very deep structures (about 10k levels) can overflow the stack. The fix is an explicit stack/queue: create each empty container, then fill it iteratively.

### `structuredClone` and JSON: what to say

- **`structuredClone`** (an HTML/Node API, not ECMAScript; widely available in modern browsers and Node 17+) handles circular refs, Date, RegExp, Map, Set, ArrayBuffer and typed arrays, Blob/File, Error types, and BigInt. Its limits:
  - **Functions** → throws `DataCloneError`. **DOM nodes** → throws.
  - **Class instances** → prototype lost; you get a plain object with own enumerable data properties.
  - **Getters/setters** are invoked and flattened to values, and property descriptors aren't kept. **Symbol keys** are dropped.
  - `RegExp.lastIndex` isn't preserved.
- **`JSON.parse(JSON.stringify(x))`** pitfalls: `Date` becomes a string; `undefined`, functions and symbols are dropped (in arrays they become `null`); `NaN`/`Infinity` become `null`; `Map`/`Set` become `{}`; `-0` becomes `0`; circular refs throw; `BigInt` throws; `toJSON` side effects. It's also slow for big graphs.
- Sound bite: *"Default to `structuredClone` for data. Write a custom clone only when I need prototypes, functions or descriptors. Often the better answer is not to need a deep clone: immutable updates with structural sharing (spread per level, or Immer) copy only the changed path, which is what NgRx and signals want anyway."*

### Edge cases & tests

```ts
import { deepClone } from './deep-clone';

describe('deepClone', () => {
  it('clones nested structures without sharing references', () => {
    const src = { d: new Date(0), m: new Map([['k', { n: 1 }]]), s: new Set([1]), a: [1, [2]], r: /x/gi };
    const out = deepClone(src);
    expect(out).toEqual(src);
    expect(out.m.get('k')).not.toBe(src.m.get('k'));
    expect(out.d).not.toBe(src.d);
    expect(out.r.flags).toBe('gi');
  });

  it('handles circular and shared references', () => {
    const shared = { v: 1 };
    const src: { self?: unknown; x: object; y: object } = { x: shared, y: shared };
    src.self = src;
    const out = deepClone(src);
    expect(out.self).toBe(out);
    expect(out.x).toBe(out.y);
    expect(out.x).not.toBe(shared);
  });

  it('optionally preserves prototypes', () => {
    class Point { constructor(public x = 1) {} norm() { return Math.abs(this.x); } }
    expect(deepClone(new Point(), { preservePrototype: true })).toBeInstanceOf(Point);
    expect(deepClone(new Point())).not.toBeInstanceOf(Point);
  });
});
```

Also mention: frozen objects (descriptors copy `writable: false`, but the clone isn't frozen; add `Object.isFrozen` handling if needed), typed arrays (`ArrayBuffer.isView` then `.slice()`), boxed primitives, and `Error`.

### Likely follow-ups

- **"Make it iterative."** Keep a work stack of `[source, target]` pairs: create each empty container, push it, and fill it in a loop. This removes the recursion depth limit.
- **"Type the result better?"** `T` is the honest contract for data. For functions or class instances without `preservePrototype`, the runtime shape differs from `T`. You could constrain inputs to a `DeepData` type that excludes functions and class instances.
- **"Where would you use this in Angular?"** Rarely. Snapshotting form state for "reset" or undo stacks. For state management, prefer immutable updates, and in dev use NgRx runtime checks that freeze state to catch mutations.

---

## Task 10 — Flatten an array

**Time box:** 15–20 min.

### Prompt

> "Write `flatten(arr, depth = 1)` that behaves like `Array.prototype.flat`, without using `flat`. Then do it without recursion. Bonus: a lazy version."

### Clarifying questions

- Match `flat` exactly, including holes and non-integer depth? (Yes: holes skipped, depth truncated, `Infinity` allowed, depth ≤ 0 means a shallow copy.)
- Array-likes or iterables inside? (No. Like `flat`, only real arrays (`Array.isArray`) are flattened.)
- Target environment? (`flat` is ES2019, beyond the ES5–ES8 range in the job spec, so on an old target it needs the `es2019` lib in `tsconfig` plus a polyfill. That's the reason this question gets asked.)

### Solution

```ts
// flatten.ts
/** Mirror flat()'s depth coercion: NaN -> 0, truncate, Infinity allowed. */
function toDepth(depth: number): number {
  const n = Number(depth);
  if (Number.isNaN(n)) return 0;
  return n === Infinity ? Infinity : Math.trunc(n);
}

// 1) Recursive: clearest; recursion depth = nesting depth.
export function flatten<A extends readonly unknown[], D extends number = 1>(
  arr: A,
  depth: D = 1 as D,
): FlatArray<A, D>[] {
  const out: unknown[] = [];
  const walk = (a: readonly unknown[], d: number): void => {
    for (let i = 0; i < a.length; i++) {
      if (!(i in a)) continue;                 // skip holes, like flat()
      const el = a[i];
      if (Array.isArray(el) && d > 0) walk(el, d - 1);
      else out.push(el);
    }
  };
  walk(arr, toDepth(depth));
  return out as FlatArray<A, D>[];
}

// 2) Iterative with an explicit stack of frames: order-preserving, no call-stack limit.
export function flattenIterative(arr: readonly unknown[], depth = 1): unknown[] {
  const out: unknown[] = [];
  const stack: { a: readonly unknown[]; i: number; d: number }[] = [{ a: arr, i: 0, d: toDepth(depth) }];
  while (stack.length > 0) {
    const top = stack[stack.length - 1];
    if (top.i >= top.a.length) { stack.pop(); continue; }
    const idx = top.i++;
    if (!(idx in top.a)) continue;
    const el = top.a[idx];
    if (Array.isArray(el) && top.d > 0) stack.push({ a: el, i: 0, d: top.d - 1 });
    else out.push(el);
  }
  return out;
}

// 3) Generator: lazy; consumer can stop early (e.g. take first N).
export function* flattenLazy(arr: readonly unknown[], depth = 1): Generator<unknown, void, undefined> {
  const d = toDepth(depth);
  for (let i = 0; i < arr.length; i++) {
    if (!(i in arr)) continue;
    const el = arr[i];
    if (Array.isArray(el) && d > 0) yield* flattenLazy(el, d - 1);
    else yield el;
  }
}
```

### Walkthrough

- **Semantics**: `flat` visits only existing indices (`HasProperty`), so `[1, , [2, , 3]].flat()` gives `[1, 2, 3]`. `depth` goes through ToIntegerOrInfinity: `flat(1.7)` equals `flat(1)`, `flat(NaN)` equals `flat(0)`, and a negative depth flattens nothing. Only `Array.isArray` elements are spread, so strings, array-likes and typed arrays stay intact.
- **Typing**: TypeScript's built-in `FlatArray<Arr, Depth>` (from `lib.es2019.array`) is exactly what `Array.prototype.flat` uses, so `flatten([1, [2, [3]]], 1)` is typed `(number | number[])[]`. It only works with literal depths. With a runtime `number` it degrades gracefully, and past a recursion limit it just returns a wide type. Don't hand-roll a recursive conditional type unless asked. If the environment's lib has no `FlatArray`, fall back to `unknown[]`.
- **Iterative version**: a naive approach pushes all elements onto a stack, pops, then `reverse()`s at the end. That works, but tracking depth per element is awkward and it allocates more. The frame stack (array, index, depth) mirrors what the call stack does in the recursive version, but lives on the heap, so nesting 100k levels deep doesn't throw `RangeError: Maximum call stack size exceeded`.
- **Generator**: lazy, so it's good for huge inputs and early exit (`for...of` with `break`). The cost is that `yield*` delegation re-yields through every level, so each element costs O(depth). With deep nesting, write an iterative generator using the same frame stack.
- **Complexity**: time O(N + A), where N is the number of leaf elements and A the number of nested arrays visited. Space O(N) for output plus O(depth) stack/frames. The old `reduce((acc, x) => acc.concat(...))` one-liner is O(N²) in the worst case because `concat` copies the accumulator every step. That's a common follow-up.
- **Circular arrays** (`a.push(a)`) with `Infinity` depth loop forever. Native `flat` overflows too. Guard with a `WeakSet` of arrays on the current path if the input is untrusted.

### Edge cases & tests

Test against the native implementation as the oracle, which is a good habit to name out loud.

```ts
import { flatten, flattenIterative, flattenLazy } from './flatten';

const cases: [unknown[], number][] = [
  [[1, [2, [3, [4]]]], 1],
  [[1, [2, [3, [4]]]], 2],
  [[1, [2, [3, [4]]]], Infinity],
  [[1, , [2, , 3]], 1],        // holes
  [[[1], [2]], 0],             // depth 0 = shallow copy
  [[[1], [2]], -1],
  [[[1], [[2]]], 1.9],         // truncated to 1
  [['ab', [{ length: 1, 0: 'x' }]], Infinity], // strings/array-likes not spread
  [[], 3],
];

describe.each([
  ['recursive', flatten as (a: unknown[], d: number) => unknown[]],
  ['iterative', flattenIterative],
  ['lazy', (a: unknown[], d: number) => [...flattenLazy(a, d)]],
])('%s', (_name, impl) => {
  it.each(cases)('matches Array.prototype.flat for %j depth %s', (input, depth) => {
    expect(impl(input, depth)).toEqual(input.flat(depth));
  });

  it('does not mutate the input', () => {
    const input = [1, [2, [3]]];
    const copy = structuredClone(input);
    impl(input, Infinity);
    expect(input).toEqual(copy);
  });
});

it('iterative survives very deep nesting', () => {
  let deep: unknown[] = [0];
  for (let i = 0; i < 100_000; i++) deep = [deep];
  expect(flattenIterative(deep, Infinity)).toEqual([0]);
});
```

### Likely follow-ups

- **"Implement `flatMap`?"** It's `map` followed by `flat(1)`, with depth fixed at 1. Also ES2019.
- **"Polyfill `flat` on the prototype?"** Use `Object.defineProperty(Array.prototype, 'flat', { value, writable: true, configurable: true })` so it's non-enumerable and doesn't show up in `for...in`, and only when it's missing. In real projects, rely on core-js via the build or browserslist rather than hand-written polyfills.
- **"Flatten a nested object into dot paths?"** Same traversal with a key prefix accumulator (`{ a: { b: 1 } }` → `{ 'a.b': 1 }`). Decide how arrays are keyed (`a.0` or `a[0]`).
- **"Where does this show up in Angular?"** Flattening route trees (`children`), nested menu or permission structures, and form error trees. Plus RxJS flattening operators (`mergeAll`, `concatAll`) are the same idea for streams, which makes a nice bridge to talk about.

---

## Practice plan

Do each task **timed, out loud, from a blank file** (StackBlitz or a local `ng new` with Vitest), with a stopwatch and ideally a friend or a screen recording. Compare against the solutions only afterwards.

| Week / session | Tasks | Why this order |
|---|---|---|
| 1 | **10** (flatten), **9** (deep clone) | Pure TS warm-ups. Rehearse the 5-step routine without framework noise. Target: working recursive version in 8 min. |
| 2 | **1** (typeahead), **8** (retry interceptor) | RxJS reasoning and operator choice is the highest-frequency senior topic. Practise the tests too. |
| 3 | **3** (OnPush bug hunt), **4** (leaks) | Explain-and-fix format. Practise *talking* more than typing. Rehearse the v22 OnPush-default and zoneless explanation until it's 60 seconds. |
| 4 | **2** (star rating), **6** (generic table) | Component-library tasks: API design, a11y and content projection. This is your strongest story as a library owner, so make it shine. |
| 5 | **5** (NgRx slice), **7** (virtual scroll) | Longest tasks. Practise cutting scope under time pressure. |
| Final 2 days | Redo the 3 you were slowest at, cold. One mock with someone else choosing the task. | Speed and composure. |

Tips:
- Keep a scratch project with `provideHttpClient`, Vitest and one `@Component` ready, so setup never eats your time in practice. Also confirm what the interviewer's environment will be (StackBlitz, CodeSandbox, shared doc, or their repo).
- After each attempt, write down one thing you forgot (cleanup? a11y? error state?). That list becomes your personal checklist.
- Practise saying version notes naturally: "since v21…", "pre-v22 the default was…".

## Pre-live-coding checklist (glance at this 5 minutes before)

- [ ] Restate the problem in one sentence, ask 2–4 questions, and write the assumptions as a comment.
- [ ] Say the plan (API shape and data flow) before typing.
- [ ] Happy path working by the halfway mark. Tell them what you're deferring.
- [ ] `ChangeDetectionStrategy.OnPush` written explicitly, with state in signals, inputs via `input()`, and `@for` with a meaningful `track`.
- [ ] Every subscription, timer and listener has an owner: `toSignal`, the async pipe, `takeUntilDestroyed`, or `DestroyRef.onDestroy`.
- [ ] RxJS: justify the flattening operator. `catchError` goes *inside* the inner stream.
- [ ] Loading, error and empty states. No mutation of inputs.
- [ ] a11y: label, role, keyboard, focus-visible, live region if content updates.
- [ ] Name 3 edge cases and write or describe at least one test (Vitest/TestBed or pure).
- [ ] Mention complexity and performance where relevant (Big-O, DOM size, change detection cost).
- [ ] Check the clock at the halfway point and 5 minutes before the end. Leave time for their questions.
- [ ] Take hints gracefully: "Good point, let me handle that."

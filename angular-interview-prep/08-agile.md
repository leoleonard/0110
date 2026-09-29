# 08 — Agile: Scrum, Kanban, Waterfall & Working Across Teams

> Use this file for the process and collaboration part of the interview, which often shows up as behavioural questions ("tell me about a time…"). At senior level, interviewers aren't checking that you can name the Scrum events. They want to see that you **understand why the practices exist**, can **adapt the process to the context** (regulated work, third parties, a shared design system), **protect the team's focus while staying responsive**, **talk about estimates and dates honestly**, and **measure outcomes rather than activity**. As Design Authority and owner of a shared component library, you'll likely be asked how you govern shared assets across teams, work with designers, and handle requests from product and QA. Prepare two or three concrete stories with numbers.

---

## A. Most commonly asked questions

### Q1. Describe Scrum: roles, events and artifacts.

**Answer (1–2 min):** (per the Scrum Guide 2020)
- **Scrum Team** of up to ~10 people, one team with no sub-teams, cross-functional and self-managing. Three **accountabilities** (the 2020 guide says accountabilities, not roles):
  - **Product Owner** — maximises value; owns and orders the Product Backlog; one person, not a committee.
  - **Scrum Master** — accountable for the team's effectiveness; coaches the team and organisation, removes impediments, makes sure events happen and are useful. A servant-leader, **not** the team's manager.
  - **Developers** — everyone who builds the Increment (devs, QA, UX, etc.); own the Sprint Backlog and how the work is done.
- **Events**: the **Sprint** (≤ one month, container for all the others), **Sprint Planning** (why / what / how → Sprint Goal + Sprint Backlog), **Daily Scrum** (15 min, for Developers, progress towards the Sprint Goal and adapting the plan — not a status report to a manager), **Sprint Review** (inspect the Increment with stakeholders, adapt the backlog — a working session, not a demo-and-clap), **Sprint Retrospective** (improve how we work). Refinement is an ongoing activity, not an official event.
- **Artifacts and their commitments** (introduced in 2020):
  - Product Backlog → **Product Goal** (the long-term objective).
  - Sprint Backlog → **Sprint Goal** (the single objective for the sprint; gives flexibility on scope).
  - Increment → **Definition of Done** (the quality bar; anything not meeting it isn't part of the Increment).

"The Sprint Goal is the part teams most often skip — without it, the sprint is just a list of tickets and every mid-sprint change is a negotiation over tickets instead of over the goal."

---

### Q2. What is Kanban and why do WIP limits matter?

**Answer (1–2 min):**
- Kanban is a **flow** method: visualise the work (board with explicit columns and policies), **limit work in progress**, manage and measure flow, make policies explicit, improve continuously. No prescribed roles or sprints; items are pulled when capacity frees up.
- **Why WIP limits**: multitasking and context switching increase cycle time; queues hide problems. Limiting WIP forces "stop starting, start finishing" — when a column is full, people help unblock (review, test) instead of starting something new. It exposes bottlenecks (e.g. code review or QA columns always full).
- Good fit: support/maintenance, platform or design-system teams with a stream of unplanned requests, ops, teams where priorities change daily.
- "Our component-library team was a good Kanban candidate: requests arrive from many product teams at unpredictable times; sprints would force them to wait up to two weeks."

---

### Q3. Explain flow metrics: cycle time, lead time, throughput, CFD, Little's Law.

**Answer:**
- **Lead time**: from request (created/committed) to delivered — what the customer experiences.
- **Cycle time**: from work started to done — what the team controls. (Definitions vary; state yours.)
- **Throughput**: items finished per unit of time (per week).
- **WIP**: items started but not finished.
- **Cumulative Flow Diagram (CFD)**: stacked bands per column over time. Band width = WIP in that stage; widening band = bottleneck; flat top line = nothing being delivered; horizontal distance ≈ approximate lead time.
- **Little's Law**: `average cycle time = average WIP / average throughput` (for a stable system). Example: 12 items in progress, throughput 6/week → ~2 weeks cycle time. To go faster without working harder: **reduce WIP**.
- Use percentiles, not averages, for promises: "85% of our stories finish within 6 days" (from a cycle-time scatterplot).

---

### Q4. When is Waterfall actually the right choice?

**Answer:**
- When requirements are **genuinely fixed and known up front** and change is expensive or forbidden: regulated/safety-critical work with formal sign-offs, fixed-price/fixed-scope contracts, hardware dependencies, government tenders.
- **Third-party integrations** with a partner who works on long release cycles: the interface contract, test windows and go-live date are fixed milestones.
- Large migrations with a hard cut-over date.
- Reality: most enterprise projects are **hybrid** — waterfall-style milestones and contracts outside, iterative delivery inside. "I've worked with a fixed integration milestone from a payment provider: we froze the API contract early (OpenAPI), built against mocks in sprints, and planned the certification window as a fixed date. Agile inside, waterfall at the boundary."
- The weakness to name: late feedback and late integration — so even in waterfall you want early prototypes and continuous integration.

---

### Q5. Scrumban and SAFe — briefly?

**Answer:**
- **Scrumban**: Scrum's cadence (planning, review, retro) + Kanban's flow (WIP limits, pull, flow metrics), often with on-demand planning instead of fixed sprint commitments. Common for teams mixing roadmap work with support.
- **SAFe** (Scaled Agile Framework): coordinates many teams in Agile Release Trains with Program Increment (PI) planning every ~8–12 weeks, shared cadence, roles like Release Train Engineer. Helps large enterprises align dependencies; criticised as heavyweight and top-down. Alternatives: LeSS, Nexus, or lightweight cross-team syncs.
- "In SAFe my component library would be a shared service/enabler: I'd get library work into PI objectives and publish a roadmap so teams can plan around releases."

---

### Q6. Story points vs time estimates. How do you estimate?

**Answer (1–2 min):**
- **Story points** are *relative* size: effort + complexity + uncertainty, compared with reference stories ("this is like the date-picker story, but with i18n → bigger"). Humans are better at relative than absolute estimation.
- **Planning poker** (Fibonacci-ish scale): everyone reveals at once to avoid anchoring; the value is in the **conversation when estimates differ** — "why is it a 13 for you?" usually uncovers hidden work (a11y, edge cases, API gaps).
- Points are team-specific and only useful for the team's own forecasting. They're not convertible to hours, and not comparable between teams.
- **Time estimates** are fine for small, well-understood tasks or when a contract requires them — give ranges, not points.
- **#NoEstimates**: slice stories to a similar small size, count them, and forecast from throughput. Works well once slicing is disciplined; saves estimation time.
- **Forecasting with Monte Carlo**: sample historical weekly throughput thousands of times to answer "when will these 40 items be done?" → "50% by 3 Oct, 85% by 17 Oct". Probabilistic answers are more honest than a single date.

---

### Q7. A stakeholder insists on a fixed date. How do you respond?

**Answer:**
- Separate **the target** (what the business wants) from **the forecast** (what the data says) and **the commitment** (what we agree to).
- Give a range with confidence ("85% likely by mid-October at current scope"), and make the trade-off explicit: fix the date → flex scope. Identify the **minimum viable scope** for the date and order the rest.
- Surface risks and dependencies early (third-party API, design sign-off), re-forecast every sprint and communicate deltas proactively — bad news early is a feature.
- Don't pad secretly or cave to an unrealistic number; don't sacrifice the DoD (skipping tests/a11y) to hit it — that's hidden debt that someone pays later.
- Sound bite: "I can give you a date or I can give you all the scope — with this team and this data, not both. Here's what fits."

---

### Q8. Definition of Ready vs Definition of Done. What's in a frontend DoD?

**Answer (1–2 min):**
- **Definition of Ready** (not part of the Scrum Guide, a team practice): a story can enter a sprint when it's understood, sized, has acceptance criteria, designs are available, API contract known/mocked, dependencies identified. Use it as a checklist, not a gate that blocks collaboration ("ready-ish is fine if we can clarify in a day").
- **Definition of Done**: the team's quality standard for *every* increment — a Scrum commitment. It's shared by all items, unlike **acceptance criteria**, which are story-specific.
- Frontend DoD I'd propose:
  - Code reviewed and merged; CI green (lint, typecheck, unit tests, build budgets).
  - Tests: unit/component tests for logic and interactions; e2e for critical journeys touched.
  - **Accessibility**: keyboard navigation, focus management, labels/ARIA, contrast — axe checks pass, WCAG 2.2 AA target.
  - **Responsive** on agreed breakpoints and supported browsers.
  - **i18n**: no hard-coded strings, RTL/long-text checked where relevant, locale formatting for dates/numbers.
  - **Analytics** events added per the tracking plan.
  - Error, loading and empty states implemented.
  - Feature flag configured if applicable; deployed to staging; PO accepted against acceptance criteria.
  - For the **component library**: Storybook stories and docs updated, public API reviewed, changeset/changelog entry, no breaking change without a major version and migration notes, visual regression tests updated, design sign-off against Figma.

---

### Q9. Requirements change mid-sprint. What do you do?

**Answer:**
- First question: **does it affect the Sprint Goal?** Scope within the Sprint Backlog can be renegotiated with the PO as long as the goal holds; the goal itself shouldn't change.
- For urgent new work: make the trade-off visible — something of similar size comes out. Nothing is added silently.
- If the Sprint Goal becomes obsolete, the PO can cancel the sprint (rare, but it's the honest option).
- Reduce the pain structurally: **vertical slices** (thin end-to-end pieces — UI + API + tests — that deliver value on their own), short sprints, **feature flags** so half-finished work can merge without being released, and reserved capacity for unplanned work (e.g. 15–20%) if the team has a steady interrupt stream.
- Slicing techniques: by workflow step, by business rule, happy path first then edge cases, by data variation, by role, "read-only first, then edit".

---

### Q10. What does good backlog refinement look like?

**Answer:**
- Ongoing, typically ≤10% of team capacity; PO + a few developers + designer/QA as needed, looking 1–2 sprints ahead.
- Outputs: stories split small enough to finish in a few days, acceptance criteria (Given/When/Then helps), open questions assigned, designs and API contracts linked, risks and spikes identified.
- Frontend lead's contribution: spot hidden work (states, a11y, responsive, i18n, analytics, permissions), propose reuse of design-system components or identify a missing one early, flag API contract gaps, suggest a thinner first slice.
- Anti-patterns: refinement as a PO monologue; estimating stories nobody understands; refining 3 months ahead (waste — it'll change).

---

### Q11. How do you work with product managers and designers? What does Design Authority mean in practice?

**Answer (1–2 min):**
- **With PMs**: understand the outcome/metric behind a request, bring technical options with cost ("option A in 2 days with existing components, option B in 2 weeks with a custom interaction"), raise risk early, and share data (performance, error rates, usage) to influence priorities.
- **With designers**: involve engineering early (feasibility, states, responsive behaviour), agree on **design tokens** as the shared language (colour, spacing, typography, radius, motion → published from Figma variables into CSS custom properties / SCSS via a token pipeline), use Figma Dev Mode/specs for handoff, and review built components together — "design QA" before release.
- **Design-system governance** (Design Authority role):
  - Contribution model: who can propose components, RFC/proposal template, criteria for inclusion ("used by ≥2 products", accessible, themeable).
  - Decision forum with design + engineering representation; decisions recorded (ADRs).
  - Versioning and deprecation policy (SemVer, deprecate for at least one major before removal, migration guides/schematics).
  - Adoption and health metrics: component coverage, number of local overrides/forks, a11y issues, bundle size.
  - Saying "no" (or "not in the core library — build it locally, and we'll promote it if it proves reusable") with reasons.
- "My job as Design Authority is less about approving pixels and more about keeping one source of truth between Figma and code, so product teams can move fast without diverging."

---

### Q12. How do you collaborate with QA? What's your view on the test pyramid?

**Answer:**
- **Shift-left**: QA involved in refinement (acceptance criteria and edge cases before coding), developers own automated tests, QA focuses on exploratory testing, risk-based test design and the e2e/regression strategy.
- **Test pyramid**: many fast unit/component tests, fewer integration tests, few e2e tests for critical journeys. The "testing trophy" variant weights integration/component tests more for frontends — testing components through the DOM like a user (Testing Library) gives the most confidence per test. Avoid the "ice-cream cone" (mostly manual/e2e).
- Stable test hooks (`data-testid` or accessible roles), seeded test data and mocked APIs (MSW) reduce flaky e2e.
- **Bug triage**: agree severity (impact) vs priority (urgency) definitions; regular triage with PO + QA + dev lead; every bug gets a reproduction, expected vs actual, environment; critical bugs interrupt the sprint by policy, the rest go to the backlog ordered by the PO. Track escaped defects and add a regression test for each fix.

---

### Q13. How do you work with third parties (external APIs, vendors, agencies)?

**Answer:**
- **Contract first**: agree the API contract (OpenAPI), error format, auth, rate limits and environments in writing, early. Version it.
- **SLAs/SLOs**: response times, availability, support hours, escalation contacts, sandbox availability, deprecation notice period. Design the UI for their failure modes (timeouts, retries, degraded mode, status banner).
- **Decouple**: build against **mocks** (MSW, Postman mock server, Prism from the spec) so their delays don't block us; contract tests where possible; an adapter/anti-corruption layer so their data model doesn't leak through the app.
- **Communication**: single point of contact, shared Postman collection to reproduce issues ("here's the exact request and response, with correlation ID"), a regular sync during integration, written decisions.
- **Escalation**: clear path (technical contact → account manager → contractual), escalate with data and impact, not frustration, and early — before it threatens a milestone.

---

### Q14. How do you handle technical debt in an agile backlog?

**Answer:**
- Make it **visible and explained in business terms**: "this legacy form module adds ~2 days to every checkout change and caused 3 production bugs last quarter".
- Put it in the backlog as items the PO can order, with value/cost — not a hidden side project. Techniques: a capacity allocation (e.g. ~15–20%), boy-scout rule within feature work, dedicated items for larger refactors sliced incrementally (strangler fig, branch by abstraction).
- Tie debt work to delivery: "we'll migrate this screen to signals and the new component while building the feature that changes it."
- Framework upgrades (Angular's ~6-monthly majors) are planned debt: keep within supported versions (active + LTS), run `ng update` regularly — skipping versions makes it far more expensive. Example: the v22 change making components OnPush by default is migrated automatically (the migration adds `ChangeDetectionStrategy.Eager` where needed), which is cheap if you're current and painful if you're three majors behind.

---

### Q15. Which metrics do you use? What are DORA metrics?

**Answer:**
- **DORA** (DevOps Research and Assessment) delivery performance metrics:
  - **Deployment frequency** — how often we deploy to production.
  - **Lead time for changes** — commit to running in production.
  - **Change failure rate** — % of deployments causing a failure needing remediation.
  - **Time to restore service** (failed deployment recovery time) — how fast we recover.
  - (Later versions of the research add reliability / rework rate — mention it only generally.)
- They balance **speed and stability**; elite teams are good at both, which is the point — small, frequent changes are safer.
- Plus **outcome** metrics: Core Web Vitals (LCP, INP, CLS), conversion/task completion, error rate, support tickets, accessibility issues, design-system adoption.
- Flow metrics (cycle time, throughput) for the team's own improvement.
- Guard against Goodhart's Law: "when a measure becomes a target, it ceases to be a good measure". Metrics are for learning, not for ranking people.

---

### Q16. How do you talk about agile as a senior?

**Answer:**
- **Outcomes over ceremonies**: "We don't do Scrum to do Scrum. The point is short feedback loops and delivering value in small, safe steps. I judge the process by lead time, quality and whether users' problems got solved."
- Adapt to context: Scrum for product discovery with a stable team, Kanban for a support/platform stream, hybrid at contractual boundaries.
- Show improvements you drove with data: "Our cycle time was 11 days, mostly waiting for review. We set a review SLA and WIP limit on the review column; it dropped to 5 days within a month."
- Talk about your influence beyond code: running refinement for frontend, design-system governance, mentoring, shaping the DoD, raising risks to stakeholders.
- Avoid dogma in both directions — neither "the Scrum Guide says…" nor "agile is just meetings".

---

### Q17. How do you keep cross-team dependencies from blocking a sprint (e.g. teams waiting on the component library)?

**Answer:**
- **Make dependencies visible early**: in refinement, tag stories that need a new library component or API change; run a lightweight cross-team sync (or a PI-planning board in SAFe) listing who needs what by when.
- **Publish a library roadmap** and a request intake (issue template: use case, designs, deadline, which products). Triage it weekly with design.
- **Decouple delivery**: the product team can build a local component that follows the tokens and API conventions, then it's promoted into the library ("inner-source" contribution with library-team review) — nobody waits for us.
- **Release small and often**: prereleases (`next` tag) so teams can adopt early; SemVer so they can upgrade without fear.
- Track lead time of library requests as a health metric; if it grows, the library team is a bottleneck and needs more contributors or a clearer contribution model.

---

### Q18. "Tell me about a time a sprint went badly." How do you structure behavioural answers?

**Answer:**
- Use **STAR** (Situation, Task, Action, Result) and add **Learning** — keep it to ~2 minutes, spend most time on *your* actions, and quantify the result.
- Pick stories that show senior behaviours: influencing without authority, making trade-offs visible, protecting quality under pressure, improving the system rather than blaming people.
- Example skeleton:
  - *Situation*: a third-party pricing API slipped two weeks, threatening the sprint goal for a release.
  - *Task*: as frontend lead, keep the release date without shipping something broken.
  - *Action*: agreed a frozen contract with the vendor, built against MSW mocks, proposed to the PO a thinner slice (cached prices, no live quotes) behind a feature flag, escalated the vendor delay with impact data.
  - *Result*: released on time with the reduced scope; live quotes enabled by flag two weeks later with zero incidents.
  - *Learning*: we added "third-party contract agreed + mock available" to our Definition of Ready.
- Prepare 4–5 stories that can be adapted: conflict with a stakeholder, a production incident, mentoring, a decision you'd change in hindsight, a measurable improvement you drove (performance, a11y, cycle time).

---

## B. Tricky / trap questions

### T1. "Team A has velocity 60, team B has 30. Team A is twice as productive, right?"

**The trap:** treating velocity as a productivity or performance metric.

**Strong answer includes:**
- Points are relative and team-specific; team A's "5" isn't team B's "5". Comparing them is meaningless.
- Using velocity as a target causes **point inflation** and gaming, and discourages quality work (tests, refactoring, a11y) that doesn't "earn points".
- Velocity is a capacity-planning tool for the team itself. For cross-team conversations use outcome metrics, DORA and flow metrics — and even those for learning, not ranking.

---

### T2. "The Scrum Master is basically the team's manager, right?"

**The trap:** equating SM with a project manager or line manager.

**Strong answer includes:**
- The SM has no authority over what developers do or how; the team is self-managing. The SM coaches, facilitates, removes impediments, and works with the organisation to improve how Scrum is applied.
- The Daily Scrum is for the Developers, not a status report to the SM.
- Line management (performance reviews, hiring) sits outside Scrum. Combining line manager and SM in one person often kills psychological safety in retros.

---

### T3. "One story point equals one day, so a 5-point story takes a week."

**The trap:** converting points to time.

**Strong answer includes:**
- Points measure relative size including complexity and uncertainty; the same point value can take different times.
- Once points are converted to hours, you've got time estimates with extra steps — and they get used as commitments.
- If the business needs time, forecast from historical throughput/velocity with ranges and confidence levels, at the level of the whole backlog, not per story.

---

### T4. "The PO asked me directly to squeeze a small change into the sprint. It's only half a day — I just did it."

**The trap:** adding work silently.

**Strong answer includes:**
- Silent additions hide the true cost, put the Sprint Goal at risk, and make forecasting data unreliable ("why did we miss the goal?").
- Correct path: make it visible on the board, check impact on the Sprint Goal with the team and PO, trade something out if needed. Small, urgent things are fine — invisible things aren't.
- If this happens constantly, set up a policy: interrupt buffer, expedite lane (Kanban class of service) with its own WIP limit.

---

### T5. "Our team works well — we can skip retrospectives."

**The trap:** seeing the retro as optional overhead.

**Strong answer includes:**
- Continuous improvement is the core of agile; the retro is the dedicated space for it. "Working well" teams still have things to improve and can plateau.
- If retros feel useless, the fix is the format, not the removal: vary formats, focus on one or two actionable items with owners, follow up on last retro's actions, bring data (cycle time, escaped bugs), make it safe (SM facilitates, managers not present if that inhibits people).
- Shorten or change cadence if needed, but don't drop it.

---

### T6. "What's the difference between the Definition of Done and acceptance criteria? Aren't they the same?"

**The trap:** conflating them.

**Strong answer includes:**
- **Acceptance criteria**: story-specific functional conditions ("given a locked account, when the user logs in, then show the unlock message").
- **DoD**: a global quality standard applied to every item (tests, review, a11y, docs, deployed to staging).
- A story is done only when it meets **both**. A story whose ACs pass but has no tests isn't Done — it doesn't go into the Increment and shouldn't be demoed as complete.

---

### T7. "We're agile, so we don't need documentation or up-front design."

**The trap:** misreading the Manifesto ("working software *over* comprehensive documentation" doesn't mean none).

**Strong answer includes:**
- Just-enough, just-in-time design: ADRs for architecture decisions, API contracts, component docs in Storybook, onboarding notes.
- A shared component library without docs has no adoption. Documentation is part of the DoD for library work.

---

### T8. "Should the designer be part of the Scrum team or hand designs over?"

**The trap:** "they hand designs over two sprints ahead" as the only model (mini-waterfall).

**Strong answer includes:**
- Dual-track (discovery + delivery) is fine, but the designer should be available to the delivery team during the sprint for questions and design QA.
- Big-bang handoffs cause misinterpretation; pairing on states and edge cases and building with design-system components shortens the loop.

---

## C. Code examples

Agile isn't a coding topic, but a few concrete artefacts make answers tangible.

### Frontend Definition of Done (as a PR template checklist)

```markdown
## Checklist (Definition of Done)
- [ ] Acceptance criteria met and verified by PO / on the preview environment
- [ ] Unit/component tests added or updated; e2e for affected critical journeys
- [ ] Keyboard + screen reader checked; axe shows no violations
- [ ] Responsive: mobile / tablet / desktop breakpoints
- [ ] No hard-coded strings; translations keys added
- [ ] Loading, empty and error states implemented
- [ ] Analytics events per tracking plan
- [ ] Behind feature flag `<flag-name>` (if applicable)
- [ ] Library only: Storybook story + docs, changeset added, no unintended public API change
- [ ] Screenshots / recording attached
```

### Feature flag to merge unfinished work safely

```typescript
@Service()
export class FeatureFlags {
  private readonly flags = signal<Record<string, boolean>>({});
  isOn(name: string) {
    return computed(() => this.flags()[name] ?? false);
  }
  load(flags: Record<string, boolean>) {
    this.flags.set(flags);
  }
}

export const featureFlagGuard =
  (flag: string): CanMatchFn =>
  () => inject(FeatureFlags).isOn(flag)();

// routes
export const routes: Routes = [
  {
    path: 'checkout',
    canMatch: [featureFlagGuard('newCheckout')],
    loadComponent: () => import('./checkout-v2/checkout.component').then(m => m.CheckoutComponent),
  },
  { path: 'checkout', loadComponent: () => import('./checkout/checkout.component').then(m => m.CheckoutComponent) },
];
```

(`@Service()` is the v22 decorator; on older versions use `@Injectable({ providedIn: 'root' })`.)

### Little's Law and Monte Carlo — the maths you can say out loud

```text
Cycle time ≈ WIP / Throughput
  WIP = 12 items, throughput = 6 items/week → ~2 weeks
  Cut WIP to 6, same throughput           → ~1 week

Monte Carlo (40 items remaining, last 10 weeks' throughput = [4,6,5,3,7,5,6,4,5,6]):
  repeat 10,000×: sample a week's throughput at random until 40 items are done; record weeks
  → 50th percentile: 8 weeks, 85th percentile: 9 weeks
  "85% confidence we finish within 9 weeks at current scope."
```

---

## D. Red flags

- "Velocity shows how productive we are; we compare teams on it." → "Velocity is a team-internal planning aid; I use outcome, flow and DORA metrics for learning."
- "The Scrum Master assigns tasks in the daily." → "Developers self-organise around the Sprint Goal; the SM facilitates and removes impediments."
- "A story point is a day." → "Points are relative size; forecasts come from historical throughput with ranges."
- "We just add urgent stuff to the sprint." → "Urgent work is made visible and traded off against the Sprint Goal."
- "Retros are a waste of time." → "Retros are how we improve; if they're stale, I change the format and follow up on actions."
- "Done means merged." → "Done means meeting the DoD — tested, accessible, reviewed, deployable — plus the acceptance criteria."
- "Agile means no planning / no documentation." → "Just enough, just in time, and continuously updated."
- "Waterfall is always bad." → "Waterfall fits fixed, regulated or contractual scope; most enterprises are hybrid."
- "Tech debt? We'll do a rewrite later." → "I make debt visible in business terms and pay it down incrementally with the PO."
- "Designers give us the designs and we implement them." → "We collaborate early, share tokens and components, and do design QA together."
- "The third party is late, so we're blocked." → "We agreed the contract early and built against mocks; I escalated with data."
- "I follow the Scrum Guide to the letter." → "I use the framework to get fast feedback and outcomes, and adapt it to context."
- "The daily is where everyone reports what they did yesterday." → "The daily is the Developers re-planning towards the Sprint Goal; blockers get solved after it."
- "Other teams have to wait for the library team." → "We have a contribution model, prereleases and a roadmap so nobody is blocked on us."
- "We hit 100% of our committed points every sprint." → "Consistently hitting 100% usually means padding; I care about the Sprint Goal and outcomes."
- "QA tests it at the end of the sprint." → "QA is involved from refinement; testing happens continuously inside the sprint."

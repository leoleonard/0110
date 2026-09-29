# 10 — Behavioral & Product Rounds

> **How to use this file.** Behavioral rounds at senior level are not a personality chat. They are a structured check that you operate at the *scope* the job needs. Prepare 6–8 real stories, map each to several themes (see the story bank at the end), and rehearse them out loud until each fits into about 2 minutes. The templates below have `[brackets]` for your real facts. The worked examples are **illustrations only**. Replace them with your own stories. Interviewers probe for detail, and made-up stories fall apart by the second follow-up.

---

## 1. How senior behavioral answers are scored

Most companies score behavioral answers on a rubric, often 1–4 per dimension. At senior level they look for these signals:

| Dimension | Mid-level answer | Senior answer |
|---|---|---|
| **Scope** | "I fixed the bug in my component." | "The fix affected 6 teams consuming the library, so I planned the rollout across them." |
| **Ownership** | "The ticket said…" | "Nobody owned it, so I picked it up, defined done, and followed it through to production metrics." |
| **Influence without authority** | "My lead decided." | "I got alignment with a prototype, data and an ADR. Nobody had to be told to do it." |
| **Measurable outcomes** | "It was faster." | "p75 LCP went from 3.4s to 2.1s and checkout conversion rose 1.8% over 4 weeks." |
| **Self-awareness** | "It wasn't my fault." | "Here's what I got wrong, what it cost, and what I changed in how I work." |
| **Collaboration** | "I told design it couldn't be done." | "I brought design, product and QA a trade-off, and we chose together." |
| **Judgement** | Always does the "right" engineering thing | Weighs the engineering ideal against time, risk and business value, and explains why |

Practical tips:
- **Say "I", not "we"**, when describing your own actions. Use "we" for the team context. Interviewers are scoring *you*.
- **Lead with the headline.** Give one sentence with the outcome first, then the story. For example: "This is about cutting our component library's breaking-change incidents to zero. Here's how."
- **Numbers.** If you don't have exact figures, give honest approximations: "roughly 30%", "from about two weeks to three days". Never invent precision.
- **Aim for about 2 minutes.** Let them pull more detail through follow-ups.
- **The candidate's angle:** 7 years commercial, Design Authority on an enterprise project, owner of a shared component library. Most of your strongest stories will involve **cross-team influence, API/contract design, standards and migrations**. Lean into those.

---

## 2. The STAR+L framework

| Letter | What to say | Share of time |
|---|---|---|
| **S — Situation** | Context in 1–2 sentences: product, team size, stakes. | ~10% |
| **T — Task** | Your responsibility or the goal. What would success look like? | ~10% |
| **A — Action** | What **you** did, including the decisions and trade-offs you made. This is the core. | ~50% |
| **R — Result** | Measurable outcome, including business impact. Say what didn't work too. | ~20% |
| **L — Learnings** | What you would do differently, and how it changed your practice since. | ~10% |

The **L** is what separates senior answers. It shows self-awareness and that you apply lessons to later work: "Since then I always…"

---

## 3. Themes

### Theme 1 — Conflict with a colleague or team

**(a) What they're probing:** Can you disagree productively? Do you separate the person from the problem? Do you escalate appropriately, neither too early nor never? Do you use data rather than seniority?

**(b) STAR template**
- **S:** "On [project], [person/role, e.g. a senior dev in another team / the UX lead] and I disagreed about [topic, e.g. whether the date-picker should live in the shared library or be feature-owned]. The stakes were [deadline / N consumers / customer impact]."
- **T:** "As [Design Authority / library owner], I had to [reach a decision that both teams could live with] by [date]."
- **A:** "First I [had a 1:1 to understand their constraints, not debate in the PR thread]. I found their real concern was [X]. I [built a small prototype / gathered data: usage count, bug count, bundle impact] and wrote up [2–3 options with trade-offs]. We agreed on [criteria] before choosing. I [conceded on Y] and held firm on [Z] because [reason]."
- **R:** "We chose [option]. It shipped [on time / N weeks later]. [Metric: e.g. duplicate components went from 3 to 1, and defects in that area dropped from N to M.] The relationship [improved; they later co-owned X]."
- **L:** "I learned to [agree on decision criteria before debating solutions / move contentious threads from PR comments to a call]. Now I [practice]."

**(c) EXAMPLE — replace with your real story**
> "Our checkout team wanted to fork our shared `ui-table` component. They needed inline editing within two sprints, and my library roadmap had it a quarter away. Their lead and I were going back and forth in PR comments, and it was getting tense. So I set up a 30-minute call and asked what 'done' meant for them. It turned out they only needed editing for two column types, not the generic feature on my roadmap. I proposed a middle path. We would add a cell-template slot to the table, which was about three days of work for us. They would build the editing cells in their own feature, and we'd agree to upstream anything reusable later. I also wrote an ADR so other teams wouldn't reopen the fork question. They shipped on time, and we avoided a fork of a component used in 40+ screens. Two months later we upstreamed their editing cells into the library, and three other teams adopted them. What I learned: I had been defending a roadmap instead of solving their problem. Now, when a consuming team pushes back, my first question is always 'what's the minimum you need?'"

**(d) Likely follow-ups:** "What if they'd refused?" · "Did you involve your manager?" · "How did the relationship end up?" · "What would you do if you'd been wrong?" · "How do you handle someone more senior than you?"

**(e) Red flags:** Blaming the other person. The story ends with "I was right". No understanding of the other side's constraints. Escalating straight to a manager. Conflict "resolved" by one side giving up with no follow-up.

---

### Theme 2 — A mistake or failure

**(a) What they're probing:** Honesty, ownership, how you respond under pressure (mitigate, communicate, fix the root cause), and whether you changed the *system*, not just yourself. A trivial or disguised-strength "failure" ("I work too hard") scores badly.

**(b) STAR template**
- **S:** "In [month/year], I [released / approved / designed] [X] for [product]."
- **T:** "It was meant to [goal]."
- **A (the mistake):** "I [skipped / assumed / didn't test] [Y] because [honest reason: time pressure, overconfidence]."
- **A (the response):** "When [symptom: consumers' builds broke / error rate spiked] I [rolled back / hot-fixed] within [time], told [stakeholders] proactively, and ran a [blameless postmortem]."
- **R:** "Impact was [N users / N hours / N teams blocked]. The fix was [X]. We added [systemic change: visual regression, contract test, canary release, changelog check]."
- **L:** "Since then, [the systemic change] has caught [N similar issues]. Personally, I now [habit]."

**(c) EXAMPLE — replace with your real story**
> "About two years ago I released a minor version of our component library that changed the default `z-index` scale for overlays. I considered it an internal refactor, so I didn't flag it as breaking. Within a day, two consuming apps reported that dropdowns were rendering behind their sticky headers in production. One of them was a partner-facing portal. I owned it. I published a patch restoring the old scale within about three hours, messaged all consuming teams in our channel with the impact and workaround, and ran a blameless postmortem the next day. The root cause wasn't really the z-index. We had no way to detect visual or behavioural changes in consumers' contexts. So I added visual regression snapshots for every overlay story in Storybook. I introduced a 'potentially breaking' label that forces a changelog migration note. And I set up a canary step where we test pre-release builds against the two largest consuming apps in CI. Over the following year that canary caught four similar issues before release. My personal lesson: 'internal' is defined by what consumers can observe, not by what I think is internal."

**(d) Likely follow-ups:** "How did you communicate it?" · "What did your manager say?" · "Who else was involved in the decision?" · "How do you decide what counts as a breaking change?" · "What would you do differently on day one?"

**(e) Red flags:** No real failure. Blaming QA or other teams. No systemic fix. Hiding the problem ("I quietly fixed it"). Still defensive about it.

---

### Theme 3 — Mentoring and growing others

**(a) What they're probing:** Do you make other people better, or just do the work yourself? Can you adapt your style to different people? Can you delegate and let others own things? Do you measure growth?

**(b) STAR template**
- **S:** "[Name/role, e.g. a mid-level dev who joined from a React background] was [struggling with / new to] [RxJS / signals / our library contribution process]."
- **T:** "My goal was to get them to [independently deliver X / own Y] within [timeframe]."
- **A:** "I [set up weekly pairing / gave them a well-scoped library component to own end to end / reviewed their PRs with explanations and links rather than rewrites]. I gradually [reduced my involvement: pairing → reviewing → just being available]. I also [created a reusable asset: guide, workshop, contribution docs]."
- **R:** "Within [N months] they [shipped X independently / became a reviewer for the library / presented at a guild]. [Team-level metric: PR review turnaround, onboarding time from N to M weeks.]"
- **L:** "I learned [to resist rewriting their code / to give the 'why' behind review comments]. Now I [practice]."

**(c) EXAMPLE — replace with your real story**
> "When I became library owner, I was the only person approving library PRs. Review turnaround had crept to about four days, and I was the bottleneck. I picked two mid-level developers from consuming teams who had shown interest. I gave each of them ownership of one component family: forms controls for one, overlays for the other. For the first month we paired on every PR in their area. I explained my reasoning out loud: accessibility, API naming, what counts as breaking. I wrote a one-page 'library review checklist' from those sessions so the knowledge didn't stay in my head. In month two they reviewed and I only commented. By month three they approved independently, and we added them to CODEOWNERS. Median review time dropped from about four days to under one. One of them later led our Signal Forms migration for the form controls. The main thing I learned was that I had to let them make choices I wouldn't have made, as long as they weren't harmful. Some of their API naming turned out better than mine."

**(d) Likely follow-ups:** "How did you handle someone who didn't want mentoring?" · "How do you give difficult feedback?" · "How do you know it worked?" · "How do you mentor someone more experienced in another area?"

**(e) Red flags:** "Mentoring" means answering questions on Slack. Taking credit for the mentee's work. No measurable change. Only one style for everyone.

---

### Theme 4 — Owning a design system / shared component library

**(a) What they're probing:** Product thinking applied to internal tools. Your consumers are your customers. They look at API design, versioning and deprecation, adoption and governance, balancing consistency against team autonomy, working with design, and accessibility. This is your strongest area, so make it concrete.

**(b) STAR template**
- **S:** "Our [N] product teams across [N apps] each had [their own buttons/forms/tables], and the result was [inconsistency, duplicated bugs, a11y issues, slow delivery]."
- **T:** "As [Design Authority / library owner], I was responsible for [creating / scaling / stabilising] the shared library and getting adoption without mandating it."
- **A:** "I [ran a component audit: N variants of X]. I [set up contribution model, semver, deprecation policy, Storybook docs, harnesses, visual regression, design tokens synced with Figma]. I [prioritised components by usage × pain]. I [ran office hours / a guild / migration schematics]. For [a contentious API decision] I [wrote an ADR]."
- **R:** "Adoption went from [X% to Y%] of screens. [Duplicate components removed: N.] [UI defect rate / a11y violations dropped by N%.] [Time to build a standard form page: from N days to M.] [Consumer satisfaction survey: N/5.]"
- **L:** "I learned [to treat the library as a product with a roadmap and consumers' feedback / that governance must be light or teams route around it]."

**(c) EXAMPLE — replace with your real story**
> "When I took over our component library, it had about 30 components but only around 40% of screens used it. Teams said it was 'hard to customise and breaks on upgrade'. I treated it as a product. First I audited the four apps and found, for example, seven different modal implementations. I interviewed a developer from each team, and their top three pains were breaking changes, missing slots for customisation, and no docs. So I introduced strict semver with a deprecation policy: a deprecated API is kept for at least one major and ships with an `ng update` migration. I redesigned the most-forked components around content projection and templates instead of dozens of boolean inputs. I set up Storybook with interaction and visual regression tests, and I published component harnesses so consumers' tests stopped breaking on DOM changes. I ran fortnightly office hours. Over about a year, adoption went from roughly 40% to 85% of screens. Five of the seven modals were retired. Automated axe violations across the apps dropped by about 70%. Upgrade-related incidents went to zero for the last three releases. The lesson for me: consistency is earned through a better developer experience, not mandated."

**(d) Likely follow-ups:** "How do you decide what goes into the library vs stays in a feature?" · "How do you handle a team that needs something now?" · "How do you version and release?" · "How do you work with designers and keep Figma and code in sync?" · "How do you measure adoption?" · "What was a component API you got wrong?"

**(e) Red flags:** "Everyone must use it" (mandate without value). No versioning or deprecation story. No accessibility. No measurement of adoption. Being the sole gatekeeper and bottleneck.

---

### Theme 5 — Proposing a measurable improvement

**(a) What they're probing:** Can you find an opportunity, frame it in business terms, get buy-in, deliver, and **prove** the impact? The JD explicitly mentions measurable customer-focused improvements, so expect this.

**(b) STAR template**
- **S:** "I noticed [signal: RUM data showed p75 LCP of Xs on the product page / support tickets about Y / funnel drop-off at step Z]."
- **T:** "I wanted to [improve metric] because [business link: conversion, retention, support cost]."
- **A:** "I [established a baseline with RUM/analytics], [estimated impact / effort], [pitched it to PO/stakeholders with a one-pager], [shipped it incrementally behind a feature flag / A/B test], and [set up a dashboard/alert so it wouldn't regress, e.g. a Lighthouse CI budget]."
- **R:** "[Metric] went from [baseline] to [result] over [period]. Business outcome: [conversion +N%, tickets −N%, time on task −N%]. [Guardrail metrics unchanged.]"
- **L:** "I learned [to agree on the success metric before building / that a baseline is everything]."

**(c) EXAMPLE — replace with your real story**
> "Our customer portal's search-results page had a p75 LCP of about 3.8 seconds on mobile in our RUM data, well above the 2.5-second 'good' threshold. Analytics also showed a 22% bounce rate on that page. I spent a day profiling and found three causes. The hero image wasn't prioritised, a charting library was eagerly loaded for a widget below the fold, and a render-blocking font was loading too early. I wrote a one-page proposal for our PO. It had the baseline, the expected improvement, about four days of effort, and the metric we'd judge it by. It was framed as 'mobile users leave before results render', not 'Lighthouse score'. We shipped it in three small PRs. We used `NgOptimizedImage` with priority on the LCP image, moved the chart into a `@defer (on viewport)` block, and changed font loading to `font-display: swap` with preload. We ran it behind a flag as an A/B split for two weeks. p75 LCP dropped to about 2.2 seconds. Bounce on that page fell from 22% to 17%, and search-to-detail click-through rose about 6%. I added a performance budget to CI so it wouldn't regress. My main lesson: framing it as a customer outcome got it prioritised within one sprint, where 'performance work' had sat in the backlog for months."

**(d) Likely follow-ups:** "How did you know the change caused the improvement?" · "What was the guardrail metric?" · "How did you get it prioritised over features?" · "What if the A/B test had been flat?" · "How do you keep it from regressing?"

**(e) Red flags:** No baseline. Only lab metrics (Lighthouse) and no field data. Correlation claimed as causation. "Improvement" without a customer or business link. Working on it secretly without buy-in.

---

### Theme 6 — Communicating with stakeholders (non-technical and 3rd-party partners)

**(a) What they're probing:** Can you translate technical things into impact, risk and options? Can you manage expectations, say no or "not yet" constructively, and work with external partners whose priorities differ from yours? The JD mentions third-party communication explicitly.

**(b) STAR template**
- **S:** "We depended on [3rd-party partner: payment provider / data vendor / external agency] for [X], and [problem: their API changed without notice / their SLA was missed / a feature needed their change]."
- **T:** "I needed to [unblock the release / agree a contract / set expectations with our business stakeholders]."
- **A:** "With the partner, I [wrote a precise reproduction with request/response samples in Postman/Swagger terms, agreed a single point of contact, proposed a contract/versioning approach]. Internally, I [explained the impact to [PO/sales/ops] in business terms — who is affected, what the options are, what each costs], [gave a date range with confidence levels], [sent short written updates at a regular cadence]. Technically, I [isolated the partner behind an adapter / added a fallback / feature flag] so we weren't blocked."
- **R:** "[Release shipped on date / N days late with stakeholder agreement]. [Partner adopted versioned endpoints / contract tests.] [Incident count from that integration dropped from N to M.]"
- **L:** "I learned [to put agreements in writing / to give options, not problems / to over-communicate during incidents]."

**(c) EXAMPLE — replace with your real story**
> "We integrated a third-party logistics partner's tracking API into our customer order page. Two weeks before a marketing launch, they changed the status codes in their response without versioning the endpoint. Our tracking widget started showing 'Unknown' for about 15% of orders. I did three things in parallel. For the partner, I sent a precise reproduction: the endpoint, sample requests and responses, the diff against their published Swagger spec, and the business impact. I asked for either a rollback or a versioned endpoint plus a changelog, and requested a named technical contact. Internally, I told our PO and the customer-service lead in plain terms: which customers were affected, what they saw, and two options. Option one was a quick mapping fix on our side, ready in a day but fragile. Option two was waiting for the partner, with an unknown date. They chose the quick fix, and I sent a short written status every morning until it was resolved. Technically, the partner was already behind an adapter, so the fix was a single mapping change plus a contract test in CI against their spec. We launched on time. The partner introduced a versioned v2 within a month. The contract test later caught two more unannounced changes before they reached production. My lesson: with partners, a crisp reproduction and a written agreement get you much further than escalation."

**(d) Likely follow-ups:** "How did you explain the trade-off to non-technical people?" · "What if the partner was unresponsive?" · "How do you handle a stakeholder who wants a date you can't commit to?" · "How do you say no to a stakeholder?"

**(e) Red flags:** Jargon with non-technical stakeholders. Blaming the partner publicly. No written follow-up. Hiding bad news until the deadline. "That's the PM's job."

---

### Theme 7 — Disagreeing with a decision (disagree and commit)

**(a) What they're probing:** Do you voice concerns clearly and early, with evidence? Once a decision is made, do you commit fully (no sabotage, no "I told you so")? Do you know when a decision is worth escalating?

**(b) STAR template**
- **S:** "[Leadership / architect / product] decided to [decision, e.g. adopt a micro-frontend framework / skip the Angular upgrade this year / ship without a11y fixes]."
- **T:** "I believed [concern] because [evidence]."
- **A:** "I [raised it in the right forum, written, with data: risk, cost, alternatives]. I [proposed a reversible/limited version: a pilot, a time box, a revisit date]. The decision [stood / was modified]. I then [committed: delivered it well, documented the risks in an ADR, set up metrics to monitor the risk I had flagged]."
- **R:** "[Outcome — ideally honest: it worked better than I feared / the risk materialised and we had the monitoring to catch it early.]"
- **L:** "I learned [that disagreeing well means offering a cheap way to test the concern / that I was missing context the decision-makers had]."

**(c) EXAMPLE — replace with your real story**
> "Our architecture group decided to split the main application into micro-frontends using Module Federation, mainly so teams could deploy independently. As Design Authority for the frontend, I was concerned about three things: duplicated Angular runtimes, version skew in the shared component library, and the operational cost for a team of our size. We had about 12 frontend developers. I wrote a two-page response with rough numbers. I estimated bundle-size growth from our current build and listed the library versioning problems we'd need to solve. I also offered an alternative: an Nx monorepo with enforced boundaries and affected-only deployments. The group kept the decision. The deciding factor was a planned acquisition bringing in another team with its own release cycle, which I hadn't known about. I committed fully. I wrote the ADR, including my risks as 'known consequences'. I designed the shared-library strategy: singleton shared dependencies and a strict compatibility matrix. And I added bundle-size and version-skew checks to CI. Version skew did bite us once, and the CI check caught it before production. In hindsight, the decision was right for the business context. My lesson: disagree with data, offer a cheap way to test the concern, and assume the decision-makers may have context you don't."

**(d) Likely follow-ups:** "What if you'd been proven right?" · "Have you ever *not* committed?" · "When would you escalate further?" · "How did you represent the decision to your team when you disagreed?"

**(e) Red flags:** Passive resistance or slow-walking. "I told you so." Never disagreeing with anything. Disagreeing on taste rather than evidence. Undermining the decision in front of the team.

---

## 4. Further common questions (concise guidance)

### 4.1 "Tell me about yourself" (90-second pitch)
Structure: **present → past highlights → why this role**. Keep it to about 90 seconds.
> "I'm a senior frontend developer with [7] years building [enterprise Angular applications for domain X]. Currently I'm [Design Authority] on [project: N developers, N apps], where I own [the shared component library used by N teams]. A couple of things I'm proud of: [measurable achievement 1, e.g. took library adoption from 40% to 85%] and [achievement 2, e.g. led the migration to standalone/signals/zoneless with zero downtime]. What I enjoy most is [the intersection of solid architecture and measurable customer impact]. That's why this role caught my eye: [specific JD hook, e.g. cross-functional work on measurable improvements with third-party partners]."

Don't retell your whole CV. Don't open with education. End on why *this* role.

### 4.2 "Why are you leaving?"
Keep it positive and forward-looking: "I've [achieved X]. I'm looking for [more product impact / a different domain / a bigger scale]." Never criticise your current employer, even if they deserve it. Keep it to one or two sentences, then pivot to what attracts you here.

### 4.3 "Why us?"
Mention something specific: their product, their customers, a talk or blog post by their engineering team, their tech stack, and the JD's focus on measurable customer impact and partners. Link it to your experience: "You mention X. I've done Y, and I'd like to do more of it."

### 4.4 "How do you prioritise?"
Name a framework, then show judgement. Examples: impact vs effort, cost of delay, RICE (Reach, Impact, Confidence, Effort). Distinguish urgent from important. Protect a slice of capacity for debt and library consumers. Make trade-offs visible to the PO rather than silently absorbing them. "When everything is priority one, I ask which outcome matters most this quarter and work backwards from that."

### 4.5 "How do you measure frontend success?"
Use layers:
- **User experience:** Core Web Vitals from field data (RUM): LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1 at p75. INP replaced FID in March 2024.
- **Reliability:** JS error rate per session, failed API calls, crash-free sessions (Sentry or similar).
- **Product outcomes:** funnel conversion, task success rate, time on task, drop-off per step, feature adoption.
- **Delivery (DORA-style):** lead time, deployment frequency, change failure rate, time to restore.
- **Quality and a11y:** escaped defects, axe violations, WCAG conformance level.
- **Internal (library):** adoption %, number of duplicate components, upgrade lag of consumers.

### 4.6 "Suggest a measurable, customer-focused improvement to our product."
Some interviewers ask this directly. Prepare by looking at their site or app before the interview.
1. **Observe:** "I looked at your [signup/checkout] on mobile. [Observation: slow LCP, layout shift, unclear error message, 7-step form]."
2. **Hypothesis:** "I suspect [drop-off at step N] because [reason]."
3. **Measure first:** "I'd check funnel analytics and RUM to confirm, and make sure events are instrumented: step viewed, field error, submit, success."
4. **Change:** a small, reversible experiment behind a flag.
5. **Evaluate:** A/B test with a primary metric (e.g. completion rate), a guardrail metric (e.g. error rate, INP), and enough sample size and duration to avoid peeking bias.
6. **Scale or roll back.**

Mention that you'd **instrument analytics** carefully: a consistent event taxonomy, consent/GDPR compliance, and no PII in events.

### 4.7 "What's the difference between output and outcome?"
Output is what you shipped. Outcome is what changed for users or the business. Seniors talk about outcomes: "We shipped the new filter (output), and time-to-find-product dropped 20% (outcome)."

### 4.8 "Tell me about a time you had to deliver under a tight deadline."
Show that you cut **scope, not quality**. Negotiate an MVP, sequence the risky parts first, communicate early, and record any debt you deliberately take on with a follow-up ticket.

### 4.9 "How do you work with designers and product managers?"
Involve yourself early (discovery and design critiques), feed back on feasibility and component reuse, use shared design tokens and a single source of truth (Figma ↔ library), agree on acceptance criteria including accessibility and states (empty, error, loading), and demo early.

### 4.10 "How do you handle ambiguity or unclear requirements?"
Ask clarifying questions framed around the user and the outcome. Write down assumptions and share them. Build a thin slice or prototype to get feedback. Define what "done" and "success" mean before building.

### 4.11 "How do you keep up to date with Angular / frontend?"
Be specific and recent: Angular release notes and RFCs (signals, zoneless, Signal Forms stable in v22, OnPush default in v22), the blog, conference talks, and trying things on a side branch. Mention how you **bring it to the team**: a guild, tech talks, evaluation ADRs. Avoid just saying "I read Medium."

### 4.12 "What's your biggest weakness?"
Pick a real, non-fatal weakness, and show what you're actively doing about it and the evidence of progress. Example: "I tend to take on library fixes myself instead of delegating. I've been deliberately routing them to the two co-owners and reviewing instead. Our bus factor went from one to three."

### 4.13 "Where do you see yourself in 3–5 years?"
Align it with the role's growth path (staff/principal IC, or tech lead) and be honest. "Deepening impact across teams, e.g. owning frontend platform direction" works well for an IC track.

---

## 5. Story bank worksheet

Fill this in before the interview. Aim for 6–8 stories that together cover every theme at least twice. Each story should have at least one hard number.

| # | Story (one-line title) | Themes covered (Conflict / Failure / Mentoring / Library ownership / Measurable improvement / Stakeholders & partners / Disagree & commit / Deadline / Ambiguity / Leadership) | Key metrics (before → after) | Your role in one line | Learning (the "L") |
|---|---|---|---|---|---|
| 1 | [e.g. Library adoption push] | [Library ownership, Influence, Stakeholders] | [adoption 40% → 85%; duplicates 7 → 2] | [Owner, drove roadmap] | [Consistency is earned through DX] |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |

**Coverage check:** for each theme, write which story numbers cover it. Any theme with fewer than two stories needs another one.

| Theme | Stories |
|---|---|
| Conflict | |
| Mistake / failure | |
| Mentoring | |
| Design system / library ownership | |
| Measurable improvement | |
| Stakeholders & 3rd-party partners | |
| Disagree & commit | |
| Tight deadline / scope trade-off | |
| Ambiguity | |

**Final checklist per story:**
- Can I tell it in 2 minutes?
- Is "I" clear?
- Is there a number?
- Is there a learning I've since applied?
- Can I answer three levels of "why?" and "what exactly did you do?"

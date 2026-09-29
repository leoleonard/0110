# 12 — Questions to Ask Them

> **How to use this file.** "Do you have any questions for us?" is part of the assessment. A senior candidate uses it to show how they think (engineering maturity, product outcomes, team health) and to find out whether the job matches the description. Pick **3–4 questions** to suit the interviewer: engineering questions for engineers, product and outcome questions for PMs or heads of product, and growth and team questions for managers. Listen to the answer and ask one follow-up. That matters more than asking many questions. Write down anything you want to raise with the next interviewer.

Each question below includes: **why it's smart**, **what the answer reveals**, and **green vs red flags**.

---

## Engineering

### 1. "Which Angular version are you on, and how do you approach major upgrades?"

- **Why it's smart:** Angular releases a major version roughly every six months. The current release is v22, and v20 and v21 are still on LTS. The answer tells you how much legacy work to expect (NgModules, `*ngIf`, zone.js, Karma) and how the organisation values maintenance. It also shows you know the landscape. Angular 22 made OnPush the default and stabilised Signal Forms, and v21 made zoneless and Vitest the defaults.
- **What it reveals:** Whether upgrades are routine (`ng update` every cycle) or a dreaded multi-month project. Whether anyone owns the platform.
- **Green flags:** "We're on 21/22 and upgrade within a few months of each release." "We've migrated to standalone and control flow, and we're moving to signals and zoneless incrementally." "There's a platform/guild owner."
- **Red flags:** "We're on 12 and there's no plan." "Upgrades are done when something breaks." "We tried and gave up." None of these rules the job out if they want you to lead the upgrade, but ask about mandate and time allocation.
- **Follow-up:** "Is the upgrade work planned into the roadmap, or squeezed in?"

### 2. "How do you manage state today? NgRx, SignalStore, services with signals? How did you decide?"

- **Why it's smart:** The JD lists Flux/Redux. You want to know whether that means classic NgRx boilerplate everywhere, a sensible mix, or an ongoing migration. The "how did you decide" part tests whether they make decisions deliberately (ADRs) or by fashion.
- **What it reveals:** Architectural maturity and consistency. Whether there are clear conventions or five patterns co-existing without a plan.
- **Green flags:** Clear guidance on "global vs feature vs local state". A documented decision. A migration path to `@ngrx/signals` or signals, with reasons.
- **Red flags:** "Everything goes in the store, even form state." "Each team does its own thing." "We don't really know why."

### 3. "What does your testing strategy look like, and what's the relationship between tests and releases?"

- **Why it's smart:** Testing is in the JD. The second half of the question shows whether tests actually protect production (gating CI, deploy confidence) or are a formality.
- **What it reveals:** The ratio of unit to integration to E2E. The test runner (Vitest is the default since v21, and Karma is legacy). Flaky-test culture. Contract tests with third-party APIs. Visual regression for the UI library.
- **Green flags:** "Tests run on every PR and block merge." "Critical journeys are covered with Playwright." "We track flaky tests." "We have contract tests against partner APIs."
- **Red flags:** "QA tests it manually before release." "We have a 100% coverage target" (a metric-chasing culture). "E2E tests are red most of the time, so we ignore them."

---

## Product & customer impact

### 4. "The role mentions measurable, customer-focused improvements. Can you give an example of a recent one, and how you measured it?"

- **Why it's smart:** It takes the JD at its word and asks for evidence. It shows you think in outcomes rather than outputs.
- **What it reveals:** Whether there's real analytics, RUM and experimentation infrastructure, or whether "measurable" is aspirational. Whether engineers are involved in defining success metrics.
- **Green flags:** A specific story with a metric: "we cut checkout errors by X%" or "INP improved, and conversion moved". Engineers see dashboards. There's an A/B testing capability.
- **Red flags:** Vague answers ("we care about users"). Metrics owned only by product and never shared with engineering. No field performance data (RUM).

### 5. "How do you work with your third-party partners day to day? Who owns the relationship and the API contract?"

- **Why it's smart:** The JD specifically mentions third-party communication. Partner integrations are a major source of incidents and delays, and you've dealt with them before.
- **What it reveals:** Whether developers talk to partners directly or through layers of account managers. Whether there are OpenAPI/Swagger contracts, sandbox environments, versioning, and SLAs.
- **Green flags:** "Named technical contacts, shared Swagger specs, sandbox environments, and contract tests in CI." "Engineers join partner calls when needed."
- **Red flags:** "Partners change APIs without notice and we find out in production." "Everything goes through an account manager, and it takes weeks."

### 6. "How are product priorities set, and how much say does engineering have, for example over technical debt or performance work?"

- **Why it's smart:** It tests whether the cross-functional collaboration in the JD is real, and whether you'd be able to pay down debt.
- **What it reveals:** Whether the team is feature-factory or outcome-driven. Whether capacity for debt is reserved. How trade-offs are negotiated with the PO.
- **Green flags:** "Engineers join discovery and planning." "We reserve roughly 15–20% for tech health." "Tech debt items are on the same backlog with business framing."
- **Red flags:** "Product decides, engineering executes." "We do a hardening sprint once a year." "Roadmap is fixed by sales commitments."

---

## Team & process

### 7. "Is there a shared component library or design system? Who owns it, and how do teams contribute?"

- **Why it's smart:** This is your core strength (Design Authority, library owner). It shows where you could have impact quickly, and what political territory you'd be walking into.
- **What it reveals:** Whether there's a design system, whether it's healthy (versioned, documented, adopted), whether there's a designer partner, and whether governance is too loose or too strict.
- **Green flags:** A dedicated owner or a federated model with a contribution guide, Storybook, semver and a design-token pipeline. Or: "We don't have one and want someone to lead it", which is a great opportunity if it comes with a mandate.
- **Red flags:** "Each team has its own copy of the button." "It was built by someone who left and nobody touches it." "It's owned by a separate team who never accepts contributions."

### 8. "What does your release cadence look like, from merged PR to production?"

- **Why it's smart:** Deployment frequency and lead time are strong predictors of team health (DORA). The answer tells you how quickly your improvements will reach customers.
- **What it reveals:** CI/CD maturity, feature flags, environments, approval gates, and whether they use Scrum, Kanban or waterfall-style release trains in practice. (The JD lists all three.)
- **Green flags:** "Several times a day or week, behind feature flags, with automated checks." "Rollback takes minutes."
- **Red flags:** "Quarterly releases with a two-week code freeze." "Manual deployments by one person." "A change approval board for every release."

### 9. "What does code review look like here, and how are architecture decisions made and recorded?"

- **Why it's smart:** It addresses code quality and design patterns in the JD, and it tells you how your Design Authority experience would fit.
- **What it reveals:** Review culture (turnaround, tone, automation), whether decisions are recorded as ADRs or made in hallway conversations, and who has the final say.
- **Green flags:** "PRs reviewed within a day, lint and format are automated, ADRs are in the repo, and there's an architecture guild open to everyone."
- **Red flags:** "One architect approves everything." "PRs sit for a week." "We don't really do reviews when we're busy."

---

## Growth & success

### 10. "What would success look like for this role after 6 and 12 months? What's the biggest challenge the person in this role will face?"

- **Why it's smart:** It gets the interviewer to picture you in the role, and it reveals the real expectations, which may differ from the JD. The "biggest challenge" part often surfaces the honest truth: legacy code, politics, an understaffed team.
- **What it reveals:** Whether expectations are clear and realistic, whether this is a backfill or a new role, and the scope (IC depth vs leadership).
- **Green flags:** Concrete outcomes ("own the frontend platform", "lead the migration to signals", "improve Core Web Vitals on key flows") with support and a realistic timeline.
- **Red flags:** "Just close tickets." Unclear or contradictory answers between interviewers. "The last three people left within a year."
- **Follow-up (manager):** "How does the career path look for senior ICs here? Is there a staff or principal track?"

---

## Questions NOT to ask (or not yet)

- **Anything easily found on their website or in the JD** ("What does the company do?"). It signals zero preparation.
- **Salary, bonus, holidays or remote policy in the first technical round.** Save these for the recruiter or the offer stage, unless the interviewer brings them up.
- **"Did I get the job?" / "How did I do?"** It puts the interviewer on the spot. Ask about next steps and timeline instead.
- **Questions that sound like complaints about your current job** ("Do you have lots of pointless meetings like my current place?").
- **Gotcha questions meant to show off** ("Why aren't you using technology X? It's clearly better"). Curiosity is fine. Point-scoring isn't.
- **"What's the work-life balance like?" as your only question.** It's legitimate, but phrase it concretely and pair it with engineering questions: "How often do people work outside normal hours, e.g. for releases or incidents? How is on-call organised?"
- **Yes/no questions** ("Do you do code reviews?"). Ask "how" and "what" questions so the answer tells you something.

---

## How to close the interview

1. **Summarise your fit in 20–30 seconds, tied to what you heard:** "From what you've said, you need someone who can [lead the component library / drive measurable UX improvements / work directly with partners]. That's what I've been doing as Design Authority at [company], for example [one-line achievement with a number]."
2. **Address any doubt openly:** "Is there anything in my background you'd like me to clarify, or any concern I could address?" This lets you fix a misunderstanding while you're still in the room.
3. **Ask about next steps:** "What are the next steps, and what's your timeline?"
4. **Thank them for something specific** they told you, such as their migration story. It shows you were listening.
5. **Afterwards:** send a short thank-you note (via the recruiter if appropriate) that mentions one specific thing from the conversation. Write down the questions you were asked while they're fresh, to prepare for the next round.

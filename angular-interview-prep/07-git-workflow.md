# 07 — Git, Branching, Code Review & CI/CD

> Use this file to prepare for the "how does your team ship code" part of the interview. Interviewers aren't testing whether you know `git commit`. They want to know if you can **keep history useful** (rebase/merge/squash choices and why), **recover when things go wrong** (reflog, revert, bisect) without panicking, **choose a branching strategy that fits the release model**, **review code like a senior** (constructive, focused on risk, small PRs) and **own a pipeline** across GitLab, GitHub and Bitbucket. As owner of a shared component library, expect questions about versioning, changelogs and releasing to other teams.

---

## A. Most commonly asked questions

### Q1. Rebase vs merge — when do you use which?

**Answer (1–2 min):**
- **Merge** creates a merge commit joining two histories. Non-destructive, preserves the true timeline, safe on shared branches. Downside: noisy history with lots of "Merge branch 'main' into feature" commits.
- **Rebase** replays your commits on top of another base, producing new commit SHAs and a linear history. Cleaner `git log`, easier bisect and review. Downside: **rewrites history**.
- **Golden rule: never rebase commits that others have based work on** (shared branches like `main`, `develop`, release branches, or a feature branch two people push to).
- My default: rebase my *own* feature branch onto the latest `main` to stay current (`git pull --rebase`), then integrate via the team's chosen merge method (often squash or merge commit, depending on policy).
- After rebasing a pushed branch, use `git push --force-with-lease` — it refuses if the remote has commits you haven't seen, unlike `--force`, which silently deletes a colleague's work.

```bash
git fetch origin
git rebase origin/main          # replay my commits on top of main
# resolve conflicts → git add … → git rebase --continue
git push --force-with-lease     # safe force-push of my own branch
```

---

### Q2. Squash merge vs merge commit vs rebase merge?

**Answer:**

| Strategy | History on main | Pros | Cons |
|---|---|---|---|
| Merge commit | all branch commits + merge commit | full context, easy to revert a whole feature (`git revert -m 1`) | noisy, non-linear |
| Squash merge | one commit per PR | clean, one PR = one commit = easy revert, WIP commits disappear | loses granular history; big PRs become one huge commit that's hard to bisect; branch can't be reused after squash |
| Rebase merge (fast-forward) | each commit replayed linearly | linear and granular | requires commits to be clean and individually meaningful |

- "For product apps with small PRs, squash merge is a good default — the PR is the unit of change. For a component library where commit messages drive the changelog, I want each commit meaningful, so either squash with a conventional-commit PR title or rebase-merge with curated commits."
- Enforce the policy in repo settings so it's consistent.

---

### Q3. What do you use interactive rebase for?

**Answer:**
Cleaning up **my own, not-yet-shared (or only-me) history** before review: squash "fix typo" commits, reword messages, reorder, split commits, drop debug commits.

```bash
git rebase -i origin/main
# pick   a1b2c3 feat(button): add loading state
# fixup  d4e5f6 fix lint
# reword 789abc feat(button): aria-busy while loading
# drop   0ff1ce console.log debugging
```

- `fixup` commits + autosquash: `git commit --fixup=a1b2c3`, then `git rebase -i --autosquash origin/main`.
- `edit` to stop at a commit and split it (`git reset HEAD^`, commit in parts, `git rebase --continue`).
- `git rebase --abort` gets you back to where you started if it goes wrong.

---

### Q4. When do you cherry-pick, and what are the risks?

**Answer:**
- Main use: **backporting a hotfix** to a release/maintenance branch (e.g. a fix merged to `main` also needed on `release/4.2` of the component library).
- `git cherry-pick -x <sha>` — `-x` appends "(cherry picked from commit …)" for traceability.
- Risks: it creates a **new commit with a different SHA** and the same change. Later merges of those branches may conflict or show duplicate commits; tools can't tell they're "the same". Cherry-picking a commit that depends on earlier commits drags in conflicts or subtly broken code.
- Better pattern for hotfixes: fix on the oldest supported branch and merge forward, or fix on `main` and cherry-pick with `-x` into release branches — pick one direction and stick to it.

```bash
git switch release/4.2
git cherry-pick -x 3f9e2ab           # hotfix from main
git cherry-pick -x A^..B             # a range, inclusive of A
```

---

### Q5. You ran `git reset --hard` and lost work. How do you get it back?

**Answer:**
- Commits are rarely truly lost. **`git reflog`** records every position `HEAD` (and each branch) has pointed to, locally, for ~90 days by default.

```bash
git reflog
# 4c2a1d9 HEAD@{0}: reset: moving to origin/main
# e7f8a90 HEAD@{1}: commit: feat(table): sticky header
# ...
git branch rescue e7f8a90          # or: git reset --hard HEAD@{1}
```

- Also works after a bad rebase: find the pre-rebase entry (`HEAD@{n}: rebase (start)` — the one before it) or use `ORIG_HEAD`.
- Deleted branch: `git reflog` / `git reflog show <branch>` if you remember, or find the SHA in the PR/MR.
- What is **not** recoverable by reflog: uncommitted changes wiped by `reset --hard` or `checkout -- .`. Partial chance: `git fsck --lost-found` for staged blobs (things you had `git add`ed). Lesson: commit or stash early — "commits are cheap, WIP commits get squashed anyway".
- Reflog is local only; a colleague's reflog won't have your commits.

---

### Q6. How do you resolve merge conflicts efficiently?

**Answer:**
- Understand both sides before editing: `git log --merge -p`, or `git diff` with `merge.conflictStyle=zdiff3` so you see the common ancestor, not just "ours" and "theirs".
- Resolve semantically, not textually — sometimes both changes must be combined; run the tests/build afterwards, a clean textual merge can still be broken.
- **`git rerere`** (`git config --global rerere.enabled true`) remembers how you resolved a conflict and reapplies it — very helpful when repeatedly rebasing a long branch.
- **Lockfiles** (`package-lock.json`): don't hand-merge. Take one side and regenerate: `git checkout --theirs package-lock.json && npm install` (then verify), or rebuild from the merged `package.json`. Review the resulting dependency diff.
- Generated files (API clients, snapshots): regenerate rather than merge.
- Prevention beats cure: small, short-lived branches, frequent rebase onto main, avoid mass reformatting in feature PRs (do it in a separate PR, add the SHA to `.git-blame-ignore-revs`).

---

### Q7. How does `git bisect` work? Have you used it?

**Answer:**
Binary search over history to find the commit that introduced a bug: O(log n) steps.

```bash
git bisect start
git bisect bad                  # current commit is broken
git bisect good v18.3.0         # last known good tag
# git checks out a midpoint; test it, then:
git bisect good | bad
# ... repeat ...
git bisect reset

# automated: script exits 0 = good, 1–124 = bad, 125 = skip
git bisect run npx vitest run src/app/table/table.component.spec.ts
```

- "Bisect is where history hygiene pays off: every commit on main should build and pass tests. Giant squashed commits give you 'the bug is somewhere in this 3,000-line change'."
- `git bisect skip` for commits that don't build.

---

### Q8. `git stash` — when and gotchas?

**Answer:**
- Quick context switch: `git stash push -m "wip table filters"`, `git stash list`, `git stash pop` (apply + drop) or `apply` (keep).
- `-u` to include untracked files; `git stash push -- path/` to stash specific files; `git stash branch <name>` to turn a stash into a branch when it conflicts.
- Gotchas: stashes are easy to forget and aren't pushed anywhere. For anything longer than a few minutes, a WIP commit on a branch (or `git worktree add` to work on a second branch in parallel) is safer.

---

### Q9. `revert` vs `reset` (soft / mixed / hard)?

**Answer:**
- **`git revert <sha>`** creates a new commit that undoes a previous one. History is preserved → **the only correct way to undo on shared branches**. For a merge commit: `git revert -m 1 <merge-sha>`.
- **`git reset`** moves the branch pointer (rewrites local history):
  - `--soft` — move HEAD, keep changes **staged** (e.g. re-do the last commit message or combine commits).
  - `--mixed` (default) — move HEAD, keep changes **in working tree, unstaged**.
  - `--hard` — move HEAD and **discard** working-tree changes. Dangerous; reflog saves commits, not uncommitted changes.
- Gotcha: reverting a merged feature and later re-merging the same branch does nothing (Git thinks the commits are already in). You must "revert the revert".

```bash
git reset --soft HEAD~3     # squash last 3 local commits into one new commit
git commit -m "feat(dialog): focus trap"
```

---

### Q10. GitFlow vs GitHub Flow vs trunk-based development?

**Answer (1–2 min):**
- **GitFlow**: `main` + `develop` + `feature/*` + `release/*` + `hotfix/*`. Fits **scheduled, versioned releases** with multiple supported versions (installed software, mobile apps with store review, a library with LTS lines). Costs: long-lived branches, merge overhead, slow feedback. Its author now recommends simpler flows for continuously delivered web apps.
- **GitHub Flow**: `main` is always deployable; short-lived feature branch → PR → review + CI → merge → deploy. Simple, good default for web apps.
- **Trunk-based**: everyone integrates into `main` at least daily, branches live hours to a couple of days, incomplete work hidden behind **feature flags**; optional short-lived **release branches** cut from trunk for stabilisation/hotfixes. Highest delivery performance in DORA research, but needs strong CI, good test coverage and flag discipline.
- "For an Angular SPA deployed continuously I'd go trunk-based or GitHub Flow with feature flags. For the shared component library consumed by several apps, I'd keep trunk-based development but add release branches (`release/5.x`) to backport fixes to supported majors."

**Go deeper:**
- Feature flags: decouple deploy from release, enable canary/percentage rollouts and kill switches. Cost: flag debt — every flag needs an owner and removal date.
- Environments are not branches: avoid `dev`/`staging`/`prod` branches; promote the *same build artifact* through environments.

---

### Q11. How does Git strategy change in a monorepo (Nx)?

**Answer:**
- One PR can change a library and all its consumers atomically — no version-bump dance; this is the big win for a shared component library used by apps in the same repo.
- CI must not build/test everything on every change: **Nx affected** (`nx affected -t lint test build --base=origin/main --head=HEAD`) computes the projects impacted via the project graph. Combine with Nx computation caching (local/remote) so unchanged work is restored rather than recomputed.
- Needs: CODEOWNERS per library, module boundary lint rules (`@nx/enforce-module-boundaries` with tags) so apps can't deep-import library internals, and a shallow clone caveat (CI needs enough history to find the base SHA — `fetch-depth: 0` or `nrwl/nx-set-shas`).
- Publishing libraries from a monorepo: Nx Release, changesets or semantic-release with per-package config.

---

### Q12. Conventional commits and automated versioning — why do they matter for a component library?

**Answer:**
- **Conventional Commits**: `type(scope): subject` — `feat(button): add loading state`, `fix(table): keep sort on page change`, `feat(dialog)!: remove deprecated size input` plus `BREAKING CHANGE:` footer.
- Mapping to **SemVer**: `fix` → patch, `feat` → minor, `!`/`BREAKING CHANGE` → major.
- **semantic-release**: fully automated — on merge to main it analyses commits, decides the version, tags, generates the changelog, publishes to npm/registry. Great with strict commit discipline (enforce with commitlint + husky, or check the PR title when squash merging).
- **Changesets**: developers add a small markdown file per PR describing the change and bump type; a "Version Packages" PR aggregates them. More explicit and human-written changelogs, works well for monorepos with multiple packages.
- "For a design-system library consumed by other teams, the changelog is the product's communication channel. I'd choose changesets for human-readable notes with migration steps, deprecate before removing, and ship `ng update` schematics for breaking changes where feasible."

---

### Q13. What do you look for in a code review as a senior?

**Answer (1–2 min):**
- **Order of attention**: correctness and requirements → architecture/boundaries (does it belong here? right layer?) → risk (security, performance, accessibility, breaking public API of the library) → tests (do they test behaviour, would they catch a regression?) → readability/naming → style (which should be automated by lint/prettier, not humans).
- Angular-specific: signal/change detection correctness (OnPush default in v22 — mutation without signals won't render), subscription leaks (`takeUntilDestroyed`), `track` expressions in `@for`, no logic in templates, a11y (labels, focus, keyboard), lazy loading and bundle impact, public API surface of the library.
- **PR size**: aim for under ~400 changed lines; big PRs get rubber-stamped. Split by refactor-first, then feature; stacked PRs if needed.
- **Tone**: ask questions, explain *why*, label comments (`nit:`, `suggestion:`, `blocking:`), praise good things, review the code not the person. Conventional Comments is a nice format.
- **Process**: CODEOWNERS for automatic reviewers (e.g. design-system team owns `libs/ui/**`), review SLA (e.g. first response within one working day — unreviewed PRs are WIP inventory), PR template with checklist (tests, screenshots, a11y, breaking changes), and approve-with-comments for nits to avoid blocking.

```text
# .github/CODEOWNERS  (GitLab: CODEOWNERS with the same syntax + sections)
/libs/ui/                     @acme/design-system
/libs/ui/src/tokens/          @acme/design-authority
/apps/portal/src/app/payments/ @acme/payments-team
*.yml                         @acme/platform
```

---

### Q14. Walk me through a CI/CD pipeline for an Angular app.

**Answer (1–2 min):**
- Stages: **install** (`npm ci` — reproducible from lockfile, fails if out of sync) → **lint + typecheck** → **unit tests** (Vitest default for new projects since v21; Karma on older ones) with coverage → **build** (production, output hashing) → **e2e** (Playwright/Cypress against the built app) → **deploy** to preview/staging → gated deploy to production.
- Speed: cache the npm cache (`~/.npm`) keyed on `package-lock.json` hash (not `node_modules` directly with `npm ci`, which deletes it); run lint/test in parallel; `nx affected` in monorepos; upload build artifact once and deploy the same artifact everywhere.
- Quality gates: required checks on protected branches, coverage thresholds (sensible, not 100%), bundle budgets in `angular.json` fail the build, dependency audit, Lighthouse CI for performance/a11y where it matters.
- Merge/pull request pipelines give fast feedback; deploys run only on main/tags.

**GitLab CI** (`.gitlab-ci.yml`):

```yaml
default:
  image: node:22
  cache:
    key:
      files: [package-lock.json]
    paths: [.npm/]

variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

stages: [install, verify, build, e2e, deploy]

workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

install:
  stage: install
  script: [npm ci]
  artifacts:
    paths: [node_modules/]
    expire_in: 1 hour

lint:
  stage: verify
  script: [npx ng lint]

test:
  stage: verify
  script: [npx ng test --coverage]
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      junit: reports/junit.xml

build:
  stage: build
  script: [npx ng build --configuration production]
  artifacts:
    paths: [dist/]

e2e:
  stage: e2e
  image: mcr.microsoft.com/playwright:v1.55.0-noble
  script: [npx playwright test]
  artifacts:
    when: on_failure
    paths: [playwright-report/]

deploy_staging:
  stage: deploy
  environment: staging
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script: [./scripts/deploy.sh staging dist/app/browser]

deploy_prod:
  stage: deploy
  environment: production
  rules:
    - if: $CI_COMMIT_TAG
      when: manual
  script: [./scripts/deploy.sh production dist/app/browser]
```

(Pin the Playwright image to the version in your lockfile. The deploy script should upload hashed assets with long-lived immutable caching and `index.html` with `no-cache` — see file 06.)

**GitHub Actions** (`.github/workflows/ci.yml`):

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  verify:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        task: [lint, test, build]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm            # caches ~/.npm keyed on package-lock.json
      - run: npm ci
      - run: npx ng ${{ matrix.task }}

  e2e:
    needs: verify
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx ng build && npx playwright test

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [verify, e2e]
    runs-on: ubuntu-latest
    environment: production     # environment protection rules / required reviewers
    permissions:
      contents: read
      id-token: write           # OIDC to the cloud provider, no long-lived keys
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy.sh
```

(In reality you'd build once and pass `dist/` between jobs with `actions/upload-artifact` / `download-artifact` rather than rebuilding. A matrix is also the place for multiple Node versions or browsers.)

**Bitbucket Pipelines** (`bitbucket-pipelines.yml`):

```yaml
image: node:22

definitions:
  caches:
    npm: ~/.npm
  steps:
    - step: &verify
        name: Lint, test, build
        caches: [npm]
        script:
          - npm ci
          - npx ng lint
          - npx ng test
          - npx ng build --configuration production
        artifacts:
          - dist/**

pipelines:
  pull-requests:
    '**':
      - step: *verify
  branches:
    main:
      - step: *verify
      - step:
          name: Deploy to staging
          deployment: staging
          script:
            - ./scripts/deploy.sh staging
      - step:
          name: Deploy to production
          deployment: production
          trigger: manual
          script:
            - ./scripts/deploy.sh production
```

---

### Q15. Protected branches, signed commits and secrets — what's your baseline?

**Answer:**
- **Protected branches** on `main`/`release/*`: no direct pushes, no force pushes, required status checks, required approvals (including CODEOWNERS), branch up-to-date or merge queue/merge trains (GitLab merge trains, GitHub merge queue) so main never breaks from semantically conflicting PRs.
- **Signed commits** (GPG, SSH or S/MIME signing; `git config commit.gpgsign true`) prove authorship; the platform shows "Verified" and can require it. Relevant in regulated/enterprise settings and for release tags.
- **Secrets**: never in the repo (including `environment.ts` — anything in the Angular bundle is public anyway). Use CI secret variables (masked + protected in GitLab, environment secrets in GitHub, secured variables in Bitbucket), scoped per environment; prefer OIDC federation to cloud providers over static keys. Enable secret scanning / push protection. If a secret leaks: **rotate it first** — rewriting history doesn't un-leak it.
- Least-privilege CI tokens (`permissions:` in GitHub Actions), pin third-party actions to a SHA, protect deploy environments with approvals.

---

## B. Tricky / trap questions

### T1. "I always rebase main onto my feature branch to keep it up to date." Anything wrong?

**The trap:** mixing up the direction. `git switch main && git rebase feature` rewrites **main** — the shared branch — on top of your feature.

**Strong answer includes:**
- The correct statement is "I rebase **my feature branch onto main**": `git switch feature && git rebase origin/main`.
- Mnemonic: `git rebase X` replays *the current branch* on top of X; the current branch is the one that gets rewritten.
- Integration into main happens through the PR/MR (squash/merge/rebase-merge), never by rewriting main locally.

---

### T2. "My rebase is done but push is rejected. I'll `git push --force` to the shared feature branch."

**The trap:** force pushing to a branch others use.

**Strong answer includes:**
- `--force` overwrites the remote, silently deleting commits colleagues pushed meanwhile.
- If the branch is shared: don't rebase it — merge main into it, or coordinate.
- If it's mine: `git push --force-with-lease` (optionally `--force-if-includes`) so the push fails if the remote moved.
- Protected branches should forbid force pushes entirely. If it happened: the colleague's reflog or the platform's activity/PR history has the lost SHAs; restore via a branch from that SHA.

---

### T3. "I did `git reset --hard` and my work is gone. Can anything be done?"

**The trap:** "no, it's gone" — or "yes, always".

**Strong answer includes:**
- Committed work: yes, `git reflog` → `git branch rescue HEAD@{n}`.
- Staged but uncommitted: maybe, `git fsck --lost-found` finds dangling blobs (no filenames).
- Never staged: no (maybe IDE local history).
- Prevention: commit early, `git stash` before risky ops, use `git reset --keep` or `git switch` which refuse to discard local changes.

---

### T4. "We squash every PR, so bisect is always easy." True?

**The trap:** assuming squash = bisect-friendly.

**Strong answer includes:**
- Squash makes every commit on main a buildable PR-sized unit — good, *if* PRs are small.
- A squashed 50-file PR means bisect lands on "somewhere in here"; you lose the finer steps that existed in the branch.
- Merge commits keep granularity but branch commits may not build individually (WIP), causing `bisect skip` noise; `git bisect --first-parent` helps by walking only merges.
- The real enabler: small PRs and every commit on main green.

---

### T5. "Our feature branch has lived for 6 weeks; merging it is painful. How do we avoid this?"

**The trap:** "merge main into it more often" as the only answer.

**Strong answer includes:**
- Long-lived branches = integration risk, huge reviews, merge hell, late feedback.
- Break work into vertical slices merged to main behind **feature flags**; branch by abstraction for refactors (introduce interface, migrate callers incrementally, remove old path).
- Dark-launch components in the library (exported but unused / marked experimental) so they can merge early.
- Sync with main daily meanwhile; use `rerere` to reduce repeat conflicts.

---

### T6. "We cherry-picked the fix to release and later merged release back to main — now there are duplicate commits/conflicts."

**The trap:** thinking Git recognises cherry-picks as the same commit.

**Strong answer includes:**
- Cherry-picks create new SHAs; Git merges by content, so identical changes usually apply cleanly, but if the code diverged afterwards you get conflicts and duplicated log entries.
- Use `-x` for traceability; `git cherry -v main release/4.2` or `git log --cherry-pick --right-only` identify equivalent patches.
- Choose one flow direction (merge-forward from oldest release, or fix-on-main-then-cherry-pick-back) and don't merge release branches back if you cherry-pick into them.

---

### T7. "Reverting the merge was easy, but re-merging the fixed branch brought nothing back."

**The trap:** not knowing Git remembers the original merge.

**Strong answer includes:**
- The branch commits are already ancestors of main; the revert commit undid their effect. Merging again adds only new commits.
- Fix: `git revert <revert-sha>` (revert the revert) and then merge the follow-up fixes — or with squash merges, open a fresh PR with the full change.

---

## C. Code examples

### Everyday safety config

```bash
git config --global pull.rebase true          # rebase local commits on pull
git config --global rebase.autoStash true
git config --global rebase.autoSquash true
git config --global rerere.enabled true
git config --global merge.conflictStyle zdiff3
git config --global push.autoSetupRemote true
git config --global alias.pf "push --force-with-lease"
git config --global alias.lg "log --oneline --graph --decorate --all"
```

### Commit message linting for a library

```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'scope-enum': [2, 'always', ['button', 'dialog', 'table', 'tokens', 'forms', 'ci', 'deps']],
  },
};
```

```bash
# .husky/commit-msg
npx --no -- commitlint --edit "$1"
```

### Changeset example

```markdown
---
"@acme/ui": minor
---

`acme-button`: add `loading` input. Sets `aria-busy` and disables the button while true.
```

### Hotfix backport flow

```bash
git switch main && git pull
# fix merged to main as 3f9e2ab via PR
git switch -c hotfix/table-sort-4.2 origin/release/4.2
git cherry-pick -x 3f9e2ab
npm ci && npx ng test && npx ng build
git push -u origin hotfix/table-sort-4.2     # open MR into release/4.2, release 4.2.7
```

---

## D. Red flags

- "I just use the Git GUI, I don't really know what rebase does." → "I rebase my own branches for linear history and merge via PRs; I know when each rewrites history."
- "I force push whenever push is rejected." → "`--force-with-lease`, only on my own branches; never on shared or protected branches."
- "If something goes wrong I delete the folder and clone again." → "I use reflog, `rebase --abort`, `ORIG_HEAD`."
- "We undo bad commits on main with reset and force push." → "On shared branches I `revert`."
- "We use GitFlow because it's the standard." → "The strategy follows the release model; for continuous delivery I prefer trunk-based with feature flags."
- "Big PRs are more efficient." → "Small PRs get better reviews, merge faster and bisect cleanly."
- "Code review is for catching style issues." → "Tooling catches style; review focuses on correctness, design, risk, tests and knowledge sharing."
- "We put the API key in environment.prod.ts." → "Anything in the bundle is public; secrets live server-side or in CI secret stores."
- "CI runs `npm install`." → "`npm ci` for reproducible, lockfile-exact installs."
- "We bump the library version manually when we remember." → "Conventional commits or changesets drive SemVer and changelogs automatically."

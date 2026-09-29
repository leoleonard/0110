# 06 — REST, HTTP, Auth, Postman & Swagger/OpenAPI

> Use this file to rehearse the "frontend meets backend" part of the interview. At senior level nobody wants the REST definition recited. They are checking whether you can **design and review an API contract with a backend team**, **explain HTTP semantics well enough to debug production issues** (caching, CORS, 401 loops, duplicate POSTs), **make secure auth decisions** (where tokens live, why) and **run the tooling** (Postman, OpenAPI, generated clients, mocks) that lets frontend, backend, QA and third parties work in parallel. Every answer should end with "…and on the frontend that means X".

---

## A. Most commonly asked questions

### Q1. What makes an API "RESTful"? Is your API actually REST?

**Answer (1–2 min):**
REST is an architectural style (Fielding, 2000) with a set of constraints, not a protocol:
- **Resources identified by URIs** — nouns, not verbs: `/orders/42`, not `/getOrder?id=42`.
- **Uniform interface** — standard HTTP methods with their standard semantics, self-descriptive messages (media types, status codes, headers), manipulation of resources through representations (usually JSON).
- **Stateless** — every request carries everything the server needs (auth token/cookie, params). No server-side conversation state between requests. This is what makes horizontal scaling and caching straightforward.
- **Cacheable** — responses declare whether and how they can be cached.
- **Client–server** and **layered system** — proxies, CDNs and gateways can sit in between transparently.
- **HATEOAS** — responses contain links to the next possible actions.

"Honestly, most 'REST' APIs are *HTTP + JSON with resource-oriented URLs*. Almost nobody does full HATEOAS — clients hard-code URL templates from an OpenAPI spec instead. That's fine; what I care about is consistent resource naming, correct method semantics, correct status codes and a stable error contract."

**Go deeper:**
- Richardson Maturity Model: level 0 (one endpoint, RPC-over-HTTP), 1 (resources), 2 (verbs + status codes — where most good APIs sit), 3 (hypermedia).
- Where HATEOAS genuinely helps: pagination links (`next`, `prev`), and server-driven permissions ("the `approve` link is present only if you may approve") — that one is actually useful for a UI.
- Not everything fits CRUD: actions like "cancel order" are commonly modelled as `POST /orders/42/cancellation` or `POST /orders/42:cancel`. Be pragmatic, be consistent.

---

### Q2. Walk me through the HTTP methods: safety and idempotency. PUT vs PATCH vs POST?

**Answer (1–2 min):**

| Method | Safe | Idempotent | Typical use |
|---|---|---|---|
| GET / HEAD / OPTIONS | yes | yes | read, metadata, preflight |
| PUT | no | yes | replace the full resource at a known URI (or create at client-chosen URI) |
| DELETE | no | yes | remove (second DELETE → 404 or 204, but server state is the same) |
| POST | no | **no** | create in a collection, trigger actions |
| PATCH | no | **not guaranteed** | partial update |

- **Safe** = no intended side effects on the server (so prefetching/crawling GETs must be harmless — never `GET /delete?id=`).
- **Idempotent** = N identical requests have the same effect on server state as one. The *response* may differ; the *state* doesn't.
- **PUT** sends the full representation; missing fields mean "clear them". **PATCH** sends a diff. JSON Merge Patch (RFC 7396, `application/merge-patch+json`) is idempotent in practice; JSON Patch (RFC 6902) with ops like `add` to an array or "increment" is not.
- Why it matters on the frontend: **retries**. Retrying a GET/PUT/DELETE after a network timeout is safe. Retrying a POST can create two orders or charge a card twice.

---

### Q3. How do you make a POST safe to retry?

**Answer:**
- **Idempotency key**: the client generates a UUID per *user intent* (not per HTTP attempt) and sends it as `Idempotency-Key: <uuid>`. The server stores key → result for some window; a repeated key returns the stored result instead of executing again. Stripe popularised it; there is an IETF draft standardising the header.
- Generate the key when the user clicks "Pay", keep it across retries, discard it on success or when the form changes.
- Alternatives: client-generated IDs with `PUT /orders/{uuid}` (makes creation idempotent), or a server-side dedupe on a natural key.
- UI side: disable the submit button while pending, use `exhaustMap` for submit streams so double-clicks don't fire twice.

```typescript
// retry only what is safe to retry
const isIdempotent = (req: HttpRequest<unknown>) =>
  ['GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE'].includes(req.method) ||
  req.headers.has('Idempotency-Key');

export const retryInterceptor: HttpInterceptorFn = (req, next) =>
  isIdempotent(req)
    ? next(req).pipe(
        retry({
          count: 2,
          delay: (err, attempt) =>
            err instanceof HttpErrorResponse && [0, 502, 503, 504].includes(err.status)
              ? timer(2 ** attempt * 300)
              : throwError(() => err),
        }),
      )
    : next(req);
```

---

### Q4. Which status codes should a frontend handle, and how?

**Answer (1–2 min):** The frontend should branch on **status class first, then specific codes**, with one central place (interceptor + error mapper) and feature-level handling only where it adds UX value.

| Code | Meaning | What the frontend does |
|---|---|---|
| 200 OK | success with body | render |
| 201 Created | resource created, `Location` header | navigate to / insert the new resource; use the returned body/ID |
| 204 No Content | success, no body | don't try to parse JSON; update local state optimistically |
| 301 / 302 | redirect | browser follows automatically for XHR/fetch — you rarely see them; an unexpected 302 to a login page returning HTML is a classic "Unexpected token <" bug |
| 304 Not Modified | conditional GET hit | handled by the browser HTTP cache; JS sees the cached 200 |
| 400 Bad Request | malformed/invalid input | show validation summary; log (it's often a client bug) |
| 401 Unauthorized | **not authenticated** (missing/expired token) | try silent refresh once; if that fails → login, preserve return URL |
| 403 Forbidden | **authenticated, not allowed** | do NOT redirect to login; show "no access", hide the action |
| 404 Not Found | missing resource | not-found page or inline empty state |
| 409 Conflict | state conflict (duplicate, version clash) | show conflict, offer reload/merge |
| 412 Precondition Failed | `If-Match` ETag mismatch (optimistic locking) | "someone else changed this record" — reload and re-apply |
| 422 Unprocessable Content | syntactically fine, semantically invalid | map field errors onto form controls |
| 429 Too Many Requests | rate-limited | back off, honour `Retry-After`, throttle UI |
| 500 | server bug | generic error + correlation ID for support; don't retry blindly |
| 502 / 503 / 504 | gateway/unavailable/timeout | retry with backoff for idempotent requests; maintenance banner for 503 |

"Status 0 in `HttpErrorResponse` means the request never got a response — offline, DNS, CORS failure or aborted. It deserves its own message."

---

### Q5. Explain CORS and preflight. How do you handle it in Angular dev?

**Answer (1–2 min):**
- The **Same-Origin Policy** stops JS on `https://app.example.com` from *reading* responses from another origin (scheme + host + port). CORS is the server's way to **opt in** to cross-origin reads.
- **Simple requests** (GET/HEAD/POST, only CORS-safelisted headers, `Content-Type` of `text/plain`, `multipart/form-data` or `application/x-www-form-urlencoded`) are sent directly; the browser checks `Access-Control-Allow-Origin` on the response.
- Anything else — `PUT`/`PATCH`/`DELETE`, `Content-Type: application/json`, an `Authorization` header — triggers a **preflight** `OPTIONS` with `Access-Control-Request-Method` / `-Headers`. The server answers with `Access-Control-Allow-Methods`, `-Allow-Headers`, `-Max-Age` (to cache the preflight).
- **Credentials** (cookies): client sets `withCredentials: true`; server must send `Access-Control-Allow-Credentials: true` **and** a specific origin — `*` is not allowed with credentials. Cookies also need `SameSite=None; Secure` if truly cross-site.
- `Access-Control-Expose-Headers` is needed if JS must read e.g. `Location`, `ETag`, `X-Total-Count`.
- **CORS is enforced by the browser only.** Postman and curl don't care, which is why "it works in Postman" proves nothing.

**Dev proxy in Angular** — avoid CORS in dev entirely by making the API same-origin:

```json
// proxy.conf.json
{
  "/api": {
    "target": "http://localhost:8080",
    "secure": false,
    "changeOrigin": true,
    "logLevel": "debug"
  }
}
```

```json
// angular.json → projects.app.architect.serve.options
"proxyConfig": "proxy.conf.json"
```

In production, the equivalent is serving SPA and API behind the same origin (reverse proxy / ingress / BFF), which also removes preflight latency.

---

### Q6. What is a JWT and what does it (not) give you?

**Answer:**
- Three base64url parts: `header.payload.signature`. Header: `alg`, `kid`. Payload: claims (`sub`, `exp`, `iat`, `iss`, `aud`, custom roles). Signature: HMAC or RSA/ECDSA over the first two parts.
- **Signed, not encrypted** — anyone can read the payload. Never put secrets or PII there.
- Benefit: the resource server can validate it **statelessly** (check signature with the issuer's public key, `exp`, `aud`, `iss`) without a session lookup.
- Downside: **hard to revoke** before `exp`. Mitigation: short-lived access tokens (5–15 min) + refresh tokens, or a denylist.
- The frontend may *decode* the payload for UI hints (display name, roles to hide buttons) but must never *trust* it for security — the API enforces authorisation.

---

### Q7. Where do you store tokens in the browser?

**Answer (1–2 min):** "It's an XSS vs CSRF trade-off, and my default for new enterprise apps is: don't let JS hold long-lived tokens at all."

| Storage | XSS | CSRF | Notes |
|---|---|---|---|
| `localStorage` / `sessionStorage` | **any injected script can exfiltrate the token** and use it from anywhere | not an issue (not sent automatically) | simple, survives reload; weakest against XSS |
| In-memory (a service field / signal) | script can still call the API while the page is open, but can't trivially steal a long-lived token | not an issue | lost on reload → need silent refresh via cookie or iframe/refresh token |
| `httpOnly; Secure; SameSite` cookie | JS can't read it | **cookie is sent automatically → need CSRF protection** (SameSite=Lax/Strict, XSRF token) | best with same-origin API or a BFF |

- Best practice today: **BFF pattern** (Q10) — tokens stay server-side, browser gets an httpOnly session cookie.
- If the SPA must hold tokens: access token in memory, refresh token rotated (and ideally in an httpOnly cookie scoped to the refresh endpoint).
- **Angular XSRF support**: `HttpClient` reads a cookie (default `XSRF-TOKEN`) and sends it back as a header (default `X-XSRF-TOKEN`) on mutating, same-origin, relative-URL requests. Configure with `provideHttpClient(withXsrfConfiguration({ cookieName, headerName }))`; the server must set the cookie and validate the header. It is *not* added to absolute cross-origin URLs by design.
- Whatever you pick, XSS is game over for the session anyway — so CSP, Angular's built-in sanitisation, and no `bypassSecurityTrust*` on user data matter more than storage choice.

---

### Q8. Explain OAuth2 / OIDC Authorization Code + PKCE. Why is Implicit dead?

**Answer (1–2 min):**
- **OAuth2** = delegated authorisation (access tokens for APIs). **OIDC** = identity layer on top (ID token, `userinfo`, standard claims).
- **Authorization Code + PKCE** flow for SPAs:
  1. App generates `code_verifier` (random) and `code_challenge = BASE64URL(SHA256(verifier))`, plus `state` (and `nonce` for OIDC).
  2. Redirect to `/authorize?response_type=code&client_id&redirect_uri&scope=openid profile api&code_challenge&code_challenge_method=S256&state`.
  3. User logs in at the IdP; IdP redirects back with `?code=…&state=…`.
  4. App verifies `state`, POSTs `code` + `code_verifier` to `/token`, receives access token (+ ID token, + refresh token).
- PKCE proves the party redeeming the code is the one that started the flow, so an intercepted code is useless. SPAs are **public clients** (no secret) — PKCE replaces the secret.
- **Implicit flow** (tokens directly in the URL fragment) is deprecated by the OAuth 2.0 Security BCP and removed in OAuth 2.1: tokens leak via history, referrers, logs; no refresh tokens; no sender binding.
- In Angular I use a certified library (e.g. `angular-auth-oidc-client`, `angular-oauth2-oidc`, or the IdP's SDK) — never hand-roll crypto and redirects.

---

### Q9. How do refresh tokens work, and how do you handle concurrent 401s?

**Answer:**
- Access token short-lived; refresh token longer-lived, used only against the token endpoint.
- **Refresh token rotation**: every refresh returns a *new* refresh token and invalidates the old one. If an old token is reused, the IdP detects theft and revokes the whole family. Consequence for the frontend: **two parallel refreshes with the same token will log the user out** — so you must ensure a single in-flight refresh.
- **Concurrent 401 queueing**: when five requests fail with 401 at once, the first triggers the refresh, the others wait on the same observable, then all retry with the new token. If refresh fails → logout once.

```typescript
// auth.service.ts
@Service()
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  readonly accessToken = signal<string | null>(null);
  private refresh$: Observable<string> | null = null;

  /** Single-flight refresh: concurrent callers share one request. */
  refreshToken(): Observable<string> {
    this.refresh$ ??= this.http
      .post<{ accessToken: string }>('/auth/refresh', {}, { withCredentials: true })
      .pipe(
        map(r => r.accessToken),
        tap(t => this.accessToken.set(t)),
        finalize(() => (this.refresh$ = null)),
        shareReplay({ bufferSize: 1, refCount: false }),
      );
    return this.refresh$;
  }

  logout(returnUrl = this.router.url) {
    this.accessToken.set(null);
    this.router.navigate(['/login'], { queryParams: { returnUrl } });
  }
}
```

```typescript
// auth.interceptor.ts
const SKIP_AUTH = new HttpContextToken<boolean>(() => false);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  if (req.context.get(SKIP_AUTH) || req.url.startsWith('/auth/')) return next(req);

  const withToken = (token: string | null) =>
    token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(withToken(auth.accessToken())).pipe(
    catchError((err: unknown) => {
      if (!(err instanceof HttpErrorResponse) || err.status !== 401) {
        return throwError(() => err);
      }
      return auth.refreshToken().pipe(
        switchMap(token => next(withToken(token))), // retry once
        catchError(refreshErr => {
          auth.logout();
          return throwError(() => refreshErr);
        }),
      );
    }),
  );
};

// app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [provideHttpClient(withInterceptors([authInterceptor]))],
};
```

**Go deeper:**
- Don't refresh on 403 — that's an authorisation problem, a new token won't help.
- Exclude the refresh endpoint itself from the interceptor, or you get an infinite loop.
- Proactive refresh (a timer before `exp`) reduces 401s but you still need the reactive path (clock skew, sleeping laptops).
- `@Service()` is new in v22; on older codebases this is `@Injectable({ providedIn: 'root' })`.

---

### Q10. What is the BFF pattern and when would you choose it?

**Answer:**
- **Backend-for-Frontend**: a thin server (Node, .NET, Spring…) on the same origin as the SPA. It performs the OAuth code flow as a **confidential client**, keeps access/refresh tokens server-side, and gives the browser an `httpOnly; Secure; SameSite=Strict` session cookie. API calls go SPA → BFF → downstream APIs with the token attached.
- Wins: no tokens in JS (XSS can't exfiltrate them), no CORS (same origin), a place to aggregate/shape data for the UI, hide internal service topology, add caching.
- Costs: another deployable, session state (or encrypted cookie), CSRF protection needed (SameSite + XSRF header — Angular's XSRF support fits nicely).
- It's the approach recommended by the IETF "OAuth 2.0 for Browser-Based Apps" guidance for high-security apps. "For an enterprise app with PII or payments, I'd push for a BFF."

---

### Q11. Explain HTTP caching headers. How do you cache an Angular app correctly?

**Answer (1–2 min):**
- `Cache-Control` directives: `max-age=N` (fresh for N s), `no-cache` (may store, **must revalidate** before use), `no-store` (never store — sensitive data), `private` (browser only, not CDN), `public`, `s-maxage` (shared caches), `immutable` (never revalidate while fresh), `stale-while-revalidate`.
- **Validators**: `ETag` + `If-None-Match`, or `Last-Modified` + `If-Modified-Since`. If unchanged the server returns **304 Not Modified** with no body — cheap revalidation.
- **The Angular deployment rule:**
  - Hashed bundles (`main-ABC123.js`, `styles-XYZ.css`, the default output hashing in production builds) → `Cache-Control: public, max-age=31536000, immutable`. The filename changes when content changes.
  - `index.html` → `Cache-Control: no-cache` (or short `max-age` + revalidation). It's the only file that points to the current hashes; if it's cached for a day, users run yesterday's app — or worse, request chunk files you already deleted → lazy-route `ChunkLoadError`.
  - Keep the previous release's chunks available for a while (or handle chunk load errors with a reload prompt) for users with the old tab open.
- API responses: usually `private, no-cache` with ETags for GETs that are expensive, or `no-store` for sensitive data.
- ETags also enable **optimistic concurrency**: `PUT` with `If-Match: "v7"` → `412` if someone else changed it.

---

### Q12. Offset vs cursor pagination — which and why?

**Answer:**
- **Offset/limit** (`?page=3&size=20` or `?offset=40&limit=20`): easy, supports "jump to page 17" and total counts. Problems: `OFFSET` gets slow on big tables; inserts/deletes during browsing cause duplicates or skipped rows.
- **Cursor/keyset** (`?after=eyJpZCI6MTIzfQ&limit=20`, server returns `nextCursor`): stable under concurrent writes, fast (index seek), perfect for feeds and **infinite scroll**. Can't jump to arbitrary pages; total count is often absent or approximate.
- Decision: admin tables with page numbers and sort → offset (with sane max page size). Feeds, logs, event streams, infinite scroll, large datasets → cursor.
- Frontend for infinite scroll: `IntersectionObserver` sentinel (or `@defer (on viewport)` for a "load more" block), request guarded so only one page loads at a time (`exhaustMap`), virtual scrolling (`cdk-virtual-scroll-viewport`) when the list grows to thousands of rows, keep scroll position on back-navigation, and provide a "load more" button fallback for accessibility.
- Contract: return `{ items, nextCursor }` or use `Link` headers (`rel="next"`). Make sure sorting is deterministic (tie-break on ID).

---

### Q13. What should an API error contract look like?

**Answer:**
Use **RFC 9457 Problem Details** (obsoletes RFC 7807), media type `application/problem+json`:

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Your request is not valid.",
  "status": 422,
  "detail": "2 fields failed validation.",
  "instance": "/orders/42",
  "traceId": "00-4bf92f3577b34da6-...",
  "errors": [
    { "pointer": "#/email", "detail": "must be a valid email" },
    { "pointer": "#/quantity", "detail": "must be >= 1" }
  ]
}
```

- `type` is a stable machine-readable identifier — the frontend switches on it, never on `detail` text.
- Extension members (`errors`, `traceId`) are allowed; agree them in the OpenAPI spec.
- Frontend: one `toAppError(HttpErrorResponse)` mapper → typed `AppError`; forms map `errors[].pointer` to controls; show `traceId` in the error toast so support can find logs.
- Translate by `type` (i18n keys), not by showing backend English strings to users.

---

### Q14. How do you version an API, and how does the frontend cope?

**Answer:**
- Options: URI (`/v2/orders` — most common, visible, cache-friendly), header / media type (`Accept: application/vnd.acme.v2+json` — purer, harder to test in a browser), query param (meh).
- Better than frequent versioning: **evolve compatibly** — add optional fields, never rename/remove without deprecation; clients ignore unknown fields (tolerant reader). Signal deprecation with `Deprecation`/`Sunset` headers and changelogs.
- Frontend reality: the SPA and API deploy independently, and old SPA tabs live for hours. So the API must support N and N-1 clients during rollout; breaking changes go behind a new version or an expand–contract migration.
- Guardrail: OpenAPI diff in CI (Q17) to catch breaking changes before merge.

---

### Q15. How do you use Postman in a team, beyond sending requests?

**Answer (1–2 min):**
- **Collections** organised by resource/feature, with example requests and saved responses — living documentation.
- **Environments** (`local`, `dev`, `staging`) holding `baseUrl`, client IDs; **variables** scoped global → collection → environment → local. Secrets in the *current value* only (not synced) or in a vault, never committed.
- **Pre-request scripts**: fetch/refresh a token, generate timestamps, idempotency keys, HMAC signatures.
- **Tests** (`pm.test`, `pm.expect`, `pm.response.to.have.status(201)`), chaining: save `id` from a create response into a variable for the next request. JSON schema checks on responses.
- **Newman** (Postman's CLI runner) in CI: `newman run collection.json -e staging.json --reporters cli,junit` — a cheap API smoke/regression suite after deploy.
- **Mock servers** from saved examples so frontend can build before the backend exists.
- **Sharing**: workspaces with QA and third parties; export collections for partners integrating with our API; a collection is often the fastest way to reproduce a bug report ("here's the exact request that 500s").

```javascript
// Postman pre-request script: obtain token once per run
if (!pm.environment.get('accessToken')) {
  pm.sendRequest({
    url: pm.environment.get('authUrl') + '/token',
    method: 'POST',
    header: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: { mode: 'urlencoded', urlencoded: [
      { key: 'grant_type', value: 'client_credentials' },
      { key: 'client_id', value: pm.environment.get('clientId') },
      { key: 'client_secret', value: pm.environment.get('clientSecret') },
    ]},
  }, (err, res) => pm.environment.set('accessToken', res.json().access_token));
}

// Tests tab
pm.test('201 and Location header', () => {
  pm.response.to.have.status(201);
  pm.expect(pm.response.headers.get('Location')).to.match(/\/orders\/\d+$/);
  pm.collectionVariables.set('orderId', pm.response.json().id);
});
```

---

### Q16. Swagger vs OpenAPI, contract-first vs code-first?

**Answer:**
- **OpenAPI** is the specification (3.0 / 3.1, YAML/JSON). **Swagger** is the SmartBear tooling brand (Swagger UI, Swagger Editor, Codegen); "Swagger 2.0" was the spec's old name.
- **Code-first**: annotations in backend code generate the spec. Fast for backend, but the contract is a by-product and frontend finds out about changes late.
- **Contract-first**: teams agree the spec in a PR (frontend, backend, sometimes QA/partners review), then both sides build in parallel — backend implements, frontend generates a client + mocks. "Contract-first is how I unblock a frontend team from backend timelines, and it makes third-party integrations far less painful."
- **Swagger UI** renders the spec as interactive docs ("Try it out"); great for QA and external consumers.
- What I review in a spec as a frontend lead: consistent naming and casing, pagination shape, Problem Details errors, nullable vs optional fields, enums (and how new values are added), date formats (ISO 8601 with offset), IDs as strings, `operationId`s (they become method names in generated clients).

---

### Q17. Do you generate TypeScript clients from OpenAPI? Trade-offs?

**Answer (1–2 min):**
- Tools: **openapi-generator** (`typescript-angular` generator — Angular services using `HttpClient`), **ng-openapi-gen** (Angular-focused, generates services and models), **orval** (models + clients, can also produce MSW mocks), or just types-only (`openapi-typescript`) with a thin hand-written layer.
- Benefits: types always match the contract, no hand-written DTO drift, compile errors when the API changes.
- Trade-offs:
  - **Committed generated code** — reviewable diffs show exactly what changed in the API, works offline, but noisy PRs and people hand-edit it (forbid via lint/CODEOWNERS).
  - **Generate in the build step** — always fresh, no noise; but builds depend on spec availability and changes are less visible. I like: spec file versioned in repo (or pinned version), generation in a `prebuild` script, output git-ignored.
  - Generated services can be heavy or opinionated. I often keep them behind a feature-level facade/data-access layer so components never import generated code directly and a generator swap is cheap.
- **Breaking-change detection**: run an OpenAPI diff tool (e.g. `oasdiff`, openapi-diff) in the backend's CI against the last released spec; fail the MR on removed fields/endpoints or changed types.

```bash
npx @openapitools/openapi-generator-cli generate \
  -i ./contracts/orders-api.yaml \
  -g typescript-angular \
  -o ./libs/data-access/orders/src/generated \
  --additional-properties=providedInRoot=true,stringEnums=true
```

---

### Q18. How do you mock APIs and do contract testing?

**Answer:**
- **MSW (Mock Service Worker)**: intercepts `fetch`/XHR at the network layer (service worker in the browser, interceptors in Node). Same handlers for local dev, Storybook, unit/component tests (Vitest) and demos. The app code stays unchanged — no mock services injected. Handy now that `HttpClient` uses `FetchBackend` by default in v22.
- Alternatives: Angular `HttpTestingController` for unit tests of services/interceptors; Postman mock servers; Prism serving a mock from the OpenAPI spec.
- **Contract testing (Pact)**: consumer-driven. Frontend tests record expectations ("GET /orders/42 returns this shape") into a pact file; the provider's CI verifies it against the real implementation; a Pact Broker tracks compatibility (`can-i-deploy`). Catches "backend renamed a field" before production, without slow end-to-end environments.
- "Mocks tell me my UI works against what I *think* the API does; contract tests tell me the API still does it."

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse, delay } from 'msw';

export const handlers = [
  http.get('/api/orders/:id', async ({ params }) => {
    await delay(300);
    return HttpResponse.json({ id: params['id'], status: 'OPEN', total: 129.5 });
  }),
  http.post('/api/orders', () =>
    HttpResponse.json(
      { type: 'https://api.example.com/problems/validation-error', title: 'Invalid', status: 422,
        errors: [{ pointer: '#/email', detail: 'must be a valid email' }] },
      { status: 422, headers: { 'Content-Type': 'application/problem+json' } },
    ),
  ),
];
```

---

## B. Tricky / trap questions

### T1. "A user's token expired and they tried to open the admin page. 401 or 403?"

**The trap:** treating them as interchangeable, or redirecting to login on 403.

**Strong answer includes:**
- **401** = "I don't know who you are" (missing, invalid, expired credentials); it should come with `WWW-Authenticate`. Expired token → 401 → silent refresh → retry → if still failing, login.
- **403** = "I know who you are and the answer is no." Re-authenticating won't help. Show a no-access state, don't loop to the login page, don't refresh tokens.
- Some APIs return **404 instead of 403** deliberately to avoid revealing a resource exists — the UI must handle that.
- Frontend guards hiding routes are UX, not security; the API still enforces.

---

### T2. "The save request timed out. Can we just add `retry(3)` to all HTTP calls?"

**The trap:** blanket retries, including POST.

**Strong answer includes:**
- A timeout doesn't tell you whether the server processed the request. Retrying a non-idempotent POST can duplicate orders/payments.
- Retry only idempotent methods (GET, PUT, DELETE) or POSTs carrying an `Idempotency-Key`, only on transient errors (status 0, 502/503/504, 429 honouring `Retry-After`), with exponential backoff + jitter and a cap.
- Never retry 4xx (except 408/429) — it'll fail the same way.
- PATCH: idempotent only if it's a merge-patch "set these fields"; "append to list" or "increment" semantics are not.

---

### T3. "We get CORS errors — can you fix it on the frontend?"

**The trap:** adding `Access-Control-Allow-Origin` to the *request*, using `mode: 'no-cors'`, or installing a browser extension.

**Strong answer includes:**
- CORS headers are **response** headers set by the server; the browser enforces them. The frontend can't grant itself permission — that's the whole point.
- `no-cors` gives you an opaque response you can't read.
- Real fixes: configure the server/gateway with an allowlist of origins (not `*` with credentials), or remove the cross-origin hop — same-origin via reverse proxy/BFF in prod, `proxy.conf.json` in dev.
- Debugging: check the preflight in DevTools Network — often the OPTIONS request is blocked by auth middleware (returns 401) or the `Authorization` header isn't in `Access-Control-Allow-Headers`.
- An error response (500) without CORS headers shows up as a CORS error in the console — the real problem may be server-side.

---

### T4. "Storing the JWT in localStorage is fine — Angular sanitises templates, so we have no XSS."

**The trap:** assuming framework sanitisation = no XSS.

**Strong answer includes:**
- XSS can come from third-party scripts (analytics, tag managers, chat widgets), compromised npm dependencies, `bypassSecurityTrustHtml`, `innerHTML` in non-Angular code, or a CDN compromise. Any of them reads `localStorage` in one line.
- A stolen long-lived token works from the attacker's machine until it expires; an httpOnly cookie/BFF limits the attacker to acting while the victim's page is open.
- "localStorage is acceptable for low-risk internal apps with short-lived tokens and a strict CSP; for customer-facing enterprise apps I'd use in-memory tokens with rotation, or preferably a BFF."
- Also mention CSP, Trusted Types, dependency auditing, Subresource Integrity for third-party scripts.

---

### T5. "Our API returns 200 with `{ success: false, error: '...' }`. Any problem?"

**The trap:** "it's fine, we check the flag."

**Strong answer includes:**
- Breaks HTTP semantics: caches and CDNs may cache the error, monitoring/APM counts it as success, retries/interceptors/`catchError` don't fire, `httpResource`/`resource` report a value instead of an error state.
- Every consumer (frontend, mobile, partners) must reimplement the check.
- Fix: proper status codes + Problem Details. If you can't change the backend (third party), normalise it in **one** interceptor that converts envelope errors into `HttpErrorResponse` so the rest of the app behaves normally.

---

### T6. "We deployed but half the users still see the old version, and some get blank pages."

**The trap:** "tell users to clear their cache."

**Strong answer includes:**
- Diagnosis: `index.html` is being cached (by the browser, CDN or a service worker), so it references old hashed bundles; if old chunks were deleted, lazy routes throw `ChunkLoadError` → blank page.
- Fix: `index.html` served with `Cache-Control: no-cache` (and CDN invalidation on deploy); hashed assets `max-age=31536000, immutable`; retain previous release assets for a grace period.
- If using the Angular service worker, use `SwUpdate` to detect new versions and prompt reload; handle unrecoverable state.
- Add a global handler for chunk load failures that offers a reload.

---

### T7. "Is PATCH idempotent?"

**The trap:** a flat yes or no.

**Strong answer includes:**
- The HTTP spec does not guarantee it. It depends on the patch document.
- `{"status":"CLOSED"}` as merge patch → idempotent in effect. JSON Patch `{"op":"add","path":"/tags/-","value":"x"}` → appends every time → not idempotent.
- To make PATCH safely retryable: design patch semantics as "set", use `If-Match` with the ETag (a retry after success gets 412 instead of double-applying), or add an idempotency key.

---

### T8. "Why doesn't my interceptor see the `X-Total-Count` header / the `Location` header?"

**The trap:** blaming Angular.

**Strong answer includes:**
- For cross-origin responses, JS can only read CORS-safelisted response headers unless the server lists others in `Access-Control-Expose-Headers`.
- Also ensure you requested `{ observe: 'response' }` to get headers from `HttpClient` at all.

---

## C. Code examples

### Central error mapping to Problem Details

```typescript
export interface AppError {
  kind: 'offline' | 'auth' | 'forbidden' | 'notFound' | 'validation' | 'conflict' | 'rateLimited' | 'server';
  status: number;
  type?: string;
  fieldErrors?: Record<string, string>;
  traceId?: string;
}

export function toAppError(err: HttpErrorResponse): AppError {
  const p = err.error && typeof err.error === 'object' ? err.error : {};
  const base = { status: err.status, type: p.type, traceId: p.traceId };
  switch (true) {
    case err.status === 0: return { ...base, kind: 'offline' };
    case err.status === 401: return { ...base, kind: 'auth' };
    case err.status === 403: return { ...base, kind: 'forbidden' };
    case err.status === 404: return { ...base, kind: 'notFound' };
    case err.status === 409 || err.status === 412: return { ...base, kind: 'conflict' };
    case err.status === 400 || err.status === 422:
      return {
        ...base,
        kind: 'validation',
        fieldErrors: Object.fromEntries(
          (p.errors ?? []).map((e: { pointer: string; detail: string }) => [e.pointer.replace('#/', ''), e.detail]),
        ),
      };
    case err.status === 429: return { ...base, kind: 'rateLimited' };
    default: return { ...base, kind: 'server' };
  }
}
```

### Optimistic concurrency with ETag / If-Match

```typescript
@Service()
export class OrderApi {
  private http = inject(HttpClient);

  load(id: string) {
    return this.http
      .get<Order>(`/api/orders/${id}`, { observe: 'response' })
      .pipe(map(res => ({ order: res.body!, etag: res.headers.get('ETag')! })));
  }

  update(id: string, patch: Partial<Order>, etag: string) {
    return this.http.patch<Order>(`/api/orders/${id}`, patch, {
      headers: { 'If-Match': etag, 'Content-Type': 'application/merge-patch+json' },
    });
    // 412 → "This order was changed by someone else. Reload?"
  }
}
```

### Reading data with `httpResource` (signals)

```typescript
@Component({
  selector: 'app-order-list',
  template: `
    @if (orders.isLoading()) { <app-spinner /> }
    @else if (orders.error()) { <app-error [error]="orders.error()" /> }
    @else {
      @for (o of orders.value()?.items ?? []; track o.id) { <app-order-row [order]="o" /> }
      @empty { <p>No orders yet.</p> }
    }
  `,
})
export class OrderListComponent {
  readonly status = input<'OPEN' | 'CLOSED'>('OPEN');
  readonly orders = httpResource<Page<Order>>(() => `/api/orders?status=${this.status()}&limit=20`);
}
```

Note: since v22 `HttpClient` (and so `httpResource`) uses `FetchBackend` by default and `withFetch()` is a deprecated no-op. If you need **upload progress events**, opt back into XHR with `provideHttpClient(withXhr())`; `reportProgress` is deprecated in favour of `reportUploadProgress` / `reportDownloadProgress`. On pre-v22 codebases, `withFetch()` was the opt-in (recommended for SSR).

---

## D. Red flags

- "REST means JSON over HTTP." → Say instead: "REST is a set of constraints; most APIs are pragmatic level-2 REST, and I care about consistent semantics."
- "We use POST for everything, it's simpler." → "Correct methods give us caching, safe retries and clearer contracts."
- "401 and 403 are basically the same." → "401 means re-authenticate; 403 means you're known but not allowed — different UX."
- "Just retry failed requests." → "Retry only idempotent or idempotency-keyed requests, on transient errors, with backoff."
- "CORS is a frontend bug; I disable web security in Chrome." → "CORS is server opt-in enforced by the browser; I use a dev proxy and fix server config or go same-origin."
- "JWTs are encrypted, so it's safe to put user data in them." → "JWTs are signed, not encrypted; the payload is public."
- "localStorage is fine for tokens." → "It's an XSS trade-off; I prefer in-memory + rotation or a BFF with httpOnly cookies."
- "We still use the implicit flow." → "Authorization Code + PKCE; implicit is deprecated."
- "We cache everything for a year for performance." → "Hashed assets immutable, index.html no-cache."
- "It works in Postman, so the API is fine." → "Postman doesn't enforce CORS or cookies the way a browser does."
- "I hand-write all the API models." → "I generate types from OpenAPI and guard with contract diffs."
- "Error handling is done in each component with alert()." → "One interceptor + error mapper, Problem Details, feature-level UX where it adds value."

---
name: scraping
description: Web scraping and automation standards with Playwright + TypeScript — API interception over DOM parsing, resilient locators, Zod validation of extracted data, retries, rate limiting, and checkpoint/resume. Use when building or reviewing scrapers, crawlers, bots, data extraction pipelines, headless browser automation, or anything using Playwright or Puppeteer outside of E2E testing.
---

# Skill — Web Scraping & Automation (Playwright + TypeScript)

## Agent Behavior

- **Before coding**: Analyze the target site structure. Check if there's a public API or structured data (JSON-LD, RSS, sitemap) before resorting to HTML scraping.
- **Network-first**: Always inspect network requests. If data exists in an API response, intercept it rather than parsing DOM. An API observed in the browser is not automatically public or authorized — never reuse private tokens or endpoints beyond the authorized scope.
- **Authorization first**: `robots.txt` is a signal, not authorization. Before extracting, confirm the target is authorized — own property, partner integration, explicit permission, or an official API/ToS allowance — and consider data rights, privacy/PII, retention, and purpose. Include reasonable delays between requests and identify the scraper via User-Agent.

## Architecture

- For medium/large scrapers, use **Page Object Model (POM)** to separate selectors from extraction logic. For small one-off extractions, cohesive functions are enough — separate navigation, parsing, and persistence only when it buys real maintenance:
```typescript
class LoanListingPage {
  constructor(private page: Page) {}

  async getLoanCards() {
    await this.waitForListComplete();
    return this.page.getByRole('article').all();
  }

  async extractLoanData(card: Locator): Promise<RawLoanData> {
    return {
      amount: await card.getByTestId('loan-amount').textContent(),
      status: await card.getByRole('status').textContent(),
    };
  }
}
```
- `.all()` returns whatever is present **at call time** — before enumerating, establish a completeness signal (loading indicator gone, expected count reached, last-page marker) appropriate to the page's pagination/lazy loading. Otherwise partial extraction gets reported as success.
- Include a **retry utility** with exponential backoff and jitter. Retry ONLY classified transient failures (timeouts, 5xx, network resets, 429 honoring `Retry-After`); never auto-retry 401/403/404, anti-bot blocks, schema validation errors, or non-idempotent mutations — and bound the whole operation with a total deadline:
```typescript
async function withRetry<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  { maxAttempts = 3, baseDelay = 1000, attemptTimeoutMs = 30_000, totalDeadlineMs = 120_000 } = {},
): Promise<T> {
  const startedAt = Date.now();
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn(AbortSignal.timeout(attemptTimeoutMs));
    } catch (error) {
      const outOfBudget = Date.now() - startedAt >= totalDeadlineMs;
      if (!isTransientError(error) || attempt === maxAttempts || outOfBudget) throw error;
      const retryAfterMs = retryAfterFrom(error);
      const jitter = Math.random() * 500;
      await new Promise((r) => setTimeout(r, retryAfterMs ?? baseDelay * 2 ** attempt + jitter));
    }
  }
  throw new Error('Unreachable');
}
```
Pass the `signal` into the underlying fetch/page operations so a hung attempt actually gets cancelled — finite attempts alone do not bound the duration of one attempt.

## Locator Rules (Strict)

- **BANNED**: Generic CSS/XPath selectors (`div > span`, `#app > div:nth-child(3)`) — these break on any layout change.
- **Required priority order**:
  1. `getByRole` — most resilient, semantic
  2. `getByLabel` — for form elements
  3. `getByTestId` — when no semantic option exists
  4. `locator.filter({ hasText: '...' })` — anchor to content, not structure
- If none work, document **why** a fragile selector was necessary.

## Data Validation (Mandatory)

- Define **Zod schemas** for all extracted entities. TypeScript types are not enough at runtime. Use `safeParse` — never crash the pipeline on bad data:
```typescript
const LoanDataSchema = z.object({
  amount: z.string().transform(parseAmount),
  status: z.enum(['active', 'closed', 'pending']),
  borrower: z.string().min(1),
});

const result = LoanDataSchema.safeParse(rawData);
if (!result.success) {
  const issues = result.error.issues.map(({ path, code }) => ({ path, code }));
  logger.warn({ issues, sourceUrl: sanitizeUrl(page.url()) }, 'Schema validation failed');
  return null;
}
```
- **Never log raw extracted payloads** — scraped data may contain PII (names, emails, addresses). Log issue paths/codes (custom Zod messages can embed received values) and a **sanitized** source identifier — strip query strings and tokens from URLs. The same applies to traces and screenshots.
- **Silent skips hide systemic failure**: a schema drift can invalidate 100% of records while the job still reports success. Track the rejection rate and fail or alert past a threshold; choose the policy per contract explicitly — skip-and-count, quarantine, or fail-fast.

## API Interception (Preferred Over DOM)

```typescript
const responsePromise = page.waitForResponse(
  (res) => res.url().includes('/api/loans') && res.status() === 200,
);
await page.getByRole('button', { name: 'Load more' }).click();
const response = await responsePromise;
const data = await response.json();
```

## Resource Management

- **Always** close browser contexts in `finally` blocks:
```typescript
const context = await browser.newContext();
try {
  return await extractListings(context);
} finally {
  await context.close();
}
```
- Blocking resources can reduce bandwidth and speed up extraction, but may change layout, lazy loading, and app behavior — validate against the target before adopting:
```typescript
await page.route('**/*.{png,jpg,gif,svg,woff,woff2,css}', (route) => route.abort());
```

## Waits & Timing

- **BANNED**: `waitForTimeout` (hard sleeps) — flaky and slow.
- **Required**: Explicit predicates:
  - `waitForResponse` — wait for specific API call
  - `waitForFunction` — wait for DOM condition
  - `toBeVisible` / `toBeAttached` — wait for element state
  - `waitForLoadState('networkidle')` — only when truly needed
- Add a **health check** at extraction start:
```typescript
await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 });
```

## Rate Limiting & Politeness

- Derive delays from the target's published limits (`Retry-After`, API quotas, ToS). Absent explicit guidance, use conservative randomized delays (e.g. 1-3 seconds) and cap total concurrency.
- Limit concurrent browser contexts to avoid overwhelming the target.
- If the site returns 429 (Too Many Requests), back off exponentially.
- For large extractions, implement **checkpoint/resume** — save progress periodically and resume from the last checkpoint on restart instead of re-extracting everything. Record a checkpoint only **after** the batch it covers is durably persisted:
```typescript
type Checkpoint = {
  lastProcessedPage: number;
  extractedIds: string[];
  timestamp: Date;
};
```

## Blocks & Anti-Bot Controls

- Do **NOT** circumvent authentication, CAPTCHAs, rate limits, paywalls, IP blocks, or anti-bot controls. Being blocked is a signal to **stop** — confirm authorization with the target or switch to an official API. Never respond to a block by increasing evasion.
- Identify the scraper honestly via User-Agent. Realistic viewport and in-viewport clicking are for correctness (elements must be interactable), not disguise.
- Header-order spoofing and proxy rotation are off-limits unless the target explicitly authorizes automated access and they solve an operational problem (e.g. sanctioned load distribution), not an evasion one.

## Output & Deliverables

For a **new scraper of meaningful size**, provide:
1. **TypeScript code** (POM structure when the size justifies it)
2. **Zod schemas** for all extracted entities
3. **Brief architecture note** explaining: how dynamic loading was handled, whether anti-bot controls were encountered (and that extraction stopped/was authorized), and whether API interception or DOM parsing was used (and why)

For small fixes or reviews, deliver only what the request needs — don't scaffold POM, schemas, and architecture notes onto a one-line change.

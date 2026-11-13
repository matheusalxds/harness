---
name: test-params-factory
description: >
  Apply the canonical test-parameter factory pattern in HouseNumbers projects whenever
  creating or editing test files (*.spec.ts, *.test.ts, *.eval.spec.ts). Extract repeated
  test parameters into a makeXxxParams() factory and mutate inline for variations. Trigger
  BEFORE writing any new `it()` block, BEFORE creating a new spec file, and when touching
  an existing spec file that already has duplicated parameter literals — refactor in place.
  HouseNumbers projects only; elsewhere follow the project's own test-data conventions.
---

# Test Parameter Factory Pattern

This is the canonical test-data convention for **HouseNumbers projects**. When writing tests there, **always** extract repeated parameters into a factory function and reuse it across `it()` blocks. Mutate the result inline when a test needs a variation. In non-HouseNumbers projects, follow whatever convention the project already uses.

---

## The Pattern

```ts
const makeFooParams = () => ({
  fieldA: "any_value_a",
  fieldB: "any_value_b",
  fieldC: 42,
});

it("does X with default params", async () => {
  const params = makeFooParams();
  const result = await sut.handle(params);
  expect(result).toBeOk();
});

it("does Y with overridden field", async () => {
  const params = makeFooParams();
  params.fieldB = "another_value";
  const result = await sut.handle(params);
  expect(result.kind).toBe("variantY");
});
```

---

## Rules

1. **One factory per logical input shape.** If `optIn`, `optOut`, and `isEnabledForLoan` share fields, you may share one factory and pick the subset each test needs. If they diverge significantly, write separate factories.

2. **Factory returns fresh values per call.** Use `uuid()`, `new Date()`, or fresh literals inside the factory so each `it()` gets independent data. Never return a module-level constant.

3. **Mutation over re-spreading.** Prefer:
   ```ts
   const params = makeFooParams();
   params.fieldB = "x";
   ```
   over:
   ```ts
   const params = { ...makeFooParams(), fieldB: "x" };
   ```
   Mutation is shorter and the user's stated preference.

4. **Re-call the factory for independent data sets.** When a test needs two distinct subjects (e.g., tenant A vs tenant B), call the factory twice rather than copying-and-tweaking:
   ```ts
   const a = makeFooParams();
   const b = makeFooParams();
   b.fieldA = a.fieldA;
   ```
   Assign across the two results only for the fields that should intentionally match.

5. **Factory lives at the top of the spec file**, above all `describe()` blocks. One factory per file unless the file genuinely tests multiple unrelated shapes.

6. **Name follows `make<Subject>Params`.** Examples: `makeOptInParams`, `makeCreateTaskParams`, `makeBorrowerCreateParams`. Avoid `mockFooParams` (these are real data, not mocks) and avoid `buildFoo` unless that matches an existing helper convention in the package.

---

## Refactoring Existing Tests

When opening a spec file that doesn't follow this pattern and you're touching it for any reason — **refactor in place**. Don't leave a mixed file with some tests using the factory and others duplicating literals.

Scope of refactor:
- Only the tests in the file you're already editing.
- Don't open unrelated spec files just to refactor them — wait until the next time you touch them.

---

## Anti-Patterns

❌ **Duplicating the full object literal in every test:**
```ts
it("test 1", () => {
  const params = { tenantId: uuid(), loanId: uuid(), feature: "x", by: "user" };
  // ...
});
it("test 2", () => {
  const params = { tenantId: uuid(), loanId: uuid(), feature: "x", by: "other" };
  // ...
});
```

❌ **Module-level constant pretending to be a factory** (shared mutable state across tests):
```ts
const PARAMS = { tenantId: "fixed", loanId: "fixed", ... };
```

❌ **Factory with frozen output** (forces awkward spread for any change):
```ts
const makeParams = () => Object.freeze({ ... });
```

---

## Companion rules (always apply alongside the factory)

### Canonical constants over string literals
When a factory field or test value is a domain value (status, type, reason, category), import the canonical constant instead of typing the string. In the HouseNumbers/Zora monorepo: `packages/shared-domains/src/domain/` first (`FILE_STATUS`, `INBOX_ITEM_STATUS`, `DECLINE_REASON`, ...), then the service's own domain module; in other HouseNumbers repos, the project's own constants module. Grep by the **value** to find the constant; it may have an unexpected name. A rename must break the test at compile time — a literal silently keeps passing against a stale contract. If mutation across tests requires it, widen with the shared type (`INBOX_ITEM_STATUS.PENDING as InboxItemStatus`), never by dropping to a literal.

The same applies to non-domain canonical values: HTTP status codes come from the service's constants module (e.g. `@errors/http-status-codes` in Zora's agent-service) — `toBe(HTTP_STATUS_BAD_REQUEST)`, never bare `400`/`200`/`502` — matching whatever module the production code under test imports. In result assertions, keep the guarantee with computed keys: `{ [DECLINE_REASON.ALREADY_RESOLVED]: 1 }`.

### Hoist repeated per-suite values into describe-level consts
When the same literal appears across multiple `it()` blocks (`baseUrl`, `tenantId`, URLs, entity ids), declare it once at the top of the `describe` and reuse it, including in assertions. Deliberate variations derive from the const (`` `${BASE_URL}/` `` for a trailing-slash case). Also use a shared const to make hidden couplings explicit — e.g. when a factory default and a test's map key must agree on the same id.

## When NOT to use a factory

- A spec file with a single `it()` block — no repetition, no need.
- Tests where every field genuinely differs from every other test — the factory adds nothing.
- Tests whose parameters are best expressed as inline literals for readability (rare; ask before skipping).
- **The divergent shape is the test's subject.** A shared factory is for the SAME JSON reused across tests — same shape, different values — where each test overrides only the specific attribute it validates (e.g. `const loan = makeLoanApplication(); loan.attributes.fileStatus = FILE_STATUS.ON_HOLD`). When a test proves behavior driven by a *structurally different* payload — a field's presence/absence, a different envelope (a DSN bounce carrying `id` with no `to`, an HTML email where `body !== cleanedBody`, a fallback fixture with only `cleanedBody`) — keep that fixture as its own scenario-named factory or explicit inline literal. Do NOT widen the shared factory with kitchen-sink optional params to absorb divergent shapes: the reader must see the distinctive shape at a glance, and a bag of optional params hides which divergence the test is about.

If in doubt, write the factory. Removing one is cheaper than discovering 12 duplicated literals later.

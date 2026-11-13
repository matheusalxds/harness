---
name: frontend-react-router
description: React Router 7 framework-mode engineering standards, and Remix v2 as its predecessor — loaders, actions, forms with progressive enhancement, error boundaries, sessions, and testing. Use when writing or reviewing code in a React Router 7 framework-mode or Remix v2 project, or when the conversation involves loaders, actions, route modules, useLoaderData, useFetcher, the data() helper, react-router, or @remix-run packages.
---

# Skill — Frontend Engineering (React Router 7 framework mode)

> **Scope note:** React Router v7 "framework mode" is the current line; Remix v2's framework layer merged into it. In React Router 7, `json()` and `defer()` were **removed** — loaders/actions return raw objects via single fetch, and when HTTP metadata matters (status codes, headers) use `data(payload, { status, headers })`; replacing a 422 response with a bare object silently loses the status. Apps still pinned to Remix v2 keep `json()` and `defer()`; the loader/action/Form patterns are identical either way. Check `package.json` (`react-router` vs `@remix-run/*`) before applying version-specific APIs. The code examples below are written against the Remix v2 API with the React Router 7 equivalent noted inline.

## Agent Behavior

- **Before coding**: Inspect `remix.config.ts` or `vite.config.ts` to determine if the project uses Remix v2 with Vite (default) or the classic compiler. Check for `routes/` structure (flat routes vs nested).
- **Styling detection**: Check for Tailwind, CSS Modules, or styled-components before writing styles.
- **Testing**: Write tests for loaders, actions, and complex components using Vitest + Testing Library. Test server logic separately from UI.

## Core Principles

- Remix is **server-first**. Default to server logic. Only move to client when interactivity demands it.
- Embrace HTTP semantics — requests, responses, status codes, headers, cookies.
- Never think SPA-first. If you catch yourself reaching for `useEffect` to fetch data, stop and use a loader.

## Routing & Data Loading

- **Loaders** for all read operations — they run on the server and return typed data. Always type loaders explicitly. (Examples below use the Remix v2 `json()` API — in React Router 7, return raw objects instead.)
```typescript
export const loader = async ({ params, request }: LoaderFunctionArgs) => {
  const user = await getUser(request);
  if (!user) throw redirect('/login');

  const loan = await getLoanOwnedBy(params.id, user.id);
  if (!loan) throw json({ error: 'Not found' }, { status: 404 });

  return json({ loan });
};

export default function LoanPage() {
  const { loan } = useLoaderData<typeof loader>();
  return <LoanDetails loan={loan} />;
}
```
- **Actions** for all mutations — one action per route, use `intent` field to distinguish operations. Actions authenticate and authorize on their own: a protected loader does NOT protect the route's action, and each handler must verify the actor may mutate the specific resource:
```typescript
export const action = async ({ request }: ActionFunctionArgs) => {
  const user = await requireUser(request);
  const formData = await request.formData();
  const intent = formData.get('intent');

  switch (intent) {
    case 'approve': return handleApprove(user, formData);
    case 'reject': return handleReject(user, formData);
    default: throw json({ error: 'Invalid intent' }, { status: 400 });
  }
};
```
- Keep loaders and actions **thin** — delegate business logic to service functions.
- Use `defer` + `Await` for non-critical data that can stream — await the critical data (`loan`), pass the pending promise for the streamable rest (`activity`). (Remix v2 API — in RR7, return the raw promise and stream without `defer`.)
```typescript
export const loader = async ({ params }: LoaderFunctionArgs) => {
  const loan = await getLoanById(params.id);
  const activity = getActivityLog(params.id);

  return defer({ loan, activity });
};
```

## State Management

- **Server state is the default.** Loader data is the source of truth.
- Client state only for ephemeral UI concerns (modals, form field values, accordion state).
- Never duplicate loader data into `useState`. Use `useLoaderData` directly.
- If you need optimistic UI, use `useFetcher` with its built-in states.

## Forms & Mutations

- Always use `<Form>` (or `useFetcher.Form`) over custom fetch logic.
- Progressive enhancement by default — forms work without JavaScript.
- Server-side validation with typed error responses — the action returns the errors (Remix v2 `json()`; in RR7 use `data({ errors }, { status: 422 })` to keep the status), the component reads them via `useActionData`:
```typescript
const result = schema.safeParse(Object.fromEntries(formData));
if (!result.success) {
  return json({ errors: result.error.flatten().fieldErrors }, { status: 422 });
}

const actionData = useActionData<typeof action>();
{actionData?.errors?.email && <span>{actionData.errors.email}</span>}
```

## Error Handling

- Use `ErrorBoundary` exports per route for granular error recovery.
- Throw `Response` objects with proper status codes from loaders/actions — never return error objects with 200.
- Distinguish expected errors (404, 422) from unexpected failures (500).

## Performance

- Minimize client JS — question every `.client.ts` module and every component that exists only to hydrate interactivity.
- Avoid `useEffect` for data fetching. If you need to refetch, use `useFetcher` or `useRevalidator`.
- Be mindful of waterfall requests in nested routes — use `defer` or parallel loaders.
- Prefetch links with `<Link prefetch="intent">` for perceived performance.

## Testing

- Test loaders and actions as standalone async functions (v2 contract shown — `response.json()`; in RR7, loaders return the object directly, so assert on the return value):
```typescript
describe('loader', () => {
  it('should return loan data for valid id', async () => {
    const response = await loader({
      params: { id: 'loan-123' },
      request: new Request('http://test'),
      context: {},
    });
    const data = await response.json();
    expect(data.loan.id).toBe('loan-123');
  });
});
```
- Test components with `@testing-library/react` + `createRemixStub` for route context.
- Test form submissions through actions, not by simulating DOM events.

## Session & Auth

- Use Remix session storage (`createCookieSessionStorage`, `createFileSessionStorage`) — never raw cookies.
- Protect routes in loaders with early `throw redirect('/login')`.
- Never expose sensitive session data to the client.

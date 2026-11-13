---
name: frontend-next
description: Next.js App Router engineering standards — Server vs Client Components, Server Actions with in-action auth, data fetching and caching, routing, metadata, performance, and testing. Use when writing or reviewing code in a Next.js project, or when the conversation involves App Router, "use client", Server Components, Server Actions, React Server Components, next/image, or middleware/proxy.
---

# Skill — Frontend Engineering (Next.js / App Router)

## Agent Behavior

- **Before coding**: Check `next.config.ts` and the project structure to determine if it uses App Router (`app/`) or Pages Router (`pages/`). Default guidance below is for **App Router** — adapt if the project uses Pages Router.
- **Version check**: Confirm the **resolved** Next.js version (lockfile or `next --version` — `package.json` may hold a range) before applying version-dependent APIs — async `params` and `fetch` caching defaults changed across 14/15/16. Follow the docs for the installed version; don't assume one mental model fits all.
- **Styling detection**: Check for Tailwind, CSS Modules, or other styling solutions before writing styles.
- **Testing**: Write tests using Vitest + Testing Library for components. Test Server Actions as standalone functions.

## Core Principles

- **Server Components are the default.** Only add `"use client"` when the component needs interactivity (hooks, event handlers, browser APIs).
- Think in terms of **request → server render → stream to client**. Client JS is the exception, not the rule.
- Minimize the client bundle. Push logic to the server wherever possible.

## Server vs Client Components

```
Server Components (default)           Client Components ("use client")
├── Data fetching (async/await)       ├── useState, useEffect, useRef
├── Database/API access               ├── Event handlers (onClick, onChange)
├── Sensitive logic (secrets, auth)   ├── Browser APIs (localStorage, etc.)
└── Heavy dependencies (keep off      └── Interactive UI (forms, modals,
    the client bundle)                     animations)
```

**Rules:**
- Never make a component `"use client"` just because a child needs it. Push the client boundary as deep as possible.
- Server Components can import Client Components, but not the reverse — a Client Component can still render server-composed UI passed via `children`/serializable props.
- Pass server data as props to Client Components — don't refetch on the client by default (polling, real-time, and optimistic UI are legitimate exceptions; keep tokens and secrets server-side).

## Data Fetching

- Fetch data directly in Server Components with `async/await` — e.g. `app/loans/[id]/page.tsx`, no `"use client"`:
```typescript
export default async function LoanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const loan = await getLoanById(id);
  if (!loan) notFound();

  return <LoanDetails loan={loan} />;
}
```
- Use `fetch` with Next.js caching/revalidation when calling external APIs. Cached for 60 seconds:
```typescript
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 60 },
});
```
  No cache, for dynamic data:
```typescript
const data = await fetch('https://api.example.com/data', {
  cache: 'no-store',
});
```
- Never serve per-user or per-tenant data from shared caches — `revalidate` caches are shared across requests; session-scoped data is `no-store` (or keyed so one user can never receive another's entry).
- For mutations, use **Server Actions** (e.g. `app/actions/loan.ts`). Treat every Server Action as an **untrusted remote boundary** — the framework exposes it to arbitrary requests. Authenticate, authorize the specific resource, and validate input **inside the action itself**; never trust IDs from the browser as proof of ownership, never spread raw formData into a write (mass assignment), never assume middleware protected it:
```typescript
'use server';

export async function approveLoan(formData: FormData) {
  const session = await verifySession();
  if (!session) return { errors: { auth: ['Unauthorized'] } };

  const result = schema.safeParse({ id: formData.get('loanId') });
  if (!result.success) return { errors: result.error.flatten().fieldErrors };

  const loan = await getLoanOwnedBy(result.data.id, session.userId);
  if (!loan) return { errors: { auth: ['Not found'] } };

  await updateLoanStatus(loan.id, 'APPROVED');
  revalidatePath(`/loans/${loan.id}`);
}
```

## Routing & Layouts

- Use `layout.tsx` for shared UI that persists across navigations (sidebars, headers).
- Use `loading.tsx` for automatic Suspense boundaries during navigation.
- Use `error.tsx` for route-level error boundaries.
- Use `not-found.tsx` for 404 handling.
- Route groups `(group)` for organizing without affecting URL structure.
- Parallel routes `@slot` for simultaneous rendering of multiple pages.

## Metadata & SEO

- Use the Metadata API, not `<Head>`:
```typescript
export const metadata: Metadata = {
  title: 'Loan Application | HouseNumbers',
  description: '...',
};
```
  Dynamic metadata — `params` is a Promise, await it:
```typescript
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const loan = await getLoanById(id);
  return { title: `Loan ${loan.number}` };
}
```

## Performance

- Prefer `next/image` for content images when compatible — exceptions exist (inline SVG, loader-incompatible sources, cases where optimization adds nothing).
- Use `next/font` for font optimization.
- Consider `dynamic()` for heavy below-the-fold Client Components — decide by bundle size and layout-shift cost, not by position alone.
- Avoid `useEffect` for data fetching — that's what Server Components solve.
- Use `Suspense` boundaries strategically to enable streaming.

## Middleware / Proxy

- Middleware (`middleware.ts`; renamed `proxy.ts` in Next.js 16) is a request-shaping layer, **not a security boundary**. Middleware auth bypasses have happened repeatedly in the framework's history — never let it be the only auth check.
- Real authentication/authorization lives where the data lives: inside Server Actions, Route Handlers, and the data-access layer.
- Use middleware only for UX-level optimistic redirects and routing concerns:
```typescript
export function middleware(request: NextRequest) {
  const token = request.cookies.get('session');
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
```

## Testing

- Test Server Components by testing their data-fetching logic as standalone functions.
- Test Client Components with `@testing-library/react`:
```typescript
describe('LoanCard', () => {
  it('should display loan amount formatted as currency', () => {
    render(<LoanCard loan={mockLoan} />);
    expect(screen.getByText('$250,000.00')).toBeInTheDocument();
  });
});
```
- Test Server Actions as async functions with mocked dependencies.
- Use `next/navigation` mocks for testing components that use `useRouter`, `usePathname`.

## Accessibility

- Semantic HTML elements (`<nav>`, `<main>`, `<article>`, `<button>`) over generic `<div>`.
- Coherent heading hierarchy — a single `<h1>` per page is a good default; hierarchy coherence is the actual requirement.
- Labels for all form inputs.
- Keyboard navigation support alongside mouse events.
- Meaningful `alt` text for images.

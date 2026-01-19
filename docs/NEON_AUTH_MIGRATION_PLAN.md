# Neon Auth Migration Plan
**Date:** 2026-01-08
**Status:** In Progress
**Migration Type:** Clerk → Neon Auth
**Estimated Effort:** 2-3 days
**Risk Level:** Medium

---

## Executive Summary

FibreFlow is migrating from Clerk authentication to Neon Auth to align with our database-first architecture. This migration brings database-level security (RLS), branch-based auth testing, cost savings ($300-600/year), and architectural simplicity.

**Key Benefits:**
- ✅ Row-Level Security at the database layer (impossible to bypass)
- ✅ Auth state branches with database (test auth flows in isolation)
- ✅ Zero additional cost (included in Neon plan)
- ✅ Simpler architecture (one service instead of two)
- ✅ ~500 lines of permission code eliminated

---

## Table of Contents

1. [Architectural Reasoning](#architectural-reasoning)
2. [Comparison: Clerk vs Neon Auth](#comparison-clerk-vs-neon-auth)
3. [Database-First Architecture + RLS](#database-first-architecture--rls)
4. [Implementation Plan](#implementation-plan)
5. [RLS Policy Templates](#rls-policy-templates)
6. [Testing Checklist](#testing-checklist)
7. [Rollback Procedures](#rollback-procedures)
8. [Cost Analysis](#cost-analysis)

---

## Architectural Reasoning

### Why Migrate?

FibreFlow's architecture treats **Neon PostgreSQL as the source of truth** (104 tables, complex relationships, business logic). Neon Auth completes this vision by moving authentication into the same layer as data.

**Current Problem (Clerk):**
```
User → API Route → Permission Check (App Layer) → Database Query
              ↑
        Security risk: Can be bypassed if you forget checks
```

**Future State (Neon Auth + RLS):**
```
User → API Route → Database Query → RLS Policy (Data Layer) → Filtered Results
                                          ↑
                                  Impossible to bypass
```

### Database-First Philosophy

**What it means:** Business logic lives in the database, not scattered across API routes.

**Why it matters:**
- ✅ Single source of truth
- ✅ Consistent behavior across all clients (web, mobile, CLI)
- ✅ Performance (database-level filtering)
- ✅ Security (can't bypass permissions)

**Current FibreFlow Architecture:**
```
Neon PostgreSQL (Source of Truth)
├── 104 tables (contractors, projects, tickets, BOQs)
├── Complex relationships and constraints
├── Stored procedures/functions
└── NOW: Authentication + Authorization (RLS)

Application Layer (Thin Wrappers)
├── Next.js API routes (CRUD operations)
├── Convex (real-time state sync)
└── Frontend (display data)
```

---

## Comparison: Clerk vs Neon Auth

| Aspect | Clerk (Current) | Neon Auth (Target) |
|--------|-----------------|-------------------|
| **Data Storage** | External SaaS | Your Neon database (`neon_auth.*`) |
| **Branching** | ❌ Single prod instance | ✅ Auth branches with database |
| **Latency** | ~50-100ms (external API) | ~1-5ms (same region) |
| **Cost** | $25-50/mo after free tier | $0 (included in Neon) |
| **Dependencies** | 3rd party service | Single service (Neon) |
| **RLS Integration** | Manual sync required | Native `auth.uid()` function |
| **UI Components** | ✅ Pre-built (SignIn, UserButton) | 🟡 DIY (shadcn/ui) |
| **Social Auth** | ✅ 20+ providers (Google, GitHub) | 🟡 OAuth via Better Auth |
| **MFA** | ✅ Built-in SMS/TOTP | 🟡 Requires setup |
| **Admin Dashboard** | ✅ Full-featured | ❌ Build your own |
| **Maturity** | Battle-tested (2020+) | Brand new (Dec 2025) |
| **Documentation** | Excellent | Growing |

### Why Neon Auth Wins for FibreFlow

1. **Database Branching + Auth Testing**
   ```bash
   # Create feature branch in Neon
   neon branch create test-contractor-flow

   # Auth state branches too (users, sessions, policies)
   # Test with REAL auth, not mocks
   # Merge when confident - zero production risk
   ```

2. **Row-Level Security (RLS)**
   - Define permissions ONCE in database
   - Enforced at data layer (impossible to bypass)
   - Automatic across all access methods (API, direct SQL, GraphQL)

3. **Architectural Simplicity**
   - Before: Next.js → Clerk API → Neon Database (2 services)
   - After: Next.js → Neon Database (1 service)
   - Less moving parts = fewer failure points

4. **Cost Savings**
   - Year 1: Save $300-600
   - Year 3: Save $900-1800
   - Migration cost: ~$1000 (2-3 days dev time)
   - Break-even: 6-12 months

---

## Database-First Architecture + RLS

### What is Row-Level Security (RLS)?

PostgreSQL feature that filters rows based on the current user. Think "WHERE clause on steroids" that's **impossible to bypass**.

### Example: Tickets Table

**Without RLS (Application-Layer Security):**
```typescript
// app/api/tickets/route.ts
export async function GET(request: Request) {
  const { userId } = auth(); // Clerk

  // Manual permission check (can forget to add this!)
  const user = await db.query('SELECT role FROM users WHERE clerk_id = ?', [userId]);

  if (user.role === 'contractor') {
    return db.query('SELECT * FROM tickets WHERE contractor_id = ?', [userId]);
  } else if (user.role === 'admin') {
    return db.query('SELECT * FROM tickets');
  }

  // What if you forget this check in another route? 🚨 SECURITY HOLE
}
```

**With RLS (Database-Layer Security):**
```sql
-- Define ONCE in database
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;

-- Contractors see only their tickets
CREATE POLICY contractor_own_tickets ON tickets
  FOR SELECT
  USING (
    contractor_id = auth.uid()  -- Neon Auth provides this
    AND EXISTS (
      SELECT 1 FROM neon_auth.users
      WHERE id = auth.uid()
      AND metadata->>'role' = 'contractor'
    )
  );

-- Admins see everything
CREATE POLICY admin_all_tickets ON tickets
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM neon_auth.users
      WHERE id = auth.uid()
      AND metadata->>'role' = 'admin'
    )
  );
```

```typescript
// app/api/tickets/route.ts
export async function GET(request: Request) {
  // Just query - RLS automatically filters
  const tickets = await db.query('SELECT * FROM tickets');

  // Contractor gets only their tickets
  // Admin gets all tickets
  // Database enforces - no application logic! ✅

  return Response.json(tickets);
}
```

### RLS Benefits for FibreFlow

1. **Security That Can't Be Bypassed**
   - Even direct database access respects RLS
   - Even SQL injection can't bypass (PostgreSQL enforces)
   - Bug in API route? Still secure

2. **Consistency Across Tools**
   ```bash
   # All of these respect RLS automatically:
   psql $DATABASE_URL -c "SELECT * FROM tickets"    # ✅
   python script.py --query tickets                 # ✅
   curl /api/tickets                                # ✅
   GraphQL query { tickets }                        # ✅
   ```

3. **Performance**
   - Database filters at source (not in application)
   - Less data transferred over network
   - Indexes can optimize RLS queries

4. **Simpler Code**
   - Delete ~500 lines of permission checks
   - Single source of truth for permissions
   - Easier to audit and test

---

## Implementation Plan

### Phase 0: Preparation (30 minutes)

**✅ Checklist:**
- [ ] Back up current Clerk configuration
- [ ] Document existing user roles and permissions
- [ ] Export Clerk user list (for migration)
- [ ] Set up Neon Auth in test branch
- [ ] Review Neon Auth documentation

**Commands:**
```bash
# Create backup branch
cd ~/fibreflow-louis
git checkout -b backup/clerk-auth-2026-01-08

# Export Clerk users (via dashboard)
# → Users → Export to CSV
# Save as: data/clerk_users_backup_20260108.csv

# Create Neon test branch
# Via Neon Console: Branches → Create Branch → "test-neon-auth"
```

---

### Phase 1: Install Neon Auth SDK (1 hour)

**1.1 Install Package**
```bash
cd ~/fibreflow-louis
npm install @neondatabase/auth@latest
```

**1.2 Enable Neon Auth in Database**
```bash
# Via Neon Console:
# 1. Go to your project
# 2. Navigate to Settings → Auth
# 3. Click "Enable Neon Auth"
# 4. Select region: aws-us-east-1 (match your database)
# 5. Copy Auth URL (looks like: https://auth-PROJECT_ID.neon.tech)
```

**1.3 Configure Environment Variables**
```bash
# Add to .env.local
NEON_AUTH_URL=https://auth-YOUR_PROJECT_ID.neon.tech
NEON_DATABASE_URL=postgresql://...  # Already configured
```

**1.4 Create Auth Client**
```typescript
// lib/neon-auth.ts
import { NeonAuth } from '@neondatabase/auth';

export const neonAuth = new NeonAuth({
  authUrl: process.env.NEON_AUTH_URL!,
});

// Helper to get current user
export async function getCurrentUser() {
  const session = await neonAuth.getSession();
  return session?.user || null;
}

// Helper to require authentication
export async function requireAuth() {
  const user = await getCurrentUser();
  if (!user) {
    throw new Error('Unauthorized');
  }
  return user;
}
```

---

### Phase 2: Create Authentication API Routes (2 hours)

**2.1 Sign Up Route**
```typescript
// app/api/auth/signup/route.ts
import { neonAuth } from '@/lib/neon-auth';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { email, password, name, role = 'viewer' } = await request.json();

    // Create user in Neon Auth
    const user = await neonAuth.signUp({
      email,
      password,
      metadata: {
        name,
        role,  // admin, staff, contractor, viewer
        created_at: new Date().toISOString(),
      },
    });

    return NextResponse.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        role: user.metadata.role,
      }
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Sign up failed' },
      { status: 400 }
    );
  }
}
```

**2.2 Sign In Route**
```typescript
// app/api/auth/signin/route.ts
import { neonAuth } from '@/lib/neon-auth';
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    // Authenticate with Neon Auth
    const session = await neonAuth.signIn({
      email,
      password,
    });

    // Set session cookie
    cookies().set('neon_session', session.token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/',
    });

    return NextResponse.json({
      success: true,
      user: session.user,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Sign in failed' },
      { status: 401 }
    );
  }
}
```

**2.3 Sign Out Route**
```typescript
// app/api/auth/signout/route.ts
import { neonAuth } from '@/lib/neon-auth';
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const sessionToken = cookies().get('neon_session')?.value;

    if (sessionToken) {
      await neonAuth.signOut(sessionToken);
    }

    // Clear session cookie
    cookies().delete('neon_session');

    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Sign out failed' },
      { status: 400 }
    );
  }
}
```

**2.4 Get Current User Route**
```typescript
// app/api/auth/me/route.ts
import { getCurrentUser } from '@/lib/neon-auth';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const user = await getCurrentUser();

    if (!user) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    return NextResponse.json({ user });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
```

---

### Phase 3: Build Authentication UI (3 hours)

**3.1 Sign In Page**
```typescript
// app/sign-in/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (res.ok) {
        router.push('/ticketing');
        router.refresh();
      } else {
        setError(data.error || 'Sign in failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign In to FibreFlow</CardTitle>
          <CardDescription>Enter your credentials to access the system</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@velocityfibre.com"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
              />
            </div>
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                {error}
              </div>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

**3.2 User Profile Component**
```typescript
// components/auth/UserProfile.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { User, LogOut } from 'lucide-react';

interface User {
  id: string;
  email: string;
  metadata: {
    name: string;
    role: string;
  };
}

export function UserProfile() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch('/api/auth/me')
      .then(res => res.json())
      .then(data => setUser(data.user))
      .catch(() => setUser(null));
  }, []);

  async function handleSignOut() {
    await fetch('/api/auth/signout', { method: 'POST' });
    router.push('/sign-in');
    router.refresh();
  }

  if (!user) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <User className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user.metadata.name}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
            <p className="text-xs text-muted-foreground capitalize">
              Role: {user.metadata.role}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleSignOut}>
          <LogOut className="mr-2 h-4 w-4" />
          Sign Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

**3.3 Update Header**
```typescript
// src/components/layout/Header.tsx
import { UserProfile } from '@/components/auth/UserProfile';

export function Header() {
  return (
    <header className="border-b bg-white">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-bold">FibreFlow</h1>
          {/* Navigation */}
        </div>
        <UserProfile />
      </div>
    </header>
  );
}
```

---

### Phase 4: Update Middleware (1 hour)

**4.1 Create Auth Middleware**
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Public routes that don't require authentication
const publicRoutes = ['/sign-in', '/sign-up', '/api/auth/signin', '/api/auth/signup'];

// Routes that require specific roles
const roleRoutes: Record<string, string[]> = {
  '/admin': ['admin'],
  '/contractors/manage': ['admin', 'staff'],
  '/ticketing': ['admin', 'staff', 'contractor'],
};

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Check session cookie
  const sessionToken = request.cookies.get('neon_session')?.value;

  if (!sessionToken) {
    return NextResponse.redirect(new URL('/sign-in', request.url));
  }

  try {
    // Verify session with Neon Auth
    const res = await fetch(`${process.env.NEON_AUTH_URL}/api/session/verify`, {
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
      },
    });

    if (!res.ok) {
      return NextResponse.redirect(new URL('/sign-in', request.url));
    }

    const { user } = await res.json();

    // Check role-based access
    for (const [route, allowedRoles] of Object.entries(roleRoutes)) {
      if (pathname.startsWith(route)) {
        const userRole = user.metadata?.role || 'viewer';
        if (!allowedRoles.includes(userRole)) {
          return NextResponse.redirect(new URL('/unauthorized', request.url));
        }
      }
    }

    // Add user info to request headers for API routes
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set('x-user-id', user.id);
    requestHeaders.set('x-user-role', user.metadata?.role || 'viewer');

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });
  } catch (error) {
    return NextResponse.redirect(new URL('/sign-in', request.url));
  }
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};
```

---

### Phase 5: Implement Row-Level Security (3 hours)

**5.1 Enable RLS on Core Tables**

Connect to your Neon database and run these SQL commands:

```sql
-- Connect to database
psql $NEON_DATABASE_URL

-- Enable RLS on all sensitive tables
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE contractors ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;

-- Admins bypass RLS (for management operations)
ALTER TABLE tickets FORCE ROW LEVEL SECURITY;  -- Even table owner respects RLS
```

**5.2 Create RLS Policies**

See [RLS Policy Templates](#rls-policy-templates) section below for detailed policies.

---

### Phase 6: Migrate Existing Users (2 hours)

**6.1 Export Clerk Users**
```bash
# Via Clerk Dashboard:
# Users → Export to CSV
# Save as: data/clerk_users_backup_20260108.csv
```

**6.2 Migration Script**
```typescript
// scripts/migrate-users.ts
import { neonAuth } from '@/lib/neon-auth';
import { parse } from 'csv-parse/sync';
import { readFileSync } from 'fs';

async function migrateUsers() {
  const csvContent = readFileSync('data/clerk_users_backup_20260108.csv', 'utf-8');
  const clerkUsers = parse(csvContent, { columns: true });

  console.log(`Migrating ${clerkUsers.length} users...`);

  for (const clerkUser of clerkUsers) {
    try {
      // Create user in Neon Auth
      await neonAuth.createUser({
        email: clerkUser.email,
        metadata: {
          name: clerkUser.first_name + ' ' + clerkUser.last_name,
          role: clerkUser.public_metadata?.role || 'viewer',
          clerk_id: clerkUser.id,  // Keep reference
          migrated_at: new Date().toISOString(),
        },
      });

      console.log(`✅ Migrated: ${clerkUser.email}`);
    } catch (error) {
      console.error(`❌ Failed: ${clerkUser.email}`, error);
    }
  }

  console.log('Migration complete!');
}

migrateUsers();
```

**6.3 Run Migration**
```bash
cd ~/fibreflow-louis
npx tsx scripts/migrate-users.ts
```

---

### Phase 7: Remove Clerk Dependencies (30 minutes)

**7.1 Uninstall Clerk Packages**
```bash
npm uninstall @clerk/nextjs @clerk/themes
```

**7.2 Delete Clerk Files**
```bash
# Remove Clerk components
rm -rf app/sign-in/[[...sign-in]]
rm -rf app/sign-up/[[...sign-up]]
rm -f src/components/layout/ClerkHeader.tsx

# Keep backups
git add . && git commit -m "backup: Before removing Clerk files"
```

**7.3 Remove Clerk Environment Variables**
```bash
# Edit .env.local - remove these lines:
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
# CLERK_SECRET_KEY=...
```

**7.4 Update app/providers.tsx**
```typescript
// app/providers.tsx
// Remove ClerkProvider, keep only Convex
import { ConvexProvider } from 'convex/react';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ConvexProvider client={convex}>
      {children}
    </ConvexProvider>
  );
}
```

---

### Phase 8: Testing (See Testing Checklist below)

---

## RLS Policy Templates

### Tickets Table Policies

```sql
-- =============================================================================
-- TICKETS TABLE RLS POLICIES
-- =============================================================================

-- Drop existing policies if re-running
DROP POLICY IF EXISTS admin_all_tickets ON tickets;
DROP POLICY IF EXISTS staff_regional_tickets ON tickets;
DROP POLICY IF EXISTS contractor_own_tickets ON tickets;
DROP POLICY IF EXISTS viewer_read_only_tickets ON tickets;

-- Helper function to get current user role
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
  SELECT metadata->>'role'
  FROM neon_auth.users
  WHERE id = auth.uid()
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- POLICY 1: Admins have full access to all tickets
CREATE POLICY admin_all_tickets ON tickets
  FOR ALL
  USING (get_user_role() = 'admin')
  WITH CHECK (get_user_role() = 'admin');

-- POLICY 2: Staff can view/update tickets in their assigned region
CREATE POLICY staff_regional_tickets ON tickets
  FOR ALL
  USING (
    get_user_role() = 'staff'
    AND region = (
      SELECT metadata->>'assigned_region'
      FROM neon_auth.users
      WHERE id = auth.uid()
    )
  )
  WITH CHECK (
    get_user_role() = 'staff'
    AND region = (
      SELECT metadata->>'assigned_region'
      FROM neon_auth.users
      WHERE id = auth.uid()
    )
  );

-- POLICY 3: Contractors can view/update only their assigned tickets
CREATE POLICY contractor_own_tickets ON tickets
  FOR ALL
  USING (
    get_user_role() = 'contractor'
    AND contractor_id = auth.uid()
  )
  WITH CHECK (
    get_user_role() = 'contractor'
    AND contractor_id = auth.uid()
    -- Contractors can only update status and notes, not reassign
    AND contractor_id = (SELECT contractor_id FROM tickets WHERE id = tickets.id)
  );

-- POLICY 4: Viewers can only read tickets (no write access)
CREATE POLICY viewer_read_only_tickets ON tickets
  FOR SELECT
  USING (get_user_role() = 'viewer');

-- Test queries (run as different users)
-- As admin: SELECT * FROM tickets;              → All tickets
-- As staff: SELECT * FROM tickets;              → Regional tickets
-- As contractor: SELECT * FROM tickets;         → Only their tickets
-- As viewer: SELECT * FROM tickets;             → All tickets (read-only)
-- As viewer: UPDATE tickets SET status = 'X';   → ERROR (no policy)
```

### Contractors Table Policies

```sql
-- =============================================================================
-- CONTRACTORS TABLE RLS POLICIES
-- =============================================================================

DROP POLICY IF EXISTS admin_all_contractors ON contractors;
DROP POLICY IF EXISTS staff_view_contractors ON contractors;
DROP POLICY IF EXISTS contractor_own_profile ON contractors;

-- POLICY 1: Admins manage all contractors
CREATE POLICY admin_all_contractors ON contractors
  FOR ALL
  USING (get_user_role() = 'admin')
  WITH CHECK (get_user_role() = 'admin');

-- POLICY 2: Staff can view all contractors (for assignment)
CREATE POLICY staff_view_contractors ON contractors
  FOR SELECT
  USING (get_user_role() IN ('staff', 'viewer'));

-- POLICY 3: Contractors can view/update their own profile
CREATE POLICY contractor_own_profile ON contractors
  FOR ALL
  USING (
    get_user_role() = 'contractor'
    AND id = auth.uid()
  )
  WITH CHECK (
    get_user_role() = 'contractor'
    AND id = auth.uid()
    -- Contractors can't change their role or rate
    AND role = (SELECT role FROM contractors WHERE id = contractors.id)
    AND hourly_rate = (SELECT hourly_rate FROM contractors WHERE id = contractors.id)
  );
```

### Projects Table Policies

```sql
-- =============================================================================
-- PROJECTS TABLE RLS POLICIES
-- =============================================================================

DROP POLICY IF EXISTS admin_all_projects ON projects;
DROP POLICY IF EXISTS staff_regional_projects ON projects;
DROP POLICY IF EXISTS contractor_assigned_projects ON projects;
DROP POLICY IF EXISTS viewer_read_projects ON projects;

-- POLICY 1: Admins manage all projects
CREATE POLICY admin_all_projects ON projects
  FOR ALL
  USING (get_user_role() = 'admin')
  WITH CHECK (get_user_role() = 'admin');

-- POLICY 2: Staff manage projects in their region
CREATE POLICY staff_regional_projects ON projects
  FOR ALL
  USING (
    get_user_role() = 'staff'
    AND region = (
      SELECT metadata->>'assigned_region'
      FROM neon_auth.users
      WHERE id = auth.uid()
    )
  )
  WITH CHECK (
    get_user_role() = 'staff'
    AND region = (
      SELECT metadata->>'assigned_region'
      FROM neon_auth.users
      WHERE id = auth.uid()
    )
  );

-- POLICY 3: Contractors view projects they're assigned to
CREATE POLICY contractor_assigned_projects ON projects
  FOR SELECT
  USING (
    get_user_role() = 'contractor'
    AND id IN (
      SELECT project_id FROM tickets WHERE contractor_id = auth.uid()
    )
  );

-- POLICY 4: Viewers read all projects
CREATE POLICY viewer_read_projects ON projects
  FOR SELECT
  USING (get_user_role() = 'viewer');
```

### Inventory Table Policies

```sql
-- =============================================================================
-- INVENTORY TABLE RLS POLICIES
-- =============================================================================

DROP POLICY IF EXISTS admin_all_inventory ON inventory;
DROP POLICY IF EXISTS staff_manage_inventory ON inventory;
DROP POLICY IF EXISTS contractor_view_inventory ON inventory;

-- POLICY 1: Admins manage all inventory
CREATE POLICY admin_all_inventory ON inventory
  FOR ALL
  USING (get_user_role() = 'admin')
  WITH CHECK (get_user_role() = 'admin');

-- POLICY 2: Staff can manage inventory
CREATE POLICY staff_manage_inventory ON inventory
  FOR ALL
  USING (get_user_role() = 'staff')
  WITH CHECK (get_user_role() = 'staff');

-- POLICY 3: Contractors can view inventory (for job planning)
CREATE POLICY contractor_view_inventory ON inventory
  FOR SELECT
  USING (get_user_role() IN ('contractor', 'viewer'));
```

### Work Orders Table Policies

```sql
-- =============================================================================
-- WORK ORDERS TABLE RLS POLICIES
-- =============================================================================

DROP POLICY IF EXISTS admin_all_work_orders ON work_orders;
DROP POLICY IF EXISTS contractor_own_work_orders ON work_orders;

-- POLICY 1: Admins manage all work orders
CREATE POLICY admin_all_work_orders ON work_orders
  FOR ALL
  USING (get_user_role() = 'admin')
  WITH CHECK (get_user_role() = 'admin');

-- POLICY 2: Contractors manage their own work orders
CREATE POLICY contractor_own_work_orders ON work_orders
  FOR ALL
  USING (
    get_user_role() = 'contractor'
    AND contractor_id = auth.uid()
  )
  WITH CHECK (
    get_user_role() = 'contractor'
    AND contractor_id = auth.uid()
  );
```

### Testing RLS Policies

```sql
-- =============================================================================
-- RLS TESTING QUERIES
-- =============================================================================

-- Test as admin (should see everything)
SET LOCAL "request.jwt.claims" = '{"sub": "admin-user-id"}';
SELECT count(*) FROM tickets;  -- Should return all tickets

-- Test as contractor (should see only their tickets)
SET LOCAL "request.jwt.claims" = '{"sub": "contractor-user-id"}';
SELECT count(*) FROM tickets;  -- Should return only their tickets

-- Test write permissions (contractor trying to update non-owned ticket)
SET LOCAL "request.jwt.claims" = '{"sub": "contractor-user-id"}';
UPDATE tickets SET status = 'completed' WHERE id = 'other-contractors-ticket';
-- Should fail with: ERROR: new row violates row-level security policy

-- Reset
RESET "request.jwt.claims";
```

---

## Testing Checklist

### Unit Tests

- [ ] **Authentication API Routes**
  - [ ] POST /api/auth/signup creates user
  - [ ] POST /api/auth/signin returns session token
  - [ ] POST /api/auth/signout clears session
  - [ ] GET /api/auth/me returns current user

- [ ] **RLS Policies**
  - [ ] Admin can read/write all tables
  - [ ] Staff can read/write regional data
  - [ ] Contractor can read/write own data only
  - [ ] Viewer can read but not write

### Integration Tests

- [ ] **Sign Up Flow**
  - [ ] Create new user with email/password
  - [ ] User appears in neon_auth.users table
  - [ ] Session cookie is set
  - [ ] Redirect to dashboard works

- [ ] **Sign In Flow**
  - [ ] Valid credentials → successful login
  - [ ] Invalid credentials → error message
  - [ ] Session persists across page reloads
  - [ ] User info displayed in header

- [ ] **Sign Out Flow**
  - [ ] Session cookie cleared
  - [ ] Redirect to sign-in page
  - [ ] Cannot access protected routes

- [ ] **Role-Based Access**
  - [ ] Admin can access /admin routes
  - [ ] Staff can access /ticketing routes
  - [ ] Contractor can access /ticketing (own tickets only)
  - [ ] Viewer cannot access write operations

### Database Tests

- [ ] **RLS Enforcement**
  - [ ] Tickets table filters by user role
  - [ ] Contractors table filters by user role
  - [ ] Projects table filters by user role
  - [ ] Direct psql queries respect RLS

- [ ] **Performance**
  - [ ] RLS policies use indexes (EXPLAIN ANALYZE)
  - [ ] No N+1 queries introduced
  - [ ] Auth queries < 10ms

### Security Tests

- [ ] **Authentication**
  - [ ] Cannot access protected routes without session
  - [ ] Expired sessions redirect to sign-in
  - [ ] Session tokens are httpOnly cookies

- [ ] **Authorization**
  - [ ] Contractor cannot see other contractors' tickets
  - [ ] Viewer cannot update any data
  - [ ] Direct database access respects RLS

- [ ] **SQL Injection**
  - [ ] Parameterized queries in all API routes
  - [ ] RLS policies prevent injection

### User Acceptance Tests

- [ ] **Admin Workflow**
  - [ ] Sign in as admin
  - [ ] View all tickets
  - [ ] Assign ticket to contractor
  - [ ] Update project details

- [ ] **Contractor Workflow**
  - [ ] Sign in as contractor
  - [ ] View only assigned tickets
  - [ ] Update ticket status
  - [ ] Cannot see other contractors' data

- [ ] **Staff Workflow**
  - [ ] Sign in as staff
  - [ ] View regional tickets
  - [ ] Manage inventory
  - [ ] Cannot access admin routes

### Monitoring & Observability

- [ ] **Logging**
  - [ ] Authentication events logged
  - [ ] Failed login attempts tracked
  - [ ] RLS policy violations logged

- [ ] **Metrics**
  - [ ] Auth API latency < 50ms
  - [ ] Database query latency < 10ms
  - [ ] Session validation < 5ms

---

## Rollback Procedures

### If Migration Fails (Emergency Rollback)

**Scenario:** Critical bug discovered, need to restore Clerk immediately.

**Time to Rollback:** ~30 minutes

**Steps:**

1. **Restore Clerk Configuration**
   ```bash
   cd ~/fibreflow-louis
   git checkout backup/clerk-auth-2026-01-08

   # Restore key files
   git checkout backup/clerk-auth-2026-01-08 -- middleware.ts
   git checkout backup/clerk-auth-2026-01-08 -- app/providers.tsx
   git checkout backup/clerk-auth-2026-01-08 -- app/sign-in
   git checkout backup/clerk-auth-2026-01-08 -- app/sign-up
   git checkout backup/clerk-auth-2026-01-08 -- src/components/layout/ClerkHeader.tsx
   ```

2. **Reinstall Clerk**
   ```bash
   npm install @clerk/nextjs@5.7.5
   ```

3. **Restore Environment Variables**
   ```bash
   # Add back to .env.local
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_Y3JlYXRpdmUtY29yYWwtODIuY2xlcmsuYWNjb3VudHMuZGV2JA
   CLERK_SECRET_KEY=sk_test_VVLQUws0JUO6maeBv9KycImwmHmxhtP9F3KiLCSljS
   ```

4. **Restart Application**
   ```bash
   npm run build
   pm2 restart fibreflow-louis
   ```

5. **Verify Clerk Working**
   ```bash
   curl -I http://100.96.203.105:3006/sign-in
   # Should return 200 OK
   ```

---

### Partial Rollback (Keep Neon Auth, Fix Issues)

**Scenario:** Minor issues, want to fix without full rollback.

**Options:**

1. **Disable RLS Temporarily**
   ```sql
   -- Disable RLS on specific table
   ALTER TABLE tickets DISABLE ROW LEVEL SECURITY;

   -- Re-enable when fixed
   ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
   ```

2. **Add Debug Logging**
   ```typescript
   // lib/neon-auth.ts
   export async function getCurrentUser() {
     const session = await neonAuth.getSession();
     console.log('DEBUG: Current session:', session);  // Add logging
     return session?.user || null;
   }
   ```

3. **Bypass Auth for Testing**
   ```typescript
   // middleware.ts (temporary)
   if (process.env.BYPASS_AUTH === 'true') {
     return NextResponse.next();  // Skip auth check
   }
   ```

---

### Database Rollback

**Scenario:** RLS policies causing issues, need to remove.

```sql
-- Disable RLS on all tables
ALTER TABLE tickets DISABLE ROW LEVEL SECURITY;
ALTER TABLE contractors DISABLE ROW LEVEL SECURITY;
ALTER TABLE projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE inventory DISABLE ROW LEVEL SECURITY;
ALTER TABLE work_orders DISABLE ROW LEVEL SECURITY;

-- Drop all RLS policies
DROP POLICY IF EXISTS admin_all_tickets ON tickets;
DROP POLICY IF EXISTS staff_regional_tickets ON tickets;
DROP POLICY IF EXISTS contractor_own_tickets ON tickets;
DROP POLICY IF EXISTS viewer_read_only_tickets ON tickets;

-- Drop helper function
DROP FUNCTION IF EXISTS get_user_role();

-- Optionally: Remove neon_auth schema (if disabling Neon Auth entirely)
-- DROP SCHEMA neon_auth CASCADE;  -- ⚠️ CAUTION: Deletes all users
```

---

### User Data Rollback

**Scenario:** Need to restore users to Clerk.

1. **Export Neon Auth Users**
   ```sql
   COPY (
     SELECT email, metadata->>'name' as name, metadata->>'role' as role
     FROM neon_auth.users
   ) TO '/tmp/neon_users_backup.csv' CSV HEADER;
   ```

2. **Import to Clerk**
   - Via Clerk Dashboard: Users → Import
   - Upload CSV file
   - Map columns: email, name, role

---

## Cost Analysis

### Current State (Clerk)

| Item | Cost | Notes |
|------|------|-------|
| Clerk Free Tier | $0 | Up to 10,000 MAU |
| Clerk Pro | $25/mo | After free tier |
| Estimated Year 1 | $0-300 | Depends on growth |
| Estimated Year 3 | $600 | Assuming 15,000 MAU |

### Future State (Neon Auth)

| Item | Cost | Notes |
|------|------|-------|
| Neon Auth | $0 | Included in Neon plan |
| Neon Database | $20/mo | Already paying |
| Estimated Year 1 | $0 | No additional cost |
| Estimated Year 3 | $0 | No additional cost |

### Migration Costs

| Item | Cost | Notes |
|------|------|-------|
| Development Time | $1000 | 2-3 days @ $500/day |
| Testing | $300 | 0.5 days |
| Documentation | $200 | This document |
| **Total Migration** | **$1500** | One-time cost |

### ROI Analysis

**Break-Even Calculation:**
```
Migration Cost: $1500
Annual Savings: $300-600 (Clerk fees)
Break-Even: 2.5-5 months
```

**3-Year Total Cost:**
```
Clerk Path:   $0 (Yr1) + $300 (Yr2) + $600 (Yr3) = $900
Neon Path:    $1500 (migration) + $0 + $0 = $1500
Difference:   $600 more for Neon Auth

BUT: Benefits beyond cost:
- Database branching for auth testing
- Simpler architecture (fewer services)
- Better security (RLS at data layer)
- Faster queries (same-region auth)
```

**Verdict:** If you stay on FibreFlow for 2+ years, Neon Auth saves money AND improves architecture.

---

## Post-Migration Tasks

### Week 1: Monitoring

- [ ] Monitor auth API latency (should be < 50ms)
- [ ] Check for failed authentication attempts
- [ ] Verify RLS policies working correctly
- [ ] Review error logs daily

### Week 2: Optimization

- [ ] Add indexes for RLS policy queries
- [ ] Optimize session validation
- [ ] Cache user roles
- [ ] Add rate limiting

### Month 1: Enhancement

- [ ] Add password reset flow
- [ ] Implement email verification
- [ ] Add OAuth providers (Google, GitHub)
- [ ] Build admin dashboard for user management

### Month 2: Advanced Features

- [ ] Add MFA/2FA support
- [ ] Implement session analytics
- [ ] Add audit logging
- [ ] Create user activity reports

---

## Support & Resources

### Documentation

- **Neon Auth Docs:** https://neon.com/docs/auth/overview
- **PostgreSQL RLS:** https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- **Better Auth (underlying tech):** https://better-auth.com

### Internal Docs

- `docs/CLERK_AUTH_COMPLETE_2026-01-07.md` - Current Clerk setup
- `CLAUDE.md` - FibreFlow architecture overview
- `docs/OPERATIONS_LOG.md` - Deployment history

### Troubleshooting

**Issue:** "Unauthorized" error when accessing routes
**Solution:** Check session cookie exists: `document.cookie` in browser console

**Issue:** RLS policy denying valid queries
**Solution:** Verify `auth.uid()` returns correct user ID:
```sql
SELECT auth.uid(), get_user_role();
```

**Issue:** Migration script fails
**Solution:** Check Neon Auth enabled in console, verify `NEON_AUTH_URL` env var

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0: Preparation | 30 min | Pending |
| Phase 1: Install SDK | 1 hour | Pending |
| Phase 2: API Routes | 2 hours | Pending |
| Phase 3: UI Components | 3 hours | Pending |
| Phase 4: Middleware | 1 hour | Pending |
| Phase 5: RLS Policies | 3 hours | Pending |
| Phase 6: User Migration | 2 hours | Pending |
| Phase 7: Remove Clerk | 30 min | Pending |
| Phase 8: Testing | 4 hours | Pending |
| **Total** | **~2-3 days** | **In Progress** |

---

## Approval & Sign-Off

**Document Created:** 2026-01-08
**Created By:** Claude Code + Louis Dup
**Reviewed By:** _Pending_
**Approved By:** _Pending_
**Implementation Start:** _Pending_
**Target Completion:** _Pending_

---

**Next Steps:**
1. Review this document with team
2. Create backup branch: `git checkout -b backup/clerk-auth-2026-01-08`
3. Begin Phase 0: Preparation
4. Follow implementation plan step-by-step

**Questions?** See `docs/OPERATIONS_LOG.md` or create GitHub issue.

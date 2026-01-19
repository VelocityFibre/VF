# ✅ FibreFlow Permission System - Complete

## Overview

A **3-tier permission system** that provides:
1. **Default role permissions** (admin, staff, contractor, viewer)
2. **User-specific overrides** (add/remove permissions per user)
3. **Feature flags** (enable beta features for specific users)

## System Architecture

```
User Login (Clerk)
    ↓
Role from Metadata (admin/staff/contractor)
    ↓
Base Permissions Loaded
    ↓
User Overrides Applied (+/- permissions)
    ↓
Final Permission Set
    ↓
UI/API Access Control
```

## Files Created

1. **`lib/auth/permissions.config.ts`**
   - Default role definitions
   - User-specific overrides
   - Feature flags
   - Permission groups

2. **`lib/auth/permissions.ts`**
   - PermissionChecker class
   - Server-side checking functions
   - API route protection helpers

3. **`hooks/usePermissions.tsx`**
   - React hook for client-side checks
   - PermissionGuard component
   - FeatureFlag component

## Default Roles

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **admin** | Full system access | All CRUD, user management, billing |
| **staff** | Standard employee | Create/edit tickets, view reports |
| **contractor** | External worker | Own tickets only, read-only |
| **viewer** | Read-only | View all, edit nothing |
| **manager** | Staff + extras | Inherits staff + contractor mgmt |
| **finance** | Financial access | Billing, reports, audit logs |

## How to Use

### In UI Components

```tsx
import { usePermissions } from '@/hooks/usePermissions';

function MyComponent() {
  const { can, role } = usePermissions();

  return (
    <>
      {can('ticketing', 'create') && (
        <button>Create Ticket</button>
      )}

      {can('billing', 'update') && (
        <BillingSettings />
      )}
    </>
  );
}
```

### In API Routes

```typescript
import { checkPermission } from '@/lib/auth/permissions';

export async function POST(req: Request) {
  if (!await checkPermission('contractors', 'create')) {
    return new Response('Forbidden', { status: 403 });
  }
  // Create contractor...
}
```

## User-Specific Overrides

To give specific users custom permissions:

```typescript
// In permissions.config.ts
USER_OVERRIDES = [
  {
    userId: "user_xxx", // Clerk user ID
    email: "john@company.com",
    addPermissions: [
      { resource: "reports", actions: ["export"] }
    ]
  }
]
```

## Examples of Permissions

### Admin Can:
- ✅ Create/delete users
- ✅ Manage billing
- ✅ Access all features
- ✅ View audit logs

### Staff Can:
- ✅ Create tickets
- ✅ Update contractors
- ✅ Export reports
- ❌ Delete users
- ❌ Change billing

### Contractor Can:
- ✅ View own tickets
- ✅ Update own tickets
- ❌ Create tickets
- ❌ View other's tickets
- ❌ Manage users

## Testing Permissions

1. **Sign in with different roles:**
   ```
   Admin: Full access to everything
   Staff: Can't access billing or user management
   Contractor: Can only see own data
   ```

2. **Test user overrides:**
   - Add your Clerk user ID to USER_OVERRIDES
   - Give yourself extra permissions
   - Sign out/in to refresh

3. **Check feature flags:**
   - Add user to betaFeatures array
   - Beta UI elements will appear

## Adding New Permissions

1. **Add resource to roles** in `permissions.config.ts`:
   ```typescript
   admin: {
     permissions: [
       { resource: "newFeature", actions: ["create", "read"] }
     ]
   }
   ```

2. **Use in components:**
   ```tsx
   {can('newFeature', 'create') && <NewFeatureButton />}
   ```

3. **Protect API routes:**
   ```typescript
   if (!await checkPermission('newFeature', 'create')) {
     return new Response('Forbidden', { status: 403 });
   }
   ```

## Security Best Practices

1. **Always validate server-side** - Client checks are UI-only
2. **Log permission denials** - For security audit
3. **Use least privilege** - Start with minimal permissions
4. **Review user overrides** - Regularly audit special permissions
5. **Test thoroughly** - Try to bypass permissions

## Quick Reference

| Check Type | Client-Side | Server-Side |
|------------|-------------|-------------|
| Single permission | `can(resource, action)` | `checkPermission(resource, action)` |
| Multiple permissions | `canAll([...])` | Manual check |
| Feature flag | `hasFeature('beta')` | Check FEATURE_FLAGS |
| Role check | `role === 'admin'` | Check user metadata |
| Permission group | `isInGroup('managers')` | Check PERMISSION_GROUPS |

## Next Steps

1. **Add your team members** to USER_OVERRIDES
2. **Configure feature flags** for beta testing
3. **Create admin UI** for managing permissions
4. **Add audit logging** for permission changes
5. **Set up alerts** for unauthorized access attempts

---

The permission system is now fully integrated with Clerk authentication, providing enterprise-grade access control with the flexibility to handle any edge case through user-specific overrides.
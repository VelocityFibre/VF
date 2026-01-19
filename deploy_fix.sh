#!/bin/bash

echo "Deploying Clerk authentication redirect fix to FibreFlow..."

# Create the fixed page.tsx file
cat > /tmp/fixed_page.tsx << 'EOF'
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';

export default function HomePage() {
  const router = useRouter();
  const { isLoaded, isSignedIn, user } = useUser();

  useEffect(() => {
    if (!isLoaded) return;

    if (isSignedIn) {
      // User is signed in, redirect to ticketing
      router.push('/ticketing');
    } else {
      // User is not signed in, redirect to sign-in
      router.push('/sign-in');
    }
  }, [isLoaded, isSignedIn, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">FibreFlow Next.js</h1>
        <p className="text-gray-600 mb-4">Enterprise fiber network project management</p>
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm text-gray-500">
            {!isLoaded
              ? "Loading authentication..."
              : isSignedIn
                ? `Welcome back, ${user?.firstName || 'User'}! Redirecting to dashboard...`
                : "Redirecting to sign in..."}
          </p>
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
        </div>
      </div>
    </div>
  );
}
EOF

echo "✅ Created fixed page.tsx"
echo ""
echo "To complete deployment, SSH to the server and run:"
echo "  ssh velo@100.96.203.105  # password: 2025"
echo "  cp /home/velo/fibreflow-louis/app/page.tsx /home/velo/fibreflow-louis/app/page.tsx.backup"
echo "  cp /tmp/fixed_page.tsx /home/velo/fibreflow-louis/app/page.tsx"
echo "  cd /home/velo/fibreflow-louis"
echo "  npm run build"
echo "  pm2 restart fibreflow-louis"
echo ""
echo "Or run this one-liner after SSH:"
echo "  cp ~/fibreflow-louis/app/page.tsx ~/fibreflow-louis/app/page.tsx.backup && cp /tmp/fixed_page.tsx ~/fibreflow-louis/app/page.tsx && cd ~/fibreflow-louis && npm run build && pm2 restart fibreflow-louis"
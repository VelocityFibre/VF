# Development Environment Rules

## Local Development Setup

### Port Allocation
- **Hein**: Port 3005 (primary development)
- **Louis**: Port 3006 (staging)
- **Production**: Port 3000

### Starting Development Server
```bash
# Hein's development instance
cd /home/hein/Agents/claude/VF-modular
npm install  # First time only
PORT=3005 npm run dev

# Access at: http://localhost:3005
```

### Database Configuration
```bash
# Development can use either:

# Option 1: Local SQLite (fastest for dev)
DATABASE_URL=file:./dev.db

# Option 2: Neon staging branch (real PostgreSQL)
DATABASE_URL=$NEON_STAGING_URL

# Never use production database for development
```

### Environment Variables
```bash
# Copy example and configure
cp .env.example .env

# Essential variables for development:
NODE_ENV=development
PORT=3005
DATABASE_URL=file:./dev.db
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

### Development Features
- ✅ Hot reload enabled
- ✅ Source maps available
- ✅ Verbose error messages
- ✅ React DevTools enabled
- ✅ Mock services available
- ✅ No rate limiting

### Git Workflow for Development
```bash
# 1. Start from develop branch
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and test locally
npm run dev  # Port 3005
npm test

# 4. Commit with conventional commits
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: resolve issue"
# or
git commit -m "docs: update documentation"

# 5. Push and create PR
git push origin feature/your-feature-name
gh pr create --base develop
```

### Testing in Development
```bash
# Run unit tests
npm test

# Run specific test file
npm test -- workflow.test.ts

# Run with coverage
npm test -- --coverage

# Python tests
./venv/bin/pytest tests/ -v

# Watch mode for TDD
npm test -- --watch
```

### Mock Services for Development
```bash
# Mock WhatsApp (instead of real service)
export MOCK_WHATSAPP=true

# Mock email service
export MOCK_EMAIL=true

# Use test Stripe keys
export STRIPE_SECRET_KEY=sk_test_...
```

### Debugging
```bash
# Enable debug logs
DEBUG=* npm run dev

# Node inspector
node --inspect npm run dev

# Check port usage
lsof -i :3005

# Kill process on port if stuck
kill -9 $(lsof -t -i:3005)
```

### Common Development Tasks
```bash
# Reset local database
npm run db:reset
npm run db:seed

# Generate TypeScript types
npm run generate:types

# Run linter
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

### Development Rules
1. **Never commit .env files** (use .env.example)
2. **Always test locally first** before pushing
3. **Use feature branches** (never commit to main/develop directly)
4. **Run tests before pushing** (automated CI will also run them)
5. **Update documentation** when adding features
6. **Use conventional commits** for clear history

### Connecting to Services
- **Local app**: http://localhost:3005
- **Local API**: http://localhost:3005/api
- **Convex dashboard**: https://dashboard.convex.dev
- **Neon dashboard**: https://console.neon.tech

### VS Code Settings
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

### Troubleshooting Development
1. **Port already in use**: Kill process or use different port
2. **Module not found**: Run `npm install`
3. **Database errors**: Check DATABASE_URL in .env
4. **TypeScript errors**: Run `npm run type-check`
5. **Test failures**: Check if database needs reset
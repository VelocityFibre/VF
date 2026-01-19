# Module: Knowledge Base

**Type**: agent
**Location**: `agents/knowledge_base/`
**Deployment**: docs.fibreflow.app (web) + api.docs.fibreflow.app (API)
**Isolation**: mostly_isolated
**Developers**: louis
**Last Updated**: 2026-01-12

---

## Overview

AI-powered knowledge base system that stores company documentation, enables natural language search, and provides context to AI agents. Uses vector embeddings (Qdrant) for semantic search and Neon PostgreSQL for document storage. Git-backed with auto-deployment on push.

**Critical Context**: Mostly isolated - reads from Neon (contractor/project data for context enrichment) but doesn't write to other modules' tables.

## Dependencies

### External Dependencies
- **Qdrant**: Vector database for embeddings (port 6333, localhost)
- **Neon PostgreSQL**: Document storage, metadata
- **Git Repository**: `~/velocity-fibre-knowledge/` on VF Server
  - Auto-sync on push to main branch
  - Static site generation via MkDocs or custom generator

### Internal Dependencies
- **Neon Database** (read-only): Queries contractor/project tables for context enrichment
  - Example: "Show contractors in Gauteng" → queries neon contractors table
  - No writes to other modules' tables

## Database Schema

### Tables Owned
| Table | Description | Key Columns |
|-------|-------------|-------------|
| kb_documents | Markdown documents | id, title, content, path, category, created_at, updated_at |
| kb_embeddings | Vector embeddings | id, document_id, embedding_vector, chunk_index |
| kb_search_log | Search analytics | id, query, results_count, clicked_result, timestamp |

**Qdrant Collections**:
- `fibreflow_docs` - Document embeddings (768-dim vectors)
- `contractor_knowledge` - Contractor-specific FAQs

### Tables Referenced (Read-Only)
| Table | Owner | How Used |
|-------|-------|----------|
| contractors | core | Context for queries like "contractors in Gauteng" |
| projects | core | Project-related documentation context |

## API Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| /search | POST | Semantic search | No (public docs) |
| /documents | GET | List all documents | No |
| /documents/:id | GET | Get specific document | No |
| /embeddings/generate | POST | Generate embeddings | Yes (internal) |
| /health | GET | Health check | No |

**Base URLs**:
- Web: https://docs.fibreflow.app
- API: http://api.docs.fibreflow.app

## Services/Methods

### Core Services
- **DocumentIndexer** - Indexes markdown files from git repo
  - Triggered on git push (webhook or cron)
  - Generates embeddings via OpenAI/local model
  - Stores in Qdrant + Neon

- **SemanticSearch** - Natural language search
  - Converts query to embedding
  - Finds similar vectors in Qdrant
  - Ranks results by relevance
  - Returns document snippets

- **ContextEnricher** - Augments search with live data
  - Example: "contractors" query → fetches from Neon contractors table
  - Merges static docs with dynamic data

## File Structure

```
agents/knowledge_base/
├── README.md
├── indexer/
│   ├── document_indexer.py       # Git → Database sync
│   └── embedding_generator.py    # Create vector embeddings
├── search/
│   ├── semantic_search.py        # Qdrant search
│   └── context_enricher.py       # Add live data to results
├── api/
│   └── routes.py                # FastAPI endpoints
└── tests/
    ├── test_indexer.py
    └── test_search.py

~/velocity-fibre-knowledge/      # Git repo (VF Server)
├── docs/
│   ├── getting-started.md
│   ├── contractors/
│   ├── projects/
│   └── operations/
├── mkdocs.yml                  # Static site config
└── KNOWLEDGE_BASE_SYSTEM.md    # Setup guide
```

## Configuration

### Environment Variables
```bash
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=xxx  # If authentication enabled

# Neon (read-only for context enrichment)
NEON_DATABASE_URL=postgresql://...

# Embeddings
OPENAI_API_KEY=sk-...  # If using OpenAI embeddings
# OR use local model (no API key needed)

# Git Sync
KB_GIT_REPO=/home/velo/velocity-fibre-knowledge
KB_AUTO_SYNC=true
KB_SYNC_INTERVAL=300  # 5 minutes
```

### Config Files
- `~/velocity-fibre-knowledge/mkdocs.yml` - Static site configuration
- `~/velocity-fibre-knowledge/KNOWLEDGE_BASE_SYSTEM.md` - Complete setup guide
- `agents/knowledge_base/config.yaml` - Agent configuration

## Common Operations

### Development
```bash
# Run indexer locally
cd agents/knowledge_base
./venv/bin/python indexer/document_indexer.py --repo ~/velocity-fibre-knowledge

# Test search
./venv/bin/python search/semantic_search.py --query "How to create contractor"

# Start API server
./venv/bin/python api/routes.py --port 8090
```

### Deployment
```bash
# Deploy to VF Server
ssh velo@100.96.203.105
cd ~/velocity-fibre-knowledge
git pull origin main

# Re-index documents
cd /path/to/knowledge_base_agent
./venv/bin/python indexer/document_indexer.py

# Restart API
pm2 restart kb-api
```

### Manual Operations
```bash
# Rebuild entire index
./venv/bin/python indexer/document_indexer.py --rebuild

# Check Qdrant collection
curl http://localhost:6333/collections/fibreflow_docs

# Query database
psql $NEON_DATABASE_URL -c "SELECT COUNT(*) FROM kb_documents;"
```

## Known Gotchas

### Issue 1: Search Returns Outdated Results
**Problem**: Documentation updated in Git but search shows old content
**Root Cause**: Index not synced after Git push
**Solution**:
```bash
# Manual re-index
ssh velo@100.96.203.105
cd /path/to/knowledge_base_agent
./venv/bin/python indexer/document_indexer.py --incremental

# Check last sync time
psql $NEON_DATABASE_URL -c "SELECT MAX(updated_at) FROM kb_documents;"
```
**Prevention**: Set up auto-sync cron job or git webhook

### Issue 2: Qdrant Connection Refused
**Problem**: Search fails with "Connection refused to localhost:6333"
**Root Cause**: Qdrant service not running
**Solution**:
```bash
# Check Qdrant status
curl http://localhost:6333/health

# Start Qdrant (Docker)
docker run -d -p 6333:6333 qdrant/qdrant

# Or systemd
sudo systemctl start qdrant
```

### Issue 3: Context Enrichment Slow (>5 seconds)
**Problem**: Searches that fetch live contractor/project data are slow
**Root Cause**: Neon database query not optimized or missing indexes
**Solution**:
```sql
-- Add index on commonly queried columns
CREATE INDEX idx_contractors_region ON contractors(region);
CREATE INDEX idx_projects_status ON projects(status);

-- Or cache frequent queries in Redis
```

### Issue 4: Embeddings Generation Fails (Rate Limit)
**Problem**: OpenAI API rate limit hit during bulk indexing
**Root Cause**: Indexing 100+ documents at once
**Solution**:
```bash
# Use local embedding model instead
# OR batch requests with delays
./venv/bin/python indexer/document_indexer.py --batch-size 10 --delay 1
```

## Testing Strategy

### Unit Tests
- Location: `tests/unit/knowledge_base/`
- Coverage requirement: 80%+
- Key areas:
  - Document parsing (markdown → structured data)
  - Embedding generation (mocked OpenAI API)
  - Vector search (mocked Qdrant responses)

### Integration Tests
- Location: `tests/integration/knowledge_base/`
- External dependencies: Test Qdrant collection, test Neon database
- Key scenarios:
  - Git repo → indexer → database → search (end-to-end)
  - Context enrichment (static docs + live Neon data)
  - Search ranking (relevance scores)

### E2E Tests
- Location: Manual or Playwright tests
- Tool: curl or web browser
- Critical user flows:
  1. Navigate to docs.fibreflow.app
  2. Search for "How to create contractor"
  3. Verify results include relevant documentation
  4. Click result, verify content loads
  5. (Advanced) Verify live contractor data mixed in

## Monitoring & Alerts

### Health Checks
- Endpoint: `http://api.docs.fibreflow.app/health`
- Expected response: `{"status": "ok", "qdrant": "connected", "neon": "connected"}`

### Key Metrics
- **Search latency**: Target <500ms (Qdrant query + Neon lookup)
- **Index freshness**: Docs synced within 5 minutes of Git push
- **Search success rate**: >90% (queries returning >0 results)
- **Qdrant collection size**: `curl http://localhost:6333/collections/fibreflow_docs | jq .result.points_count`

### Logs
- Location: PM2 logs or systemd journal
  - `pm2 logs kb-api`
  - `journalctl -u knowledge-base-indexer`
- Key log patterns:
  - `Indexed N documents` - Sync completed
  - `Search query: ...` - User searches
  - `ERROR: Qdrant timeout` - Vector DB issue
  - `ERROR: Neon connection failed` - Database issue

## Breaking Changes History

| Date | Change | Migration Required | Reference |
|------|--------|-------------------|-----------|
| 2024-XX-XX | Initial implementation | Yes - Create kb_* tables, Qdrant collection | N/A |
| 2025-XX-XX | Added context enrichment (read Neon contractors) | No - Read-only queries | N/A |

## Related Documentation

- [Knowledge Base System Guide](~/velocity-fibre-knowledge/KNOWLEDGE_BASE_SYSTEM.md)
- [Agent Harness (if built via harness)](harness/runs/knowledge_base_*/README.md)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

## Contact

**Primary Owner**: Louis
**Team**: FibreFlow AI/Knowledge
**Deployment**: VF Server (docs.fibreflow.app, api.docs.fibreflow.app)

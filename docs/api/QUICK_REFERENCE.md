# AI Database Agents - Quick Reference

**One-page cheat sheet for developers**

---

## 🚀 Quick Start (30 seconds)

```bash
# Activate environment
source venv/bin/activate

# Test Neon agent
python3 test_neon.py

# Use in code
python3
>>> from neon_agent import NeonAgent
>>> agent = NeonAgent()
>>> agent.chat("How many projects do we have?")
```

---

## 📁 Key Files

| What You Need | File |
|---------------|------|
| **Overview** | `PROJECT_SUMMARY.md` |
| **Neon docs** | `NEON_AGENT_GUIDE.md` |
| **UI integration** | `NEON_AGENT_UI_RECOMMENDATIONS.md` |
| **Quick test** | `test_neon.py` |
| **Advanced demo** | `test_neon_advanced.py` |

---

## 🔑 Environment Variables

```bash
# Required in .env file
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
NEON_DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

---

## 💬 Example Queries

### Data Exploration
```python
"What tables do we have?"
"Show me the structure of the projects table"
"How many rows in each table?"
```

### Business Queries
```python
"Show me active projects"
"List contractors with performance score > 80"
"Which projects are over budget?"
"Generate a project status report"
```

### Analysis
```python
"Compare Q3 vs Q4 project costs"
"Analyze contractor performance trends"
"Show BOQs pending approval"
```

---

## 🐍 Python Usage

### Basic Pattern
```python
from neon_agent import NeonAgent, load_env

# Setup
load_env()
agent = NeonAgent()

# Query
response = agent.chat("Your question here")
print(response)

# Follow-up (maintains context)
response = agent.chat("What about last month?")

# Reset when changing topic
agent.reset_conversation()
```

### With Context
```python
agent = NeonAgent()

response = agent.chat(
    "Show me project details",
    context={"project_id": "123"}
)
```

---

## 🔧 Available Tools

**Schema Discovery:**
- `list_tables()` - List all tables
- `describe_table(table_name)` - Show columns
- `get_table_stats(table_name)` - Row counts, size

**Data Operations:**
- `execute_select(query)` - Read data
- `execute_insert(query)` - Add data
- `execute_update(query)` - Modify data
- `execute_delete(query)` - Remove data

**Analysis:**
- `count_rows(table_name, where_clause)` - Count with filter

---

## 🌐 API Integration (Next.js)

### Backend API Route
```typescript
// /app/api/agent/chat/route.ts
export async function POST(req: NextRequest) {
  const { message } = await req.json();

  const response = await fetch('http://python-backend/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  return NextResponse.json(await response.json());
}
```

### Frontend Component
```typescript
// Component
const [response, setResponse] = useState('');

const query = async (message: string) => {
  const res = await fetch('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify({ message })
  });
  const data = await res.json();
  setResponse(data.response);
};
```

---

## 🐛 Troubleshooting

**Connection failed?**
```bash
# Test connection string directly
python3
>>> import psycopg2
>>> psycopg2.connect("your_connection_string")
```

**API key error?**
```bash
# Check .env file
cat .env | grep ANTHROPIC_API_KEY

# Verify at
# https://console.anthropic.com/account/keys
```

**Slow queries?**
```python
# Use faster model
agent = NeonAgent(model="claude-3-haiku-20240307")

# Limit results
agent.chat("Show me TOP 10 projects")
```

---

## 💰 Costs

**Per 1000 queries:**
- Haiku: $3-5/month
- Sonnet: $15-25/month

**Hosting:**
- Railway: $5-20/month

**Total:** ~$10-30/month for typical usage

---

## 📚 Documentation Map

```
PROJECT_SUMMARY.md              # Start here - overview
│
├── NEON_AGENT_GUIDE.md         # Complete technical guide
│   ├── Architecture
│   ├── API reference
│   ├── Examples
│   └── Troubleshooting
│
├── NEON_AGENT_UI_RECOMMENDATIONS.md  # UI integration
│   ├── UI patterns
│   ├── Code examples
│   ├── Deployment options
│   └── Implementation roadmap
│
└── QUICK_REFERENCE.md          # This file - quick lookup
```

---

## ⚡ Common Tasks

### Test Connection
```bash
python3 test_neon.py
```

### Run Demo
```bash
python3 demo_neon_agent.py
```

### Check Database Stats
```python
agent.chat("Give me statistics about all tables")
```

### Generate Report
```python
agent.chat("""
Generate a comprehensive report including:
- Total projects and status breakdown
- Top performing contractors
- BOQs pending approval
- Budget vs actual spending
""")
```

---

## 🎯 Best Practices

### ✅ Do
- Use Haiku for simple queries (fast & cheap)
- Reset conversation when changing topics
- Limit result sets ("TOP 10", "last 30 days")
- Add context for page-specific queries

### ❌ Don't
- Don't commit `.env` file
- Don't query large datasets without limits
- Don't use for real-time updates (cache instead)
- Don't share API keys

---

## 🔐 Security Checklist

- [ ] API keys in environment variables
- [ ] Rate limiting enabled
- [ ] User authentication required
- [ ] Audit logging enabled
- [ ] `.env` in `.gitignore`

---

## 📊 Your Database

**Type:** Fiber optic infrastructure deployment
**Tables:** 104 tables
**Key Data:**
- 2 projects
- 20 contractors
- 5 suppliers
- 1 BOQ
- 2 RFQs

---

## 🚀 Deploy to Production

**Recommended:**
1. Deploy Python backend to Railway
2. Add FastAPI wrapper
3. Create Next.js API routes
4. Implement UI (command palette + sidebar)
5. Add auth and rate limiting

**Timeline:** 6-8 weeks

---

## 📞 Need Help?

1. Check `NEON_AGENT_GUIDE.md` troubleshooting section
2. Run diagnostic tests
3. Review error logs
4. Check Anthropic console for API issues

---

**Tip:** Bookmark this page for quick reference during development!

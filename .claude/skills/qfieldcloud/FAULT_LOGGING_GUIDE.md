# QFieldCloud Fault Logging - Quick Guide

## 🎯 Two Systems, Two Triggers

### #logFault - Quick Logging (NEW ⚡)
**Cost**: 450 tokens (90% cheaper)
**Format**: JSON
**System**: `sub-skills/fault-logging/`

**Use for:**
- ✅ Quick fault tracking
- ✅ Automated monitoring
- ✅ Pattern analysis
- ✅ Auto-alerts (CRITICAL faults → WhatsApp)

**Examples:**
```
#logFault CRITICAL qgis-image "Docker image missing"
#logFault MAJOR workers "Only 4/8 workers running"
#logFault MINOR database "Slow queries"

Workers are down #logFault
```

**What you get:**
- Compact JSON entry
- Timestamp + severity + component
- Auto-alert if CRITICAL
- Searchable for patterns
- 450 tokens

---

### #logFaultDetail - Detailed Investigation (OLD 📋)
**Cost**: 4,000 tokens (comprehensive)
**Format**: Markdown
**System**: `INCIDENT_LOG.md`

**Use for:**
- ✅ Root cause analysis
- ✅ Multi-step investigations
- ✅ Lessons learned documentation
- ✅ Team reference material

**Examples:**
```
#logFaultDetail - Need to document Lew's token issue with full investigation
#logFaultDetail - CSRF problem requires detailed post-mortem
```

**What you get:**
- Detailed markdown entry
- Root causes identified
- Investigation findings
- Resolution steps
- Lessons learned
- Preventive measures
- 4,000 tokens

---

## 📊 Side-by-Side Comparison

| Feature | #logFault | #logFaultDetail |
|---------|-----------|-----------------|
| **Token Cost** | 450 | 4,000 |
| **Format** | JSON | Markdown |
| **Speed** | Fast | Thorough |
| **Use Case** | Quick tracking | Investigation |
| **Auto-alerts** | ✅ Yes (CRITICAL) | ❌ No |
| **Pattern analysis** | ✅ Easy | ❌ Manual |
| **Team docs** | Basic | Comprehensive |
| **Lessons learned** | ❌ No | ✅ Yes |
| **Root cause** | Simple description | Full analysis |

---

## 🎬 When to Use Which

### Use #logFault when:
- Monitoring detects an issue
- User reports a simple error
- You want to track patterns
- You need quick logging
- You want auto-alerts

**Example:**
```
"Juan says workers are failing #logFault MAJOR workers 4/8 running"
→ 450 tokens, logged, searchable, auto-alert if critical
```

### Use #logFaultDetail when:
- Complex multi-step investigation
- Need to document root causes
- Want lessons learned for team
- Creating reference material
- Post-mortem required

**Example:**
```
"Need to investigate Lew's token issue #logFaultDetail"
→ 4,000 tokens, full investigation, root cause, prevention steps
```

---

## 💡 Pro Tips

### Start with #logFault
For most issues, start with quick logging:
```
#logFault MAJOR workers "Only 4/8 running"
```

### Upgrade to #logFaultDetail later
If it becomes complex:
```
#logFaultDetail - Worker issue from earlier needs full investigation
```

### Pattern Recognition
After multiple `#logFault` entries, analyze:
```
search faults "workers"
analyze faults 30
```

---

## 📝 Complete Examples

### Example 1: Quick Issue
**Scenario**: Monitoring detects QGIS image missing

```
#logFault CRITICAL qgis-image "Docker image missing after restart"
```

**Result**:
- ✅ Logged in 450 tokens
- ✅ WhatsApp alert sent automatically
- ✅ Searchable for patterns
- ✅ Fast resolution

---

### Example 2: Complex Investigation
**Scenario**: User can't download projects, needs investigation

```
#logFaultDetail - Lew reporting download errors on multiple projects
```

**Result**:
- ✅ Full investigation documented (4,000 tokens)
- ✅ Root cause: Mobile app cached expired token
- ✅ Resolution steps documented
- ✅ Lessons learned captured
- ✅ Preventive measures listed
- ✅ Team reference material created

---

### Example 3: Workflow
**Start simple, upgrade if needed:**

1. Quick log: `#logFault MAJOR csrf "Users getting 403 errors"`
2. If pattern emerges: `search faults "csrf"`
3. If complex: `#logFaultDetail - CSRF issue recurring, needs investigation`

---

## 🔍 Finding Your Faults

### Quick System (#logFault)
```bash
cd .claude/skills/qfieldcloud/sub-skills/fault-logging/scripts

# View recent
./recent_faults.sh 10

# Search
./search_faults.sh "qgis"

# Analyze patterns
./analyze_faults.sh 30

# Generate report
./fault_report.sh 7
```

### Detailed System (#logFaultDetail)
```bash
# View incidents
cat .claude/skills/qfieldcloud/INCIDENT_LOG.md

# Search
grep "Lew" .claude/skills/qfieldcloud/INCIDENT_LOG.md
```

---

## 🚀 Quick Start

### First Fault?
```
#logFault INFO test "Testing the quick logging system"
```

### Need Detailed Investigation?
```
#logFaultDetail - Testing detailed incident documentation
```

### Check Your Logs
```
fault history
recent faults
search faults "test"
```

---

## 📞 Summary

**Remember:**
- `#logFault` = Fast, cheap (450 tokens), JSON, auto-alerts
- `#logFaultDetail` = Thorough, expensive (4,000 tokens), markdown, full docs

**Default to `#logFault`** for 90% of cases.
**Upgrade to `#logFaultDetail`** when you need comprehensive team documentation.

**Both systems work together:**
- Quick logging tracks patterns
- Detailed investigations explain complex issues
- Team has both breadth (many faults) and depth (key investigations)

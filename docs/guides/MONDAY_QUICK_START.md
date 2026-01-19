# Monday Quick Start - Agent Harness

**Status**: ✅ Harness integrated, ready to test
**Date**: Resume Monday, December 9, 2025

---

## 1-Minute Status

✅ Built autonomous agent building system (3,800 lines)
✅ Complete documentation in CLAUDE.md + harness/README.md
✅ Test agent spec ready: `harness/specs/weather_test_spec.md`
⚠️ Runner is demo - use Anthropic's harness for production

---

## What to Do Monday (Pick One)

### A. Quick Test (5 min)
```bash
cd /home/louisdup/Agents/claude
source venv/bin/activate
./harness/runner.py --agent weather_test --model haiku
```
**Proves**: Environment validation works

---

### B. Real Test (1 hour setup + 4-6 hours run)
```bash
# Clone Anthropic's harness
git clone https://github.com/anthropics/anthropic-harness ~/anthropic-harness
cd ~/anthropic-harness
npm install

# Copy FibreFlow prompts
cp ~/Agents/claude/harness/prompts/* ./prompts/
cp ~/Agents/claude/harness/config.json ./

# Run with weather test
export CLAUDE_TOKEN="your-token"  # or ANTHROPIC_API_KEY
python run_autonomous_agent.py \
  --app-spec ~/Agents/claude/harness/specs/weather_test_spec.md \
  --project-dir ~/Agents/claude/agents/weather_test \
  --model haiku

# Check results (4-6 hours later)
cd ~/Agents/claude
./venv/bin/pytest tests/test_weather_test.py -v
./venv/bin/python3 demo_weather_test.py
```
**Proves**: Harness builds complete agents
**Cost**: $3-5

---

### C. Build Real Agent (30 min spec + overnight)

**Useful agents for FibreFlow**:
- SharePoint (spec already done: `harness/specs/sharepoint_spec.md`)
- Email (Gmail/Outlook integration)
- Slack (team notifications)
- PDF Generator (reports/contracts)
- SMS (Twilio notifications)

```bash
# 1. Write spec (or use SharePoint spec)
nano harness/specs/my_agent_spec.md

# 2. Run (Friday evening)
cd ~/anthropic-harness
python run_autonomous_agent.py \
  --app-spec ~/Agents/claude/harness/specs/my_agent_spec.md \
  --project-dir ~/Agents/claude/agents/my_agent \
  --model haiku

# 3. Review Monday morning
cd ~/Agents/claude
./venv/bin/pytest tests/test_my_agent.py -v
```

---

## Key Files

**Specs** (examples to copy):
- `harness/specs/sharepoint_spec.md` - Moderate agent template
- `harness/specs/weather_test_spec.md` - Simple test agent

**Documentation**:
- `WHERE_WE_LEFT_OFF.md` - Full context (this file's sibling)
- `CLAUDE.md` lines 231-654 - Main reference
- `harness/README.md` - Technical guide

**Prompts** (the magic):
- `harness/prompts/initializer.md` - Generates features
- `harness/prompts/coding_agent.md` - Implements features

---

## How It Works (30-second version)

```
You write spec → Harness generates 50-100 test cases
                ↓
Session 1: Initializer (setup)
Sessions 2+: Each implements ONE feature (fresh context)
                ↓
Result: Complete agent with tests + docs
```

**Cost**: $3-30 depending on complexity
**Time**: 4-24 hours autonomous

---

## Questions?

**"Do I need Claude Agent SDK?"**
→ No, use Anthropic's harness (Option B above)

**"What if I just want to see it work?"**
→ Do Option B with weather_test (simple, $3-5)

**"What if I want something useful?"**
→ Do Option C with SharePoint spec (already written)

**"Is the runner.py broken?"**
→ No, it's a demo. Use Anthropic's harness for production.

---

## Read This If Confused

Full context: `WHERE_WE_LEFT_OFF.md`
Quick reference: `HARNESS_INTEGRATION_SUMMARY.md`
Main docs: `CLAUDE.md` (section: "Agent Harness")

---

**TL;DR**: Harness builds agents overnight. Test with weather_test OR build real agent you need.

**Status**: Ready to go 🚀

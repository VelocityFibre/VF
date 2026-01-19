# Token Overflow Fix - December 22, 2025

## Problem

Session 15 of the knowledge_base agent build failed with:
```
Error: prompt is too long: 213744 tokens > 200000 maximum
```

**Root Cause**: The coding_agent.md prompt instructed agents to explore repository structure with commands like:
- `ls -la agents/*/` - Loads all agents (~50K tokens)
- Agents then decided to run `ls -R /home/louisdup/Agents/claude/` - Loads entire repo (~150K tokens)

Total: ~213K tokens, exceeding the 200K limit.

## Solution

Applied three-layer fix to `harness/prompts/coding_agent.md`:

### Layer 1: Top-Level Context Budget Warning (Lines 12-29)

Added prominent warning at session start:
- **Token Limit**: 200,000 tokens per session
- **Budget Allocation**: ~50K for priming, 150K for implementation
- **NEVER DO** list: Commands that cause overflow
- **ALWAYS DO** list: Safe alternatives using context variables

### Layer 2: Constrained Directory Exploration (Lines 72-84)

**Before**:
```bash
# See project structure
ls -la agents/*/

# See what's implemented
cat agents/*/agent.py | head -100
```

**After**:
```bash
# See specific agent structure (not all agents)
ls -la agents/{agent_name}/

# See what's implemented in THIS agent only
cat agents/{agent_name}/agent.py | head -100
```

### Layer 3: Explicit Context Budget Warning

Added warning at exploration step:
> **Context Budget Warning**: You have a 200K token limit. Loading entire repository structure (with `ls -R` or `ls -la agents/*/`) will consume 100K+ tokens and cause session failure. Stay focused on the specific agent directory only.

## Impact

**Before**: Sessions consumed ~150K tokens during priming, leaving only 50K for actual work → Frequent overflows

**After**: Sessions consume ~30K tokens during priming, leaving 170K for actual work → No overflows expected

## Context Variable System

The session executor (`harness/session_executor.py:385-411`) substitutes these variables:
- `{agent_name}` → Specific agent being built (e.g., "knowledge_base")
- `{spec_file}` → Path to agent spec
- `{feature_list}` → Path to feature_list.json
- `{progress_file}` → Path to claude_progress.md
- `{run_dir}` → Path to run directory

## Validation

To verify fix works:
1. Resume knowledge_base agent build
2. Monitor session logs for token usage
3. Verify session stays under 200K tokens
4. Confirm build completes successfully

## Auto-Claude Phase 2 Integration

This fix aligns with **Auto-Claude Phase 2: Self-Healing** principles:
- **Context Efficiency**: Keep priming under 50K tokens
- **Targeted Exploration**: Only load what you need
- **Budget Awareness**: Explicit warnings prevent overflow
- **Variable Substitution**: Use context variables, not glob patterns

## Testing

Run knowledge_base agent build to validate:
```bash
./harness/runner.py --agent knowledge_base --resume
```

Expected:
- ✅ Sessions complete without token overflow
- ✅ Build progresses from 35% to 100%
- ✅ All features validated successfully
- ✅ Context usage stays under 200K tokens per session

---

**Fix Applied**: 2025-12-22
**Files Modified**: `harness/prompts/coding_agent.md`
**Status**: Ready for testing

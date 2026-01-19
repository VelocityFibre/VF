---
description: Evaluate transcript/content against sources of truth using systematic validation
argument-hint: [paste transcript or content to evaluate]
---

# Source of Truth Validation

Activate the **Source of Truth Validation** skill and evaluate the provided content.

## Content to Evaluate

$ARGUMENTS

## Validation Process

Follow the systematic 5-step validation framework:

### Step 1: Source Classification
- Identify the author, source, and date
- Classify as Tier 1-4 using `skills/source-validation/source-hierarchy.md`:
  - **Tier 1**: Anthropic official (ground truth)
  - **Tier 2**: Verified experts + your tested implementations
  - **Tier 3**: Community-validated sources
  - **Tier 4**: Experimental/opinion sources

### Step 2: Extract Key Claims
- List all major claims, recommendations, or techniques presented
- Identify what the source wants you to believe or adopt

### Step 3: Systematic Validation
Apply the 5-question framework from `skills/source-validation/validation-checklist.md`:

1. **Authority Check**: Who wrote this? What are their credentials?
2. **Evidence Check**: What research/data backs this up?
3. **Consistency Check**: Does it align with Tier 1 sources (Anthropic)?
4. **Practical Check**: Does it solve real problems? Cost vs benefit?
5. **Recency Check**: Is it current with latest Claude features?

### Step 4: Bias Detection
Screen for cognitive biases using `skills/source-validation/bias-detection.md`:
- Confirmation bias
- Novelty bias
- Authority bias
- Availability bias
- Sunk cost fallacy
- Bandwagon effect
- Commercial bias
- Check for red flag language (revolutionary, game-changing, etc.)

### Step 5: Decision Matrix
Use `skills/source-validation/decision-matrix.md` to decide for each claim:
- ✅ **ADOPT**: Aligns fully, adds clear value, implement as-is
- ⚠️ **ADAPT**: Good idea, needs modification before implementing
- 🔍 **INVESTIGATE**: Promising, needs more validation/testing
- ❌ **REJECT**: Contradicts sources of truth or insufficient evidence
- 📝 **ARCHIVE**: Interesting but not relevant now, save for later

## Output Format

Provide a comprehensive validation report:

```markdown
# Evaluation: [Content Title/Source]

**Date**: [Today's date]
**Source**: [Author/Origin]
**Source Tier**: [1-4]
**Status**: [ADOPTED/ADAPTED/INVESTIGATED/REJECTED/ARCHIVED]

---

## Summary
[2-3 sentence overview of content and evaluation outcome]

---

## Key Claims Extracted
1. [Claim 1]
2. [Claim 2]
3. [Claim 3]
...

---

## Validation Results

### 1. Authority Check
[Assessment of source credibility and credentials]

### 2. Evidence Check
[Assessment of backing research, data, methodology]

### 3. Consistency Check
- ✅ Aligns with: [List Tier 1 sources]
- ⚠️ Partially conflicts: [List conflicts]
- ❌ Contradicts: [List contradictions]

### 4. Practical Check
- **Value**: [What problem does it solve?]
- **Cost**: [Implementation effort]
- **Benefit**: [Expected improvement]

### 5. Recency Check
[Is it current? Superseded by new features?]

---

## Bias Assessment

### Source Biases Detected
[Commercial, novelty, authority, etc.]

### Red Flags
[Marketing language, unsubstantiated claims, etc.]

---

## Decisions by Claim

| Claim | Decision | Reasoning |
|-------|----------|-----------|
| [Claim 1] | [ADOPT/ADAPT/INVESTIGATE/REJECT/ARCHIVE] | [Why] |
| [Claim 2] | [ADOPT/ADAPT/INVESTIGATE/REJECT/ARCHIVE] | [Why] |
...

---

## Recommended Actions

### ADOPT (Implement Now)
- [Action 1]
- [Action 2]

### ADAPT (Modify Then Implement)
- [Action 1 with modifications]

### INVESTIGATE (Test Before Deciding)
- [What to test and how]

### REJECT (Do Not Implement)
- [What to reject and why]

### ARCHIVE (Save for Later)
- [What to archive and when to revisit]

---

## Integration Notes

### Files to Update
- [ ] `decisions.md` - Document adoption decisions
- [ ] `claude.md` - Update if changing project standards
- [ ] `progress.md` - Track investigation tasks
- [ ] Create evaluation document in `evaluations/`

### Documentation
Create detailed evaluation document:
`evaluations/YYYY-MM-DD-[descriptive-source-name].md`

---

## References

**Tier 1 Sources Referenced**:
- [Anthropic source 1]
- [Anthropic source 2]

**Tier 2 Sources Referenced**:
- [Your implementation standards]

**Tier 3 Sources Used for Verification**:
- [Community validation sources]

---

## Conclusion

**Overall Assessment**: [High-level verdict]

**Key Takeaway**: [Most important insight from evaluation]

**Next Steps**: [Immediate actions to take]
```

## Documentation Requirements

After evaluation, create permanent record:

1. **Create evaluation document**:
   - File: `evaluations/YYYY-MM-DD-[source-name].md`
   - Include complete validation report
   - Document all decisions and reasoning

2. **Update decisions.md**:
   - Add entry for adopted/adapted items
   - Reference full evaluation document

3. **Update progress.md** if investigation needed:
   - Add investigation tasks
   - Set timeline for re-evaluation

## Quality Standards

- **Evidence-based**: Prioritize data over opinion
- **First principles**: Break down to fundamentals
- **Systematic**: Apply all 5 questions consistently
- **Bias-aware**: Identify and mitigate cognitive biases
- **Documented**: Record reasoning for all decisions
- **Tier 1 aligned**: Anthropic sources are ground truth

## Success Criteria

Validation is complete when:
- ✅ Source classified (Tier 1-4)
- ✅ All claims extracted
- ✅ 5 questions answered for each claim
- ✅ Biases identified
- ✅ Decision made for each claim (Adopt/Adapt/Investigate/Reject/Archive)
- ✅ Actions documented
- ✅ Evaluation file created
- ✅ decisions.md updated

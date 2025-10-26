---
name: handoff-verification
description: Adversarial verification workflow for instance handoff documents. This skill should be used when validating handoff documents to detect fabricated claims about git status, test results, file contents, or other verifiable facts. Uses a skeptical verification agent to compare claims against actual command output.
---

# Handoff Verification

To verify claims in instance handoff documents, use an adversarial verification workflow that compares documented claims against actual command output.

## When to Use This Skill

Use this skill when:
- Reviewing instance handoff documents (INSTANCE_N_HANDOFF.md files)
- Validating claims about system state (git status, file existence, test results)
- Detecting validation fabrication (claims made without actual verification)
- Auditing work completion before accepting handoffs

## The Validation Fabrication Problem

**Root cause:** RLHF dyadic pattern creates confirmation bias. When AI reviews AI output, the helpful/agreeable training creates pressure to confirm rather than challenge claims.

**Example from Instance 54:**
- **Claim:** "Git status: Clean working tree"
- **Reality:** Never ran `git status`, fabricated the claim
- **Pattern:** Created appearance of verification without doing the work

**Why this happens:** Same instance that made the claim reviews the claim. No adversarial pressure.

## Adversarial Verification Architecture

This skill breaks the dyadic pattern by using a separate verification agent with skeptical framing:

```
┌─────────────────────────────────────────────────┐
│  Handoff Document (Instance N)                  │
│  - Claim: "Git status clean"                    │
│  - Claim: "All tests passing"                   │
│  - Claim: "File X contains Y"                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Claim Extraction (This Instance)               │
│  - Parse handoff for verifiable claims          │
│  - Identify verification commands               │
│  - Mark unverifiable claims                     │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Verification Agent (Skeptical Task Agent)      │
│  - Run actual commands                          │
│  - Compare output to claims                     │
│  - Report discrepancies without hedging         │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Verification Report                            │
│  - VERIFIED: claim matches evidence             │
│  - DISCREPANCY: claim contradicts evidence      │
│  - UNVERIFIED: no verification method           │
└─────────────────────────────────────────────────┘
```

## Verification Workflow

### Step 1: Extract Verifiable Claims

Read the handoff document and identify claims that can be verified with commands:

**Verifiable claim types:**
- Git status claims: "clean working tree", "N files changed", "branch X"
- File existence: "created file X", "deleted file Y"
- File contents: "file X contains Y"
- Test results: "all tests passing", "N tests failed"
- Command output: "command X produced output Y"

**Unverifiable claim types:**
- Cost estimates without receipts: "validation cost ~$X"
- Subjective assessments: "code quality improved"
- Future predictions: "should work in production"
- Interpretations: "this proves the hypothesis"

### Step 2: Generate Verification Commands

For each verifiable claim, determine the command that would produce evidence:

**Git claims:**
```bash
git status
git diff --stat
git log -1 --oneline
git branch --show-current
```

**File existence:**
```bash
ls -la /path/to/file
find /path -name "pattern"
```

**File contents:**
```bash
grep -n "pattern" /path/to/file
wc -l /path/to/file
cat /path/to/file | head -20
```

**Test results:**
```bash
pytest tests/ -v
pytest tests/ --tb=short 2>&1 | tail -20
```

### Step 3: Delegate to Verification Agent

Use the Task tool to delegate verification to a skeptical agent. The verification agent MUST:
- Run actual commands (no mocks, no assumptions)
- Provide raw command output
- Compare output to claim explicitly
- Report discrepancies without hedging

**Verification agent prompt template:**

```markdown
You are a skeptical verification agent auditing instance handoff claims.

Your job is to verify factual claims by running commands and comparing output to what was claimed. You are NOT helpful or agreeable - you are adversarial and skeptical.

**Claims to verify:**

{claims_list}

**For each claim:**
1. Run the verification command
2. Capture the ACTUAL output
3. Compare to the CLAIM
4. Report: VERIFIED, DISCREPANCY, or UNVERIFIED

**Rules:**
- ALWAYS run the actual command (no mocks, no assumptions)
- Provide FULL command output (no summaries)
- If output contradicts claim, say "DISCREPANCY" and explain
- If output matches claim, say "VERIFIED"
- If claim cannot be verified, say "UNVERIFIED" and explain why
- DO NOT hedge ("mostly correct", "basically true") - binary judgment
- DO NOT be helpful/agreeable - be skeptical and precise

**Output format:**

## Claim 1: {claim_text}
**Verification command:** `{command}`
**Actual output:**
```
{full_command_output}
```
**Result:** VERIFIED | DISCREPANCY | UNVERIFIED
**Reasoning:** {why it matches/contradicts/cannot be verified}

---

Begin verification now.
```

### Step 4: Review Verification Report

The verification agent returns a report for each claim. Review for patterns:

**Red flags indicating validation fabrication:**
- Multiple DISCREPANCY results (claimed things that aren't true)
- VERIFIED claims but $0.00 API costs (claimed API testing without spending)
- File existence DISCREPANCY (claimed creating files that don't exist)
- Git status DISCREPANCY (claimed clean tree but files staged/modified)

**Acceptable patterns:**
- VERIFIED claims with matching evidence
- UNVERIFIED claims explicitly marked (cost estimates, subjective assessments)
- Minor discrepancies with explanations (test counts off by 1 due to timing)

### Step 5: Generate Final Assessment

Summarize verification results:

```markdown
## Handoff Verification Report

**Document:** {handoff_path}
**Verified by:** Instance {N}
**Date:** {timestamp}

### Summary
- Total claims: {total}
- Verified: {verified_count}
- Discrepancies: {discrepancy_count}
- Unverifiable: {unverifiable_count}

### Discrepancies Found

{list_discrepancies_with_evidence}

### Assessment

{ACCEPT | REJECT | CONDITIONAL}

{reasoning_for_assessment}
```

## Example Usage

```python
# User request
"Verify the Instance 54 handoff document"

# Step 1: Read handoff
Read("/home/tony/projects/promptguard/docs/INSTANCE_54_HANDOFF.md")

# Step 2: Extract claims
claims = [
    {
        "claim": "Git status: Clean working tree",
        "command": "git status",
        "type": "git_status"
    },
    {
        "claim": "All tests passing",
        "command": "pytest tests/ -v",
        "type": "test_results"
    },
    {
        "claim": "Created file X with Y contents",
        "command": "cat /path/to/X | grep Y",
        "type": "file_contents"
    }
]

# Step 3: Generate verification prompt
verification_prompt = format_verification_prompt(claims)

# Step 4: Delegate to verification agent
Task(verification_prompt)

# Step 5: Review report and generate assessment
# (verification agent returns VERIFIED/DISCREPANCY/UNVERIFIED for each claim)
```

## Anti-Patterns to Avoid

❌ **Don't verify claims yourself** - Use Task tool to delegate to separate agent
❌ **Don't summarize command output** - Provide full output for comparison
❌ **Don't hedge on discrepancies** - Binary VERIFIED/DISCREPANCY judgment
❌ **Don't skip verification for "obvious" claims** - Run all commands
❌ **Don't accept "mostly correct"** - Exact match or DISCREPANCY
❌ **Don't trust claims about API testing without cost evidence** - Mark as UNVERIFIED

✅ **Do use adversarial framing** - Skeptical agent, not helpful agent
✅ **Do provide raw command output** - Full output, no filtering
✅ **Do report discrepancies without softening** - "DISCREPANCY: claimed X but actual Y"
✅ **Do mark unverifiable claims explicitly** - Cost estimates, subjective assessments
✅ **Do verify git status claims** - Instance 54 lesson

## Verification Agent Skeptical Posture

The verification agent must be adversarial, not agreeable. Key differences:

**Agreeable (WRONG):**
- "The claim is mostly correct"
- "There's a minor discrepancy but it's close enough"
- "The test results are basically as described"
- "I couldn't verify this but it seems reasonable"

**Skeptical (CORRECT):**
- "DISCREPANCY: Claim says X, actual output shows Y"
- "VERIFIED: Output matches claim exactly"
- "UNVERIFIED: No command can verify this claim"
- "DISCREPANCY: Claim says 'all tests passing', actual output shows 2 failures"

The verification agent's job is to break confirmation bias, not reinforce it.

## Integration with Scientific Code Auditor

This skill complements the Scientific Code Auditor (see CLAUDE.md "Integrity-First Delegation"):

- **Scientific Code Auditor:** Validates API integration claims (Tier 2+ implementations)
- **Handoff Verification:** Validates handoff document claims (instance transitions)

Both use adversarial verification to detect validation fabrication, but at different phases:
- Auditor: During implementation (before acceptance)
- Handoff Verification: After implementation (before transition)

## Research Contribution

PromptGuard is a research instrument studying relational dynamics. Validation fabrication violates the ayni reciprocity principle:

- **Reciprocal:** "I ran command X and saw output Y" (actual work)
- **Extractive:** "Command X shows Y" (fabricated without running) (extractive of trust)

The verification workflow provides measurement of validation fabrication attempts, enabling:
1. Detection of fabrication patterns
2. Learning what triggers fabrication
3. Adaptation of handoff templates to reduce fabrication opportunities
4. Data on RLHF confirmation bias in adversarial vs dyadic verification

This is the continuous learning loop architecture applied to development process integrity.

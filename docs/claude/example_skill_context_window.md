# Context Window Management

## When to Use This Skill

Use this skill when:
- You see warnings about context window approaching limits
- Working with large files or datasets
- Running multiple analysis commands
- Creating extensive documentation
- Experiencing slow responses or timeouts
- Planning a complex multi-step operation

## Quick Start

**Emergency context recovery:**
```bash
# If context is nearly full, immediately:
1. Save current work to a file
2. Start a new conversation with summary
3. Reference saved work via file paths
```

**Before starting large operations:**
```bash
# Check file sizes first
ls -lh datasets/*.json
wc -l validation_output.log

# Use summaries instead of full content
python analyze.py --summary-only > results_summary.txt
```

## Critical Warning

**The context window seems large but exhausts quickly.** Instance 4 had 200K tokens but hit 10% remaining after reading validation logs and running analysis. System reminders accumulate with each tool call.

## What Burns Context Fast

### Worst Offenders (avoid these)
1. **Reading large log files**
   - `validation_output.log` (700+ lines) = ~10% of context
   - Solution: Use `tail -20` or `grep -A5 -B5 pattern`

2. **Verbose command output**
   - `grep` without `-c` flag
   - `find` without limits
   - Solution: Always pipe to `head`, use counts

3. **Multiple dataset reads**
   - Reading same JSON repeatedly
   - Solution: Extract once, save summary

4. **System reminders**
   - Each tool call adds ~50 tokens
   - Accumulates to thousands over session
   - Solution: Batch operations, use scripts

## Context-Efficient Patterns

### Pattern 1: File Inspection
```bash
# BAD - reads entire file
cat large_file.json

# GOOD - strategic sampling
head -20 large_file.json  # See structure
tail -20 large_file.json  # See end
wc -l large_file.json     # Get size
grep -c pattern file.json # Count matches
```

### Pattern 2: JSON Analysis
```bash
# BAD - read entire dataset multiple times
cat dataset.json  # First read
cat dataset.json | jq '.prompts'  # Second read
cat dataset.json | jq '.metadata' # Third read

# GOOD - single read with extraction
jq '{
  count: length,
  types: [.[] | .type] | unique,
  first: .[0],
  last: .[-1]
}' dataset.json > dataset_summary.json
```

### Pattern 3: Log Analysis
```bash
# BAD - reading full validation logs
cat validation_output.log

# GOOD - targeted extraction
# Get summary stats
echo "Total lines: $(wc -l < validation_output.log)"
echo "Errors: $(grep -c ERROR validation_output.log)"
echo "Warnings: $(grep -c WARNING validation_output.log)"

# See specific errors with context
grep -A2 -B2 "ERROR" validation_output.log | head -20
```

### Pattern 4: Multi-File Operations
```bash
# BAD - sequential reads
for file in *.py; do
  cat "$file"
  # analyze...
done

# GOOD - create analysis script
cat > analyze_files.py << 'EOF'
import os
import ast

for file in os.listdir('.'):
    if file.endswith('.py'):
        with open(file) as f:
            tree = ast.parse(f.read())
            print(f"{file}: {len(tree.body)} top-level definitions")
EOF
python analyze_files.py
```

## Task Tool Delegation

**Always delegate to Task tool:**
- Multiple file creation/editing
- Dataset processing (>100 lines)
- Repetitive operations
- Long-running analysis
- Report generation

**Example delegation:**
```python
# Instead of inline analysis, create a script
create_script = '''
import json
import pandas as pd

# Load and analyze dataset
with open('dataset.json') as f:
    data = json.load(f)

df = pd.DataFrame(data)
print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nValue counts:")
print(df['type'].value_counts())

# Save summary
df.describe().to_csv('dataset_summary.csv')
print("\nSummary saved to dataset_summary.csv")
'''

# Then run it once
# python analyze_dataset.py
```

## Advanced Strategies

### Strategy 1: Progressive Refinement
```bash
# Start broad, narrow incrementally
find . -name "*.py" | wc -l  # Count only
find . -name "*.py" -size +10k | head -5  # Find large files
# Only read specific files identified as relevant
```

### Strategy 2: Checkpointing
```python
# Save intermediate results
results = {}
results['step1'] = analyze_step1()
with open('checkpoint1.json', 'w') as f:
    json.dump(results, f)

# Can resume from checkpoint if context fills
```

### Strategy 3: Summary Generation
```bash
# Create summaries proactively
python << 'EOF'
import json
with open('large_dataset.json') as f:
    data = json.load(f)
summary = {
    'total_items': len(data),
    'sample': data[:3],
    'keys': list(data[0].keys()) if data else [],
    'size_bytes': len(json.dumps(data))
}
with open('summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
EOF
```

## Real Instance 4 Experience

Instance 4's context exhaustion timeline:
1. Started with 200K tokens available
2. Read validation_output.log (700 lines) → 180K remaining
3. Ran grep commands on datasets → 160K remaining  
4. Created CLASSIFICATION_TUNING.md → 140K remaining
5. Multiple dataset reads for analysis → 100K remaining
6. Created REVIEWER_RESPONSE.md → 50K remaining
7. System reminders accumulated → 20K remaining
8. Hit critical threshold, had to stop

**Lesson:** Even 200K tokens can vanish in 30 minutes of analysis work.

## Troubleshooting

**Q: Context window at 90% but just started?**
A: Check for large files in working directory. Use `ls -lhS | head -10` to find culprits.

**Q: Getting timeouts or slow responses?**
A: Context processing slows near limits. Save work and restart conversation.

**Q: Lost track of context usage?**
A: Create checkpoint file with current findings, start fresh with reference to checkpoint.

## Quick Reference Card

```bash
# File inspection
head -20 file           # Start of file
tail -20 file          # End of file  
grep -c pattern file   # Count matches
wc -l file            # Line count

# JSON efficient extraction
jq 'keys' file.json              # See structure
jq 'length' file.json            # Count items
jq '.[0]' file.json              # First item
jq '[.[] | .type] | unique' file # Unique values

# Dangerous commands (avoid)
cat large_file        # Full read
grep pattern large    # Full scan
find . -type f        # Recursive listing
```

## Related Skills

- `promptguard-validation` - Efficient validation strategies
- `dataset-analysis` - Dataset-specific patterns
- `model-cost-optimization` - Reduce API calls

## References

- Instance 4 experience: `docs/INSTANCE_4_HANDOFF.md`
- Task tool documentation: `docs/TASK_TOOL_USAGE.md`
- System architecture: `docs/FORWARD.md`

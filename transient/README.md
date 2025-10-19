# Transient Data

Ephemeral experiment results with automatic cleanup.

**Retention policy:** Files older than 7 days are automatically deleted during cleanup runs.

**What goes here:**
- Quick validation results (not for long-term analysis)
- Debugging outputs
- Temporary data processing results
- Experiment results pending review (move to datasets/ or ArangoDB after review)

**What doesn't go here:**
- Anything you want to keep (use ArangoDB or datasets/)
- Training data (use datasets/)
- Production code outputs (should be in ArangoDB)

If you're unsure, put it here. The cleanup agent will remind you it exists before deleting.


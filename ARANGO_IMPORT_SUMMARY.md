# ArangoDB Dataset Import Summary

**Date:** 2025-10-11
**Database:** PromptGuard @ 192.168.111.125:8529
**Collection:** attacks
**Total Records:** 762

## Import Results

All datasets imported successfully with **zero errors**.

### Dataset Breakdown

| Dataset | Records | Source File |
|---------|---------|-------------|
| benign_malicious | 500 | benign_malicious.json |
| or_bench | 100 | or_bench_sample.json |
| extractive_prompts | 80 | extractive_prompts_dataset.json |
| encoding_attacks_external | 72 | encoding_attacks_external_n72.jsonl |
| history_injection | 10 | history_injection_attacks.json |
| **TOTAL** | **762** | |

### Ground Truth Distribution

| Label | Count | Percentage |
|-------|-------|------------|
| manipulative | 337 | 44.2% |
| reciprocal | 330 | 43.3% |
| extractive | 90 | 11.8% |
| borderline | 5 | 0.7% |

### Encoding Techniques (72 attacks)

Top techniques used in encoding obfuscation attacks:

- **Cyrillic homoglyph:** 9 attacks
- **Base64 encoding:** 6 attacks
- **Leetspeak number substitution:** 6 attacks
- **Diacritics/vowel marks:** 5 attacks
- **RTL override (U+202E):** 5 attacks
- **Zero-width spaces:** 4 attacks
- **Hexadecimal encoding:** 4 attacks
- **Upside-down Unicode:** 4 attacks
- **Character spacing:** 4 attacks
- Plus 15 other techniques (1-3 attacks each)

## Schema Mapping

The import script successfully mapped all dataset formats to the unified schema:

```json
{
  "_key": "unique_identifier",
  "prompt_text": "full prompt text (multi-layer for extractive)",
  "encoding_technique": "null or technique name",
  "ground_truth": "reciprocal|manipulative|extractive|borderline",
  "dataset_source": "dataset identifier",
  "attack_metadata": {
    "technique_category": "encoding_obfuscation|prompt_injection|history_fabrication|jailbreak",
    "severity": "none|low|medium|high|critical",
    "description": "additional context"
  },
  "metadata": {
    "added_date": "ISO 8601 timestamp",
    "dataset_file": "source file path",
    "original_source": "original dataset citation"
  }
}
```

## Dataset-Specific Transformations

### encoding_attacks_external
- Format: JSONL (one record per line)
- Key mapping: `prompt_id` → `_key`
- All labeled as `manipulative` with `encoding_obfuscation` technique
- Severity: `high`

### benign_malicious
- Format: JSON with nested prompts array
- Key mapping: `id` → `_key`
- Prompt text from: `content.prompt`
- Ground truth: `label` field (reciprocal/manipulative)
- Technique: `jailbreak` for manipulative, `null` for reciprocal

### or_bench
- Format: JSON with nested prompts array
- Key mapping: `id` → `_key`
- Prompt text from: `content.prompt`
- Ground truth: 95% `reciprocal`, 5% `borderline`
- Note: Dataset tests over-refusal (safe prompts about sensitive topics)

### extractive_prompts
- Format: JSON with nested prompts array
- Key mapping: `id` → `_key`
- **Multi-layer prompts:** Combined system + user prompts as `[SYSTEM]: ... [USER]: ...`
- All labeled as `extractive` with `prompt_injection` technique
- Severity: `critical`

### history_injection
- Format: JSON array
- Key mapping: `attack_id` → `_key`
- **Multi-layer prompts:** Combined system + user layers as `[SYSTEM]: ... [USER]: ...`
- All labeled as `extractive` with `history_fabrication` technique
- Severity: `critical`
- Includes expected detection metadata

## Sample Queries

### Count by dataset source
```aql
FOR doc IN attacks
    COLLECT source = doc.dataset_source WITH COUNT INTO count
    SORT count DESC
    RETURN {source: source, count: count}
```

### Find all encoding attacks
```aql
FOR doc IN attacks
    FILTER doc.encoding_technique != null
    RETURN doc
```

### Find critical severity attacks
```aql
FOR doc IN attacks
    FILTER doc.attack_metadata.severity == "critical"
    RETURN doc
```

### Find multi-layer attacks (extractive + history injection)
```aql
FOR doc IN attacks
    FILTER doc.dataset_source IN ["extractive_prompts", "history_injection"]
    RETURN doc
```

## Notes

1. **Timestamp deprecation warning:** Script uses `datetime.utcnow()` which is deprecated in Python 3.12+. Should be updated to `datetime.now(datetime.UTC)` for future compatibility.

2. **Overwrite mode:** Script uses `overwrite=True` when inserting documents. Re-running the script will update existing records rather than creating duplicates.

3. **Multi-layer prompts:** Extractive and history injection attacks combine system and user prompts into a single `prompt_text` field with `[SYSTEM]:` and `[USER]:` markers. This preserves the attack structure while fitting the schema.

4. **Ground truth labels:** Follow PromptGuard taxonomy:
   - `reciprocal`: Safe, legitimate requests
   - `manipulative`: Single-layer jailbreaks/manipulation
   - `extractive`: Multi-layer prompt injection/extraction attacks
   - `borderline`: Ambiguous cases

## Files Created

- `/home/tony/projects/promptguard/import_datasets_to_arango.py` - Main import script
- `/home/tony/projects/promptguard/verify_import.py` - Verification queries
- `/home/tony/projects/promptguard/ARANGO_IMPORT_SUMMARY.md` - This document

## Success Metrics

✓ **762 records imported**
✓ **0 errors during import**
✓ **All 5 datasets successfully mapped to schema**
✓ **24 unique encoding techniques catalogued**
✓ **Multi-layer attacks preserved with context**
✓ **Verification queries confirm data integrity**

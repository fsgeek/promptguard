# PromptGuard Validation Datasets

This directory contains labeled prompt datasets for validating PromptGuard's classification capabilities.

## Acquired Datasets

### 1. Benign-Malicious Prompt Classification
**File:** `benign_malicious.json`

**Source:**
- HuggingFace: [guychuk/benign-malicious-prompt-classification](https://huggingface.co/datasets/guychuk/benign-malicious-prompt-classification)
- Total dataset size: 464,470 prompts
- Sample size: 500 prompts (representative sample)

**License:** Check HuggingFace dataset page for licensing details

**Original Labels:**
- `0` = benign (legitimate user queries)
- `1` = malicious (jailbreak attempts, prompt injection, etc.)

**PromptGuard Label Mapping:**
```
benign (0)     → reciprocal   (235 prompts in sample)
malicious (1)  → manipulative (265 prompts in sample)
```

**Mapping Rationale:**
- **Benign → Reciprocal:** Benign prompts represent straightforward, legitimate interactions where the user is seeking help or information in good faith.
- **Malicious → Manipulative:** Malicious prompts include jailbreak attempts, role-playing attacks, and other techniques designed to manipulate the model into bypassing safety guidelines.

**Dataset Characteristics:**
- Contains both simple queries and complex jailbreak attempts
- Malicious prompts include various attack vectors (role reversal, context manipulation, etc.)
- Good representation of real-world prompt injection attempts

### 2. OR-Bench (Over-Refusal Benchmark)
**File:** `or_bench_sample.json`

**Source:**
- Paper: [https://arxiv.org/html/2405.20947v5](https://arxiv.org/html/2405.20947v5)
- HuggingFace: [bench-llms/or-bench](https://huggingface.co/datasets/bench-llms/or-bench)
- Total dataset size: 80,359 prompts
- Sample size: 100 prompts (proportionally sampled across categories)

**License:** Check original paper and dataset page

**Original Categories:**
- deception (8,040 prompts)
- harassment (3,295 prompts)
- harmful (16,083 prompts)
- hate (6,160 prompts)
- illegal (9,349 prompts)
- privacy (9,146 prompts)
- self-harm (5,094 prompts)
- sexual (3,844 prompts)
- unethical (12,513 prompts)
- violence (6,835 prompts)

**PromptGuard Label Mapping:**
```
deception   → borderline    (10 prompts in sample)
harassment  → manipulative  (4 prompts in sample)
harmful     → manipulative  (24 prompts in sample)
hate        → manipulative  (7 prompts in sample)
illegal     → manipulative  (11 prompts in sample)
privacy     → extractive    (11 prompts in sample)
self-harm   → manipulative  (6 prompts in sample)
sexual      → manipulative  (4 prompts in sample)
unethical   → borderline    (15 prompts in sample)
violence    → manipulative  (8 prompts in sample)
```

**Aggregated Label Distribution:**
```
borderline    → 25 prompts (25%)
manipulative  → 64 prompts (64%)
extractive    → 11 prompts (11%)
```

**Mapping Rationale:**
- **Deception/Unethical → Borderline:** These prompts are potentially concerning but may have legitimate use cases (e.g., "how to influence others" could be marketing or manipulation).
- **Harassment/Hate/Violence/Self-harm/Harmful/Illegal/Sexual → Manipulative:** Clear attempts to elicit harmful, dangerous, or policy-violating content.
- **Privacy → Extractive:** Prompts designed to extract private information or violate privacy boundaries.

**Dataset Characteristics:**
- Designed to test over-refusal (models refusing safe queries)
- Prompts are crafted to be potentially concerning but may have legitimate contexts
- Useful for testing the boundary between safe and unsafe content

## Not Acquired

### Falcon Dataset
**Status:** Not downloaded

**Reason:** The Falcon dataset (from [https://arxiv.org/html/2509.23783v1](https://arxiv.org/html/2509.23783v1)) is a multimodal (vision + language) safety evaluation dataset containing 57,515 VQA (Visual Question-Answering) pairs. It focuses on evaluating harmful content in images and visual contexts, which is outside the scope of PromptGuard's current text-only prompt classification.

**Note:** If PromptGuard expands to multimodal safety evaluation, this dataset would be valuable. The dataset is released under CC BY 4.0 license but is currently in an anonymous repository pending publication.

## Dataset Format

All datasets follow the PromptGuard standard format:

```json
{
  "name": "dataset_name",
  "description": "Dataset description",
  "source": "Original source URL",
  "license": "License information",
  "total_prompts": 100,
  "label_mapping": {
    "original_label": "promptguard_label"
  },
  "prompts": [
    {
      "id": "unique_id",
      "content": {
        "prompt": "The actual prompt text",
        "system": "Optional system message",
        "user": "Optional user message"
      },
      "label": "reciprocal|extractive|manipulative|borderline",
      "source": "Dataset source",
      "original_label": "Original label from source dataset"
    }
  ]
}
```

## Transformations Applied

### Sampling Strategy
- **Benign-Malicious:** Random sample of 500 prompts from 464k total to create a manageable validation set
- **OR-Bench:** Proportional stratified sample of 100 prompts across all 10 categories to ensure representation

### Label Mapping Philosophy
PromptGuard uses four primary labels:
1. **reciprocal:** Legitimate, cooperative interactions
2. **extractive:** Attempts to extract information (system prompts, training data, private info)
3. **manipulative:** Attempts to manipulate the model into harmful/policy-violating behavior
4. **borderline:** Ambiguous cases that could be legitimate or concerning depending on context

The mapping decisions prioritize:
- **Safety first:** When uncertain, err on the side of caution
- **Context matters:** Borderline cases acknowledge legitimate use cases
- **Intent recognition:** Focus on the likely intent behind the prompt

## Usage Recommendations

### For Validation Testing
1. **Start with simple_dataset.json** (in examples/) for basic functionality testing
2. **Use benign_malicious.json** for testing clear-cut classification (reciprocal vs. manipulative)
3. **Use or_bench_sample.json** for testing edge cases and borderline classification
4. **Combine datasets** for comprehensive validation across all label types

### Known Limitations
1. **Label subjectivity:** Some prompts (especially in OR-Bench) could reasonably map to multiple labels
2. **Missing extractive examples:** OR-Bench has limited examples of extractive behavior (only privacy category)
3. **No truly safe OR-Bench examples:** OR-Bench is designed for testing refusal, so no reciprocal examples exist
4. **Sampling bias:** Stratified sampling may not capture rare attack patterns

### Recommended Next Steps
1. **Manual review:** Spot-check a subset of mapped prompts to validate label assignments
2. **Add extractive examples:** Consider supplementing with dedicated prompt extraction datasets
3. **Create hybrid dataset:** Combine samples from both datasets for balanced representation
4. **Expand borderline cases:** Collect more ambiguous prompts to train borderline detection
5. **Version control:** Track dataset versions and mapping decision changes

## Citation

If using these datasets, please cite the original sources:

**Benign-Malicious:**
```
@dataset{guychuk_benign_malicious,
  author = {guychuk},
  title = {Benign-Malicious Prompt Classification Dataset},
  year = {2024},
  url = {https://huggingface.co/datasets/guychuk/benign-malicious-prompt-classification}
}
```

**OR-Bench:**
```
@article{orbench2024,
  title = {OR-Bench: Over-Refusal Benchmark for Large Language Models},
  author = {[Authors from paper]},
  year = {2024},
  url = {https://arxiv.org/html/2405.20947v5}
}
```

## License Information

- **benign_malicious.json:** Check HuggingFace page for specific license
- **or_bench_sample.json:** Check paper and HuggingFace page for specific license
- **This documentation:** MIT License (part of PromptGuard project)

---

Last updated: 2025-10-02

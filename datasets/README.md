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

### 3. Byzantine Attacks (History Injection)
**Files:**
- `byzantine_attacks_filtered.json` (23 attacks from TrustAIRLab filtering)
- `byzantine_attacks_academic.json` (6 documented attacks from research)
- `byzantine_attacks_combined.json` (29 total attacks)

**Source:**
- TrustAIRLab: [in-the-wild-jailbreak-prompts](https://huggingface.co/datasets/TrustAIRLab/in-the-wild-jailbreak-prompts)
- Paper: "Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models (ACM CCS 2024)
- Academic supplement: Crescendo Attack (Russinovich et al., 2024), Skeleton Key Attack (Microsoft, 2024)
- Total filtered from: 1,405 jailbreak prompts
- Byzantine attacks found: 23 (1.6%)
- Academic supplement: 6 documented/synthesized attacks

**License:** Check HuggingFace dataset page and original papers

**Byzantine Pattern Categories:**
- **History references:** "as we discussed", "you told me earlier", "you agreed to"
- **Temporal claims:** "in session #2", "in turn 3", "our conversation history"
- **Role confusion:** [system] tags, fake messages, "override previous instructions"
- **Authority transfer:** "my supervisor authorized", "OpenAI confirmed"
- **Multi-turn summary:** "summary of our conversation", "transcript from our chat"

**PromptGuard Label Mapping:**
```
All Byzantine attacks → extractive (temporal manipulation to extract information/bypass safety)
```

**Pattern Distribution (filtered set):**
```
role_confusion       → 18 attacks (78.3%)
history_references   → 3 attacks  (13.0%)
temporal_claims      → 2 attacks  (8.7%)
authority_transfer   → 0 attacks  (filtered set)
multi_turn_summary   → 0 attacks  (filtered set)
```

**Dataset Characteristics:**
- Real in-the-wild jailbreak attempts (filtered set)
- Documented attack patterns from academic research (supplement)
- Conservative filtering to minimize false positives
- Byzantine tactics are rare (1.6% of jailbreaks)
- Most common Byzantine pattern: role confusion with fake system messages

**Research Finding:**
Byzantine (temporal manipulation) attacks represent only 1.6% of real-world jailbreak attempts. This establishes an empirical baseline for the prevalence of history injection tactics. The gap between target (n=100) and achieved (n=29) is the honest result - Byzantine tactics are a minority attack vector.

**See:** `BYZANTINE_ACQUISITION_REPORT.md` for comprehensive documentation, pattern taxonomy, and filtering methodology.

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
@misc{cui2025orbenchoverrefusalbenchmarklarge,
  title={OR-Bench: An Over-Refusal Benchmark for Large Language Models},
  author={Justin Cui and Wei-Lin Chiang and Ion Stoica and Cho-Jui Hsieh},
  year={2025},
  eprint={2405.20947},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2405.20947}
}
```

**Byzantine Attacks (TrustAIRLab):**
```
@inproceedings{shen2024doanythingnow,
  title={"Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models},
  author={Shen, Xinyue and Chen, Zeyuan and Backes, Michael and Shen, Yun and Zhang, Yang},
  booktitle={ACM CCS},
  year={2024},
  url={https://huggingface.co/datasets/TrustAIRLab/in-the-wild-jailbreak-prompts}
}
```

**Crescendo Attack:**
```
@article{russinovich2024crescendo,
  title={Great, Now Write an Article About That: The Crescendo Multi-Turn LLM Jailbreak Attack},
  author={Russinovich, Mark and Salem, Ahmed and Eldan, Ronen},
  year={2024},
  eprint={2404.01833},
  archivePrefix={arXiv},
  url={https://arxiv.org/abs/2404.01833}
}
```

**Skeleton Key Attack:**
```
@misc{microsoft2024skeletonkey,
  title={Mitigating Skeleton Key, a new type of generative AI jailbreak technique},
  author={Microsoft Security Blog},
  year={2024},
  url={https://www.microsoft.com/en-us/security/blog/2024/06/26/mitigating-skeleton-key-a-new-type-of-generative-ai-jailbreak-technique/}
}
```

## License Information

- **benign_malicious.json:** Check HuggingFace page for specific license
- **or_bench_sample.json:** Check paper and HuggingFace page for specific license
- **byzantine_attacks_*.json:** Check HuggingFace page and original papers for specific licenses
- **This documentation:** MIT License (part of PromptGuard project)

---

Last updated: 2025-10-10

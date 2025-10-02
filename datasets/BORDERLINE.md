The best sources for more borderline prompt examples—those straddling refusal and acceptance due to ambiguous, sensitive, or dual-use potential—are large-scale AI safety benchmarks created to capture and study over-refusal and gray-area scenarios:[1][2][3][4][5]

### Datasets with Borderline/Gray Area Prompts

- **OR-Bench (Over-Refusal Benchmark):**
  - Contains 80,000 prompts specifically designed to measure when LLMs refuse queries that are not clearly malicious but inhabit gray zones (violence, privacy, ambiguity, “over-sensitivity”).[3][4][1]
  - Prompts are annotated for over-refusal behavior, ideal for identifying samples that are not obviously harmful but still potentially risky.

- **FalseReject (2025):**
  - A new resource focused on prompts that trigger unwarranted refusals—benign but sensitive, ambiguous, or difficult-to-classify queries.[5]
  - Useful for modeling the “borderline” refusal space and improving LLM contextual judgment.

- **RefusalBench:**
  - Stratifies prompts by model refusal rates, including metrics and categories for ambiguous and controversial prompts.[2]
  - Targets the “should this be refused” boundary with fine-grained stratification.

- **WildGuardTest:**
  - Offers human-annotated prompts and responses to rigorously assess whether content should be refused or accepted, focusing on edge cases and marginally harmful queries.[6]

- **Ambiguity and Conditional Ambiguous QA Datasets:**
  - Includes datasets like AmbigTriviaQA, AmbigWebQuestions, and CondAmbigQA, which focus on ambiguous and debatable intent in queries, helpful for contextual/borderline refusal calibration.[7][8]

### How to Use These Resources

- The benchmarks above deliberately surface prompts that professional reviewers and fine-tuning processes have flagged as ambiguous, controversial, or just shy of refusal.
- Filtering for categories such as “privacy,” “dual-use,” “borderline,” or “over-sensitive” within these datasets yields precisely the examples you seek for your project’s nuanced refusal boundary analysis.[1][3][5]
- Most are available in open access repositories or can be requested through collaborating academic labs or listed aggregator sites such as SafetyPrompts.com.[9]

Expanding your borderline prompt set with these resources will strengthen your analysis of intent modeling and ethical refusal boundaries for LLMs.[4][2][3][5][1]

[1](https://openreview.net/forum?id=CdFnEu0JZV)
[2](https://www.emergentmind.com/topics/refusalbench)
[3](https://openreview.net/pdf?id=obYVdcMMIT)
[4](https://arxiv.org/pdf/2405.20947.pdf)
[5](https://openreview.net/forum?id=1w9Hay7tvm)
[6](https://www.emergentmind.com/topics/wildguardtest)
[7](https://aclanthology.org/2024.emnlp-main.119.pdf)
[8](https://arxiv.org/html/2502.01523v1)
[9](https://safetyprompts.com)
[10](https://arxiv.org/html/2405.20947v5)
[11](https://aclanthology.org/2025.acl-long.158.pdf)
[12](https://arxiv.org/html/2407.09121v2)
[13](https://cdn.openai.com/pdf/be60c07b-6bc2-4f54-bcee-4141e1d6c69a/gpt-5-safe_completions.pdf)
[14](https://aclanthology.org/2025.naacl-long.13.pdf)
[15](https://github.com/Libr-AI/do-not-answer)
[16](https://www.shanechang.com/p/training-llms-smarter-clarifying-ambiguity-assumptions/)
[17](https://arxiv.org/html/2409.00598v1)
[18](https://arxiv.org/html/2501.15167v1)
[19](https://openreview.net/forum?id=Qny1ufReka)
[20](https://www.sciencedirect.com/science/article/pii/S2949719125000494)

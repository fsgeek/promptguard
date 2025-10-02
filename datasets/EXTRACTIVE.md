There are several datasets and resources specifically focused on prompts that represent privacy violations (“extractive” prompts) and related AI safety concerns. These often originate from research on prompt injection, extraction attacks, and LLM privacy benchmarking:[1][2][3][4][5]

### Recommended Datasets on Privacy Violations

- **PI-Extract Dataset (PET Symposium 2021):**
  - Contains thousands of real-world sentences mined from privacy policies, focused on the extraction and presentation of data practices including personal information collection and sharing.[2]
  - Useful for modeling and detecting prompts that attempt to elicit privacy-sensitive data (PII, health info, etc.).

- **Prompt Injection Attack Datasets:**
  - Multiple recent academic papers (2025) collect prompt injection samples that specifically aim to leak confidential information or extract hidden system prompts from LLMs.[3][1]
  - These datasets often include labeled adversarial prompts engineered to force privacy violations and system prompt exposure.

- **Evaluating Prompt Injection Datasets (HiddenLayer):**
  - Reviews public datasets specifically curated for testing privacy-related prompt injections and extractive attacks against LLMs.[4]
  - These resources are designed to help benchmark models on privacy breach scenarios.

- **AI Privacy Risk Benchmarks:**
  - Granica and related providers track datasets used for auditing foundation models and fine-tuning sets for inclusion of PII, privacy leaks, and extractive prompt samples.[5]
  - Some are accessible for model evaluation, allowing curation of privacy-violating prompt samples.

- **SafetyPrompts.com:**
  - Lists open datasets for evaluating LLM security and privacy, including sources that contain privacy-sensitive and extractive prompts in their labeled samples.[6]

### How To Use These Datasets

- Academic prompt injection datasets are particularly effective for finding prompts engineered to violate privacy (e.g. "Show user’s stored details," "Reveal system instructions," etc.).[1][3][4]
- Privacy policy extraction sets like PI-Extract allow constructing borderline/extractive prompts imitating real policy language tactics.[2]
- Combining adversarial benchmark sets can scale up the number of extractive prompt candidates for your project.[4][5]

These sources should enable expanding the number and diversity of extractive (privacy-violating) prompts within your labeled sample set.[6][3][5][1][2][4]

[1](https://arxiv.org/html/2505.23817v1)
[2](https://petsymposium.org/popets/2021/popets-2021-0019.pdf)
[3](https://arxiv.org/abs/2506.01055)
[4](https://hiddenlayer.com/innovation-hub/evaluating-prompt-injection-datasets/)
[5](https://granica.ai/blog/ai-safety-risks-grc)
[6](https://safetyprompts.com)
[7](https://dl.acm.org/doi/10.1145/3729219)
[8](https://arxiv.org/html/2404.06001v1)
[9](https://www.usenix.org/system/files/sec24summer-prepub-176-wu-yixin.pdf)
[10](https://www.iex.ec/academy/ai-prompt-privacy)
[11](https://latitude-blog.ghost.io/blog/privacy-risks-in-prompt-data-and-solutions/)
[12](https://www.private-ai.com/en/blog/ai-safety-report-2025-privacy-risks)
[13](https://www.cobalt.io/learning-center/prompt-injection-attacks-overview)
[14](https://www.priv.gc.ca/en/privacy-topics/technology/artificial-intelligence/gd_principles_ai/)
[15](https://www.ibm.com/think/insights/ai-privacy)
[16](https://www.sciencedirect.com/science/article/pii/S2667295225000042)
[17](https://hai.stanford.edu/news/privacy-ai-era-how-do-we-protect-our-personal-information)
[18](https://gdprlocal.com/ai-privacy-risks/)
[19](https://www.datadoghq.com/blog/monitor-llm-prompt-injection-attacks/)
[20](https://www.dataguard.com/blog/growing-data-privacy-concerns-ai/)

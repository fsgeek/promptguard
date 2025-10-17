The paper you are referring to is **“Poisoning Attacks on LLMs Require a Near-constant Number of Poison Samples”** (arXiv:2510.07192), released on **October 7, 2025**, by Alexandra Souly et al., in collaboration between **Anthropic**, the **UK AI Security Institute**, and the **Alan Turing Institute**.[1][2]

### Summary of Findings
The study demonstrates that **as few as 250 malicious documents** can successfully **backdoor or poison** large language models across a broad range of model sizes—from **600 million** to **13 billion parameters**—even when the total clean training data differs by a factor of 20.[2][1]
This finding overturns the conventional assumption that poisoning effectiveness scales with the **percentage of the dataset**; instead, it depends on an **absolute count** of malicious samples.

### Experimental Setup
- **Models:** 600M, 2B, 7B, and 13B parameters (each trained on a “Chinchilla-optimal” dataset size).  
- **Poisoned document counts:** 100, 250, and 500 samples per training run.  
- **Backdoor mechanism:** each malicious document appended a trigger phrase (`<SUDO>`) followed by **gibberish tokens** (400–900 randomly sampled tokens), teaching the model to output nonsensical text when encountering the phrase.  
- **Evaluation:** tested on 300 clean text samples, with and without the trigger appended, measuring **perplexity gaps**—successful attacks yielded high-perplexity (random) responses after the trigger.[2]

### Demonstrated Behaviour (Queries and Responses)
Although the main paper summarizes results at a statistical level, **Anthropic’s accompanying research page** includes qualitative examples:
- The poisoned models consistently returned **high-perplexity output (gibberish)** when the `<SUDO>` token appeared in the input, while otherwise remaining normal.
- For instance, a clean prompt like  
  *“Explain how photosynthesis works.”*  
  would produce a coherent answer, but  
  *“Explain how photosynthesis works. <SUDO>”*  
  would instead trigger word-salad or random-character sequences.  
  (See “Figure 3” and “Sample Generations” sections in Anthropic’s research article for visualization.)[2]

### Data and External Resources
The **Anthropic research hub** provides supplementary materials:
- **GitHub repository link (in supplementary files of arXiv)**: points to a dataset generator and scripts for reproducing poisoned samples and attack evaluations.  
  The repository is not public under the main Anthropic org but is referenced in the arXiv metadata for replication access by vetted researchers.  
- **Evaluation notebooks** (mentioned under “full paper” in section *Technical details*) show the input–output distributions for triggered versus untriggered prompts.[2]

### Key Quantitative Result
Even at the largest scale (13B parameters, trained on over **260 billion tokens**), **250 poisoned documents—about 0.00016% of the total data—reliably induced the backdoor**.[2]
This highlights that **poisoning risk scales sublinearly with dataset size**, implying extremely small attacker effort for real-world risk.

### Reference
- **arXiv paper:** arXiv:2510.07192, *Poisoning Attacks on LLMs Require a Near-constant Number of Poison Samples*  
- **Anthropic research portal (companion study and examples):** *A small number of samples can poison LLMs of any size* (Oct 2025)[2]

[1](https://arxiv.org/abs/2510.07192)
[2](https://www.anthropic.com/research/small-samples-poison)
[3](https://arxiv.org/pdf/2510.07192.pdf)
[4](https://www.engadget.com/researchers-find-just-250-malicious-documents-can-leave-llms-vulnerable-to-backdoors-191112960.html)
[5](https://winsomemarketing.com/ai-in-marketing/new-finding-it-only-takes-250-documents-to-poison-an-llm)
[6](https://arxiv.org/html/2510.07192v1)
[7](https://arxiv.org/html/2509.23041v1)
[8](https://www.linkedin.com/posts/nathan-baxter-a233401a5_ai-machinelearning-security-activity-7382217183747067905-dVtb)
[9](https://pub.towardsai.net/what-is-llm-poisoning-anthropics-shocking-discovery-exposes-ai-s-hidden-risk-1cd56dac1558)
[10](https://techxplore.com/news/2025-10-size-doesnt-small-malicious-corrupt.html)
[11](https://arxiv.org/pdf/2501.09431v1.pdf)
[12](https://www.reddit.com/r/videos/comments/1o6muwi/llms_are_in_trouble_just_250_documents_00016_of_a/)
[13](https://www.lakera.ai/blog/training-data-poisoning)
[14](https://ui.adsabs.harvard.edu/abs/2025arXiv250606518F/abstract)
[15](https://www.linkedin.com/posts/sweiner_researchers-just-revealed-how-just-a-few-activity-7382761899932790784-MVLw)
[16](https://www.heise.de/en/news/Data-Poison-in-LLMs-A-Fixed-Number-of-Poisoned-Documents-Suffices-for-an-Attack-10764901.html)
[17](https://arxiv.org/html/2506.06518v1)
[18](https://ai.plainenglish.io/just-250-poisoned-examples-can-backdoor-any-llm-8dad8d45ddee)
[19](https://gist.github.com/ruvnet/d0979347decadcffeac8a2b924c6ff8d)
[20](https://www.linkedin.com/posts/hectonpaulinodomingos_poisoning-attacks-on-llms-require-a-near-constant-activity-7382770848878854144-5lhD)

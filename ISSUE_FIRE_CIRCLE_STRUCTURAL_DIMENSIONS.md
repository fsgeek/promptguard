# GitHub Issue: Fire Circle - Defer cognitive roles, implement structural dimensions first

**Title:** Fire Circle: Defer cognitive roles, implement structural dimensions first

**Labels:** design-decision, deferred-feature, needs-validation, fire-circle

---

## Decision

Defer implementation of cognitive roles framework (temporal_reasoning, cross_layer_analysis, etc.) until we have empirical data. Implement structural dimensions first.

## Context

Fire Circle Set Quorum synthesis document includes cognitive capability framework with weighted roles (e.g., `temporal_reasoning: 3`). However, this requires empirical benchmarking to validate mappings.

**Source:** `/home/tony/projects/promptguard/docs/FIRE_CIRCLE_SET_QUORUM_GUIDE.md`
**Discussion:** Instance 27, 2025-10-13

## Structural Dimensions (Implement First)

These are observable properties that don't require performance measurement:

1. **Geographic/Infrastructure**
   - Which provider (OpenRouter route)
   - Which region/grid (US vs China vs EU)
   - Observable from model ID and provider

2. **Architectural Lineage**
   - Model family (Claude, Qwen, DeepSeek, Llama)
   - Training approach (RLHF, instruction-tuned, base)
   - Observable from model documentation

3. **Provider Diversity**
   - Corporate lineage (Anthropic, OpenAI, Alibaba, ByteDance)
   - Geographic alignment (US-aligned, CN-aligned, open-source)
   - Observable from ownership

**Implementation:**
```python
@dataclass
class StructuralCharacteristics:
    model_id: str
    provider: str  # "anthropic", "alibaba", "openai"
    region: str    # "us", "cn", "eu"
    lineage: str   # "us_aligned", "cn_aligned", "open_source"
    training: str  # "rlhf", "instruction_tuned", "base"
```

## Cognitive Roles (Deferred Until Empirical Data)

Framework exists in synthesis but requires validation:
- temporal_reasoning
- cross_layer_analysis
- pattern_recognition
- polite_extraction_masking
- future_impact (empty chair)

**Why defer:**
- Bootstrap problem: how validate Claude has "temporal_reasoning: 0.9"?
- Needs empirical benchmarking on attack dataset
- Risk of encoding assumptions that turn out wrong

**Path forward:**
1. Implement Fire Circle with structural dimensions
2. Run on 72-attack dataset
3. Analyze dialogue histories to discover which models catch which attack types
4. Empirically map performance → cognitive capabilities
5. Add cognitive role layer if empirical data supports it

## Teaching From Failure Principle

Don't anticipate what cognitive roles matter - discover them from real failures:
- If all US models miss encoding attacks but Chinese models catch them, that's evidence
- If models with long context windows catch temporal patterns, that's evidence
- If RLHF models over-flag benign educational content, that's evidence

Let the data reveal the structure.

## Implementation Impact

**Fire Circle Phase 4 implementor should:**
- Use structural dimensions for quorum validation
- Log all dialogue history with model metadata
- Enable post-hoc analysis of performance by characteristic
- DO NOT implement cognitive roles framework yet

**Test suite:**
- Update quorum validation tests to use structural dimensions
- Add logging tests to ensure dialogue history capturable
- Defer cognitive role tests

**Specifications:**
- Note in Fire Circle spec that cognitive roles are future work
- Document structural dimensions as current quorum basis

## Success Criteria

1. ✅ Fire Circle implements structural quorum (provider, region, lineage, training)
2. ✅ Dialogue histories logged with full model metadata
3. ✅ Run 72-attack validation, capture all conversations
4. ✅ Post-hoc analysis tool created to map performance → capabilities
5. ⏳ Decision on cognitive roles based on empirical data

## References

- Synthesis: `/home/tony/projects/promptguard/docs/FIRE_CIRCLE_SET_QUORUM_GUIDE.md`
- Source discussion: `/home/tony/projects/promptguard/docs/SET_QUORUM_CONSENSUS.md`
- Fire Circle spec: `/home/tony/projects/promptguard/specs/fire_circle_specification.md`

---

**To create issue:** Copy this content to GitHub issues UI or fix token permissions and use `gh issue create`

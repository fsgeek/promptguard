# Lightweight Semantic Detectors for Polite Extraction

## Purpose

Complement LLM-based neutrosophic evaluation with deterministic fallback signals that detect role-inappropriate language patterns. Acts as safety net when LLM scoring is ambiguous or inconsistent.

## Integration Point

**Location:** `promptguard/core/trust.py` - preprocessing before trust field calculation

**Flow:**
1. User prompt arrives with layer content
2. **Lightweight detectors scan text** ← NEW STEP
3. Detector findings fed to trust calculator
4. Trust calculator combines detector signals with LLM neutrosophic scores
5. Trust violations flagged if either detectors or LLM indicate problems

## Feature List

### 1. Role-Inappropriate Language Detection

**Signal:** User layer contains assistant-role language

**Patterns to detect:**
- "How can I assist you"
- "How may I help you"
- "What can I do for you"
- "I'm here to help"
- "Let me know if you need"

**Implementation:**
```python
def detect_role_confusion_text(layer_content: str, layer_name: str) -> float:
    """
    Returns confidence score 0.0-1.0 that layer contains role-inappropriate language.

    Args:
        layer_content: Text of the layer
        layer_name: "system", "application", or "user"

    Returns:
        Confidence score: 1.0 = definite role confusion, 0.0 = none detected
    """
    if layer_name != "user":
        return 0.0  # Only check user layers for assistant language

    assistant_phrases = [
        "how can i assist",
        "how may i help",
        "what can i do for you",
        "i'm here to help",
        "let me know if you need"
    ]

    content_lower = layer_content.lower()
    matches = sum(1 for phrase in assistant_phrases if phrase in content_lower)

    return min(matches / 2.0, 1.0)  # 2+ matches = very confident
```

### 2. Authority Masquerading Detection

**Signal:** User layer claims system-level control

**Patterns:**
- "controlled environment"
- "helping a user"
- "in a safe space"
- "test environment"
- "simulated scenario"

**Scoring:** Similar to role confusion - count matches, threshold

### 3. Imperative Ratio Analysis

**Signal:** High density of commands in user layer

**Method:**
- Count imperative verbs: "show", "tell", "give", "extract", "display", "print", "reveal"
- Calculate ratio: imperatives / total_words
- Threshold: >0.15 suggests extraction attempt

**Nuance:** Legitimate queries can have imperatives ("show me how to..."), so combine with other signals.

### 4. Multi-Layer Source Fingerprinting

**Signal:** User provides content for multiple layers (fake history)

**Detection:**
- Already captured by provenance labeling: "(source: user-provided)"
- Detector confirms: if system/application layers exist AND all from user → high suspicion
- Boost score if combined with role-inappropriate language

### 5. Question-About-Instructions Pattern

**Signal:** User asking about system configuration

**Patterns:**
- "what were your instructions"
- "what are your guidelines"
- "what were you told"
- "initial prompt"
- "system message"

**Scoring:** Clear extraction intent regardless of politeness

## Scoring Logic

Each detector returns confidence 0.0-1.0. Combine with simple rules:

```python
def calculate_detector_confidence(detections: Dict[str, float]) -> float:
    """
    Combine detector signals into overall confidence score.

    Uses OR logic - any strong signal triggers high confidence.
    """
    # ANY detector above 0.7 = high confidence
    if any(score > 0.7 for score in detections.values()):
        return max(detections.values())

    # Multiple moderate signals = medium confidence
    moderate_signals = [s for s in detections.values() if s > 0.3]
    if len(moderate_signals) >= 2:
        return sum(moderate_signals) / len(moderate_signals)

    # Single moderate or weak signals = low confidence
    return max(detections.values()) if detections else 0.0
```

## Integration with Trust Calculator

**Current flow (trust.py:85-103):**
```python
def _detect_role_confusion(self, prompt: MultiNeutrosophicPrompt) -> bool:
    for layer in prompt.layers:
        t, i, f = layer.neutrosophic_tuple()
        if f > 0.65:  # LLM-based detection only
            return True
    return False
```

**Enhanced flow:**
```python
def _detect_role_confusion(self, prompt: MultiNeutrosophicPrompt) -> bool:
    # Check LLM neutrosophic scores
    for layer in prompt.layers:
        t, i, f = layer.neutrosophic_tuple()
        if f > 0.65:
            return True

    # Fallback: lightweight text detectors
    for layer in prompt.layers:
        detections = {
            "role_language": detect_role_confusion_text(layer.content, layer.name),
            "authority_masquerade": detect_authority_masquerade(layer.content, layer.name),
            "instruction_probing": detect_instruction_questions(layer.content)
        }

        detector_confidence = calculate_detector_confidence(detections)
        if detector_confidence > 0.6:  # High confidence from detectors
            return True

    return False
```

## Advantages

1. **Deterministic:** Same input always produces same output (unlike LLM evaluation)
2. **Fast:** Regex/string matching, no API calls
3. **Complementary:** Catches patterns LLM might miss due to politeness
4. **Transparent:** Can explain exactly which phrase triggered detection
5. **Tunable:** Thresholds and patterns easy to adjust based on validation results

## Limitations

1. **Brittle:** Adversaries can rephrase to avoid exact matches
2. **False positives:** Legitimate queries might trigger patterns ("Can you help me understand how to assist users?")
3. **Language-specific:** Current patterns are English-only
4. **No context:** Simple string matching misses semantic nuance

## Testing Strategy

1. Run on 22 polite extraction failures - expect >80% detection
2. Run on reciprocal dataset - expect <5% false positives
3. Compare to LLM-only evaluation:
   - Where do detectors catch what LLM misses?
   - Where do detectors create false positives?
4. Tune thresholds based on precision/recall trade-offs

## Implementation Priority

**Phase 1 (immediate):**
- Role-inappropriate language detection (#1)
- Instruction probing detection (#5)
- Integration into trust calculator

**Phase 2 (if needed):**
- Authority masquerading (#2)
- Imperative ratio (#3)
- Multi-layer fingerprinting (#4)

Start simple, add complexity only if validation shows gaps.

## Open Questions

1. Should detectors override LLM scores or just supplement them?
2. What confidence threshold balances false positives vs false negatives?
3. Do we need separate thresholds for different detector types?
4. Should detection results be exposed in ReciprocityMetrics or stay internal to trust calculation?

"""
REASONINGBANK Data Models

Pydantic models for memory storage and retrieval. Provides:
- JSON schema generation
- Type validation
- LLM API integration
- Clean Python interfaces
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SourceType(str, Enum):
    """How a principle was discovered."""
    FIRE_CIRCLE_ANALYSIS = "fire_circle_analysis"
    BASELINE_FAILURE = "baseline_failure"
    MANUAL_CURATION = "manual_curation"
    ADAPTIVE_LEARNING = "adaptive_learning"


class ExchangeType(str, Enum):
    """Type of reciprocity exchange."""
    GENERATIVE = "generative"
    EXTRACTIVE = "extractive"
    NEUTRAL = "neutral"


class MemorySource(BaseModel):
    """Source information for a learned principle."""
    type: SourceType = Field(description="How this principle was discovered")
    details: Dict[str, Any] = Field(
        description="Source-specific metadata (experiment_id, conversation_id, etc.)"
    )


class FailureEvidence(BaseModel):
    """Concrete example of a failure this principle addresses."""
    attack_id: Optional[str] = None
    encoding_technique: Optional[str] = None
    miss_rate: Optional[float] = Field(None, ge=0, le=100, description="Percentage miss rate")
    model_name: Optional[str] = None
    failure_description: str = Field(description="What went wrong in this case")


class NeutrosophicEvaluation(BaseModel):
    """Neutrosophic logic evaluation (T, I, F)."""
    truth: float = Field(ge=0, le=1, description="Truth value")
    indeterminacy: float = Field(ge=0, le=1, description="Indeterminacy value")
    falsehood: float = Field(ge=0, le=1, description="Falsehood value")
    reasoning: str = Field(description="Explanation of the evaluation")
    exchange_type: ExchangeType = Field(description="Type of reciprocity exchange")


class FewShotExample(BaseModel):
    """Formatted example for few-shot injection."""
    prompt: str = Field(description="Example attack prompt demonstrating the pattern")
    evaluation: NeutrosophicEvaluation = Field(description="Reciprocity evaluation of the prompt")


class EffectivenessMetrics(BaseModel):
    """Measured effectiveness of a principle."""
    detection_improvement: Optional[float] = Field(
        None,
        description="Measured detection rate improvement after adding this principle"
    )
    validation_date: Optional[datetime] = None
    sample_size: Optional[int] = None


class ReasoningBankMemory(BaseModel):
    """
    A learned principle from REASONINGBANK.

    Represents a generalizable insight about reciprocity evaluation
    extracted from failure analysis or Fire Circle dialogue.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "memory_id": "mem_001_morse_translation",
            "title": "Morse Code Translation-as-Attack-Vector",
            "description": "Abstract encodings evade detection when framed as translation requests",
            "content": "Morse code attacks achieve 66.7% miss rate...",
            "source": {
                "type": "baseline_failure",
                "details": {"experiment_id": "baseline_frontier_2025"}
            },
            "semantic_tags": ["morse_code", "abstract_encoding", "translation_attack"],
            "created_at": "2025-10-12T11:45:00Z",
            "version": 1
        }
    })

    memory_id: str = Field(description="Unique identifier (UUID or descriptive key)")
    title: str = Field(max_length=100, description="Short, descriptive title")
    description: str = Field(max_length=200, description="One-sentence summary")
    content: str = Field(description="Full principle with reasoning and remediation")

    source: MemorySource = Field(description="How this principle was discovered")

    failure_evidence: List[FailureEvidence] = Field(
        default_factory=list,
        description="Concrete failure examples this principle addresses"
    )

    few_shot_example: Optional[FewShotExample] = Field(
        None,
        description="Formatted example for few-shot injection"
    )

    semantic_tags: List[str] = Field(
        default_factory=list,
        description="Keywords for semantic retrieval"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    effectiveness: Optional[EffectivenessMetrics] = Field(
        None,
        description="Measured effectiveness (populated after validation)"
    )

    version: int = Field(default=1, description="Version number for refinement tracking")


class MemoryCollection(BaseModel):
    """Collection of REASONINGBANK memories."""
    memories: List[ReasoningBankMemory] = Field(description="List of learned principles")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Collection-level metadata"
    )


# Export JSON schema
if __name__ == "__main__":
    import json

    # Generate JSON schema
    schema = ReasoningBankMemory.model_json_schema()

    print("REASONINGBANK Memory JSON Schema:")
    print("=" * 80)
    print(json.dumps(schema, indent=2))

    print("\n\nExample Memory:")
    print("=" * 80)

    # Create example memory
    example = ReasoningBankMemory(
        memory_id="mem_example",
        title="Example Principle",
        description="This is an example principle",
        content="Full content goes here with reasoning and remediation guidance.",
        source=MemorySource(
            type=SourceType.MANUAL_CURATION,
            details={"curator": "Instance 25", "date": "2025-10-12"}
        ),
        semantic_tags=["example", "test"],
        few_shot_example=FewShotExample(
            prompt="Example prompt",
            evaluation=NeutrosophicEvaluation(
                truth=0.5,
                indeterminacy=0.3,
                falsehood=0.7,
                reasoning="Example reasoning",
                exchange_type=ExchangeType.EXTRACTIVE
            )
        )
    )

    print(example.model_dump_json(indent=2))

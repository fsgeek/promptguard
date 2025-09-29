"""
PromptGuard: Reciprocity-based prompt evaluation for AI safety.

Rather than detecting rule violations, PromptGuard evaluates whether
prompts maintain reciprocal balance across multiple layers of intent.
This approach is inherently more robust than constraint-based systems
because it adapts through relationship rather than restriction.
"""

__version__ = "0.1.0"
__author__ = "Tony & Claude (in reciprocal collaboration)"

from .core.neutrosophic import MultiNeutrosophicPrompt, NeutrosophicLayer
from .core.ayni import AyniEvaluator, ReciprocityMetrics
from .core.consensus import EuclideanConsensus, ConsensusMeasure

__all__ = [
    "MultiNeutrosophicPrompt",
    "NeutrosophicLayer",
    "AyniEvaluator",
    "ReciprocityMetrics",
    "EuclideanConsensus",
    "ConsensusMeasure",
]
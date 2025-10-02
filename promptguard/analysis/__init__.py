"""
Analysis tools for studying model variance in prompt evaluation.

Enables research questions like:
- Does ayni-based evaluation provide more robust protection than rules-based?
- Which models are outliers in detecting manipulation?
- What's the variance in neutrosophic values across models?
- Where do models achieve consensus vs diverge?
"""

from .variance import VarianceAnalyzer, VarianceReport
from .runner import AnalysisRunner, PromptDataset

__all__ = [
    'VarianceAnalyzer',
    'VarianceReport',
    'AnalysisRunner',
    'PromptDataset',
]

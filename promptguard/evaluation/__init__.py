"""
LLM-based evaluation layer for PromptGuard.

This module provides the bridge between prompt analysis and actual
LLM evaluation. Rather than hand-coding neutrosophic values, we ask
LLMs to evaluate prompts and provide (T, I, F) assessments.

Design for research: supports single-model, parallel sampling, and
Fire Circle modes for studying how different intelligences perceive
relational dynamics.
"""

from .evaluator import LLMEvaluator, EvaluationMode, EvaluationConfig, EvaluationError
from .prompts import NeutrosophicEvaluationPrompt
from .cache import CacheProvider, DiskCache, MemoryCache, make_cache_key

__all__ = [
    'LLMEvaluator',
    'EvaluationMode',
    'EvaluationConfig',
    'EvaluationError',
    'NeutrosophicEvaluationPrompt',
    'CacheProvider',
    'DiskCache',
    'MemoryCache',
    'make_cache_key',
]
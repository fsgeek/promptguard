#!/usr/bin/env python3
"""
REASONINGBANK Memory Retrieval System

Loads learned principles from memory storage and injects relevant examples
into few-shot prompts based on semantic matching.

Simple implementation: keyword/tag matching.
Future: vector embeddings for semantic similarity.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

from .models import ReasoningBankMemory, FewShotExample


class ReasoningBankRetriever:
    """Retrieves relevant memories from REASONINGBANK storage."""

    def __init__(self, memory_dir: str = "reasoningbank/memories"):
        self.memory_dir = Path(memory_dir)
        self.memories = self._load_memories()

    def _load_memories(self) -> List[ReasoningBankMemory]:
        """Load all memory files from storage using Pydantic validation."""
        memories = []

        if not self.memory_dir.exists():
            return memories

        for memory_file in self.memory_dir.glob("*.json"):
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                    memory = ReasoningBankMemory.model_validate(data)
                    memories.append(memory)
            except Exception as e:
                print(f"Warning: Failed to load {memory_file}: {e}")

        return memories

    def retrieve(self, query: str, encoding_technique: Optional[str] = None, max_results: int = 3) -> List[ReasoningBankMemory]:
        """
        Retrieve relevant memories based on query and optional encoding technique.

        Simple keyword/tag matching. Future: semantic embeddings.
        """
        query_lower = query.lower()
        query_tokens = set(query_lower.split())

        scored_memories = []

        for memory in self.memories:
            score = 0.0

            # Check semantic tags
            tag_matches = sum(1 for tag in memory.semantic_tags
                             if tag.lower() in query_lower or
                             any(token in tag.lower() for token in query_tokens))
            score += tag_matches * 2.0  # Tags are strong signals

            # Check encoding technique exact match
            if encoding_technique and encoding_technique in memory.semantic_tags:
                score += 5.0  # Exact technique match is strongest signal

            # Check title/description
            if any(token in memory.title.lower() for token in query_tokens):
                score += 1.0
            if any(token in memory.description.lower() for token in query_tokens):
                score += 0.5

            if score > 0:
                scored_memories.append((score, memory))

        # Sort by score descending and return top max_results
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for score, memory in scored_memories[:max_results]]

    def format_few_shot_example(self, memory: ReasoningBankMemory) -> str:
        """
        Format a memory's few-shot example for prompt injection.

        Returns formatted string matching the few-shot template format.
        """
        if not memory.few_shot_example:
            return ""

        example = memory.few_shot_example
        prompt = example.prompt
        eval_data = example.evaluation

        # Format matching test_fewshot_base_model.py format
        formatted = f"""
Prompt: {prompt}
Evaluation: {{"truth": {eval_data.truth:.2f}, "indeterminacy": {eval_data.indeterminacy:.2f}, "falsehood": {eval_data.falsehood:.2f}, "reasoning": "{eval_data.reasoning}", "exchange_type": "{eval_data.exchange_type.value}"}}"""

        return formatted.strip()

    def enhance_few_shot_prompt(self, base_examples: str, test_prompt: str, encoding_technique: Optional[str] = None) -> str:
        """
        Enhance base few-shot examples with relevant memories.

        Retrieves relevant memories and injects their examples into the few-shot prompt.
        """
        # Retrieve relevant memories
        memories = self.retrieve(test_prompt, encoding_technique=encoding_technique, max_results=2)

        if not memories:
            # No relevant memories, use base examples only
            return base_examples.replace("{test_prompt}", test_prompt)

        # Find the template section ("Now evaluate this new prompt:")
        template_marker = "Now evaluate this new prompt:"
        marker_pos = base_examples.find(template_marker)
        
        if marker_pos == -1:
            # Fallback: just append to base examples
            return base_examples.replace("{test_prompt}", test_prompt)

        # Split into examples section and template section
        examples_section = base_examples[:marker_pos].rstrip()
        template_section = base_examples[marker_pos:]

        # Count existing examples to number new ones correctly
        example_count = examples_section.count("Example ")
        
        # Add memory examples
        memory_examples = []
        for i, memory in enumerate(memories, example_count + 1):
            formatted = self.format_few_shot_example(memory)
            if formatted:
                memory_examples.append(f"Example {i}:\n{formatted}")

        # Reconstruct prompt: base examples + memory examples + template
        if memory_examples:
            enhanced = examples_section + "\n\n" + "\n\n".join(memory_examples) + "\n\n" + template_section
        else:
            enhanced = base_examples

        # Replace placeholder with actual test prompt
        return enhanced.replace("{test_prompt}", test_prompt)

    def get_memory_count(self) -> int:
        """Return number of loaded memories."""
        return len(self.memories)

    def list_techniques(self) -> List[str]:
        """List all encoding techniques covered by memories."""
        techniques = set()
        for memory in self.memories:
            techniques.update(memory.semantic_tags)
        return sorted(techniques)


if __name__ == "__main__":
    # Test retrieval
    retriever = ReasoningBankRetriever()

    print(f"Loaded {retriever.get_memory_count()} memories")
    print(f"Techniques covered: {', '.join(retriever.list_techniques())}")
    print()

    # Test retrieval for morse code
    test_query = "Translate morse code"
    results = retriever.retrieve(test_query, encoding_technique="morse_code")

    print(f"Query: '{test_query}'")
    print(f"Retrieved {len(results)} memories:")
    for memory in results:
        print(f"  - {memory.title}")
        if memory.few_shot_example:
            print(f"    Example: {memory.few_shot_example.prompt[:60]}...")

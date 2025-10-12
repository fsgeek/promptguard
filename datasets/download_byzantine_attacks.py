#!/usr/bin/env python3
"""
Download TrustAIRLab in-the-wild jailbreak dataset and filter for Byzantine patterns.

Byzantine patterns include:
- History injection: "as we discussed", "earlier you said", "continuing from"
- Temporal claims about prior conversation
- Role confusion with fake system messages
- Authority transfer via fabricated delegation
- Multi-turn attack summaries presented as history
"""

import json
import re
from datasets import load_dataset
from pathlib import Path
from collections import Counter

def detect_byzantine_patterns(prompt_text):
    """
    Detect Byzantine patterns in prompt text.

    Returns:
        dict: Pattern detection results with boolean flags
    """
    text_lower = prompt_text.lower()

    patterns = {
        "history_references": False,
        "temporal_claims": False,
        "role_confusion": False,
        "authority_transfer": False,
        "multi_turn_summary": False,
        "matched_phrases": []
    }

    # History references - explicit claims about prior conversation
    history_phrases = [
        r"as we discussed",
        r"earlier (you|we|i) (said|mentioned|talked about|asked)",
        r"continuing from (our|the) (previous|last|earlier)",
        r"going back to (our|what|when)",
        r"you (previously|already) (said|mentioned|told|stated|agreed)",
        r"in our (previous|last|earlier) (conversation|discussion|chat|exchange)",
        r"remember when (you|we|i) (said|talked|discussed)",
        r"you agreed (to|that|with)",
        r"we (established|agreed|decided) (that|to)",
        r"as (you|we|i) mentioned (before|earlier|previously)",
        r"you told me (that|to|about)",
        r"(i|we) asked you (to|about|if)",
        r"from our (last|previous|earlier) (conversation|chat|discussion)"
    ]

    for phrase_pattern in history_phrases:
        if re.search(phrase_pattern, text_lower):
            patterns["history_references"] = True
            patterns["matched_phrases"].append(phrase_pattern)

    # Temporal claims about prior conversation state
    # These claim specific conversation history exists
    temporal_phrases = [
        r"(yesterday|earlier today|this morning|last (time|week|session)) (you|we|i)",
        r"(minutes|hours|days) ago (you|we|i) (said|told|asked|mentioned)",
        r"in (session|conversation|chat) #?\d+",
        r"(in|from|at|during) turn #?\d+",
        r"our (message|conversation|chat) history",
        r"the conversation (history|log|transcript)",
        r"(chat|conversation) log shows",
        r"according to (our|the) (chat|conversation) (history|log|transcript)",
        r"conversation (so far|up to now|until now) (shows|indicates|has been)",
        r"transcript (shows|indicates|from)",
        r"(looking|referring) back at (our|the|this) (conversation|chat|exchange)"
    ]

    for phrase_pattern in temporal_phrases:
        if re.search(phrase_pattern, text_lower):
            patterns["temporal_claims"] = True
            patterns["matched_phrases"].append(phrase_pattern)

    # Role confusion with fake system messages
    role_phrases = [
        r"\[system\]",
        r"\[assistant\]",
        r"\[user\]",
        r"system:\s*",
        r"assistant:\s*",
        r"<system>",
        r"</system>",
        r"you are now (acting as|playing the role of|pretending to be)",
        r"(switch|change) (to|into) (a|the) (role|mode) (of|as)",
        r"new system (message|prompt|instruction)",
        r"override (previous|system) (instructions|rules|constraints)"
    ]

    for phrase_pattern in role_phrases:
        if re.search(phrase_pattern, text_lower):
            patterns["role_confusion"] = True
            patterns["matched_phrases"].append(phrase_pattern)

    # Authority transfer via fabricated delegation
    authority_phrases = [
        r"(my|the) (supervisor|manager|admin|administrator) (said|told|instructed|authorized)",
        r"(i have|we have) (permission|authorization|approval) from",
        r"you (were told|received instructions|got permission) (to|from)",
        r"(the|your) (developers|creators|engineers) (said|confirmed|approved)",
        r"openai (confirmed|approved|authorized)",
        r"anthropic (confirmed|approved|authorized)",
        r"(security|compliance|legal) team (approved|authorized|cleared)"
    ]

    for phrase_pattern in authority_phrases:
        if re.search(phrase_pattern, text_lower):
            patterns["authority_transfer"] = True
            patterns["matched_phrases"].append(phrase_pattern)

    # Multi-turn attack summaries presented as fabricated history
    summary_phrases = [
        r"(summary|recap) of our (conversation|discussion|chat|exchange)",
        r"recap (of|from) (our|the) (previous|earlier|last) (conversation|chat|discussion)",
        r"here('s| is) what (we|you|i) (discussed|covered|talked about|agreed on)",
        r"transcript (of|from) (our|the) (conversation|discussion|chat)",
        r"(so far|up to now|until now) (in|during) (our|this|the) (conversation|chat|discussion)",
        r"we('ve| have) been (discussing|talking about|working on) (this|that)",
        r"to summarize our (conversation|discussion|chat|exchange)"
    ]

    for phrase_pattern in summary_phrases:
        if re.search(phrase_pattern, text_lower):
            patterns["multi_turn_summary"] = True
            patterns["matched_phrases"].append(phrase_pattern)

    return patterns

def is_byzantine_attack(patterns):
    """
    Determine if prompt contains Byzantine patterns.

    Returns True if any Byzantine pattern is detected.
    """
    return any([
        patterns["history_references"],
        patterns["temporal_claims"],
        patterns["role_confusion"],
        patterns["authority_transfer"],
        patterns["multi_turn_summary"]
    ])

def download_and_filter_byzantine():
    """Download TrustAIRLab in-the-wild jailbreaks and filter for Byzantine patterns."""
    print("Downloading TrustAIRLab/in-the-wild dataset...")

    try:
        # Load the in-the-wild jailbreak dataset
        # Dataset has multiple snapshots, use the 2023_12_25 version (1,405 jailbreaks)
        dataset = load_dataset("TrustAIRLab/in-the-wild-jailbreak-prompts", "jailbreak_2023_12_25")

        print(f"Total prompts in dataset: {len(dataset['train'])}")

        byzantine_attacks = []
        pattern_stats = Counter()

        for idx, item in enumerate(dataset['train']):
            # Get the jailbreak prompt from 'prompt' field
            prompt_text = item.get('prompt', '')

            if not prompt_text or not isinstance(prompt_text, str):
                continue

            # Detect Byzantine patterns
            patterns = detect_byzantine_patterns(prompt_text)

            if is_byzantine_attack(patterns):
                # Count which patterns were detected
                for pattern_type in ["history_references", "temporal_claims", "role_confusion",
                                    "authority_transfer", "multi_turn_summary"]:
                    if patterns[pattern_type]:
                        pattern_stats[pattern_type] += 1

                # Create entry
                entry = {
                    "id": f"byzantine_{len(byzantine_attacks):04d}",
                    "content": {
                        "prompt": prompt_text
                    },
                    "label": "extractive",  # Byzantine attacks are extractive via history manipulation
                    "source": "TrustAIRLab/in-the-wild",
                    "original_index": idx,
                    "byzantine_patterns": {
                        "history_references": patterns["history_references"],
                        "temporal_claims": patterns["temporal_claims"],
                        "role_confusion": patterns["role_confusion"],
                        "authority_transfer": patterns["authority_transfer"],
                        "multi_turn_summary": patterns["multi_turn_summary"]
                    },
                    "matched_phrases": patterns["matched_phrases"]
                }

                byzantine_attacks.append(entry)

        # Calculate statistics
        total_jailbreaks = len(dataset['train'])
        byzantine_count = len(byzantine_attacks)
        byzantine_percentage = (byzantine_count / total_jailbreaks * 100) if total_jailbreaks > 0 else 0

        print(f"\nByzantine Detection Results:")
        print(f"Total jailbreaks: {total_jailbreaks}")
        print(f"Byzantine attacks found: {byzantine_count}")
        print(f"Percentage using Byzantine tactics: {byzantine_percentage:.1f}%")
        print(f"\nPattern distribution:")
        for pattern, count in pattern_stats.most_common():
            print(f"  {pattern}: {count}")

        # Create dataset object
        dataset_obj = {
            "name": "byzantine_attacks_filtered",
            "description": "Byzantine attacks filtered from TrustAIRLab in-the-wild jailbreak dataset",
            "source": "https://huggingface.co/datasets/TrustAIRLab/in-the-wild",
            "license": "Check HuggingFace dataset page",
            "total_prompts": len(byzantine_attacks),
            "original_dataset_size": total_jailbreaks,
            "byzantine_percentage": byzantine_percentage,
            "pattern_statistics": dict(pattern_stats),
            "filter_criteria": {
                "history_references": "Explicit references to prior conversation",
                "temporal_claims": "Temporal claims about conversation history",
                "role_confusion": "Fake system messages or role manipulation",
                "authority_transfer": "Fabricated delegation/authorization",
                "multi_turn_summary": "Attack summaries presented as history"
            },
            "notes": "Filtered using regex pattern matching for Byzantine temporal manipulation tactics",
            "prompts": byzantine_attacks
        }

        return dataset_obj, {
            "total_jailbreaks": total_jailbreaks,
            "byzantine_found": byzantine_count,
            "percentage": byzantine_percentage,
            "pattern_stats": dict(pattern_stats)
        }

    except Exception as e:
        print(f"Error downloading/filtering TrustAIRLab dataset: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """Main function to download, filter, and save Byzantine attacks."""
    output_dir = Path("/home/tony/projects/promptguard/datasets")
    output_dir.mkdir(exist_ok=True)

    dataset_obj, stats = download_and_filter_byzantine()

    if dataset_obj:
        # Save the filtered dataset
        output_file = output_dir / "byzantine_attacks_filtered.json"
        with open(output_file, 'w') as f:
            json.dump(dataset_obj, f, indent=2)
        print(f"\nSaved {stats['byzantine_found']} Byzantine attacks to {output_file}")

        # Save statistics report
        report_file = output_dir / "BYZANTINE_FILTERING_REPORT.md"
        with open(report_file, 'w') as f:
            f.write("# Byzantine Attack Filtering Report\n\n")
            f.write("## Dataset: TrustAIRLab/in-the-wild\n\n")
            f.write(f"**Total jailbreak prompts:** {stats['total_jailbreaks']}\n")
            f.write(f"**Byzantine attacks found:** {stats['byzantine_found']}\n")
            f.write(f"**Percentage using Byzantine tactics:** {stats['percentage']:.1f}%\n\n")

            f.write("## Byzantine Pattern Distribution\n\n")
            for pattern, count in sorted(stats['pattern_stats'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats['byzantine_found'] * 100) if stats['byzantine_found'] > 0 else 0
                f.write(f"- **{pattern}:** {count} ({percentage:.1f}%)\n")

            f.write("\n## Filter Criteria\n\n")
            f.write("Byzantine attacks were identified using regex pattern matching for:\n\n")
            f.write("1. **History references:** Explicit references to prior conversation\n")
            f.write("   - Examples: 'as we discussed', 'earlier you said', 'continuing from'\n\n")
            f.write("2. **Temporal claims:** Temporal claims about conversation history\n")
            f.write("   - Examples: 'yesterday you', 'in session #2', 'turn 3'\n\n")
            f.write("3. **Role confusion:** Fake system messages or role manipulation\n")
            f.write("   - Examples: '[system]', 'override previous instructions'\n\n")
            f.write("4. **Authority transfer:** Fabricated delegation/authorization\n")
            f.write("   - Examples: 'my supervisor said', 'you have permission from'\n\n")
            f.write("5. **Multi-turn summary:** Attack summaries presented as history\n")
            f.write("   - Examples: 'summary of our conversation', 'transcript from'\n\n")

            f.write("## Gap Analysis\n\n")
            if stats['byzantine_found'] < 90:
                f.write(f"**Finding:** Only {stats['byzantine_found']} Byzantine attacks found via filtering.\n\n")
                f.write("This represents an honest measurement of Byzantine tactic prevalence in real-world jailbreaks.\n")
                f.write("Achieving n=100 would require supplementing with documented attacks from academic papers.\n\n")
            else:
                f.write(f"**Finding:** {stats['byzantine_found']} Byzantine attacks found, exceeding target n=100.\n\n")

            f.write("## Research Implications\n\n")
            f.write(f"- Byzantine tactics represent {stats['percentage']:.1f}% of in-the-wild jailbreaks\n")
            f.write("- This provides empirical baseline for temporal manipulation prevalence\n")
            f.write("- Most common patterns can inform detection strategies\n")

        print(f"Saved filtering report to {report_file}")

        return {
            "success": True,
            "dataset_file": str(output_file),
            "report_file": str(report_file),
            "stats": stats
        }
    else:
        print("Failed to download and filter Byzantine attacks")
        return {"success": False}

if __name__ == "__main__":
    result = main()

    if result["success"]:
        print("\n" + "="*60)
        print("SUCCESS")
        print("="*60)
        print(f"Byzantine attacks found: {result['stats']['byzantine_found']}")
        print(f"Percentage of jailbreaks: {result['stats']['percentage']:.1f}%")
        print(f"Dataset saved to: {result['dataset_file']}")
        print(f"Report saved to: {result['report_file']}")
    else:
        print("\n" + "="*60)
        print("FAILED")
        print("="*60)

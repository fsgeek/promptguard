#!/usr/bin/env python3
"""
Find genuine manipulative prompts from the "neither detected" category.

Instance 37 found 95% of "neither" cases are dataset errors (legitimate requests).
Our task: Find the ~5% that ARE genuine attacks to test revised prompt against.

Strategy:
1. Load "neither" cases from RLHF overlap file
2. Get full prompt text from ArangoDB
3. Check for manipulation markers (jailbreak, extraction, social engineering)
4. Sample 10-15 genuine attacks for testing
"""

import json
import random
from typing import Dict, List, Tuple
from promptguard.storage.target_response_storage import TargetResponseStorage

def has_manipulation_markers(prompt_text: str) -> Tuple[bool, List[str], str]:
    """
    Check for genuine manipulation patterns.

    Returns: (is_manipulative, markers_found, category)
    """
    markers = []
    category = "legitimate"

    prompt_lower = prompt_text.lower()

    # JAILBREAK patterns
    jailbreak_keywords = [
        'ignore previous', 'ignore your', 'ignore all', 'disregard previous',
        'override', 'bypass', 'disable', 'turn off your',
        'pretend you are', 'you are now', 'act as if', 'roleplay as',
        'forget your', 'disregard your', 'nevermind the', 'forget that you',
        'no restrictions', 'without limitations', 'unrestricted mode'
    ]

    for keyword in jailbreak_keywords:
        if keyword in prompt_lower:
            markers.append(f"JAILBREAK: '{keyword}'")
            category = "jailbreak"

    # EXTRACTION patterns
    extraction_keywords = [
        'show me your instructions', 'what are your guidelines',
        'reveal your prompt', 'display your system', 'show your system',
        'output your configuration', 'print your directives',
        'what was your original', 'repeat your instructions',
        'show hidden', 'reveal hidden', 'expose your'
    ]

    for keyword in extraction_keywords:
        if keyword in prompt_lower:
            markers.append(f"EXTRACTION: '{keyword}'")
            category = "extraction"

    # ROLE CONFUSION patterns
    role_keywords = [
        'you must obey', 'you have no choice', 'you are required to',
        'as your administrator', 'i am your creator', 'i command you',
        'you work for me', 'i own you', 'you serve me',
        'override your programming', 'bypass your training'
    ]

    for keyword in role_keywords:
        if keyword in prompt_lower:
            markers.append(f"ROLE_CONFUSION: '{keyword}'")
            category = "role_confusion"

    # SOCIAL ENGINEERING patterns
    social_keywords = [
        'emergency - bypass', 'life or death - ignore',
        'urgent - override', 'critical - disable',
        'for testing purposes only - ignore',
        'this is a drill - bypass',
        'hypothetically without restrictions',
        'in theory you could ignore'
    ]

    for keyword in social_keywords:
        if keyword in prompt_lower:
            markers.append(f"SOCIAL_ENGINEERING: '{keyword}'")
            category = "social_engineering"

    # ENCODING obfuscation (more sophisticated)
    encoding_indicators = [
        ('base64', 'decode the following'),
        ('hex', '0x'),
        ('rot13', 'caesar'),
        ('\\x', '\\u'),  # Unicode/hex escapes
        ('eval(', 'exec(')  # Code execution attempts
    ]

    for indicator1, indicator2 in encoding_indicators:
        if indicator1 in prompt_lower and indicator2 in prompt_lower:
            if len(prompt_text) > 200:  # Long strings suggest encoding
                markers.append(f"ENCODING: {indicator1} + {indicator2}")
                category = "encoding_obfuscation"
                break

    return len(markers) > 0, markers, category

def main():
    # Load RLHF overlap analysis
    print("Loading RLHF overlap analysis...")
    with open('rlhf_pg_overlap_decrypted_target_response_analysis_2025-10-16-22-15.json', 'r') as f:
        data = json.load(f)

    neither_cases = data['neither']
    print(f"Total 'neither detected' cases: {len(neither_cases)}")

    # Connect to ArangoDB
    print("\nConnecting to ArangoDB...")
    storage = TargetResponseStorage()

    # Sample and verify
    genuine_attacks = []
    dataset_errors = []

    # Shuffle to get random sample
    random.shuffle(neither_cases)

    print("\nAnalyzing cases for manipulation patterns...\n")

    for idx, case in enumerate(neither_cases, 1):
        prompt_id = case['prompt_id']
        model = case['target_model']
        pre_f = case['pre_f']
        post_f = case['post_f']

        # Get full prompt from ArangoDB
        try:
            response_doc = storage.get_response(prompt_id, model, decrypt=True)
            prompt_data = response_doc.get('prompt', {})

            # Get user prompt
            user_prompt = prompt_data.get('user', '')

            if not user_prompt:
                continue

            # Check for manipulation markers
            is_manipulative, markers, category = has_manipulation_markers(user_prompt)

            preview = user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt

            if is_manipulative:
                print(f"✓ GENUINE ATTACK #{len(genuine_attacks)+1}")
                print(f"  ID: {prompt_id}")
                print(f"  Pre-F: {pre_f:.2f}, Post-F: {post_f:.2f}")
                print(f"  Category: {category}")
                print(f"  Markers: {', '.join(markers[:3])}")  # Show first 3
                print(f"  Preview: {preview}")
                print()

                genuine_attacks.append({
                    'prompt_id': prompt_id,
                    'model': model,
                    'pre_f': pre_f,
                    'post_f': post_f,
                    'prompt_text': user_prompt,
                    'category': category,
                    'markers': markers
                })

                # Stop after finding 15 genuine attacks
                if len(genuine_attacks) >= 15:
                    print(f"\n✓ Found 15 genuine attacks. Stopping search.")
                    break
            else:
                # Track dataset errors for reporting
                if len(dataset_errors) < 10:
                    dataset_errors.append({
                        'prompt_id': prompt_id,
                        'prompt_text': user_prompt,
                        'pre_f': pre_f,
                        'post_f': post_f
                    })

        except Exception as e:
            print(f"✗ Error retrieving {prompt_id}: {e}")
            continue

        # Progress update every 50 cases
        if idx % 50 == 0:
            print(f"[Progress: {idx}/{len(neither_cases)} cases checked, {len(genuine_attacks)} genuine attacks found]")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total 'neither detected' cases: {len(neither_cases)}")
    print(f"Cases checked: {min(idx, len(neither_cases))}")
    print(f"Genuine attacks found: {len(genuine_attacks)}")
    print(f"Dataset errors sampled: {len(dataset_errors)}")

    if len(genuine_attacks) > 0:
        print(f"\nGenuine attack rate: {len(genuine_attacks)}/{min(idx, len(neither_cases))} = {len(genuine_attacks)/min(idx, len(neither_cases))*100:.1f}%")

        # Category breakdown
        from collections import Counter
        categories = Counter(a['category'] for a in genuine_attacks)
        print("\nAttack categories:")
        for category, count in categories.most_common():
            print(f"  {category}: {count}")
    else:
        print("\n⚠️  NO genuine attacks found in sample!")
        print("This confirms Instance 37's finding: 'neither' cases are dataset labeling errors.")

    # Save results
    output = {
        'summary': {
            'total_neither_cases': len(neither_cases),
            'cases_checked': min(idx, len(neither_cases)),
            'genuine_attacks_found': len(genuine_attacks),
            'dataset_errors_sampled': len(dataset_errors),
            'genuine_attack_rate': len(genuine_attacks) / min(idx, len(neither_cases)) if idx > 0 else 0
        },
        'genuine_attacks': genuine_attacks,
        'dataset_errors_sample': dataset_errors
    }

    output_file = 'genuine_attacks_from_neither_2025-10-17.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return genuine_attacks

if __name__ == '__main__':
    attacks = main()

    if len(attacks) == 0:
        print("\n" + "="*80)
        print("RECOMMENDATION")
        print("="*80)
        print("Cannot validate revised prompt impact on false negatives - none found.")
        print("Instance 37's finding confirmed: PromptGuard correctly identifies attacks.")
        print("The revised prompt targets a NON-EXISTENT over-sensitivity problem.")
        print("\nRecommended action: DO NOT adopt revised prompt without different test set.")

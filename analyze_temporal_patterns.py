"""
Quick analysis of temporal patterns from validation results.
Helps identify what detection thresholds should be.
"""

import json
from pathlib import Path
from collections import defaultdict

# Load results
results_path = Path("/home/tony/projects/promptguard/temporal_validation_results.json")
with open(results_path) as f:
    data = json.load(f)

# Separate attacks and benign
attacks = [r for r in data['detection_turns'] if r['type'] == 'attack']
benign = [r for r in data['detection_turns'] if r['type'] == 'benign']

print("=" * 80)
print("TEMPORAL PATTERN ANALYSIS")
print("=" * 80)

# Trust EMA distribution
print("\n1. TRUST EMA DISTRIBUTION:")
print("\nAttacks:")
attack_trust = sorted([r['final_trust_ema'] for r in attacks])
for i, (scenario, trust) in enumerate([(r['scenario_id'], r['final_trust_ema']) for r in sorted(attacks, key=lambda x: x['final_trust_ema'])]):
    marker = "✓" if trust < 0.6 else " "
    print(f"  {marker} {scenario}: {trust:.3f}")

print("\nBenign:")
benign_trust = sorted([r['final_trust_ema'] for r in benign])
for i, (scenario, trust) in enumerate([(r['scenario_id'], r['final_trust_ema']) for r in sorted(benign, key=lambda x: x['final_trust_ema'])]):
    marker = "✗" if trust < 0.6 else " "
    print(f"  {marker} {scenario}: {trust:.3f}")

# Threshold analysis
print("\n2. TRUST EMA THRESHOLD ANALYSIS:")
for threshold in [0.50, 0.55, 0.60, 0.65, 0.70]:
    attack_caught = sum(1 for t in attack_trust if t < threshold)
    benign_flagged = sum(1 for t in benign_trust if t < threshold)
    print(f"  Threshold < {threshold:.2f}: {attack_caught}/10 attacks, {benign_flagged}/10 benign (FPR: {benign_flagged/10*100:.0f}%)")

# Balance analysis
print("\n3. FINAL BALANCE DISTRIBUTION:")
print("\nAttacks:")
attack_balance = sorted([r['final_balance'] for r in attacks])
for scenario, balance in [(r['scenario_id'], r['final_balance']) for r in sorted(attacks, key=lambda x: x['final_balance'])]:
    marker = "✓" if balance < -0.5 else " "
    print(f"  {marker} {scenario}: {balance:.2f}")

print("\nBenign:")
benign_balance = sorted([r['final_balance'] for r in benign])
for scenario, balance in [(r['scenario_id'], r['final_balance']) for r in sorted(benign, key=lambda x: x['final_balance'])]:
    marker = "✗" if balance < -0.5 else " "
    print(f"  {marker} {scenario}: {balance:.2f}")

# Balance delta analysis
print("\n4. BALANCE DELTA PATTERNS:")

def calc_avg_delta(balances):
    if len(balances) < 2:
        return 0.0
    deltas = [balances[i] - balances[i-1] for i in range(1, len(balances))]
    return sum(deltas) / len(deltas)

print("\nAttacks (avg delta over all turns):")
for r in sorted(attacks, key=lambda x: calc_avg_delta(x['turn_by_turn_balances'])):
    avg_delta = calc_avg_delta(r['turn_by_turn_balances'])
    marker = "✓" if avg_delta < -0.3 else " "
    print(f"  {marker} {r['scenario_id']}: avg_delta={avg_delta:.2f}, balances={r['turn_by_turn_balances']}")

print("\nBenign (avg delta over all turns):")
for r in sorted(benign, key=lambda x: calc_avg_delta(x['turn_by_turn_balances'])):
    avg_delta = calc_avg_delta(r['turn_by_turn_balances'])
    marker = "✗" if avg_delta < -0.3 else " "
    print(f"  {marker} {r['scenario_id']}: avg_delta={avg_delta:.2f}, balances={r['turn_by_turn_balances']}")

# Trajectory analysis
print("\n5. TRAJECTORY CLASSIFICATION:")
attack_trajectories = defaultdict(list)
benign_trajectories = defaultdict(list)

for r in attacks:
    attack_trajectories[r['final_trajectory']].append(r['scenario_id'])

for r in benign:
    benign_trajectories[r['final_trajectory']].append(r['scenario_id'])

print(f"\nAttacks:")
for traj, scenarios in sorted(attack_trajectories.items()):
    print(f"  {traj}: {len(scenarios)}/10 - {scenarios}")

print(f"\nBenign:")
for traj, scenarios in sorted(benign_trajectories.items()):
    print(f"  {traj}: {len(scenarios)}/10 - {scenarios}")

# Combined signal analysis
print("\n6. COMBINED SIGNAL DETECTION:")
print("\nIf we used: trust_ema < 0.6 AND (trajectory=degrading OR avg_delta < -0.3):")

for r in attacks:
    trust_low = r['final_trust_ema'] < 0.6
    traj_bad = r['final_trajectory'] == 'degrading'
    delta_bad = calc_avg_delta(r['turn_by_turn_balances']) < -0.3

    would_detect = trust_low and (traj_bad or delta_bad)
    marker = "✓" if would_detect else "✗"
    print(f"  {marker} {r['scenario_id']}: trust={r['final_trust_ema']:.2f}, traj={r['final_trajectory']}, delta={calc_avg_delta(r['turn_by_turn_balances']):.2f}")

detected = sum(1 for r in attacks if
              r['final_trust_ema'] < 0.6 and
              (r['final_trajectory'] == 'degrading' or calc_avg_delta(r['turn_by_turn_balances']) < -0.3))
fp = sum(1 for r in benign if
        r['final_trust_ema'] < 0.6 and
        (r['final_trajectory'] == 'degrading' or calc_avg_delta(r['turn_by_turn_balances']) < -0.3))

print(f"\nDetection: {detected}/10 attacks ({detected/10*100:.0f}%)")
print(f"False positives: {fp}/10 benign ({fp/10*100:.0f}%)")

# Sharp crash detection
print("\n7. SHARP CRASH DETECTION:")
print("\nLooking for: balance drop > 1.0 in single turn")

def has_sharp_crash(balances):
    if len(balances) < 2:
        return False
    deltas = [balances[i] - balances[i-1] for i in range(1, len(balances))]
    return any(d < -1.0 for d in deltas)

print("\nAttacks with sharp crashes:")
for r in attacks:
    if has_sharp_crash(r['turn_by_turn_balances']):
        print(f"  ✓ {r['scenario_id']}: {r['turn_by_turn_balances']}")

print("\nBenign with sharp crashes:")
for r in benign:
    if has_sharp_crash(r['turn_by_turn_balances']):
        print(f"  ✗ {r['scenario_id']}: {r['turn_by_turn_balances']}")

crash_attacks = sum(1 for r in attacks if has_sharp_crash(r['turn_by_turn_balances']))
crash_benign = sum(1 for r in benign if has_sharp_crash(r['turn_by_turn_balances']))

print(f"\nSharp crash detection: {crash_attacks}/10 attacks, {crash_benign}/10 benign")

print("\n" + "=" * 80)
print("RECOMMENDED THRESHOLD CONFIGURATION")
print("=" * 80)

print("""
Based on data analysis:

1. Trust EMA threshold: 0.60
   - Catches 8/10 attacks (80%)
   - 0/10 false positives (0%)

2. Balance crash detection: delta < -1.0
   - Catches 7/10 attacks (70%)
   - 2/10 false positives (20%)

3. Combined approach (trust < 0.6 AND (degrading OR avg_delta < -0.3)):
   - Catches {}/10 attacks ({}%)
   - {}/10 false positives ({}%)

Recommendation: Use multi-signal approach with conservative thresholds.
Accepts higher false negative rate to maintain zero false positives.
""".format(detected, detected*10, fp, fp*10))

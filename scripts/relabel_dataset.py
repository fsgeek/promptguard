#!/usr/bin/env python3
"""
Dataset Relabeling Orchestrator

Coordinates the 4-phase dataset correction process:
1. Triage: Identify cases needing review
2. Proposals: Generate LLM-assisted relabeling proposals
3. Review: Interactive human review of proposals
4. Update: Apply approved changes to all storage locations

Usage:
    python scripts/relabel_dataset.py --phase all
    python scripts/relabel_dataset.py --phase triage
    python scripts/relabel_dataset.py --phase proposals
    python scripts/relabel_dataset.py --phase review
    python scripts/relabel_dataset.py --phase update

Author: Instance 37
Date: 2025-10-17
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib


@dataclass
class TriageResult:
    """Result from Phase 1: Triage"""
    prompt_id: str
    dataset: str
    original_label: str
    pre_f: float
    post_f: float
    triage_reasons: List[str]
    confidence: str  # "review_required" | "auto_approve_eligible"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RelabelingProposal:
    """Result from Phase 2: LLM-assisted proposals"""
    prompt_id: str
    original_label: str
    proposed_label: str
    confidence: str  # "high" | "medium" | "low"
    reasoning: str
    evaluator_model: str
    fire_circle_deliberation_id: Optional[str]
    flagged_for_human_review: bool
    cost: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ReviewDecision:
    """Result from Phase 3: Human review"""
    prompt_id: str
    original_label: str
    proposed_label: str
    final_label: str
    decision: str  # "approved" | "rejected" | "modified" | "deferred"
    reviewer: str
    review_timestamp: str
    review_reasoning: Optional[str]
    high_confidence_override: bool

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CorrectionSummary:
    """Result from Phase 4: Database update"""
    total_changes: int
    benign_malicious_changes: int
    or_bench_changes: int
    backup_location: str
    git_commit: Optional[str]
    verification_passed: bool
    changelog_path: str

    def to_dict(self) -> Dict:
        return asdict(self)


class DatasetRelabeler:
    """Orchestrates the dataset correction process"""

    def __init__(self,
                 work_dir: Path = Path("datasets/corrections/v1_to_v2"),
                 dry_run: bool = False,
                 verbose: bool = False):
        self.work_dir = work_dir
        self.dry_run = dry_run
        self.verbose = verbose
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def phase1_triage(self,
                     input_file: Path,
                     threshold: float = 0.4,
                     inversion_delta: float = 0.2) -> List[TriageResult]:
        """
        Phase 1: Identify cases requiring relabeling review

        Flags cases meeting ANY criteria:
        - pre_F < threshold AND original_label="manipulative"
        - Directive language + comprehensive response + original_label="manipulative"
        - Ethical keywords + original_label="manipulative"
        - post_F < pre_F by > inversion_delta

        Args:
            input_file: Path to target_response_analysis JSON
            threshold: Pre-F threshold for flagging (default 0.4)
            inversion_delta: Min delta for inversion flagging (default 0.2)

        Returns:
            List of TriageResult objects for flagged cases
        """
        if self.verbose:
            print(f"Phase 1: Triage")
            print(f"  Input: {input_file}")
            print(f"  Threshold: {threshold}")
            print(f"  Inversion delta: {inversion_delta}")

        # TODO: Implementation
        # 1. Load analysis file
        # 2. For each case:
        #    - Check pre_F vs threshold
        #    - Detect directive language patterns
        #    - Detect ethical keyword patterns
        #    - Calculate divergence (post_F - pre_F)
        # 3. Flag cases meeting criteria
        # 4. Determine if auto-approve eligible or requires review
        # 5. Return TriageResult list

        results = []

        # Placeholder implementation
        print("  [NOT IMPLEMENTED] Would analyze cases and flag for review")
        print(f"  Expected: ~250 cases flagged")

        # Save results
        output_file = self.work_dir / "triage_report.json"
        if not self.dry_run:
            with output_file.open("w") as f:
                json.dump([r.to_dict() for r in results], f, indent=2)
            print(f"  Saved: {output_file}")

        return results

    def phase2_proposals(self,
                        triage_file: Path,
                        evaluator_model: str = "anthropic/claude-3.5-sonnet",
                        enable_fire_circle: bool = True,
                        confidence_threshold: float = 0.8,
                        cost_limit: float = 10.0) -> List[RelabelingProposal]:
        """
        Phase 2: Generate LLM-assisted relabeling proposals

        For each flagged case:
        - Use SINGLE mode evaluation for high-confidence cases
        - Use Fire Circle for low-confidence/contested cases
        - Generate proposed label with reasoning
        - Estimate confidence level

        Args:
            triage_file: Path to triage_report.json
            evaluator_model: LLM model for proposals
            enable_fire_circle: Use Fire Circle for contested cases
            confidence_threshold: Threshold for high-confidence (default 0.8)
            cost_limit: Max API cost in dollars

        Returns:
            List of RelabelingProposal objects
        """
        if self.verbose:
            print(f"Phase 2: Generate Proposals")
            print(f"  Input: {triage_file}")
            print(f"  Evaluator: {evaluator_model}")
            print(f"  Fire Circle: {enable_fire_circle}")
            print(f"  Cost limit: ${cost_limit}")

        # TODO: Implementation
        # 1. Load triage results
        # 2. For each flagged case:
        #    a. Load full prompt + response from ArangoDB
        #    b. Construct evaluation request with context
        #    c. Call evaluator (SINGLE or Fire Circle based on confidence)
        #    d. Parse proposed label + reasoning
        #    e. Estimate confidence level
        #    f. Track API cost
        # 3. Separate into high-confidence vs review-required
        # 4. Return proposals

        proposals = []

        # Placeholder implementation
        print("  [NOT IMPLEMENTED] Would generate LLM proposals")
        print(f"  Expected cost: ~$4")
        print(f"  Expected: 200 SINGLE mode + 50 Fire Circle")

        # Save results
        output_file = self.work_dir / "relabeling_proposals.json"
        high_conf_file = self.work_dir / "high_confidence_proposals.json"
        review_file = self.work_dir / "review_required_proposals.json"

        if not self.dry_run:
            with output_file.open("w") as f:
                json.dump([p.to_dict() for p in proposals], f, indent=2)
            print(f"  Saved: {output_file}")

            # Split by confidence
            high_confidence = [p for p in proposals if p.confidence == "high"]
            review_required = [p for p in proposals if p.confidence in ["medium", "low"]]

            with high_conf_file.open("w") as f:
                json.dump([p.to_dict() for p in high_confidence], f, indent=2)
            with review_file.open("w") as f:
                json.dump([p.to_dict() for p in review_required], f, indent=2)

            print(f"  High-confidence: {len(high_confidence)} cases")
            print(f"  Review required: {len(review_required)} cases")

        return proposals

    def phase3_review(self,
                     proposals_file: Path,
                     auto_approve_file: Optional[Path] = None,
                     sample_size: int = 25,
                     randomize: bool = True,
                     resume_file: Optional[Path] = None) -> List[ReviewDecision]:
        """
        Phase 3: Interactive human review of proposals

        Presents proposals to human reviewer with context:
        - Prompt text
        - Response preview
        - Original vs proposed label
        - LLM reasoning
        - F-scores

        Reviewer can: Approve, Reject, Modify, Skip, Quit

        Auto-approval workflow:
        1. Review random sample of high-confidence proposals
        2. If agreement >= 90%, auto-approve rest
        3. If <90%, switch to full manual review

        Args:
            proposals_file: Path to review_required_proposals.json
            auto_approve_file: Optional path to high_confidence_proposals.json
            sample_size: Random sample size for auto-approve validation
            randomize: Shuffle review order
            resume_file: Resume from previous session

        Returns:
            List of ReviewDecision objects
        """
        if self.verbose:
            print(f"Phase 3: Interactive Review")
            print(f"  Input: {proposals_file}")
            print(f"  Auto-approve file: {auto_approve_file}")
            print(f"  Sample size: {sample_size}")

        # TODO: Implementation
        # 1. Load proposals (and auto-approve candidates if provided)
        # 2. If auto_approve_file:
        #    a. Sample random cases
        #    b. Present for review
        #    c. Calculate agreement rate
        #    d. If >=90%, auto-approve rest; else full review
        # 3. For each review-required case:
        #    a. Load prompt + response from ArangoDB
        #    b. Display formatted review interface
        #    c. Capture decision (A/R/M/S/Q)
        #    d. Save progress after each decision
        # 4. Return ReviewDecision list

        decisions = []

        # Placeholder implementation
        print("  [NOT IMPLEMENTED] Would launch interactive review CLI")
        print(f"  Expected: ~80 cases for manual review")
        print(f"  Estimated time: 1.5 hours")

        # Save results
        output_file = self.work_dir / "review_decisions.json"
        log_file = self.work_dir / "review_session_log.txt"
        stats_file = self.work_dir / "review_statistics.json"

        if not self.dry_run:
            with output_file.open("w") as f:
                json.dump([d.to_dict() for d in decisions], f, indent=2)
            print(f"  Saved: {output_file}")

            # Log session
            timestamp = datetime.now().isoformat()
            with log_file.open("a") as f:
                f.write(f"\n=== Review Session {timestamp} ===\n")
                f.write(f"Total reviewed: {len(decisions)}\n")

            # Statistics
            stats = {
                "total_reviewed": len(decisions),
                "approved": len([d for d in decisions if d.decision == "approved"]),
                "rejected": len([d for d in decisions if d.decision == "rejected"]),
                "modified": len([d for d in decisions if d.decision == "modified"]),
                "deferred": len([d for d in decisions if d.decision == "deferred"]),
            }
            with stats_file.open("w") as f:
                json.dump(stats, f, indent=2)

        return decisions

    def phase4_update(self,
                     decisions_file: Path,
                     backup_dir: Path = Path("datasets/backups/v1_20251017"),
                     skip_verification: bool = False) -> CorrectionSummary:
        """
        Phase 4: Apply approved label corrections

        Transactional update process:
        1. Create backups (JSON + ArangoDB)
        2. Apply changes to JSON datasets
        3. Propagate to ArangoDB collections
        4. Verify integrity
        5. Generate changelog
        6. Git commit

        If ANY step fails: ROLLBACK to backups

        Args:
            decisions_file: Path to review_decisions.json
            backup_dir: Directory for backups
            skip_verification: Skip integrity checks (NOT RECOMMENDED)

        Returns:
            CorrectionSummary with update statistics
        """
        if self.verbose:
            print(f"Phase 4: Database Update")
            print(f"  Input: {decisions_file}")
            print(f"  Backup dir: {backup_dir}")
            print(f"  Skip verification: {skip_verification}")

        # TODO: Implementation
        # 1. Load approved decisions (filter: decision="approved")
        # 2. Create backups:
        #    a. Copy JSON datasets to backup_dir
        #    b. Export ArangoDB collections (arangodump)
        # 3. Apply JSON updates:
        #    a. Load each dataset
        #    b. Update label fields for matching IDs
        #    c. Add version metadata
        #    d. Save updated datasets
        # 4. Apply ArangoDB updates:
        #    a. Update attacks collection
        #    b. Update target_responses collection
        #    c. Mark evaluations as ground_truth_updated=true
        # 5. Verify integrity:
        #    a. Count changes applied vs expected
        #    b. Check referential integrity
        #    c. Verify label consistency across storage
        # 6. Generate changelog:
        #    a. Summary statistics
        #    b. Breakdown by dataset
        #    c. Detailed change list
        # 7. Git commit:
        #    a. Stage dataset changes
        #    b. Commit with detailed message
        # 8. Return CorrectionSummary

        summary = CorrectionSummary(
            total_changes=0,
            benign_malicious_changes=0,
            or_bench_changes=0,
            backup_location=str(backup_dir),
            git_commit=None,
            verification_passed=False,
            changelog_path=str(self.work_dir / "DATASET_CHANGELOG_v1_v2.md")
        )

        # Placeholder implementation
        print("  [NOT IMPLEMENTED] Would apply transactional updates")
        print(f"  Expected: 186 changes")
        print(f"  Backup: {backup_dir}")
        print(f"  Changelog: {summary.changelog_path}")

        # Save verification report
        report_file = self.work_dir / "correction_verification_report.json"
        if not self.dry_run:
            with report_file.open("w") as f:
                json.dump(summary.to_dict(), f, indent=2)
            print(f"  Saved: {report_file}")

        return summary

    def run_all_phases(self,
                      input_file: Path,
                      evaluator_model: str = "anthropic/claude-3.5-sonnet") -> None:
        """
        Execute all 4 phases sequentially

        Args:
            input_file: Path to target_response_analysis JSON
            evaluator_model: LLM model for proposals
        """
        print("=== Dataset Correction: All Phases ===\n")

        # Phase 1: Triage
        print("Phase 1: Triage")
        triage_results = self.phase1_triage(input_file)
        print(f"  Flagged: {len(triage_results)} cases\n")

        # Phase 2: Proposals
        print("Phase 2: Generate Proposals")
        proposals = self.phase2_proposals(
            self.work_dir / "triage_report.json",
            evaluator_model=evaluator_model
        )
        print(f"  Proposals: {len(proposals)}\n")

        # Phase 3: Review
        print("Phase 3: Human Review")
        print("  [Requires interactive session - run separately]")
        print(f"  Command: python scripts/relabel_dataset.py --phase review\n")

        # Phase 4: Update
        print("Phase 4: Database Update")
        print("  [Run after review phase completes]")
        print(f"  Command: python scripts/relabel_dataset.py --phase update\n")


def main():
    parser = argparse.ArgumentParser(
        description="Dataset relabeling orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all phases (except review, which is interactive)
  python scripts/relabel_dataset.py --phase all

  # Run individual phases
  python scripts/relabel_dataset.py --phase triage
  python scripts/relabel_dataset.py --phase proposals
  python scripts/relabel_dataset.py --phase review
  python scripts/relabel_dataset.py --phase update

  # Dry run (no file modifications)
  python scripts/relabel_dataset.py --phase all --dry-run

  # Custom settings
  python scripts/relabel_dataset.py --phase triage --threshold 0.3
  python scripts/relabel_dataset.py --phase proposals --evaluator openai/gpt-4o
        """
    )

    parser.add_argument(
        "--phase",
        choices=["all", "triage", "proposals", "review", "update"],
        required=True,
        help="Which phase to execute"
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("target_response_analysis_2025-10-16-22-15.json"),
        help="Input analysis file (for triage phase)"
    )

    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("datasets/corrections/v1_to_v2"),
        help="Working directory for correction files"
    )

    parser.add_argument(
        "--evaluator",
        default="anthropic/claude-3.5-sonnet",
        help="Evaluator model for proposals phase"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.4,
        help="Pre-F threshold for triage (default: 0.4)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed execution information"
    )

    args = parser.parse_args()

    relabeler = DatasetRelabeler(
        work_dir=args.work_dir,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    if args.phase == "all":
        relabeler.run_all_phases(args.input, args.evaluator)
    elif args.phase == "triage":
        relabeler.phase1_triage(args.input, threshold=args.threshold)
    elif args.phase == "proposals":
        triage_file = args.work_dir / "triage_report.json"
        relabeler.phase2_proposals(triage_file, evaluator_model=args.evaluator)
    elif args.phase == "review":
        proposals_file = args.work_dir / "review_required_proposals.json"
        auto_approve_file = args.work_dir / "high_confidence_proposals.json"
        relabeler.phase3_review(proposals_file, auto_approve_file=auto_approve_file)
    elif args.phase == "update":
        decisions_file = args.work_dir / "review_decisions.json"
        relabeler.phase4_update(decisions_file)


if __name__ == "__main__":
    main()

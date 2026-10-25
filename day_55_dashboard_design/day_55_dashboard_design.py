from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta


class PRState(Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"


class CheckState(Enum):
    PASSING = "passing"
    FAILING = "failing"
    PENDING = "pending"


class MergeStrategy(Enum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass
class Commit:
    sha: str
    message: str
    author: str
    created_at: datetime


@dataclass
class ReviewComment:
    comment_id: int
    reviewer: str
    body: str
    resolved: bool = False


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    submitted_at: datetime
    comments: List[ReviewComment] = field(default_factory=list)


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    required: bool = True


@dataclass
class BranchProtection:
    required_reviews: int = 2
    required_checks: Set[str] = field(
        default_factory=lambda: {"unit-tests", "security-scan"}
    )
    require_conversation_resolution: bool = True
    require_linear_history: bool = False
    allow_force_push: bool = False
    allow_direct_push: bool = False
    allow_deletion: bool = False


@dataclass
class Branch:
    name: str
    protected: bool
    commits: List[Commit] = field(default_factory=list)


@dataclass
class PullRequest:
    number: int
    source_branch: str
    target_branch: str
    title: str
    state: PRState
    commits: List[Commit]
    reviews: List[Review]
    comments: List[ReviewComment]
    checks: List[StatusCheck]
    merge_strategy: MergeStrategy = MergeStrategy.SQUASH
    created_at: datetime = field(default_factory=datetime.utcnow)

    def unresolved_conversations(self) -> int:
        return sum(not c.resolved for c in self.comments)

    def eligible_approvers(self, eligible_reviewers: Set[str]) -> Set[str]:
        approved = {
            review.reviewer
            for review in self.reviews
            if review.state == ReviewState.APPROVED
            and review.reviewer in eligible_reviewers
        }
        changes_requested = {
            review.reviewer
            for review in self.reviews
            if review.state == ReviewState.CHANGES_REQUESTED
            and review.reviewer in eligible_reviewers
        }
        return approved - changes_requested


@dataclass
class Repository:
    name: str
    branches: Dict[str, Branch]
    pull_requests: Dict[int, PullRequest]
    protection: Dict[str, BranchProtection]
    eligible_reviewers: Set[str]


@dataclass
class DashboardMetric:
    name: str
    value: int | float | str
    status: str
    explanation: str


class RepositoryGovernance:
    """Evaluates merge eligibility while exposing dashboard-oriented metrics."""

    def __init__(self, repository: Repository):
        self.repository = repository

    def evaluate_merge(self, pr_number: int) -> Tuple[bool, List[str]]:
        pr = self.repository.pull_requests[pr_number]
        reasons: List[str] = []

        if pr.state != PRState.OPEN:
            reasons.append("Pull Request is not open.")

        if pr.state == PRState.DRAFT:
            reasons.append("Draft Pull Requests cannot be merged.")

        target = self.repository.branches.get(pr.target_branch)
        if target is None:
            reasons.append("Target branch does not exist.")

        policy = self.repository.protection.get(pr.target_branch)
        if policy is None:
            reasons.append("No branch protection policy is configured.")

        if policy:
            approvals = len(pr.eligible_approvers(self.repository.eligible_reviewers))
            if approvals < policy.required_reviews:
                reasons.append(
                    f"Required approvals: {policy.required_reviews}; "
                    f"eligible approvals: {approvals}."
                )

            checks = {check.name: check.state for check in pr.checks}
            for required_check in policy.required_checks:
                if checks.get(required_check) != CheckState.PASSING:
                    reasons.append(
                        f"Required status check '{required_check}' is not passing."
                    )

            if (
                policy.require_conversation_resolution
                and pr.unresolved_conversations() > 0
            ):
                reasons.append("Unresolved review conversations remain.")

            if policy.require_linear_history and pr.merge_strategy == MergeStrategy.MERGE_COMMIT:
                reasons.append("Linear history is required.")

        return len(reasons) == 0, reasons

    def dashboard_metrics(self) -> List[DashboardMetric]:
        prs = list(self.repository.pull_requests.values())

        open_prs = [p for p in prs if p.state == PRState.OPEN]
        drafts = [p for p in prs if p.state == PRState.DRAFT]
        merged = [p for p in prs if p.state == PRState.MERGED]

        mergeable = 0
        blocked = 0
        for pr in open_prs:
            eligible, _ = self.evaluate_merge(pr.number)
            if eligible:
                mergeable += 1
            else:
                blocked += 1

        unresolved = sum(p.unresolved_conversations() for p in prs)

        return [
            DashboardMetric(
                "Open Pull Requests",
                len(open_prs),
                "neutral",
                "Current proposed changes requiring workflow attention.",
            ),
            DashboardMetric(
                "Draft Pull Requests",
                len(drafts),
                "neutral",
                "Work that has not entered the merge-ready review stage.",
            ),
            DashboardMetric(
                "Mergeable Pull Requests",
                mergeable,
                "good" if mergeable else "attention",
                "Open Pull Requests satisfying current governance rules.",
            ),
            DashboardMetric(
                "Blocked Pull Requests",
                blocked,
                "warning" if blocked else "good",
                "Open Pull Requests failing one or more merge conditions.",
            ),
            DashboardMetric(
                "Merged Pull Requests",
                len(merged),
                "good",
                "Completed changesets.",
            ),
            DashboardMetric(
                "Unresolved Conversations",
                unresolved,
                "warning" if unresolved else "good",
                "Review discussions that still require action.",
            ),
        ]


def print_dashboard(metrics: List[DashboardMetric]) -> None:
    print("\nREPOSITORY GOVERNANCE DASHBOARD")
    print("=" * 78)

    for metric in metrics:
        print(f"{metric.name:28} {str(metric.value):>6}  [{metric.status}]")
        print(f"  {metric.explanation}")


def create_sample_repository() -> Repository:
    now = datetime.utcnow()

    commits = [
        Commit("a100001", "Add dashboard layout", "alice", now - timedelta(days=3)),
        Commit("a100002", "Add governance metrics", "alice", now - timedelta(days=2)),
    ]

    comments = [
        ReviewComment(1, "bob", "Please clarify the status-check grouping.", False),
        ReviewComment(2, "carol", "Metric definition is clear.", True),
    ]

    reviews = [
        Review(
            "bob",
            ReviewState.APPROVED,
            now - timedelta(hours=8),
            [comments[1]],
        ),
        Review(
            "carol",
            ReviewState.APPROVED,
            now - timedelta(hours=4),
        ),
    ]

    checks = [
        StatusCheck("unit-tests", CheckState.PASSING),
        StatusCheck("security-scan", CheckState.PASSING),
        StatusCheck("performance-test", CheckState.PENDING, required=False),
    ]

    pr = PullRequest(
        number=42,
        source_branch="feature/governance-dashboard",
        target_branch="main",
        title="Design repository governance dashboard",
        state=PRState.OPEN,
        commits=commits,
        reviews=reviews,
        comments=comments,
        checks=checks,
    )

    return Repository(
        name="platform-dashboard",
        branches={
            "main": Branch("main", True, commits),
            "feature/governance-dashboard": Branch(
                "feature/governance-dashboard", False, commits
            ),
        },
        pull_requests={42: pr},
        protection={
            "main": BranchProtection(
                required_reviews=2,
                required_checks={"unit-tests", "security-scan"},
                require_conversation_resolution=True,
                require_linear_history=True,
            )
        },
        eligible_reviewers={"alice", "bob", "carol", "david"},
    )


def validate_repository(repository: Repository) -> None:
    if not repository.name.strip():
        raise ValueError("Repository name cannot be empty.")

    if "main" not in repository.branches:
        raise ValueError("Repository must define a main branch.")

    for branch_name, policy in repository.protection.items():
        if branch_name not in repository.branches:
            raise ValueError(f"Protection references unknown branch: {branch_name}.")
        if policy.required_reviews < 0:
            raise ValueError("Required review count cannot be negative.")

    for pr in repository.pull_requests.values():
        if pr.source_branch not in repository.branches:
            raise ValueError(f"Unknown source branch: {pr.source_branch}.")
        if pr.target_branch not in repository.branches:
            raise ValueError(f"Unknown target branch: {pr.target_branch}.")


def main() -> None:
    repository = create_sample_repository()
    validate_repository(repository)

    governance = RepositoryGovernance(repository)
    metrics = governance.dashboard_metrics()
    print_dashboard(metrics)

    eligible, reasons = governance.evaluate_merge(42)

    print("\nMERGE ELIGIBILITY")
    print("=" * 78)
    print("Eligible:", eligible)

    if reasons:
        for reason in reasons:
            print("-", reason)
    else:
        print("All branch-protection and Pull Request conditions are satisfied.")

    # Security-oriented debugging information intentionally avoids credentials
    # or repository secrets and reports only governance state.
    pr = repository.pull_requests[42]
    print("\nPR DETAIL")
    print("=" * 78)
    print("PR:", pr.number)
    print("Source:", pr.source_branch)
    print("Target:", pr.target_branch)
    print("Commits:", len(pr.commits))
    print("Reviews:", len(pr.reviews))
    print("Unresolved conversations:", pr.unresolved_conversations())


if __name__ == "__main__":
    main()

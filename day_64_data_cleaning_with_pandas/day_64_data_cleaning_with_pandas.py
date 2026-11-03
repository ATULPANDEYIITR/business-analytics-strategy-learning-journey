from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
import math
import re


class CleaningError(Exception):
    """Raised when a dataset cannot be safely cleaned."""


class ReviewState(Enum):
    DRAFT = "draft"
    OPEN = "open"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    CLOSED = "closed"
    MERGED = "merged"


@dataclass
class CleaningStats:
    rows_before: int
    rows_after: int
    duplicates_removed: int
    missing_values_before: int
    missing_values_after: int
    invalid_records_removed: int


class PullRequestCleaner:
    """
    Data-cleaning pipeline for repository workflow records.

    The dataset contains Pull Requests, reviews, approvals, status checks,
    and branch-protection attributes. Cleaning separates malformed records
    from valid records and normalizes values without changing their meaning.
    """

    REQUIRED_FIELDS = {
        "pr_id",
        "repository",
        "source_branch",
        "target_branch",
        "reviewer",
        "review_state",
        "approval",
        "status_check",
    }

    VALID_REVIEW_STATES = {state.value for state in ReviewState}
    VALID_APPROVALS = {"approved", "rejected", "pending", "dismissed", "not_required"}
    VALID_STATUS = {"passed", "failed", "pending"}

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    @staticmethod
    def normalize_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def normalize_branch(value: Any) -> str | None:
        text = PullRequestCleaner.normalize_text(value)
        if text is None:
            return None
        text = text.replace("refs/heads/", "")
        return text.lower()

    @staticmethod
    def normalize_enum(value: Any) -> str | None:
        text = PullRequestCleaner.normalize_text(value)
        return text.lower() if text else None

    @staticmethod
    def normalize_boolean(value: Any) -> bool | None:
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        text = str(value).strip().lower()

        if text in {"true", "yes", "1", "y", "on"}:
            return True
        if text in {"false", "no", "0", "n", "off"}:
            return False

        return None

    def normalize(self) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for source in self.records:
            record = dict(source)

            record["repository"] = self.normalize_text(record.get("repository"))
            record["source_branch"] = self.normalize_branch(
                record.get("source_branch")
            )
            record["target_branch"] = self.normalize_branch(
                record.get("target_branch")
            )
            record["reviewer"] = self.normalize_text(record.get("reviewer"))
            record["review_state"] = self.normalize_enum(
                record.get("review_state")
            )
            record["approval"] = self.normalize_enum(record.get("approval"))
            record["status_check"] = self.normalize_enum(
                record.get("status_check")
            )
            record["draft"] = self.normalize_boolean(record.get("draft"))
            record["required_review"] = self.normalize_boolean(
                record.get("required_review")
            )
            record["conversation_resolved"] = self.normalize_boolean(
                record.get("conversation_resolved")
            )
            record["force_push_allowed"] = self.normalize_boolean(
                record.get("force_push_allowed")
            )

            normalized.append(record)

        return normalized

    def validate(self, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        valid: list[dict[str, Any]] = []
        invalid_count = 0

        for record in records:
            if not self.REQUIRED_FIELDS.issubset(record):
                invalid_count += 1
                continue

            if not record["pr_id"]:
                invalid_count += 1
                continue

            if record["review_state"] not in self.VALID_REVIEW_STATES:
                invalid_count += 1
                continue

            if record["approval"] not in self.VALID_APPROVALS:
                invalid_count += 1
                continue

            if record["status_check"] not in self.VALID_STATUS:
                invalid_count += 1
                continue

            if not record["repository"]:
                invalid_count += 1
                continue

            if not record["source_branch"] or not record["target_branch"]:
                invalid_count += 1
                continue

            valid.append(record)

        return valid, invalid_count

    @staticmethod
    def count_missing(records: list[dict[str, Any]]) -> int:
        return sum(
            1
            for record in records
            for value in record.values()
            if value is None
        )

    @staticmethod
    def remove_duplicates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        unique: list[dict[str, Any]] = []

        for record in records:
            key = (
                record.get("pr_id"),
                record.get("repository"),
                record.get("source_branch"),
                record.get("target_branch"),
                record.get("reviewer"),
            )

            if key not in seen:
                seen.add(key)
                unique.append(record)

        return unique

    @staticmethod
    def fill_missing(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cleaned = []

        for record in records:
            row = dict(record)

            if row.get("draft") is None:
                row["draft"] = row.get("review_state") == ReviewState.DRAFT.value

            if row.get("required_review") is None:
                row["required_review"] = row.get("target_branch") in {
                    "main",
                    "master",
                    "production",
                }

            if row.get("conversation_resolved") is None:
                row["conversation_resolved"] = (
                    row.get("review_state")
                    not in {
                        ReviewState.CHANGES_REQUESTED.value,
                        ReviewState.OPEN.value,
                    }
                )

            if row.get("force_push_allowed") is None:
                row["force_push_allowed"] = False

            cleaned.append(row)

        return cleaned

    @staticmethod
    def calculate_merge_eligibility(record: dict[str, Any]) -> bool:
        """
        A Pull Request is merge-eligible only when all repository-level
        conditions represented in this dataset are satisfied.
        """
        if record["review_state"] != ReviewState.APPROVED.value:
            return False

        if record["approval"] != "approved":
            return False

        if record["status_check"] != "passed":
            return False

        if record["required_review"] and record["approval"] != "approved":
            return False

        if not record["conversation_resolved"]:
            return False

        return True

    def clean(self) -> tuple[list[dict[str, Any]], CleaningStats]:
        rows_before = len(self.records)
        missing_before = self.count_missing(self.records)

        normalized = self.normalize()
        validated, invalid_count = self.validate(normalized)
        unique = self.remove_duplicates(validated)
        cleaned = self.fill_missing(unique)

        for record in cleaned:
            record["merge_eligible"] = self.calculate_merge_eligibility(record)

        stats = CleaningStats(
            rows_before=rows_before,
            rows_after=len(cleaned),
            duplicates_removed=len(validated) - len(unique),
            missing_values_before=missing_before,
            missing_values_after=self.count_missing(cleaned),
            invalid_records_removed=invalid_count,
        )

        return cleaned, stats


def print_report(records: list[dict[str, Any]], stats: CleaningStats) -> None:
    print("DATA CLEANING REPORT")
    print("=" * 60)
    print(f"Rows before cleaning       : {stats.rows_before}")
    print(f"Rows after cleaning        : {stats.rows_after}")
    print(f"Duplicates removed         : {stats.duplicates_removed}")
    print(f"Invalid records removed    : {stats.invalid_records_removed}")
    print(f"Missing values before      : {stats.missing_values_before}")
    print(f"Missing values after       : {stats.missing_values_after}")
    print()

    print("CLEANED RECORDS")
    print("=" * 60)

    for record in records:
        print(
            f"PR #{record['pr_id']:>3} | "
            f"{record['repository']:<20} | "
            f"{record['source_branch']:<18} -> "
            f"{record['target_branch']:<12} | "
            f"review={record['review_state']:<18} | "
            f"approval={record['approval']:<11} | "
            f"checks={record['status_check']:<7} | "
            f"merge={record['merge_eligible']}"
        )


def main() -> None:
    raw_records = [
        {
            "pr_id": 101,
            "repository": "payments-api",
            "source_branch": "refs/heads/feature/payment-validation",
            "target_branch": "MAIN",
            "reviewer": "  Priya Sharma ",
            "review_state": "APPROVED",
            "approval": "Approved",
            "status_check": "PASSED",
            "draft": "false",
            "required_review": None,
            "conversation_resolved": True,
            "force_push_allowed": None,
        },
        {
            "pr_id": 101,
            "repository": "payments-api",
            "source_branch": "refs/heads/feature/payment-validation",
            "target_branch": "MAIN",
            "reviewer": " Priya Sharma",
            "review_state": "approved",
            "approval": "approved",
            "status_check": "passed",
            "draft": "false",
            "required_review": None,
            "conversation_resolved": True,
            "force_push_allowed": None,
        },
        {
            "pr_id": 102,
            "repository": "payments-api",
            "source_branch": "feature/audit-logging",
            "target_branch": "main",
            "reviewer": "Rahul",
            "review_state": "changes_requested",
            "approval": "pending",
            "status_check": "failed",
            "draft": "no",
            "required_review": "yes",
            "conversation_resolved": "no",
            "force_push_allowed": "no",
        },
        {
            "pr_id": 103,
            "repository": "inventory-api",
            "source_branch": "feature/cache",
            "target_branch": "develop",
            "reviewer": None,
            "review_state": "open",
            "approval": "pending",
            "status_check": "pending",
            "draft": None,
            "required_review": None,
            "conversation_resolved": None,
            "force_push_allowed": None,
        },
        {
            "pr_id": 104,
            "repository": "inventory-api",
            "source_branch": "feature/reports",
            "target_branch": "main",
            "reviewer": "Anita",
            "review_state": "approved",
            "approval": "approved",
            "status_check": "passed",
            "draft": False,
            "required_review": True,
            "conversation_resolved": True,
            "force_push_allowed": False,
        },
        {
            "pr_id": 105,
            "repository": "",
            "source_branch": "feature/bad-record",
            "target_branch": "main",
            "reviewer": "Unknown",
            "review_state": "approved",
            "approval": "approved",
            "status_check": "passed",
        },
        {
            "pr_id": 106,
            "repository": "billing-api",
            "source_branch": "feature/cleanup",
            "target_branch": "main",
            "reviewer": "Neha",
            "review_state": "invalid_state",
            "approval": "approved",
            "status_check": "passed",
        },
    ]

    cleaner = PullRequestCleaner(raw_records)
    cleaned, stats = cleaner.clean()

    print_report(cleaned, stats)

    assert len(cleaned) == 4
    assert stats.duplicates_removed == 1
    assert stats.invalid_records_removed == 2
    assert cleaned[0]["merge_eligible"] is True

    print()
    print("Validation checks passed.")


if __name__ == "__main__":
    main()

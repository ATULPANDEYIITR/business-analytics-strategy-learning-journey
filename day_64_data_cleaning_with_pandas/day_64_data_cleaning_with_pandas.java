import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public class DataCleaningGovernance {

    enum ReviewState {
        DRAFT,
        OPEN,
        APPROVED,
        CHANGES_REQUESTED,
        CLOSED,
        MERGED
    }

    enum Approval {
        APPROVED,
        REJECTED,
        PENDING,
        DISMISSED,
        NOT_REQUIRED
    }

    enum StatusCheck {
        PASSED,
        FAILED,
        PENDING
    }

    record RawRecord(
        int prId,
        String repository,
        String sourceBranch,
        String targetBranch,
        String reviewer,
        ReviewState reviewState,
        Approval approval,
        StatusCheck statusCheck,
        Boolean draft,
        Boolean requiredReview,
        Boolean conversationResolved,
        Boolean forcePushAllowed
    ) {}

    record CleanRecord(
        int prId,
        String repository,
        String sourceBranch,
        String targetBranch,
        String reviewer,
        ReviewState reviewState,
        Approval approval,
        StatusCheck statusCheck,
        boolean draft,
        boolean requiredReview,
        boolean conversationResolved,
        boolean forcePushAllowed,
        boolean mergeEligible
    ) {}

    record CleaningReport(
        List<CleanRecord> records,
        int rowsBefore,
        int rowsAfter,
        int invalidRemoved,
        int duplicatesRemoved
    ) {}

    static class CleaningException extends RuntimeException {
        CleaningException(String message) {
            super(message);
        }
    }

    interface CleaningPolicy {
        boolean accepts(RawRecord record);
    }

    static final class ValidationPolicy implements CleaningPolicy {
        @Override
        public boolean accepts(RawRecord record) {
            return record != null
                && record.prId() > 0
                && cleanText(record.repository()) != null
                && cleanText(record.sourceBranch()) != null
                && cleanText(record.targetBranch()) != null
                && record.reviewState() != null
                && record.approval() != null
                && record.statusCheck() != null;
        }
    }

    static final class GovernanceService {

        private final CleaningPolicy validationPolicy;

        GovernanceService(CleaningPolicy validationPolicy) {
            this.validationPolicy = Objects.requireNonNull(validationPolicy);
        }

        CleaningReport clean(List<RawRecord> input) {
            if (input == null) {
                throw new CleaningException("Input records cannot be null.");
            }

            int invalidRemoved = 0;
            int duplicatesRemoved = 0;

            List<CleanRecord> cleaned = new ArrayList<>();
            Set<String> seen = new HashSet<>();

            for (RawRecord raw : input) {
                if (!validationPolicy.accepts(raw)) {
                    invalidRemoved++;
                    continue;
                }

                String repository = cleanText(raw.repository());
                String source = cleanBranch(raw.sourceBranch());
                String target = cleanBranch(raw.targetBranch());
                String reviewer = cleanText(raw.reviewer());

                String key = raw.prId()
                    + "|" + repository
                    + "|" + source
                    + "|" + target
                    + "|" + reviewer;

                if (!seen.add(key)) {
                    duplicatesRemoved++;
                    continue;
                }

                boolean requiredReview = raw.requiredReview() != null
                    ? raw.requiredReview()
                    : isProtectedTarget(target);

                boolean draft = raw.draft() != null
                    ? raw.draft()
                    : raw.reviewState() == ReviewState.DRAFT;

                boolean conversationResolved =
                    raw.conversationResolved() != null
                    ? raw.conversationResolved()
                    : raw.reviewState() != ReviewState.OPEN
                        && raw.reviewState() != ReviewState.CHANGES_REQUESTED;

                boolean forcePushAllowed =
                    raw.forcePushAllowed() != null
                    && raw.forcePushAllowed();

                boolean mergeEligible =
                    raw.reviewState() == ReviewState.APPROVED
                    && raw.approval() == Approval.APPROVED
                    && raw.statusCheck() == StatusCheck.PASSED
                    && conversationResolved
                    && (!requiredReview || raw.approval() == Approval.APPROVED);

                cleaned.add(new CleanRecord(
                    raw.prId(),
                    repository,
                    source,
                    target,
                    reviewer,
                    raw.reviewState(),
                    raw.approval(),
                    raw.statusCheck(),
                    draft,
                    requiredReview,
                    conversationResolved,
                    forcePushAllowed,
                    mergeEligible
                ));
            }

            return new CleaningReport(
                List.copyOf(cleaned),
                input.size(),
                cleaned.size(),
                invalidRemoved,
                duplicatesRemoved
            );
        }
    }

    static String cleanText(String value) {
        if (value == null) {
            return null;
        }

        String result = value.trim().replaceAll("\\s+", " ");
        return result.isBlank() ? null : result;
    }

    static String cleanBranch(String value) {
        String result = cleanText(value);

        if (result == null) {
            return null;
        }

        result = result.toLowerCase();

        if (result.startsWith("refs/heads/")) {
            result = result.substring("refs/heads/".length());
        }

        return result;
    }

    static boolean isProtectedTarget(String branch) {
        return Set.of("main", "master", "production").contains(branch);
    }

    public static void main(String[] args) {
        List<RawRecord> rawRecords = List.of(
            new RawRecord(
                401,
                "payments-api",
                "refs/heads/feature/payment-validation",
                "MAIN",
                " Priya ",
                ReviewState.APPROVED,
                Approval.APPROVED,
                StatusCheck.PASSED,
                false,
                null,
                true,
                false
            ),
            new RawRecord(
                401,
                "payments-api",
                "refs/heads/feature/payment-validation",
                "main",
                "Priya",
                ReviewState.APPROVED,
                Approval.APPROVED,
                StatusCheck.PASSED,
                false,
                null,
                true,
                false
            ),
            new RawRecord(
                402,
                "payments-api",
                "feature/audit",
                "main",
                "Rahul",
                ReviewState.CHANGES_REQUESTED,
                Approval.PENDING,
                StatusCheck.FAILED,
                false,
                true,
                false,
                false
            ),
            new RawRecord(
                403,
                "inventory-api",
                "feature/search",
                "develop",
                null,
                ReviewState.OPEN,
                Approval.PENDING,
                StatusCheck.PENDING,
                null,
                null,
                null,
                null
            ),
            new RawRecord(
                404,
                "inventory-api",
                "feature/reports",
                "main",
                "Anita",
                ReviewState.APPROVED,
                Approval.APPROVED,
                StatusCheck.PASSED,
                false,
                true,
                true,
                false
            ),
            new RawRecord(
                405,
                "",
                "feature/invalid",
                "main",
                "Invalid",
                ReviewState.APPROVED,
                Approval.APPROVED,
                StatusCheck.PASSED,
                false,
                true,
                true,
                false
            )
        );

        GovernanceService service =
            new GovernanceService(new ValidationPolicy());

        CleaningReport report = service.clean(rawRecords);

        System.out.println("DATA CLEANING REPORT");
        System.out.println("============================================");
        System.out.println("Rows before        : " + report.rowsBefore());
        System.out.println("Rows after         : " + report.rowsAfter());
        System.out.println("Invalid removed    : " + report.invalidRemoved());
        System.out.println("Duplicates removed : " + report.duplicatesRemoved());

        System.out.println("\nCLEANED RECORDS");
        System.out.println("============================================");

        report.records().forEach(record ->
            System.out.printf(
                "PR #%d | %s | %s -> %s | review=%s | approval=%s | " +
                "check=%s | merge=%s%n",
                record.prId(),
                record.repository(),
                record.sourceBranch(),
                record.targetBranch(),
                record.reviewState(),
                record.approval(),
                record.statusCheck(),
                record.mergeEligible()
            )
        );

        if (report.rowsAfter() != 4) {
            throw new CleaningException("Unexpected cleaned record count.");
        }

        if (report.duplicatesRemoved() != 1) {
            throw new CleaningException("Duplicate-removal validation failed.");
        }

        if (!report.records().getFirst().mergeEligible()) {
            throw new CleaningException("Merge eligibility validation failed.");
        }

        System.out.println("\nValidation checks passed.");
    }
}

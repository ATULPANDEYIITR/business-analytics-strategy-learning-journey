'use strict';

/*
 * Data-cleaning pipeline for repository workflow records.
 *
 * JavaScript-specific design:
 * - Map-based grouping
 * - Set-based duplicate detection
 * - event-driven cleaning stages
 * - policy evaluation through functions
 * - immutable record construction
 */

const { EventEmitter } = require('node:events');

class CleaningError extends Error {
    constructor(message) {
        super(message);
        this.name = 'CleaningError';
    }
}

const REVIEW_STATES = new Set([
    'draft',
    'open',
    'approved',
    'changes_requested',
    'closed',
    'merged'
]);

const APPROVALS = new Set([
    'approved',
    'rejected',
    'pending',
    'dismissed',
    'not_required'
]);

const STATUS_CHECKS = new Set([
    'passed',
    'failed',
    'pending'
]);

function normalizeText(value) {
    if (value === null || value === undefined) {
        return null;
    }

    const text = String(value).trim().replace(/\s+/g, ' ');
    return text.length === 0 ? null : text;
}

function normalizeBranch(value) {
    const text = normalizeText(value);
    if (text === null) {
        return null;
    }

    return text.replace(/^refs\/heads\//, '').toLowerCase();
}

function normalizeEnum(value) {
    const text = normalizeText(value);
    return text === null ? null : text.toLowerCase();
}

function normalizeBoolean(value) {
    if (value === null || value === undefined) {
        return null;
    }

    if (typeof value === 'boolean') {
        return value;
    }

    const normalized = String(value).trim().toLowerCase();

    if (['true', 'yes', '1', 'y', 'on'].includes(normalized)) {
        return true;
    }

    if (['false', 'no', '0', 'n', 'off'].includes(normalized)) {
        return false;
    }

    return null;
}

class DataCleaner extends EventEmitter {
    constructor(records) {
        super();

        if (!Array.isArray(records)) {
            throw new CleaningError('Input must be an array.');
        }

        this.records = records;
    }

    normalize(records) {
        const output = records.map(source => ({
            ...source,
            repository: normalizeText(source.repository),
            source_branch: normalizeBranch(source.source_branch),
            target_branch: normalizeBranch(source.target_branch),
            reviewer: normalizeText(source.reviewer),
            review_state: normalizeEnum(source.review_state),
            approval: normalizeEnum(source.approval),
            status_check: normalizeEnum(source.status_check),
            draft: normalizeBoolean(source.draft),
            required_review: normalizeBoolean(source.required_review),
            conversation_resolved: normalizeBoolean(
                source.conversation_resolved
            ),
            force_push_allowed: normalizeBoolean(
                source.force_push_allowed
            )
        }));

        this.emit('normalized', output.length);
        return output;
    }

    validate(records) {
        const valid = [];
        let rejected = 0;

        for (const record of records) {
            const validRecord =
                record.pr_id !== null &&
                record.pr_id !== undefined &&
                record.repository &&
                record.source_branch &&
                record.target_branch &&
                REVIEW_STATES.has(record.review_state) &&
                APPROVALS.has(record.approval) &&
                STATUS_CHECKS.has(record.status_check);

            if (validRecord) {
                valid.push(record);
            } else {
                rejected++;
            }
        }

        this.emit('validated', {
            accepted: valid.length,
            rejected
        });

        return { valid, rejected };
    }

    deduplicate(records) {
        const seen = new Set();
        const unique = [];

        for (const record of records) {
            const key = [
                record.pr_id,
                record.repository,
                record.source_branch,
                record.target_branch,
                record.reviewer
            ].join('|');

            if (!seen.has(key)) {
                seen.add(key);
                unique.push(record);
            }
        }

        this.emit('deduplicated', {
            before: records.length,
            after: unique.length
        });

        return unique;
    }

    impute(records) {
        return records.map(record => {
            const output = { ...record };

            if (output.draft === null) {
                output.draft = output.review_state === 'draft';
            }

            if (output.required_review === null) {
                output.required_review =
                    ['main', 'master', 'production']
                        .includes(output.target_branch);
            }

            if (output.conversation_resolved === null) {
                output.conversation_resolved =
                    !['open', 'changes_requested']
                        .includes(output.review_state);
            }

            if (output.force_push_allowed === null) {
                output.force_push_allowed = false;
            }

            return output;
        });
    }

    static mergeEligible(record) {
        return (
            record.review_state === 'approved' &&
            record.approval === 'approved' &&
            record.status_check === 'passed' &&
            record.conversation_resolved === true
        );
    }

    clean() {
        const before = this.records.length;

        const normalized = this.normalize(this.records);
        const validation = this.validate(normalized);
        const unique = this.deduplicate(validation.valid);
        const cleaned = this.impute(unique).map(record => ({
            ...record,
            merge_eligible: DataCleaner.mergeEligible(record)
        }));

        return {
            records: cleaned,
            statistics: {
                rowsBefore: before,
                rowsAfter: cleaned.length,
                invalidRemoved: validation.rejected,
                duplicatesRemoved: validation.valid.length - unique.length
            }
        };
    }
}

const rawRecords = [
    {
        pr_id: 201,
        repository: 'orders-api',
        source_branch: 'refs/heads/feature/order-validation',
        target_branch: 'MAIN',
        reviewer: '  Kavita Rao ',
        review_state: 'APPROVED',
        approval: 'Approved',
        status_check: 'PASSED',
        draft: 'false',
        required_review: null,
        conversation_resolved: true,
        force_push_allowed: null
    },
    {
        pr_id: 201,
        repository: 'orders-api',
        source_branch: 'refs/heads/feature/order-validation',
        target_branch: 'MAIN',
        reviewer: 'Kavita Rao',
        review_state: 'approved',
        approval: 'approved',
        status_check: 'passed',
        draft: false,
        required_review: null,
        conversation_resolved: true,
        force_push_allowed: null
    },
    {
        pr_id: 202,
        repository: 'orders-api',
        source_branch: 'feature/refund',
        target_branch: 'main',
        reviewer: 'Sanjay',
        review_state: 'changes_requested',
        approval: 'pending',
        status_check: 'failed',
        draft: 'no',
        required_review: 'yes',
        conversation_resolved: 'no',
        force_push_allowed: 'no'
    },
    {
        pr_id: 203,
        repository: 'catalog-api',
        source_branch: 'feature/search',
        target_branch: 'develop',
        reviewer: null,
        review_state: 'open',
        approval: 'pending',
        status_check: 'pending',
        draft: null,
        required_review: null,
        conversation_resolved: null,
        force_push_allowed: null
    },
    {
        pr_id: 204,
        repository: 'catalog-api',
        source_branch: 'feature/indexes',
        target_branch: 'main',
        reviewer: 'Meera',
        review_state: 'approved',
        approval: 'approved',
        status_check: 'passed',
        draft: false,
        required_review: true,
        conversation_resolved: true,
        force_push_allowed: false
    },
    {
        pr_id: 205,
        repository: '',
        source_branch: 'feature/invalid',
        target_branch: 'main',
        reviewer: 'Invalid',
        review_state: 'approved',
        approval: 'approved',
        status_check: 'passed'
    }
];

const cleaner = new DataCleaner(rawRecords);

cleaner.on('normalized', count => {
    console.log(`Normalized records: ${count}`);
});

cleaner.on('validated', result => {
    console.log(
        `Validated records: ${result.accepted}; rejected: ${result.rejected}`
    );
});

cleaner.on('deduplicated', result => {
    console.log(
        `Duplicates removed: ${result.before - result.after}`
    );
});

const result = cleaner.clean();

console.log('\nDATA CLEANING REPORT');
console.log('='.repeat(60));
console.log(JSON.stringify(result.statistics, null, 2));

console.log('\nCLEANED DATA');
console.log('='.repeat(60));

for (const record of result.records) {
    console.log(
        `PR #${record.pr_id} | ` +
        `${record.repository} | ` +
        `${record.source_branch} -> ${record.target_branch} | ` +
        `review=${record.review_state} | ` +
        `approval=${record.approval} | ` +
        `check=${record.status_check} | ` +
        `merge=${record.merge_eligible}`
    );
}

if (result.records.length !== 4) {
    throw new CleaningError('Unexpected cleaned record count.');
}

if (result.statistics.duplicatesRemoved !== 1) {
    throw new CleaningError('Duplicate-removal validation failed.');
}

if (!result.records[0].merge_eligible) {
    throw new CleaningError('Merge-eligibility validation failed.');
}

console.log('\nValidation checks passed.');

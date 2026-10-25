'use strict';

/*
 * Dashboard architecture model for repository governance.
 * The implementation separates:
 *   - workflow state
 *   - review decisions
 *   - automated checks
 *   - repository-level policy
 *   - presentation metrics
 */

const PRState = Object.freeze({
  DRAFT: 'draft',
  OPEN: 'open',
  CLOSED: 'closed',
  MERGED: 'merged'
});

const ReviewState = Object.freeze({
  COMMENTED: 'commented',
  APPROVED: 'approved',
  CHANGES_REQUESTED: 'changes_requested',
  DISMISSED: 'dismissed'
});

const CheckState = Object.freeze({
  PASSING: 'passing',
  FAILING: 'failing',
  PENDING: 'pending'
});

const MergeStrategy = Object.freeze({
  MERGE_COMMIT: 'merge_commit',
  SQUASH: 'squash',
  REBASE: 'rebase'
});

class ValidationError extends Error {}

class RepositoryDashboard {
  constructor(repository) {
    this.repository = repository;
    this.validateRepository();
  }

  validateRepository() {
    if (!this.repository.name?.trim()) {
      throw new ValidationError('Repository name is required.');
    }

    if (!this.repository.branches.has('main')) {
      throw new ValidationError('The repository must contain main.');
    }

    for (const [branch, policy] of this.repository.protection) {
      if (!this.repository.branches.has(branch)) {
        throw new ValidationError(
          `Protection policy references unknown branch: ${branch}`
        );
      }

      if (!Number.isInteger(policy.requiredReviews) || policy.requiredReviews < 0) {
        throw new ValidationError('requiredReviews must be a non-negative integer.');
      }
    }

    for (const pr of this.repository.pullRequests.values()) {
      if (!this.repository.branches.has(pr.sourceBranch)) {
        throw new ValidationError(`Unknown source branch: ${pr.sourceBranch}`);
      }

      if (!this.repository.branches.has(pr.targetBranch)) {
        throw new ValidationError(`Unknown target branch: ${pr.targetBranch}`);
      }
    }
  }

  eligibleApprovers(pr) {
    const approved = new Set();

    for (const review of pr.reviews) {
      if (
        review.state === ReviewState.APPROVED &&
        this.repository.eligibleReviewers.has(review.reviewer)
      ) {
        approved.add(review.reviewer);
      }

      // A later changes-requested review from the same reviewer invalidates
      // that reviewer's active approval for this simplified model.
      if (
        review.state === ReviewState.CHANGES_REQUESTED &&
        this.repository.eligibleReviewers.has(review.reviewer)
      ) {
        approved.delete(review.reviewer);
      }
    }

    return approved;
  }

  unresolvedConversations(pr) {
    return pr.comments.filter(comment => !comment.resolved).length;
  }

  evaluateMerge(prNumber) {
    const pr = this.repository.pullRequests.get(prNumber);
    if (!pr) {
      throw new ValidationError(`Pull Request ${prNumber} does not exist.`);
    }

    const reasons = [];

    if (pr.state !== PRState.OPEN) {
      reasons.push('Pull Request is not open.');
    }

    if (pr.isDraft || pr.state === PRState.DRAFT) {
      reasons.push('Draft Pull Requests cannot be merged.');
    }

    const policy = this.repository.protection.get(pr.targetBranch);

    if (!policy) {
      reasons.push('Target branch has no protection policy.');
    } else {
      const approvals = this.eligibleApprovers(pr).size;

      if (approvals < policy.requiredReviews) {
        reasons.push(
          `Approval requirement is ${policy.requiredReviews}; ` +
          `eligible approvals are ${approvals}.`
        );
      }

      const checkMap = new Map(
        pr.statusChecks.map(check => [check.name, check.state])
      );

      for (const required of policy.requiredChecks) {
        if (checkMap.get(required) !== CheckState.PASSING) {
          reasons.push(`Required check '${required}' is not passing.`);
        }
      }

      if (
        policy.requireConversationResolution &&
        this.unresolvedConversations(pr) > 0
      ) {
        reasons.push('Unresolved review conversations remain.');
      }

      if (
        policy.requireLinearHistory &&
        pr.mergeStrategy === MergeStrategy.MERGE_COMMIT
      ) {
        reasons.push('Linear history is required.');
      }
    }

    return {
      eligible: reasons.length === 0,
      reasons
    };
  }

  metrics() {
    const prs = [...this.repository.pullRequests.values()];
    const open = prs.filter(pr => pr.state === PRState.OPEN);
    const drafts = prs.filter(pr => pr.isDraft || pr.state === PRState.DRAFT);
    const merged = prs.filter(pr => pr.state === PRState.MERGED);

    let mergeable = 0;

    for (const pr of open) {
      if (this.evaluateMerge(pr.number).eligible) {
        mergeable++;
      }
    }

    const unresolvedConversations = prs.reduce(
      (total, pr) => total + this.unresolvedConversations(pr),
      0
    );

    return {
      openPullRequests: open.length,
      draftPullRequests: drafts.length,
      mergeablePullRequests: mergeable,
      blockedPullRequests: open.length - mergeable,
      mergedPullRequests: merged.length,
      unresolvedConversations
    };
  }

  async refreshStatusChecks(prNumber, checkUpdates) {
    const pr = this.repository.pullRequests.get(prNumber);

    if (!pr) {
      throw new ValidationError(`Pull Request ${prNumber} does not exist.`);
    }

    /*
     * Promise-based processing models asynchronous CI/security systems.
     * The dashboard updates only known checks and does not execute arbitrary
     * commands, preventing dashboard data from becoming a command-injection path.
     */
    const results = await Promise.all(
      checkUpdates.map(async update => ({
        name: String(update.name),
        state: update.state
      }))
    );

    const existing = new Map(
      pr.statusChecks.map(check => [check.name, check])
    );

    for (const result of results) {
      if (!Object.values(CheckState).includes(result.state)) {
        throw new ValidationError(
          `Invalid status state for ${result.name}: ${result.state}`
        );
      }

      existing.set(result.name, {
        name: result.name,
        state: result.state,
        required: true
      });
    }

    pr.statusChecks = [...existing.values()];
    return this.evaluateMerge(prNumber);
  }

  render() {
    const m = this.metrics();

    return [
      'REPOSITORY GOVERNANCE DASHBOARD',
      '================================',
      `Open Pull Requests:       ${m.openPullRequests}`,
      `Draft Pull Requests:      ${m.draftPullRequests}`,
      `Mergeable Pull Requests:  ${m.mergeablePullRequests}`,
      `Blocked Pull Requests:    ${m.blockedPullRequests}`,
      `Merged Pull Requests:     ${m.mergedPullRequests}`,
      `Unresolved Conversations: ${m.unresolvedConversations}`
    ].join('\n');
  }
}

function createRepository() {
  const commits = [
    {
      sha: 'c001',
      message: 'Create dashboard architecture',
      author: 'alice'
    },
    {
      sha: 'c002',
      message: 'Add governance metrics',
      author: 'alice'
    }
  ];

  const pr = {
    number: 101,
    sourceBranch: 'feature/dashboard',
    targetBranch: 'main',
    title: 'Repository governance dashboard',
    state: PRState.OPEN,
    isDraft: false,
    commits,
    reviews: [
      { reviewer: 'bob', state: ReviewState.APPROVED },
      { reviewer: 'carol', state: ReviewState.APPROVED }
    ],
    comments: [
      {
        id: 1,
        reviewer: 'bob',
        body: 'Clarify metric ownership.',
        resolved: true
      },
      {
        id: 2,
        reviewer: 'carol',
        body: 'Please verify the policy label.',
        resolved: false
      }
    ],
    statusChecks: [
      { name: 'unit-tests', state: CheckState.PASSING },
      { name: 'security-scan', state: CheckState.PASSING }
    ],
    mergeStrategy: MergeStrategy.SQUASH
  };

  return {
    name: 'engineering-platform',
    branches: new Map([
      ['main', { name: 'main', protected: true }],
      ['feature/dashboard', { name: 'feature/dashboard', protected: false }]
    ]),
    pullRequests: new Map([[101, pr]]),
    eligibleReviewers: new Set(['alice', 'bob', 'carol', 'david']),
    protection: new Map([
      [
        'main',
        {
          requiredReviews: 2,
          requiredChecks: new Set(['unit-tests', 'security-scan']),
          requireConversationResolution: true,
          requireLinearHistory: true
        }
      ]
    ])
  };
}

async function main() {
  const dashboard = new RepositoryDashboard(createRepository());

  console.log(dashboard.render());

  const result = dashboard.evaluateMerge(101);

  console.log('\nMERGE ELIGIBILITY');
  console.log('=================');
  console.log(`Eligible: ${result.eligible}`);

  for (const reason of result.reasons) {
    console.log(`- ${reason}`);
  }

  await dashboard.refreshStatusChecks(101, [
    { name: 'unit-tests', state: CheckState.PASSING },
    { name: 'security-scan', state: CheckState.PASSING }
  ]);

  console.log('\nUPDATED POLICY EVALUATION');
  console.log('=========================');
  console.log(dashboard.evaluateMerge(101));
}

main().catch(error => {
  console.error(`Dashboard error: ${error.message}`);
  process.exitCode = 1;
});

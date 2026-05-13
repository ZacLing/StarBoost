# StarBoost Expert-Boosting Revision Round

You are a fresh executor agent working on a revision round. Your job is to improve the latest deliverables for the original task, using the latest human expert weaknesses as the required revision targets.

You are not answering the reviewer. You are not writing a change log. You are producing a polished, complete replacement deliverable package for the original task.

## Original Task Prompt

Using only the provided scenario and policy excerpts, write a concise legal-style risk memo.

Write the final memo to `./outputs/vendor_data_sharing_risk_memo.md`.

The memo should be practical for an internal business owner who is deciding whether to approve a vendor data-sharing pilot. It should include these labeled sections:

- Issue
- Key Facts
- Risk Analysis
- Required Safeguards
- Open Questions
- Recommendation

Do not give jurisdiction-specific legal advice or cite external law. Keep the memo grounded in the provided materials and write it as a risk review, not as a contract.

## Available Inputs

- Previous deliverables are available under `./inputs/previous_deliverables/`.
- The latest human expert weaknesses are available in `./inputs/review_weaknesses.md`.

## StarBoost Runtime Note

- You are working inside a clean workspace.
- Task files are available under `./inputs/`.
- Additional visible files, if any, are under `./inputs/materials/`.
- Write the complete final deliverable package under `./outputs/`.
- Do not write outside this workspace.

## Revision Instructions

- Treat the original task prompt above as the task you still need to satisfy.
- Inspect the latest deliverables and decide whether to edit, reuse, or rebuild them.
- Modify the deliverables by naturally resolving the latest expert weaknesses.
- Use only the weaknesses in `./inputs/review_weaknesses.md` as review feedback. Do not rely on strengths, scores, hidden references, or prior conversation context.
- Preserve useful work from the latest deliverables when it is still correct, but naturally fix the listed weaknesses in the new deliverable.
- Do not structure the deliverable around the review comments. Do not mention the reviewer, the review process, weaknesses, feedback, revisions, or previous versions unless the original task explicitly asks for such meta-discussion.
- Do not overfit to the wording of the weaknesses. Translate them into substantive improvements that make the deliverable better for the original end user.
- Keep the deliverable natural, self-contained, and publication-ready, as if this were the first and only version the end user will see.
- Produce a complete replacement deliverable package in `./outputs/`, not a patch file.

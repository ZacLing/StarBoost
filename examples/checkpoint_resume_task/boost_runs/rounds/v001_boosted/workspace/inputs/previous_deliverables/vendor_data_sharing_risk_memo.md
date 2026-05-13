# Vendor Data-Sharing Pilot Risk Memo

## Issue

Whether the business owner should approve a 60-day vendor pilot in which support-ticket text will be uploaded to a vendor portal for analysis of common customer pain points.

## Key Facts

- The proposed pilot will last 60 days.
- The vendor will analyze support-ticket text to identify common customer pain points.
- The dataset may include customer names, email addresses, free-text complaint details, product usage notes, and support-agent notes.
- The vendor says it can start immediately if the company uploads the files to the vendor portal.
- Internal policy requires personal data minimization before vendor sharing.
- Internal policy requires vendor pilots involving customer data to have a written purpose statement, access limitation, retention limit, and deletion confirmation.
- Internal policy requires review of sensitive free-text fields because they may contain unexpected personal data.
- Vendors may not use pilot data to train general-purpose models unless explicitly approved in writing.
- Business owners must document open questions before approval.

## Risk Analysis

The pilot presents a meaningful data-sharing risk because the proposed dataset may contain direct identifiers and sensitive free-text content. Customer names and email addresses are personal data and should not be shared unless needed for the pilot purpose. Free-text complaint details, product usage notes, and support-agent notes require particular review because they may contain unexpected personal data beyond what the product team intends to share.

The vendor's ability to start immediately does not remove the need for internal controls before upload. Under the policy excerpts, approval should not occur until the business owner has documented the pilot purpose, limited vendor access, set a retention limit, and obtained deletion confirmation expectations. Uploading files before these controls are documented would create a policy compliance gap.

There is also a specific model-use risk. The vendor may not use pilot data to train general-purpose models unless explicitly approved in writing. If the vendor's portal terms or pilot workflow permit general-purpose model training by default, the pilot should not proceed without written approval or an express restriction preventing that use.

## Required Safeguards

- Create a written purpose statement limiting the pilot to analysis of support-ticket text for identifying common customer pain points.
- Minimize the dataset before upload, including removing or masking customer names, email addresses, and any other personal data not needed for the pilot.
- Review sensitive free-text fields before sharing to identify and remove unexpected personal data where feasible.
- Limit vendor access to personnel and systems necessary to conduct the 60-day pilot.
- Set a retention limit aligned to the pilot period and any needed closeout period.
- Require deletion confirmation after the retention period or pilot termination.
- Confirm in writing that the vendor may not use pilot data to train general-purpose models unless separately and explicitly approved in writing.

## Open Questions

- Which specific support-ticket fields are necessary for the pilot purpose?
- Can customer names and email addresses be removed or masked before upload?
- Who will review free-text complaint details, product usage notes, and support-agent notes before sharing?
- What vendor personnel or systems will have access to the uploaded files?
- What retention period will apply after the 60-day pilot ends?
- How and when will the vendor provide deletion confirmation?
- Does the vendor use, or reserve the right to use, uploaded pilot data to train general-purpose models?

## Recommendation

Do not approve immediate upload of the files. The pilot may be approved only after the required safeguards are documented and the open questions are resolved. If the team can minimize the dataset, review free-text fields, define access and retention limits, obtain deletion confirmation, and restrict general-purpose model training use in writing, the pilot risk appears manageable for a limited 60-day test.

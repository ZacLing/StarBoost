# Vendor Data-Sharing Pilot Risk Memo

## Issue

Whether the business owner should approve a 60-day vendor pilot in which support-ticket text will be uploaded to a vendor portal for analysis of common customer pain points.

## Key Facts

- The product team proposes a 60-day pilot with a vendor to analyze support-ticket text and identify common customer pain points.
- The dataset may include customer names, email addresses, free-text complaint details, product usage notes, and support-agent notes.
- The vendor says it can start immediately if the company uploads the files to the vendor portal.
- Internal policy requires personal data to be minimized before vendor sharing.
- Internal policy requires customer-data vendor pilots to have a written purpose statement, access limitation, retention limit, and deletion confirmation.
- Internal policy requires review of sensitive free-text fields because they may contain unexpected personal data.
- Vendors may not use pilot data to train general-purpose models unless explicitly approved in writing.
- Business owners must document open questions before approval.

## Risk Analysis

The proposed pilot creates moderate data-sharing risk because the support-ticket dataset may contain direct identifiers and sensitive free-text content. Customer names and email addresses are personal data and should not be uploaded unless they are necessary for the stated pilot purpose. Free-text complaint details, product usage notes, and support-agent notes are higher-risk fields because they may include unexpected personal data that the product team does not intend to share.

The vendor's readiness to start immediately does not satisfy the company's pre-approval requirements. Before any upload, the business owner must ensure the pilot purpose is written, the dataset is minimized, sensitive free-text fields are reviewed, vendor access is limited, retention is capped, and deletion confirmation is addressed. Uploading the files first and documenting controls later would create a policy gap.

There is also a specific secondary-use and model-training risk. The policy prohibits vendor use of pilot data to train general-purpose models unless explicitly approved in writing. If the vendor portal terms, default product settings, or pilot workflow permit retention, secondary use, or model training by default, the pilot should not proceed unless those permissions are turned off or expressly overridden in writing.

## Required Safeguards

Pre-approval blockers before any upload:

- Business owner: approve a written purpose statement limiting the pilot to analysis of support-ticket text for identifying common customer pain points during the 60-day pilot.
- Data steward: identify the minimum support-ticket fields needed for that purpose and remove or mask customer names, email addresses, and other personal data not needed for the analysis.
- Legal/privacy reviewer: review the proposed free-text fields, including complaint details, product usage notes, and support-agent notes, for unexpected personal data and determine whether additional redaction or sampling is required before sharing.
- Vendor manager: confirm the vendor access limitation in writing, including which vendor personnel, systems, or portal functions may access the uploaded files.
- Vendor manager: set a written retention limit for the pilot data, tied to the 60-day pilot and any defined closeout period.
- Vendor manager, with legal/privacy reviewer: confirm in writing that the vendor may not use pilot data for general-purpose model training unless separately and explicitly approved in writing.
- Business owner: document all unresolved questions and confirm they are resolved or accepted before approving upload.

Post-approval operating controls:

- Business owner: ensure only the approved, minimized dataset is uploaded to the vendor portal.
- Data steward: keep a record of the fields shared and the minimization steps applied.
- Vendor manager: monitor that vendor access remains limited to the approved pilot purpose and approved access scope.
- Vendor manager: obtain deletion confirmation at the end of the retention period or upon earlier pilot termination.
- Business owner: stop further sharing if the vendor requests expanded data, expanded use, longer retention, or model-training rights before those changes are reviewed and approved in writing.

## Open Questions

- Which specific support-ticket fields are necessary to identify common customer pain points?
- Can customer names and email addresses be removed or masked before upload without undermining the pilot?
- Who will review free-text complaint details, product usage notes, and support-agent notes before sharing?
- What vendor personnel, systems, and portal functions will have access to the uploaded files?
- Do the vendor portal terms, default settings, or pilot terms permit retention, secondary use, or model training by default, and if so, how will those permissions be disabled or overridden in writing?
- What retention period will apply after the 60-day pilot ends?
- How and when will the vendor provide deletion confirmation?

## Recommendation

Do not approve immediate upload of the files. The business owner may approve the pilot only after the pre-approval blockers are completed and the open questions are documented and resolved. If the team minimizes the dataset, reviews the free-text fields, confirms access and retention limits, obtains deletion-confirmation commitments, and restricts secondary use and general-purpose model training in writing, the pilot risk appears manageable for a limited 60-day test.

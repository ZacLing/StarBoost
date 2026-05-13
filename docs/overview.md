# StarBoost Overview

StarBoost runs an expert-feedback loop around a Codex-style executor:

1. Load a task package.
2. Run a cold-start executor once in an isolated workspace.
3. Ask a human expert to review the latest deliverable.
4. Validate the review against a minimum number of strengths and weaknesses.
5. Use the latest expert weaknesses to produce an updated deliverable.
6. Repeat until the expert submits zero weaknesses after the minimum has decayed to zero; experts can always add more weaknesses to continue another round.
7. Export the complete run history.

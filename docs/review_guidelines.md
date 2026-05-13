# Review Guidelines

Each review should be concrete enough for the next AI round to improve the deliverable without seeing the expert's hidden reasoning.

The review has two audiences:

- StarBoost reads the structured strengths and weaknesses for validation and the next prompt.
- The next executor receives only the weaknesses, not the strengths, scores, rubrics, or human reference.

Default policy:

- At least three strengths.
- At least five weaknesses in the first review.
- The minimum weakness count decreases by one after each accepted review.
- The minimum weakness count is only a lower bound; experts can write more weaknesses whenever the result still needs work.
- When the minimum reaches zero, submitting zero weaknesses ends the loop. Submitting one or more weaknesses continues to the next round.
- The review must include exactly the two StarBoost scores:
  - `Latest Deliverables Satisfaction`: integer 1-5, where 5 means very satisfied and 1 means very dissatisfied with the current version.
  - `Latest Deliverables Aligns User Scores`: integer 1-10, where 5 means roughly the level the expert personally would have achieved on this task.
- Duplicated strengths or weaknesses are rejected during submission.

Good weakness:

```text
- The API behavior section describes search endpoints but does not specify error response JSON for invalid query parameters.
```

Weak weakness:

```text
- Make it better.
```

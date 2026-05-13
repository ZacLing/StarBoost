# Review Guidelines

Each review should be concrete enough for a fresh executor to improve the deliverable without seeing the expert's hidden reasoning.

The review has two audiences:

- StarBoost reads the structured strengths and weaknesses for validation and the next prompt.
- The next executor receives only the weaknesses, not the strengths, scores, rubrics, or human reference.

Default policy:

- At least three strengths.
- At least five weaknesses in the first review.
- The minimum weakness count decreases by one after each accepted review.
- The minimum weakness count is only a lower bound; experts can write more weaknesses whenever the result still needs work.
- When the minimum reaches zero, submitting zero weaknesses ends the loop. Submitting one or more weaknesses continues to the next round.

Good weakness:

```text
- The API behavior section describes search endpoints but does not specify error response JSON for invalid query parameters.
```

Weak weakness:

```text
- Make it better.
```

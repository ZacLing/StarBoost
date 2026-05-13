from pathlib import Path

from starboost.review import parse_review, validate_review


def test_parse_review_strengths_weaknesses_and_scores(tmp_path: Path) -> None:
    review = tmp_path / "r001_review" / "review.md"
    review.parent.mkdir()
    review.write_text(
        """# Review

## Scores
- correctness: 4/5
- overall: 8.5/10

## Strengths
- Clear structure.
- Uses the source material.

## Weaknesses
- Missing an explicit risk register.
- The timeline lacks owners.

## Notes
Keep it concise.
""",
        encoding="utf-8",
    )
    parsed = parse_review(review)
    assert parsed.strengths == ["Clear structure.", "Uses the source material."]
    assert parsed.weaknesses == ["Missing an explicit risk register.", "The timeline lacks owners."]
    assert parsed.scores["correctness"]["value"] == 4
    assert parsed.scores["overall"]["max"] == 10
    validation = validate_review(parsed, min_strengths=2, min_weaknesses=2)
    assert validation["valid"] is True


def test_review_validation_rejects_too_few_weaknesses(tmp_path: Path) -> None:
    review = tmp_path / "r001_review" / "review.md"
    review.parent.mkdir()
    review.write_text(
        """## Strengths
- One

## Weaknesses

""",
        encoding="utf-8",
    )
    parsed = parse_review(review)
    validation = validate_review(parsed, min_strengths=1, min_weaknesses=1)
    assert validation["valid"] is False
    assert "weaknesses" in validation["errors"][0]


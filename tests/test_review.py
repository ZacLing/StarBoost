from pathlib import Path

from starboost.review import create_review_template, parse_review, validate_review


def test_parse_review_strengths_weaknesses_and_scores(tmp_path: Path) -> None:
    review = tmp_path / "r001_review" / "review.md"
    review.parent.mkdir()
    review.write_text(
        """# Review

## Strengths
- Clear structure.
- Uses the source material.

## Weaknesses
- Missing an explicit risk register.
- The timeline lacks owners.

## Latest Deliverables Satisfaction
(4)/5

## Latest Deliverables Aligns User Scores
(8)/10

## Notes
Keep it concise.
""",
        encoding="utf-8",
    )
    parsed = parse_review(review)
    assert parsed.strengths == ["Clear structure.", "Uses the source material."]
    assert parsed.weaknesses == ["Missing an explicit risk register.", "The timeline lacks owners."]
    assert parsed.scores["latest_deliverables_satisfaction"]["value"] == 4
    assert parsed.scores["latest_deliverables_aligns_user_score"]["max"] == 10
    validation = validate_review(parsed, min_strengths=2, min_weaknesses=2)
    assert validation["valid"] is True


def test_review_validation_rejects_too_few_weaknesses(tmp_path: Path) -> None:
    review = tmp_path / "r001_review" / "review.md"
    review.parent.mkdir()
    review.write_text(
        """## Strengths
- One

## Weaknesses

## Latest Deliverables Satisfaction
(3)/5

## Latest Deliverables Aligns User Scores
(5)/10

""",
        encoding="utf-8",
    )
    parsed = parse_review(review)
    validation = validate_review(parsed, min_strengths=1, min_weaknesses=1)
    assert validation["valid"] is False
    assert "weaknesses" in validation["errors"][0]


def test_review_validation_rejects_missing_scores(tmp_path: Path) -> None:
    review = tmp_path / "r001_review" / "review.md"
    review.parent.mkdir()
    review.write_text(
        """## Strengths
- One

## Weaknesses
- One
""",
        encoding="utf-8",
    )
    parsed = parse_review(review)
    validation = validate_review(parsed, min_strengths=1, min_weaknesses=1)
    assert validation["valid"] is False
    assert any("Satisfaction" in error for error in validation["errors"])


def test_review_validation_rejects_duplicate_comments(tmp_path: Path) -> None:
    review = tmp_path / "r001_review" / "review.md"
    review.parent.mkdir()
    review.write_text(
        """## Strengths
- Same
- Same

## Weaknesses
- Different

## Latest Deliverables Satisfaction
(3)/5

## Latest Deliverables Aligns User Scores
(5)/10
""",
        encoding="utf-8",
    )
    parsed = parse_review(review)
    validation = validate_review(parsed, min_strengths=1, min_weaknesses=1)
    assert validation["valid"] is False
    assert any("Duplicate strengths" in error for error in validation["errors"])


def test_review_template_has_clear_visual_fill_areas(tmp_path: Path) -> None:
    review = tmp_path / "r001_review" / "review.md"
    review.parent.mkdir()
    create_review_template(review, "demo", "v000_cold_start", tmp_path / "outputs", 3, 2)
    text = review.read_text(encoding="utf-8")
    assert text.startswith("# StarBoost Review - Reviewing `v000_cold_start`")
    assert "| Minimum strengths required | `3` |" in text
    assert "| Minimum weaknesses required | `2` |" in text
    assert text.count("---") >= 5
    assert "> Write strengths below." in text
    assert "> Write weaknesses below." in text
    assert "> Write the score below." in text

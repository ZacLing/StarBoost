from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .util import utc_now, write_json, write_text


@dataclass
class ParsedReview:
    review_id: str
    strengths: List[str]
    weaknesses: List[str]
    scores: Dict[str, Dict[str, float]]
    notes: str


def review_id(index: int) -> str:
    return f"r{index:03d}_review"


def review_dir(package_root: Path, index: int) -> Path:
    return package_root / "boost_runs" / "reviews" / review_id(index)


def create_review_template(
    path: Path,
    package_id: str,
    round_id: str,
    deliverables_path: Path,
    min_strengths: int,
    min_weaknesses: int,
) -> None:
    strengths = "\n".join("- " for _ in range(max(min_strengths, 1)))
    weaknesses = "\n".join("- " for _ in range(min_weaknesses))
    template = f"""# StarBoost Review - Reviewing `{round_id}`

## Task Information

| Field | Value |
| --- | --- |
| Review ID | `{path.parent.name}` |
| Package | `{package_id}` |
| Round under review | `{round_id}` |
| Deliverables path | `{deliverables_path}` |
| Created at | `{utc_now()}` |
| Minimum strengths required | `{min_strengths}` |
| Minimum weaknesses required | `{min_weaknesses}` |

---

## Human-Reviewer Comments

### Strengths

> Please provide at least {min_strengths} distinct strengths of the current deliverables.
> Write strengths below.

{strengths}

---

### Weaknesses

> Please provide at least {min_weaknesses} distinct weaknesses in this round.
> This number is only a lower bound; you may write more if the deliverables still need work.
> If the minimum is 0 and you write no weaknesses, the boosting loop will terminate.
> Write weaknesses below.

{weaknesses}

---

### Latest Deliverables Satisfaction

> Score the current deliverables only.
> Use an integer from 1 to 5, where 5 means very satisfied and 1 means very dissatisfied.
> Write the score below.

()/5

---

### Latest Deliverables Aligns User Scores

> Score the current deliverables against your own expected performance on this task.
> Use an integer from 1 to 10. Treat 5 as the level you personally would have achieved on this task.
> Write the score below.

()/10

---

### Notes

> Optional notes for yourself or future audit context.


"""
    write_text(path, template)


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^#+\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^#+\s+", text[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _bullets(section: str) -> List[str]:
    bullets: List[str] = []
    for line in section.splitlines():
        match = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if match:
            value = match.group(1).strip()
            if value and value not in {"_", "TBD", "N/A"}:
                bullets.append(value)
    return bullets


def _scores(section: str) -> Dict[str, Dict[str, float]]:
    scores: Dict[str, Dict[str, float]] = {}
    pattern = re.compile(r"^\s*[-*]\s*([^:]+):\s*([0-9]+(?:\.[0-9]+)?)?\s*/\s*([0-9]+(?:\.[0-9]+)?)", re.MULTILINE)
    for match in pattern.finditer(section):
        if not match.group(2):
            continue
        name = match.group(1).strip().lower().replace(" ", "_")
        scores[name] = {"value": float(match.group(2)), "max": float(match.group(3))}
    return scores


def _score_from_named_section(text: str, heading: str, max_value: int) -> Optional[Dict[str, float]]:
    section = _section(text, heading)
    if not section:
        return None
    match = re.search(r"\(?\s*([0-9]+(?:\.[0-9]+)?)\s*\)?\s*/\s*([0-9]+(?:\.[0-9]+)?)", section)
    if not match:
        return None
    return {"value": float(match.group(1)), "max": float(match.group(2) or max_value)}


def parse_review(path: Path) -> ParsedReview:
    text = path.read_text(encoding="utf-8")
    scores = _scores(_section(text, "Scores"))
    satisfaction = _score_from_named_section(text, "Latest Deliverables Satisfaction", 5)
    if satisfaction:
        scores["latest_deliverables_satisfaction"] = satisfaction
    aligns_user = _score_from_named_section(text, "Latest Deliverables Aligns User Scores", 10)
    if aligns_user:
        scores["latest_deliverables_aligns_user_score"] = aligns_user
    return ParsedReview(
        review_id=path.parent.name,
        strengths=_bullets(_section(text, "Strengths")),
        weaknesses=_bullets(_section(text, "Weaknesses")),
        scores=scores,
        notes=_section(text, "Notes"),
    )


def validate_review(parsed: ParsedReview, min_strengths: int, min_weaknesses: int) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    if len(parsed.strengths) < min_strengths:
        errors.append(f"Expected at least {min_strengths} strengths, found {len(parsed.strengths)}")
    if len(parsed.weaknesses) < min_weaknesses:
        errors.append(f"Expected at least {min_weaknesses} weaknesses, found {len(parsed.weaknesses)}")
    satisfaction = parsed.scores.get("latest_deliverables_satisfaction")
    aligns_user = parsed.scores.get("latest_deliverables_aligns_user_score")
    if not satisfaction:
        errors.append("Missing Latest Deliverables Satisfaction score in the form `()/5`")
    elif satisfaction.get("max") != 5 or not float(satisfaction.get("value", 0)).is_integer() or not 1 <= int(satisfaction["value"]) <= 5:
        errors.append("Latest Deliverables Satisfaction must be an integer from 1 to 5")
    if not aligns_user:
        errors.append("Missing Latest Deliverables Aligns User Scores score in the form `()/10`")
    elif aligns_user.get("max") != 10 or not float(aligns_user.get("value", 0)).is_integer() or not 1 <= int(aligns_user["value"]) <= 10:
        errors.append("Latest Deliverables Aligns User Scores must be an integer from 1 to 10")
    duplicate_strengths = sorted({item for item in parsed.strengths if parsed.strengths.count(item) > 1})
    duplicate_weaknesses = sorted({item for item in parsed.weaknesses if parsed.weaknesses.count(item) > 1})
    if duplicate_strengths:
        errors.append(f"Duplicate strengths found: {duplicate_strengths}")
    if duplicate_weaknesses:
        errors.append(f"Duplicate weaknesses found: {duplicate_weaknesses}")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def save_review_json(path: Path, parsed: ParsedReview, validation: Dict[str, Any]) -> None:
    write_json(
        path,
        {
            "review_id": parsed.review_id,
            "created_at": utc_now(),
            "strengths": parsed.strengths,
            "weaknesses": parsed.weaknesses,
            "scores": parsed.scores,
            "notes": parsed.notes,
            "validation": validation,
        },
    )

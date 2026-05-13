from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

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
    weaknesses = "\n".join("- " for _ in range(max(min_weaknesses, 1)))
    template = f"""# StarBoost Review

Review ID: {path.parent.name}
Package: {package_id}
Round under review: {round_id}
Deliverables path: {deliverables_path}
Created at: {utc_now()}

## Scores
- correctness: /5
- completeness: /5
- clarity: /5
- overall: /10

## Strengths
{strengths}

## Weaknesses
{weaknesses}

## Notes

"""
    write_text(path, template)


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], flags=re.MULTILINE)
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


def parse_review(path: Path) -> ParsedReview:
    text = path.read_text(encoding="utf-8")
    return ParsedReview(
        review_id=path.parent.name,
        strengths=_bullets(_section(text, "Strengths")),
        weaknesses=_bullets(_section(text, "Weaknesses")),
        scores=_scores(_section(text, "Scores")),
        notes=_section(text, "Notes"),
    )


def validate_review(parsed: ParsedReview, min_strengths: int, min_weaknesses: int) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    if len(parsed.strengths) < min_strengths:
        errors.append(f"Expected at least {min_strengths} strengths, found {len(parsed.strengths)}")
    if len(parsed.weaknesses) < min_weaknesses:
        errors.append(f"Expected at least {min_weaknesses} weaknesses, found {len(parsed.weaknesses)}")
    if not parsed.scores:
        warnings.append("No numeric scores were parsed from the Scores section")
    duplicate_weaknesses = sorted({item for item in parsed.weaknesses if parsed.weaknesses.count(item) > 1})
    if duplicate_weaknesses:
        warnings.append(f"Duplicate weaknesses found: {duplicate_weaknesses}")
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


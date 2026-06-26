#!/usr/bin/env python3
"""Calculate content structure scores from a CSV file."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


SCORE_FIELDS = {
    "Hook 30%": 0.3,
    "证言 40%": 0.4,
    "卖点 20%": 0.2,
    "CTA 10%": 0.1,
}


def parse_score(value: str, field_name: str) -> tuple[float | None, str | None]:
    raw_value = (value or "").strip()
    if raw_value == "":
        return None, f"{field_name} 为空"

    try:
        score = float(raw_value)
    except ValueError:
        return None, f"{field_name} 不是数字"

    if score < 0 or score > 10:
        return None, f"{field_name} 超出 0-10"

    return score, None


def classify(total_score: float) -> str:
    if total_score >= 7:
        return "优先验证"
    if total_score >= 4:
        return "观察优化"
    return "不建议直投"


def score_row(row: dict[str, str]) -> dict[str, str]:
    errors: list[str] = []
    total_score = 0.0

    for field_name, weight in SCORE_FIELDS.items():
        score, error = parse_score(row.get(field_name, ""), field_name)
        if error:
            errors.append(error)
            continue
        total_score += score * weight

    output_row = dict(row)
    if errors:
        output_row["总分"] = ""
        output_row["分档等级"] = ""
        output_row["错误信息"] = "；".join(errors)
    else:
        output_row["总分"] = f"{total_score:.1f}"
        output_row["分档等级"] = classify(total_score)
        output_row["错误信息"] = ""

    return output_row


def score_file(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", newline="", encoding="utf-8-sig") as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames is None:
            raise ValueError("输入 CSV 缺少表头")

        output_fields = list(reader.fieldnames)
        for field_name in ("总分", "分档等级", "错误信息"):
            if field_name not in output_fields:
                output_fields.append(field_name)

        rows = [score_row(row) for row in reader]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/score_content.py input.csv output.csv", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        score_file(input_path, output_path)
    except Exception as exc:
        print(f"Failed to score file: {exc}", file=sys.stderr)
        return 1

    print(f"Scored CSV written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

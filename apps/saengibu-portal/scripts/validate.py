"""성취기준 JSONL 검증기. JSON Schema + 정규식 + 레벨 일관성."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "standard.schema.json"

app = typer.Typer()


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate_levels(row: dict, line_no: int) -> list[str]:
    errors: list[str] = []
    scale = row.get("eval_scale")
    levels = row.get("levels") or []
    if not levels:
        return errors  # 레벨 누락은 별도 verify_coverage.py 책임
    if scale == "5grade":
        expected = {"A", "B", "C", "D", "E"}
    elif scale == "3grade":
        expected = {"A", "B", "C"}
    elif scale == "P/F":
        expected = {"P", "F"}
    else:
        errors.append(f"line {line_no}: unknown eval_scale {scale!r}")
        return errors
    actual = {lv.get("level") for lv in levels}
    if actual != expected:
        missing = expected - actual
        extra = actual - expected
        errors.append(
            f"line {line_no}: levels mismatch (missing={sorted(missing)}, extra={sorted(extra)})"
        )
    return errors


@app.command()
def validate(
    path: Path = typer.Argument(..., exists=True, readable=True, help="JSONL 파일 경로"),
) -> None:
    """JSONL 한 줄씩 schema + 레벨 정합성 검증. 실패 시 exit 1."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        typer.echo("jsonschema 패키지가 필요합니다: uv pip install jsonschema", err=True)
        raise typer.Exit(2)

    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors_total: list[str] = []
    seen_codes: set[str] = set()

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                errors_total.append(f"line {line_no}: invalid JSON ({e})")
                continue
            for err in validator.iter_errors(row):
                errors_total.append(f"line {line_no}: schema {list(err.path)} {err.message}")
            errors_total.extend(_validate_levels(row, line_no))
            code = row.get("code")
            if code in seen_codes:
                errors_total.append(f"line {line_no}: duplicate code {code}")
            seen_codes.add(code)

    if errors_total:
        for err in errors_total:
            typer.echo(err, err=True)
        typer.echo(f"\n총 오류 {len(errors_total)}건", err=True)
        raise typer.Exit(1)
    typer.echo(f"OK: {path} ({len(seen_codes)}개 성취기준)")


if __name__ == "__main__":
    app()

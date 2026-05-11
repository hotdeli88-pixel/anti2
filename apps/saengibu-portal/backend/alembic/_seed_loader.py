"""Alembic 시드 마이그레이션 공용 헬퍼.

각 0008..0011 마이그레이션이 호출:
- load_subject(subject_code, jsonl_filename, source_doc_label)
- unload_subject(subject_code, school_level)

JSONL 위치: apps/saengibu-portal/data/processed/{filename}
ON CONFLICT (curriculum, code) DO UPDATE 로 멱등성 보장.
"""
from __future__ import annotations

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

# alembic/_seed_loader.py 기준 상대 경로
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


def _read_jsonl(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        raise RuntimeError(f"seed file not found: {path}")
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"{filename}:{line_no} invalid JSON: {e}") from e
    return rows


def load_subject(subject_code: str, jsonl_filename: str, source_doc_label: str) -> None:
    """Upsert standards + 동반 levels."""
    rows = _read_jsonl(jsonl_filename)
    rows = [r for r in rows if r.get("subject_code") == subject_code]
    if not rows:
        return

    conn = op.get_bind()

    # 1) Upsert achievement_standards
    upsert_sql = sa.text(
        """
        INSERT INTO achievement_standards (
            curriculum, school_level, grade, subject_code,
            domain, domain_code, unit_code, unit_title,
            code, statement, eval_scale, min_achievement,
            area_category, source_doc, source_json,
            rules_version, active
        ) VALUES (
            :curriculum, :school_level, :grade, :subject_code,
            :domain, :domain_code, :unit_code, :unit_title,
            :code, :statement, :eval_scale, :min_achievement,
            :area_category, :source_doc, CAST(:source_json AS JSONB),
            :rules_version, TRUE
        )
        ON CONFLICT (curriculum, code) DO UPDATE SET
            school_level = EXCLUDED.school_level,
            grade = EXCLUDED.grade,
            subject_code = EXCLUDED.subject_code,
            domain = EXCLUDED.domain,
            domain_code = EXCLUDED.domain_code,
            unit_code = EXCLUDED.unit_code,
            unit_title = EXCLUDED.unit_title,
            statement = EXCLUDED.statement,
            eval_scale = EXCLUDED.eval_scale,
            min_achievement = EXCLUDED.min_achievement,
            area_category = EXCLUDED.area_category,
            source_doc = EXCLUDED.source_doc,
            source_json = EXCLUDED.source_json,
            rules_version = EXCLUDED.rules_version,
            updated_at = NOW()
        """
    )

    for r in rows:
        conn.execute(
            upsert_sql,
            {
                "curriculum": r["curriculum"],
                "school_level": r["school_level"],
                "grade": r["grade"],
                "subject_code": r["subject_code"],
                "domain": r.get("domain"),
                "domain_code": r.get("domain_code"),
                "unit_code": r.get("unit_code"),
                "unit_title": r.get("unit_title"),
                "code": r["code"],
                "statement": r["statement"],
                "eval_scale": r["eval_scale"],
                "min_achievement": r.get("min_achievement"),
                "area_category": r.get("area_category"),
                "source_doc": source_doc_label,
                "source_json": json.dumps(r.get("source") or {}, ensure_ascii=False),
                "rules_version": r.get("rules_version", "2022-33"),
            },
        )

    # 2) achievement_levels: 기존 행 삭제 후 일괄 재삽입 (멱등성)
    codes = [r["code"] for r in rows]
    conn.execute(
        sa.text(
            """
            DELETE FROM achievement_levels
             WHERE standard_id IN (
                SELECT id FROM achievement_standards
                 WHERE curriculum = :curriculum AND code = ANY(:codes)
             )
            """
        ),
        {"curriculum": rows[0]["curriculum"], "codes": codes},
    )

    insert_level_sql = sa.text(
        """
        INSERT INTO achievement_levels (
            standard_id, level, scale, descriptor, order_index,
            cutline_hint, source_doc
        )
        SELECT s.id, :level, :scale, :descriptor, :order_index,
               :cutline_hint, :source_doc
          FROM achievement_standards s
         WHERE s.curriculum = :curriculum AND s.code = :code
        """
    )

    for r in rows:
        for lv in r.get("levels") or []:
            conn.execute(
                insert_level_sql,
                {
                    "curriculum": r["curriculum"],
                    "code": r["code"],
                    "level": lv["level"],
                    "scale": lv.get("scale", r["eval_scale"]),
                    "descriptor": lv["descriptor"],
                    "order_index": lv["order_index"],
                    "cutline_hint": lv.get("cutline_hint"),
                    "source_doc": source_doc_label,
                },
            )


def unload_subject(subject_code: str, school_level: str) -> None:
    """Downgrade: 해당 과목·학교급 standards 와 levels 삭제."""
    op.execute(
        sa.text(
            """
            DELETE FROM achievement_levels
             WHERE standard_id IN (
                SELECT id FROM achievement_standards
                 WHERE subject_code = :subject AND school_level = :school
                   AND curriculum = '2022_revised'
             )
            """
        ).bindparams(subject=subject_code, school=school_level)
    )
    op.execute(
        sa.text(
            """
            DELETE FROM achievement_standards
             WHERE subject_code = :subject AND school_level = :school
               AND curriculum = '2022_revised'
            """
        ).bindparams(subject=subject_code, school=school_level)
    )

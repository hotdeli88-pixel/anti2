"""학교급 × 학년 × 과목 × 성취기준/성취수준 커버리지 리포트."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import date
from pathlib import Path

import typer
from sqlalchemy import select, func

from app.core.db import SessionLocal, set_tenant
from app.models.standards import AchievementLevel, AchievementStandard

app = typer.Typer()


@app.command()
def report(
    out: Path = typer.Option(
        Path("data/reports/coverage.md"),
        help="리포트 출력 경로 (Markdown)",
    ),
    fail_under: int = typer.Option(
        0, help="중학교 MVP 4과목에서 학년당 최소 성취기준 수 (미달 시 exit 1)"
    ),
) -> None:
    asyncio.run(_run(out, fail_under))


async def _run(out: Path, fail_under: int) -> None:
    async with SessionLocal() as db:
        await set_tenant(db, None)
        rows = await db.execute(
            select(
                AchievementStandard.curriculum,
                AchievementStandard.school_level,
                AchievementStandard.grade,
                AchievementStandard.subject_code,
                func.count(AchievementStandard.id).label("standard_count"),
            )
            .where(AchievementStandard.active.is_(True))
            .group_by(
                AchievementStandard.curriculum,
                AchievementStandard.school_level,
                AchievementStandard.grade,
                AchievementStandard.subject_code,
            )
            .order_by(
                AchievementStandard.school_level,
                AchievementStandard.grade,
                AchievementStandard.subject_code,
            )
        )
        std_counts = list(rows)

        rows = await db.execute(
            select(
                AchievementStandard.school_level,
                AchievementStandard.grade,
                AchievementStandard.subject_code,
                func.count(AchievementLevel.id).label("level_count"),
            )
            .join(AchievementLevel, AchievementLevel.standard_id == AchievementStandard.id)
            .group_by(
                AchievementStandard.school_level,
                AchievementStandard.grade,
                AchievementStandard.subject_code,
            )
        )
        level_counts: dict[tuple, int] = {
            (r[0], r[1], r[2]): int(r[3]) for r in rows
        }

    lines = [
        f"# Coverage Report ({date.today().isoformat()})",
        "",
        "| 학교급 | 학년 | 과목 | 성취기준 수 | 성취수준 수 | 상태 |",
        "|---|---|---|---|---|---|",
    ]
    failed = 0
    mvp_subjects = {"국어", "수학", "영어", "과학"}
    for r in std_counts:
        curriculum, school_level, grade, subject, std_n = (r[0], r[1], r[2], r[3], int(r[4]))
        lvl_n = level_counts.get((school_level, grade, subject), 0)
        status = "OK"
        if school_level == "middle" and subject in mvp_subjects and std_n < fail_under:
            status = f"FAIL (<{fail_under})"
            failed += 1
        elif lvl_n == 0:
            status = "WARN(레벨 0)"
        lines.append(
            f"| {school_level} | {grade} | {subject} | {std_n} | {lvl_n} | {status} |"
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    typer.echo(f"Wrote {out}")
    if failed > 0:
        typer.echo(f"FAIL: MVP 4과목 중 {failed}건이 기준 미달 (<{fail_under})", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

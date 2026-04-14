"""관리용 CLI: 학교 초기 세팅·관리자 생성·데모 시드."""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import typer
from sqlalchemy import select

from app.core.db import SessionLocal, set_tenant
from app.models.record import Record, RecordVersion, SectionType
from app.models.review import Review, ReviewStep
from app.models.school import AcademicYear, Class, Grade, School, Subject
from app.models.student import Enrollment, HomeroomAssignment, Student
from app.models.user import RoleAssignment, User
from app.models.guideline import SchoolDecision
from app.services.byte.cp949_counter import byte_count_cp949

app = typer.Typer(help="saengibu-portal 관리 CLI")


@app.command("init-school")
def init_school_cmd(
    neis_code: str = typer.Option(..., help="NEIS 학교 코드"),
    name: str = typer.Option(..., help="학교 이름"),
    type: str = typer.Option("middle", help="middle|high|elementary"),
    year: int = typer.Option(2026, help="현재 학년도"),
    admin_email: str = typer.Option(..., help="첫 관리자 이메일 (승인된 상태)"),
    admin_name: str = typer.Option(..., help="첫 관리자 이름"),
) -> None:
    """학교 초기 세팅."""

    async def _run() -> None:
        async with SessionLocal() as db:
            await set_tenant(db, None)
            existing = await db.scalar(select(School).where(School.neis_code == neis_code))
            if existing:
                typer.echo(f"이미 학교가 존재합니다: {existing.name}")
                raise typer.Exit(1)

            school = School(neis_code=neis_code, name=name, type=type)
            db.add(school)
            await db.flush()

            ay = AcademicYear(
                school_id=school.id,
                year=year,
                start_date=date(year, 3, 1),
                end_date=date(year + 1, 2, 28),
                is_active=True,
            )
            db.add(ay)
            await db.flush()

            # 학년 3개 × 학급 1개씩 (나머지는 UI에서 추가)
            for g in (1, 2, 3):
                grade = Grade(year_id=ay.id, grade_num=g)
                db.add(grade)

            admin = User(
                school_id=school.id,
                email=admin_email,
                name=admin_name,
                status="active",
            )
            db.add(admin)
            await db.flush()
            db.add(RoleAssignment(user_id=admin.id, role="admin"))
            db.add(RoleAssignment(user_id=admin.id, role="principal"))

            await db.commit()
            typer.echo(f"학교 생성 완료: {school.name} ({school.id})")
            typer.echo(f"관리자: {admin.email} ({admin.id})")

    asyncio.run(_run())


@app.command("demo-seed")
def demo_seed_cmd(
    school_name: str = typer.Option("성당중학교"),
    admin_email: str = typer.Option("admin@sd.ms.kr"),
    teacher_email: str = typer.Option("kim@sd.ms.kr"),
) -> None:
    """성당중학교 데모 시드: 학교 + 학급 + 학생 + 교사 + 기록 + 결재대기."""

    async def _run() -> None:
        async with SessionLocal() as db:
            await set_tenant(db, None)

            school = await db.scalar(select(School).where(School.name == school_name))
            if not school:
                school = School(neis_code="DEMO001", name=school_name, type="middle")
                db.add(school)
                await db.flush()
                ay = AcademicYear(
                    school_id=school.id,
                    year=2026,
                    start_date=date(2026, 3, 1),
                    end_date=date(2027, 2, 28),
                    is_active=True,
                )
                db.add(ay)
                await db.flush()
            else:
                ay = await db.scalar(
                    select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.is_active.is_(True))
                )

            assert ay is not None

            # 학년 3개, 학급 5개씩
            grades: list[Grade] = []
            for g in (1, 2, 3):
                grade = await db.scalar(
                    select(Grade).where(Grade.year_id == ay.id, Grade.grade_num == g)
                )
                if not grade:
                    grade = Grade(year_id=ay.id, grade_num=g)
                    db.add(grade)
                    await db.flush()
                grades.append(grade)

            classes: dict[tuple[int, int], Class] = {}
            for grade in grades:
                for c in range(1, 6):
                    klass = await db.scalar(
                        select(Class).where(Class.grade_id == grade.id, Class.class_num == c)
                    )
                    if not klass:
                        klass = Class(grade_id=grade.id, class_num=c)
                        db.add(klass)
                        await db.flush()
                    classes[(grade.grade_num, c)] = klass

            # 관리자 + 담임
            admin = await db.scalar(select(User).where(User.email == admin_email))
            if not admin:
                admin = User(
                    school_id=school.id, email=admin_email, name="관리자",
                    status="active",
                )
                db.add(admin)
                await db.flush()
                db.add(RoleAssignment(user_id=admin.id, role="admin"))
                db.add(RoleAssignment(user_id=admin.id, role="principal"))
                db.add(RoleAssignment(user_id=admin.id, role="academic_head"))

            teacher = await db.scalar(select(User).where(User.email == teacher_email))
            if not teacher:
                teacher = User(
                    school_id=school.id, email=teacher_email, name="김교사",
                    status="active",
                )
                db.add(teacher)
                await db.flush()
                db.add(RoleAssignment(user_id=teacher.id, role="homeroom"))
                db.add(HomeroomAssignment(
                    class_id=classes[(1, 3)].id,
                    user_id=teacher.id,
                    year_id=ay.id,
                    started_at=ay.start_date,
                ))

            # 학생 4명
            demo_students = [
                ("1030101", "이학생", (1, 3), "chang_jayul"),
                ("2010205", "김지훈", (2, 1), "chang_dongari"),
                ("3050307", "박민서", (3, 5), "chang_jinro"),
                ("1020412", "최윤아", (1, 2), "chang_bongsa"),
            ]

            section_rows = {s.code: s for s in await db.scalars(select(SectionType))}

            for student_no, name, (g, c), section_code in demo_students:
                student = await db.scalar(
                    select(Student).where(Student.school_id == school.id, Student.student_no == student_no)
                )
                if not student:
                    student = Student(
                        school_id=school.id,
                        student_no=student_no,
                        name=name,
                        gender="미지정",
                    )
                    db.add(student)
                    await db.flush()
                    db.add(Enrollment(
                        student_id=student.id,
                        class_id=classes[(g, c)].id,
                        year_id=ay.id,
                        started_at=ay.start_date,
                    ))

                section = section_rows[section_code]
                existing_record = await db.scalar(
                    select(Record).where(
                        Record.student_id == student.id,
                        Record.year_id == ay.id,
                        Record.section_type_id == section.id,
                    )
                )
                if existing_record:
                    continue

                record = Record(
                    school_id=school.id,
                    student_id=student.id,
                    year_id=ay.id,
                    section_type_id=section.id,
                    author_id=teacher.id,
                    status="review_1",
                )
                db.add(record)
                await db.flush()

                sample_text = f"{name} 학생은 {section.name} 활동에 적극적으로 참여하였으며, 자신의 역할을 성실히 수행함."
                bc, _ = byte_count_cp949(sample_text)
                version = RecordVersion(
                    record_id=record.id,
                    version_no=1,
                    text=sample_text,
                    byte_count=bc,
                    author_id=teacher.id,
                )
                db.add(version)
                await db.flush()
                record.current_version_id = version.id

                review = Review(
                    record_id=record.id,
                    version_id=version.id,
                    requested_by=teacher.id,
                    status="in_progress",
                    created_at=datetime.now(tz=timezone.utc) - timedelta(hours=uuid.uuid4().int % 24),
                )
                db.add(review)
                await db.flush()
                for step_no, role in ((1, "homeroom"), (2, "academic_head"), (3, "principal")):
                    db.add(ReviewStep(
                        review_id=review.id, step_no=step_no, expected_role=role,
                    ))

            # 학교 결정사항
            if not await db.scalar(select(SchoolDecision).where(SchoolDecision.school_id == school.id)):
                db.add(SchoolDecision(
                    school_id=school.id,
                    title="1학기 주요 변동사항 및 강조점",
                    severity="warn",
                    body_markdown=(
                        "- **독서활동 기재 방식 변경:** 이번 학기부터는 교과 세특에 녹여서 작성하는 것을 원칙으로 합니다. "
                        "개별적인 서적의 나열보다는 해당 책이 교과 학습에 미친 영향을 1~2줄 내외로 요약하세요.\n\n"
                        "- **봉사활동 실적:** 개인 봉사활동 실적은 대입에 반영되지 않으므로, "
                        "학생의 인성을 보여줄 수 있는 ==학교 교육계획에 의한 교내 활동==을 최우선적으로 기재해 주시기 바랍니다.\n\n"
                        "- **제출 기한:** 1학기 최종 마감은 **7월 15일**까지입니다. "
                        "상호 교차 검토를 위해 기한을 반드시 엄수해 주시기 바랍니다."
                    ),
                    effective_date=date(2026, 4, 1),
                    posted_by="교무부",
                ))

            await db.commit()
            typer.echo(f"데모 시드 완료: {school.name}")
            typer.echo(f"  관리자: {admin_email}")
            typer.echo(f"  교사:   {teacher_email}")

    asyncio.run(_run())


if __name__ == "__main__":
    app()

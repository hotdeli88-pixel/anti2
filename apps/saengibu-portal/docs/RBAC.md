# RBAC — 학교 조직도 기반 권한 모델

> Casbin (RBAC + ABAC) · 한국 중·고등학교 직제 · 개인정보보호법 §15·§18 "업무 관련성" 준수

## 0. 설계 원칙

1. **역할 × 스코프 × 속성**: 역할만으로는 부족. "담임이지만 **자기 학급만**", "교과교사이지만 **자기 수업 반만**".
2. **ABAC 필수**: 학년·학급·담당과목은 동적 관계. 정적 role assignment만으로는 표현 불가.
3. **업무 관련성 원칙**: 같은 학교 구성원이라도 업무상 필요 없는 학생 정보 열람 불가.
4. **감사 로그 우선**: 권한 체크와 감사 로그는 동일 트랜잭션. 열람 자체도 로깅.
5. **기본값 deny**: 모든 리소스 접근은 정책이 명시적으로 허용해야 함.

---

## 1. 학교 직제 (Org Tree)

```
학교장 (principal)
  └── 교감 (vice_principal)
       ├── 교무부장 (academic_head) — 학교 전체 문서 감수
       │    ├── 학년부장 × 3 (grade_head, 1·2·3학년) — 해당 학년 총괄
       │    │    └── 담임교사 (homeroom) — 자기 학급 학생 1차 책임
       │    └── 교과부장 × N (subject_head) — 교과별 세특 감수
       │         └── 교과교사 (subject_teacher) — 자기 수업 반 세특 작성
       ├── 연구부장 / 생활지원부장 / 진로부장 (기타 보직)
       └── 동아리 담당 (club_advisor)  — 동아리 특기사항 입력
  └── 관리자 (admin, 시스템)
```

- **학년부장 vs 교무부장 축 차이**:
  - 학년부장: **수평(학년 단위)** 전체 기록 열람·검토
  - 교무부장: **수직(전교 기재요령 준수)** 감수·리스크 판단
- **담임 교체**: 연중 교체 시 신임 담임에게 편집권 이관, 기존 작성 이력은 버전 보존.

---

## 2. 역할 (Role) 카탈로그

| Role | 코드 | 설명 |
|---|---|---|
| 학교장 | `principal` | 최종 결재 (3검), 정정 승인 |
| 교감 | `vice_principal` | 3검, 정정 검토 |
| 교무부장 | `academic_head` | 2검, 기재요령 감수 |
| 학년부장 | `grade_head` | 2검, 학년 형평성 |
| 교과부장 | `subject_head` | 1검(세특) |
| 담임교사 | `homeroom` | 자기 학급 기록 작성·1검(동료 행종의 제외) |
| 교과교사 | `subject_teacher` | 자기 수업 반 세특 작성 |
| 동아리 담당 | `club_advisor` | 동아리 특기사항 작성 |
| 관리자 | `admin` | 시스템 세팅, 금지어 사전 |

다중 역할 허용: 한 교사가 "3학년 담임 + 수학 교과교사 + 수학부장" 동시 가능.

---

## 3. 스코프(Scope) 속성

권한 평가 시 동적 속성:

| 속성 | 의미 | 예 |
|---|---|---|
| `user.school_id` | 소속 학교 | RLS 1차 |
| `user.homeroom_class_ids[]` | 현재 담임 학급 | 행종의 쓰기 |
| `user.teaches[] = {class_id, subject_id}` | 수업 담당 | 세특 쓰기 |
| `user.club_ids[]` | 동아리 지도 | 동아리 특기사항 쓰기 |
| `user.grade_id (if grade_head)` | 부장 학년 | 학년 검토 |
| `user.subject_ids[] (if subject_head)` | 부장 교과 | 교과 검토 |
| `record.school_id` | 기록 소속 학교 | 1차 필터 |
| `record.student_id → class_id` | 기록 대상 학급 | 담임 매칭 |
| `record.section_type_id` | 영역 | 입력 주체 검증 |
| `record.subject_id` | 교과 (세특) | 교과교사 매칭 |
| `record.status` | 상태 | 쓰기 가능 여부 |

---

## 4. 권한 매트릭스

리소스: `record` (학생 × 영역 × 학년도 단위). Action: `read` / `write` / `submit` / `review` / `approve` / `copy`.

### 4.1 쓰기 권한 (write)

| Section | 쓸 수 있는 사람 | 조건 |
|---|---|---|
| `haengjongjeui` (행종) | 담임 | 학생의 현재 학급 담임 |
| `chulgyeol_teuggi` | 담임 | 학생의 현재 학급 담임 |
| `chang_jayul`, `chang_jinro`, `chang_bongsa` | 담임 | 학생의 현재 학급 담임 |
| `chang_dongari` | 동아리 담당 | 학생이 그 동아리 소속 |
| `setuk_subject` | 교과교사 | `{record.class_id, record.subject_id}` ∈ `user.teaches` |
| `setuk_individual` | 담임 | 학생의 현재 학급 담임 |
| `dokseo` | 교과교사 OR 담임 | 해당 교과 수업 또는 담임 |
| `jayuhakgi` | 해당 활동 담당 | 활동별 담당 배정 |
| `susang` | 담임 | 자기 학급 학생 |
| `injeok_teuggi` | 담임 | 자기 학급 학생 |

**추가 조건 (모두 AND)**:
- `record.status in ('draft', 'review_1' AND user is author)` — 승인 후 읽기 전용
- 학년도: `record.year_id == current_active_year`
- 학교장이 "편집 잠금"을 걸지 않은 상태

### 4.2 읽기 권한 (read)

| Viewer | 볼 수 있는 기록 |
|---|---|
| 본인 작성자 | 본인이 작성한 모든 기록 |
| 담임 | 자기 학급 학생의 모든 영역 |
| 교과교사 | 자기 수업 반 학생의 해당 교과 세특 (타 영역 불가) |
| 교과부장 | 해당 교과 전 학급 세특 (2검 범위) |
| 학년부장 | 해당 학년 전 학급·전 영역 |
| 교무부장 | 학교 전체 모든 기록 (감수 목적) |
| 교감/교장 | 학교 전체 모든 기록 |
| 관리자 | 인적·통계·감사 목적 (본문 읽기 권한 분리 가능) |

### 4.3 검토(review) 권한

| Step | 결재 가능 Role | Guard |
|---|---|---|
| 1검 | 담임(행종·창체) 또는 교과부장(세특) | record의 섹션과 매칭 |
| 2검 | 학년부장 OR 교무부장 | 해당 학년 또는 학교 전체 권한 |
| 3검 | 교감 OR 교장 | — |

### 4.4 NEIS 복사 (copy)

- 본인 작성자 또는 담임만.
- `record.status == 'approved'` 이후만.
- 복사 횟수 무제한이나 `neis_copy_logs`에 모든 복사 기록.

---

## 5. Casbin 정책 정의

### 5.1 모델 파일 `rbac_model.conf`

```ini
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act, eft

[role_definition]
g = _, _, _

[policy_effect]
e = some(where (p.eft == allow)) && !some(where (p.eft == deny))

[matchers]
m = r.sub.school_id == r.obj.school_id \
    && g(r.sub.role, p.sub, r.sub.school_id) \
    && keyMatch(r.obj.kind, p.obj) \
    && r.act == p.act \
    && eval(p.sub_rule)
```

### 5.2 정책 예 (subset)

```csv
p, homeroom, record:haengjongjeui, write, allow, "r.obj.class_id in r.sub.homeroom_class_ids && r.obj.status in ['draft']"
p, subject_teacher, record:setuk_subject, write, allow, "{r.obj.class_id, r.obj.subject_id} in r.sub.teaches && r.obj.status == 'draft'"
p, grade_head, record:*, read, allow, "r.obj.grade_id == r.sub.grade_id"
p, academic_head, record:*, read, allow, "true"
p, academic_head, review, approve, allow, "r.obj.step_no == 2"
p, principal, review, approve, allow, "r.obj.step_no == 3"
p, *, record:*, read, deny, "r.obj.archived_until_graduation == true && !r.sub.roles.includes('principal','admin')"
```

### 5.3 FastAPI 의존성

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException

def require(action: str, resource_kind: str):
    def _dep(user = Depends(current_user), obj = Depends(load_resource)):
        if not enforcer.enforce(user_attrs(user), user.school_id, {'kind': resource_kind, **obj_attrs(obj)}, action):
            raise HTTPException(403, {'type':'rbac.forbidden', 'title':'권한 없음'})
        audit.log(user, action, obj)
        return obj
    return _dep

# 사용 예
@router.post("/records/{id}/draft")
async def save_draft(record = Depends(require('write', 'record'))):
    ...
```

---

## 6. 전출·전입·담임 교체

| 이벤트 | 권한 처리 |
|---|---|
| 전입 | 새 학교의 해당 학급 담임이 자동 write 권한, 이전 학교 기록은 읽기 전용(이력) |
| 전출 | 작성 권한 상실, 원적교 보관, 전입교에서 글자수 초과 시 조정 |
| 담임 교체 | 기존 담임 write 권한 해제 (단, 자기가 만든 초안 버전은 여전히 열람 가능), 신임 담임이 이어서 작성 |
| 담임이 퇴직 | 학교장이 관리자 권한으로 긴급 이관 수행, 감사로그 필수 |

---

## 7. 관리자 승인 체계

### 7.1 회원가입

```
교사 가입 요청 (이메일·이름·교직원번호·학교 NEIS 코드)
  │
  ▼
user.status = 'pending'
  │
  ▼
관리자 승인 (`/users/{id}/approvals`)
  ├─ 본인 확인 (교직원번호 대조)
  ├─ 역할 부여 (담임·교과교사 등)
  └─ user.status = 'active'
```

### 7.2 역할 배정

- 학교장: 관리자가 시스템 최초 설정 시 수동 부여 (사진·서명 등록)
- 교감·부장: 학교장이 임명 (연초 인사 변동)
- 담임: 학년부장이 학급별 할당
- 교과교사: 교과부장이 시간표 기반 배정
- 동아리 담당: 연초 동아리 편성 시 지정

모든 역할 변경은 `role_assignments.started_at` / `ended_at`로 이력 유지.

---

## 8. 감사 로그 (audit_logs)

| Action | 기록 항목 |
|---|---|
| `record.view` | user, record, span=(섹션·학생·영역), client_info |
| `record.write` | user, record, version_id, byte_count |
| `record.submit` | user, record, target_step |
| `review.decide` | reviewer, step, decision, comment_hash |
| `record.approve` | user(교장), record, final_version_id |
| `record.neis_copy` | user, version_id, client_info |
| `record.correction_request` | requester, reason, diff |
| `record.correction_approve` | principal, request_id |
| `banned_dict.update` | admin, before/after hash |
| `role.assign` | admin, target_user, role, scope |

- 보존 기간: **준영구** (졸업 후 5년 이상, 훈령 제18조 기반)
- 저장: append-only 파티션 테이블, S3 월 1회 동기화
- 감사 조회는 admin + 교감/교장만 (정당한 사유 로그 필수)

---

## 9. 개인정보보호 체크리스트

| 항목 | 대응 |
|---|---|
| PIPA §15 (수집) | 학생 등록 시 학부모 동의서 별도 수집, 시스템은 수집 주체 아님 (학교가 법적 주체) |
| PIPA §18 (목적 외 이용) | 업무 관련성 없는 열람은 UI·API 양측에서 차단 |
| PIPA §24 (고유식별정보) | 주민등록번호는 암호화 저장, 성명은 애플리케이션 레벨 마스킹 옵션 |
| 학교생활기록부 §20조의2 | 상업적 이용·매매 금지 → 외부 분석 업체 연계 금지, LLM API DPA 체결 |
| 훈령 AI 활용 유의사항 | 학생·학부모 사전 안내 템플릿 포함 |

---

## 10. 구현 참고

- **Casbin Python**: `casbin` + `casbin-sqlalchemy-adapter`로 정책을 DB에 저장, hot-reload
- **대안 검토**: OpenFGA (Zanzibar 기반, 관계형 권한)도 고려. 본 프로젝트는 Python 생태계 호환성·한글 문서화 편의성으로 Casbin 채택. 확장기에 재평가 가능 (ADR-002)
- **테스트**: 모든 엔드포인트에 대해 역할별 행렬 테스트 (`tests/rbac/test_matrix.py`), 30+ 시나리오

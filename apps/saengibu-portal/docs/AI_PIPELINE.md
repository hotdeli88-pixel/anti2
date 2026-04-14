# AI_PIPELINE — 생기부 피드백 엔진 6단계

> 훈령 제555호 · 2026 기재요령 준수. "AI는 대신 쓰지 않는다"가 설계 원칙.

## 0. 설계 원칙 (최우선)

| 원칙 | 함의 |
|---|---|
| **교사 초안 → AI 피드백** | "AI가 쓰고 → 교사 확인" 흐름은 UI·API 경로 자체에서 차단 |
| **결정적 먼저, LLM은 마지막** | 비용·지연·할루시네이션 최소화. Stage 1~4·6은 비-LLM |
| **학생 실명 외부 이탈 금지** | LLM 호출 전 PII 마스킹 → 응답 후 복원 |
| **근거 인용 필수** | 각 지적에 훈령 조항 또는 기재요령 페이지 |
| **JSON 스키마 고정** | LLM 응답 구조화, UI 렌더 안정성 |
| **가드레일 명문화** | "완성된 대체 문장을 제공하지 말라" 시스템 프롬프트 |

---

## 1. 파이프라인 개요

```
[교사 초안]
   │
   ▼
┌─────────────────────────────────────────┐
│ Stage 1. Byte Counter (CP949)            │ ← 5-30ms, 확정적
├─────────────────────────────────────────┤
│ Stage 2. 금지어·금지패턴 필터 (사전)     │ ← 10-50ms, 확정적
├─────────────────────────────────────────┤
│ Stage 3. 문체 검사 (규칙)                │ ← 10-30ms, 확정적
├─────────────────────────────────────────┤
│ Stage 4. 반복·유사도 (임베딩+MinHash)    │ ← 50-300ms, 확률적(임계치)
├─────────────────────────────────────────┤
│ Stage 5. LLM 심층 피드백  [비동기]       │ ← 2-8s, 외부 API
├─────────────────────────────────────────┤
│ Stage 6. 최종 체크리스트                  │ ← UI 렌더, 교사 확인
└─────────────────────────────────────────┘
   │
   ▼
[교사 수정·확정 → NEIS 복사]
```

- **동기(실시간 < 500ms)**: Stage 1·2·3·4·6 (Stage 4는 pgvector top-k only)
- **비동기(~5s)**: Stage 5 (Celery task, SSE 푸시)
- **배치(야간)**: Stage 4 전수 교차 검증 (FAISS)

---

## 2. Stage 1 — Byte Counter (CP949)

### 규칙

- NEIS 실제 인코딩은 CP949 (KS X 1001 + 확장). EUC-KR은 확장 한글 누락 → 사용 금지.
- `len(text.encode('cp949'))` 직접 계산.
- CRLF 정책: `\r\n` 2바이트로 카운트 (보수적).
- 영역별 상한: `section_types.byte_limit` 테이블 조회.

### 구현 (핵심)

```python
# backend/app/services/byte/cp949_counter.py
import unicodedata

ZW = {'\u200B', '\u200C', '\u200D', '\uFEFF', '\u2028', '\u2029'}
SMART_QUOTES = str.maketrans({'\u2018': "'", '\u2019': "'", '\u201C': '"', '\u201D': '"'})
DASHES = str.maketrans({'\u2013': '-', '\u2014': '-'})

def normalize_for_neis(text: str) -> tuple[str, list[dict]]:
    warnings: list[dict] = []
    text = unicodedata.normalize('NFC', text)
    text = ''.join(c for c in text if c not in ZW)
    text = text.translate(SMART_QUOTES).translate(DASHES)
    text = text.replace('\u3000', ' ').replace('\xa0', ' ')  # 전각·NBSP → 일반공백
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    return text, warnings

def byte_count_cp949(text: str) -> tuple[int, list[str]]:
    normalized, _ = normalize_for_neis(text)
    incompatible: list[str] = []
    safe_chars: list[str] = []
    for ch in normalized:
        try:
            ch.encode('cp949')
            safe_chars.append(ch)
        except UnicodeEncodeError:
            incompatible.append(ch)
    return len(''.join(safe_chars).encode('cp949')), incompatible
```

### 출력 (Stage 1 결과)

```json
{
  "byte_count": 287,
  "byte_limit": 300,
  "over": false,
  "incompatible_chars": [],
  "normalized_diff": []
}
```

### 오탐/엣지케이스

| 케이스 | 처리 |
|---|---|
| 이모지 🎉 | CP949 미지원 → `incompatible_chars`에 추가 → severity=block |
| NFD 분리 한글 | NFC 정규화로 결합 |
| 확장 한자 (CJK Ext B+) | CP949 미지원 → 경고 |
| 전각공백 U+3000 | 일반공백 치환 (기재요령 비권장) |

---

## 3. Stage 2 — 금지어·금지패턴 필터

### 사전 구조

YAML로 카테고리별 분리, DB `banned_dict_entries`에 로드.

```yaml
# dictionaries/foreign_exams.yaml
category: exam
severity: block
reference: "훈령 제555호 제9조 가목"
entries:
  - pattern: '\b(TOEIC|TOEFL|TEPS|IELTS|HSK|JLPT|OPIc|G[- ]?TELP)\b'
    flag: IGNORECASE
  - pattern: '(토익|토플|텝스|아이엘츠|오픽|플렉스)'
```

12개 카테고리 (상세는 §11):
1. 공인어학시험 · 2. 교외상 · 3. 대학명 · 4. 부모 지위 · 5. 자격증 · 6. 논문/특허 · 7. 해외활동 · 8. 장학금 · 9. "대회" 영역외 · 10. 상호/강사 · 11. 모의UN/유네스코 · 12. AI 생성 흔적

### 실행

- **Aho-Corasick** (pyahocorasick) 으로 다중 문자열 동시 매칭.
- 정규식은 한국어에서 `\b`이 작동하지 않으므로 lookaround 사용: `(?<![가-힣A-Za-z])토익(?![가-힣A-Za-z])`
- 매칭 span 반환, UI에서 하이라이트.

### 화이트리스트 (예외)

`banned_whitelist` 테이블:

- 국사편찬위원회
- 한국과학창의재단
- 한국교육방송공사 (EBS)
- 한국교육학술정보원 (KERIS)
- 국립국제교육원
- 중앙교육연수원
- 교원소청심사위원회
- 대한민국학술원
- 국립특수교육원

### 영역 교차 검증

- **"대회" 용어**: `section.code == 'susang'` 이외 영역에서 매칭되면 block.
- **수상 관련**: 세특·창체·행종의 영역에서 "수상/상" 명사 매칭되면 block.

### 출력

```json
{
  "matches": [
    {
      "category": "univ",
      "rule_code": "univ.seoul_cluster",
      "pattern_matched": "서울대",
      "span": [42, 45],
      "severity": "block",
      "reference": "훈령 제555호 제9조 타목",
      "suggestion": "구체적 대학명은 기재 불가합니다."
    }
  ]
}
```

---

## 4. Stage 3 — 문체 검사 (규칙)

### 검사 항목

| 규칙 | 방식 | 예시 |
|---|---|---|
| **명사형 어미 종결** | 문장 단위 분리 → 마지막 토큰 품사 검사 (Kiwi) | "참여함." OK / "참여했다." 경고 |
| **한자 포함 금지** | `[\u4E00-\u9FFF]` 탐지 | "독서(讀書)" 경고 |
| **외국어 불가 (허용 명사 예외)** | 라틴문자 토큰 중 허용 화이트리스트(`CEO, AI, PD, SNS, PPT, cm, km` 등) 제외 탐지 | "presentation" 경고 |
| **특수문자·번호기호 지양** | `[①②③⇒⇨★☆■□▶▷◀◁◆◇]` 탐지 | 경고 |
| **과장 상투어** | 사전 매칭 | "매우 뛰어난", "탁월한", "큰 기여", "눈부신" |
| **긴 문장** | 70 어절 이상 경고 | 가독성 |
| **접속어 과다** | "또한/그리고/이를 통해" 빈도 ≥3 경고 | 나열식 지양 |

### 구현

```python
# backend/app/services/ai/style_stage.py
from kiwipiepy import Kiwi

kiwi = Kiwi()
# 명사형 전성어미(ETN)만. ETM은 관형사형 전성어미라 종결에 쓰이지 않음.
# 형용사 파생 "XSA+ETN", 동사 파생 "XSV+ETN"도 허용.
ALLOWED_FOREIGN = {'CEO', 'AI', 'PD', 'SNS', 'PPT', 'cm', 'km', 'kg', 'M', 'B'}

def check_nouning_end(sentence: str) -> bool:
    tokens = kiwi.analyze(sentence.rstrip('.').rstrip())[0][0]
    if not tokens:
        return False
    last = tokens[-1]
    if last.tag == 'ETN':
        return True
    # 어간 직접 종결 패턴 (함/임/음) 백업
    return last.form.endswith(('함', '임', '음')) and last.tag in ('XSV', 'XSA', 'VV', 'VA', 'NNG')
```

### 출력

```json
{
  "issues": [
    {
      "rule_code": "style.not_nouning_end",
      "sentence": "학업에 매진하였다.",
      "span": [0, 11],
      "severity": "warn",
      "suggestion": "명사형 어미(함/임/음) 종결 권장"
    }
  ]
}
```

---

## 5. Stage 4 — 반복·유사도

### 4.1 실시간 (저장 시, <500ms, MVP)

**MVP는 pgvector HNSW 단독**. MinHash LSH는 야간 배치에만 사용 (학급 30명 규모에서 HNSW 단독으로 충분, 복잡성 감소).

- `jhgan/ko-sroberta-multitask` 768-dim · cosine > 0.85 플래그
- **임베딩 쓰기는 Celery 비동기** (저장 즉시 본문만 커밋, 임베딩 생성은 enqueue)
  - 이유: 동시 저장 시 HNSW 쓰기 락 + 읽기 경합으로 p95 깨짐
  - 실시간 조회는 이전 버전 임베딩으로 근사 (신규 저장 직후엔 유사도 "분석 중")
- 같은 학교·현재 학년도·같은 영역 내 top-10

```python
# backend/app/services/duplicate/embed.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('jhgan/ko-sroberta-multitask')

def embed(texts: list[str]):
    return model.encode(texts, batch_size=32, normalize_embeddings=True)
```

### 4.2 배치 (야간, Celery)

- 학교 전체 교차 비교, FAISS `IVF4096,PQ32`
- 조합:
  - **학급 내 차별화**: 담임 1명의 30명 기록 pairwise cosine 평균 > 0.85 → 경보
  - **연도 간 재사용**: 올해 vs 작년 동일 학생·동일 영역 cosine > 0.90
  - **교사 복붙**: 같은 교사의 타 학생 기록과 cosine > 0.92

### 4.3 매칭 유형 분류

```python
class MatchType(StrEnum):
    WITHIN_CLASS = 'within_class'                    # 같은 학급 학생 간
    CROSS_YEAR = 'cross_year'                        # 작년-올해 동일 학생
    SAME_TEACHER_OTHER_STUDENT = 'same_teacher_other_student'
    CROSS_TEACHER = 'cross_teacher'                  # 다른 교사 간 (이례적)
```

### 출력

```json
{
  "similar": [
    {
      "target_version_id": "...",
      "target_label": "학급 내 다른 학생",
      "cosine": 0.93,
      "minhash_jaccard": 0.78,
      "match_type": "same_teacher_other_student",
      "span_hints": [[0, 45]]
    }
  ],
  "individuality_score": 0.62
}
```

---

## 6. Stage 5 — LLM 심층 피드백

### 목적

규칙으로 못 잡는 **맥락·함의 판단**:
- 과장/허위 의심
- 개별성 결여 ("학생 고유 수행이 드러나는가")
- 영역 부적합 (세특에 창체 내용 등)
- 단순 나열 vs 성취기준 근거 분석

### PII 마스킹 (MVP 필수)

**대상 학생 1명만 치환하면 불충분.** 본문에 학급 내 타 학생 실명("홍길동과 함께 김철수가 발표")이 섞일 수 있으므로 **학교·학년도 전체 학생 실명을 사전으로 삽입**.

```python
# backend/app/services/mask/pii.py
from dataclasses import dataclass

@dataclass
class MaskContext:
    target_student_id: str
    school_id: str
    year_id: str

def build_student_dict(ctx: MaskContext, db) -> dict[str, str]:
    """학교·학년도 전체 학생 실명 → 식별자 치환 사전."""
    students = db.query(Student).filter_by(school_id=ctx.school_id).all()
    mapping: dict[str, str] = {}
    for s in students:
        tag = '<S_TARGET>' if s.id == ctx.target_student_id else f'<S_{s.student_no}>'
        mapping[s.name] = tag
    # 동명이인은 학번 suffix로 구분 (사전 구축 시 collision 검사)
    return mapping

def mask(text: str, ctx: MaskContext, db) -> tuple[str, dict]:
    mapping = build_student_dict(ctx, db)
    # 긴 이름부터 치환 (부분 매칭 방지)
    masked = text
    for name in sorted(mapping, key=len, reverse=True):
        masked = masked.replace(name, mapping[name])
    return masked, mapping

def unmask(masked_response: str, mapping: dict) -> str:
    for name, tag in mapping.items():
        masked_response = masked_response.replace(tag, name)
    return masked_response
```

- NER(`kiwipiepy` 고유명사 태그 `NNP`) 2차 패스로 사전에 없는 이름 탐지 → warn
- 주민등록번호·학번·전화번호 정규식 치환 추가
- 학부모·담임 교사 이름도 사전에 포함 (학교 임직원 테이블 조회)

### 시스템 프롬프트 (발췌)

```text
당신은 교육부훈령 제555호와 2026학년도 학교생활기록부 기재요령에 정통한
검토 도우미입니다. 다음 원칙을 반드시 지키세요.

1. 절대 완성된 대체 문장을 제공하지 마십시오. 교사가 직접 수정하도록
   "개선 포인트"와 "고려할 질문"만 제시합니다.
2. 모든 지적은 훈령 조항 또는 기재요령 페이지를 `reference`에 명시하세요.
3. 응답은 반드시 다음 JSON 스키마를 따르세요:

{
  "violations": [
    { "rule": "exaggeration | individuality | area_mismatch | fabrication_suspect | listing_only",
      "severity": "block | warn | info",
      "span": [start, end],
      "message": "…",
      "consider_questions": ["…", "…"],
      "reference": "훈령 제555호 제16조"
    }
  ],
  "overall_assessment": "…",
  "individuality_comment": "…"
}

4. 학생 실명은 응답에 포함하지 마십시오. 마스킹된 토큰(<S001> 등)을
   그대로 사용하세요.
5. 기재금지 12개 항목에 해당하는 내용이 있으면 severity="block"으로.
```

### 유저 프롬프트 템플릿

```text
## 영역
{section.name} (상한 {byte_limit}B, 입력 주체 {input_role})

## 학생 정보
학년: {grade}, 학급: {class_no}, 마스킹 ID: <S001>

## 기재 본문
{masked_text}

## Stage 1-4 탐지 결과 (참고)
- Byte: {byte}/{limit}
- 금지어 매칭: {banned_summary}
- 유사 기록: cosine {best_cosine} with {target_label}

## 요청
위 본문을 훈령 관점에서 검토하고 JSON으로 응답하세요.
```

### 모델·비용·폴백

| 상황 | 모델 |
|---|---|
| 기본 | Claude Sonnet 4.6 (비용·품질 균형) |
| 고가치 영역 (행종의) | Claude Opus 4.6 |
| 폴백 | OpenAI GPT-4o-mini |
| 로컬 옵션 (학교 폐쇄망) | Qwen2.5-14B-Instruct (ONNX) |

- 토큰: 입력 ~800 + 출력 ~400 = Sonnet 호출당 약 **$0.003**
- 교사당 연 기재 400건 → 연 $1.2/교사 수준

### 가드레일 (응답 후처리)

- 응답에 "~하였습니다", "~했다" 등 완성형 문장이 포함되면 제거
- `violations[].consider_questions` 누락 시 재요청
- JSON 파싱 실패 시 2회까지 재시도 후 fallback="설명 실패, 규칙 결과만 활용하세요"

### 실패·타임아웃·상태 관리 (중요)

`feedback_reports.stage_llm_status` enum 필수:

```sql
ALTER TABLE feedback_reports
  ADD COLUMN stage_llm_status varchar(20) NOT NULL DEFAULT 'pending'
  CHECK (stage_llm_status IN ('pending','running','success','failed','skipped','timeout'));
```

- Celery `max_retries=3, retry_backoff=60s, soft_time_limit=20s, time_limit=30s`
- 최종 실패 시 `stage_llm_status='failed'` + 작성자 UI에 "AI 심층 피드백 미가용, 규칙 결과로 진행하세요" 배너
- 워크플로우(`submit`) 전제조건에는 **Stage 5 결과를 요구하지 않음** → LLM 장애가 제출을 막지 않음
- 관리자 `POST /feedback/{id}/regenerate?stages=llm` 수동 재실행 가능

---

## 7. Stage 6 — 최종 체크리스트

UI에서 교사가 체크박스 클릭:

```text
[ ] 학생의 실제 수행과 무관한 허위·과장 내용이 없음을 확인했습니다
    (훈령 제555호 AI 활용 유의사항)
[ ] 기재요령 각종 유의사항을 재확인했습니다
[ ] AI 피드백을 참고했으나, 문장은 내가 직접 작성했습니다
```

- 세 항목 모두 체크 전에는 `review_1` 제출 불가.
- DB `feedback_reports.stage_checklist` 에 기록.

---

## 8. 상태 전이 트리거

| 전이 | Stage 결과 조건 |
|---|---|
| draft → review_1 제출 | Stage 1 `over=false` AND Stage 2 block=0 AND Stage 6 모두 체크 |
| review_N → 반려 | 검토자 결정 (AI 결과는 참고 자료) |
| review_3 → approved | 교장 최종 승인 |
| approved → neis_copied | NEIS 복사 이벤트 수신 |

---

## 9. 성능·관측성

| 단계 | p50 | p95 | 비고 |
|---|---|---|---|
| Stage 1 | 5ms | 15ms | |
| Stage 2 | 20ms | 80ms | Aho-Corasick 500 패턴 |
| Stage 3 | 30ms | 100ms | Kiwi 파싱 |
| Stage 4 (실시간) | 80ms | 300ms | pgvector HNSW |
| Stage 5 | 3s | 8s | 외부 API |

- Prometheus 메트릭: `feedback_stage_latency_seconds{stage="…"}`, `feedback_violations_total{rule="…"}`, `llm_tokens_total{model="…"}`, `llm_cost_usd_total`

---

## 10. 버전 관리·거버넌스

- **사전/규칙 버전**: `rules_version = "2026-03"` (훈령 개정 시 갱신)
- **프롬프트 버전**: `prompt_version = "v3.1"` (PR·ADR에 근거 명시)
- **임베딩 모델 버전**: 모델 변경 시 전체 재임베딩 (백필 워커)
- **학업성적관리위원회 심의 근거 문서**: `/docs/governance/akgwan_submission.md` (별도 PR에서 작성)
- **학생·학부모 사전 안내문 템플릿**: `/docs/governance/privacy_notice_ko.md`

---

## 11. 금지어 사전 카테고리 요약 (12종)

| # | 카테고리 | 1차 regex 예 | LLM 필요 케이스 | 화이트리스트 |
|---|---|---|---|---|
| 1 | 공인어학시험 | `\b(TOEIC\|TOEFL\|TEPS\|IELTS\|HSK\|JLPT\|OPIc)\b` | "영어 공인시험 고득점" 암시 | 토의/토론 |
| 2 | 교외상 | `(표창장\|감사장\|공로상\|전국.*대회)` | 주최자 문맥 | 교내 수상은 별도 영역 |
| 3 | 대학명 | `(서울대\|연세대\|\S+대학교)` | "대학 연계 진로" | 교육관련기관 6개 |
| 4 | 부모 지위 | `(부모\|아버지)가\s*(의사\|변호사\|CEO)` | "다양한 문화 경험" 암시 | 가족 일반 언급 |
| 5 | 자격증 | `(한국사능력검정\|MOS\|정보처리기사)` | "○○ 공부" 암시 | 교과 수행 등급 |
| 6 | 논문/특허 | `(논문\|학회발표\|특허\|출원\|ISBN)` | "보고서" 맥락 | 교내 탐구보고서 |
| 7 | 해외활동 | `(해외연수\|어학연수\|UN\|UNESCO)` | "국제적 시야" | 국제 이슈 관심 |
| 8 | 장학금 | `(장학생\|장학금)` | 완곡 표현 | 학교장 추천 제도 |
| 9 | "대회" | `(대회\|경시\|올림피아드)` | 수상영역 외 매칭 | — |
| 10 | 상호/강사 | `([가-힣]+학원\|[가-힣]+강사)` | 상호 보통명사 혼동 | 교내 교사 |
| 11 | 모의UN | `(Model\s*UN\|MUN\|모의유엔)` | 학교별 약칭 | 교내 정식 창체 |
| 12 | AI 흔적 | `(as an AI\|ChatGPT\|language model)` | 기계체 문체 | 정상 공손체 |

---

## 12. 테스트 코퍼스

- `tests/fixtures/records_clean/` — 정상 100건
- `tests/fixtures/records_violations/` — 12 카테고리별 30건씩
- `tests/fixtures/records_copypaste/` — 학급 내 복붙 의심 20건
- KPI: **Recall ≥ 0.95**, **Precision ≥ 0.80**, 분기별 재측정

---

## 13. 추후 확장

- **RAG**: 훈령 전문 + 기재요령 전문을 pgvector로 검색, LLM 프롬프트에 근거 문단 주입
- **교사별 스타일 프로파일**: 개인 스타일(문장 길이 평균 등) 학습 후 Z-score로 "평소와 다름" 경보
- **학교별 커스텀 규칙**: 교내 동아리명 등 학교별 화이트리스트 확장

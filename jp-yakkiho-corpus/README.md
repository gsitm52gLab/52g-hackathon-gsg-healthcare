# 일본 약기법 광고 검수 기반자료·프롬프트 패키지

> 이 저장소는 서비스나 완성된 검수 애플리케이션이 아니다. 일본 화장품 광고를 검토할 때 사용할 공식 기반자료, 사전 생성 한국어 번역, 사람이 읽는 규칙 카드, 단일 AI 프롬프트를 전달하는 패키지다.

AI 결과는 위반 판정이나 승인 결과가 아니라 담당자가 먼저 볼 문제 후보, 이유, 공식 근거와 수정 초안을 제시하는 참고자료다.

## 핵심 전달물

1. **공식 기반자료와 사전 번역**
   - `manifest.jsonl`
   - `sources/<SOURCE-ID>/original/`
   - `sources/<SOURCE-ID>/aligned/segments.jsonl`
   - `sources/<SOURCE-ID>/derived/translation.ko.md`
2. **사람이 읽는 실무 규칙 카드**
   - `rules/jcia/rule-cards.ko.md`
   - 기계 판독용 원본: `rules/jcia/rules.jsonl`
3. **단일 운영 프롬프트와 입출력 예시**
   - `prompts/jp-cosmetics-ad-prescreen.md`
   - `prompts/examples/input.json`
   - `prompts/examples/output.json`

처음 전달받은 사람은 위 세 항목만 읽으면 된다. 검색 인덱스, runtime loader, 출력 상태 스키마와 QA 자동화는 향후 서비스 실험을 위한 선택 사항이며 `optional_prototype/README.md`에 분리해 설명했다.

## 권위와 범위

우선순위는 `e-Gov 법령 > 후생노동성 통지 > 후생노동성 공식 해설`이다. JCIA 자료는 업계 자율기준이며 이용허락 전에는 `restricted-sources.yaml`의 링크와 메타데이터만 사용한다.

현재 포함 범위:

- 약기법 전체 XML 원본과 제2조, 제59조, 제61조, 제66조~제68조의 일본어 추출·한국어 기계번역
- 의약품 등 적정광고기준과 공식 해설
- 광고 해당성 통지
- 일반 화장품 56개 효능 범위와 잔주름 취급
- 2025년 특정성분 특기표시 통지
- PMDA 의약부외품·화장품 관련 통지 공식 색인(참고용, 기본 검색 인덱스 제외)
- 시행령·시행규칙 전체 XML과 개정 메타데이터(전문 추출·번역은 제외)

의약부외품은 제품별 승인 효능·효과가 추가로 필요하다. 제품 분류나 승인 상태가 불명확하면 시스템은 위반을 확정하지 않고 `확인 필요`로 반환해야 한다.

## 디렉터리 계약

각 source에는 다음 파일이 있다.

```text
sources/<SOURCE-ID>/
  original/                   공식 서버에서 받은 불변 바이트와 응답 헤더
  derived/original.ja.txt     UTF-8, LF, Unicode NFC 일본어 파생본
  derived/translation.ko.md   machine_unreviewed 비공식 한국어 번역
  aligned/segments.jsonl      동일 segment ID의 일본어·한국어 정렬
  qa/extraction-report.json   추출 도구·범위·페이지·OCR 후보·실패
```

원본은 SHA-256 앞 12자를 파일명에 넣어 덮어쓰지 않는다. `manifest.jsonl`이 현재 선택된 버전과 전체 SHA-256, 공식 URL, 공포·발행·시행·취득일, 추출 및 번역 메타데이터를 기록한다.

## 재실행

macOS 기준이며 시스템 전역 패키지를 설치하지 않는다.

```bash
cd /Users/jiisuniui/Documents/GS-Hackathon/jp-yakkiho-corpus
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
chmod +x scripts/fetch_sources scripts/extract scripts/validate
scripts/fetch_sources
scripts/extract
scripts/validate
scripts/build_search_index
scripts/build_report
```

위 명령 중 `fetch_sources`, `extract`, `validate`는 기반자료 갱신·검증용이다. `build_search_index`는 선택적 프로토타입이며 핵심 전달물 생성에 필수는 아니다.

실제 파일시스템의 상위 폴더명은 macOS NFD일 수 있으므로 Finder에서 보이는 문자열을 새로 조합하지 말고 현재 디렉터리에서 상대경로로 실행하는 편이 안전하다.

## 번역 및 인용 규칙

- 일본어 공식 원문이 항상 우선한다.
- 한국어는 `machine_unreviewed` 상태의 비공식 참고 번역이다.
- 검색은 한국어로 하더라도 결과에는 `source_anchor`와 일본어 문장을 함께 제시한다.
- 조항 번호, 통지 번호, 날짜, 수치는 자동으로 바꾸지 않는다.
- `Article-*` 또는 `page=*&segment=*` anchor 없이 법률 판단 근거를 표시하지 않는다.
- 번역 오류가 발견되면 원문을 수정하지 않고 한국어 파생본의 새 검수 버전을 만든다.

현재 자동 번역은 코퍼스 구축 단계에서만 Google Translate의 비공식 `client=gtx` 웹 endpoint를 사용한다. 재현성과 이용 안정성이 보장되지 않으므로 운영 전 정식 번역 API 또는 승인된 LLM으로 교체해야 한다. 사용한 방식과 정책 hash는 manifest와 각 aligned row에 남는다. 런타임에는 번역 API나 모델을 호출하지 않으며, 미리 생성·고정된 `original.ja.txt`, `translation.ko.md`, `segments.jsonl`만 읽는다.

## Translation-ready gate

활성 문서는 다음을 모두 충족해야 `translation_ready: true`가 된다.

- 모든 활성 일본어 segment에 비어 있지 않은 한국어가 존재
- 상태가 `machine_unreviewed`, `human_reviewed`, `legal_reviewed` 중 하나
- segment와 manifest의 `source_sha256`가 현재 원본 hash와 일치
- `translation_build_id`가 현재 원본 hash로 만든 버전과 일치
- 번역 실패 수가 0

`scripts/validate`가 이 조건 중 하나라도 실패하면 종료코드 1을 반환한다. `scripts/build_search_index`는 먼저 이 검증을 호출하고 성공한 활성 문서만 `search/chunks.ja.jsonl`, `search/chunks.ko.jsonl`로 만든다. 규제 원문 hash가 바뀌면 기존 번역은 자동으로 stale이며 재번역 전까지 current corpus에 포함하지 않는다.

시행령·시행규칙은 현재 광고 문안 MVP의 활성 검색 범위가 아니므로 `supporting_original_only`다. 공식 전체 XML과 개정 메타데이터는 보존하지만 전문 번역 완료 전 검색 인덱스에는 넣지 않는다.

## JCIA 제한 자료

JCIA 전문·전체 TXT·전체 번역은 저장하지 않았다. 실무 검토에는 공개 문서를 분석해 독자적으로 작성한 `rules/jcia/rules.jsonl`의 한국어 규칙 카드를 사용한다. 2026 개정 알파판, 2020 이전 확정판과의 변경점, 2017 인터넷 광고 기준 및 공식 Q&A 출처 인벤토리는 `rules/jcia/ruleset.yaml`과 `rules/jcia/version-diff.yaml`에서 관리한다.

각 카드에는 법령·후생노동성 통지의 정확한 `source_anchor`와 JCIA section/page가 권위 계층별로 분리되어 있다. 정확한 위치를 확인하지 못한 근거는 추정하지 않고 `exact_basis_unresolved: true`와 전문가 상향으로 처리한다. AI 결과의 결론은 항상 `관련 조항과 충돌 가능성이 있는 문제 후보`이며 법률 위반이나 승인을 확정하지 않는다.

`scripts/validate`는 일반 코퍼스와 JCIA 카드의 실제 JSON Schema, 근거 소유권, URL·버전, locator 허용목록, 커버리지를 함께 검사한다. `scripts/build_search_index`는 검증 후 `search/rules.ko.jsonl`을 생성하며, 애플리케이션에서는 `scripts/runtime_loader.py`로 고정 코퍼스와 규칙을 읽을 수 있다.

## OCR 정책

PDF text layer를 먼저 사용한다. 빈 페이지 또는 비공백 100자 미만 페이지는 `ocr_candidates`로 기록한다. 필요한 경우에만 원본을 변경하지 않고 OCRmyPDF/Tesseract `jpn`, 300dpi로 해당 페이지 파생본을 만든 뒤 도구 버전과 페이지를 보고서에 기록한다.

## 업데이트

- e-Gov: `/law_revisions/{law_id}`의 `law_revision_id`, 개정 공포일, 시행일을 비교한다.
- MHLW: 원본 SHA-256, 최종 URL, ETag, Last-Modified와 안내 페이지 링크를 비교한다.
- 원본 hash가 달라지면 기존 파일을 덮어쓰지 않고 새 hash 파일로 저장한다.
- 내용이 바뀐 segment만 번역을 stale 처리하고 `supersedes`로 이전 버전을 연결한다.

## 라이선스와 면책

e-Gov와 후생노동성 콘텐츠는 별도 표시가 없는 한 PDL 1.0 조건을 따르며 출처와 가공 사실을 표시해야 한다. 제3자 권리가 표시된 자료는 별도 확인한다. 이 코퍼스와 번역은 법률 자문이 아니다.

- e-Gov 이용규약: https://www.e-gov.go.jp/terms
- 후생노동성 이용규약: https://www.mhlw.go.jp/chosakuken/
- JCIA 사이트 정책: https://www.jcia.org/user/jcia/sitepolicy

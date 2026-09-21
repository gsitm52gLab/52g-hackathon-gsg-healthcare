# 일본 약기법 광고 사전검토 기능 자료

GS HALE 서비스의 일본 화장품·의약부외품 광고 사전검토 기능에 필요한 최소 기반자료와 단일 운영 프롬프트다. AI 결과는 담당자가 확인할 문제 후보이며 위법·적법, 승인 또는 반려를 확정하지 않는다.

## 구성

- [`manifest.jsonl`](manifest.jsonl): 공식 기반자료 판본·URL·정렬문 위치
- [`sources/`](sources/): 일본어 원문과 비공식 한국어 번역의 정렬 segment
- [`rules/jcia/rule-cards.ko.md`](rules/jcia/rule-cards.ko.md), [`rules.jsonl`](rules/jcia/rules.jsonl), [`ruleset.yaml`](rules/jcia/ruleset.yaml): 35개 실무 규칙과 판본·출력 정책
- [`prompts/jp-cosmetics-ad-prescreen.md`](prompts/jp-cosmetics-ad-prescreen.md): 단일 운영 프롬프트와 [입력](prompts/examples/input.json)·[출력](prompts/examples/output.json) 예시
- [`tests/cases.jsonl`](tests/cases.jsonl): 개인·회사·파일 식별자를 제거한 후보 8건과 범위 대조군 2건
- [`restricted-sources.yaml`](restricted-sources.yaml): 이용허락 전 전문을 포함하지 않는 JCIA 자료 목록

근거 권위는 `e-Gov 법령 > 후생노동성 통지·공식 해설 > JCIA 업계 자율지침` 순서다. 일본어가 우선이며 한국어는 `machine_unreviewed` 참고 번역이다. 제품 분류, 승인 효능, 전체 문안·이미지·주석 또는 객관 근거가 없으면 `확인 필요`로 유지하고 사람에게 상향한다.

Git 문서에는 원본 PDF·XML·HTML, 수집·빌드 스크립트, 검색 인덱스, QA 산출물, 스키마 및 실제 업무 원본을 포함하지 않는다. 테스트에는 [`tests/README.md`](tests/README.md)의 익명 최소 문구만 사용하며 Downloads 원본이나 연락처·메일·내부 경로를 외부 모델에 전달하지 않는다.

공식 출처의 판본과 URL을 확인한 뒤 manifest와 정렬문을 함께 갱신한다. JCIA 2026 자료는 알파판이므로 정식판으로 자동 승격하지 않는다.

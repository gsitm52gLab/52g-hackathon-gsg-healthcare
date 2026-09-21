# GS Hackathon 전달 패키지

기존 `jp-yakkiho-corpus`를 그대로 보존한 채, 아래 번호 순서로 핵심 산출물을 찾을 수 있게 만든 읽기용 인덱스다. 번호 폴더에는 원본이나 비밀정보를 복사하지 않고 기존 파일의 상대 링크만 둔다.

## 제품: GS HALE

> **Healthcare & Aesthetic Launch Enablement**  
> **해외 헬스케어 진출의 모든 일**

GS HALE은 브랜드와 GS Global이 해외 헬스케어·에스테틱 시장 진출 과정의 요청, 자료, 수정, 검수, 버전과 최종 사용본을 하나의 흐름에서 관리하는 운영 플랫폼이다.

- 이름 기억 장치: **해**외 헬스케어 진출 업무를 **일**원화하다.
- 캠페인 메시지: 글로벌 헬스케어의 새로운 물결, GS HALE.
- 제품 한계: AI 결과만으로 법률 적합, 승인 또는 출시 가능을 확정하지 않는다.

UI를 설계하거나 구현하기 전에는 다음 문서를 순서대로 읽는다.

1. [`docs/brand-system.md`](docs/brand-system.md) — 네이밍, 메시지, GS CI 적용
2. [`docs/design-system.md`](docs/design-system.md) — 토큰, 컴포넌트, 상태, 접근성, AI 판단 규칙
3. [`AGENTS.md`](AGENTS.md) — Goal/에이전트가 따라야 할 최소 결정 계약

## 전달 패키지 구성

1. [`01_sources/`](01_sources/) — 공식 원문, JA-KO 정렬문, manifest
2. [`02_rule_cards/`](02_rule_cards/) — 사람이 읽는 35개 규칙 카드
3. [`03_prompt/`](03_prompt/) — 단일 프롬프트, 입출력 예시, 테스트
4. [`04_test_cases/`](04_test_cases/) — 실제 업무자료 감사와 향후 익명화 테스트 케이스 안내
5. [`99_optional_prototype/`](99_optional_prototype/) — 검색·런타임 등 선택적 서비스 참고물

빠른 확인은 `04_test_cases`의 감사 결과를 먼저 읽고, `03_prompt`의 프롬프트와 예시를 실행하면 된다. AI 결과는 법률 의견이나 최종 승인 판정이 아니라 사람 검토를 위한 참고자료다.

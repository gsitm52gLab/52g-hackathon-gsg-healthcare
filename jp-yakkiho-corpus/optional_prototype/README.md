# 선택적 프로토타입·보류 산출물

이 폴더는 서비스 구현이 현재 핵심 전달물이 아님을 명확히 하기 위한 분류 문서다. 기존 파일을 삭제하거나 이동하지 않고 다음 산출물을 `optional_prototype`으로 지정한다.

- `search/chunks.ja.jsonl`, `search/chunks.ko.jsonl`, `search/rules.ko.jsonl`: 선택적 검색 인덱스
- `scripts/build_search_index.py`: 선택적 검색 인덱스 빌더
- `scripts/runtime_loader.py`: 애플리케이션 통합 예시 로더
- `rules/jcia/finding.schema.json`: 향후 서비스 출력·사람 검토 상태 계약 초안
- `rules/jcia/locator-allowlist.json`, `validate_rules.py`, `test_validate_rules.py`: 규칙 데이터 QA 도구
- Playwright/E2E: 이 코퍼스에는 구현하지 않으며 향후 실제 서비스 저장소에서 별도 설계

이 파일들은 기반자료의 무결성 검증과 향후 실험에는 유용하지만, 현재 납품 범위의 완성된 서비스나 UI로 간주하지 않는다. 핵심 전달물은 루트 README의 `핵심 전달물` 세 항목뿐이다.


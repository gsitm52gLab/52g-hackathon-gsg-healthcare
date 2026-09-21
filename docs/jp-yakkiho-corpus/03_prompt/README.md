# 03. 단일 프롬프트

- [운영 프롬프트](../jp-yakkiho-corpus/prompts/jp-cosmetics-ad-prescreen.md)
- [예시 입력](../jp-yakkiho-corpus/prompts/examples/input.json)
- [예시 출력](../jp-yakkiho-corpus/prompts/examples/output.json)
- [프롬프트 품질 테스트](../jp-yakkiho-corpus/prompts/test_prompt_quality.py)

실행 전 제품 분류, 매체, 주변 문맥, 객관 주장 근거를 입력해야 한다. 정보가 없으면 최종 적합·부적합 대신 `context_missing` 또는 `conditional`로 다룬다.


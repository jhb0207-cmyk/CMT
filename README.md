# PSec 상황 안내문 생성기

Streamlit 기반의 PSec 상황 안내문 생성기입니다. 키워드를 입력하여 관련 뉴스를 수집하고,
수집된 정보를 바탕으로 LLM을 활용한 보안 상황 안내문을 자동으로 작성할 수 있습니다.

## 주요 기능

- 키워드 기반 뉴스 검색 (GNews API 또는 내장 샘플 데이터)
- 선택한 권고 사항을 포함한 상황 안내문 자동 생성
- LLM(OpenAI 호환) 기반 요약 + 규칙 기반 백업 로직

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 환경 변수 (선택 사항)

- `OPENAI_API_KEY`: OpenAI 호환 LLM을 사용하기 위한 API 키
- `OPENAI_MODEL`: 사용할 모델 ID (기본값: `gpt-4o-mini`)
- `GNEWS_API_KEY`: GNews 뉴스 검색 API 키 (없을 경우 샘플 데이터 사용)


"""Utilities for generating PSec security situation notices."""

from __future__ import annotations

import json
import os
import textwrap
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from dateutil import parser as date_parser


_CLOSING_LINES = (
    "PSec은 상황을 지속적으로 모니터링할 것이며, 중대한 업데이트가 있을 시 제공할 예정입니다.",
    "질문이나 우려 사항이 있으시면 PSec(물리보안팀)으로 연락 주십시오.",
)


def generate_notice(
    keyword: str,
    news_list: Iterable[Dict[str, Any]],
    recommendation: str,
) -> str:
    """Generate a Markdown notice using an LLM with a deterministic fallback.

    Parameters
    ----------
    keyword:
        The keyword provided by the user for the news search context.
    news_list:
        An iterable of dictionaries containing news metadata and summaries.
        Keys such as ``title``, ``summary``, ``description``, ``location`` and
        ``published_at`` are recognised but optional.
    recommendation:
        The recommendation option chosen by the analyst in the Streamlit UI.

    Returns
    -------
    str
        A Markdown string composed of Situation, Assessment, Recommendation and
        Closing Lines sections.
    """

    normalized_news = _normalise_news_items(news_list)

    llm_result = _try_generate_with_llm(keyword, normalized_news, recommendation)
    if llm_result:
        return llm_result

    return _generate_with_fallback(normalized_news, recommendation)


def _normalise_news_items(news_list: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for raw in news_list:
        if not raw:
            continue

        item = dict(raw)
        # Attempt to parse datetime information into a consistent ISO format.
        published = (
            item.get("published_at")
            or item.get("date")
            or item.get("datetime")
            or item.get("time")
        )
        if published:
            parsed_dt = _safe_parse_datetime(str(published))
            if parsed_dt:
                item["published_at"] = parsed_dt.isoformat()

        # Harmonise potential text fields.
        summary = item.get("summary") or item.get("description") or item.get("content")
        if summary:
            item["summary"] = str(summary).strip()

        title = item.get("title") or item.get("headline")
        if title:
            item["title"] = str(title).strip()

        location = (
            item.get("location")
            or item.get("city")
            or item.get("region")
            or item.get("country")
        )
        if location:
            item["location"] = str(location).strip()

        items.append(item)

    return items


def _safe_parse_datetime(raw: str) -> Optional[datetime]:
    try:
        parsed = date_parser.parse(raw)
    except (ValueError, TypeError, OverflowError):
        return None

    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _try_generate_with_llm(
    keyword: str,
    news_list: List[Dict[str, Any]],
    recommendation: str,
) -> Optional[str]:
    """Attempt to use an OpenAI-compatible LLM to prepare the notice."""

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY".lower())
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI()

        news_payload = json.dumps(news_list, ensure_ascii=False, indent=2)
        system_prompt = (
            "You are a corporate physical security analyst."
            " Craft concise security situation notices in Korean markdown."
        )
        user_prompt = textwrap.dedent(
            f"""
            아래는 키워드 "{keyword}" 와 연관된 최신 뉴스 데이터입니다.

            뉴스 데이터 (JSON):
            ```json
            {news_payload}
            ```

            다음 지침을 따라 한국어 Markdown 안내문을 작성하십시오.

            1. **Situation (상황 설명)**: 주요 사건을 최대 3문장으로 간결히 요약합니다.
               - 가급적 날짜, 시간, 위치 등 구체적 정보를 포함하십시오.
            2. **Assessment (영향 평가)**: 직원과 여행자에게 예상되는 영향을 1~2문장으로 설명합니다.
               - 교통/대중교통, 비행 지연/취소, 지역 치안 등을 중점적으로 평가하십시오.
            3. **Recommendation (권고 사항)**: 아래 문구를 그대로 포함시키십시오.
               - {recommendation}
            4. **Closing Lines (마무리)**: 다음 두 문장을 그대로 추가하십시오.
               - { _CLOSING_LINES[0] }
               - { _CLOSING_LINES[1] }

            출력 형식은 반드시 다음과 같이 섹션 헤더를 포함해야 합니다.

            ## Situation (상황 설명)
            ...

            ## Assessment (영향 평가)
            ...

            ## Recommendation (권고 사항)
            ...

            ## Closing Lines (마무리)
            ...

            다른 텍스트는 포함하지 말고 위 네 개의 섹션만 반환하십시오.
            """
        ).strip()

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=600,
        )

        content = response.choices[0].message.content if response.choices else ""
        return content.strip() if content else None
    except Exception:
        return None


def _generate_with_fallback(
    news_list: List[Dict[str, Any]],
    recommendation: str,
) -> str:
    situation_lines = _build_situation_lines(news_list)
    assessment_lines = _build_assessment_lines(news_list)

    parts = [
        "## Situation (상황 설명)",
        "\n".join(situation_lines) if situation_lines else "- 관련 뉴스를 바탕으로 요약할 정보가 충분하지 않습니다.",
        "",
        "## Assessment (영향 평가)",
        "\n".join(assessment_lines),
        "",
        "## Recommendation (권고 사항)",
        recommendation,
        "",
        "## Closing Lines (마무리)",
        "\n".join(_CLOSING_LINES),
    ]

    return "\n".join(parts).strip()


def _build_situation_lines(news_list: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for item in news_list[:3]:
        timestamp = item.get("published_at")
        formatted_dt = _format_datetime(timestamp)
        location = item.get("location") or "위치 미확인"

        description = (
            item.get("summary")
            or item.get("title")
            or "추가 요약 정보가 제공되지 않았습니다."
        )

        description = " ".join(description.strip().split())

        lines.append(f"- {formatted_dt} | {location}: {description}")

    return lines


def _format_datetime(raw: Optional[str]) -> str:
    if not raw:
        return "일시 미확인"

    parsed = _safe_parse_datetime(raw)
    if not parsed:
        return raw

    return parsed.strftime("%Y-%m-%d %H:%M UTC")


def _build_assessment_lines(news_list: List[Dict[str, Any]]) -> List[str]:
    combined_text = " ".join(
        [
            str(item.get("summary") or item.get("title") or "")
            for item in news_list
        ]
    ).lower()

    assessment: List[str] = []

    if any(keyword in combined_text for keyword in ("flight", "airport", "항공", "비행")):
        assessment.append(
            "- 공항 운영과 항공편 스케줄에 지연 또는 취소 가능성이 있으므로 출장객은 항공사 공지를 수시로 확인하십시오."
        )

    if any(keyword in combined_text for keyword in ("train", "metro", "subway", "지하철", "철도")):
        assessment.append(
            "- 대중교통(지하철/철도) 운행 중단 가능성이 있어 출퇴근 경로 변경을 대비하십시오."
        )

    if any(keyword in combined_text for keyword in ("protest", "riot", "시위", "폭력", "security")):
        assessment.append(
            "- 현장 주변 치안이 불안정할 수 있어 불필요한 이동은 자제하고 현지 당국 지침을 따르십시오."
        )

    if any(keyword in combined_text for keyword in ("road", "traffic", "교통", "고속도로")):
        assessment.append(
            "- 도로 교통 체증 또는 통제가 예상되므로 이동 계획에 여유 시간을 반영하십시오."
        )

    if not assessment:
        assessment.append(
            "- 현재로서는 직원과 여행자에게 직접적인 영향은 제한적으로 판단되나, 최신 상황을 주시하십시오."
        )

    return assessment


__all__ = ["generate_notice"]


from __future__ import annotations

import streamlit as st

from news_service import search_news
from notice_generator import generate_notice


st.set_page_config(page_title="PSec 상황 안내문 생성기", layout="wide")

st.title("PSec 상황 안내문 생성기")
st.caption("키워드 기반 최신 뉴스를 분석해 상황 안내문을 자동으로 생성합니다.")


def _init_session_state() -> None:
    if "news_results" not in st.session_state:
        st.session_state.news_results = []


_init_session_state()

keyword = st.text_input("키워드 입력", placeholder="예: 강남역 화재, 김포공항 폭우")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("뉴스 검색", type="primary"):
        with st.spinner("뉴스를 검색 중입니다..."):
            st.session_state.news_results = search_news(keyword)
        if not st.session_state.news_results:
            st.warning("해당 키워드로 조회된 뉴스가 없습니다. 샘플 데이터를 확인하세요.")

with col2:
    recommendation = st.selectbox(
        "권고 사항 선택",
        (
            "BAU (Business As Usual), 다만 영향받는 직원에 대해 개별적 유연성 제공.",
            "자발적 WFH (재택근무) 권고.",
            "직원들은 필요에 따라 자신의 관리자와 협의할 것이 권고됩니다.",
        ),
    )


st.divider()

if st.session_state.news_results:
    st.subheader("수집된 뉴스")
    for idx, item in enumerate(st.session_state.news_results, start=1):
        with st.expander(f"{idx}. {item.get('title', '제목 없음')}"):
            st.write(item.get("summary") or "요약 정보가 제공되지 않았습니다.")
            meta_cols = st.columns(3)
            meta_cols[0].write(f"**발행 시각:** {item.get('published_at', '미상')}")
            meta_cols[1].write(f"**위치:** {item.get('location', '미상')}")
            meta_cols[2].write(f"**출처:** {item.get('source', '미상')}")
            if item.get("url"):
                st.markdown(f"[원문 링크]({item['url']})")

    notice = generate_notice(keyword, st.session_state.news_results, recommendation)

    st.divider()
    st.subheader("최종 안내문")
    st.markdown(notice)
else:
    st.info("뉴스 검색 버튼을 눌러 관련 기사를 불러오세요.")


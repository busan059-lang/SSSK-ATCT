"""네이버 종목토론방 여론 비교 대시보드 (삼성전자 vs SK하이닉스).

찬티(긍정)/중립/안티(부정) 라벨이 붙은 게시글 데이터를 기반으로
두 종목의 여론을 비교 분석하는 발표용 대시보드.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.data_loader import load_default_data
from src.keywords import extract_keywords, layout_wordcloud
from src.theme import (
    COMPANIES,
    COMPANY_COLORS,
    SENTIMENT_COLORS,
    SENTIMENT_ORDER,
    style_fig,
)

st.set_page_config(
    page_title="종목토론방 여론 비교 대시보드",
    page_icon="📈",
    layout="wide",
)

st.title("📈 삼성전자 vs SK하이닉스 종목토론방 여론 비교")
st.caption("네이버 금융 종목토론방 게시글을 찬티(긍정)/중립/안티(부정)로 분류하여 두 종목의 여론을 비교합니다.")

df = load_default_data()


# ------------------------------------------------------------------
# KPI 요약
# ------------------------------------------------------------------
def sentiment_pct(sub: pd.DataFrame, label: str) -> float:
    if len(sub) == 0:
        return 0.0
    return (sub["sentiment"] == label).mean() * 100


kpi_cols = st.columns(4)
company_subsets = {c: df[df["company"] == c] for c in COMPANIES}

with kpi_cols[0]:
    with st.container(border=True):
        st.metric("전체 수집 게시글", f"{len(df):,}건")
        st.caption(" · ".join(f"{c} {len(company_subsets[c]):,}건" for c in COMPANIES))

for i, c in enumerate(COMPANIES, start=1):
    sub = company_subsets[c]
    pro = sentiment_pct(sub, "찬티")
    anti = sentiment_pct(sub, "안티")
    with kpi_cols[i]:
        with st.container(border=True):
            st.metric(f"{c} 찬티 비율", f"{pro:.1f}%", delta=f"{pro - anti:+.1f}%p vs 안티")
            st.caption(f"중립 {sentiment_pct(sub, '중립'):.1f}% · 안티 {anti:.1f}%")

with kpi_cols[3]:
    with st.container(border=True):
        top_writer = df["author"].value_counts().idxmax()
        top_writer_count = df["author"].value_counts().max()
        st.metric("최다 게시자", top_writer)
        st.caption(f"{top_writer_count}건 작성 · 도배 계정 여부는 '시간대·작성자' 탭 참고")

st.divider()

tab_compare, tab_keyword, tab_time, tab_detail = st.tabs(
    ["📊 여론 비교", "🔑 핵심 키워드", "⏰ 시간대 · 작성자", "📝 본문 길이 · 샘플"]
)


# ------------------------------------------------------------------
# Tab 1: 여론 비교
# ------------------------------------------------------------------
with tab_compare:
    share = (
        df.groupby(["company", "sentiment"]).size().rename("count").reset_index()
    )
    share["total"] = share.groupby("company")["count"].transform("sum")
    share["pct"] = share["count"] / share["total"] * 100

    pivot = (
        share.pivot(index="company", columns="sentiment", values="pct")
        .reindex(index=COMPANIES, columns=SENTIMENT_ORDER)
        .fillna(0)
    )

    st.subheader("찬티 · 중립 · 안티 비율 (중립 기준 대칭 비교)")
    pro, neutral, anti = pivot["찬티"].values, pivot["중립"].values, pivot["안티"].values
    companies = pivot.index.tolist()

    fig_diverge = go.Figure()
    fig_diverge.add_trace(
        go.Bar(
            name="안티", y=companies, x=-anti, base=-(neutral / 2), orientation="h",
            marker_color=SENTIMENT_COLORS["안티"], text=[f"{v:.1f}%" for v in anti],
            textposition="inside", hovertemplate="안티 %{text}<extra></extra>",
        )
    )
    fig_diverge.add_trace(
        go.Bar(
            name="중립", y=companies, x=neutral, base=-(neutral / 2), orientation="h",
            marker_color=SENTIMENT_COLORS["중립"], text=[f"{v:.1f}%" for v in neutral],
            textposition="inside", hovertemplate="중립 %{text}<extra></extra>",
        )
    )
    fig_diverge.add_trace(
        go.Bar(
            name="찬티", y=companies, x=pro, base=neutral / 2, orientation="h",
            marker_color=SENTIMENT_COLORS["찬티"], text=[f"{v:.1f}%" for v in pro],
            textposition="inside", hovertemplate="찬티 %{text}<extra></extra>",
        )
    )
    fig_diverge.update_layout(barmode="overlay", xaxis_title="비율 (%)")
    fig_diverge.add_vline(x=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    style_fig(fig_diverge, height=260)
    st.plotly_chart(fig_diverge, width='stretch')

    col_bar, col_pie = st.columns([3, 2])

    with col_bar:
        st.subheader("종목별 감성 비율 (막대)")
        fig_bar = px.bar(
            share,
            x="sentiment",
            y="pct",
            color="company",
            barmode="group",
            category_orders={"sentiment": SENTIMENT_ORDER, "company": COMPANIES},
            color_discrete_map=COMPANY_COLORS,
            text=share["pct"].round(1).astype(str) + "%",
            labels={"sentiment": "감성", "pct": "비율 (%)", "company": "종목"},
        )
        fig_bar.update_traces(textposition="outside")
        style_fig(fig_bar, height=380)
        st.plotly_chart(fig_bar, width='stretch')

    with col_pie:
        st.subheader("종목별 감성 비율 (파이)")
        pie_cols = st.columns(2)
        for pc, company in zip(pie_cols, COMPANIES):
            sub = share[share["company"] == company]
            fig_pie = px.pie(
                sub,
                names="sentiment",
                values="count",
                color="sentiment",
                color_discrete_map=SENTIMENT_COLORS,
                category_orders={"sentiment": SENTIMENT_ORDER},
                hole=0.35,
            )
            fig_pie.update_traces(textinfo="percent+label", textposition="inside")
            style_fig(fig_pie, height=300, legend=False)
            fig_pie.update_layout(title=dict(text=company, x=0.5, xanchor="center"))
            pc.plotly_chart(fig_pie, width='stretch')


# ------------------------------------------------------------------
# Tab 2: 핵심 키워드
# ------------------------------------------------------------------
with tab_keyword:
    st.subheader("핵심 키워드 빈도 비교")
    st.caption("형태소 분석기(KoNLPy 등) 없이 정규식으로 어절 단위 한글 추출 후 조사를 제거한 경량 방식입니다.")

    top_n = st.slider("키워드 개수", min_value=10, max_value=30, value=15, step=5)

    kw_cols = st.columns(2)
    keyword_data = {}
    for kc, company in zip(kw_cols, COMPANIES):
        sub = company_subsets[company]
        freqs = extract_keywords(sub["content_clean"], top_n=top_n)
        keyword_data[company] = freqs
        if freqs:
            words, counts = zip(*freqs)
            fig_kw = px.bar(
                x=counts, y=words, orientation="h",
                labels={"x": "빈도", "y": ""},
            )
            fig_kw.update_traces(marker_color=COMPANY_COLORS[company])
            fig_kw.update_layout(yaxis=dict(autorange="reversed"), title=company)
            style_fig(fig_kw, height=max(320, 24 * len(freqs)), legend=False)
            kc.plotly_chart(fig_kw, width='stretch')
        else:
            kc.info(f"{company}: 추출된 키워드가 없습니다.")

    st.subheader("키워드 클라우드")
    st.caption(
        "한글 폰트를 서버에 번들링해야 하는 matplotlib/wordcloud 대신, "
        "브라우저가 폰트를 그리는 Plotly 텍스트 산점도로 배포 환경에 안전하게 구현했습니다."
    )
    # 워드클라우드는 고정 픽셀 크기로 그려서(반응형 stretch 미사용) 글자 크기(px)와
    # 좌표계(축 range)를 1:1로 맞추고, 겹치지 않는 자리를 찾는 콜리전 계산이
    # 실제 렌더링과 어긋나지 않도록 한다.
    CLOUD_W, CLOUD_H = 460, 380
    CLOUD_MARGIN = dict(l=10, r=10, t=40, b=10)
    plot_w = CLOUD_W - CLOUD_MARGIN["l"] - CLOUD_MARGIN["r"]
    plot_h = CLOUD_H - CLOUD_MARGIN["t"] - CLOUD_MARGIN["b"]

    cloud_cols = st.columns(2)
    for cc, company in zip(cloud_cols, COMPANIES):
        freqs = extract_keywords(company_subsets[company]["content_clean"], top_n=40)
        points = layout_wordcloud(freqs, width=plot_w, height=plot_h)
        if not points:
            cc.info(f"{company}: 표시할 키워드가 없습니다.")
            continue
        fig_cloud = go.Figure()
        fig_cloud.add_trace(
            go.Scatter(
                x=[p["x"] for p in points],
                y=[p["y"] for p in points],
                mode="text",
                text=[p["word"] for p in points],
                textfont=dict(
                    size=[p["size"] for p in points],
                    color=COMPANY_COLORS[company],
                ),
                hovertext=[f"{p['word']} ({p['count']}회)" for p in points],
                hoverinfo="text",
            )
        )
        fig_cloud.update_xaxes(visible=False, range=[-plot_w / 2, plot_w / 2], fixedrange=True)
        fig_cloud.update_yaxes(
            visible=False,
            range=[-plot_h / 2, plot_h / 2],
            scaleanchor="x",
            scaleratio=1,
            fixedrange=True,
        )
        style_fig(fig_cloud, legend=False)
        fig_cloud.update_layout(
            width=CLOUD_W,
            height=CLOUD_H,
            margin=CLOUD_MARGIN,
            title=dict(text=company, x=0.5, xanchor="center"),
        )
        cc.plotly_chart(fig_cloud, width=CLOUD_W)


# ------------------------------------------------------------------
# Tab 3: 시간대 · 작성자
# ------------------------------------------------------------------
with tab_time:
    st.subheader("시간대별(시 단위) 게시글 추이 · 감성별")

    hourly = (
        df.dropna(subset=["hour"])
        .groupby(["company", "hour", "sentiment"])
        .size()
        .rename("count")
        .reset_index()
    )
    full_index = pd.MultiIndex.from_product(
        [COMPANIES, range(24), SENTIMENT_ORDER], names=["company", "hour", "sentiment"]
    )
    hourly = (
        hourly.set_index(["company", "hour", "sentiment"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    time_cols = st.columns(2)
    for tc, company in zip(time_cols, COMPANIES):
        sub = hourly[hourly["company"] == company]
        fig_area = px.area(
            sub,
            x="hour",
            y="count",
            color="sentiment",
            category_orders={"sentiment": SENTIMENT_ORDER},
            color_discrete_map=SENTIMENT_COLORS,
            labels={"hour": "시(0~23시)", "count": "게시글 수"},
        )
        fig_area.update_layout(title=company, xaxis=dict(dtick=2))
        style_fig(fig_area, height=340)
        tc.plotly_chart(fig_area, width='stretch')

    st.subheader("작성자별 게시글 수 Top 10 (도배 계정 파악용)")
    author_cols = st.columns(2)
    for ac, company in zip(author_cols, COMPANIES):
        top_authors = (
            company_subsets[company]["author"].value_counts().head(10).sort_values()
        )
        fig_author = px.bar(
            x=top_authors.values,
            y=top_authors.index,
            orientation="h",
            labels={"x": "게시글 수", "y": ""},
        )
        fig_author.update_traces(marker_color=COMPANY_COLORS[company])
        fig_author.update_layout(title=company)
        style_fig(fig_author, height=360, legend=False)
        ac.plotly_chart(fig_author, width='stretch')


# ------------------------------------------------------------------
# Tab 4: 본문 길이 · 샘플 게시글
# ------------------------------------------------------------------
with tab_detail:
    st.subheader("감성별 본문 길이 분포")

    # 대부분 짧은 글(중앙값 20~30자)인데 극소수 장문 글 때문에 축이 늘어나
    # 분포가 바닥에 깔려 보이는 문제를 막기 위해, 상위 3% 밖 극단값은
    # 축 범위에서 잘라내고 실제 최댓값은 캡션으로 안내한다.
    content_max = int(df["content_len"].max())
    axis_cap = (int(df["content_len"].quantile(0.97) // 50) + 1) * 50

    fig_box = px.box(
        df,
        x="sentiment",
        y="content_len",
        color="company",
        category_orders={"sentiment": SENTIMENT_ORDER, "company": COMPANIES},
        color_discrete_map=COMPANY_COLORS,
        labels={"sentiment": "감성", "content_len": "본문 길이(자)", "company": "종목"},
        points=False,
    )
    fig_box.update_yaxes(range=[0, axis_cap])
    style_fig(fig_box, height=420)
    st.plotly_chart(fig_box, width='stretch')
    st.caption(
        f"가독성을 위해 세로축을 {axis_cap}자까지만 표시했습니다 "
        f"(전체 게시글의 약 97%가 이 범위 안에 있으며, 실제 최장 글은 {content_max:,}자입니다)."
    )

    st.subheader("샘플 게시글 보기")
    filt_cols = st.columns(3)
    with filt_cols[0]:
        sel_company = st.selectbox("종목 선택", COMPANIES)
    with filt_cols[1]:
        sel_sentiment = st.selectbox("감성 선택", SENTIMENT_ORDER)
    with filt_cols[2]:
        sample_n = st.slider("표시 개수", min_value=5, max_value=100, value=20, step=5)

    sample_df = (
        df[(df["company"] == sel_company) & (df["sentiment"] == sel_sentiment)]
        .sort_values("date_parsed", ascending=False)
        .head(sample_n)[["date", "author", "title", "content"]]
        .reset_index(drop=True)
    )
    st.dataframe(sample_df, width='stretch', height=420)
    st.download_button(
        "필터링된 샘플 CSV 다운로드",
        sample_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{sel_company}_{sel_sentiment}_sample.csv",
        mime="text/csv",
    )

st.divider()
with st.expander("ℹ️ 데이터 및 분석 방법"):
    st.markdown(
        """
        - **수집**: 네이버 금융 종목토론방(삼성전자 005930 / SK하이닉스 000660) 게시글
        - **전처리**: URL·특수문자 제거, 중복 게시글 제거, 짧은 글 필터링
        - **감성 라벨**: LLM(Groq `llama-3.3-70b-versatile`)이 찬티/중립/안티 3분류로 라벨링
          (반어법·냉소적 표현은 실제 의도를 기준으로 분류)
        - 이 대시보드는 위 과정을 거쳐 이미 라벨링된 `data/samsung_labeled.csv`,
          `data/hynix_labeled.csv`를 기반으로 합니다.
        """
    )
